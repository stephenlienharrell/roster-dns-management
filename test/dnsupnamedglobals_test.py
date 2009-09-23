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
__version__ = '0.5'


import os
import sys
import socket
import threading
import time
import getpass
import fakeldap
import datetime

import unittest
sys.path.append('../')

import roster_core
from roster_user_tools  import roster_client_lib
import roster_server

CONFIG_FILE = os.path.expanduser('~/.rosterrc') # Example in test_data
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
                                                CERTFILE, ldap_module=fakeldap,
                                                unittest_timestamp=(
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

    schema = open(SCHEMA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.CommitTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.CommitTransaction()
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
    output = os.popen('python %s -f %s -d set1 --update '
                      '-s %s -u %s -p %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD))
    self.assertEqual(output.read(),
                     'ADDED NAMED_CONF_GLOBAL_OPTION: test_data/test_named\n')
    output.close()
    timestamp_string = self.unittest_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    # Print the file list of set1 from the database
    output = os.popen('python %s -l -d set1 -t "%s" '
                      '-s %s -u %s -p %s' % (
                           EXEC, timestamp_string, self.server_name,
                           USERNAME, PASSWORD))
    self.assertEqual(output.read(), '1 %s set1\n\n' % timestamp_string)
    output.close()
    # Write uploaded file from the database by set name and timestamp
    output = os.popen('python %s -e -d set1 -t "%s" -f %s '
                      '-s %s -u %s -p %s' % (
                           EXEC, timestamp_string, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD))
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
    output = os.popen('python %s -e -i 1 -f %s '
                      '-s %s -u %s -p %s' % (
                           EXEC, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD))
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
    output = os.popen('python %s -r set1 -i 1 -s %s -u %s -p %s' % (
                           EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(
        output.read(),
        'REVERTED NAMED_CONF_GLOBAL_OPTION: dns_server_set: set1 rev: 1\n')
    output.close()
    # Download original file string and write to new file
    output = os.popen('python %s -e -i 4 -f %s '
                      '-s %s -u %s -p %s' % (
                           EXEC, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD))
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
    output = os.popen('python %s -l -d set1 -t "%s" '
                      '-s %s -u %s -p %s' % (
                           EXEC, timestamp_string, self.server_name,
                           USERNAME, PASSWORD))
    self.assertEqual(output.read(), '1 %s set1\n2 %s set1\n3 %s set1\n'
                                    '4 %s set1\n\n' % (
        timestamp_string, timestamp_string, timestamp_string, timestamp_string))
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
    self.core_instance.db_instance.CommitTransaction()
    time.sleep(2)
    output = os.popen('python %s -n -f %s -d set1 '
                      '-s %s -u %s -p %s' % (
                           EXEC, TEST_FILE, self.server_name,
                           USERNAME, PASSWORD))
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



  def testErrors(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options2')
    output = os.popen('python %s -t 299 -s %s -u %s -p %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(), 'CLIENT ERROR: Timestamp incorrectly formatted.\n')
    output.close()
    output = os.popen(
        'python %s -f test --update -l -i 1 -t "2009-02-02 01:10:10" -r '
        '1 -e -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -l/--list flag cannot be used.\n'
        'CLIENT ERROR: The -e/--edit flag cannot be used.\n'
        'CLIENT ERROR: The -i/--option-id flag cannot be used.\n'
        'CLIENT ERROR: The -r/--revert flag cannot be used.\n'
        'CLIENT ERROR: The -t/--timestamp flag cannot be used.\n')
    output.close()
    output = os.popen(
        'python %s -l -i 1 -t "2009-02-02 01:10:10" -r set1 -f file -e '
        '-s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                               PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -f/--file flag cannot be used.\n'
        'CLIENT ERROR: The -e/--edit flag cannot be used.\n'
        'CLIENT ERROR: The -r/--revert flag cannot be used.\n')
    output.close()
    output = os.popen('python %s -e -r 1 -s %s -u %s -p %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -r/--revert flag cannot be used.\n')
    output.close()
    output = os.popen('python %s -e -s %s -u %s -p %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: Either an option id or dns server set and '
        'timestamp are needed.\n')
    output.close()
    output = os.popen('python %s -e -d set1 -s %s -u %s -p %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: Multiple configurations found. This could '
        'be due to an internal error or arguments may be '
        'too general.\n')
    output.close()
    output = os.popen('python %s -e -d set2 -s %s -u %s -p %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(), 'CLIENT ERROR: No configurations found.\n')
    output.close()
    output = os.popen('python %s -r set1 -f file -s %s -u %s -p %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -f/--file flag cannot be used.\n')
    output.close()
    output = os.popen('python %s -r set1 -s %s -u %s -p %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: To revert a configuration, the desired '
        'replacement must be specified with -i\n')
    output.close()
    output = os.popen(
        'python %s -f test -n --update -l -i 1 -t "2009-02-02 01:10:10" -r '
        '1 -e -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -l/--list flag cannot be used.\n'
        'CLIENT ERROR: The -e/--edit flag cannot be used.\n'
        'CLIENT ERROR: The -i/--option-id flag cannot be used.\n'
        'CLIENT ERROR: The -r/--revert flag cannot be used.\n'
        'CLIENT ERROR: The -t/--timestamp flag cannot be used.\n'
        'CLIENT ERROR: The --update flag cannot be used.\n')
    output.close()
    output = os.popen(
        'python %s -n  '
        '-s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME, PASSWORD))
    self.assertEqual(output.read(), 'CLIENT ERROR: Must specify a dns server '
                                    'set with -d.\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
