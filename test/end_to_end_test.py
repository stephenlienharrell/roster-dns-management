#!/usr/bin/env python

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

"""Regression test for roster cl tools

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.

This test REQUIRES SELinux or Apparmor to be reconfigured or disabled
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import bz2
import ConfigParser
import glob
import os
import re
import shutil
import sys
import socket
import string
import subprocess
import tarfile
import threading
import time
import getpass
import unittest


UNITTEST_CONFIG = 'test_data/roster.conf'
HOST = u'localhost'
CREDFILE = '%s/.dnscred' % os.getcwd()
USERNAME = 'shuey'
PASSWORD = 'testpass'
TESTDIR = 'unittest_dir'
#bind binary files
CHECKZONE_EXEC = '/usr/sbin/named-checkzone'
CHECKCONF_EXEC = '/usr/sbin/named-checkconf'
#SSH
SSH_ID = 'test_data/roster_id_dsa'
SSH_USER = getpass.getuser()
TEST_DNS_SERVER = u'localhost' # change this to real bind servers
TEST_DNS_SERVER2 = u'testns2'
SESSION_KEYFILE = 'test_data/session.key'
LOCKFILE = '/tmp/roster_lock_file'
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

class InitThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.init_instance = None

  def run(self):
    ## Daemon Thread to start the roster init command
    command_string = (
        '%s/init start' % TESTDIR)
    self.daemon_instance = os.popen(command_string)
    output = self.daemon_instance.read()
    self.daemon_instance.close()

class TestComplete(unittest.TestCase):

  def setUp(self):
    rndc_key = open(RNDC_KEY, 'w')
    rndc_key.write(RNDC_KEY_DATA)
    rndc_key.close()
    rndc_conf = open(RNDC_CONF, 'w')
    rndc_conf.write(RNDC_CONF_DATA)
    rndc_conf.close()

    config = ConfigParser.ConfigParser()
    config.read(UNITTEST_CONFIG)
    self.login = config.get('database','login')
    self.password = config.get('database','passwd')
    self.database = config.get('database','database')
    self.server = config.get('database','server')
    self.backup_dir = config.get('exporter','backup_dir')
    self.root_config_dir = config.get('exporter','root_config_dir')
    self.key = config.get('server','ssl_key_file')
    self.cert = config.get('server','ssl_cert_file')
    self.logfile = config.get('server','server_log_file')
    self.ldap = config.get('fakeldap','server')
    self.binddn = config.get('fakeldap','binddn')
    self.userconfig = './completeconfig.conf'
    self.toolsconfig = './completetoolsconfig.conf'
    self.testfile = '%s/testfile' % TESTDIR
    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port
    self.port = PickUnusedPort()
    self.rndc_port = PickUnusedPort()
    self.named_port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.named_dir = config.get('exporter', 'named_dir')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)
    if( os.path.exists(self.userconfig) ):
      os.remove(self.userconfig)
    if( os.path.exists(self.toolsconfig) ):
      os.remove(self.toolsconfig)
    if( os.path.exists(self.testfile) ):
      os.remove(self.testfile)
    if( os.path.exists(TESTDIR) ):
      shutil.rmtree(TESTDIR)
    if( os.path.exists(self.backup_dir) ):
      shutil.rmtree(self.backup_dir)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    ## kill rosterd deamon threads
    if( os.path.exists(LOCKFILE) ):
      os.remove(LOCKFILE)
    if( os.path.exists('%s/named' % self.named_dir) ):
      shutil.rmtree('%s/named' % self.named_dir)
    if( os.path.exists('%s/named.conf' % self.named_dir) ):
      os.remove('%s/named.conf' % self.named_dir)
    if( os.path.exists('./temp_dir') ):
      shutil.rmtree('./temp_dir')

  def testEndToEnd(self):
    ## Bootstraps
    ## Bootstrap: Config file and Database
    ## roster_database_bootstrap -c <config-file> -u <login> -U <roster-user> 
    ## -p <passwd> -d <database> -n <db)host> --ssl-cert <cert-file>
    ## --ssl-key <key-file> --root-config-dir <root_dir>
    ## --backup-dir <backup-dir> -i <init-file> --server-log-file <log-file>
    ## --run-as <uuid> --force
    command_string = (
        'python ../roster-core/scripts/roster_database_bootstrap '
        '-c %s -u %s -U %s -p %s '
        '-d %s -n %s '
        '--ssl-cert %s --ssl-key %s '
        '--root-config-dir %s --backup-dir %s -i %s/init --server-log-file %s '
        '--run-as %s --force' % (
            self.userconfig,
            self.login, USERNAME, self.password,
            self.database,
            self.server,
            self.cert, self.key,
            TESTDIR,
            self.backup_dir,
            TESTDIR,
            self.logfile,
            os.getuid()))
    bootstrapDB = subprocess.Popen(
        command_string, shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    ## The first number represents the auth_module chosen. This can change if
    ## more modules are added later and appear before general_ldap.
    bootstrapDB.communicate('1\nuid=%%%%s,ou=People,'
        'dc=dc,dc=university,dc=edu\n'
        '%s\nVERSION3\n%s\n' % (
            self.cert,
            self.ldap))
    if( not os.path.exists(
        '%s' % self.userconfig) ):
      self.fail('Config file was not created.')
    if( not os.path.exists(
        '%s/init' % TESTDIR) ):
      self.fail('Init file was not created.')

    ## Bootstrap: User Tools
    ## roster_user_tools_bootstrap --server <server> --cred-file <credfile>
    ## --config-file <config-file> 
    command_string = (
        'python ../roster-user-tools/scripts/roster_user_tools_bootstrap '
        '--server %s --cred-file %s '
        '--config-file %s' % (
            self.server_name,
            CREDFILE,
            self.toolsconfig))
    bootstrapUserTools = subprocess.Popen(
        command_string, shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    bootstrapUserTools.communicate()
    if( not os.path.exists(
        '%s' % self.toolsconfig) ):
      self.fail('User tools config file was not created.')

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
    named_proc = os.popen('/usr/sbin/named -p %s -u %s -c %s/named.conf' % ( 
        self.named_port, SSH_USER, self.named_dir))
    output = named_proc.read()
    time.sleep(2)

    ## Turn off the killswitch and add fakeldap to the config
    config = ConfigParser.ConfigParser()
    config.read(self.userconfig)
    if( not config.has_section('fakeldap') ):
      config.add_section('fakeldap')
      config.set('fakeldap','binddn',self.binddn)
      config.set('fakeldap','server',self.ldap)
    config.set('credentials','authentication_method','fakeldap')
    config.set('server','lock_file', LOCKFILE)
    config.set('server','server_killswitch','off')
    config.set('server','port',self.port)
    handle = open(self.userconfig,'w')
    config.write(handle)
    handle.close()

    ## Init and RosterD
    ## Inject --unit-test and other userflags into init.d
    handle = open('%s/init' % TESTDIR,'r')
    filestring = handle.read()
    handle.close()
    filestring = filestring.replace('rosterd &',
        'rosterd ' 
        '--config-file %s -p %s -c %s -k %s --unit-test '% (
            self.userconfig, self.port, self.cert, self.key),1)
    handle = open('%s/init' % TESTDIR,'w')
    handle.write(filestring)
    handle.close()
    ## ERROR: Roster will not start with a world writable config file.
    os.system('chmod 600 %s' % self.userconfig)
    os.system('chmod 760 %s/init' % TESTDIR)
    self.init_thread = InitThread()
    self.init_thread.start()
    time.sleep(3)


    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server -d dns1
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server -d %s '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER: %s\n' % TEST_DNS_SERVER)
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server -d dns2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server -d %s '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER2, 
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER: %s\n' % TEST_DNS_SERVER2)
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server_set -e set1
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server_set -e set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET: set1\n')
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver assignment -d dns1 -e set1
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'assignment -d %s -e set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET ASSIGNMENT: dns_server: %s dns_server_set: set1\n' % TEST_DNS_SERVER)
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server_set -e set3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server_set -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET: set3\n')
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver assignment -d dns2 -e set3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'assignment -d %s -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER2,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET ASSIGNMENT: dns_server: %s dns_server_set: set3\n' % TEST_DNS_SERVER2)
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server_set -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server_set -e set2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET: set2\n')
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver assignment -d dns1 -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'assignment -d %s -e set2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET ASSIGNMENT: dns_server: %s dns_server_set: set2\n' % TEST_DNS_SERVER)
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server_set -e set4
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server_set -e set4 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET: set4\n')
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver assignment -d dns2 -e set4
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'assignment -d %s -e set4 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER2,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET ASSIGNMENT: dns_server: %s dns_server_set: set4\n' % TEST_DNS_SERVER2)
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server -d dns3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server -d dns3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER: dns3\n')
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server_set -e set5
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server_set -e set5 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET: set5\n')
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver assignment -d dns3 -e set5
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'assignment -d dns3 -e set5 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET ASSIGNMENT: dns_server: dns3 dns_server_set: set5\n')
    command.close()
    ## User tool: dnsmkdnsserver
    ## dnsmkdnsserver dns_server -d dns3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkdnsserver '
        'dns_server -d dns3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: DNS Server "dns3" already exists.\n')
    command.close()
    ## User tool: dnslsdnsservers
    ## dnslsdnsservers dns_server
    command_string = (
        'python ../roster-user-tools/scripts/dnslsdnsservers '
        'dns_server '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'dns_server\n'
        '----------\n'
        'dns3\n'
        '%s\n'
        '%s\n\n' % (TEST_DNS_SERVER, TEST_DNS_SERVER2) )
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver assignment -d dns2 -e set4
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'assignment -d %s -e set4 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER2,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET ASSIGNMENT: dns_server_set: set4 dns_server: %s\n' % TEST_DNS_SERVER2)
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server -d dns3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server -d dns3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER: dns3\n')
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server_set -e set4
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server_set -e set4 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET: set4\n')
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server_set -e set4
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server_set -e set5 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET: set5\n')
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server -d dns2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server -d NONE '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: DNS server "NONE" does not exist.\n')
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server_set -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server_set -e NONE '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: DNS server set "NONE" does not exist.\n')
    command.close()
    ## User tool: dnslsdnsservers
    ## dnslsdnsservers dns_server
    command_string = (
        'python ../roster-user-tools/scripts/dnslsdnsservers '
        'dns_server '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'dns_server\n'
        '----------\n'
        '%s\n'
        '%s\n\n' % (TEST_DNS_SERVER, TEST_DNS_SERVER2))
    command.close()
    ## User tool: dnslsdnsservers
    ## dnslsdnsservers dns_server
    command_string = (
        'python ../roster-user-tools/scripts/dnslsdnsservers '
        'dns_server_set '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'dns_server_set\n'
        '--------------\n'
        'set1\n'
        'set2\n'
        'set3\n\n')
    command.close()
    ## User tool: dnslsdnsservers
    ## dnslsdnsservers dns_server
    command_string = (
        'python ../roster-user-tools/scripts/dnslsdnsservers '
        'assignment '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'set  dns_servers\n'
        '----------------\n'
        'set1 %s\n'
        'set2 %s\n'
        'set3 %s\n\n' % (
          TEST_DNS_SERVER, TEST_DNS_SERVER, TEST_DNS_SERVER2))
    command.close()

    ## User tool: dnsauditlog
    ## dnslsauditlog --success 0
    command_string = (
        'python ../roster-user-tools/scripts/dnslsauditlog '
        '--success 0 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = re.sub("\s+"," ",output)
    output = output.split(' ')
    self.assertEqual(output[10:16],
        ['shuey', '0', "{'dns_server_name':", "u'%s'," % TEST_DNS_SERVER2, "'dns_server_set_name':", "u'set4'}"])
    command.close()
    ## User tool: dnsauditlog
    ## dnslsauditlog --success 1
    command_string = (
        'python ../roster-user-tools/scripts/dnslsauditlog '
        '--success 1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = re.sub("\s+"," ",output)
    output = output.split(' ')
    #output[9] is a timestamp that will change every time the test is run
    self.assertEqual(output[7:14],
        ['1', 'MakeDnsServer', output[9], 'shuey', '1', 
         '{\'dns_server_name\':', u"u\'%s\'}" % TEST_DNS_SERVER])
    self.assertEqual(output[24:30],
        ['shuey', '1', '{\'dns_server_set_name\':', 'u\'set1\'}', 
         '4', 'MakeDnsServerSetAssignments'])
    command.close()

    ## User tool: dnsmkreservedword
    ## dnsmkreservedword -w testreserved
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkreservedword '
        '-w testreserved '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED RESERVED_WORD: testreserved\n')
    command.close()
    ## User tool: dnsmkreservedword
    ## dnsmkreservedword -w testreserved
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkreservedword '
        '-w darn '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED RESERVED_WORD: darn\n')
    command.close()
    ## User tool: dnslsreservedwords
    ## dnslsreservedwords
    command_string = (
        'python ../roster-user-tools/scripts/dnslsreservedwords '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'darn\n'
        'testreserved\n')
    command.close()
    ## User tool: dnsrmreservedword
    ## dnsrmreservedword -w damn
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmreservedword '
        '-w darn '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED RESERVED_WORD: darn\n')
    command.close()
    ## User tool: dnsrmreservedword
    ## dnsrmreservedword -w NONE 
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmreservedword '
        '-w NONE '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Reserved word not found.\n')
    command.close()
    ## User tool: dnsmkreservedword
    ## dnsmkreservedword -w testreserved
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkreservedword '
        '-w testreserved '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = output.split(')')
    self.assertEqual(output[2],
        ' (1062, "Duplicate entry \'testreserved\' for key 2"')
    command.close()
    ## User tool: dnslsreservedwords
    ## dnslsreservedwords
    command_string = (
        'python ../roster-user-tools/scripts/dnslsreservedwords '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'testreserved\n')
    command.close()

    ## Test reserved words
    ## dnsmkusergroup user -n sharrell -a 128
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'user -n sharrell -a 128 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED USER: username: sharrell access_level: 128\n')
    command.close()
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkacl '
        '-a testreserved --cidr-block 168.192.1.0/24 '
        '-u %s -p %s '
        '-s %s --config-file %s -c %s ' % (
            'sharrell', 'test', self.server_name,
            self.toolsconfig, CREDFILE))
    command = os.popen(command_string)
    output = command.read()
    self.assertEqual(output,
        'USER ERROR: Reserved word testreserved found, unable to complete request\n')
    command.close()

    ## User tool: dnsmkacl
    ## dnsmkacl -a test_acl --cidr-block 168.192.1.0/24 --allow
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkacl '
        '-a test_acl --cidr-block 168.192.1.0/24 '
        '-u %s -p %s '
        '-s %s --config-file %s -c %s ' % (
            USERNAME, PASSWORD, self.server_name,
            self.toolsconfig, CREDFILE))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED ACL: acl: test_acl cidr_block: 168.192.1.0/24\n')
    command.close()
    ## User tool: dnsmkacl
    ## dnsmkacl -a test_acl2 --cidr-block 168.192.2.0/24 --allow
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkacl '
        '-a test_acl2 --cidr-block 168.192.2.0/24 '
        '-u %s -p %s '
        '-s %s --config-file %s -c %s ' % (
            USERNAME, PASSWORD, self.server_name,
            self.toolsconfig, CREDFILE))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED ACL: acl: test_acl2 cidr_block: 168.192.2.0/24\n')
    command.close()
    ## User tool: dnslsacl
    ## dnslsacl
    command_string = (
        'python ../roster-user-tools/scripts/dnslsacl '
        '-u %s -p %s -s %s --config-file %s -c %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig,
            CREDFILE))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Name      CIDR Block\n'
        '--------------------\n'
        'test_acl2 168.192.2.0/24\n'
        'any       None\n'
        'test_acl  168.192.1.0/24\n\n')
    command.close()
    ## User tool: dnsmkacl
    ## dnsmkacl -a test_acl3 --cidr-block 168.192.2.0/24
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkacl '
        '-a test_acl3 --cidr-block 168.192.3.0/24 '
        '-u %s -p %s -s %s --config-file %s -c %s ' % (
            USERNAME, PASSWORD, self.server_name,
            self.toolsconfig, CREDFILE))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED ACL: acl: test_acl3 cidr_block: 168.192.3.0/24\n')
    command.close()
    ## User tool: dnslsacl
    ## dnslsacl
    command_string = (
        'python ../roster-user-tools/scripts/dnslsacl '
        '-u %s -p %s -s %s --config-file %s -c %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig,
            CREDFILE))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Name      CIDR Block\n'
        '--------------------\n'
        'test_acl  168.192.1.0/24\n'
        'test_acl2 168.192.2.0/24\n'
        'test_acl3 168.192.3.0/24\n'
        'any       None\n\n')
    command.close()
    ## User tool: dnsrmacl
    ## dnsrmacl -a test_acl2 --force 
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmacl '
        '-a test_acl3 --force '
        '-u %s -p %s '
        '-s %s --config-file %s -c %s ' % (
            USERNAME, PASSWORD, self.server_name,
            self.toolsconfig, CREDFILE))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED ACL: acl: test_acl3\n')
    command.close()
    ## User tool: dnslsacl
    ## dnslsacl
    command_string = (
        'python ../roster-user-tools/scripts/dnslsacl '
        '-u %s -p %s -s %s --config-file %s -c %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig,
            CREDFILE))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Name      CIDR Block\n'
        '--------------------\n'
        'test_acl2 168.192.2.0/24\n'
        'any       None\n'
        'test_acl  168.192.1.0/24\n\n')
    command.close()

    ## User tool: dnsmkview
    ## dnsmkview view -v test_view --acl test_acl
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'view -v test_view --acl test_acl --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED VIEW: view_name: test_view options None\n'
        'ADDED VIEW ACL ASSIGNMENT: view: test_view acl: test_acl allowed: 1\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview dns_server_set -v test_view -e set1
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'dns_server_set -v test_view -e set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET VIEW ASSIGNMENT: view_name: test_view dns_server_set: set1\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview view -v test_view2 --acl test_acl
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'view -v test_view2 --acl test_acl --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
         'ADDED VIEW: view_name: test_view2 options None\n'
         'ADDED VIEW ACL ASSIGNMENT: view: test_view2 acl: test_acl allowed: 1\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview acl -v test_view2 -a test_acl2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'acl -v test_view2 -a test_acl2 --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED VIEW ACL ASSIGNMENT: view: test_view2 acl: test_acl2\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview dns_server_set -v test_view2 -e set1
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'dns_server_set -v test_view2 -e set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
         'ADDED DNS SERVER SET VIEW ASSIGNMENT: view_name: test_view2 dns_server_set: set1\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview dns_server_set -v test_view2 -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'dns_server_set -v test_view2 -e set2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
         'ADDED DNS SERVER SET VIEW ASSIGNMENT: view_name: test_view2 dns_server_set: set2\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview dns_server_set -v test_view2 -e set3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'dns_server_set -v test_view2 -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
         'ADDED DNS SERVER SET VIEW ASSIGNMENT: view_name: test_view2 dns_server_set: set3\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview view -v test_view3 --acl test_acl
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'view -v test_view3 --acl test_acl --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
         'ADDED VIEW: view_name: test_view3 options None\n'
         'ADDED VIEW ACL ASSIGNMENT: view: test_view3 acl: test_acl allowed: 1\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview dns_server_set -v test_view3 -e set3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'dns_server_set -v test_view3 -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
         'ADDED DNS SERVER SET VIEW ASSIGNMENT: view_name: test_view3 dns_server_set: set3\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews view
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view_name  view_options\n'
        '-----------------------\n'
        'test_view2\n'
        'test_view\n'
        'test_view3\n\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews dns_server_set
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'dns_server_set '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'dns_server_set view_name\n'
        '------------------------\n'
        'set1           test_view, test_view2\n'
        'set2           test_view2\n'
        'set3           test_view2, test_view3\n\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews dns_server_set
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'acl '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view_name  acl_name  acl_range_allowed\n'
        '--------------------------------------\n'
        'test_view  test_acl  True\n'
        'test_view2 test_acl  True\n'
        'test_view2 test_acl2 True\n'
        'test_view3 test_acl  True\n\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews view_subset
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'view_subset '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view       view_subset\n'
        '----------------------\n'
        'test_view2 any, test_view2\n'
        'test_view  any, test_view\n'
        'test_view3 any, test_view3\n\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview dns_server_set -v test_view3 -e set3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'acl -v test_view3 -a test_acl --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED VIEW TO ACL ASSIGNMENT: view_name: test_view3 acl_name: test_acl\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews dns_server_set
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'acl '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view_name  acl_name  acl_range_allowed\n'
        '--------------------------------------\n'
        'test_view  test_acl  True\n'
        'test_view2 test_acl  True\n'
        'test_view2 test_acl2 True\n\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview dns_server_set -v test_view3 -e set3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'dns_server_set -v test_view3 -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET VIEW ASSIGNMENT: view_name: test_view3 dns_server_set: set3\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews dns_server_set
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'dns_server_set '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'dns_server_set view_name\n'
        '------------------------\n'
        'set1           test_view, test_view2\n'
        'set2           test_view2\n'
        'set3           test_view2\n\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview dns_server_set -v test_view3 -e set3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'view -v test_view3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED VIEW view_name: view_name: test_view3 options None\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews view
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view_name  view_options\n'
        '-----------------------\n'
        'test_view2\n'
        'test_view\n\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview view -v test_view --acl test_acl
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'view -v test_subview --acl test_acl --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
    'ADDED VIEW: view_name: test_subview options None\n'
    'ADDED VIEW ACL ASSIGNMENT: view: test_subview acl: test_acl allowed: 1\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview view -v test_subview -V 
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'view_subset -v test_subview -V test_subview '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED VIEW ASSIGNMENT: view_name: test_subview view_subset: test_subview\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview view_subset -v test_view4 -V test_view
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'view_subset -V test_subview -v test_view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
         'ADDED VIEW ASSIGNMENT: view_name: test_view view_subset: test_subview\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews view
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view_name    view_options\n'
        '-------------------------\n'
        'test_subview\n'
        'test_view2\n'
        'test_view\n\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews dns_server_set
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'dns_server_set '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'dns_server_set view_name\n'
        '------------------------\n'
        'set1           test_view, test_view2\n'
        'set2           test_view2\n'
        'set3           test_view2\n\n')
    command.close()
    ## User tool: dnslsviews
    ## dnslsviews dns_server_set
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'acl '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view_name    acl_name  acl_range_allowed\n'
        '----------------------------------------\n'
        'test_view    test_acl  True\n'
        'test_view2   test_acl  True\n'
        'test_view2   test_acl2 True\n'
        'test_subview test_acl  True\n\n')
    command.close()
    ## User tool: dnslsviews
    ## /dnslsviews view_subset
    command_string = (
        'python ../roster-user-tools/scripts/dnslsviews '
        'view_subset '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'view         view_subset\n'
        '------------------------\n'
        'test_subview any\n'
        'test_view2   any, test_view2\n'
        'test_view    any, test_subview, test_view\n\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview view -v NONE
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'view -v NONE '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: View "NONE" does not exist.\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview dns_server_set -v NONE -e set1 
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'dns_server_set -v NONE -e set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: View "NONE" does not exist.\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview dns_server_set -v test_view -e NONE
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'dns_server_set -v test_view -e NONE '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Dns Server Set "NONE" does not exist.\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview acl -v NONE -a test_acl
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'acl -v NONE -a test_acl '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: View "NONE" does not exist.\n')
    command.close()
    ## User tool: dnsrmview
    ## dnsrmview acl -v test_view -a NONE
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmview '
        'acl -v test_view -a NONE --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: View ACL Assignment does not exist.\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview view -v test_view2 --acl test_acl
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'view -v test_view2 --acl test_acl --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: View "test_view2" already exists.\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview dns_server_set -v test_view2 -e set1 
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'dns_server_set -v test_view2 -e set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = output.split(')')
    self.assertEqual(output[2],
        ' (1062, "Duplicate entry \'set1-test_view2\' for key 2"')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview acl -v test_view2 -a test_acl
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'acl -v test_view2 --acl test_acl --allow '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: View ACL Assignment already exists.\n')
    command.close()
    ## User tool: dnsmkview
    ## dnsmkview dns_server_set -v test_view -e set1
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkview '
        'dns_server_set -v test_view -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED DNS SERVER SET VIEW ASSIGNMENT: view_name: test_view dns_server_set: set3\n')
    command.close()

    ## User tool: dnsmkzone
    ## dnsmkzone forward -z test_zone -v test_view -t master --origin university.edu.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'forward -z test_zone -v test_view -t master --origin university.edu. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone zone_type: master '
        'zone_origin: university.edu. zone_options: None '
        'view_name: test_view\n')
    command.close()
    ## User tool: dnsmkzone
    ## dnsmkzone forward -z test_zone2 -v test_view2 -t master --origin 1.168.192.in-addr.arpa.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'forward -z test_zone2 -v test_view2 -t master --origin 1.168.192.in-addr.arpa. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone2 zone_type: master '
        'zone_origin: 1.168.192.in-addr.arpa. zone_options: None '
        'view_name: test_view2\n')
    command.close()
    ## User tool: dnsmkzone
    ## dnsmkzone reverse -z test_zone3 -v test_view -t master --origin 2.168.192.in-addr.arpa.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'reverse -z test_zone3 -v test_view -t master --origin 2.168.192.in-addr.arpa. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED REVERSE ZONE: zone_name: test_zone3 zone_type: master '
        'zone_origin: 2.168.192.in-addr.arpa. zone_options: None '
        'view_name: test_view\n'
        'ADDED REVERSE RANGE ZONE ASSIGNMENT: zone_name: test_zone3 '
        'cidr_block: 192.168.2/24 \n')
    command.close()
    ## User tool: dnsmkzone
    ## dnsmkzone reverse -z test_zone4 -v test_view2 -t master --origin 3.168.192.in-addr.arpa.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'reverse -z test_zone4 -v test_view2 -t master --origin 3.168.192.in-addr.arpa. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED REVERSE ZONE: zone_name: test_zone4 zone_type: master '
        'zone_origin: 3.168.192.in-addr.arpa. zone_options: None '
        'view_name: test_view2\n'
        'ADDED REVERSE RANGE ZONE ASSIGNMENT: zone_name: test_zone4 '
        'cidr_block: 192.168.3/24 \n')
    command.close()
    ## User tool: dnsmkzone
    ## dnsmkzone reverse -v test_view -t master --origin 5.168.192.in-addr.arpa.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'forward -z test_zone5 -v test_view -t master --origin 5.168.192.in-addr.arpa. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED FORWARD ZONE: zone_name: test_zone5 zone_type: master '
        'zone_origin: 5.168.192.in-addr.arpa. zone_options: None '
        'view_name: test_view\n')
    command.close()
    ## User tool: dnsmkzone
    ## dnsmkzone reverse -z test_zone6 -v test_view2 -t master --origin 6.168.192.in-addr.arpa.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'reverse -z test_zone6 -v test_view2 -t master --origin 6.168.192.in-addr.arpa. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED REVERSE ZONE: zone_name: test_zone6 zone_type: master '
        'zone_origin: 6.168.192.in-addr.arpa. zone_options: None '
        'view_name: test_view2\n'
        'ADDED REVERSE RANGE ZONE ASSIGNMENT: zone_name: test_zone6 '
        'cidr_block: 192.168.6/24 \n')
    command.close()
    ## User tool: dnsmkzone
    ## dnsmkzone reverse -v test_view -t master --origin 5.168.192.in-addr.arpa.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'forward -z test_zone5 -v test_view -t master --origin 5.168.192.in-addr.arpa. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = output.split(')')
    self.assertEqual(output[2],
        ' (1062, "Duplicate entry \'test_zone5-test_view_dep\' for key 2"')
    command.close()
    ## User tool: dnsmkzone
    ## dnsmkzone reverse -z test_zone6 -v test_view2 -t master --origin 6.168.192.in-addr.arpa.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'reverse -z test_zone6 -v test_view2 -t master --origin 6.168.192.in-addr.arpa. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = output.split(')')
    self.assertEqual(output[2],
        ' (1062, "Duplicate entry \'test_zone6-test_view2_dep\' for key 2"')
    command.close()
    ## User tool: dnslszones
    ## dnslszones all
    command_string = (
        'python ../roster-user-tools/scripts/dnslszones '
        'all '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'zone_name  view_name  zone_type zone_origin             zone_options cidr_block\n'
        '-------------------------------------------------------------------------------\n'
        'test_zone  test_view  master    university.edu.                      -\n'
        'test_zone  any        master    university.edu.                      -\n'
        'test_zone3 test_view  master    2.168.192.in-addr.arpa.              192.168.2/24\n'
        'test_zone3 any        master    2.168.192.in-addr.arpa.              192.168.2/24\n'
        'test_zone2 test_view2 master    1.168.192.in-addr.arpa.              -\n'
        'test_zone2 any        master    1.168.192.in-addr.arpa.              -\n'
        'test_zone5 test_view  master    5.168.192.in-addr.arpa.              -\n'
        'test_zone5 any        master    5.168.192.in-addr.arpa.              -\n'
        'test_zone4 test_view2 master    3.168.192.in-addr.arpa.              192.168.3/24\n'
        'test_zone4 any        master    3.168.192.in-addr.arpa.              192.168.3/24\n'
        'test_zone6 test_view2 master    6.168.192.in-addr.arpa.              192.168.6/24\n'
        'test_zone6 any        master    6.168.192.in-addr.arpa.              192.168.6/24\n\n')
    command.close()
    ## User tool: dnslszones
    ## dnslszones forward
    command_string = (
        'python ../roster-user-tools/scripts/dnslszones '
        'forward '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'zone_name  view_name  zone_type zone_origin             zone_options cidr_block\n'
        '-------------------------------------------------------------------------------\n'
        'test_zone  test_view  master    university.edu.                      -\n'
        'test_zone  any        master    university.edu.                      -\n'
        'test_zone2 test_view2 master    1.168.192.in-addr.arpa.              -\n'
        'test_zone2 any        master    1.168.192.in-addr.arpa.              -\n'
        'test_zone5 test_view  master    5.168.192.in-addr.arpa.              -\n'
        'test_zone5 any        master    5.168.192.in-addr.arpa.              -\n\n')
    command.close()
    ## User tool: dnslszones
    ## dnslszones all
    command_string = (
        'python ../roster-user-tools/scripts/dnslszones '
        'reverse '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'zone_name  view_name  zone_type zone_origin             zone_options cidr_block\n'
        '-------------------------------------------------------------------------------\n'
        'test_zone3 test_view  master    2.168.192.in-addr.arpa.              192.168.2/24\n'
        'test_zone3 any        master    2.168.192.in-addr.arpa.              192.168.2/24\n'
        'test_zone4 test_view2 master    3.168.192.in-addr.arpa.              192.168.3/24\n'
        'test_zone4 any        master    3.168.192.in-addr.arpa.              192.168.3/24\n'
        'test_zone6 test_view2 master    6.168.192.in-addr.arpa.              192.168.6/24\n'
        'test_zone6 any        master    6.168.192.in-addr.arpa.              192.168.6/24\n\n')
    command.close()
    ## User tool: dnsrmzone
    ## dnsrmzone -z test_zone5 -v test_view
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmzone '
        '-z test_zone5 -v test_view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED ZONE: zone_name: test_zone5 view_name: test_view\n')
    ## User tool: dnsrmzone
    ## dnsrmzone -z test_zone6 -v test_view2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmzone '
        '-z test_zone6 --force '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED ZONE: zone_name: test_zone6 view_name: None\n')
    ## User tool: dnsrmzone
    ## dnsrmzone -z NONE -v test_view
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmzone '
        '-z NONE -v test_view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Zone "NONE" does not exist in "test_view" view.\n')
    ## User tool: dnsrmzone
    ## dnsrmzone -z test_zone -v NONE 
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmzone '
        '-z testzone -v NONE '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: View not found.\n')
    ## User tool: dnslszones
    ## dnslszones all
    command_string = (
        'python ../roster-user-tools/scripts/dnslszones '
        'all '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'zone_name  view_name  zone_type zone_origin             zone_options cidr_block\n'
        '-------------------------------------------------------------------------------\n'
        'test_zone  test_view  master    university.edu.                      -\n'
        'test_zone  any        master    university.edu.                      -\n'
        'test_zone3 test_view  master    2.168.192.in-addr.arpa.              192.168.2/24\n'
        'test_zone3 any        master    2.168.192.in-addr.arpa.              192.168.2/24\n'
        'test_zone2 test_view2 master    1.168.192.in-addr.arpa.              -\n'
        'test_zone2 any        master    1.168.192.in-addr.arpa.              -\n'
        'test_zone5 any        master    5.168.192.in-addr.arpa.              -\n'
        'test_zone4 test_view2 master    3.168.192.in-addr.arpa.              192.168.3/24\n'
        'test_zone4 any        master    3.168.192.in-addr.arpa.              192.168.3/24\n\n')
    command.close()
    ## User tool: dnsrmzone
    ## dnsrmzone -z test_zone5 -v test_view
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmzone '
        '-z test_zone5 --force '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED ZONE: zone_name: test_zone5 view_name: None\n')


    ## User tool: dnsmkusergroup
    ## dnsmkusergroup group -g test_group
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'group -g test_group '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED GROUP: group: test_group\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup user -n test_user -a 128
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'user -n test_user -a 128 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED USER: username: test_user access_level: 128\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup assignment -n test_user -g test_group
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'assignment -n test_user -g test_group '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED USER_GROUP_ASSIGNMENT: username: test_user group: test_group\n')
    command.close()
    ## User tool: dnslsusergroup
    ## dnslsusergroup user
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'username         access_level\n'
        '-----------------------------\n'
        'shuey            128\n'
        'test_user        128\n'
        'tree_export_user 0\n'
        'sharrell         128\n\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup forward -z test_zone -g test_group
    ## --group-permission=a,aaaa
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'forward -z test_zone -g test_group --group-permission=a,aaaa '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED FORWARD_ZONE_PERMISSION: zone_name: test_zone group: '
        'test_group group_permission: [\'a\', \'aaaa\']\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup reverse -b 168.192.0.0/24 -g test_group 
    ## --group-permission=ptr,cname
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'reverse -b 168.192.2.0/24 -g test_group --group-permission=ptr,cname '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED REVERSE_RANGE_PERMISSION: cidr_block: 168.192.2.0/24 '
        'group: test_group group_permission: [\'ptr\', \'cname\']\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup group -g test_group2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'group -g test_group2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED GROUP: group: test_group2\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup user -n test_user2 -a 64
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'user -n test_user2 -a 64 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED USER: username: test_user2 access_level: 64\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup assignment -n test_user2 -g test_group2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'assignment -n test_user2 -g test_group2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED USER_GROUP_ASSIGNMENT: username: test_user2 group: test_group2\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup forward -z test_zone -g test_group2
    ## --group-permission=a,aaaa
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'forward -z test_zone -g test_group2 --group-permission=a,aaaa '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED FORWARD_ZONE_PERMISSION: zone_name: test_zone '
        'group: test_group2 group_permission: [\'a\', \'aaaa\']\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup reverse -b 168.192.0.0/24 -g test_group 
    ## --group-permission=ptr,cname
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'reverse -b 168.192.2.0/24 -g test_group2 --group-permission=ptr,cname '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED REVERSE_RANGE_PERMISSION: cidr_block: 168.192.2.0/24 '
        'group: test_group2 group_permission: [\'ptr\', \'cname\']\n')
    command.close()
    ## User tool: dnslsusergroup
    ## dnslsusergroup user
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'username         access_level\n'
        '-----------------------------\n'
        'shuey            128\n'
        'test_user        128\n'
        'tree_export_user 0\n'
        'test_user2       64\n'
        'sharrell         128\n\n')
    command.close()
    ## User tool: dnsrmusergroup
    ## dnsrmusergroup user reverse -b 192.168.2.0/24
    ## -g test_group2 --group-permission=ptr,cname
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmusergroup '
        'reverse -b 192.168.2.0/24 -g test_group2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED REVERSE_RANGE_PERMISSION: cidr_block: 192.168.2.0/24 '
        "group: test_group2 group_permission: ['ptr', 'cname']\n")
    command.close()
    ## User tool: dnsrmusergroup
    ## dnsrmusergroup forward -z test_zone -g test_group2
    ## --group-permission=a,aaaa
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmusergroup '
        'forward -z test_zone -g test_group2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED FORWARD_ZONE_PERMISSION: zone_name: test_zone '
        "group: test_group2 group_permission: ['a', 'aaaa']\n")
    command.close()
    ## User tool: dnsrmusergroup
    ## dnsrmusergroup assignment -n test_user2 -g test_group2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmusergroup '
        'assignment -n test_user2 -g test_group2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED USER_GROUP_ASSIGNMENT: username: test_user2 group: test_group2\n')
    command.close()
    ## User tool: dnsrmusergroup
    ## dnsrmusergroup group -g test_group2 
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmusergroup '
        'group -g test_group2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED GROUP: group: test_group2\n')
    command.close()
    ## User tool: dnsrmusergroup
    ## dnsrmusergroup user -n test_user2 
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmusergroup '
        'user -n test_user2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED USER: username: test_user2 access_level: None\n')
    command.close()
    ## User tool: dnsmkusergroup
    ## dnsmkusergroup user -n test_user2 -a 64
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkusergroup '
        'user -n test_user -a 64 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Username already exists.\n')
    command.close()
    ## dnslsusergroup user
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'username         access_level\n'
        '-----------------------------\n'
        'shuey            128\n'
        'test_user        128\n'
        'tree_export_user 0\n'
        'sharrell         128\n\n')
    ## dnsrmusergroup user -n test_user2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmusergroup '
        'user -n NONE '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Username does not exist.\n')
    command.close()
    ## dnslsusergroup user
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'username         access_level\n'
        '-----------------------------\n'
        'shuey            128\n'
        'test_user        128\n'
        'tree_export_user 0\n'
        'sharrell         128\n\n')
    ## dnslsusergroup group -g test_group
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'group -g test_group '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'group\n'
        '-----\n'
        'test_group\n\n')
    ## dnslsusergroup assignment -n test_user -g test_group
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'assignment -n test_user -g test_group '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'username  groups\n'
        '----------------\n'
        'test_user test_group\n\n')
    command.close()
    ## dnslsusergroup forward -z test_zone -g test_group
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'forward -z test_zone -g test_group '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'group      zone_name group_permission\n'
        '-------------------------------------\n'
        'test_group test_zone [\'a\', \'aaaa\']\n\n')
    command.close()
    ## dnslsusergroup reverse -b 192.168.2.0/24 -g test_group
    command_string = (
        'python ../roster-user-tools/scripts/dnslsusergroup '
        'reverse -b 168.192.2.0/24 -g test_group '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'group      cidr_block     group_permission\n'
        '------------------------------------------\n'
        'test_group 168.192.2.0/24 [\'ptr\', \'cname\']\n\n')
    command.close()

    #dnscredential
    command_string = (
        'python ../roster-user-tools/scripts/dnscredential '
        'make_infinite -U test_user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()
    #dnscredential
    command_string = (
        'python ../roster-user-tools/scripts/dnscredential '
        'list -U new_user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = output.split('\n')
    self.assertEqual('user_name credential_string                    infinite_cred',
        output[0])
    self.assertTrue('shuey     ' in output[2])
    self.assertTrue('test_user ' in output[3])
    self.assertTrue('sharrell  ' in output[4])
    command.close()
    #dnscredential
    command_string = (
        'python ../roster-user-tools/scripts/dnscredential '
        'remove -U test_user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()
    #dnscredential
    command_string = (
        'python ../roster-user-tools/scripts/dnscredential '
        'list -U new_user '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = output.split('\n')
    self.assertEqual('user_name credential_string                    infinite_cred',
        output[0])
    self.assertTrue('shuey     ' in output[2])
    self.assertTrue('sharrell  ' in output[3])
    for i in output:
      self.assertFalse('test_user' in i)
    command.close()

    ## User tool: dnsmkrecord
    ## dnsmkrecord soa --admin-email="university.edu." --name-server="ns.university.edu."
    ## --serial-number=123456 --refresh-seconds=30 --retry-seconds=30
    ## --minimum-seconds=30 --expiry-seconds=30 -t @ -v test_view -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'soa --admin-email="university.edu." '
        '--name-server="ns.university.edu." '
        '--serial-number=111 --refresh-seconds=30 '
        '--retry-seconds=30 --minimum-seconds=30 '
        '--expiry-seconds=30 '
        '-t @ -v test_view -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED SOA: @ zone_name: test_zone view_name: test_view ttl: 3600\n    '
        'refresh_seconds: 30 expiry_seconds: 30 name_server: ns.university.edu. '
        'minimum_seconds: 30 retry_seconds: 30 serial_number: 111 '
        'admin_email: university.edu.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord soa --admin-email="university.edu." --name-server="ns.university.edu."
    ## --serial-number=123456 --refresh-seconds=30 --retry-seconds=30
    ## --minimum-seconds=30 --expiry-seconds=30 -t @ -v test_view -z test_zone2
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'soa --admin-email="university.edu." '
        '--name-server="ns2.university.edu." '
        '--serial-number=222 --refresh-seconds=30 '
        '--retry-seconds=30 --minimum-seconds=30 '
        '--expiry-seconds=30 '
        '-t @ -v test_view -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED SOA: @ zone_name: test_zone3 view_name: test_view ttl: 3600\n    '
        'refresh_seconds: 30 expiry_seconds: 30 name_server: ns2.university.edu. '
        'minimum_seconds: 30 retry_seconds: 30 serial_number: 222 '
        'admin_email: university.edu.\n')
    command.close()

    ## User tool: dnsmkrecord
    ## dnsmkrecord a --assignment-ip 168.192.2.1 -t machine1 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'a --assignment-ip 192.168.2.1 -t machine1 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED A: machine1 zone_name: test_zone3 view_name: any '
        'ttl: 3600\n    assignment_ip: 192.168.2.1\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord a --assignment-ip 168.192.2.1 -t machine1 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'a --assignment-ip 192.168.2.1 -t machine1 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord a --assignment-ip 168.192.2.2 -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'a --assignment-ip 192.168.2.2 -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED A: machine2 zone_name: test_zone3 view_name: any '
        'ttl: 3600\n    assignment_ip: 192.168.2.2\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord a --assignment-ip 168.192.1.3 -t machine3 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'a --assignment-ip 192.168.1.3 -t machine3 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED A: machine3 zone_name: test_zone view_name: any '
        'ttl: 3600\n    assignment_ip: 192.168.1.3\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord a --assignment-ip 192.168.2.4 -t machine3 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'a --assignment-ip 192.168.2.4 -t machine4 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED A: machine4 zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    assignment_ip: 192.168.2.4\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord a --assignment-ip 192.168.2.4 -t NONE -v any -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'a --assignment-ip 192.168.2.4 -t NONE -v any -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    self.assertEqual(output,
        'USER ERROR: No records found.\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord a --assignment-ip NONE -t machine4 -v any -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'a --assignment-ip NONE -t machine4 -v any -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    self.assertEqual(output,
        'USER ERROR: Invalid data type IPv4IPAddress: NONE\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord a --assignment-ip 192.168.2.4 -t machine4 -v any -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'a --assignment-ip 192.168.2.4 -t machine4 -v any -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED A: machine4 zone_name: test_zone3 view_name: any ttl: 3600\n    '
        'assignment_ip: 192.168.2.4\n')
    command.close()
    ## User tool: dnslsrecord
    ## dnslsrecord a -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'a -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name  assignment_ip\n'
        '----------------------------------------------------------------------\n'
        'machine1 3600 a           any       shuey     test_zone3 192.168.2.1\n'
        'machine2 3600 a           any       shuey     test_zone3 192.168.2.2\n\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord aaaa --assignment-ip ::ffff:168.192.2.0 -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'aaaa --assignment-ip ::ffff:168.192.2.0 -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED AAAA: machine2 zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    assignment_ip: 0000:0000:0000:0000:0000:ffff:a8c0:0200\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord aaaa --assignment-ip ::ffff:168.192.2.0 -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'aaaa --assignment-ip ::ffff:168.192.2.0 -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord aaaa --assignment-ip ::ffff:168.192.2.6 -t machine3 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'aaaa --assignment-ip ::ffff:168.192.2.6 -t machine3 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED AAAA: machine3 zone_name: test_zone view_name: any ttl: 3600\n    '
        'assignment_ip: 0000:0000:0000:0000:0000:ffff:a8c0:0206\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord aaaa --assignment-ip ::ffff:168.192.2.6 -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'aaaa --assignment-ip ::ffff:168.192.2.6 -t machine4 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED AAAA: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'assignment_ip: 0000:0000:0000:0000:0000:ffff:a8c0:0206\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord aaaa --assignment-ip ::ffff:168.192.2.6 -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'aaaa --assignment-ip ::ffff:168.192.2.6 -t machine4 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED AAAA: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'assignment_ip: 0000:0000:0000:0000:0000:ffff:a8c0:0206\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord aaaa --assignment-ip NONE -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'aaaa --assignment-ip NONE -t machine4 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    self.assertEqual(output,
        'USER ERROR: NONE is not a valid IP address\n')
    command.close()
    ## User tool: dnslsrecord
    ## dnslsrecord a -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'aaaa -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name  assignment_ip\n'
        '----------------------------------------------------------------------\n'
        'machine2 3600 aaaa        any       shuey     test_zone3 0000:0000:0000:0000:0000:ffff:a8c0:0200\n\n')
    command.close()


    ## User tool: dnsmkrecord
    ## dnsmkrecord cname --assignment-host "university.edu." -t machine4 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'cname --assignment-host "university.edu." -t machine4 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED CNAME: machine4 zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    assignment_host: university.edu.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord cname --assignment-host "university.edu." -t machine4 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'cname --assignment-host "university.edu." -t machine4 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord cname --assignment-host "university.edu." -t machine5 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'cname --assignment-host "university.edu." -t machine5 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED CNAME: machine5 zone_name: test_zone view_name: any ttl: 3600\n'
        '    assignment_host: university.edu.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord cname --assignment-host "university.edu." -t machine6 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'cname --assignment-host "university.edu." -t machine6 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED CNAME: machine6 zone_name: test_zone view_name: any ttl: 3600\n    '
        'assignment_host: university.edu.\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord cname --assignment-host "university.edu." -t machine6 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'cname --assignment-host "university.edu." -t machine6 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED CNAME: machine6 zone_name: test_zone view_name: any ttl: 3600\n    '
        'assignment_host: university.edu.\n')
    command.close()
    ## User tool: dnslsrecord
    ## dnslsrecord cname -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'cname -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name  assignment_host\n'
        '------------------------------------------------------------------------\n'
        'machine4 3600 cname       any       shuey     test_zone3 university.edu.\n\n')
    command.close()

    ## User tool: dnsmkrecord
    ## dnsmkrecord hinfo --hardware Hardware1 --os "Linux" -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'hinfo --hardware Hardware1 --os "Linux" -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED HINFO: machine2 zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    hardware: Hardware1 os: Linux\n')
    command.close() 
    ## User tool: dnsmkrecord
    ## dnsmkrecord hinfo --hardware Hardware3 --os "RH5.5" -t machine3 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'hinfo --hardware Hardware3 --os "RH5.5" -t machine3 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED HINFO: machine3 zone_name: test_zone view_name: any ttl: 3600\n    '
        'hardware: Hardware3 os: RH5.5\n')
    command.close() 
    ## User tool: dnsmkrecord
    ## dnsmkrecord hinfo --hardware Hardware2 --os "OSX" -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'hinfo --hardware Hardware2 --os "OSX" -t machine4 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED HINFO: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'hardware: Hardware2 os: OSX\n')
    command.close() 
    ## User tool: dnsmkrecord
    ## dnsmkrecord hinfo --hardware Hardware1 --os "Linux" -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'hinfo --hardware Hardware1 --os "Linux" -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close() 
    ## User tool: dnsrmrecord
    ## dnsrmrecord hinfo --hardware NONE --os "OSX" -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'hinfo --hardware NONE --os "OSX" -t machine4 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    self.assertEqual(output,
        'USER ERROR: No records found.\n')
    command.close() 
    ## User tool: dnsrmrecord
    ## dnsrmrecord hinfo --hardware Hardware2 --os NONE -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'hinfo --hardware Hardware2 --os NONE -t machine4 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    self.assertEqual(output,
        'USER ERROR: No records found.\n')
    command.close() 
    ## User tool: dnsrmrecord
    ## dnsrmrecord hinfo --hardware Hardware2 --os "OSX" -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'hinfo --hardware Hardware2 --os "OSX" -t machine4 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED HINFO: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'hardware: Hardware2 os: OSX\n')
    command.close() 
    ## User tool: dnslsrecord
    ## dnslsrecord hinfo -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'hinfo -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target   ttl  hardware  record_type view_name last_user zone_name  os\n'
        '---------------------------------------------------------------------\n'
        'machine2 3600 Hardware1 hinfo       any       shuey     test_zone3 Linux\n\n')
    command.close()

    ## User tool: dnsmkrecord
    ## dnsmkrecord txt --quoted-text "Text Record" -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'txt --quoted-text "Text Record" -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED TXT: machine2 zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    quoted_text: Text Record\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord txt --quoted-text "Lots of dots.......dots... . ." -t machine3 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'txt --quoted-text "Lots of dots.......dots... . ." -t machine3 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED TXT: machine3 zone_name: test_zone view_name: any ttl: 3600\n    '
        'quoted_text: Lots of dots.......dots... . .\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord txt --quoted-text "\\\///delete///" -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'txt --quoted-text "\\\///delete///" -t machine4 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED TXT: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'quoted_text: \\///delete///\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord txt --quoted-text "Text Record" -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'txt --quoted-text "Text Record" -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord txt --quoted-text "\\\///delete///" -t machine4 -v any -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'txt --quoted-text "\\\///delete///" -t machine4 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED TXT: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'quoted_text: \\///delete///\n')
    command.close()
    ## User tool: dnslsrecord
    ## dnslsrecord txt -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'txt -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name  quoted_text\n'
        '--------------------------------------------------------------------\n'
        'machine2 3600 txt         any       shuey     test_zone3 Text Record\n\n')
    command.close()

    ## User tool: dnsmkrecord
    ## dnsmkrecord srv --priority 10 --weight 5 --port 2020
    ## --assignment-host "university.edu." -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'srv --priority 10 --weight 5 --port 2020 '
        '--assignment-host "university.edu." -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED SRV: machine2 zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    priority: 10 assignment_host: university.edu. port: 2020 weight: 5\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord srv --priority 10 --weight 5 --port 2020
    ## --assignment-host "university.edu." -t machine3 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'srv --priority 10 --weight 5 --port 2020 '
        '--assignment-host "university.edu." -t machine3 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED SRV: machine3 zone_name: test_zone view_name: any ttl: 3600\n    '
        'priority: 10 assignment_host: university.edu. port: 2020 weight: 5\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord srv --priority 10 --weight 5 --port 2020
    ## --assignment-host "university.edu." -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'srv --priority 10 --weight 5 --port 2020 '
        '--assignment-host "university.edu." -t machine4 -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED SRV: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'priority: 10 assignment_host: university.edu. port: 2020 weight: 5\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord srv --priority 10 --weight 5 --port 2020
    ## --assignment-host "university.edu." -t machine4 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'srv --priority 10 --weight 5 --port 2020 '
        '--assignment-host "university.edu." -t machine4 -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED SRV: machine4 zone_name: test_zone view_name: any ttl: 3600\n    '
        'priority: 10 assignment_host: university.edu. port: 2020 weight: 5\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord srv --priority 10 --weight 5 --port 2020
    ## --assignment-host "university.edu." -t machine2 -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'srv --priority 10 --weight 5 --port 2020 '
        '--assignment-host "university.edu." -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnslsrecord
    ## dnslsrecord srv -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'srv -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target   weight last_user priority record_type view_name ttl  zone_name  assignment_host port\n'
        '---------------------------------------------------------------------------------------------\n'
        'machine2 5      shuey     10       srv         any       3600 test_zone3 university.edu. 2020\n\n')
    command.close()

    ## User tool: dnsmkrecord
    ## dnsmkrecord ns --name-server "ns.university.edu." -t @ -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'ns --name-server "ns.university.edu." -t @ -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED NS: @ zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    name_server: ns.university.edu.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord ns --name-server "3.168.192.in-addr.arpa." -t @ -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'ns --name-server "3.168.192.in-addr.arpa." -t @ -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED NS: @ zone_name: test_zone view_name: any ttl: 3600\n'
        '    name_server: 3.168.192.in-addr.arpa.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord ns --name-server "4.168.192.in-addr.arpa." -t @ -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'ns --name-server "4.168.192.in-addr.arpa." -t @ -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED NS: @ zone_name: test_zone view_name: any ttl: 3600\n'
        '    name_server: 4.168.192.in-addr.arpa.\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord ns --name-server "4.168.192.in-addr.arpa." -t @ -v any -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'ns --name-server "4.168.192.in-addr.arpa." -t @ -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED NS: @ zone_name: test_zone view_name: any ttl: 3600\n'
        '    name_server: 4.168.192.in-addr.arpa.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord ns --name-server "3.168.192.in-addr.arpa." -t @ -v any -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'ns --name-server "3.168.192.in-addr.arpa." -t @ -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnsrmrecord
    ## dnsrmrecord ns --name-server NONE -t @ -v any -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmrecord '
        'ns --name-server NONE -t @ -v any -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    self.assertEqual(output,
        'USER ERROR: Invalid data type Hostname: NONE\n')
    command.close()
    ## User tool: dnslsrecord
    ## dnslsrecord ns -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'ns -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target name_server        ttl  record_type view_name last_user zone_name\n'
        '------------------------------------------------------------------------\n'
        '@      ns.university.edu. 3600 ns          any       shuey     test_zone3\n\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord mx --mail-server "university.edu." --priority 5 -t machine2 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'mx --mail-server "university.edu." --priority 5 -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED MX: machine2 zone_name: test_zone3 view_name: any ttl: 3600\n'
        '    priority: 5 mail_server: university.edu.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord mx --mail-server "university.edu." --priority 5 -t machine2 -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'mx --mail-server "university.edu." --priority 5 -t machine2 -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord mx --mail-server "university.edu." --priority 5 -t machine -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'mx --mail-server "university.edu." --priority 5 -t machine -z test_zone '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED MX: machine zone_name: test_zone view_name: any ttl: 3600\n    '
        'priority: 5 mail_server: university.edu.\n')
    command.close()
    ## User tool: dnsmkrecord
    ## dnsmkrecord mx --mail-server "university.edu." --priority 5 -t machine -z test_zone3
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkrecord '
        'mx --mail-server "university.edu." --priority 5 -t machine -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED MX: machine zone_name: test_zone3 view_name: any ttl: 3600\n    '
        'priority: 5 mail_server: university.edu.\n')
    command.close()
    ## User tool: dnslsrecord
    ## dnslsrecord mx -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnslsrecord '
        'mx -z test_zone3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'target   ttl  priority record_type view_name last_user zone_name  mail_server\n'
        '-----------------------------------------------------------------------------\n'
        'machine2 3600 5        mx          any       shuey     test_zone3 university.edu.\n'
        'machine  3600 5        mx          any       shuey     test_zone3 university.edu.\n\n')
    command.close()

    ## User tool: dnsmkhost
    ## dnsmkhost -i 192.168.2.0 -t @ -z test_zone -v test_view
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkhost add '
        '-i 192.168.2.0 -t @ -z test_zone -v test_view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED A: @ zone_name: test_zone view_name: test_view ttl: 3600\n'
        '    assignment_ip: 192.168.2.0\n'
        'ADDED PTR: 0.2.168.192.in-addr.arpa. zone_name: test_zone3 view_name: test_view ttl: 3600\n'
        '    assignment_host: @.university.edu.\n')
    command.close()
    ## User tool: dnsmkhost
    ## dnsmkhost -i 192.168.2.0 -t @ -z test_zone -v test_view
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkhost add '
        '-i 192.168.2.0 -t @ -z test_zone -v test_view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'CLIENT ERROR: Duplicate record!\n')
    command.close()
    ## User tool: dnsmkhost
    ## dnsmkhost -i 192.168.2.1 -t @ -z test_zone -v test_view
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkhost add '
        '-i 192.168.2.1 -t @ -z test_zone -v test_view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED A: @ zone_name: test_zone view_name: test_view ttl: 3600\n    '
        'assignment_ip: 192.168.2.1\nADDED PTR: 1.2.168.192.in-addr.arpa. '
        'zone_name: test_zone3 view_name: test_view ttl: 3600\n    '
        'assignment_host: @.university.edu.\n')
    command.close()
    ## User tool: dnslshost
    ## dnslshost --cidr-block 192.168.2.0/29
    command_string = (
        'python ../roster-user-tools/scripts/dnslshost '
        'cidr --cidr-block 192.168.2.0/29 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'View:       any\n'
        '192.168.2.0 --        --                              --         any\n'
        '192.168.2.1 Forward   machine1.2.168.192.in-addr.arpa test_zone3 any\n'
        '192.168.2.2 Forward   machine2.2.168.192.in-addr.arpa test_zone3 any\n'
        '192.168.2.3 --        --                              --         any\n'
        '192.168.2.4 --        --                              --         any\n'
        '192.168.2.5 --        --                              --         any\n'
        '192.168.2.6 --        --                              --         any\n'
        '192.168.2.7 --        --                              --         any\n'
        'View:       test_view\n'
        '192.168.2.0 Reverse   university.edu                  test_zone3 test_view\n'
        '192.168.2.0 Forward   @.university.edu                test_zone  test_view\n'
        '192.168.2.1 Reverse   university.edu                  test_zone3 test_view\n'
        '192.168.2.1 Forward   @.university.edu                test_zone  test_view\n'
        '192.168.2.2 --        --                              --         test_view\n'
        '192.168.2.3 --        --                              --         test_view\n'
        '192.168.2.4 --        --                              --         test_view\n'
        '192.168.2.5 --        --                              --         test_view\n'
        '192.168.2.6 --        --                              --         test_view\n'
        '192.168.2.7 --        --                              --         test_view\n'
        '\n')
    command.close()
    ## User tool: dnsrmhost
    ## dnsrmhost --ip-address 192.168.2.1 -t @ -z test_zone
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmhost '
        '--ip-address 192.168.2.1 -t @ -z test_zone -v test_view '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED A: @ zone_name: test_zone view_name: test_view ttl: 3600\n    '
        'assignment_ip: 192.168.2.1\nREMOVED PTR: 1 zone_name: test_zone3 '
        'view_name: test_view ttl: 3600\n    assignment_host: @.university.edu.\n')
    command.close()
    ## User tool: dnslshosts
    ## dnslshost --cidr-block 192.168.2.0/29
    command_string = (
        'python ../roster-user-tools/scripts/dnslshost '
        'cidr --cidr-block 192.168.2.0/29 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)

    self.assertEqual(set(command.read().split('\n')),
    set(['View:       test_view',
        '192.168.2.0 Reverse   university.edu                  test_zone3 test_view',
        '192.168.2.0 Forward   @.university.edu                test_zone  test_view',
        '192.168.2.1 --        --                              --         test_view',
        '192.168.2.2 --        --                              --         test_view',
        '192.168.2.3 --        --                              --         test_view',
        '192.168.2.4 --        --                              --         test_view',
        '192.168.2.5 --        --                              --         test_view',
        '192.168.2.6 --        --                              --         test_view',
        '192.168.2.7 --        --                              --         test_view',
        'View:       any',
        '192.168.2.0 --        --                              --         any',
        '192.168.2.1 Forward   machine1.2.168.192.in-addr.arpa test_zone3 any',
        '192.168.2.2 Forward   machine2.2.168.192.in-addr.arpa test_zone3 any',
        '192.168.2.3 --        --                              --         any',
        '192.168.2.4 --        --                              --         any',
        '192.168.2.5 --        --                              --         any',
        '192.168.2.6 --        --                              --         any',
        '192.168.2.7 --        --                              --         any',
        '']))
    command.close()
    ## User tool: dnsuphosts
    ## dnsuphosts dump -r 192.168.2.0/29 -f backup_dir/hosts_out
    command_string = (
        'python ../roster-user-tools/scripts/dnsuphosts '
        'dump -r 192.168.2.0/29 -f %s/hosts_out '
        '-u %s -p %s -s %s --config-file %s ' % (
            self.backup_dir,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),'')
    command.close()
    handle = open('%s/hosts_out' % self.backup_dir,'r')
    self.assertEqual(handle.read(),
        '#:range:192.168.2.0/29\n'
        '#:view_dependency:any\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#192.168.2.0\n'
        #'192.168.2.1  machine1.2.168.192.in-addr.arpa machine1\n'
        '#192.168.2.1 machine1.2.168.192.in-addr.arpa machine1 # No reverse assignment\n'
        '#192.168.2.2 machine2.2.168.192.in-addr.arpa machine2 # No reverse assignment\n'
        '#192.168.2.3\n'
        '#192.168.2.4\n'
        '#192.168.2.5\n'
        '#192.168.2.6\n'
        #'#192.168.2.6 university.edu                           # No forward assignment\n'
        '#192.168.2.7\n')
    handle.close()

    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server_set -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'assignment -d %s -e set2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET ASSIGNMENT: dns_server_set: set2 dns_server: %s\n' % (
          TEST_DNS_SERVER))
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server_set -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server_set -e set2 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET: set2\n')
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server_set -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'assignment -d %s -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER2,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET ASSIGNMENT: dns_server_set: set3 dns_server: %s\n' % (
          TEST_DNS_SERVER2))
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server_set -e set2
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server_set -e set3 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER SET: set3\n')
    command.close()
    ## User tool: dnsrmdnsserver
    ## dnsrmdnsserver dns_server -d dns3
    command_string = (
        'python ../roster-user-tools/scripts/dnsrmdnsserver '
        'dns_server -d %s '
        '-u %s -p %s -s %s --config-file %s ' % (
            TEST_DNS_SERVER2,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'REMOVED DNS SERVER: %s\n' % TEST_DNS_SERVER2)
    command.close()

    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals update -d set1 -f unittest_dir/namedglobalconfoption
    handle = open('%s/namedconfglobaloption' % TESTDIR,'w')
    handle.write(
        'options { additional-from-auth yes; };')
    handle.close()
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'update -f %s/namedconfglobaloption -d set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED NAMED_CONF_GLOBAL_OPTION: %s/namedconfglobaloption\n' % TESTDIR)
    command.close()
    handle = open('%s/namedconfglobaloption' % TESTDIR,'w')
    handle.write(
        'options { additional-from-auth yes; };')
    handle.close()
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals list -d set1
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'list -d set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = output.splitlines()
    output=output[2].split(' ')
    self.assertEqual(output[10],'set1')
    self.assertEqual(output[0],'1')
    command.close()
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals dump -i 1 -f unittest_dir/dump
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'dump -i 1 -f %s/dump '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Wrote file: %s/dump\n' % TESTDIR)
    command.close()
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals update -d set1 -f unittest_dir/in
    handle = open('%s/in' % TESTDIR,'w')
    handle.write('options { new2; new; test; };')
    handle.close()
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'update -f %s/in -d set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED NAMED_CONF_GLOBAL_OPTION: %s/in\n' % TESTDIR)
    command.close()
    time.sleep(5)
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals dump -i 4 -f unittest_dir/dump
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'dump -f %s/dump '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Wrote file: %s/dump\n' % TESTDIR)
    command.close()
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals update -d set1 -f unittest_dir/in
    os.environ['EDITOR'] = 'python fake_editor.py options tools '
    handle = open('%s/in' % TESTDIR,'w')
    handle.write(
        'options { test; newoption; };\n')
    handle.close()
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'update -f %s/in -d set1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED NAMED_CONF_GLOBAL_OPTION: %s/in\n' % TESTDIR)
    command.close()
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'edit -d set1 -f %s/dump '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED NAMED_CONF_GLOBAL_OPTION: %s/dump\n' % TESTDIR )
    command.close()
    time.sleep(5)
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals dump -i 6 -f unittest_dir/dump
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'dump -i 4 -f %s/dump '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Wrote file: %s/dump\n' % TESTDIR)
    command.close()
    time.sleep(1)
    handle = open('%s/dump' % TESTDIR,'r')
    self.assertEqual(handle.read(),
        'tools { test;\nnewoption; };')
    handle.close()
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals revert -d set1 -i 1
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'revert -d set1 -i 1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    time.sleep(5)
    ## User tool: dnsupnamedglobals
    ## dnsupnamedglobals dump -i 7 -f unittest_dir/dump 
    command_string = (
        'python ../roster-user-tools/scripts/dnsupnamedglobals '
        'dump -i 5 -f %s/dump '
        '-u %s -p %s -s %s --config-file %s ' % (
            TESTDIR,
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Wrote file: %s/dump\n' % TESTDIR)
    command.close()
    handle = open('%s/dump' % TESTDIR,'r')
    self.assertEqual(handle.read(),
        'options { additional-from-auth yes; };')
    handle.close()
    ## User tool: dnsauditlog
    ## dnslsauditlog --success 1
    command_string = (
        'python ../roster-user-tools/scripts/dnslsauditlog '
        '--success 1 '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    output = command.read()
    output = re.sub("\s+"," ",output)
    output = output.split(' ')
    output = output[-21]

    ## User tool: dnssetmaintenance
    ## dnssetmaintenance list
    command_string = (
        'python ../roster-user-tools/scripts/dnssetmaintenance '
        'set --on '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()
    command_string = (
        'python ../roster-user-tools/scripts/dnssetmaintenance '
        'list '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Maintenance mode is ON\n')
    command.close()
    ## dnstreeexport -f --config-file ./completeconfig.conf
    command_string = (
        'python ../roster-config-manager/scripts/dnstreeexport '
        ' --config-file %s ' % (
            self.userconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ERROR: Database currently under maintenance.\n')
    command.close()
    ## User tool: dnssetmaintenance
    command_string = (
        'python ../roster-user-tools/scripts/dnssetmaintenance '
        'set --off '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()
    ## dnssetmaintenance list
    command_string = (
        'python ../roster-user-tools/scripts/dnssetmaintenance '
        'list '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Maintenance mode is OFF\n')
    command.close()
    ## dnstreeexport -f --config-file ./completeconfig.conf
    os.system('rm -rf temp_dir')
    command_string = (
        'python ../roster-config-manager/scripts/dnstreeexport '
        ' -f --config-file %s ' % (
            self.userconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()

    #dump the database that will be reverted to
    origdb = glob.glob('%s/full_database_dump-*' % self.backup_dir)
    origtarfile = glob.glob('%s/audit_log*' % self.backup_dir)
    tarfilename = origtarfile[0].split('/')
    tarfilename = tarfilename[2].split('-')
    tarfilename = tarfilename[1].split('.')
    ## dnscheckconfig -d <dir> --config-file ./completeconfig.conf
    command_string = (
        'python ../roster-config-manager/scripts/dnscheckconfig '
        '-i %s -d %s --config-file %s -z %s -c %s' % (
            tarfilename[0], self.backup_dir, self.userconfig,
            CHECKZONE_EXEC, CHECKCONF_EXEC))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()
    ## dnscheckconfig -d <dir> --config-file ./completeconfig.conf
    command_string = (
        'python ../roster-config-manager/scripts/dnscheckconfig '
        '-i %s -d %s --config-file %s -z %s -c %s' % (
            tarfilename[0], self.backup_dir, self.userconfig,
            CHECKZONE_EXEC, CHECKCONF_EXEC))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()

    ## dnsconfigsync -i <timestamp> --config-file ./completeconfig.conf
    ## connection to rsync is not successfully established.
    command_string = (
        'python ../roster-config-manager/scripts/dnsconfigsync '
        ' -i %s -u %s --ssh-id %s -c %s --rndc-port %s --rndc-key %s' % (
            tarfilename[0], SSH_USER, SSH_ID, self.userconfig,
	    self.rndc_port, RNDC_KEY)) # ADD RNDC PORT CALC
    command = os.popen(command_string)
    output = command.read()
    output = re.sub('\d+\s','',output)
    output = re.sub('\d+\.','',output)
    # Below we remove the last "Disconnecting" line since the text
    # can vary depending on operating system
    self.assertEqual(output.split("Disconnecting")[0],
        'Connecting to "%s"\n'
        '[%s@%s] out: server reload successful\r\n' % (
            TEST_DNS_SERVER, SSH_USER, TEST_DNS_SERVER))
    command.close()
    ## dnsmkzone forward -z sub.university.edu -v test_view -t master --origin sub.university.edu.
    command_string = (
        'python ../roster-user-tools/scripts/dnsmkzone '
        'forward -z sub.university.edu -v test_view -t master '
        '--origin sub.university.edu. '
        '-u %s -p %s -s %s --config-file %s ' % (
            USERNAME, PASSWORD, self.server_name, self.toolsconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'ADDED FORWARD ZONE: zone_name: sub.university.edu zone_type: master '
        'zone_origin: sub.university.edu. zone_options: None '
        'view_name: test_view\n')
    command.close()
    ## dnszoneimporter
    command_string = (
        'python ../roster-config-manager/scripts/dnszoneimporter '
        ' -f test_data/test_zone.db -v test_view '
        '-u %s --config-file %s -z sub.university.edu' % (
            USERNAME, self.userconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        'Loading in test_data/test_zone.db\n'
        '17 records loaded from zone test_data/test_zone.db\n'
        '17 total records added\n')
    command.close()
    ## dnstreeexport -f --config-file ./completeconfig.conf
    command_string = (
        'python ../roster-config-manager/scripts/dnstreeexport '
        ' -f --config-file %s ' % (
            self.userconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()
    os.rename('%s/full_database_dump-145.bz2' % (self.backup_dir),
                                '%s/origdb.bz2' % self.backup_dir)
    dbdump = glob.glob('%s/*-145.*' % self.backup_dir)
    for db in dbdump:
      if( os.path.exists(db) ):
        os.remove(db)
    ## dnsrecover
    command_string = (
        'python ../roster-config-manager/scripts/dnsrecover '
        ' -i %s '
        '-u %s --config-file %s ' % (145,
            USERNAME, self.userconfig))
    command = os.popen(command_string)
    time.sleep(1)
    self.assertEqual(command.read(),
        'Loading database from backup with ID 142\n'
        'Replaying action with id 143: MakeZone\n'
        'with arguments: [u\'sub.university.edu\', '
        'u\'master\', u\'sub.university.edu.\', u\'test_view\', None, True]\n'
        'Replaying action with id 144: ProcessRecordsBatch\n'
        'with arguments: [[], [{u\'record_arguments\': '
        '{u\'refresh_seconds\': 10800L, u\'expiry_seconds\': '
        '3600000L, u\'name_server\': u\'ns.university.lcl.\', '
        'u\'minimum_seconds\': 86400L, u\'retry_seconds\': 3600L, '
        'u\'serial_number\': 794L, u\'admin_email\': '
        'u\'hostmaster.ns.university.lcl.\'}, u\'record_type\': u\'soa\', '
        'u\'ttl\': 3600L, u\'record_target\': u\'@\', u\'record_zone_name\': '
        'u\'sub.university.edu\', u\'record_view_dependency\': '
        'u\'test_view\'}, {u\'record_arguments\': '
        '{u\'name_server\': u\'ns.sub.university.edu.\'}, u\'record_type\': '
        'u\'ns\', u\'ttl\': 3600L, u\'record_target\': u\'@\', '
        'u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'name_server\': '
        'u\'ns2.sub.university.edu.\'}, u\'record_type\': u\'ns\', '
        'u\'ttl\': 3600L, u\'record_target\': u\'@\', '
        'u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'priority\': 10, u\'mail_server\': '
        'u\'mail1.sub.university.edu.\'}, u\'record_type\': '
        'u\'mx\', u\'ttl\': 3600L, u\'record_target\': u\'@\', '
        'u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'priority\': 20, u\'mail_server\': '
        'u\'mail2.sub.university.edu.\'}, u\'record_type\': '
        'u\'mx\', u\'ttl\': 3600L, u\'record_target\': u\'@\', '
        'u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'quoted_text\': u\'"Contact 1:  '
        'Stephen Harrell (sharrell@university.lcl)"\'}, '
        'u\'record_type\': u\'txt\', u\'ttl\': 3600L, u\'record_target\': '
        'u\'@\', u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_ip\': u\'192.168.0.1\'}, '
        'u\'record_type\': u\'a\', u\'ttl\': 3600L, u\'record_target\': '
        'u\'@\', u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_ip\': u\'192.168.1.103\'}, '
        'u\'record_type\': u\'a\', u\'ttl\': 3600L, u\'record_target\': '
        'u\'ns\', u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_ip\': '
        'u\'3ffe:0800:0000:0000:02a8:79ff:fe32:1982\'}, u\'record_type\': '
        'u\'aaaa\', u\'ttl\': 3600L, u\'record_target\': u\'desktop-1\', '
        'u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_ip\': u\'192.168.1.100\'}, '
        'u\'record_type\': u\'a\', u\'ttl\': 3600L, u\'record_target\': '
        'u\'desktop-1\', u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_ip\': u\'192.168.1.104\'}, '
        'u\'record_type\': u\'a\', u\'ttl\': 3600L, u\'record_target\': '
        'u\'ns2\', u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'hardware\': u\'PC\', u\'os\': '
        'u\'NT\'}, u\'record_type\': u\'hinfo\', u\'ttl\': 3600L, '
        'u\'record_target\': u\'ns2\', u\'record_zone_name\': '
        'u\'sub.university.edu\', u\'record_view_dependency\': '
        'u\'test_view\'}, {u\'record_arguments\': '
        '{u\'assignment_host\': u\'sub.university.edu.\'}, '
        'u\'record_type\': u\'cname\', u\'ttl\': 3600L, '
        'u\'record_target\': u\'www\', u\'record_zone_name\': '
        'u\'sub.university.edu\', u\'record_view_dependency\': '
        'u\'test_view\'}, {u\'record_arguments\': '
        '{u\'assignment_ip\': u\'127.0.0.1\'}, u\'record_type\': '
        'u\'a\', u\'ttl\': 3600L, u\'record_target\': '
        'u\'localhost\', u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_host\': '
        'u\'ns.university.lcl.\'}, u\'record_type\': '
        'u\'cname\', u\'ttl\': 3600L, u\'record_target\': '
        'u\'www.data\', u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_ip\': '
        'u\'192.168.1.101\'}, u\'record_type\': u\'a\', '
        'u\'ttl\': 3600L, u\'record_target\': u\'mail1\', '
        'u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}, '
        '{u\'record_arguments\': {u\'assignment_ip\': '
        'u\'192.168.1.102\'}, u\'record_type\': u\'a\', '
        'u\'ttl\': 3600L, u\'record_target\': u\'mail2\', '
        'u\'record_zone_name\': u\'sub.university.edu\', '
        'u\'record_view_dependency\': u\'test_view\'}], True]\n')
    command.close()
    ## dnstreeexport -f --config-file ./completeconfig.conf
    command_string = (
        'python ../roster-config-manager/scripts/dnstreeexport '
        ' -f --config-file %s ' % (
            self.userconfig))
    command = os.popen(command_string)
    self.assertEqual(command.read(),
        '')
    command.close()
    time.sleep(1)
    ## dump reverted database
    origdb = bz2.BZ2File('%s/origdb.bz2' % self.backup_dir)
    origdump = origdb.read()
    origdump = re.sub(
        '[0-9]{1,4}-[0-9]{1,2}-[0-9]{1,2} [0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}',
        ' ', origdump)
    origdb.close()
    os.remove('%s/origdb.bz2' % self.backup_dir)
  
    newdb = bz2.BZ2File('%s/full_database_dump-148.bz2' % self.backup_dir)
    newdump = newdb.read()
    newdump = re.sub(
        '[0-9]{1,4}-[0-9]{1,2}-[0-9]{1,2} [0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}',
        ' ', newdump)
    newdb.close()
    newdump_list = []
    for line in newdump.split('\n'):
      if( line.startswith('INSERT INTO audit_log') ):
        number = int(line.split()[5].strip('(').strip(',').strip())
        if( number < 145 ):
          newdump_list.append(line)
      else:
        newdump_list.append(line)
    newdump = '\n'.join(newdump_list)
    origdump = re.sub('AUTO_INCREMENT=[0-9]+', 'AUTO_INCREMENT=', origdump)
    newdump = re.sub('AUTO_INCREMENT=[0-9]+', 'AUTO_INCREMENT=', newdump)
    self.assertEqual(origdump, newdump)

if( __name__ == '__main__' ):
    unittest.main()
