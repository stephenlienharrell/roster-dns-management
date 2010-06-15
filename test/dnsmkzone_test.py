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

"""Regression test for dnsmkzone

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
EXEC='../roster-user-tools/scripts/dnsmkzone'

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

class TestDnsMkZone(unittest.TestCase):

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
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)


  def testMakeZoneWithView(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s forward -v test_view -z test_zone --origin '
                      'dept.univiersity.edu. --type master --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED FORWARD ZONE: zone_name: test_zone zone_type: '
                     'master zone_origin: dept.univiersity.edu. '
                     'zone_options: None view_name: test_view\n')
    output.close()

    self.assertEqual(self.core_instance.ListZones(),
        {u'test_zone':
            {u'test_view':
                {'zone_type': u'master', 'zone_options': u'',
                 'zone_origin': u'dept.univiersity.edu.'}}})
    output = os.popen('python %s forward -z test_zone2 -v test_view --origin '
                      'dept2.univiersity.edu. --type master --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED FORWARD ZONE: zone_name: test_zone2 zone_type: '
                     'master zone_origin: dept2.univiersity.edu. '
                     'zone_options: None view_name: test_view\n')
    output.close()
    self.assertEqual(self.core_instance.ListZones(),
        {u'test_zone':
            {u'test_view':
                {'zone_type': u'master', 'zone_options': u'',
                 'zone_origin': u'dept.univiersity.edu.'}},
         u'test_zone2':
             {u'test_view':
                 {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'dept2.univiersity.edu.'}}})

  def testMakeReverseZoneOrigin(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--origin 168.192.in-addr.arpa. '
                      '--type master --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED REVERSE ZONE: zone_name: reverse_zone '
                     'zone_type: master zone_origin: 168.192.in-addr.arpa. '
                     'zone_options: None view_name: test_view\n'
                     'ADDED REVERSE RANGE ZONE ASSIGNMENT: '
                     'zone_name: reverse_zone cidr_block: 192.168/16 \n')
    output.close()

  def testMakeReverseZoneCidr(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--cidr-block 192.168/16 '
                      '--type master --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED REVERSE ZONE: zone_name: reverse_zone '
                     'zone_type: master zone_origin: 168.192.in-addr.arpa. '
                     'zone_options: None view_name: test_view\n'
                     'ADDED REVERSE RANGE ZONE ASSIGNMENT: '
                     'zone_name: reverse_zone cidr_block: 192.168/16 \n')
    output.close()

  def testmakeReverseZoneWeird(self):
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--cidr-block 192.168/27 '
                      '--type master --dont-make-any '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'ADDED REVERSE ZONE: zone_name: reverse_zone '
                     'zone_type: master zone_origin: 0/27.168.192.in-addr.arpa. '
                     'zone_options: None view_name: test_view\n'
                     'ADDED REVERSE RANGE ZONE ASSIGNMENT: '
                     'zone_name: reverse_zone cidr_block: 192.168/27 \n')
    output.close()

  def testErrors(self):
    output = os.popen('python %s forward -v test_view -z test_zone --origin '
                      'dept.univiersity.edu. --type master '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The view specified does not exist.\n')
    output.close()
    self.core_instance.MakeView(u'test_view')
    output = os.popen('python %s forward -v test_view -z test_zone --type master '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The --origin flag is required.\n')
    output.close()
    output = os.popen('python %s forward -v test_view -z test_zone --origin '
                      'dept.univiersity.edu. -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The -t/--type flag is required.\n')
    output.close()
    output = os.popen('python %s reverse -v test_view -z reverse_zone --origin '
                      '168.192.in-addr.arpa. --cidr-block 192.168/16 '
                      '--type master '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: --cidr-block and --origin cannot be used '
                     'simultaneously.\n')
    output.close()
    output = os.popen('python %s reverse -v test_view -z reverse_zone '
                      '--type master '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Either --cidr-block or --origin must be '
                     'used.\n')
    output.close()
    output = os.popen('python %s forward --origin test '
                      '-v view -s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: The -z/--zone-name flag is required.\n')
    output.close()
    output = os.popen('python %s reverse -z test_rev -t master --origin foo.com '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read().split(')')[1],
                     ' Invalid data type Hostname '
                     'for zone_origin: foo.com\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
