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


"""Test for Credential cache library."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import datetime
import time
import unittest
import os
import sys


import roster_core
import roster_server


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='test_data/dnscred'


class TestCredentialsLibrary(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.server_instance = roster_server.Server(self.config_instance, KEYFILE,
                                                CERTFILE, core_die_time=5,
                                                inf_renew_time=5, clean_time=0)
    self.credential = self.server_instance.GetCredentials(USERNAME, u'test')
    self.server_instance.core_store = [] # Clear out core instance from above

    self.logfile = self.config_instance.config_file['server']['server_log_file']

  def tearDown(self):
    if( os.path.exists(self.logfile) ):
      os.remove(self.logfile)

  def testLogException(self):
    try:
      raise Exception
    except Exception, e:
      self.server_instance.LogException('testfunction', ['arg1', 'arg2'],
                                        {'kwarg': 'value'}, USERNAME)
    logfile_handle = open(self.logfile, 'r')
    logfile_lines = logfile_handle.readlines()
    logfile_handle.close()

    self.assertEqual(logfile_lines[12:16],
        ['FUNCTION: testfunction\n', "ARGS: ['arg1', 'arg2']\n",
         "KWARGS: {'kwarg': 'value'}\n", 'USER: sharrell\n'])
    self.assertEqual(logfile_lines[17:],
        ['\n', 'Traceback (most recent call last):\n',
         '  File "%s", line 88, in testLogException\n' % sys.argv[0],
         '    raise Exception\n', 'Exception\n', '\n',
         '---------------------\n'])
    self.assertEqual(len(logfile_lines), 24)

  def testLogMessage(self):
    self.server_instance.LogMessage('On the record.', USERNAME)
    logfile_handle = open(self.logfile, 'r')
    logfile_lines = logfile_handle.readlines()
    logfile_handle.close()
    self.assertEqual(logfile_lines[12:14],
                     ['MESSAGE: On the record.\n',
                      'USER: sharrell\n'])

  def testCoreRun(self):
    new_cred = self.server_instance.GetCredentials(u'shuey', 'testpass')
    self.assertEqual(self.server_instance.CoreRun('ListUsers', USERNAME,
                                                  self.credential),
                     {'new_credential': u'',
                      'core_return': {u'shuey': 64, u'jcollins': 32,
                                      u'tree_export_user': 0,
                                      u'sharrell': 128},
                      'log_uuid_string': None, 'error': None})
    self.assertEqual(self.server_instance.CoreRun('ListUsers', USERNAME,
                                                  self.credential),
                     {'new_credential': u'',
                      'core_return': {u'shuey': 64, u'jcollins': 32,
                                      u'tree_export_user': 0,
                                      u'sharrell': 128},
                      'log_uuid_string': None, 'error': None})
    self.assertTrue(len(self.server_instance.core_store))
    time.sleep(6)
    self.server_instance.CleanupCoreStore()
    self.assertFalse(len(self.server_instance.core_store))
    self.assertEqual(self.server_instance.CoreRun('ListUsers', USERNAME,
                                                  self.credential),
                     {'new_credential': u'',
                      'core_return': {u'shuey': 64, u'jcollins': 32,
                                      u'tree_export_user': 0,
                                      u'sharrell': 128},
                      'log_uuid_string': None, 'error': None})
    self.assertEqual(self.server_instance.CoreRun('ListUsers', USERNAME,
                                                  self.credential),
                     {'new_credential': u'',
                      'core_return': {u'shuey': 64, u'jcollins': 32,
                                      u'tree_export_user': 0,
                                      u'sharrell': 128},
                      'log_uuid_string': None, 'error': None})
    self.assertEqual(self.server_instance.CoreRun('ListUsers', USERNAME,
                                                  self.credential),
                     {'new_credential': u'',
                      'core_return': {u'shuey': 64, u'jcollins': 32,
                                      u'tree_export_user': 0,
                                      u'sharrell': 128},
                      'log_uuid_string': None, 'error': None})
    self.assertEqual(len(self.server_instance.core_store), 1)

  def testCoreStoreCleanup(self):
    self.assertEqual(self.server_instance.core_store, [])
    self.assertEqual(self.server_instance.CoreRun(u'ListUsers', USERNAME,
                                        self.credential)['core_return'],
                                        {'tree_export_user': 0,
                                         'shuey': 64, 'jcollins': 32,
                                         'sharrell': 128})
    self.assertTrue(len(self.server_instance.core_store))
    time.sleep(6)
    self.assertEqual(self.server_instance.CoreRun(u'ListUsers', USERNAME,
                                        self.credential)['core_return'],
                     {'shuey': 64, 'tree_export_user': 0, 'jcollins': 32,
                      'sharrell': 128})
    self.server_instance.CleanupCoreStore()
    self.assertFalse(len(self.server_instance.core_store))

  def testCoreWrongPassword(self):
    initial_time = datetime.datetime.now()
    self.server_instance.GetCredentials(u'shuey', u'fakepass')
    self.server_instance.GetCredentials(u'shuey', u'fakepass')
    self.server_instance.GetCredentials(u'shuey', u'fakepass')
    self.server_instance.GetCredentials(u'shuey', u'fakepass')
    self.assertTrue( initial_time + datetime.timedelta(seconds=4) < (
        datetime.datetime.now()))

  def testStringToUnicode(self):
    self.assertEqual(repr(self.server_instance.StringToUnicode('test')),
                     "u'test'")
    self.assertEqual(self.server_instance.StringToUnicode(2), 2)
                    
    self.assertEqual(repr(self.server_instance.StringToUnicode(
        [{'record_target': 'host3', 'record_type': 'a',
          'view_name': 'test_view', 'record_zone_name': 'forward_zone',
          'record_arguments': {'assignment_ip': '192.168.1.5'}},
         {'record_target': '5', 'record_type': 'ptr',
          'view_name': 'test_view', 'record_zone_name': 'forward_zone',
          'record_arguments': {'assignment_host': 'host3.university.edu.'}}])),
        "[{u'record_target': u'host3', u'record_type': u'a', "
          "u'view_name': u'test_view', u'record_zone_name': u'forward_zone', "
          "u'record_arguments': {u'assignment_ip': u'192.168.1.5'}}, "
         "{u'record_target': u'5', u'record_type': u'ptr', "
          "u'view_name': u'test_view', u'record_zone_name': u'forward_zone', "
          "u'record_arguments': {u'assignment_host': u'host3.university.edu.'}}]")

if( __name__ == '__main__' ):
  unittest.main()

