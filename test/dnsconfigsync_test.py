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

"""Regression test for dnsconfigsync

Make sure you are running this against a database that can be destroyed.

In order to restart bind for this unittest on Ubuntu, make sure
/etc/apparmor.d/usr/sbin/named has permission to your roster test directory
I added "/home/dcfritz/** r," under the "/usr/sbin/named {" section

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.

This test needs apparmor and selinux either disabled or reconfigured

This test requires BIND 9.9 with dig 9.9
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import getpass
import os
import sys
import subprocess
import shutil
import socket
import time
import unittest
import tarfile
from fabric import api as fabric_api
from fabric import network as fabric_network
from fabric import state as fabric_state

import roster_core
from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnsconfigsync'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
KEY_FILE = 'test_data/rndc.key'
RNDC_CONF_FILE = 'test_data/rndc.conf'
USERNAME = u'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
SSH_ID = 'test_data/roster_id_dsa'
SSH_USER = getpass.getuser()
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


class TestCheckConfig(unittest.TestCase):
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
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)

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

  def testNull(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'sub.university.lcl', u'master',
                                u'sub.university.lcl.', view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_zone.db '
                      '--view test_view -u %s --config-file %s '
                      '-z sub.university.lcl' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone.db\n'
                     '17 records loaded from zone test_data/test_zone.db\n'
                      '17 total records added\n')
    output.close()

    self.core_instance.MakeDnsServer(TEST_DNS_SERVER)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', u'set1')
    self.core_instance.MakeNamedConfGlobalOption(
        u'set1', u'include "%s/test_data/rndc.key"; options { pid-file "test_data/named.pid";};\ncontrols { inet 127.0.0.1 port %d allow{localhost;} keys {rndc-key;};};' % (os.getcwd(), self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'any')
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
            EXEC, self.rndc_port, SSH_USER, SSH_ID, CONFIG_FILE, self.rndc_port))
    lines = command.read().split('\n')
    # These lines will likely need changed depending on implementation
    self.assertTrue('Connecting to "%s"' % TEST_DNS_SERVER in lines)
    # self.assertTrue('sending incremental file list' in lines)
    # self.assertTrue('named/' in lines)
    # self.assertTrue('named/test_view/' in lines)
    # self.assertTrue('test_data/named/' in lines)
    # self.assertTrue('server reload successful' in lines)
    # self.assertTrue('[%s@%s] out:  * Starting domain name service... bind9\r' % (
    #     SSH_USER, TEST_DNS_SERVER) in lines)
    self.assertTrue('[%s@%s] out: server reload successful\r' % (
        SSH_USER, TEST_DNS_SERVER) in lines)
    self.assertTrue('Disconnecting from %s... done.' % (
            TEST_DNS_SERVER) in lines)
    command.close()

    try:

      file_handle = open('temp_dir/set1_servers/named.conf', 'r')
      lines = file_handle.read()
      file_handle.close()
      ##lines = lines.replace('\"temp_dir\"', '%s/temp_dir' % os.getcwd())
      ##lines = lines.replace('temp_dir/', '%s/temp_dir/set1_servers/named/' % os.getcwd())
      file_handle = open('temp_dir/set1_servers/named.conf', 'w')
      file_handle.write(lines)
      file_handle.close()
      file_handle = open('temp_dir/set1_servers/named.conf', 'r')
      lines = file_handle.read()
    except IOError:
      pass

    command = os.popen('dig @%s%s mail1.sub.university.lcl -p %s' % (
        TEST_DNS_SERVER, NS_DOMAIN, self.port))
    lines = ''.join(command.read()).split('\n')

    testlines = (
        '\n'
        '%s\n'
        '; (1 server found)\n'
        '%s\n'
        ';; Got answer:\n'
        '%s\n'
        ';; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 2, ADDITIONAL: '
        '3\n'
        '\n'
        ';; OPT PSEUDOSECTION:\n'
        '; EDNS: version: 0, flags:; udp: 4096\n'
        ';; QUESTION SECTION:\n'
        ';mail1.sub.university.lcl.\tIN\tA\n'
        '\n'
        ';; ANSWER SECTION:\n'
        'mail1.sub.university.lcl. 3600\tIN\tA\t192.168.1.101\n'
        '\n'
        ';; AUTHORITY SECTION:\n'
        'sub.university.lcl.\t3600\tIN\tNS\tns2.sub.university.lcl.\n'
        'sub.university.lcl.\t3600\tIN\tNS\tns.sub.university.lcl.\n'
        '\n'
        ';; ADDITIONAL SECTION:\n'
        'ns.sub.university.lcl.\t3600\tIN\tA\t192.168.1.103\n'
        'ns2.sub.university.lcl.\t3600\tIN\tA\t192.168.1.104\n'
        '\n'
        '%s\n'
        ';; SERVER: %s#%s(%s)\n'
        '%s\n'
        ';; MSG SIZE  rcvd: 136\n'
        '\n' % (lines[1], lines[3], lines[5], lines[24], NS_IP_ADDRESS,
            self.port, NS_IP_ADDRESS, lines[26]))
    lines = '\n'.join(lines)
    self.assertEqual(set(lines.split()), set(testlines.split()))
    command.close()

if( __name__ == '__main__' ):
      unittest.main()
