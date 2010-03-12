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

"""Regression test for dnslsauditlog

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

import unittest
import roster_core
import roster_server
from roster_user_tools import roster_client_lib

USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-user-tools/scripts/dnslsauditlog'

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
  def __init__(self, config_instance, port):
    threading.Thread.__init__(self)
    self.config_instance = config_instance
    self.port = port
    self.daemon_instance = None

  def run(self):
    self.daemon_instance = roster_server.Server(self.config_instance, KEYFILE,
                                                CERTFILE)
    self.daemon_instance.Serve(port=self.port)

class Testdnslsauditlog(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    schema = roster_core.embedded_files.SCHEMA_FILE
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_thread = DaemonThread(self.config_instance, self.port)
    self.daemon_thread.start()
    self.db_instance = db_instance
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testListAuditLog(self):
    audit_dict = {'audit_log_user_name': None,
                  'action': None, 'data': None, 'success': None,
                  'audit_log_timestamp': None}

    self.core_instance.MakeACL(u'acl1', u'192.168.1/24', 1)
    audit_dict['data'] = (u'acl_name: acl1 cidr_block: 192.168.1/24 '
                           'range_allowed: 1')
    self.db_instance.StartTransaction()
    try:
      entry1 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry1_timestamp = str(entry1[0]['audit_log_timestamp']).replace(' ', 'T')

    time.sleep(2)
    self.core_instance.MakeACL(u'acl2', u'10.10.1/24', 0)

    audit_dict['data'] = (u'acl_name: acl2 cidr_block: 10.10.1/24 '
                           'range_allowed: 0')
    self.db_instance.StartTransaction()
    try:
      entry2 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry2_timestamp = str(entry2[0]['audit_log_timestamp']).replace(' ', 'T')

    self.core_instance.MakeView(u'test_view')

    audit_dict['data'] = u'view_name: test_view view_options:'
    self.db_instance.StartTransaction()
    try:
      entry3 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry3_timestamp = str(entry3[0]['audit_log_timestamp']).replace(' ', 'T')

    command = os.popen('python %s '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        'Action   Timestamp           Data'
        '                                                     Username '
        'Success\n'
        '---------------------------------'
        '--------------------------------------------------------------'
        '-------\n'
        'MakeACL  %s acl_name: acl1 cidr_block: 192.168.1/24 '
        'range_allowed: 1 sharrell 1\n'
        'MakeACL  %s acl_name: acl2 cidr_block: 10.10.1/24 '
        'range_allowed: 0   sharrell 1\n'
        'MakeView %s view_name: test_view view_options:'
        '                       sharrell 1\n\n' % (
            entry1_timestamp, entry2_timestamp, entry3_timestamp))
    command.close()
    command = os.popen('python %s -b %s -e %s '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, entry3_timestamp, entry3_timestamp,
                                  USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        'Action   Timestamp           Data'
        '                                                   Username Success\n'
        '---------------------------------'
        '-------------------------------------------------------------------\n'
        'MakeACL  %s acl_name: acl2 cidr_block: 10.10.1/24 '
        'range_allowed: 0 sharrell 1\n'
        'MakeView %s view_name: test_view view_options:'
        '                     sharrell 1\n\n' % (entry2_timestamp,
                                                 entry3_timestamp))
    command.close()
    command = os.popen('python %s -a MakeACL '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        'Action  Timestamp           Data'
        '                                                     '
        'Username Success\n'
        '--------------------------------'
        '-----------------------------------------------------'
        '----------------\n'
        'MakeACL %s acl_name: acl1 cidr_block: 192.168.1/24 '
        'range_allowed: 1 sharrell 1\n'
        'MakeACL %s acl_name: acl2 cidr_block: 10.10.1/24 '
        'range_allowed: 0   sharrell 1\n\n' % (entry1_timestamp,
                                               entry2_timestamp))
    command.close()
    command = os.popen('python %s -a MakeACL --success 0 '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        'Action Timestamp Data Username Success\n'
        '--------------------------------------\n\n')
    command.close()
    command = os.popen('python %s -U sharrell '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        'Action   Timestamp           Data'
        '                                                     Username '
        'Success\n'
        '---------------------------------'
        '--------------------------------------------------------------'
        '-------\n'
        'MakeACL  %s acl_name: acl1 cidr_block: 192.168.1/24 '
        'range_allowed: 1 sharrell 1\n'
        'MakeACL  %s acl_name: acl2 cidr_block: 10.10.1/24 '
        'range_allowed: 0   sharrell 1\n'
        'MakeView %s view_name: test_view view_options:'
        '                       sharrell 1\n\n' % (
            entry1_timestamp, entry2_timestamp, entry3_timestamp))
    command.close()

  def testErrors(self):
    command = os.popen('python %s --success no '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: --success must be a 1 or 0\n')
    command = os.popen('python %s -e time1 -b time0 '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: Improperly formatted timestamps.\n')
    command.close()
    command = os.popen('python %s -e tTime1 -b tTime0 '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: Improperly formatted timestamps.\n')
    command.close()
    command = os.popen('python %s -U sharrell -e time '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: Both --begin-time and --end-time must be specified.\n')

if( __name__ == '__main__' ):
      unittest.main()
