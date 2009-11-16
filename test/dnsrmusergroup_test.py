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

"""Regression test for dnsrmusergroup

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.6'


import os
import sys
import socket
import threading
import time
import getpass

import unittest
sys.path.append('../')

import roster_core
from roster_user_tools import roster_client_lib
import roster_server

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
EXEC = '../roster-user-tools/scripts/dnsrmusergroup'

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

class Testdnsrmusergroup(unittest.TestCase):

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

  def testRemoveUserGroupUserGroupAssignments(self):
    self.assertEqual(self.core_instance.ListUsers(),
                     {u'shuey': 64, u'jcollins': 32, u'sharrell': 128})
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'sharrell': [u'cs']})
    output = os.popen('python %s -n shuey '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'REMOVED USER: shuey\n')
    output.close()
    self.assertEqual(self.core_instance.ListUsers(),
                     {u'jcollins': 32, u'sharrell': 128})
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'sharrell': [u'cs']})
    output = os.popen('python %s -g cs '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'REMOVED GROUP: cs\n')
    output.close()
    self.assertEqual(self.core_instance.ListUsers(),
                     {u'jcollins': 32, u'sharrell': 128})
    self.assertEqual(self.core_instance.ListUserGroupAssignments(), {})

  def testRemovePermissions(self):
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [{'zone_name': u'bio.university.edu',
                                'access_right': u'rw'}],
                      u'cs': [{'zone_name': u'cs.university.edu',
                                 'access_right': u'rw'},
                                {'zone_name': u'eas.university.edu',
                                 'access_right': u'r'}]})
    output = os.popen('python %s -g '
                      '--forward-zone-permission -z bio.university.edu -g bio '
                      '--access-right rw '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'REMOVED GROUP: bio\n')
    output.close()
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'cs': [{'zone_name': u'cs.university.edu',
                                 'access_right': u'rw'},
                                {'zone_name': u'eas.university.edu',
                                 'access_right': u'r'}]})
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'cs': [{'zone_name': u'192.168.0.0/24',
                                 'access_right': u'rw'}]})
    output = os.popen('python %s '
                      '--reverse-range-permission --cidr-block 192.168.0.0/24 '
                      '-g cs --access-right rw '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'REMOVED REVERSE_RANGE_PERMISSION: cidr_block: '
                     '192.168.0.0/24 group: cs access_right: rw\n')
    output.close()
    self.assertEqual(self.core_instance.ListReverseRangePermissions(), {})

  def testListUsers(self):
    output = os.popen('python %s -l '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),'shuey    bio,cs 64\n'
                                   'jcollins --     32\n'
                                   'sharrell cs     128\n\n')
    output.close()
    output = os.popen('python %s -l -n shuey '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'shuey cs,bio 64\n\n')
    output.close()

  def testErrors(self):
    output = os.popen('python %s -n shuey '
                      '-g test_group_error '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: The -g/--group flag cannot '
                                    'be used.\n')
    output.close()
    output = os.popen('python %s -f forward '
                      '-r test_reverse_error '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -r/--reverse-range-permission '
        'flag cannot be used.\n')
    output.close()
    output = os.popen('python %s -f forward '
                      '-n test_user_name_error '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -f/--forward-zone-permission flag cannot be used.\n')
    output.close()
    output = os.popen('python %s -f forward '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: An access right must be specified '
        'with the --access-right flag.\n')
    output.close()
    output = os.popen('python %s -f forward '
                      '--access-right access_right '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: A group must be specified '
                                    'with the -g flag.\n')
    output.close()
    output = os.popen('python %s -f forward '
                      '--access-right access_right -g test_group '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: An access right of either rw|r is required.\n')
    output.close()
    output = os.popen('python %s -f forward '
                      '--access-right rw -g test_group '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: A zone must be specified with the -z flag.\n')
    output.close()
    output = os.popen('python %s -r reverse '
                      '-n test_user_name_error '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -r/--reverse-range-permission '
        'flag cannot be used.\n')
    output.close()
    output = os.popen('python %s -r reverse '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: A CIDR block must be specified '
        'with the --cidr-block flag.\n')
    output.close()
    output = os.popen('python %s -r reverse '
                      '--cidr-block 192.168.0.0/24 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: A group must be specified '
                                    'with the -g flag.\n')
    output.close()
    output = os.popen('python %s -r reverse '
                      '--cidr-block 192.168.0.0/24 '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: A group must be specified '
                                    'with the -g flag.\n')
    output.close()
    output = os.popen('python %s -r reverse '
                      '--cidr-block 192.168.0.0/24 -g test_group '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: An access right must be specified '
        'with the --access-right flag.\n')
    output.close()
    output = os.popen('python %s -r reverse '
                      '--cidr-block 192.168.0.0/24 -g test_group '
                      '--access-right fake_access_right '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: An access right of either rw|r is required.\n')
    output.close()
    output = os.popen('python %s '
                      '-s %s -u %s -p %s --config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'Usage: dnsrmusergroup [options]\n'
                     '\nOptions:\n'
                     '  --version             show program\'s version number '
                     'and exit\n'
                     '  -h, --help            show this help message and exit\n'
                     '  -l, --list            List users, apply -u flag to'
                     ' filter.\n'
                     '  -n <new-user>, --user-name=<new-user>\n'
                     '                        String of the user to remove.\n'
                     '  -g <group>, --group=<group>\n'
                     '                        String of the group name to'
                     ' remove.\n'
                     '  -f, --forward-zone-permission\n'
                     '                        Make a forward zone permission.\n'
                     '  -r, --reverse-range-permission\n'
                     '                        Make a reverse range '
                     'permission.\n'
                     '  -z <zone>, --zone=<zone>\n'
                     '                        String of the zone name '
                     '(optional)\n'
                     '  --access-right=r|rw   String of the access right'
                     ' (r/rw)\n'
                     '  -b <cidr-block>, --cidr-block=<cidr-block>\n'
                     '                        String of CIDR block.\n'
                     '  -s <server>, --server=<server>\n'
                     '                        XML RPC Server address.\n'
                     '  --config-file=<file>  Config file location.\n'
                     '  -u <username>, --username=<username>\n'
                     '                        Run as a different username.\n'
                     '  -p <password>, --password=<password>\n'
                     '                        Password string, NOTE: It is'
                     ' insecure to use this flag\n'
                     '                        on the command line.\n'
                     '  -c <cred-file>, --cred-file=<cred-file>\n'
                     '                        Location of credential file.\n'
                     '  --cred-string=<cred-string>\n'
                     '                        String of credential.\n'
                     '  -q, --quiet           Suppress program output.\n'
                     'CLIENT ERROR: Need to specify an option.\n')
    output.close()


if( __name__ == '__main__' ):
      unittest.main()
