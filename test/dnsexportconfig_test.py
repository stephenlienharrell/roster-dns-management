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

import roster_core
from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf.real'
EXEC = '../roster-config-manager/scripts/dnsexportconfig'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
KEY_FILE = 'test_data/rndc.key'
USERNAME = 'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TEST_DNS_SERVER = u'localhost'
SSH_ID = 'test_data/roster_id_dsa'
SSH_USER = getpass.getuser()


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
        'exporter']['root_config_dir'].rstrip('/').lstrip('./')
    self.backup_dir = self.config_instance.config_file[
        'exporter']['backup_dir'].rstrip('/').lstrip('./')
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    self.named_dir = os.path.expanduser(
        self.config_instance.config_file['exporter']['named_dir'])
    if( not os.path.exists(self.named_dir)):
      os.mkdir(self.named_dir)

    db_instance = self.config_instance.GetDb()
    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()
    self.db_instance = db_instance

  def tearDown(self):
    if( os.path.exists(KEY_FILE) ):
      os.remove(KEY_FILE)
    if( os.path.exists(self.backup_dir) ):
      shutil.rmtree(self.backup_dir)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    if( os.path.exists(self.named_dir)):
      shutil.rmtree(self.named_dir)

  def testCheckConfig(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'sub.university.edu', u'master',
                                u'sub.university.edu.', view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(), []) 
    output = os.popen('python %s -f test_data/test_zone.db '
                      '--view test_view -u %s --config-file %s '
                      '-z sub.university.edu' % ( 
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
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'options{allow-transfer {"none";};}')

    self.tree_exporter_instance.ExportAllBindTrees()

    output = os.popen('python %s -f --config-file %s '
    '-u %s --ssh-id %s' % (
        EXEC, CONFIG_FILE, SSH_USER, SSH_ID))
    lines = output.read().split('\n')
    self.assertTrue('[%s@%s] out: server reload successful\r' % (
        SSH_USER, TEST_DNS_SERVER) in lines)
    output.close()
    
if( __name__ == '__main__' ):
      unittest.main()
