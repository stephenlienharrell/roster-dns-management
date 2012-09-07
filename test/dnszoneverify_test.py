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

"""Regression test for dnszoneverify

Make sure you are running this against a database that can be destroyed.

In order to restart bind for this unittest on Ubuntu, make sure
/etc/apparmor.d/usr/sbin/named has permission to your roster test directory
I added "/home/dcfritz/** r," under the "/usr/sbin/named {" section

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.

This test needs apparmor and selinux either disabled or reconfigured

This test requires BIND 9.9
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import getpass
import os
import sys
import shutil
import socket
import time
import unittest
from fabric import api as fabric_api
from fabric import network as fabric_network
from fabric import state as fabric_state

import roster_core
from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf'
CONFIG_SYNC_EXEC = '../roster-config-manager/scripts/dnsconfigsync'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
ZONE_VERIFY_EXEC='../roster-config-manager/scripts/dnszoneverify'
KEY_FILE = 'test_data/rndc.key'
RNDC_CONF_FILE = 'test_data/rndc.conf'
USERNAME = u'sharrell'
TESTDIR = u'%s/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/named/' % os.getcwd()
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
SSH_ID = 'test_data/roster_id_dsa'
SSH_USER = unicode(getpass.getuser())
TEST_DNS_SERVER = u'localhost'
NS_IP_ADDRESS = '127.0.0.1'
NS_DOMAIN = '' #Blank since using localhost
NAMEDPID_FILE = '/var/run/named/named.pid'
SESSION_KEYFILE = 'test_data/session.key'
RNDC_CONF_DATA = ('# Start of rndc.conf\n'
                  'key "rndc-key" {\n'
                  '    algorithm hmac-md5;\n'
                  '      secret "yTB86M+Ai8vKJYGYo2ossQ==";\n'
                  '};\n\n'
                  'options {\n'
                  '    default-key "rndc-key";\n'
                  '      default-server 127.0.0.1;\n'
                  '};\n')
RNDC_KEY_DATA = ('key "rndc-key" {\n'
                 '   algorithm hmac-md5;\n'
                 '   secret "yTB86M+Ai8vKJYGYo2ossQ==";\n'
                 ' };')
RNDC_CONF = 'test_data/rndc.conf'
RNDC_KEY = 'test_data/rndc.key'

class TestZoneVerify(unittest.TestCase):
  def setUp(self):
    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((TEST_DNS_SERVER, 0))
      addr, port = s.getsockname()
      s.close()
      return port
    self.port = PickUnusedPort()
    self.rndc_port = PickUnusedPort()
    while( self.rndc_port == self.port ):
      self.rndc_port = PickUnusedPort()

    rndc_key = open(RNDC_KEY, 'w')
    rndc_key.write(RNDC_KEY_DATA)
    rndc_key.close()
    rndc_conf = open(RNDC_CONF, 'w')
    rndc_conf.write(RNDC_CONF_DATA)
    rndc_conf.close()

    fabric_api.env.warn_only = True
    fabric_state.output['everything'] = False
    fabric_state.output['warnings'] = False
    fabric_api.env.host_string = "%s@%s" % (SSH_USER, TEST_DNS_SERVER)

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()
    db_instance.CreateRosterDatabase()

    self.bind_config_dir = os.path.expanduser(
        self.config_instance.config_file['exporter']['root_config_dir'])
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)

    self.named_dir = os.path.expanduser(
        self.config_instance.config_file['exporter']['named_dir'])
    self.lockfile = self.config_instance.config_file[
        'server']['lock_file']

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()
    self.db_instance = db_instance

    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')

  def tearDown(self):
    fabric_api.local('killall named', capture=True)
    fabric_network.disconnect_all()
    time.sleep(1) # Wait for disk to settle
    if( os.path.exists('%s/named' % self.named_dir) ):
      shutil.rmtree('%s/named' % self.named_dir)
    if( os.path.exists('%s/named.conf' % self.named_dir) ):
      os.remove('%s/named.conf' % self.named_dir)
    if( os.path.exists('backup') ):
      shutil.rmtree('backup')
    if( os.path.exists('test_data/backup_dir') ):
      shutil.rmtree('test_data/backup_dir')
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)

  def testZoneVerify(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'sub.university.lcl.', view_name=u'test_view')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'0.168.192.in-addr.arpa.', view_name=u'test_view')
    self.core_instance.MakeZone(u'reverse_ipv6_zone', u'master',
                                u'8.0.e.f.f.3.ip6.arpa.', view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_zone.db '
                      '--view test_view -u %s --config-file %s '
                      '-z forward_zone' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone.db\n'
                     '17 records loaded from zone test_data/test_zone.db\n'
                     '17 total records added\n')
    output.close()
    output = os.popen('python %s -f test_data/test_reverse_zone.db '
                      '--view test_view -u %s --config-file %s '
                      '-z reverse_zone' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_reverse_zone.db\n'
                     '6 records loaded from zone '
                     'test_data/test_reverse_zone.db\n'
                     '6 total records added\n')
    output.close()
    output = os.popen('python %s -f test_data/test_reverse_ipv6_zone.db '
                      '--view test_view -u %s --config-file %s '
                      '-z reverse_ipv6_zone' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_reverse_ipv6_zone.db\n'
                     '5 records loaded from zone '
                     'test_data/test_reverse_ipv6_zone.db\n'
                     '5 total records added\n')
    output.close()

    self.core_instance.MakeDnsServer(TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', u'set1')
    self.core_instance.MakeNamedConfGlobalOption(
        u'set1', u'include "%s/test_data/rndc.key"; options { pid-file "test_data/named.pid";};\n'
        'controls { inet 127.0.0.1 port %d allow{localhost;} keys {rndc-key;};};' % (os.getcwd(), self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'any', 1)
    self.tree_exporter_instance.ExportAllBindTrees()
    # Copy blank named.conf to start named with
    shutil.copyfile('test_data/named.blank.conf', '%s/named.conf' % self.named_dir)
    named_file_contents = open('%s/named.conf' % self.named_dir, 'r').read()
    named_file_contents = named_file_contents.replace('RNDC_KEY', '%s/test_data/rndc.key' % os.getcwd())
    named_file_contents = named_file_contents.replace('NAMED_DIR', '%s/test_data/named' % os.getcwd())
    named_file_contents = named_file_contents.replace('NAMED_PID', '%s/test_data/named.pid' % os.getcwd())
    named_file_contents = named_file_contents.replace('RNDC_PORT', str(self.rndc_port))
    named_file_contents = named_file_contents.replace('SESSION_KEYFILE', '%s/%s' % (os.getcwd(), str(SESSION_KEYFILE)))
    named_file_handle = open('%s/named.conf' % self.named_dir, 'w')
    named_file_handle.write(named_file_contents)
    named_file_handle.close()
    named_file_contents = open('%s/named.conf' % self.named_dir, 'r').read()
    # Start named
    out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %s/named.conf' % (
        self.port, SSH_USER, self.named_dir), capture=True)
    time.sleep(2)

    command = os.popen(
        'python %s --rndc-key test_data/rndc.key --rndc-port %s -u %s '
        '--ssh-id %s --config-file %s --rndc-port %s' % (
            CONFIG_SYNC_EXEC, self.rndc_port, SSH_USER, SSH_ID, 
            CONFIG_FILE, self.rndc_port))
    lines = command.read().split('\n')
    # These lines will likely need changed depending on implementation
    self.assertTrue('Connecting to "%s"' % TEST_DNS_SERVER in lines)
    self.assertTrue('[%s@%s] out: server reload successful\r' % (
        SSH_USER, TEST_DNS_SERVER) in lines)
    self.assertTrue('Disconnecting from %s... done.' % (
            TEST_DNS_SERVER) in lines)
    command.close()
 
    #Checking output of dnszoneverify
    command = os.popen('python %s -f test_data/test_zone.db '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER, 
                                        self.port))
    self.assertEqual(command.read(), 
                     'Able to verify 15 records.\nUnable to verify 0 records.\n')
    command.close()
    command = os.popen('python %s -f test_data/test_reverse_zone.db '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER, 
                                        self.port))
    self.assertEqual(command.read(), 
                     'Able to verify 5 records.\nUnable to verify 0 records.\n')
    command.close()
    command = os.popen('python %s -f test_data/test_reverse_ipv6_zone.db '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER, 
                                        self.port))
    self.assertEqual(command.read(), 
                     'Able to verify 4 records.\nUnable to verify 0 records.\n')
    command.close()

  def testErrors(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'reverse_ipv6_zone', u'master',
                                u'8.0.e.f.f.3.ip6.arpa.', view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_reverse_ipv6_zone.db '
                      '--view test_view -u %s --config-file %s '
                      '-z reverse_ipv6_zone' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_reverse_ipv6_zone.db\n'
                     '5 records loaded from zone '
                     'test_data/test_reverse_ipv6_zone.db\n'
                     '5 total records added\n')
    output.close()

    self.core_instance.MakeDnsServer(TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', u'set1')
    self.core_instance.MakeNamedConfGlobalOption(
        u'set1', u'include "%s/test_data/rndc.key"; options { pid-file "test_data/named.pid";};\n'
        'controls { inet 127.0.0.1 port %d allow{localhost;} keys {rndc-key;};};' % (os.getcwd(), self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'any', 1)
    self.tree_exporter_instance.ExportAllBindTrees()
    # Copy blank named.conf to start named with
    shutil.copyfile('test_data/named.blank.conf', '%s/named.conf' % self.named_dir)
    named_file_contents = open('%s/named.conf' % self.named_dir, 'r').read()
    named_file_contents = named_file_contents.replace('RNDC_KEY', '%s/test_data/rndc.key' % os.getcwd())
    named_file_contents = named_file_contents.replace('NAMED_DIR', '%s/test_data/named' % os.getcwd())
    named_file_contents = named_file_contents.replace('NAMED_PID', '%s/test_data/named.pid' % os.getcwd())
    named_file_contents = named_file_contents.replace('RNDC_PORT', str(self.rndc_port))
    named_file_contents = named_file_contents.replace('SESSION_KEYFILE', '%s/%s' % (os.getcwd(), str(SESSION_KEYFILE)))
    named_file_handle = open('%s/named.conf' % self.named_dir, 'w')
    named_file_handle.write(named_file_contents)
    named_file_handle.close()
    named_file_contents = open('%s/named.conf' % self.named_dir, 'r').read()
    # Start named
    out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %s/named.conf' % (
        self.port, SSH_USER, self.named_dir), capture=True)
    time.sleep(2)

    command = os.popen(
        'python %s --rndc-key test_data/rndc.key --rndc-port %s -u %s '
        '--ssh-id %s --config-file %s --rndc-port %s' % (
            CONFIG_SYNC_EXEC, self.rndc_port, SSH_USER, SSH_ID, 
            CONFIG_FILE, self.rndc_port))
    lines = command.read().split('\n')
    # These lines will likely need changed depending on implementation
    self.assertTrue('Connecting to "%s"' % TEST_DNS_SERVER in lines)
    self.assertTrue('[%s@%s] out: server reload successful\r' % (
        SSH_USER, TEST_DNS_SERVER) in lines)
    self.assertTrue('Disconnecting from %s... done.' % (
            TEST_DNS_SERVER) in lines)
    command.close()

    command = os.popen('python %s -f test_data/test_zone.db '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER, 
                                        self.port))
    self.assertEqual(command.read(),
        'Able to verify 0 records.\n'
        'Unable to verify 15 records.\n'
        '\n'
        'Unverifiable records:\n'
        'sub.university.lcl. IN SOA ns.university.lcl. hostmaster.ns.university.lcl. 794 10800 3600 3600000 86400\n'
        'sub.university.lcl. IN NS ns2.sub.university.lcl.\n'
        'sub.university.lcl. IN MX 20 mail2.sub.university.lcl.\n'
        'sub.university.lcl. IN TXT "Contact 1:  Stephen Harrell (sharrell@university.lcl)"\n'
        'sub.university.lcl. IN A 192.168.0.1\n'
        'ns.sub.university.lcl. IN A 192.168.1.103\n'
        'desktop-1.sub.university.lcl. IN AAAA 3ffe:800::2a8:79ff:fe32:1982\n'
        'desktop-1.sub.university.lcl. IN A 192.168.1.100\n'
        'ns2.sub.university.lcl. IN A 192.168.1.104\n'
        'ns2.sub.university.lcl. IN HINFO "PC" "NT"\n'
        'www.sub.university.lcl. IN CNAME sub.university.lcl.\n'
        'localhost.sub.university.lcl. IN A 127.0.0.1\n'
        'www.data.sub.university.lcl. IN CNAME ns.university.lcl.\n'
        'mail1.sub.university.lcl. IN A 192.168.1.101\n'
        'mail2.sub.university.lcl. IN A 192.168.1.102\n')
    command.close()

    command = os.popen('python %s -f test_data/test_reverse_zone.db '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER, 
                                        self.port))
    self.assertEqual(command.read(),
        'Able to verify 0 records.\n'
        'Unable to verify 5 records.\n'
        '\n'
        'Unverifiable records:\n'
        '0.168.192.in-addr.arpa. IN SOA ns.university.lcl. hostmaster.university.lcl. 4 10800 3600 3600000 86400\n'
        '0.168.192.in-addr.arpa. IN NS ns2.university.lcl.\n'
        '1.0.168.192.in-addr.arpa. IN PTR router.university.lcl.\n'
        '11.0.168.192.in-addr.arpa. IN PTR desktop-1.university.lcl.\n'
        '12.0.168.192.in-addr.arpa. IN PTR desktop-2.university.lcl.\n')
    command.close()
    command = os.popen('python %s -f test_data/test_reverse_ipv6_zone.db '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER, 
                                        self.port))
    self.assertEqual(command.read(), 
                     'Able to verify 4 records.\nUnable to verify 0 records.\n')
    command.close()

    command = os.popen('python %s -f test_data/no_zone.db '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER,
                                        self.port))
    self.assertEqual(command.read(),
        "Unable to read file test_data/no_zone.db: "
        "[Errno 2] No such file or directory: 'test_data/no_zone.db'\n")
    command.close()

    command = os.popen('python %s -f test_data/test_zone.db '
                       '-p %s' % (ZONE_VERIFY_EXEC, self.port))
    self.assertEqual(command.read(),
                     'Must specify -s/--server flag.\n')
    command.close()

    command = os.popen('python %s '
                       '-s %s -p %s' % (ZONE_VERIFY_EXEC, TEST_DNS_SERVER,
                       self.port))
    self.assertEqual(command.read(),
        'Must specify -f/--file flag.\n')
    command.close()

if( __name__ == '__main__' ):
      unittest.main()
