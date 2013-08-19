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
__version__ = '0.18'


import getpass
import os
import sys
import subprocess
import shutil
import socket
import time
import unittest
import tarfile
import glob
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
TESTDIR = unicode(os.path.join(os.getcwd(), 'test_data/unittest_dir/'))
BINDDIR = unicode(os.path.join(os.getcwd(), 'test_data/bind_dir/'))
SSH_USER = unicode(getpass.getuser())
TEST_DNS_SERVER = u'localhost'
NS_IP_ADDRESS = '127.0.0.1'
NS_DOMAIN = '' #Blank since using localhost
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
RNDC_CONF = unicode(os.path.join(os.getcwd(), 'test_data', 'rndc.conf'))
RNDC_KEY = unicode(os.path.join(os.getcwd(), 'test_data', 'rndc.key'))


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

    self.core_instance.MakeDnsServer(
        TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(
        u'set1',
        u'include "%s"; options { pid-file "%s";};\n'
         'controls { inet 127.0.0.1 port %d allow{localhost;} '
         'keys {rndc-key;};};' % (
            RNDC_KEY,
            os.path.join(BINDDIR, 'named.pid'), 
            self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'set1',
                                                u'any', 1)
    self.tree_exporter_instance.ExportAllBindTrees()
    # Copy blank named.conf to start named with

    bind_dir_named_conf = os.path.join(BINDDIR, 'named.conf')

    shutil.copyfile('test_data/named.blank.conf', 
        bind_dir_named_conf)
    named_file_contents = open(bind_dir_named_conf, 'r').read()
    named_file_contents = named_file_contents.replace('RNDC_KEY', RNDC_KEY)
    named_file_contents = named_file_contents.replace('NAMED_DIR', BINDDIR)
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

    self.command_string = (
        'python %s -d %s --rndc-key %s --rndc-conf %s --rndc-port %s '
        '--ssh-id %s --config-file %s ' % (
            EXEC, TEST_DNS_SERVER, RNDC_KEY, RNDC_CONF, self.rndc_port, SSH_ID, 
            CONFIG_FILE))
    self.audit_id, filename = self.config_lib_instance.FindNewestDnsTreeFilename()


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

    bind_dirs = glob.glob('%s*' % BINDDIR.rstrip('/'))
    for bind_dir in bind_dirs:
      if( os.path.islink(bind_dir) ):
        os.unlink(bind_dir)
      else:
        shutil.rmtree(bind_dir)

  def testConfigSync(self):
    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    dns_server_info = self.config_lib_instance.GetDnsServerInfo(TEST_DNS_SERVER)
    dns_server_info['server_info']['bind_version'] = '9.8.1-P1'
    dns_server_info['server_info']['bind_dir'] = '/wrong/bind_dir/'
    dns_server_info['server_info']['test_dir'] = '/wrong/test_dir/'
    dns_server_info['tools'] = {}
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)
    
    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertTrue(
        'ERROR: Failed in moving BIND tree files to server localhost.' in lines)
    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    dns_server_info['tools']['tar'] = True
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)


    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertTrue(
        'ERROR: Failed to move compressed BIND tree '
                    'to server localhost' in lines)

    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    dns_server_info['server_info']['test_dir'] = TESTDIR
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)

    #Bind directory raise
    command = os.popen(self.command_string)
    output = command.read()
    command.close()
    self.assertEqual(output,
        'ERROR: BIND directory /wrong/bind_dir does not exist on server localhost\n')

    #Make sure can run successfully without any tools
    dns_server_info['server_info']['bind_dir'] = BINDDIR
    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)

    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertEqual(lines, [''])
    self.assertTrue(os.path.exists(os.path.join(BINDDIR, 'named.conf')))

    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    dns_server_info = self.config_lib_instance.GetDnsServerInfo(TEST_DNS_SERVER)
    dns_server_info['server_info']['bind_version'] = '9.8.1-P1'
    dns_server_info['server_info']['bind_dir'] = BINDDIR
    dns_server_info['server_info']['test_dir'] = TESTDIR
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)
    self.config_lib_instance.UnTarDnsTree(self.audit_id)

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
    dns_server_info = self.config_lib_instance.GetDnsServerInfo(TEST_DNS_SERVER)
    dns_server_info['tools']['named-checkconf'] = True
    dns_server_info['tools']['named-compilezone'] = False
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)

    if( not os.path.exists(TESTDIR) ):
      os.mkdir(TESTDIR)

    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertTrue('ERROR: Named.conf check failed on localhost.' in lines)

    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    dns_server_info['tools']['named-compilezone'] = True
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)
    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertTrue('ERROR: Binary named.conf check failed on localhost.' in lines)

    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    os.remove('%s/localhost/named.conf.a' % self.root_config_dir)
    os.remove('%s/localhost/named.conf.b' % self.root_config_dir)
    shutil.move('%s/localhost/named.conf.a.old' % self.root_config_dir,
            '%s/localhost/named.conf.a' % self.root_config_dir)
    shutil.move('%s/localhost/named.conf.b.old' % self.root_config_dir,
            '%s/localhost/named.conf.b' % self.root_config_dir)
    
    shutil.move('%s/localhost/named/test_view/sub.university.lcl.db' % self.root_config_dir,
        '%s/sub.university.lcl.db.old' % self.backup_dir)
    f = open('%s/localhost/named/test_view/sub.university.lcl.db' % self.root_config_dir, 'w')
    f.write('bad zone\n$ORIGIN sub.university.lcl.')
    f.close()
    self.config_lib_instance.TarDnsTree(self.audit_id)
    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertTrue('ERROR: Failed to compile zone sub.university.lcl.' in lines)

    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    dns_server_info['tools']['named-checkzone'] = True
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)
    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertTrue('ERROR: Zone sub.university.lcl did not pass the check.' in lines)

    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    shutil.move('%s/sub.university.lcl.db.old' % self.backup_dir,
        '%s/localhost/named/test_view/sub.university.lcl.db' % self.root_config_dir)
    self.config_lib_instance.TarDnsTree(self.audit_id)

    for bind_dir in glob.glob('%s*' % BINDDIR.rstrip('/')):
      if( os.path.isdir(bind_dir) ):
        shutil.rmtree(bind_dir)
      elif( os.path.islink(bind_dir) ):
        os.unlink(bind_dir)
    os.mkdir(BINDDIR)

    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()

    self.assertEqual(lines, [''])
    self.assertTrue(os.path.exists(os.path.join(BINDDIR, 'named/test_view/sub.university.lcl.aa')))
    self.assertTrue(os.path.exists('%s/named.conf' % BINDDIR))
    self.assertTrue(os.path.exists('%s/named/named.ca' % BINDDIR))
    self.assertTrue(os.path.exists('%s/named/named.conf' % BINDDIR))

    self.core_instance.MakeRecord(u'a', u'desktop-2', u'sub.university.lcl', 
        { u'assignment_ip': u'192.168.1.105' }, view_name=u'test_view')
    self.tree_exporter_instance.ExportAllBindTrees()

    #Remember, 1 for the new A record, and 1 for the export
    self.audit_id += 2

    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)
    
    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertEqual(lines, [''])

    self.assertTrue(os.path.exists('%s/named.conf' % BINDDIR))
    self.assertTrue(os.path.exists('%s/named/named.ca' % BINDDIR))
    self.assertTrue(os.path.exists('%s/named/named.conf' % BINDDIR))

    # Tests that zones with name ending with 'd' or 'b' are not improperly named
    self.core_instance.MakeZone(u'zoned', u'master', u'zoned.lcl.', view_name=u'test_view')
    output = os.popen('python %s -f test_data/test_zone.db '
                      '--view test_view -u %s --config-file %s '
                      '-z zoned' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone.db\n'
                     '17 records loaded from zone test_data/test_zone.db\n'
                     '17 total records added\n')
    output.close()

    self.tree_exporter_instance.ExportAllBindTrees()
    self.audit_id += 3
    self.config_lib_instance.UnTarDnsTree(self.audit_id)
    self.config_lib_instance.WriteDnsServerInfo(dns_server_info)
    self.config_lib_instance.TarDnsTree(self.audit_id)

    command = os.popen(self.command_string)
    lines = command.read().split('\n')
    command.close()
    self.assertEqual(lines, [''])
    zone_files = os.listdir('%s/named/test_view/' % BINDDIR.rstrip('/'))
    self.assertTrue('zone.aa' not in zone_files)
    self.assertTrue('zoned.aa' in zone_files)

if( __name__ == '__main__' ):
      unittest.main()
