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
import re
from fabric import api as fabric_api
from fabric import network as fabric_network
from fabric import state as fabric_state

import roster_core
from roster_config_manager import tree_exporter
from roster_config_manager import config_lib

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnsexportconfig'
QUERY_CHECK_EXEC = '../roster-config-manager/scripts/dnsquerycheck'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
USERNAME = 'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TESTDIR = u'%s/test_data/unittest_dir/' % os.getcwd()
#BINDDIR = u'/etc/bind/'
BINDDIR = u'%s/test_data/bind_dir/' % os.getcwd()
THREADING_DIR = os.path.join(BINDDIR, 'threading')
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

def PickUnusedPort():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((TEST_DNS_SERVER, 0)) 
  addr, port = s.getsockname()
  s.close()
  return port

class TestCheckConfig(unittest.TestCase):
  def setUp(self):
    self.port = PickUnusedPort()
    self.rndc_port = PickUnusedPort()
    while( self.rndc_port == self.port ):
      self.rndc_port = PickUnusedPort()

    if( not os.path.exists(BINDDIR) ):
      os.mkdir(BINDDIR)
    if( not os.path.exists(TESTDIR) ):
      os.mkdir(TESTDIR)

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

    database_server = self.config_instance.config_file['database']['server']
    traceroute_output =  os.popen(
        'dig +trace www.google.com | grep Received').read().strip('\n')
    traceroute_lines = traceroute_output.split('\n')
    self.real_dns_server = traceroute_lines[0].split(' ')[5].split('#')[0]

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

    self.config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)

    if( not os.path.exists(TESTDIR) ):
      os.system('mkdir %s' % TESTDIR)

  def tearDown(self):
    fabric_api.local('killall named', capture=True)
    fabric_network.disconnect_all()
    time.sleep(1) # Wait for disk to settle
    if( os.path.exists(self.backup_dir) ):
      shutil.rmtree(self.backup_dir)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    if( os.path.exists(BINDDIR) ):
      shutil.rmtree(BINDDIR)
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)
    if( os.path.exists('/etc/resolv.conf.unittest_backup') ):
      os.system('sudo mv /etc/resolv.conf.unittest_backup /etc/resolv.conf')

  def startNamed(self, bind_dir, rndc_port, port, root_server=False):
    # Copy blank named.conf to start named with
    if( not os.path.exists(bind_dir) ):
      os.mkdir(bind_dir)
    if( not os.path.exists('%s/named' % bind_dir.rstrip('/')) ):
      os.mkdir('%s/named' % bind_dir.rstrip('/'))
    shutil.copyfile('test_data/named.blank.conf',
                    '%s/named.conf' % bind_dir.rstrip('/'))
    named_file_contents = open('%s/named.conf' % bind_dir.rstrip('/'), 'r').read()
    named_file_contents = named_file_contents.replace(
        'RNDC_KEY', '%s/rndc.key' % bind_dir.rstrip('/'))
    named_file_contents = named_file_contents.replace(
        'NAMED_DIR', '%s/named' % bind_dir.rstrip('/'))
    named_file_contents = named_file_contents.replace(
        'NAMED_PID', '%s/named.pid' % bind_dir.rstrip('/'))
    named_file_contents = named_file_contents.replace(
        'RNDC_PORT', str(rndc_port))
    named_file_contents = named_file_contents.replace(
        'SESSION_KEYFILE', '%s/session.key' % bind_dir.rstrip('/'))
    named_file_handle = open('%s/named.conf' % bind_dir.rstrip('/'), 'w')
    named_file_handle.write(named_file_contents)
    named_file_handle.close()

    # Start named
    if( root_server ):
      named_file_contents = named_file_contents.replace(
          'forwarders { 127.0.0.1; };\n', 'forwarders { %s; };\n' % self.real_dns_server)
      named_file_handle = open('%s/named.conf' % bind_dir.rstrip('/'), 'w')
      named_file_handle.write(named_file_contents)
      named_file_handle.close()

      # Requires root access. This is to allow the service to start on port 53
      out = fabric_api.local('sudo /usr/sbin/named -u %s -c %s/named.conf' % (
          SSH_USER, bind_dir.rstrip('/')), capture=True)
    else:
      out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %s/named.conf' % (
          port, SSH_USER, bind_dir.rstrip('/')), capture=True)
    time.sleep(5)
    
  def testCheckConfigThreading(self):
    zone_name = u'unittest'
    zone_origin = u'%s.' % zone_name

    os.system('sudo mv /etc/resolv.conf /etc/resolv.conf.unittest_backup')
    os.system("""sudo sh -c "echo 'search %s\nnameserver 127.0.0.1\n' > /etc/resolv.conf"\n""" % zone_name)

    num_test_machines = 30
    ports = []
    test_dns_servers = []

    # Getting some free ports that we use for our 'fake' test machines.
    # Get 2 ports for each server, RNDC Port and BIND Port
    for i in range(num_test_machines * 2):
      port = PickUnusedPort()
      while( port in ports ):
        port = PickUnusedPort()
      ports.append(port)

    for i in range(num_test_machines):
      test_dns_servers.append({'server_name': u'server%s.%s' % (str(i + 1), zone_name),
                               'port': ports.pop(),
                               'rndc_port': ports.pop(),
                               'bind_dir': ''})

    # Getting our "base" DNS server's records created.
    # The "base" DNS server redirects 'server27' to 127.0.0.1 but
    #   for server1 through serverN for N = num_test_machines
    # The "base" DNS server will sit on 127.0.0.1 serving requests on port 53
    #   which is the default DNS server port. Later in this unittest, we'll have 
    #   a bunch of 'fake' DNS servers that we will export too. (server1 to serverN)
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(zone_name, u'master',
                                zone_origin, view_name=u'test_view',
                                make_any=False)
    self.assertEqual(self.core_instance.ListRecords(), []) 
    self.core_instance.MakeRecord(u'soa', u'@', zone_name,
        {u'refresh_seconds': 28800, u'expiry_seconds': 604800,
         u'name_server': u'ns1.unittest.com.', 
         u'minimum_seconds': 38400, u'retry_seconds': 3600, 
         u'serial_number': 1, u'admin_email': u'admin.unittest.com.'}, 
         view_name=u'test_view')
    self.core_instance.MakeRecord(u'ns', u'@', zone_name,
      {u'name_server': u'ns1.unittest.com.'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'ns1', zone_name,
      {u'assignment_ip': u'127.0.0.1'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'localhost', zone_name,
      {u'assignment_ip': u'127.0.0.1'}, view_name=u'test_view')

    self.core_instance.MakeDnsServerSet(u'test_set')
    self.core_instance.MakeDnsServer(TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'test_set')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'test_set')
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'test_set', u'any', 1)
    self.core_instance.MakeNamedConfGlobalOption(
        u'test_set',
        u'include "%s"; options { \n'
        u'pid-file "%s/named.pid"; };\n'
        u'controls { inet 127.0.0.1 port %d allow { localhost; } '
        u'keys { rndc-key; }; };\n'
        u'' % (RNDC_KEY, BINDDIR.rstrip('/'), self.rndc_port)) # So we can test

    # We export so we know what we've done so far is valid.
    # If this export fails, something above this line is messed up.
    self.tree_exporter_instance.ExportAllBindTrees()
    shutil.rmtree(self.tree_exporter_instance.backup_dir)

    # Starting the "base" DNS server.
    self.startNamed(BINDDIR, self.rndc_port, 53, root_server=True)

    for dns_server_dict in test_dns_servers:
      dns_server = dns_server_dict['server_name']
      bind_dir = os.path.join(THREADING_DIR, 'bind_dir_%s/' % dns_server)
      test_dir = os.path.join(THREADING_DIR, 'test_dir_%s/' % dns_server)

      dns_server_dict['bind_dir'] = bind_dir
      dns_server_dict['test_dir'] = test_dir

      if( not os.path.exists(THREADING_DIR) ):
        os.mkdir(THREADING_DIR)
      if( not os.path.exists(bind_dir) ):
        os.mkdir(bind_dir)
      if( not os.path.exists(test_dir) ):
        os.mkdir(test_dir)

      key = open(os.path.join(bind_dir, 'rndc.key'), 'w')
      key.write(RNDC_KEY_DATA)
      key.close()

      conf = open(os.path.join(bind_dir, 'rndc.conf'), 'w')
      conf.write(RNDC_CONF_DATA)
      conf.close()

      self.startNamed(bind_dir, dns_server_dict['rndc_port'], dns_server_dict['port'])

      # This next record gets made for the 'base' DNS server.
      self.core_instance.MakeRecord(u'a', unicode(dns_server.split('.')[0]), zone_name, 
          {u'assignment_ip': u'127.0.0.1'}, view_name=u'test_view')

    command_string = ('python %s -f --config-file %s '
    '--ssh-id %s --rndc-key %s --rndc-conf %s -p %s' % (
        EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY,
        RNDC_CONF, 53))

    # Running dnsexportconfig the first time to the 'base' DNS server.
    output = os.popen(command_string)
    output_string = output.read()
    output.close()

    audit_id = 17 + num_test_machines
    self.assertTrue('Finished - %s/localhost/named.conf.a' % self.root_config_dir in output_string)
    self.assertTrue('Finished - %s/localhost/named/test_view/unittest.db' % self.root_config_dir in output_string)
    # The following were commented out
    self.assertTrue('[localhost] local: dnsservercheck --export-config -c %s -i %s -d localhost' % (CONFIG_FILE, audit_id) in output_string)
    self.assertTrue('[localhost] local: dnsconfigsync --export-config -i %s -c %s --ssh-id test_data/roster_id_dsa --rndc-key %s --rndc-conf %s -d localhost' % (audit_id, CONFIG_FILE, RNDC_KEY, RNDC_CONF) in output_string)
    self.assertTrue('[localhost] local: dnsquerycheck --export-config -c %s -i %s -n 5 -p 53 -d localhost' % (CONFIG_FILE, audit_id) in output_string)

    # At this point, running 'nslookup server1' should return OK.
    # Otherwise, something above this line did not complete successfully 
    for dns_server_dict in test_dns_servers:
      #Making a bunch of useless records for each 'fake' DNS server
      dns_server = dns_server_dict['server_name']
      
      # Run nslookup to ensure we have access to the new servers.
      output = os.popen('nslookup %s' % dns_server)
      output_string = output.read()
      output.close()
      self.assertEqual('Server:\t\t127.0.0.1\n'
          'Address:\t127.0.0.1#53\n\n'
          'Name:\t%s\n'
          'Address: 127.0.0.1\n\n' % dns_server, output_string)

      server_number = dns_server.split('.')[0].strip('server')
      server_set = u'test_set_%s' % server_number

      server_view_name = u'test_view_%s' % dns_server
      server_zone_name = u'%s' %  dns_server
      server_zone_origin = u'%s.' % server_zone_name
      
      self.core_instance.MakeView(server_view_name)
      self.core_instance.MakeZone(server_zone_name, u'master',
                                  server_zone_origin, 
                                  view_name=server_view_name,
                                  make_any=False)
      self.core_instance.MakeRecord(u'soa', u'@', server_zone_name,
          {u'refresh_seconds': 28800, u'expiry_seconds': 604800,
           u'name_server': u'ns1.%s.' % dns_server, 
           u'minimum_seconds': 38400, u'retry_seconds': 3600, 
           u'serial_number': 1, u'admin_email': u'admin.%s.' % server_number}, 
           view_name=server_view_name)
      self.core_instance.MakeRecord(u'ns', u'@', server_zone_name,
        {u'name_server': u'ns1.%s.' % dns_server}, view_name=server_view_name)
      self.core_instance.MakeRecord(u'a', u'ns1', server_zone_name,
        {u'assignment_ip': u'127.0.0.1'}, view_name=server_view_name)
      for i in range(10):
        self.core_instance.MakeRecord(u'a', u'record%s' % i, server_zone_name,
          {u'assignment_ip': u'192.168.%s.%s' % (server_number, i)}, view_name=server_view_name)

      bind_dir = dns_server_dict['bind_dir']
      test_dir = dns_server_dict['test_dir']
      rndc_port = dns_server_dict['rndc_port']
      self.core_instance.MakeDnsServerSet(server_set)
      self.core_instance.MakeDnsServer(dns_server, SSH_USER, bind_dir, test_dir)
      self.core_instance.MakeDnsServerSetAssignments(dns_server, server_set)
      self.core_instance.MakeDnsServerSetViewAssignments(server_view_name, 1, server_set)
      self.core_instance.MakeViewToACLAssignments(server_view_name, server_set, u'any', 1)
      self.core_instance.MakeNamedConfGlobalOption(
          server_set,
          u'include "%s"; options { \n'
          u'pid-file "%s"; };\n'
          u'controls { inet 127.0.0.1 port %s allow { localhost; } '
          u'keys { rndc-key; }; };' % (RNDC_KEY, 
              os.path.join(dns_server_dict['bind_dir'], 'named.pid'),
              rndc_port))

    # We export so we know what we've done so far is valid.
    # If this export fails, something above this line was not successful.
    self.tree_exporter_instance.ExportAllBindTrees()
    audit_id = self.config_lib_instance.FindNewestDnsTreeFilename()[0]
    shutil.rmtree(self.tree_exporter_instance.backup_dir)

    # Running dnsexportconfig to all of the servers. 
    # This is where threading works or doesn't...
    output = os.popen(command_string)
    output_string = output.read()
    output.close()

    # Checking that each server executed each ConfigManager tool successfully
    #   With the exception of dnsquerycheck.  We can not successfully test
    #   that dnsquerycheck will succeed through dnsexportconfig due to the
    #   non default and unique ports of the name servers
    for i in range(num_test_machines):
      try:
        self.assertTrue('Finished - %s/server%s.unittest/named.conf.a' % (self.root_config_dir, i+1) in output_string)
        self.assertTrue('Finished - %s/server%s.unittest/named/test_view_server%s.unittest/server%s.unittest.db' % (self.root_config_dir, i+1, i+1, i+1) in output_string)
        self.assertTrue('[localhost] local: dnsservercheck --export-config -c %s -i %s -d server%s.unittest' % (CONFIG_FILE, audit_id+1, i+1) in output_string)
        self.assertTrue('[localhost] local: dnsconfigsync --export-config -i %s -c %s --ssh-id test_data/roster_id_dsa --rndc-key %s --rndc-conf %s -d server%s.unittest' % (audit_id+1, CONFIG_FILE, RNDC_KEY, RNDC_CONF, i+1) in output_string)
        self.assertTrue('[localhost] local: dnsquerycheck --export-config -c %s -i %s -n 5 -p 53 -d server%s.unittest' % (CONFIG_FILE, audit_id+1, i+1) in output_string)
      except AssertionError as e:
        print i+1
        raise

    # During the above execution of dnsexportconfig, dnsquerycheck will fail on all servers.
    # This will happen for the following reason. dnsexportconfig has a flag, '-p'
    #   which is passes onto dnsquerycheck. It is the flagto control what port
    #   dnsquerycheck queries for records on. (Default if 53) However, each 'fake' DNS server
    #   that we started earlier, runs on a different port.
    # So we need to run dnsquerycheck separately. 
    for dns_server_dict in test_dns_servers:
      command_string = ('python %s --config-file %s -p %s -i %s -d %s -n 0' % (
          QUERY_CHECK_EXEC, CONFIG_FILE, dns_server_dict['port'], audit_id + 1, 
          dns_server_dict['server_name']))
      command = os.popen(command_string)
      output = command.read()
      command.close()
      self.assertEqual(output, '')

    shutil.rmtree(THREADING_DIR)

  def testCheckConfig(self):
    output = os.popen('python %s -f --config-file %s '
    '--ssh-id %s --rndc-key %s --rndc-conf %s 2>/dev/null' % (
        EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY,
        RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    self.assertTrue('[localhost] local: dnstreeexport -c test_data/roster.conf --force' in lines)
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
        u'set1', 
        u'include "%s"; options { '
        u'pid-file "test_data/named.pid"; };\n'
        u'controls { inet 127.0.0.1 port %d allow { localhost; } '
        u'keys { rndc-key; }; };' % (RNDC_KEY, self.rndc_port)) # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'set1', u'any', 1)

    # We export so we know what we've done so far is valid.
    # If this export fails, something above this line is messed up.
    self.tree_exporter_instance.ExportAllBindTrees()
    shutil.rmtree(self.tree_exporter_instance.backup_dir)
  
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
    # Start named
    out = fabric_api.local('/usr/sbin/named -p %s -u %s -c %s/named.conf' % (
        self.port, SSH_USER, BINDDIR.rstrip('/')), capture=True)
    time.sleep(2)
   
    output = os.popen('python %s -f --config-file %s '
    '--ssh-id %s --rndc-key %s --rndc-conf %s -p %s' % (
        EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY,
        RNDC_CONF, self.port))
    lines = output.read().split('\n')
    output.close()

    audit_log_id = 15 #Makes for easier fixing of the unittest later
    self.assertTrue('[localhost] local: dnstreeexport -c test_data/roster.conf --force' in lines)
    self.assertTrue('[localhost] local: dnscheckconfig -i %s --config-file test_data/roster.conf -z /usr/sbin/named-checkzone -c /usr/sbin/named-checkconf -v'  % audit_log_id in lines)
    self.assertTrue('Finished - %s/%s/named.conf.a' % (self.root_config_dir, TEST_DNS_SERVER) in lines)
    self.assertTrue('Finished - %s/%s/named/test_view/sub.university.lcl.db' % (self.root_config_dir, TEST_DNS_SERVER) in lines)
    self.assertTrue('All checks successful' in lines)
    self.assertTrue('[localhost] local: dnsservercheck --export-config -c test_data/roster.conf -i %s -d %s' % (audit_log_id, TEST_DNS_SERVER) in lines)
    self.assertTrue('[localhost] local: dnsquerycheck --export-config -c test_data/roster.conf -i %s -n 5 -p %s -d %s' % (audit_log_id, self.port, TEST_DNS_SERVER) in lines)

    self.core_instance.MakeDnsServer(u'bad.server.local', SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSetAssignments(u'bad.server.local', u'set1')
    output = os.popen('export ROSTERTESTPATH=%s && export ROSTERTESTSMTPERROR='
        'server_error && python %s -f --config-file %s --ssh-id %s '
        '--rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY, RNDC_CONF))
    lines = output.read().split('\n')
    output.close()

    self.assertTrue('[localhost] local: dnscheckconfig -i %s --config-file test_data/roster.conf -z /usr/sbin/named-checkzone -c /usr/sbin/named-checkconf -v' % (audit_log_id + 3) in lines)

    smtp_server = self.config_instance.config_file['exporter']['smtp_server']
    self.assertTrue('%s is an invalid smtp server.' % smtp_server in lines)
    output = os.popen('export ROSTERTESTPATH=%s && export ROSTERTESTSMTPERROR='
                      'connect_error && python %s -f --config-file %s --ssh-id %s '
                      '--rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY, RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    self.assertTrue('Failed to connect to %s.' % smtp_server in lines)

    output = os.popen('export ROSTERTESTPATH=%s && export ROSTERTESTSMTPERROR='
        'message_error && python %s -f --config-file %s --ssh-id %s '
        '--rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY, RNDC_CONF))
    lines = output.read().split('\n')
    output.close()
    self.assertTrue('%s is an invalid email address.' % self.config_instance.config_file[
        'exporter']['failure_notification_email'] in lines)

    # Can't connect to server (dnscheckconf)
    output = os.popen('export ROSTERTESTPATH=%s && python %s -f --config-file %s --ssh-id %s '
        '--rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY, RNDC_CONF))
    out_str = output.read()
    output.close()
    self.assertTrue("<p>Return Code: 1<br/><br/>ERROR: Could not connect to "
                    "bad.server.local via SSH.<br/></p><br/>" in out_str)

    # No ns record for zone (dnscheckconf)
    self.core_instance.RemoveDnsServer(u'bad.server.local')
    self.core_instance.RemoveRecord(u'a', u'ns', u'sub.university.lcl', {u'assignment_ip': u'192.168.1.103'}, u'test_view')
    output = os.popen('export ROSTERTESTPATH=%s && python %s -f --config-file %s --ssh-id %s '
        '--rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY, RNDC_CONF))
    out_str = output.read()
    output.close()
    self.assertTrue("""Content-Type: text/plain; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""MIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\n\n""" in out_str)
    self.assertTrue("""<h4>dnscheckconfig -i 24 --config-file """
                    """test_data/roster.conf -z /usr/sbin/named-checkzone -c """
                    """/usr/sbin/named-checkconf -v</h4>""" in out_str)
    self.assertTrue("""<p>Return Code: 1<br/><br/>Finished - %s/%s/named.conf.a""" % (self.config_lib_instance.root_config_dir, TEST_DNS_SERVER) in out_str)
    self.assertTrue("""ERROR: zone sub.university.lcl/IN: NS 'ns.sub.university.lcl' has no address records (A or AAAA)\n""" in out_str)
    self.assertTrue("""zone sub.university.lcl/IN: not loaded due to errors.""" in out_str)

    self.assertTrue("""dnscheckconfig -i 24 --config-file """
                    """test_data/roster.conf -z /usr/sbin/named-checkzone -c """
                    """/usr/sbin/named-checkconf -v""" in out_str)
    self.assertTrue("""Finished - %s/%s/named.conf.a""" % (self.config_lib_instance.root_config_dir, TEST_DNS_SERVER) in out_str)
    self.assertTrue("""ERROR: zone sub.university.lcl/IN: NS 'ns.sub.university.lcl' has no address records (A or AAAA)""" in out_str)

    self.core_instance.MakeRecord(u'a', u'ns', u'sub.university.lcl', {u'assignment_ip': u'192.168.1.103'}, u'test_view')

    # bad test directory on server (dnscheckconf)
    self.core_instance.UpdateDnsServer(TEST_DNS_SERVER, TEST_DNS_SERVER, SSH_USER, u'/bad/directory/', TESTDIR)
    output = os.popen('export ROSTERTESTPATH=%s && python %s -f --config-file %s --ssh-id %s '
        '--rndc-key %s  --rndc-conf %s 2>&1' % (os.getcwd(),
            EXEC, CONFIG_FILE, SSH_ID, RNDC_KEY, RNDC_CONF))
    out_str = output.read()
    output.close()
    self.assertTrue("""Content-Type: text/plain; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""MIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\n\n""" in out_str)
    self.assertTrue("""ERROR: The remote BIND directory /bad/directory/ does not exist or """ in out_str)
    self.assertTrue("""the user %s does not have permission.""" % SSH_USER in out_str)

    self.assertTrue("""Content-Type: text/html; charset="us-ascii"\n""" in out_str)
    self.assertTrue("""<br/><h4>dnsservercheck --export-config -c test_data/roster.conf -i 27 -d %s</h4>""" % TEST_DNS_SERVER in out_str)
    self.assertTrue("""The remote BIND directory /bad/directory/ does not exist or """ in out_str)
    self.assertTrue("""the user %s does not have permission.<br/></p></body></html>""" % SSH_USER in out_str)
    self.core_instance.UpdateDnsServer(TEST_DNS_SERVER, TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)

if( __name__ == '__main__' ):
      unittest.main()
