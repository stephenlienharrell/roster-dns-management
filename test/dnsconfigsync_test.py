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

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.14'


import os
import sys
import subprocess
import shutil
import unittest
import tarfile

import roster_core
from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf.real'
EXEC = '../roster-config-manager/scripts/dnsconfigsync'
ZONE_IMPORTER_EXEC='../roster-config-manager/scripts/dnszoneimporter'
KEY_FILE = 'test_data/rndc.key'
RNDC_CONF_FILE = 'test_data/rndc.conf'
USERNAME = 'sharrell'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
SSH_ID = 'test_data/roster_id_dsa'
SSH_USER = 'root'
TEST_DNS_SERVER = u'localhost'
NS_IP_ADDRESS = '127.0.0.1'
NS_DOMAIN = '' #Blank since using localhost


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
    if( os.path.exists('backup') ):
      shutil.rmtree('backup')
    if( os.path.exists('test_data/backup_dir') ):
      shutil.rmtree('test_data/backup_dir')

  def testNull(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    output = os.popen('python %s -f test_data/test_zone.db '
                      '--view test_view -u %s --config-file %s' % ( 
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
        u'set1', u'#options') # So we can test
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'any')
    self.tree_exporter_instance.ExportAllBindTrees()

    command = os.popen('python %s -i 26 -u %s --ssh-id %s --config-file %s' % (EXEC,
        SSH_USER, SSH_ID, CONFIG_FILE))
    lines = command.read().split('\n')
    # These lines will likely need changed depending on implementation
    self.assertTrue('Connecting to rsync on "%s"' % TEST_DNS_SERVER in lines)
    self.assertTrue('building file list ... done' in lines)
    self.assertTrue('named/' in lines)
    self.assertTrue('named/test_view/' in lines)
    # Variable line 5 'X bytes/sec'
    # Variable line 6 'total size is 1070  speedup is X'
    self.assertTrue('Connecting to ssh on "%s"' % TEST_DNS_SERVER in lines)
    self.assertTrue('server reload successful' in lines)
    command.close()

    command = os.popen('dig @%s%s mail1.sub.university.edu' % (
        TEST_DNS_SERVER, NS_DOMAIN))
    lines = command.readlines()
    id = lines[5].split()[-1]
    outputlines = ''.join(lines)
    testlines = (
        '\n'
        '%s'
        '; (1 server found)\n'
        ';; global options:  printcmd\n'
        ';; Got answer:\n'
        ';; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: %s\n'
        ';; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 2, ADDITIONAL: '
        '2\n'
        '\n'
        ';; QUESTION SECTION:\n'
        ';mail1.sub.university.edu. IN  A\n'
        '\n'
        ';; ANSWER SECTION:\n'
        'mail1.sub.university.edu. 3600 IN  A 192.168.1.101\n'
        '\n'
        ';; AUTHORITY SECTION:\n'
        'sub.university.edu.  3600  IN  NS  ns.sub.university.edu.\n'
        'sub.university.edu.  3600  IN  NS  ns2.sub.university.edu.\n'
        '\n'
        ';; ADDITIONAL SECTION:\n'
        'ns.sub.university.edu. 3600  IN  A 192.168.1.103\n'
        'ns2.sub.university.edu.  3600  IN  A 192.168.1.104\n'
        '\n'
        '%s'
        ';; SERVER: %s#53(%s)\n'
        '%s'
        ';; MSG SIZE  rcvd: 125\n'
        '\n' % (lines[1], id, lines[22], NS_IP_ADDRESS, NS_IP_ADDRESS,
                lines[24]))
    self.assertEqual(set(outputlines.split()), set(outputlines.split()))
    command.close()

if( __name__ == '__main__' ):
      unittest.main()
