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

"""Regression test for roster_user_tools_bootstrap

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import os
import sys
import shutil
import unittest
import tarfile

import roster_core
from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnscheckconfig'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
KEY_FILE = 'test_data/rndc.key'
USERNAME = 'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'


class TestCheckConfig(unittest.TestCase):
  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.bind_config_dir = os.path.expanduser(
        self.config_instance.config_file['exporter']['root_config_dir'])
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)

    db_instance = self.config_instance.GetDb()
    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

    schema = roster_core.embedded_files.SCHEMA_FILE
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()
    self.db_instance = db_instance

  def tearDown(self):
    if( os.path.exists(KEY_FILE) ):
      os.remove(KEY_FILE)
    if( os.path.exists('backup') ):
      shutil.rmtree('backup')
    for fname in os.listdir('.'):
      if( fname.startswith('bind_configs_1') ):
        shutil.rmtree(fname)

  def testCheckConfig(self):
    self.assertEqual(self.core_instance.ListRecords(), []) 
    output = os.popen('python %s -f test_data/test_zone.db '
                      '--zone-view test_view -u %s --config-file %s' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone.db\n'
                     '16 records loaded from zone test_data/test_zone.db\n'
                     '16 total records added\n')
    output.close()

    self.core_instance.MakeDnsServer(u'dns1')
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()
    tar = tarfile.open(self.tree_exporter_instance.tar_file_name)
    tar.extractall()
    tar.close()

    output = os.popen3('/usr/sbin/rndc-confgen -a -c %s -r %s' % (
        KEY_FILE, EXEC))[2]
    self.assertEqual(output.read(), 'wrote key file "%s"\n' % KEY_FILE)
    output.close()

    output = os.popen('python %s -d test_data/backup -i 1 --config-file %s' % (
        EXEC, CONFIG_FILE))
    self.assertEqual(output.read(), '')
    output.close()
    
  def testCheckErrorConfig(self):
    f = open('test_data/test_zone.db', 'r')
    fcontents = f.read()
    f.close()
    
    fcontents = fcontents.replace('mail1.sub.university.edu.',
                                  'mail1.university.edu.')
    fcontents = fcontents.replace('mail1     in  a     192.168.1.101\n', '')

    f = open('test_data/test_zone2.db', 'w')
    f.writelines(fcontents)
    f.close()

    self.assertEqual(self.core_instance.ListRecords(), []) 
    output = os.popen('python %s -f test_data/test_zone2.db '
                      '--zone-view test_view -u %s --config-file %s' % ( 
                          ZONE_IMPORTER_EXEC, USERNAME, CONFIG_FILE))
    self.assertEqual(output.read(),
                     'Loading in test_data/test_zone2.db\n'
                     '15 records loaded from zone test_data/test_zone2.db\n'
                     '15 total records added\n')
    output.close()

    self.core_instance.MakeDnsServer(u'dns1')
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()
    tar = tarfile.open(self.tree_exporter_instance.tar_file_name)
    tar.extractall()
    tar.close()

    output = os.popen3('/usr/sbin/rndc-confgen -a -c %s -r %s' % (
        KEY_FILE, EXEC))[2]
    self.assertEqual(output.read(), 'wrote key file "%s"\n' % KEY_FILE)
    output.close()

    output = os.popen('python %s -d test_data/backup -i 1 --config-file %s' % (
        EXEC, CONFIG_FILE))
    self.assertEqual(output.read(),
        "ERROR: zone sub.university.edu/IN: sub.university.edu/MX "
        "'mail1.university.edu' (out of zone) has no addresses records "
        "(A or AAAA)\n"
        "zone sub.university.edu/IN: loaded serial 809\n"
        "OK\n\n")
    output.close()

    os.remove('test_data/test_zone2.db')

if( __name__ == '__main__' ):
      unittest.main()
