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

"""Regression test for dnsexportconfig

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import cPickle
import getpass
import iscpy
import os
import sys
import shutil
import unittest
import tarfile
import StringIO
import socket
import time
import smtplib
from fabric import api as fabric_api
from fabric import network as fabric_network
from fabric import state as fabric_state

import roster_core
from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf.real'
EXEC = '../roster-config-manager/scripts/dnsexportconfig'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
KEY_FILE = 'test_data/rndc.key'
USERNAME = 'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TESTDIR = u'%s/test_data/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/named/' % os.getcwd()
TEST_DNS_SERVER = u'localhost'
SSH_ID = 'test_data/roster_id_dsa'
SSH_USER = unicode(getpass.getuser())
SESSION_KEYFILE = '%s/test_data/session.key' % os.getcwd()
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
RNDC_CONF = '%s/rndc.conf' % BINDDIR.rstrip('/')
RNDC_KEY = '%s/rndc.key' % BINDDIR.rstrip('/')


class TestCheckConfig(unittest.TestCase):
  def TarReplaceString(self, tar_file_name, member, string1, string2):
    tar_contents = {}
    exported_file = tarfile.open(tar_file_name, 'r')
    for current_member in exported_file.getmembers():
      tar_contents[current_member.name] = exported_file.extractfile(
          current_member.name).read()
    tarred_file_handle = exported_file.extractfile(member)
    tarred_file = tarred_file_handle.read()
    tarred_file_handle.close()
    exported_file.close()

    tarred_file = tarred_file.replace(string1, string2)

    exported_file = tarfile.open(tar_file_name, 'w')
    for current_member in tar_contents:
      info = tarfile.TarInfo(name=current_member)
      if( current_member == member ):
        info.size = len(tarred_file)
        exported_file.addfile(info, StringIO.StringIO(tarred_file))
      else:
        info.size = len(tar_contents[current_member])
        exported_file.addfile(info, StringIO.StringIO(
            tar_contents[current_member]))
    exported_file.close()

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
    self.root_config_dir = self.config_instance.config_file[
        'exporter']['root_config_dir'].rstrip('/').lstrip('./')
    self.backup_dir = self.config_instance.config_file[
        'exporter']['backup_dir'].rstrip('/').lstrip('./')
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    self.lockfile = self.config_instance.config_file[
        'server']['lock_file']

    db_instance = self.config_instance.GetDb()
    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()
    self.db_instance = db_instance

    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)
    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')

    if( not os.path.exists(TESTDIR) ):
      os.system('mkdir %s' % TESTDIR)

  def tearDown(self):
    fabric_api.local('killall named', capture=True)
    fabric_network.disconnect_all()
    time.sleep(1) # Wait for disk to settle
    if( os.path.exists(KEY_FILE) ):
      os.remove(KEY_FILE)
    if( os.path.exists(self.backup_dir) ):
      shutil.rmtree(self.backup_dir)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    if( os.path.exists('%s/named' % BINDDIR.rstrip('/')) ):
      shutil.rmtree('%s/named' % BINDDIR.rstrip('/'))
    if( os.path.exists('%s/named.conf' % BINDDIR.rstrip('/')) ):
      os.remove('%s/named.conf' % BINDDIR.rstrip('/'))
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)

  def testCheckConfig(self):
    output = os.popen('python %s -f --config-file %s '
    '--ssh-id %s --rndc-port %s --rndc-key %s --rndc-conf %s' % (
        EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY,
        RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    self.assertTrue('[localhost] local: dnstreeexport -c test_data/roster.conf.real --force' in lines)
    self.assertTrue('ERROR: No dns server sets found.' in lines)

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
        u'set1', u'include "%s"; options { pid-file "test_data/named.pid"; };\ncontrols { inet 127.0.0.1 port %d allow{localhost;} keys {rndc-key;};};' % (RNDC_KEY, self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'set1', u'any', 1)
    self.tree_exporter_instance.ExportAllBindTrees()
    # Copy blank named.conf to start named with
    if( not os.path.exists(BINDDIR) ):
      os.mkdir(BINDDIR)
    shutil.copyfile('test_data/named.blank.conf',
                    '%s/named.conf' % BINDDIR.rstrip('/'))
    named_file_contents = open('%s/named.conf' % BINDDIR.rstrip('/'), 'r').read()
    named_file_contents = named_file_contents.replace(
        'RNDC_KEY', '%s' % RNDC_KEY)
    named_file_contents = named_file_contents.replace(
        'NAMED_DIR', '%s' % BINDDIR.rstrip('/'))
    named_file_contents = named_file_contents.replace(
        'NAMED_PID', '%s/test_data/named.pid' % os.getcwd())
    named_file_contents = named_file_contents.replace(
        'RNDC_PORT', str(self.rndc_port))
    named_file_contents = named_file_contents.replace(
        'SESSION_KEYFILE', '%s' % str(SESSION_KEYFILE))
    named_file_handle = open('%s/named.conf' % BINDDIR.rstrip('/'), 'w')
    named_file_handle.write(named_file_contents)
    named_file_handle.close()
    named_file_contents = open('%s/named.conf' % BINDDIR.rstrip('/'), 'r').read()
    # Start named
    out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %s/named.conf' % (
        self.port, SSH_USER, BINDDIR.rstrip('/')), capture=True)
    time.sleep(2)
   
    output = os.popen('python %s -f --config-file %s '
    '--ssh-id %s --rndc-port %s --rndc-key %s --rndc-conf %s' % (
        EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY,
        RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    
    self.assertTrue('[localhost] local: dnstreeexport -c test_data/roster.conf.real --force' in lines)
    self.assertTrue('[localhost] local: dnscheckconfig -i 14 --config-file test_data/roster.conf.real -d test_data/backup_dir -o temp_dir -z /usr/sbin/named-checkzone -c /usr/sbin/named-checkconf -v -s localhost' in lines)
    self.assertTrue('Finished - temp_dir/%s/named.conf.a' % TEST_DNS_SERVER in lines)
    self.assertTrue('Finished - temp_dir/%s/named/test_view/sub.university.lcl.db' % TEST_DNS_SERVER in lines)
    self.assertTrue('All checks successful' in lines)
    self.assertTrue('[localhost] local: dnsservercheck -c test_data/roster.conf.real -i 14 -d %s' % TEST_DNS_SERVER in lines)
    self.assertTrue('[localhost] local: dnsquerycheck -c test_data/roster.conf.real -i 14 -n 5 -p 53 -s %s' % TEST_DNS_SERVER in lines)

    self.core_instance.MakeDnsServer(u'bad.server.local', SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSetAssignments(u'bad.server.local', u'set1')
    output = os.popen('export ROSTERTESTPATH=%s && export ROSTERTESTSMTPERROR='
        'server_error && python %s -f --config-file %s --ssh-id %s '
        '--rndc-port %s --rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY, RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    self.assertTrue('[localhost] local: dnscheckconfig -i 17 --config-file test_data/roster.conf.real -d test_data/backup_dir -o temp_dir -z /usr/sbin/named-checkzone -c /usr/sbin/named-checkconf -v -s bad.server.local' in lines)

    smtp_server = self.config_instance.config_file['exporter']['smtp_server']
    self.assertTrue('%s is an invalid smtp server.' % smtp_server in lines)
    output = os.popen('export ROSTERTESTPATH=%s && export ROSTERTESTSMTPERROR='
                      'connect_error && python %s -f --config-file %s --ssh-id %s '
                      '--rndc-port %s --rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY, RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    self.assertTrue('Failed to connect to bad.server.local.' in lines)

    output = os.popen('export ROSTERTESTPATH=%s && export ROSTERTESTSMTPERROR='
        'message_error && python %s -f --config-file %s --ssh-id %s '
        '--rndc-port %s --rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY, RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    self.assertTrue('%s is an invalid email address.' % self.config_instance.config_file[
        'exporter']['failure_notification_email'] in lines)

    # Can't connect to server (dnscheckconf)
    output = os.popen('export ROSTERTESTPATH=%s && python %s -f --config-file %s --ssh-id %s '
        '--rndc-port %s --rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY, RNDC_CONF))
    out_str = output.read()
    output.close()
    self.assertTrue("""<html><head></head><body><br/><h4>dnscheckconfig has failed on server'bad.server.local' with the following error:</h4>""" in out_str)
    self.assertTrue("""raise ServerCheckError('Could not connect to %s via SSH.' % dns_server)<br/>""" in out_str)
    self.assertTrue("""roster_config_manager.config_lib.ServerCheckError: Could not connect to bad.server.local via SSH.<br/></p></body></html>""" in out_str)

    
    self.assertTrue("""dnscheckconfig has failed on server'bad.server.local' with the following error:\n""" in out_str)
    self.assertTrue("""Traceback (most recent call last):\n""" in out_str)
    self.assertTrue("""config_lib_instance.CheckDnsServer(options.server, [])\n """ in out_str)
    self.assertTrue("""raise ServerCheckError('Could not connect to %s via SSH.' % dns_server)\n""" in out_str)
    self.assertTrue("""roster_config_manager.config_lib.ServerCheckError: Could not connect to bad.server.local via SSH.""" in out_str)

    # No ns record for zone (dnscheckconf)
    self.core_instance.RemoveDnsServer(u'bad.server.local')
    self.core_instance.RemoveRecord(u'a', u'ns', u'sub.university.lcl', {u'assignment_ip': u'192.168.1.103'}, u'test_view')
    output = os.popen('export ROSTERTESTPATH=%s && python %s -f --config-file %s --ssh-id %s '
        '--rndc-port %s --rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY, RNDC_CONF))
    out_str = output.read()
    output.close()
    self.assertTrue("""Content-Type: text/plain; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""MIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\n\n""" in out_str)
    self.assertTrue("""dnscheckconfig has failed on server'%s' with the following error:\n\n""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""Finished - temp_dir/%s/named.conf.a\n""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""ERROR: zone sub.university.lcl/IN: NS 'ns.sub.university.lcl' has no address records (A or AAAA)\n""" in out_str)
    self.assertTrue("""zone sub.university.lcl/IN: not loaded due to errors.""" in out_str)

    self.assertTrue("""Content-Type: text/html; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""<html><head></head><body><br/><h4>dnscheckconfig has failed on server'%s' with the following error:</h4>""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""<p>Finished - temp_dir/%s/named.conf.a<br/>""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""ERROR: zone sub.university.lcl/IN: NS 'ns.sub.university.lcl' has no address records (A or AAAA)<br/>""" in out_str)
    self.assertTrue("""zone sub.university.lcl/IN: not loaded due to errors.</p></body></html>""" in out_str)

    self.core_instance.MakeRecord(u'a', u'ns', u'sub.university.lcl', {u'assignment_ip': u'192.168.1.103'}, u'test_view')

    # bad test directory on server (dnscheckconf)
    self.core_instance.UpdateDnsServer(TEST_DNS_SERVER, TEST_DNS_SERVER, SSH_USER, u'/bad/directory/', TESTDIR)
    output = os.popen('export ROSTERTESTPATH=%s && python %s -f --config-file %s --ssh-id %s '
        '--rndc-port %s --rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY, RNDC_CONF))
    out_str = output.read()
    output.close()
    self.assertTrue("""Content-Type: text/plain; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""MIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\n\n""" in out_str)
    self.assertTrue("""dnscheckconfig has failed on server'%s' with the following error:\n""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""Traceback (most recent call last):\n""" in out_str)
    self.assertTrue("""config_lib_instance.CheckDnsServer(options.server, [])\n """ in out_str)
    self.assertTrue("""dns_server_info['server_info']['server_user']))\n""" in out_str)
    self.assertTrue("""roster_config_manager.config_lib.ServerCheckError: The remote BIND directory /bad/directory/ does not exist or """ in out_str)
    self.assertTrue("""the user %s does not have permission.""" % SSH_USER in out_str)

    self.assertTrue("""Content-Type: text/html; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""<html><head></head><body><br/><h4>dnscheckconfig has failed on server'%s' with the following error:</h4>""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""<p>Traceback (most recent call last):<br/>""" in out_str)
    self.assertTrue("""main(sys.argv[1:])<br/>""" in out_str)
    self.assertTrue("""config_lib_instance.CheckDnsServer(options.server, [])<br/>""" in out_str)
    self.assertTrue("""dns_server_info['server_info']['server_user']))<br/>""" in out_str)
    self.assertTrue("""roster_config_manager.config_lib.ServerCheckError: The remote BIND directory /bad/directory/ does not exist or """ in out_str)
    self.assertTrue("""the user %s does not have permission.<br/></p></body></html>""" % SSH_USER in out_str)
    self.core_instance.UpdateDnsServer(TEST_DNS_SERVER, TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)

    # rndc reload failure (dnsconfigsync)
    fabric_api.local('killall named', capture=True)
    output = os.popen('export ROSTERTESTPATH=%s && python %s -f --config-file %s --ssh-id %s '
        '--rndc-port %s --rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, self.rndc_port, RNDC_KEY, RNDC_CONF))
    out_str = output.read()
    output.close()
    self.assertTrue("""Content-Type: text/plain; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""MIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\n\n""" in out_str)
    self.assertTrue("""dnsconfigsync failed on server '%s' with the following error:\n\n""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""ERROR: Failed to reload """ in out_str)
    self.assertTrue(""" BIND server: rndc: connect failed: 127.0.0.1#""" in out_str)
    self.assertTrue(""": connection refused.""" in out_str)

    self.assertTrue("""Content-Type: text/html; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""MIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\n\n""" in out_str)
    self.assertTrue("""<html><head></head><body><br/><h4>dnsconfigsync failed on server '%s' with the following error:</h4>""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""<p>ERROR: Failed to reload """ in out_str)
    self.assertTrue(""" BIND server: rndc: connect failed: 127.0.0.1#""" in out_str)
    self.assertTrue(""": connection refused.</p></body></html>""" in out_str)

if( __name__ == '__main__' ):
      unittest.main()
