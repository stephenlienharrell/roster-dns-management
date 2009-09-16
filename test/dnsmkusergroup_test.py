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

"""Regression test for dnsmkusergroup

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

import fakeldap
import roster_core
import roster_server
from roster_user_tools import roster_client_lib


CONFIG_FILE = os.path.expanduser('~/.rosterrc') # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC = '../roster-user-tools/scripts/dnsmkusergroup'


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
                                                CERTFILE, ldap_module=fakeldap)
    self.daemon_instance.Serve(port=self.port)

class Testdnsmkusergroup(unittest.TestCase):

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

  def testMakeUserGroupUserGroupAssignments(self):
    output = os.popen('python %s -n new_user'
                      ' -a 128 -g cs -m'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(
        output.read(),
        'ADDED USER: username: new_user access_level: 128\n'
        'ADDED USER_GROUP_ASSIGNMENT: username: new_user group: cs\n')
    output.close()
    self.assertEqual(self.core_instance.ListUsers(),
                     {u'shuey': 64, u'new_user': 128, u'jcollins': 32,
                      u'sharrell': 128})
    self.assertEqual(self.core_instance.ListGroups(), [u'bio', u'cs', u'eas'])
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'new_user': [u'cs'],
                      u'sharrell': [u'cs']})

  def testMakeUserWithZone(self):
    self.core_instance.MakeZone(u'test_zone', u'master', u'here.')
    output = os.popen('python %s -n new_user'
                      ' -a 128 -g testgroup -m -z test_zone -f --access-right rw'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(
        output.read(),
        'ADDED GROUP: group: testgroup\n'
        'ADDED USER: username: new_user access_level: 128\n'
        'ADDED USER_GROUP_ASSIGNMENT: username: new_user group: testgroup\n'
        'ADDED FORWARD_ZONE_PERMISSION: zone_name: test_zone group: '
        'testgroup access_right: rw\n')
    output.close()
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [{'zone_name': u'bio.university.edu',
                                'access_right': u'rw'}],
                      u'testgroup': [{'zone_name': u'test_zone',
                                      'access_right': u'rw'}],
                      u'cs': [{'zone_name': u'cs.university.edu',
                                 'access_right': u'rw'},
                                {'zone_name': u'eas.university.edu',
                                 'access_right': u'r'}]})
    output = os.popen('python %s -n newuser'
                      ' -a 128 -g testgroup -m -z test_zone -b 192.168.1.4/30'
                      ' -r --access-right rw'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(
        output.read(),
        'ADDED USER: username: newuser access_level: 128\n'
        'ADDED USER_GROUP_ASSIGNMENT: username: newuser group: testgroup\n'
        'ADDED REVERSE_RANGE_PERMISSION: cidr_block: 192.168.1.4/30 '
        'group: testgroup access_right: rw\n')
    output.close()
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio':
                          [{'zone_name': u'192.168.0.0/24',
                            'access_right': u'r'},
                           {'zone_name': u'192.168.1.0/24',
                            'access_right': u'rw'}],
                      u'testgroup':
                          [{'zone_name': u'192.168.1.4/30',
                            'access_right': u'rw'}],
                      u'cs': [{'zone_name': u'192.168.0.0/24',
                                 'access_right': u'rw'}]})

  def testMakeZoneAssignments(self):
    self.core_instance.MakeGroup(u'test_group')
    self.core_instance.MakeZone(u'test_zone', u'master', u'here.')
    output = os.popen('python %s -z test_zone -r -b '
                      '192.168.1.0/24 -g test_group -m --access-right rw'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(
        output.read(),
        'ADDED REVERSE_RANGE_PERMISSION: cidr_block: 192.168.1.0/24 '
        'group: test_group access_right: rw\n')
    output.close()
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio':
                          [{'zone_name': u'192.168.0.0/24',
                            'access_right': u'r'},
                           {'zone_name': u'192.168.1.0/24',
                            'access_right': u'rw'}],
                      u'test_group':
                          [{'zone_name': u'192.168.1.0/24',
                            'access_right': u'rw'}],
                      u'cs':
                          [{'zone_name': u'192.168.0.0/24',
                            'access_right': u'rw'}]})

  def testMakeGroup(self):
    output = os.popen('python %s -g test_group'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(output.read(), 'ADDED GROUP: group: test_group\n')
    output.close()
    self.assertEqual(self.core_instance.ListGroups(), [u'bio', u'cs',
                                                       u'eas', u'test_group'])


  def testErrors(self):
    output = os.popen('python %s -n jcollins'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(output.read(), 'ERROR: A username must be accompanied by'
                                    ' a group name with the -g flag.\n')
    output.close()
    output = os.popen('python %s -n jcollins'
                      ' -g cs'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(output.read(), 'ERROR: A username must be accompanied by'
                                    ' an access level with the -a flag.\n')
    output.close()
    output = os.popen('python %s -n jcollins'
                      ' -a 128 -g cs'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(output.read(), 'ERROR: A username of that name already'
                                    ' exists.\n')
    output.close()
    output = os.popen('python %s -n newuser'
                      ' -a 128 -g fakegroup'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(output.read(), 'ERROR: Group does not exist, use the -m'
                                    ' flag to make this group.\n')
    output.close()
    self.core_instance.MakeZone(u'test_zone', u'master', u'here.')
    output = os.popen('python %s -n testuser'
                      ' -a 128 -g testgroup -m -z test_zone'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(output.read(), 'ERROR: A zone must be accompanied with'
                                    ' an access right, CIDR block or both.\n')
    output.close()
    output = os.popen('python %s -n testuser2'
                      ' -a 128 -g testgroup -m -z test_zone --access-right x'
                      ' -s %s -u %s -p %s' % (EXEC, self.server_name, USERNAME,
                                              PASSWORD))
    self.assertEqual(output.read(), 'ERROR: An access right of either rw|r '
                                    'is required if specifying a zone.\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
