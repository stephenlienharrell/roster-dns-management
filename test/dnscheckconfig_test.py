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


import os
import re
import sys
import shutil
import subprocess
import unittest
import tarfile
import time
import StringIO
import getpass

import roster_core
from roster_config_manager import tree_exporter
from roster_config_manager import config_lib

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnscheckconfig'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
KEY_FILE = 'test_data/rndc.key'
USERNAME = u'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TEST_DIR = u'%s/unittest_dir/' % os.getcwd()
BIND_DIR = u'%s/test_data/named/' % os.getcwd()
NAMED_DIR = u'%s/test_data/named/named' % os.getcwd()
SSH_USER = unicode(getpass.getuser())
DNS_SERVER = u'dns1'

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
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.root_config_dir = self.config_instance.config_file[
        'exporter']['root_config_dir'].lstrip('./').rstrip('/')
    self.backup_dir = self.config_instance.config_file[
        'exporter']['backup_dir'].lstrip('./').rstrip('/')
    self.bind_config_dir = os.path.expanduser(self.root_config_dir)
    self.lockfile = self.config_instance.config_file[
        'server']['lock_file']
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)

    self.config_lib_instance = config_lib.ConfigLib(CONFIG_FILE)

    db_instance = self.config_instance.GetDb()
    db_instance.CreateRosterDatabase()

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
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'sub.university.lcl', u'master',
                                u'sub.university.lcl.', view_name=u'test_view')

  def tearDown(self):
    if( os.path.exists(KEY_FILE) ):
      os.remove(KEY_FILE)
    if( os.path.exists(self.backup_dir) ):
      shutil.rmtree(self.backup_dir)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    if( os.path.exists('temp_dir') ):
      shutil.rmtree('temp_dir')
    if( os.path.exists('%s/named' % BIND_DIR) ):
      shutil.rmtree('%s/named' % BIND_DIR)
    if( os.path.exists('%s/named.conf' % BIND_DIR) ):
      os.remove('%s/named.conf' % BIND_DIR)
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)

  def testCheckConfig(self):
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

    self.core_instance.MakeDnsServer(u'dns1', SSH_USER, BIND_DIR, TEST_DIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()
    self.config_lib_instance.UnTarDnsTree()

    output = subprocess.Popen(('/usr/sbin/rndc-confgen -a -c %s -r %s' % (
        KEY_FILE, EXEC)).split(), stderr=subprocess.PIPE).stderr
    self.assertEqual(output.read(), 'wrote key file "%s"\n' % KEY_FILE)
    output.close()
    output = os.popen('python %s -i 12 --config-file %s' % (
        EXEC, CONFIG_FILE))
    time.sleep(2) # Wait for disk to settle
    self.assertEqual(output.read(), '')
    output.close()

  def testCheckServerInfo(self):
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

    self.core_instance.MakeDnsServer(u'localhost', SSH_USER, BIND_DIR, TEST_DIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'localhost', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()
    self.config_lib_instance.UnTarDnsTree()
    self.assertTrue(os.path.isdir(self.root_config_dir))

    output = os.popen('python %s -s localhost --config-file %s' % (
        EXEC, CONFIG_FILE))
    time.sleep(2) # Wait for disk to settle
    self.assertEqual(output.read(), '')
    output.close()

  def testCheckErrorConfig(self):
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

    self.core_instance.MakeDnsServer(DNS_SERVER, SSH_USER, BIND_DIR, TEST_DIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(DNS_SERVER, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()
    self.config_lib_instance.UnTarDnsTree()
    self.assertTrue(os.path.isdir(self.root_config_dir))

    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named/test_view/sub.university.lcl.db' % DNS_SERVER,
        'ns2 3600 in a 192.168.1.104', 'ns2 3600 in aaq 192.168.1.104')
    output = os.popen('python %s --config-file %s --' % (
        EXEC, CONFIG_FILE))
    # Replacement below to accomodate for later bind versions
    self.assertEqual(output.read().replace(
        'zone sub.university.lcl/IN: not loaded due to errors.\n', ''),
        'ERROR: temp_dir/%s/named/test_view/sub.university.lcl.db:16: '
        'unknown RR type \'aaq\'\n'
        'zone sub.university.lcl/IN: loading from master '
        'file temp_dir/dns1/named/test_view/sub.university.lcl.db '
        'failed: unknown class/type\n' % DNS_SERVER)
    output.close()

    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named/test_view/sub.university.lcl.db' % DNS_SERVER,
        'ns2 3600 in aaq 192.168.1.104', 'ns2 3600 in a 192.168.1.104')
    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named/test_view/sub.university.lcl.db' % DNS_SERVER,
        ' 796 10800', ' 10800')
    output = os.popen('python %s --config-file %s --verbose' % (
        EXEC, CONFIG_FILE))
    self.assertEqual(output.read(),
        'Finished - temp_dir/%s/named.conf.a\n'
        'Finished - temp_dir/%s/named/test_view/sub.university.lcl.db\n'
        '--------------------------------------------------------------------\n'
        'Checked 1 named.conf file(s) and 1 zone file(s)\n'
        '\n'
        'All checks successful\n' % (DNS_SERVER, DNS_SERVER))
    output.close()

    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named/test_view/sub.university.lcl.db' % DNS_SERVER,
        ' 10800', ' 810 10800')
    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named.conf.a' % DNS_SERVER,
        'type master;', 'type bad_type;')
    output = os.popen('python %s --config-file %s' % (
        EXEC, CONFIG_FILE))
    self.assertTrue(re.search('[\']bad_type[\'] unexpected',output.read()))
    output.close()

    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named.conf.a' % DNS_SERVER, 
        'type bad_type;', 'type master;')
    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named.conf.a' % DNS_SERVER,
        'type master;',
        'type master;\nwrong;')
    output = os.popen('python %s --config-file %s' % (
        EXEC, CONFIG_FILE))
    lines = output.read()
    self.assertTrue(re.search('unknown option \'wrong\'', lines))
    output.close()

    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named.conf.a' % DNS_SERVER,
        'wrong;',
        '')
    self.TarReplaceString(
        self.tree_exporter_instance.tar_file_name,
        '%s/named.conf.a' % DNS_SERVER,
        'options { directory "%s"; };' % NAMED_DIR,
        '\noptions\n{\ndirectory "another";\n};\noptions {\n print-time yes;};\n')
    output = os.popen('python %s --config-file %s' % (
        EXEC, CONFIG_FILE))
    lines = output.read()
    ##ISCPY now combines directives defined twice
    ##self.assertTrue(re.search('\'options\' redefined near \'options\'',lines))
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
