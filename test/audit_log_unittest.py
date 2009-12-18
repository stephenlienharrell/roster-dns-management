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

"""Unittest for audit logger

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.10'


import datetime
import os
import time
import unicodedata
import unittest

from roster_core import audit_log

import roster_core


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TEMP_LOG = 'temp_log'

class TestAuditLog(unittest.TestCase):

  def setUp(self):
    config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = config_instance.GetDb()

    schema = roster_core.embedded_files.SCHEMA_FILE
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.db_instance = db_instance
    self.audit_log_instance = audit_log.AuditLog(db_instance=db_instance,
                                                 log_file_name=TEMP_LOG)

  def testPrettyPrintLogString(self):
    self.assertEqual(self.audit_log_instance._PrettyPrintLogString(
      'sharrell', 'MakeUser', 'user=ahoward user_level=64', True,
      '2009-04-28 10:46:50'),  'User sharrell SUCCEEDED while executing '
      'MakeUser with data user=ahoward user_level=64 at 2009-04-28 10:46:50')

  def testLogToSyslog(self):
    current_time = time.time()
    unittest_string = 'unittest %s' % current_time
    self.audit_log_instance._LogToSyslog(unittest_string)
    lines = open('/var/log/messages', 'r').readlines()
    for line in lines:
      if( line.endswith('dnsManagement: %s' % unittest_string) != -1):
        break
    else:
      self.fail()

    unittest_string = u'unicode \xc6 unittest %s' % current_time
    self.audit_log_instance._LogToSyslog(unittest_string)
    unittest_string = unicodedata.normalize('NFKD', unittest_string).encode(
        'ASCII', 'replace')
    lines = open('/var/log/messages', 'r').readlines()
    for line in lines:
      if( line.endswith('dnsManagement: %s' % unittest_string) != -1):
        break
    else:
      self.fail()

  def testLogToDatabase(self):
    self.audit_log_instance._LogToDatabase(u'sharrell', u'MakeUser', 
                                           u'user=ahoward user_level=64', True,
                                           datetime.datetime(2009, 4, 28, 10,
                                                             46, 50))
    audit_log_dict = self.db_instance.GetEmptyRowDict('audit_log')
    self.db_instance.StartTransaction()
    try:
      self.assertEqual(self.db_instance.ListRow('audit_log', audit_log_dict),
                       ({'action': u'MakeUser', 
                         'audit_log_timestamp':
                             datetime.datetime(2009, 4, 28, 10, 46, 50), 
                         'data': u'user=ahoward user_level=64', 
                         'audit_log_user_name': u'sharrell', 'success': 1},))
    finally:
      self.db_instance.EndTransaction()

  def testLogToFile(self):
    current_time = time.time()
    unittest_string = 'unittest %s' % current_time
    try:
      self.audit_log_instance._LogToFile(unittest_string)
      lines = open(TEMP_LOG, 'r').readlines()
      for line in lines:
        if( line.endswith(unittest_string) != -1):
          break
      else:
        self.fail()
    finally:
      os.remove(TEMP_LOG)


if( __name__ == '__main__' ):
  unittest.main()
