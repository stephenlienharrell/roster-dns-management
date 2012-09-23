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

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'

"""Tests Roster Server's SetCoreDirty functionality, as well as the ability to
group permissions on the fly, without restarting Roster."""

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
USER_TOOLS_DIR = '../roster-user-tools/scripts'

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

class TestSetCoreDirty(unittest.TestCase):

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

    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testCoreDirty(self):

    command = os.popen('python %s/dnsmkacl acl -a test_acl '
                       '--cidr-block=192.168.0.0/24 '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    self.assertEqual(command.read(),
        'ADDED ACL: acl: test_acl cidr_block: 192.168.0.0/24\n')
    command.close()

    command = os.popen('python %s/dnsmkview view -v test_view -a test_acl '
                       '--allow '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    self.assertEqual(command.read(),
        'ADDED VIEW: view_name: test_view options None\nADDED VIEW ACL ASSIGNMENT: view: test_view acl: test_acl allowed: 1\n')
    command.close()

    
    command = os.popen('python %s/dnsmkzone forward -z test_zone -v test_view '
                       '--origin=university.edu. -t master '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    self.assertEqual(command.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone zone_type: master zone_origin: university.edu. zone_options: None view_name: test_view\n')
    command.close()

    command = os.popen('python %s/dnsmkrecord soa '
                       '--admin-email=admin.university.edu. --expiry-seconds=3600 '
                       '--name-server=ns.university.edu. --retry-seconds=3600 '
                       '--refresh-seconds=3600 -v test_view -z test_zone '
                       '--minimum-seconds=3600 --serial-number=123 '
                       '-t university.edu '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    self.assertEqual(command.read(),
        'ADDED SOA: university.edu zone_name: test_zone view_name: test_view ttl: 3600\n'
        '    refresh_seconds: 3600 expiry_seconds: 3600 name_server: ns.university.edu. minimum_seconds: 3600 retry_seconds: 3600 serial_number: 123 admin_email: admin.university.edu.\n')
    command.close()
    
    #command = os.popen('python %s/dnsmkusergroup user -n jcollins -a 32 '
    #                   '-u %s -p %s -s %s' % (
    #                   USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    #self.assertEqual(command.read(),
    #    'ADDED USER: username: jcollins access_level: 32\n')
    #command.close()

    command = os.popen('python %s/dnsmkusergroup group -g test_group '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    self.assertEqual(command.read(),
         'ADDED GROUP: group: test_group\n')
    command.close()

    command = os.popen('python %s/dnsmkusergroup assignment -n jcollins '
                       ' -g test_group '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    self.assertEqual(command.read(),
        'ADDED USER_GROUP_ASSIGNMENT: username: jcollins group: test_group\n')
    command.close()

    command = os.popen('python %s/dnsmkusergroup forward -z test_zone '
                       ' -g test_group --group-permission=txt '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    self.assertEqual(command.read(),
        "ADDED FORWARD_ZONE_PERMISSION: zone_name: test_zone group: test_group group_permission: ['txt']\n")
    command.close()

    command = os.popen('python %s/dnsmkrecord txt -t txt_target1 -z test_zone '
                       '--quoted-text="this is text1" '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, 'jcollins', 'test', self.server_name))
    #Since the group permissions allow jcollins to create a txt record, he does.
    self.assertEqual(command.read(),
        'ADDED TXT: txt_target1 zone_name: test_zone view_name: any ttl: 3600\n'
        '    quoted_text: this is text1\n')
    command.close()

    #This is the core instance that will be used in the next command.
    #Once the permissions are updated, this core_instance will be dirty,
    #and replaced with a new one.
    old_core_instance = self.daemon_thread.daemon_instance.GetCoreInstance(
        u'sharrell')

    command = os.popen('python %s/dnsupusergroup forward -z test_zone '
                       '-g test_group --group-permission=a,aaaa '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, USERNAME, PASSWORD, self.server_name))
    #Changing the permissions to not allow jcollins to create a txt record.
    self.assertEqual(command.read(), '')
    command.close()

    new_core_instance = self.daemon_thread.daemon_instance.GetCoreInstance(
        u'sharrell')

    self.assertTrue(old_core_instance.dirty)
    self.assertFalse(new_core_instance.dirty)
    self.assertTrue(old_core_instance != new_core_instance)

    command = os.popen('python %s/dnsmkrecord txt -t txt_target2 -z test_zone '
                       '--quoted-text="this is text2" '
                       '-u %s -p %s -s %s' % (
                       USER_TOOLS_DIR, 'jcollins', 'test', self.server_name))
    #Permissions were successfully reloaded
    self.assertEqual(command.read(),
        'USER ERROR: User jcollins is not allowed to use MakeRecord with txt_target2 on test_zone of type txt\n')
    command.close()

if( __name__ == '__main__' ):
    unittest.main()
