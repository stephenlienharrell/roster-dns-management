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

"""Regression test for dnsquerycheck

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
from roster_config_manager import config_lib

CONFIG_FILE = 'test_data/roster.conf'
CONFIG_SYNC_EXEC = '../roster-config-manager/scripts/dnsconfigsync'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
QUERY_CHECK_EXEC='../roster-config-manager/scripts/dnsquerycheck'
SERVER_CHECK_EXEC='../roster-config-manager/scripts/dnsservercheck'
KEY_FILE = 'test_data/rndc.key'
RNDC_CONF_FILE = 'test_data/rndc.conf'
USERNAME = u'sharrell'
TESTDIR = u'%s/test_data/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/bind_dir/' % os.getcwd()
NAMED_DIR = '%s/test_data/bind_dir/named'  % os.getcwd()
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

class TestQueryCheck(unittest.TestCase):
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

    if( not os.path.exists(BINDDIR) ):
      os.mkdir(BINDDIR)
    if( not os.path.exists(NAMED_DIR) ):
      os.mkdir(NAMED_DIR)
    if( not os.path.exists(TESTDIR) ):
      os.mkdir(TESTDIR)

  def tearDown(self):
    fabric_api.local('killall named', capture=True)
    fabric_network.disconnect_all()
    time.sleep(1) # Wait for disk to settle
    if( os.path.exists('backup') ):
      shutil.rmtree('backup')
    if( os.path.exists('test_data/backup_dir') ):
      shutil.rmtree('test_data/backup_dir')
    if( os.path.exists('root_config_dir') ):
      shutil.rmtree('root_config_dir')
    #Clearing unittest_dir to empty directory
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)

    if( os.path.exists(BINDDIR) ):
      shutil.rmtree(BINDDIR)
    if( os.path.exists(NAMED_DIR) ):
      shutil.rmtree(NAMED_DIR)
    if( os.path.exists(TESTDIR) ):
      shutil.rmtree(TESTDIR)

  def testErrors(self):
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
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(
        u'set1', u'include "%s/test_data/rndc.key"; options { pid-file "test_data/named.pid";};\n'
        'controls { inet 127.0.0.1 port %d allow{localhost;} keys {rndc-key;};};' % (os.getcwd(), self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'set1',
                                                u'any', 1)
    self.tree_exporter_instance.ExportAllBindTrees()

    # Copy blank named.conf to start named with
    shutil.copyfile('test_data/named.blank.conf', 
                    os.path.join(BINDDIR, 'named.conf'))
    named_file_contents = open(os.path.join(BINDDIR, 'named.conf')).read()
    named_file_contents = named_file_contents.replace('RNDC_KEY', '%s/test_data/rndc.key' % os.getcwd())
    named_file_contents = named_file_contents.replace('NAMED_DIR', NAMED_DIR)
    named_file_contents = named_file_contents.replace('NAMED_PID', '%s/test_data/named.pid' % os.getcwd())
    named_file_contents = named_file_contents.replace('RNDC_PORT', str(self.rndc_port))
    named_file_contents = named_file_contents.replace('SESSION_KEYFILE', '%s/%s' % (os.getcwd(), str(SESSION_KEYFILE)))
    named_file_handle = open('%s/named.conf' % BINDDIR, 'w')
    named_file_handle.write(named_file_contents)
    named_file_handle.close()

    # Start named
    out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %snamed.conf' % (
        self.port, SSH_USER, BINDDIR), capture=True)
    time.sleep(2)

    # Running dnsservercheck
    command = os.popen('python %s --config-file %s -i 17 -d %s' % (
        SERVER_CHECK_EXEC, CONFIG_FILE, TEST_DNS_SERVER))
    output = command.read()
    command.close()
    self.assertEqual(output, '')

    # Running dnsconfisync
    command = os.popen(
        'python %s -d localhost --config-file %s -i 17 '
        '--rndc-key %s --rndc-conf %s --rndc-port %s' % (
            CONFIG_SYNC_EXEC, CONFIG_FILE, RNDC_KEY, RNDC_CONF, self.rndc_port))
    output = command.read()
    command.close()
    self.assertEqual(output, '')

    #Messing with the zone files so that dnsquerycheck will not pass
    config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)
    config_lib_instance.UnTarDnsTree()
    zone_dir = 'root_config_dir/%s/named/test_view' % TEST_DNS_SERVER
    for zone_file_name in os.listdir(zone_dir):
      zone_file_path = os.path.join(zone_dir, zone_file_name)

      zone_file_handle = open(zone_file_path, 'r')
      zone_file_string = zone_file_handle.read()
      zone_file_string = zone_file_string.replace('.lcl', '.lol')
      zone_file_handle.close()

      zone_file_handle = open(zone_file_path, 'w')
      zone_file_handle.write(zone_file_string)
      zone_file_handle.close()

    config_lib_instance.TarDnsTree(17)

    # Running dnsquerycheck
    command = os.popen(
        'python %s -s %s -c %s -p %s -i 17' % (
        QUERY_CHECK_EXEC, TEST_DNS_SERVER, CONFIG_FILE, self.port))
    output = command.read()
    command.close()
    self.assertEqual(output, 
        'Zone reverse_ipv6_zone does not appear to be online '
        'for server localhost\n'
        'Zone reverse_zone does not appear to be online '
        'for server localhost\n'
        'Zone forward_zone does not appear to be online '
        'for server localhost\n')

    command = os.popen(
        'python %s -s %s -p %s -f no_file' % (
        QUERY_CHECK_EXEC, TEST_DNS_SERVER, self.port))
    output = command.read()
    command.close()
    self.assertEqual(output, 
        'Unable to open zone file no_file\n'
        'Zone no_file does not appear to be online for server localhost\n')

  def testQueryCheck(self):
    self.core_instance.MakeView(u'test_view1')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'sub.university.lcl.', view_name=u'test_view1')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'0.168.192.in-addr.arpa.', view_name=u'test_view1')
    self.core_instance.MakeZone(u'reverse_ipv6_zone', u'master',
                                u'8.0.e.f.f.3.ip6.arpa.', view_name=u'test_view1')
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_zone.db '
                      '--view test_view1 -u %s --config-file %s '
                      '-z forward_zone' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone.db\n'
                     '17 records loaded from zone test_data/test_zone.db\n'
                     '17 total records added\n')
    output.close()
    output = os.popen('python %s -f test_data/test_reverse_zone.db '
                      '--view test_view1 -u %s --config-file %s '
                      '-z reverse_zone' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_reverse_zone.db\n'
                     '6 records loaded from zone '
                     'test_data/test_reverse_zone.db\n'
                     '6 total records added\n')
    output.close()
    output = os.popen('python %s -f test_data/test_reverse_ipv6_zone.db '
                      '--view test_view1 -u %s --config-file %s '
                      '-z reverse_ipv6_zone' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_reverse_ipv6_zone.db\n'
                     '5 records loaded from zone '
                     'test_data/test_reverse_ipv6_zone.db\n'
                     '5 total records added\n')
    output.close()

    named_conf_global_options_string = (
        u'include "%s/test_data/rndc.key";\n'
        u'options {\n'
        u'\tpid-file "test_data/named.pid";\n'
        u'\tsession-keyfile "%s";\n'
        u'};\n'
        u'controls { inet 127.0.0.1 port %d allow { localhost; } '
        u'keys { rndc-key; }; };\n') % (os.getcwd(), SESSION_KEYFILE, self.rndc_port)

    self.core_instance.MakeDnsServer(TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view1', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', named_conf_global_options_string)
    self.core_instance.MakeViewToACLAssignments(u'test_view1', u'set1',
                                                u'any', 1)
    self.tree_exporter_instance.ExportAllBindTrees()

    # Copy blank named.conf to start named with
    shutil.copyfile('test_data/named.blank.conf', 
                    os.path.join(BINDDIR, 'named.conf'))
    named_file_contents = open(os.path.join(BINDDIR, 'named.conf')).read()
    named_file_contents = named_file_contents.replace('RNDC_KEY', '%s/test_data/rndc.key' % os.getcwd())
    named_file_contents = named_file_contents.replace('NAMED_DIR', NAMED_DIR)
    named_file_contents = named_file_contents.replace('NAMED_PID', '%s/test_data/named.pid' % os.getcwd())
    named_file_contents = named_file_contents.replace('RNDC_PORT', str(self.rndc_port))
    named_file_contents = named_file_contents.replace('SESSION_KEYFILE', '%s/%s' % (os.getcwd(), str(SESSION_KEYFILE)))
    named_file_handle = open('%s/named.conf' % BINDDIR, 'w')
    named_file_handle.write(named_file_contents)
    named_file_handle.close()

    # Start named
    out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %snamed.conf' % (
        self.port, SSH_USER, BINDDIR), capture=True)
    time.sleep(2)

    # Running dnsservercheck
    command = os.popen('python %s --config-file %s -i 17 -d %s' % (
        SERVER_CHECK_EXEC, CONFIG_FILE, TEST_DNS_SERVER))
    output = command.read()
    command.close()
    self.assertEqual(output, '')

    # Running dnsconfigsync
    command = os.popen(
        'python %s -d localhost --config-file %s -i 17 '
        '--rndc-key %s --rndc-conf %s --rndc-port %s' % (
            CONFIG_SYNC_EXEC, CONFIG_FILE, RNDC_KEY, RNDC_CONF, self.rndc_port))
    output = command.read()
    command.close()
    self.assertEqual(output, '')
    
    # Running dnsquerycheck with audit log
    command = os.popen(
        'python %s -s %s -c %s -p %s -i 17 ' % (
        QUERY_CHECK_EXEC, TEST_DNS_SERVER, CONFIG_FILE, self.port))
    output = command.read()
    command.close()
    self.assertEqual(output, '')

    # Running dnsquerycheck with the view flag 
    command = os.popen(
        'python %s -s %s -c %s -p %s -i 17 --view test_view1 ' % (
        QUERY_CHECK_EXEC, TEST_DNS_SERVER, CONFIG_FILE, self.port))
    output = command.read()
    command.close()
    self.assertEqual(output, '')

    # Running dnsquerycheck with on a view/zone pair
    command = os.popen(
        'python %s -s %s -c %s -p %s -i 17 --view test_view1 '
        '--zone sub.university.lcl ' % (
        QUERY_CHECK_EXEC, TEST_DNS_SERVER, CONFIG_FILE, self.port))
    output = command.read()
    command.close()
    self.assertEqual(output, '')

    # Running dnsquerycheck with file
    command = os.popen(
        'python %s -s %s -c %s -p %s -f test_data/test_zone.db' % (
        QUERY_CHECK_EXEC, TEST_DNS_SERVER, CONFIG_FILE, self.port))
    output = command.read()
    command.close()
    self.assertEqual(output, '')

if( __name__ == '__main__' ):
      unittest.main()
