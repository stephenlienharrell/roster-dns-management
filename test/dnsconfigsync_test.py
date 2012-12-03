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
from roster_config_manager import config_lib

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnsconfigsync'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
USERNAME = u'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
SSH_ID = 'test_data/roster_id_dsa'
TESTDIR = u'%s/test_data/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/bind_dir/' % os.getcwd()
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
RNDC_CONF = 'test_data/bind_dir/rndc.conf'
RNDC_KEY = 'test_data/bind_dir/rndc.key'


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
    self.root_config_dir = self.config_instance.config_file['exporter']['root_config_dir']
    self.backup_dir = self.config_instance.config_file['exporter']['backup_dir']

    db_instance = self.config_instance.GetDb()
    db_instance.CreateRosterDatabase()

    self.bind_config_dir = os.path.expanduser(
        self.config_instance.config_file['exporter']['root_config_dir'])
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    self.config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)

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
    if( not os.path.exists(TESTDIR) ):
      os.mkdir(TESTDIR)
    if( not os.path.exists(BINDDIR) ):
      os.mkdir(BINDDIR)

  def tearDown(self):
    fabric_api.local('killall named', capture=True)
    fabric_network.disconnect_all()
    time.sleep(1) # Wait for disk to settle
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    if( os.path.exists(self.backup_dir) ):
      shutil.rmtree(self.backup_dir)
    if( os.path.exists(TESTDIR) ):
      shutil.rmtree(TESTDIR)

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

    self.core_instance.MakeDnsServer(TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(
        u'set1', u'include "%srndc.key"; options { pid-file "%snamed.pid";};\n'
        'controls { inet 127.0.0.1 port %d allow{localhost;} keys {rndc-key;};};' % (BINDDIR, BINDDIR, self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'any', 1)
    self.tree_exporter_instance.ExportAllBindTrees()
    # Copy blank named.conf to start named with
    shutil.copyfile('test_data/named.blank.conf', '%s/named.conf' % BINDDIR.rstrip('/'))
    named_file_contents = open('%s/named.conf' % BINDDIR.rstrip('/'), 'r').read()
    named_file_contents = named_file_contents.replace('RNDC_KEY', '%srndc.key' % BINDDIR)
    named_file_contents = named_file_contents.replace('NAMED_DIR', '%snamed' % BINDDIR)
    named_file_contents = named_file_contents.replace('NAMED_PID', '%snamed.pid' % BINDDIR)
    named_file_contents = named_file_contents.replace('RNDC_PORT', str(self.rndc_port))
    named_file_contents = named_file_contents.replace('SESSION_KEYFILE', '%s/%s' % (os.getcwd(), str(SESSION_KEYFILE)))
    named_file_handle = open('%s/named.conf' % BINDDIR.rstrip('/'), 'w')
    named_file_handle.write(named_file_contents)
    named_file_handle.close()
    # Start named
    out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %s/named.conf' % (
        self.port, SSH_USER, BINDDIR.rstrip('/')), capture=True)
    time.sleep(2)
    # Start of testing tool functionality
    command_string = (
        'python %s -d %s --rndc-key %s --rndc-port %s '
        '--ssh-id %s --config-file %s --rndc-conf %s' % (
            EXEC, TEST_DNS_SERVER, RNDC_KEY, self.rndc_port, SSH_ID, 
            CONFIG_FILE, RNDC_CONF))

    audit_id, filename = self.config_lib_instance.FindNewestDnsTreeFilename()
    self.config_lib_instance.UnTarDnsTree(audit_id)
    dns_server_info = self.config_lib_instance.GetDnsServerInfo(TEST_DNS_SERVER)
    dns_server_info['server_info']['bind_version'] = '9.8.1-P1'
    dns_server_info['server_info']['bind_dir'] = '/wrong/dir/'
    dns_server_info['server_info']['test_dir'] = '/wrong/test/dir/'
    dns_server_info['tools'] = {}
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(audit_id)
    
    command = os.popen(command_string)
    lines = command.read().split('\n')
    self.assertTrue('ERROR: Failed in moving BIND tree files to server localhost.' in lines)
    
    self.config_lib_instance.UnTarDnsTree(audit_id)
    dns_server_info['tools']['tar'] = True
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(audit_id)

    command = os.popen(command_string)
    lines = command.read().split('\n')
    self.assertTrue('ERROR: Failed to move compressed BIND tree to server localhost.' in lines)

    self.config_lib_instance.UnTarDnsTree(audit_id)
    dns_server_info['server_info']['test_dir'] = TESTDIR
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(audit_id)

    # Bind directory raise
    command = os.popen(command_string)
    lines = command.read().split('\n')
    self.assertTrue('ERROR: Failed to move files from test directory to bind directory on server localhost.' in lines)

    # Make sure can run successfully without any tools
    dns_server_info['server_info']['bind_dir'] = BINDDIR
    self.config_lib_instance.UnTarDnsTree(audit_id)
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(audit_id)

    command = os.popen(command_string)
    lines = command.read().split('\n')
    self.assertEqual(lines, [''])
    self.assertTrue(os.path.exists('%s/named.conf' % BINDDIR))

    self.config_lib_instance.UnTarDnsTree(audit_id)
    shutil.move('%s/localhost/named.conf.a' % self.root_config_dir,
            '%s/localhost/named.conf.a.old' % self.root_config_dir)
    shutil.move('%s/localhost/named.conf.b' % self.root_config_dir,
            '%s/localhost/named.conf.b.old' % self.root_config_dir)
    f = open('%s/localhost/named.conf.a' % self.root_config_dir, 'w')
    f.write('bad named.conf')
    f.close()
    f = open('%s/localhost/named.conf.b' % self.root_config_dir, 'w')
    f.write('bad named.conf')
    f.close()
    dns_server_info['tools']['named-checkconf'] = True
    dns_server_info['tools']['named-compilezone'] = False
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(audit_id)
    command = os.popen(command_string)
    lines = command.read().strip('\n')
    self.assertTrue('ERROR: Named.conf check failed on localhost.' in lines)

    self.config_lib_instance.UnTarDnsTree(audit_id)
    dns_server_info['tools']['named-compilezone'] = True
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(audit_id)
    command = os.popen(command_string)
    lines = command.read().split('\n')
    self.assertTrue('ERROR: Binary named.conf check failed on localhost.' in lines)

    self.config_lib_instance.UnTarDnsTree(audit_id)
    os.remove('%s/localhost/named.conf.a' % self.root_config_dir)
    os.remove('%s/localhost/named.conf.b' % self.root_config_dir)
    shutil.move('%s/localhost/named.conf.a.old' % self.root_config_dir,
            '%s/localhost/named.conf.a' % self.root_config_dir)
    shutil.move('%s/localhost/named.conf.b.old' % self.root_config_dir,
            '%s/localhost/named.conf.b' % self.root_config_dir)
    
    f = open('%s/localhost/named/test_view/bad_zone.db' % self.root_config_dir, 'w')
    f.write('bad zone\n$ORIGIN badzone.edu.')
    f.close()
    self.config_lib_instance.TarDnsTree(audit_id)
    command = os.popen(command_string)
    lines = command.read().split('\n')
    self.assertTrue('ERROR: Failed to compile zone badzone.edu.' in lines)

    self.config_lib_instance.UnTarDnsTree(audit_id)
    dns_server_info['tools']['named-checkzone'] = True
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(audit_id)
    command = os.popen(command_string)
    lines = command.read().split('\n')
    self.assertTrue('ERROR: Zone badzone.edu did not pass the check.' in lines)

    self.config_lib_instance.UnTarDnsTree(audit_id)
    os.remove('%s/localhost/named/test_view/bad_zone.db' % self.root_config_dir)
    self.config_lib_instance.TarDnsTree(audit_id)
    command = os.popen(command_string)
    lines = command.read().split('\n')

    result = os.popen('rndc -c /etc/bind/rndc.conf -k /etc/bind/rndc.key -p %s reload' % self.rndc_port).readlines()
    self.assertEqual(lines, [''])
    self.assertTrue(os.path.exists('%s/named/test_view/sub.university.lcl.aa' % BINDDIR))
    self.assertTrue(os.path.exists('%s/named/named.ca' % BINDDIR))
    self.assertTrue(os.path.exists('%s/named.conf' % BINDDIR))

if( __name__ == '__main__' ):
      unittest.main()
