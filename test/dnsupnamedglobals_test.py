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

"""Regression test for dnsupnamedglobals

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import os
import sys
import socket
import threading
import time
import getpass
import datetime

import unittest

import roster_core
from roster_user_tools  import roster_client_lib
import roster_server

USER_CONFIG = 'test_data/roster_user_tools.conf'
if( len(sys.argv) > 1 ):
  CONFIG_FILE = sys.argv[1]
  del sys.argv[1]
else:
  CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TEST_FILE = 'test_data/test_named'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-user-tools/scripts/dnsupnamedglobals'

class options(object):
  password = u'test'
  username = u'sharrell'
  server = None
  ldap = u'ldaps://ldap.cs.university.edu:636'
  credfile = CREDFILE
  view_name = None
  ip_address = None
  target = u'machine1'
  ttl = 64

class DaemonThread(threading.Thread):
  def __init__(self, config_instance, port, unittest_timestamp=None):
    threading.Thread.__init__(self)
    self.config_instance = config_instance
    self.port = port
    self.unittest_timestamp = unittest_timestamp
    self.daemon_instance = None

  def run(self):
    self.daemon_instance = roster_server.Server(self.config_instance, KEYFILE,
                                                CERTFILE, unittest_timestamp=(
                                                    self.unittest_timestamp))
    self.daemon_instance.Serve(port=self.port)

class TestDnsMkHost(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    self.db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.unittest_timestamp = datetime.datetime.now()
    self.daemon_thread = DaemonThread(self.config_instance, self.port,
                                      self.unittest_timestamp)
    self.daemon_thread.start()
    self.core_instance = roster_core.Core(USERNAME, self.config_instance,
                                          unittest_timestamp=(
                                              self.unittest_timestamp))
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)
    handle = open(TEST_FILE, 'w')
    try:
      handle.writelines('zone "example.com" IN {\n'
                        '    type master;\n'
                        '    file "example.com.zone";\n'
                        '    allow-update { none; };\n};\n\n')
    finally:
      handle.close()

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)
    if( os.path.exists(TEST_FILE) ):
      os.remove(TEST_FILE)

  def testUpNamedGlobalsReadWriteRevert(self):
    # Upload file to database
    self.core_instance.MakeDnsServerSet(u'set1')
    output = os.popen('python %s update -f %s -d set1 '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED NAMED_CONF_GLOBAL_OPTION: test_data/test_named\n')
    output.close()
    timestamp_string = self.unittest_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    # Print the file list of set1 from the database
    output = os.popen('python %s list -d set1 -t "%s" --no-header '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, timestamp_string, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), '1 %s set1\n\n' % timestamp_string)
    output.close()
    # Write uploaded file from the database by set name and timestamp
    output = os.popen('python %s dump -d set1 -t "%s" -f %s '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, timestamp_string, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'Wrote file: %s\n' % TEST_FILE)
    output.close()
    # Verify file contents
    handle = open(TEST_FILE, 'r')
    try:
      file_contents = handle.read()
    finally:
      handle.close()
    self.assertEqual(file_contents, 'zone "example.com" IN {\n'
                                    '    type master;\n'
                                    '    file "example.com.zone";\n'
                                    '    allow-update { none; };\n};\n\n')
    # Write uploaded file from the database by id
    output = os.popen('python %s dump -i 1 -f %s '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'Wrote file: %s\n' % TEST_FILE)
    output.close()
    # Verify file contents
    handle = open(TEST_FILE, 'r')
    try:
      file_contents = handle.read()
    finally:
      handle.close()
    self.assertEqual(file_contents, 'zone "example.com" IN {\n'
                                    '    type master;\n'
                                    '    file "example.com.zone";\n'
                                    '    allow-update { none; };\n};\n\n')
    # Add some more configurations to test revert
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options2')
    # Revert last version to original file
    output = os.popen('python %s revert -d set1 -i 1 -s %s -u %s -p %s '
                      '--config-file %s' % (
                           EXEC, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(
        output.read(),
        'REVERTED NAMED_CONF_GLOBAL_OPTION: dns_server_set: set1 rev: 1\n')
    output.close()
    # Download original file string and write to new file
    output = os.popen('python %s dump -i 4 -f %s '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'Wrote file: %s\n' % TEST_FILE)
    output.close()
    # Verify file contents
    handle = open(TEST_FILE, 'r')
    try:
      file_contents = handle.read()
    finally:
      handle.close()
    self.assertEqual(file_contents, 'zone "example.com" IN {\n'
                                    '    type master;\n'
                                    '    file "example.com.zone";\n'
                                    '    allow-update { none; };\n};\n\n')
    # Print configuration revisions list
    output = os.popen('python %s list -d set1 -t "%s" '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, timestamp_string, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'option_id timestamp           dns_server_set\n'
        '--------------------------------------------\n'
        '1         %s set1\n'
        '2         %s set1\n'
        '3         %s set1\n'
        '4         %s set1\n\n' % (
            timestamp_string, timestamp_string, timestamp_string,
            timestamp_string))
    # Write latest configuration to a file
    config_dict = self.core_instance.db_instance.GetEmptyRowDict(
        'named_conf_global_options')
    config_dict['named_conf_global_options_id'] = 4
    update_config_dict = self.core_instance.db_instance.GetEmptyRowDict(
        'named_conf_global_options')
    time_difference = self.unittest_timestamp + datetime.timedelta(seconds=1)
    update_config_dict['options_created'] = time_difference
    self.core_instance.db_instance.StartTransaction()
    try:
      self.core_instance.db_instance.UpdateRow('named_conf_global_options',
                                               config_dict, update_config_dict)
    except:
      self.core_instance.db_instance.RollbackTransaction()
      raise
    self.core_instance.db_instance.EndTransaction()
    time.sleep(2)
    output = os.popen('python %s dump -f %s -d set1 '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'Wrote file: test_data/test_named\n')
    output.close()
    # Verify file contents
    handle = open(TEST_FILE, 'r')
    try:
      file_contents = handle.read()
    finally:
      handle.close()
    self.assertEqual(file_contents,
        'zone "example.com" IN {\n'
        '    type master;\n'
        '    file "example.com.zone";\n'
        '    allow-update { none; };\n};\n\n')

  def testEdit(self):
    os.environ['EDITOR'] = 'python fake_editor.py example.com new_zone'
    # Upload file to database
    self.core_instance.MakeDnsServerSet(u'set1')
    output = os.popen('python %s update -f %s -d set1 '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED NAMED_CONF_GLOBAL_OPTION: %s\n' % TEST_FILE)
    output.close()
    timestamp_string = self.unittest_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    # Print the file list of set1 from the database
    output = os.popen('python %s list -d set1 -t "%s" --no-header '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, timestamp_string, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), '1 %s set1\n\n' % timestamp_string)
    output.close()
    # Write uploaded file from the database by set name and timestamp
    output = os.popen('python %s edit -d set1 -t "%s" -f %s --keep-output '
                      '-s %s -u %s -p %s --config-file %s' % (
                           EXEC, timestamp_string, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'ADDED NAMED_CONF_GLOBAL_OPTION: %s\n' % TEST_FILE)
    output.close()
    # Verify file contents
    handle = open(TEST_FILE, 'r')
    try:
      file_contents = handle.read()
    finally:
      handle.close()
    self.assertEqual(file_contents, 'zone "new_zone" IN {\n'
                                    '    type master;\n'
                                    '    file "new_zone.zone";\n'
                                    '    allow-update { none; };\n};\n\n')

  def testErrors(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options2')
    output = os.popen('python %s dump -d d -t 299 -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: Timestamp incorrectly formatted.\n')
    output.close()
    output = os.popen('python %s dump -d set2 -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: No configurations found.\n')
    output.close()
    output = os.popen('python %s revert set1 -f file -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -f/--file flag cannot be used with the revert '
        'command.\n')
    output.close()
    output = os.popen('python %s revert -d set1 -s %s -u %s -p %s --config-file %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -i/--option-id flag is required.\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
