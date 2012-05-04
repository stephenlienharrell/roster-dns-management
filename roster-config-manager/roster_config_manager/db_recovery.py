#!/usr/bin/python

# Copyright (c) 2009, Purdue University
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# Neither the name of the Purdue University nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This module contains all of the logic for the recovery system.

It should be only called by the roster recovery system.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'

import roster_core
import os
import bz2
import cPickle


roster_core.core.CheckCoreVersionMatches(__version__)


class Recover(object):
  """Roster Recovery

  This class contains methods pertaining to recover roster after
  catastrophic failure.
  """
  def __init__(self, username, config_instance):
    """Sets self.db_instance

    Inputs:
      config_instance: instantiated config class object
    """
    self.username = username
    self.config_instance = config_instance
    self.db_instance = config_instance.GetDb()
    self.core_instance = roster_core.Core(self.username, self.config_instance)
    self.core_helper_instance = roster_core.CoreHelpers(
         self.core_instance)

  def PushBackup(self, audit_log_id):
    """Restores database from sql backup with specified audit log id

    Inputs:
      audit_log_id: integer of audit log id
    """
    backup_dir = self.config_instance.config_file['exporter']['backup_dir']

    full_dump_file = bz2.BZ2File('%s/audit_log_replay_dump-%s.bz2' %
                                 (backup_dir, audit_log_id))
    try:
      full_dump_file_contents = full_dump_file.read()
    finally:
      full_dump_file.close()

    print 'Loading database from backup with ID %s' % audit_log_id

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(full_dump_file_contents)
    self.db_instance.EndTransaction()

  def RunAuditStep(self, audit_log_id):
    """Runs a step from the audit_log

    Inputs:
      audit_log_id: integer of audit_log_id
    """
    forbidden_actions = ['ExportAllBindTrees']
    audit_dict = self.db_instance.GetEmptyRowDict('audit_log')
    audit_dict['audit_log_id'] = audit_log_id
    self.db_instance.StartTransaction()
    try:
      audit_log = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    if( audit_log == () ):
      print 'Not replaying action with id %s, action is blank.' % audit_log_id
      return
    action = audit_log[0]['action']
    success = audit_log[0]['success']
    if( action in forbidden_actions ):
      print 'Not replaying action with id %s, action not allowed.' % (
          audit_log_id)
    elif( not success ):
      print 'Not replaying action with id %s, action was unsuccessful.' % (
          audit_log_id)
    else:
      data = cPickle.loads(str(audit_log[0]['data']))['replay_args']
      print 'Replaying action with id %s: %s\nwith arguments: %s' % (
          audit_log_id, action, str(data))
      if( hasattr(self.core_instance, action) ):
        function = getattr(self.core_instance, action)
        function(*data)
      elif( hasattr(self.core_helper_instance, action) ):
        function = getattr(self.core_helper_instance, action)
        function(*data)
      else:
        raise roster_core.errors.UnexpectedDataError(
            "Function %s does not exist." % action)

  def RunAuditRange(self, audit_log_id):
    """Runs a range of audit steps

    Inputs:
      audit_log_id: integer of audit_log_id
    """
    backup_dir = self.config_instance.config_file['exporter']['backup_dir']
    file_list = os.listdir(backup_dir)
    db_dumps = []

    for fname in file_list:
      if( fname.startswith('audit_log_replay_dump-') ):
        db_dumps.append(int(fname.split('-')[1].split('.')[0]))
    audit_id = 0
    for audit_id in reversed(sorted(db_dumps)):
      if( audit_id < audit_log_id ):
        break
    self.PushBackup(audit_id)

    for current_id in range(audit_id + 1, audit_log_id):
      self.RunAuditStep(current_id)
