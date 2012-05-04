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

"""This module is used to create an audit log of activities executed on the
dnsManagement core and user libs.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = "0.16"


import cPickle
import datetime
import syslog
import unicodedata


class AuditLog(object):

  def __init__(self, log_to_syslog=False, log_to_db=False, db_instance=None,
               log_to_file=False, log_file_name=None):
    """Sets where log messages get sent.
    
    Inputs:
      log_to_syslog: bool of if syslog is used
      log_to_db: bool of if db is used
      db_instance: instance of DbAccess class
      log_to_file: bool of if file is used
      log_file: string of file name to log to
    """
    self.log_to_syslog = log_to_syslog
    self.log_to_db = log_to_db
    self.db_instance = db_instance
    self.log_to_file = log_to_file
    self.log_file_name = log_file_name

  def LogAction(self, user, action, data, success):
    """Logs action to places specified in initalizer.

    Inputs:
      user: string of user name
      action: string of function name that is being logged
      data: dictionary of arguments
        ex: {'replay_args': [u'test_acl', u'192.168.0/24', 1],
             'audit_args': {'cidr_block': u'192.168.0/24',
                            'range_allowed': 1,
                            'acl_name': u'test_acl'}}
      success: bool of success of action
    """
    current_datetime = datetime.datetime.now()
    current_timestamp = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    pretty_print_log_string = self._PrettyPrintLogString(user, action, data,
                                                         success,
                                                         current_timestamp)

    if( self.log_to_db ):
      audit_log_id = self._LogToDatabase(user, action, data, success,
                                         current_datetime)

    if( self.log_to_syslog ):
      self._LogToSyslog(pretty_print_log_string)

    if( self.log_to_file ):
      self._LogToFile(pretty_print_log_string)

    if( self.log_to_db ):
      return audit_log_id

  def _LogToSyslog(self, log_string):
    """Writes log string to syslog.

    Inputs:
      log_string: string of message to write to syslog 
    """
    syslog.openlog('dnsManagement')
    # Convert the unicode strings to ascii if needed
    if( isinstance(log_string, unicode) ):
      log_string = unicodedata.normalize('NFKD', log_string).encode(
          'ASCII', 'replace')
    try:
      syslog.syslog(log_string)
    finally:
      syslog.closelog()

  def _LogToDatabase(self, user, action, data, success, current_timestamp):
    """Writes log data to db.
    
    Inputs:
      user: string of user name
      action: string of action
      data: string of data
      success: bool of success of action
      current_timestamp: string of mysql formated time stamp
    """
    if( success ):
      success = 1
    else:
      success = 0
    data = cPickle.dumps(data)
    log_dict = {'audit_log_id': None,
                'audit_log_user_name': user,
                'action': action,
                'data': data,
                'success': success,
                'audit_log_timestamp': current_timestamp}

    self.db_instance.StartTransaction()
    try:
      audit_log_id = self.db_instance.MakeRow('audit_log', log_dict)
    except:
      self.db_instance.EndTransaction(rollback=True)
      raise

    self.db_instance.EndTransaction()

    return audit_log_id

  def _LogToFile(self, log_string):
    """Writes log string to file.

    Inputs:
      log_string: string of message to write to file
    """
    log_file = open(self.log_file_name, 'a')
    try:
      log_file.write('%s\n' % log_string)
    finally:
      log_file.flush()
      log_file.close()

  def _PrettyPrintLogString(self, user, action, data, success,
                            current_timestamp):
    """Formats data into human readable string.

    Inputs:
      user: string of user name
      action: string of action
      data: string of data
      success: bool of success of action
      current_timestamp: string of mysql formated time stamp

    Outputs:
      string of log message
        example: User sharrell SUCCEEDED while executing MakeUser with data
                     user_name: ahoward access_level: 64 at 2009-04-22 16:20:18
    """
    if( success ):
      success_string = 'SUCCEEDED'
    else:
      success_string = 'FAILED'

    return 'User %s %s while executing %s with data %s at %s' % (
        user, success_string, action, data['audit_args'], current_timestamp)


# vi: set ai aw sw=2:
