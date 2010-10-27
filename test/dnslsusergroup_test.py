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

"""Regression test for dnslsusergroup

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
EXEC = '../roster-user-tools/scripts/dnslsusergroup'


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

class Testdnslsusergroup(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_thread = DaemonThread(self.config_instance, self.port)
    self.daemon_thread.daemon = True
    self.daemon_thread.start()
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testListUserGroupUserGroupAssignments(self):
    output = os.popen('python %s assignment -s %s -u %s -p %s '
                      '--config-file %s' % (
        EXEC, self.server_name, USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
                     'username groups\n'
                     '---------------\n'
                     'shuey    bio,cs\n'
                     'sharrell cs\n\n')
    output.close()
    output = os.popen('python %s assignment -n sharrell -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'username groups\n'
                                    '---------------\n'
                                    'sharrell cs\n\n')
    output.close()
    output = os.popen('python %s assignment -g cs -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'username groups\n'
                                    '---------------\n'
                                    'shuey    cs\n'
                                    'sharrell cs\n\n')
    output.close()

  def testListGroup(self):
    output = os.popen('python %s group -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'group\n'
                                    '-----\n'
                                    'bio\n'
                                    'cs\n'
                                    'eas\n\n')
    output.close()
    output = os.popen('python %s group -g eas -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'group\n'
                                    '-----\n'
                                    'eas\n\n')
    output.close()

  def testListUser(self):
    output = os.popen('python %s user -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'username         access_level\n'
                                    '-----------------------------\n'
                                    'shuey            64\n'
                                    'jcollins         32\n'
                                    'tree_export_user 0\n'
                                    'sharrell         128\n\n')
    output.close()
    output = os.popen('python %s user -n tree_export_user -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'username         access_level\n'
                                    '-----------------------------\n'
                                    'tree_export_user 0\n\n')
    output.close()
    output = os.popen('python %s user -a 128 -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'username access_level\n'
                                    '---------------------\n'
                                    'sharrell 128\n\n')
    output.close()

  def testListReverseRangePermissions(self):
    self.core_instance.MakeGroup(u'group1')
    self.core_instance.MakeReverseRangePermission(u'10/8', u'group1', u'r')
    output = os.popen('python %s reverse -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(),
                     'group  cidr_block     access_right\n'
                     '----------------------------------\n'
                     'cs     192.168.0.0/24 rw\n'
                     'bio    192.168.0.0/24 r\n'
                     'bio    192.168.1.0/24 rw\n'
                     'group1 10/8           r\n\n')
    output.close()
    output = os.popen('python %s reverse -g bio -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(),
                     'group cidr_block     access_right\n'
                     '---------------------------------\n'
                     'bio   192.168.0.0/24 r\n'
                     'bio   192.168.1.0/24 rw\n\n')
    output.close()
    output = os.popen('python %s reverse --cidr-block 192.168.0.0/24 -s %s '
                      '-u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(),
                     'group cidr_block     access_right\n'
                     '---------------------------------\n'
                     'cs    192.168.0.0/24 rw\n'
                     'bio   192.168.0.0/24 r\n\n')
    output.close()
    output = os.popen('python %s reverse --access-right r -s %s -u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(),
                     'group  cidr_block     access_right\n'
                     '----------------------------------\n'
                     'bio    192.168.0.0/24 r\n'
                     'group1 10/8           r\n\n')
    output.close()

  def testForwardZonePermission(self):
    output = os.popen('python %s forward -s %s '
                      '-u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'group zone_name          access_right\n'
                                    '-------------------------------------\n'
                                    'cs    cs.university.edu  rw\n'
                                    'cs    eas.university.edu r\n'
                                    'bio   bio.university.edu rw\n\n')
    output.close()
    output = os.popen('python %s forward -g bio -s %s '
                      '-u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'group zone_name          access_right\n'
                                    '-------------------------------------\n'
                                    'bio   bio.university.edu rw\n\n')
    output.close()
    output = os.popen('python %s forward -z bio.university.edu -s %s '
                      '-u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'group zone_name          access_right\n'
                                    '-------------------------------------\n'
                                    'bio   bio.university.edu rw\n\n')
    output.close()
    output = os.popen('python %s forward --access-right rw -s %s '
                      '-u %s -p %s '
                      '--config-file %s' % (
                          EXEC, self.server_name, USERNAME, PASSWORD,
                          USER_CONFIG))
    self.assertEqual(output.read(), 'group zone_name          access_right\n'
                                    '-------------------------------------\n'
                                    'cs    cs.university.edu  rw\n'
                                    'bio   bio.university.edu rw\n\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
