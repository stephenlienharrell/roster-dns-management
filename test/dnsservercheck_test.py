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

"""Regression test for dnscheckconfig

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import ConfigParser
import datetime
import getpass
import os
import re
import roster_core
import shutil
import StringIO
import subprocess
import sys
import time
import unittest

from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnscheckconfig'
SERVER_CHECKER_EXEC='../roster-config-manager/scripts/dnsservercheck'
KEY_FILE = 'test_data/rndc.key'
USERNAME = u'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TESTDIR = u'%s/test_data/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/named/' % os.getcwd()
SSH_USER = unicode(getpass.getuser())

class TestDnsServerCheck(unittest.TestCase):
  def setUp(self):
    self.config_instance = roster_core.Config(CONFIG_FILE)
    self.root_config_dir = self.config_instance.config_file['exporter'][
        'root_config_dir'].rstrip('/')
    self.root_backup_dir = self.config_instance.config_file['exporter'][
        'backup_dir'].rstrip('/')
    if( os.path.exists(self.root_backup_dir) ):
      shutil.rmtree(self.root_backup_dir)
    os.mkdir(self.root_backup_dir)

    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    os.mkdir(self.root_config_dir)

    self.db_instance = self.config_instance.GetDb()

    self.db_instance.CreateRosterDatabase()

    self.data = open(DATA_FILE, 'r').read()
    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(self.data)
    self.db_instance.EndTransaction()
    self.db_instance.close()

    self.core_instance = roster_core.Core(USERNAME,self.config_instance)

    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)

    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')
    
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(
        u'set1', u'include "%s/test_data/rndc.key"; options { pid-file "test_data/named.pid";};\n'
        'controls { inet 127.0.0.1 port 5555 allow{localhost;} keys {rndc-key;};};' % (os.getcwd())) # So we can test

    self.core_instance.MakeACL(u'test_acl', u'127.0.0.1')
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'test_acl', 1)

    self.core_instance.MakeZone(u'sub.university.lcl', u'master',
                                u'sub.university.lcl.', view_name=u'test_view')
    soa_args_dict = self.core_instance.GetEmptyRecordArgsDict(u'soa')
    soa_args_dict[u'refresh_seconds'] = 500
    soa_args_dict[u'expiry_seconds'] = 500
    soa_args_dict[u'name_server'] = u'ns.sub.university.lcl.'
    soa_args_dict[u'minimum_seconds'] = 500
    soa_args_dict[u'retry_seconds'] = 500
    soa_args_dict[u'serial_number'] = 1000
    soa_args_dict[u'admin_email'] = u'root.sub.university.lcl.'
    self.core_instance.MakeRecord(u'soa', u'@', u'sub.university.lcl', soa_args_dict, view_name=u'test_view')

  def tearDown(self):
    if( os.path.exists(self.root_backup_dir) ):
      shutil.rmtree(self.root_backup_dir)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)


  def testDnsServerCheck(self):
    self.core_instance.MakeDnsServer(u'localhost', SSH_USER,
                                     BINDDIR, TESTDIR)
    output = os.popen('python %s -d localhost -c %s' %
        (SERVER_CHECKER_EXEC, CONFIG_FILE))
    self.assertEqual(output.read(),
            'ERROR: Backup directory %s does not contain any files or directories.\n' % self.root_backup_dir)
    output.close()
    self.core_instance.RemoveDnsServer(u'localhost')

    self.core_instance.MakeDnsServer(u'255.254.253.251', SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSetAssignments(u'255.254.253.251', u'set1')
    self.tree_exporter_instance.ExportAllBindTrees()
    output = os.popen('python %s -d localhost -c %s' %
        (SERVER_CHECKER_EXEC, CONFIG_FILE))
    self.assertEqual(output.read(),
        'ERROR: DNS server localhost does not exist.\n')
    output.close()

    output = os.popen('python %s -d 255.254.253.251 -c %s' %
        (SERVER_CHECKER_EXEC, CONFIG_FILE))
    self.assertEqual(output.read(),
        'ERROR: Could not connect to 255.254.253.251 via SSH.\n')
    output.close()

    self.core_instance.MakeDnsServer(u'localhost', SSH_USER,
                                     u'/some_dir/', u'/some_test_dir/')
    self.core_instance.MakeDnsServerSetAssignments(u'localhost', u'set1')
    self.tree_exporter_instance.ExportAllBindTrees()
    output = os.popen('python %s -d localhost -c %s' %
        (SERVER_CHECKER_EXEC, CONFIG_FILE))
    self.assertEqual(output.read(), 'ERROR: The remote BIND directory '
        '/some_dir/ does not exist or the user %s does not have '
        'permission.\n' % SSH_USER)
    output.close()

    self.core_instance.UpdateDnsServer(u'localhost', u'localhost', SSH_USER,
                                       BINDDIR, u'/some_test_dir/')
    output = os.popen('python %s -d localhost -c %s' %
        (SERVER_CHECKER_EXEC, CONFIG_FILE))
    self.assertEqual(output.read(), 'ERROR: The remote test directory '
        '/some_test_dir/ does not exist or the user %s does not have '
        'permission.\n' % SSH_USER)
    output.close()

    self.core_instance.UpdateDnsServer(u'localhost', u'localhost', SSH_USER,
                                       BINDDIR, TESTDIR)
    audit_id = self.tree_exporter_instance.ExportAllBindTrees()
    file_name = 'dns_tree_%s-22.tar.bz2' %  datetime.datetime.now().strftime('%d_%m_%yT%H_%M')
    output = os.popen('python %s -d localhost -c %s -i 22' %
        (SERVER_CHECKER_EXEC, CONFIG_FILE))
    self.assertEqual(output.read(), '')
    output.close()

    shutil.rmtree(self.root_config_dir)
    config_lib_instance.UnTarDnsTree(self.backup_dir, self.root_config_dir, 22)

    self.assertTrue(os.path.exists('%s/localhost/localhost.info' % self.root_config_dir))
    localhost_info = ConfigParser.SafeConfigParser()
    localhost_info.read('%s/localhost/localhost.info' % self.root_config_dir)
    self.assertTrue(localhost_info.has_section('tools'))
    self.assertTrue(localhost_info.has_option('tools', 'named-checkconf'))
    self.assertTrue(localhost_info.has_option('tools', 'named-checkzone'))
    self.assertTrue(localhost_info.has_option('tools', 'named-compilezone'))
    self.assertTrue(localhost_info.has_option('tools', 'tar'))

if( __name__ == '__main__' ):
  unittest.main()
