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

"""Regression test for tree exporter

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'

import tarfile
import unittest
import os

import tree_exporter_test_lib
from roster_config_manager import tree_exporter
from roster_config_manager import config_lib

class TestTreeExporter(tree_exporter_test_lib.TreeExportTestCase):
  def setUp(self):
    super(TestTreeExporter, self).setUp()
    self.tree_exporter_instance = tree_exporter.BindTreeExport(tree_exporter_test_lib.CONFIG_FILE)
    self.config_lib_instance = config_lib.ConfigLib(tree_exporter_test_lib.CONFIG_FILE)
    self.tree_exporter_instance.db_instance.StartTransaction()
    self.data = self.tree_exporter_instance.GetRawData()
    self.tree_exporter_instance.db_instance.EndTransaction()
    self.cooked_data = self.tree_exporter_instance.CookData(self.data[0])

  def testTreeExporterListRecordArgumentDefinitions(self):
    search_record_arguments_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments')

    self.db_instance.StartTransaction()
    try:
      record_arguments = self.db_instance.ListRow('record_arguments',
                                                  search_record_arguments_dict)
    finally:
      self.db_instance.EndTransaction()

    self.assertEqual(self.tree_exporter_instance.ListRecordArgumentDefinitions(
        record_arguments),
        {u'a': [{'argument_name': u'assignment_ip', 'argument_order': 0}],
         u'soa': [{'argument_name': u'name_server', 'argument_order': 0},
                  {'argument_name': u'admin_email', 'argument_order': 1},
                  {'argument_name': u'serial_number', 'argument_order': 2},
                  {'argument_name': u'refresh_seconds', 'argument_order': 3},
                  {'argument_name': u'retry_seconds', 'argument_order': 4},
                  {'argument_name': u'expiry_seconds', 'argument_order': 5},
                  {'argument_name': u'minimum_seconds', 'argument_order': 6}],
         u'ns': [{'argument_name': u'name_server', 'argument_order': 0}],
         u'ptr': [{'argument_name': u'assignment_host', 'argument_order': 0}],
         u'aaaa': [{'argument_name': u'assignment_ip', 'argument_order': 0}],
         u'cname': [{'argument_name': u'assignment_host',
                     'argument_order': 0}],
         u'srv': [{'argument_name': u'priority', 'argument_order': 0},
                  {'argument_name': u'weight', 'argument_order': 1},
                  {'argument_name': u'port', 'argument_order': 2},
                  {'argument_name': u'assignment_host', 'argument_order': 3}],
         u'hinfo': [{'argument_name': u'hardware', 'argument_order': 0},
                    {'argument_name': u'os', 'argument_order': 1}],
         u'txt': [{'argument_name': u'quoted_text', 'argument_order': 0}],
         u'mx': [{'argument_name': u'priority', 'argument_order': 0},
                 {'argument_name': u'mail_server', 'argument_order': 1}]})

  def testTreeExporterSortRecords(self):
    records_dict = self.db_instance.GetEmptyRowDict('records')
    record_args_assignment_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments_records_assignments')
    self.db_instance.StartTransaction()
    try:
      records = self.db_instance.ListRow(
          'records', records_dict, 'record_arguments_records_assignments',
          record_args_assignment_dict)
    finally:
      self.db_instance.EndTransaction()

    self.assertEqual(self.tree_exporter_instance.SortRecords(records),
        {(u'university.edu', u'external_dep'): 
          {8: {'target': u'computer1',
            'ttl': 3600,
            'record_type': u'a',
            'view_name': u'external',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'assignment_ip': u'1.2.3.5'},
       11: {'target': u'computer3',
            'ttl': 3600,
            'record_type': u'a',
            'view_name': u'external',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'assignment_ip': u'1.2.3.6'},
       5: {u'serial_number': 20091234,
           u'refresh_seconds': 5,
            'target': u'@',
           u'name_server': u'ns1.university.edu.',
           u'retry_seconds': 5,
            'ttl': 3600,
           u'minimum_seconds': 5,
            'record_type': u'soa',
            'view_name': u'external',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'admin_email': u'admin@university.edu.',
           u'expiry_seconds': 5}},
     (u'4.3.2.in-addr', u'external_dep'): 
      {2: {u'serial_number': 20091226,
           u'refresh_seconds': 5,
            'target': u'@',
           u'name_server': u'ns1.university.edu.',
           u'retry_seconds': 5,
            'ttl': 3600,
           u'minimum_seconds': 5,
            'record_type': u'soa',
             'view_name': u'external',
            'last_user': u'sharrell',
            'zone_name': u'4.3.2.in-addr',
           u'admin_email': u'admin@university.edu.',
           u'expiry_seconds': 5},
       15: {'target': u'1',
            'ttl': 3600,
            'record_type': u'ptr',
            'view_name': u'external',
            'last_user': u'sharrell',
            'zone_name': u'4.3.2.in-addr',
           u'assignment_host': u'computer1.university.edu.'}},
     (u'168.192.in-addr', u'internal_dep'): 
      {16: {'target': u'4',
            'ttl': 3600,
            'record_type': u'ptr',
            'view_name': u'internal',
            'last_user': u'sharrell',
            'zone_name': u'168.192.in-addr',
           u'assignment_host': u'computer4.university.edu.'},
       1: {u'serial_number': 20091225,
           u'refresh_seconds': 5,
            'target': u'@',
           u'name_server': u'ns1.university.edu.',
           u'retry_seconds': 5,
            'ttl': 3600,
           u'minimum_seconds': 5,
            'record_type': u'soa',
            'view_name': u'internal',
            'last_user': u'sharrell',
            'zone_name': u'168.192.in-addr',
           u'admin_email': u'admin@university.edu.',
           u'expiry_seconds': 5}},
     (u'university.edu', u'private_dep'): 
      {4: {u'serial_number': 20091227,
           u'refresh_seconds': 5,
            'target': u'@',
           u'name_server': u'ns1.university.edu.',
           u'retry_seconds': 5,
            'ttl': 3600,
           u'minimum_seconds': 5,
            'record_type': u'soa',
            'view_name': u'private',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'admin_email': u'admin@university.edu.',
           u'expiry_seconds': 5}},
     (u'university.edu', u'internal_dep'): 
       {9: {'target': u'computer1',
            'ttl': 3600,
            'record_type': u'a',
            'view_name': u'internal',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'assignment_ip': u'192.168.1.1'},
       10: {'target': u'computer2',
            'ttl': 3600,
            'record_type': u'a',
            'view_name': u'internal',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'assignment_ip': u'192.168.1.2'},
       3: {u'serial_number': 20091229,
           u'refresh_seconds': 5,
            'target': u'@',
           u'name_server': u'ns1.university.edu.',
           u'retry_seconds': 5,
            'ttl': 3600,
           u'minimum_seconds': 5,
            'record_type': u'soa',
            'view_name': u'internal',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'admin_email': u'admin@university.edu.',
           u'expiry_seconds': 5},
       12: {'target': u'computer4',
            'ttl': 3600,
            'record_type': u'a',
            'view_name': u'internal',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'assignment_ip': u'192.168.1.4'}},
    (u'university.edu', u'any'): 
      {14: {'target': u'@',
           u'name_server': u'ns2.university.edu.',
            'ttl': 3600,
            'record_type': u'ns',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu'},
       13: {'target': u'@',
           u'name_server': u'ns1.university.edu.',
            'ttl': 3600,
            'record_type': u'ns',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu'},
        6: {'target': u'@',
            'ttl': 3600,
           u'priority': 1,
            'record_type': u'mx',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'mail_server': u'mail1.university.edu.'},
        7: {'target': u'@',
            'ttl': 3600,
           u'priority': 1,
            'record_type': u'mx',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'mail_server': u'mail2.university.edu.'}}})

  def testTreeExporterExportAllBindTreesError(self):
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    zone_view_assignments_dict['zone_origin'] = u'university3.edu.'
    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'private_dep')
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'priv.university.edu')

    self.db_instance.StartTransaction()
    rows = self.db_instance.ListRow(
      'zone_view_assignments', zone_view_assignments_dict)
    self.assertEqual(len(rows), 1)
    row = rows[0]

    #Removing the private_dep assignment
    self.db_instance.RemoveRow('zone_view_assignments', row)

    #Chaning it to any
    row['zone_view_assignments_view_dependency'] = u'any'
    self.db_instance.MakeRow('zone_view_assignments', row)
    self.db_instance.EndTransaction()

    self.core_instance.SetMaintenanceFlag(0)
    self.assertRaises(tree_exporter.Error,
                      self.tree_exporter_instance.ExportAllBindTrees)

  def testTreeExporterMakeNamedConf(self):
    self.core_instance.SetMaintenanceFlag(1)
    self.assertRaises(tree_exporter.MaintenanceError,
                      self.tree_exporter_instance.ExportAllBindTrees)
    self.core_instance.SetMaintenanceFlag(0)
    self.tree_exporter_instance.ExportAllBindTrees()
    self.config_lib_instance.UnTarDnsTree()
    n_conf = self.tree_exporter_instance.MakeNamedConf(self.data[0],
        self.cooked_data, u'internal_dns', 'db', 'remote_bind_dir')
   
    expected_n_conf = (
        u'#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "remote_bind_dir/named";\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t''10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t'
        '192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "external" {\n'
        '\tmatch-clients { \n'
        '\t\tpublic;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/4.3.2.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "internal" {\n'
        '\tmatch-clients { \n'
        '\t\t!public;\n'
        '\t\tsecret;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "internal/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "168.192.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "internal/168.192.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};')


    self.assertEqual(n_conf, expected_n_conf)

    # Test creating binary named conf
    binary_n_conf = self.tree_exporter_instance.MakeNamedConf(self.data[0],
        self.cooked_data, u'internal_dns', 'db', 'remote_bind_dir', binary=True)

    expected_binary_n_conf = (
        u'#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "remote_bind_dir/named";\n'
        'masterfile-format raw;\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "external" {\n'
        '\tmatch-clients { \n'
        '\t\tpublic;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/4.3.2.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "internal" {\n'
        '\tmatch-clients { \n'
        '\t\t!public;\n'
        '\t\tsecret;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "internal/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "168.192.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "internal/168.192.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};')
    self.assertEqual(binary_n_conf, expected_binary_n_conf)

    for fname in ['audit_log_replay_dump-1.bz2', 'full_database_dump-1.bz2',
                  self.tree_exporter_instance.tar_file_name]:
      if( os.path.exists(fname) ):
        os.remove(fname)

    self.assertRaises(tree_exporter.ChangesNotFoundError,
                      self.tree_exporter_instance.ExportAllBindTrees)

  def testTreeExporterCookRawDump(self):
    self.db_instance.StartTransaction()
    raw_dump = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    dump_lines = ''.join(self.tree_exporter_instance.CookRawDump(raw_dump)[1])

    self.core_instance.SetMaintenanceFlag(1)
    self.core_instance.MakeZoneType(u'zonetype5')

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(dump_lines)
    self.db_instance.EndTransaction()

    self.db_instance.StartTransaction()
    raw_dump_2 = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()

    self.assertEquals(raw_dump, raw_dump_2)

    self.db_instance.StartTransaction()
    raw_dump = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    dump_lines = ''.join(self.tree_exporter_instance.CookRawDump(raw_dump)[0])

    self.core_instance.MakeZoneType(u'zonetype5')

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(dump_lines)
    self.db_instance.EndTransaction()

    self.db_instance.StartTransaction()
    raw_dump_2 = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    # audit log is constantly changing
    del raw_dump['audit_log']
    del raw_dump_2['audit_log']

    self.assertEquals(raw_dump, raw_dump_2)

    self.db_instance.StartTransaction()
    raw_dump = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    dump_lines = ''.join(self.tree_exporter_instance.CookRawDump(raw_dump)[0])

    self.core_instance.SetMaintenanceFlag(1)

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(dump_lines)
    self.db_instance.EndTransaction()

    self.db_instance.StartTransaction()
    raw_dump_2 = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    del raw_dump['audit_log']
    del raw_dump_2['audit_log']

    self.assertNotEquals(raw_dump, raw_dump_2)

  def testTreeExporterGetRawData(self):
    self.tree_exporter_instance.db_instance.StartTransaction()
    raw_data = self.tree_exporter_instance.GetRawData()
    self.tree_exporter_instance.db_instance.EndTransaction()

    ## Testing the RawData raw_data[0]
    self.assertEqual(raw_data[0]['dns_server_sets'],
        ({'dns_server_set_name':u'external_dns'},
         {'dns_server_set_name':u'internal_dns'},
         {'dns_server_set_name':u'private_dns'}))

    test_assignments = [{'view_acl_assignments_range_allowed': 1, 
                        'view_acl_assignments_view_name': u'internal', 
                        'view_acl_assignments_dns_server_set_name': u'internal_dns', 
                        'view_acl_assignments_acl_name': u'secret'}, 
                       {'view_acl_assignments_range_allowed': 0, 
                        'view_acl_assignments_view_name':
                        u'internal', 'view_acl_assignments_dns_server_set_name': u'internal_dns',
                        'view_acl_assignments_acl_name': u'public'},
                       {'view_acl_assignments_range_allowed': 1,
                        'view_acl_assignments_view_name': u'external',
                        'view_acl_assignments_dns_server_set_name': u'internal_dns',
                        'view_acl_assignments_acl_name': u'public'},
                       {'view_acl_assignments_range_allowed': 0,
                        'view_acl_assignments_view_name': u'private',
                        'view_acl_assignments_dns_server_set_name': u'private_dns',
                        'view_acl_assignments_acl_name': u'secret'}]

    self.assertTrue(len(raw_data[0]['view_acl_assignments']) ==
                    len(test_assignments))

    for assign in test_assignments:
      self.assertTrue(assign in raw_data[0]['view_acl_assignments'])

    self.assertEqual(raw_data[0]['view_dependency_assignments'],
        ({'view_dependency_assignments_view_dependency':u'any',
          'view_dependency_assignments_view_name':u'external'},
         {'view_dependency_assignments_view_dependency':u'external_dep',
          'view_dependency_assignments_view_name':u'external'},
         {'view_dependency_assignments_view_dependency':u'any',
          'view_dependency_assignments_view_name':u'internal'},
         {'view_dependency_assignments_view_dependency':u'internal_dep',
          'view_dependency_assignments_view_name':u'internal'},
         {'view_dependency_assignments_view_dependency':u'any',
          'view_dependency_assignments_view_name':u'private'},
         {'view_dependency_assignments_view_dependency':u'private_dep',
          'view_dependency_assignments_view_name':u'private'}))

    self.assertEqual(raw_data[0]['zone_view_assignments'],
         ({'zone_origin': u'university.edu.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'university.edu',
           'zone_view_assignments_view_dependency': u'internal_dep',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'},
          {'zone_origin': u'university.edu.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'university.edu',
           'zone_view_assignments_view_dependency': u'any',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'},
          {'zone_origin': u'university.edu.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'university.edu',
           'zone_view_assignments_view_dependency': u'external_dep',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'},
          {'zone_origin': u'university.edu.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'university.edu',
           'zone_view_assignments_view_dependency': u'private_dep',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'},
          {'zone_origin': u'university2.edu.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'int.university.edu',
           'zone_view_assignments_view_dependency': u'internal_dep',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'},
          {'zone_origin': u'university3.edu.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'priv.university.edu',
           'zone_view_assignments_view_dependency': u'private_dep',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'},
          {'zone_origin': u'168.192.in-addr.arpa.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'168.192.in-addr',
           'zone_view_assignments_view_dependency': u'internal_dep',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'},
          {'zone_origin': u'4.3.2.in-addr.arpa.',
           'zone_view_assignments_zone_type': u'master',
           'zone_view_assignments_zone_name': u'4.3.2.in-addr',
           'zone_view_assignments_view_dependency': u'external_dep',
           'zone_options': u'(dp1\nVallow-update\np2\n(dp3\nVnone\np4\nI01\nss.'}))

    ## Testing the RawDump raw_data[1]
    self.assertEqual(raw_data[1]['zones']['rows'],
         [{'zone_name': u"'168.192.in-addr'", 'zones_id': u'7'},
          {'zone_name': u"'4.3.2.in-addr'", 'zones_id': u'8'},
          {'zone_name': u"'int.university.edu'", 'zones_id': u'5'},
          {'zone_name': u"'priv.university.edu'", 'zones_id': u'6'},
          {'zone_name': u"'university.edu'", 'zones_id': u'4'}])

    self.assertEqual(raw_data[1]['reserved_words']['columns'],
        [u'reserved_word_id', u'reserved_word'])

    self.assertEqual(raw_data[1]['reserved_words']['rows'],
        [])

    self.assertEqual(raw_data[1]['zone_types']['rows'],
        [{'zone_type': "'forward'", 'zone_type_id': '3'},
         {'zone_type': "'hint'", 'zone_type_id': '4'},
         {'zone_type': "'master'", 'zone_type_id': '1'},
         {'zone_type': "'slave'", 'zone_type_id': '2'}])

    self.assertEqual(raw_data[1]['users']['rows'],
        [{'access_level': '0',
          'user_name': "'tree_export_user'",
          'users_id': '1'},
         {'access_level': '32',
          'user_name': "'jcollins'",
          'users_id': '2'},
         {'access_level': '128',
          'user_name': "'sharrell'",
          'users_id': '3'},
         {'access_level': '64',
          'user_name': "'shuey'",
          'users_id': '4'}])

    self.assertEqual(raw_data[1]['view_dependency_assignments']['rows'],
        [{'view_dependency_assignments_view_dependency': u"'any'",
          'view_dependency_assignments_id': u'4',
          'view_dependency_assignments_view_name': u"'external'"},
         {'view_dependency_assignments_view_dependency': u"'external_dep'",
          'view_dependency_assignments_id': u'3',
          'view_dependency_assignments_view_name': u"'external'"},
         {'view_dependency_assignments_view_dependency': u"'any'",
          'view_dependency_assignments_id': u'2',
          'view_dependency_assignments_view_name': u"'internal'"},
         {'view_dependency_assignments_view_dependency': u"'internal_dep'",
          'view_dependency_assignments_id': u'1',
          'view_dependency_assignments_view_name': u"'internal'"},
         {'view_dependency_assignments_view_dependency': u"'any'",
          'view_dependency_assignments_id': u'6',
          'view_dependency_assignments_view_name': u"'private'"},
         {'view_dependency_assignments_view_dependency': u"'private_dep'",
          'view_dependency_assignments_id': u'5',
          'view_dependency_assignments_view_name': u"'private'"}])

  def testTreeExporterCookData(self):
    self.tree_exporter_instance.db_instance.StartTransaction()
    raw_data = self.tree_exporter_instance.GetRawData()
    self.tree_exporter_instance.db_instance.EndTransaction()
    cooked_data = self.tree_exporter_instance.CookData(raw_data[0])

    self.assertEqual(cooked_data['dns_server_sets']['external_dns'],
         {'dns_servers': [u'ns1.university.edu', u'dns2.university.edu', u'dns3.university.edu'],
          'view_order': {1: u'external'},
          'views': {u'external': {'view_options': u'recursion no;',
          'zones': {u'university.edu': {'zone_type': u'master',
          'records': [{'target': '@',
                      u'name_server': u'ns2.university.edu.',
                       'ttl': 3600,
                       'record_type': u'ns',
                       'view_name': u'any',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu'},
                      {'target': '@',
                       u'name_server': u'ns1.university.edu.',
                       'ttl': 3600,
                       'record_type': u'ns',
                       'view_name': u'any',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu'},
                      {'target': '@',
                       'ttl': 3600,
                      u'priority': 1,
                       'record_type': u'mx',
                       'view_name': u'any',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                      u'mail_server': u'mail1.university.edu.'},
                      {'target': '@',
                       'ttl': 3600,
                      u'priority': 1,
                       'record_type': u'mx',
                       'view_name': u'any',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                      u'mail_server': u'mail2.university.edu.'},
                      {'target': 'computer1',
                       'ttl': 3600,
                       'record_type': u'a',
                       'view_name': u'external',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                      u'assignment_ip': u'1.2.3.5'},
                      {'target': 'computer3',
                       'ttl': 3600,
                       'record_type': u'a',
                       'view_name': u'external',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                      u'assignment_ip': u'1.2.3.6'},
                     {u'serial_number': 20091234,
                      u'refresh_seconds': 5,
                       'target': '@',
                      u'name_server': u'ns1.university.edu.',
                      u'retry_seconds': 5,
                       'ttl': 3600,
                      u'minimum_seconds': 5,
                       'record_type': u'soa',
                       'view_name': u'external',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                      u'admin_email': u'admin@university.edu.',
                      u'expiry_seconds': 5}],
          'zone_origin': 'university.edu.',
          'zone_options': u'allow-update { none; };'},

         u'4.3.2.in-addr': {'zone_type': u'master',
                     'records': [{u'serial_number': 20091226,
                      u'refresh_seconds': 5,
                       'target': '@',
                      u'name_server': u'ns1.university.edu.',
                      u'retry_seconds': 5,
                       'ttl': 3600,
                      u'minimum_seconds': 5,
                       'record_type': u'soa',
                       'view_name': u'external',
                       'last_user': u'sharrell',
                       'zone_name': u'4.3.2.in-addr',
                      u'admin_email': u'admin@university.edu.',
                      u'expiry_seconds': 5},
                      {'target': '1',
                       'ttl': 3600,
                       'record_type': u'ptr',
                       'view_name': u'external',
                       'last_user': u'sharrell',
                       'zone_name': u'4.3.2.in-addr',
                      u'assignment_host': 'computer1.university.edu.'}],
                        'zone_origin': '4.3.2.in-addr.arpa.', 
                        'zone_options': u'allow-update { none; };'}}, 
         'acls': [u'public']}}})

    self.assertEqual(cooked_data['dns_server_sets']['private_dns'],
        {'dns_servers': [u'dns4.university.edu'],
          'view_order': {1: u'private'},
          'views': {u'private': {'view_options': u'recursion no;',
          'zones': {u'university.edu': {'zone_type': u'master',
          'records': [{'target': '@',
           u'name_server': u'ns2.university.edu.',
            'ttl': 3600,
            'record_type': u'ns',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu'},
           {'target': '@',
           u'name_server': u'ns1.university.edu.',
            'ttl': 3600,
            'record_type': u'ns',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu'},
           {'target': '@',
            'ttl': 3600,
           u'priority': 1,
            'record_type': u'mx',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'mail_server': u'mail1.university.edu.'},
           {'target': '@',
            'ttl': 3600,
           u'priority': 1,
            'record_type': u'mx',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'mail_server': u'mail2.university.edu.'},
          {u'serial_number': 20091227,
           u'refresh_seconds': 5,
            'target': '@',
           u'name_server': u'ns1.university.edu.',
           u'retry_seconds': 5,
            'ttl': 3600,
           u'minimum_seconds': 5,
            'record_type': u'soa',
            'view_name': u'private',
            'last_user': u'sharrell',
            'zone_name': u'university.edu',
           u'admin_email': u'admin@university.edu.',
           u'expiry_seconds': 5}],
            'zone_origin': 'university.edu.',
            'zone_options': u'allow-update { none; };'}},
            'acls': [u'secret']}}})

    self.assertEqual(cooked_data['dns_server_sets']['internal_dns'],
         {'dns_servers': [u'ns1.int.university.edu', u'dns1.university.edu'],
           'view_order': {1: u'external', 2: u'internal'},
           'views': {u'internal': {'view_options': u'recursion no;',
             'zones': {u'university.edu': {'zone_type': u'master',
               'records': [{'target': '@',
                 u'name_server': u'ns2.university.edu.',
                 'ttl': 3600,
                 'record_type': u'ns',
                 'view_name': u'any',
                 'last_user': u'sharrell',
                 'zone_name': u'university.edu'},
                 {'target': '@',
                   u'name_server': u'ns1.university.edu.',
                   'ttl': 3600,
                   'record_type': u'ns',
                   'view_name': u'any',
                   'last_user': u'sharrell',
                   'zone_name': u'university.edu'},
                 {'target': '@',
                   'ttl': 3600,
                   u'priority': 1,
                   'record_type': u'mx',
                   'view_name': u'any',
                   'last_user': u'sharrell',
                   'zone_name': u'university.edu',
                   u'mail_server': u'mail1.university.edu.'},
                 {'target': '@',
                   'ttl': 3600,
                   u'priority': 1,
                   'record_type': u'mx',
                   'view_name': u'any',
                   'last_user': u'sharrell',
                   'zone_name': u'university.edu',
                   u'mail_server': u'mail2.university.edu.'},
                 {'target': 'computer1',
                   'ttl': 3600,
                   'record_type': u'a',
                   'view_name': u'internal',
                   'last_user': u'sharrell',
                   'zone_name': u'university.edu',
                   u'assignment_ip': u'192.168.1.1'},
                 {'target': 'computer2',
                   'ttl': 3600,
                   'record_type': u'a',
                   'view_name': u'internal',
                   'last_user': u'sharrell',
                   'zone_name': u'university.edu',
                   u'assignment_ip': u'192.168.1.2'},
                 {u'serial_number': 20091229,
                   u'refresh_seconds': 5,
                   'target': '@',
                   u'name_server': u'ns1.university.edu.',
                   u'retry_seconds': 5,
                   'ttl': 3600,
                   u'minimum_seconds': 5,
                   'record_type': u'soa',
                   'view_name': u'internal',
                   'last_user': u'sharrell',
                   'zone_name': u'university.edu',
                   u'admin_email': u'admin@university.edu.',
                   u'expiry_seconds': 5},
                 {'target': 'computer4',
                     'ttl': 3600,
                     'record_type': u'a',
                     'view_name': u'internal',
                     'last_user': u'sharrell',
                     'zone_name': u'university.edu',
                     u'assignment_ip': u'192.168.1.4'}],
           'zone_origin': 'university.edu.',
           'zone_options': u'allow-update { none; };'},
      u'168.192.in-addr': {'zone_type': u'master',
          'records': [{'target': '4',
            'ttl': 3600,
            'record_type': u'ptr',
            'view_name': u'internal',
            'last_user': u'sharrell',
            'zone_name': u'168.192.in-addr',
            u'assignment_host': 'computer4.university.edu.'},
            {u'serial_number': 20091225,
              u'refresh_seconds': 5,
              'target': '@',
              u'name_server': u'ns1.university.edu.',
              u'retry_seconds': 5,
              'ttl': 3600,
              u'minimum_seconds': 5,
              'record_type': u'soa',
              'view_name': u'internal',
              'last_user': u'sharrell',
              'zone_name': u'168.192.in-addr',
              u'admin_email': u'admin@university.edu.',
              u'expiry_seconds': 5}],
            'zone_origin': '168.192.in-addr.arpa.',
            'zone_options': u'allow-update { none; };'}},
      'acls': [u'secret', u'public']},
    u'external': {'view_options': u'recursion no;',
        'zones': {u'university.edu': {'zone_type': u'master',
          'records': [{'target': '@',
            u'name_server': u'ns2.university.edu.',
            'ttl': 3600,
            'record_type': u'ns',
            'view_name': u'any',
            'last_user': u'sharrell',
            'zone_name': u'university.edu'},
            {'target': '@',
              u'name_server': u'ns1.university.edu.',
              'ttl': 3600,
              'record_type': u'ns',
              'view_name': u'any',
              'last_user': u'sharrell',
              'zone_name': u'university.edu'},
            {'target': '@',
              'ttl': 3600,
              u'priority': 1,
              'record_type': u'mx',
              'view_name': u'any',
              'last_user': u'sharrell',
              'zone_name': u'university.edu',
              u'mail_server': u'mail1.university.edu.'},
            {'target': '@',
              'ttl': 3600,
              u'priority': 1,
              'record_type': u'mx',
              'view_name': u'any',
              'last_user': u'sharrell',
              'zone_name': u'university.edu',
              u'mail_server': u'mail2.university.edu.'},
            {'target': 'computer1',
              'ttl': 3600,
              'record_type': u'a',
              'view_name': u'external',
              'last_user': u'sharrell',
              'zone_name': u'university.edu',
              u'assignment_ip': u'1.2.3.5'},
            {'target': 'computer3',
              'ttl': 3600,
              'record_type': u'a',
              'view_name': u'external',
              'last_user': u'sharrell',
              'zone_name': u'university.edu',
              u'assignment_ip': u'1.2.3.6'},
            {u'serial_number': 20091234,
              u'refresh_seconds': 5,
              'target': '@',
              u'name_server': u'ns1.university.edu.',
              u'retry_seconds': 5,
              'ttl': 3600,
              u'minimum_seconds': 5,
              'record_type': u'soa',
              'view_name': u'external',
              'last_user': u'sharrell',
              'zone_name': u'university.edu',
              u'admin_email': u'admin@university.edu.',
              u'expiry_seconds': 5}],
            'zone_origin': 'university.edu.',
          'zone_options': u'allow-update { none; };'},
    u'4.3.2.in-addr': {'zone_type': u'master',
        'records': [{u'serial_number': 20091226,
          u'refresh_seconds': 5,
          'target': '@',
          u'name_server': u'ns1.university.edu.',
          u'retry_seconds': 5,
          'ttl': 3600,
          u'minimum_seconds': 5,
          'record_type': u'soa',
          'view_name': u'external',
          'last_user': u'sharrell',
          'zone_name': u'4.3.2.in-addr',
          u'admin_email': u'admin@university.edu.',
          u'expiry_seconds': 5},
          {'target': '1',
            'ttl': 3600,
            'record_type': u'ptr',
            'view_name': u'external',
            'last_user': u'sharrell',
            'zone_name': u'4.3.2.in-addr',
            u'assignment_host': 'computer1.university.edu.'}],
          'zone_origin': '4.3.2.in-addr.arpa.',
          'zone_options': u'allow-update { none; };'}},
    'acls': [u'public']}}})

  def testTreeExporterListACLNamesByView(self):
    acl_names_private = self.tree_exporter_instance.ListACLNamesByView(
        self.data[0], u'private')
    self.assertEqual(
        acl_names_private, [u'secret'])
    acl_names_internal = self.tree_exporter_instance.ListACLNamesByView(
        self.data[0], u'internal')
    self.assertEqual(
        acl_names_internal, [u'secret', u'public'])
    acl_names_external = self.tree_exporter_instance.ListACLNamesByView(
        self.data[0], u'external')
    self.assertEqual(
        acl_names_external, [u'public'])

  def testTreeExporterListLatestNamedConfGlobalOptions(self):
    global_options_internal = (
        self.tree_exporter_instance.ListLatestNamedConfGlobalOptions(
            self.data[0], u'internal_dns'))
    self.assertEqual(
        global_options_internal, (
          'include "/etc/rndc.key";\n'
          'logging { category "update-security" { "security"; };\n'
          'category "queries" { "query_logging"; };\n'
          'channel "query_logging" { syslog local5;\n'
          'severity info; };\n'
          'category "client" { "null"; };\n'
          'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
          'print-time yes; }; };\n'
          'options { directory "test_data/named/named";\n'
          'recursion no;\n'
          'max-cache-size 512M; };\n'
          'controls { inet * allow { control-hosts; } keys { rndc-key; }; };'))
    global_options_external = (
        self.tree_exporter_instance.ListLatestNamedConfGlobalOptions(
            self.data[0], u'external_dns'))
    self.assertEqual(
        global_options_external,
            u'include "/etc/rndc.key";\n'
            'logging { category "update-security" { "security"; };\n'
            'category "queries" { "query_logging"; };\n'
            'channel "query_logging" { syslog local5;\n'
            'severity info; };\n'
            'category "client" { "null"; };\n'
            'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
            'print-time yes; }; };\n'
            'options { directory "test_data/named/named";\n'
            'recursion no;\n'
            'max-cache-size 512M; };\n'
            'controls { inet * allow { control-hosts; } keys { rndc-key; }; };')
    global_options_private = (
        self.tree_exporter_instance.ListLatestNamedConfGlobalOptions(
            self.data[0], u'private_dns'))
    self.assertEqual(
        global_options_private,
            u'include "/etc/rndc.key";\n'
            'logging { category "update-security" { "security"; };\n'
            'category "queries" { "query_logging"; };\n'
            'channel "query_logging" { syslog local5;\n'
            'severity info; };\n'
            'category "client" { "null"; };\n'
            'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
            'print-time yes; }; };\n'
            'options { directory "test_data/named/named";\n'
            'recursion no;\n'
            'max-cache-size 512M; };\n'
            'controls { inet * allow { control-hosts; } keys { rndc-key; }; };')

  def testTreeExporterExportAllBindTrees(self):
    self.core_instance.SetMaintenanceFlag(1)
    self.assertRaises(tree_exporter.MaintenanceError,
        self.tree_exporter_instance.ExportAllBindTrees)
    self.core_instance.SetMaintenanceFlag(0)
    self.tree_exporter_instance.ExportAllBindTrees()
    self.config_lib_instance.UnTarDnsTree()

    # Test ns1 named_conf
    expected_ns1_university_edu_named_conf_a_string = (
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s";\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "external" {\n'
        '\tmatch-clients { \n'
        '\t\t\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/4.3.2.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tree_exporter_test_lib.NAMED_DIR)

    # Test named_conf_a
    handle = open('%s/ns1.university.edu/named.conf.a' %
        self.root_config_dir, 'r')
    ns1_university_edu_named_conf_a_string = handle.read()
    handle.close()
    self.assertEqual(ns1_university_edu_named_conf_a_string,
                     expected_ns1_university_edu_named_conf_a_string)

    # Test ns1 binary named_conf
    expected_binary_ns1_university_edu_named_conf_b_string = (
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s";\n'
        'masterfile-format raw;\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "external" {\n'
        '\tmatch-clients { \n'
        '\t\t\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/university.edu.aa";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/4.3.2.in-addr.aa";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tree_exporter_test_lib.NAMED_DIR)

    # Test named_conf_b
    handle = open('%s/ns1.university.edu/named.conf.b' %
        self.root_config_dir, 'r')
    binary_ns1_university_edu_named_conf_b_string = handle.read()
    handle.close()
    self.assertEqual(binary_ns1_university_edu_named_conf_b_string,
                     expected_binary_ns1_university_edu_named_conf_b_string)

    handle = open(
        '%s/ns1.university.edu/named/external/4.3.2.in-addr.db' %
        self.root_config_dir, 'r')
    self.assertEqual(handle.read(),
                     '; This zone file is autogenerated. DO NOT EDIT.\n'
                     '$ORIGIN 4.3.2.in-addr.arpa.\n'
                     '@ 3600 in soa ns1.university.edu. '
                     'admin@university.edu. 20091226 5 5 5 5\n'
                     '1 3600 in ptr computer1.university.edu.\n')
    handle.close()
    handle = open(
        '%s/ns1.university.edu/named/external/university.edu.db' %
        self.root_config_dir, 'r')
    output = handle.read()
    handle.close()
    self.assertEqual(output,
        '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        '@ 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091234 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu.\n'
        '@ 3600 in ns ns2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        'computer1 3600 in a 1.2.3.5\n'
        'computer3 3600 in a 1.2.3.6\n')

    # Test dns1 named_conf
    expected_dns1_university_edu_named_conf_a_string = (
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s";\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "external" {\n'
        '\tmatch-clients { \n'
        '\t\tpublic;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/4.3.2.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "internal" {\n'
        '\tmatch-clients { \n'
        '\t\t!public;\n'
        '\t\tsecret;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
    '\t\tfile "named.ca";\n'
    '\t};\n'
    '\tzone "university.edu" {\n'
    '\t\ttype master;\n'
    '\t\tfile "internal/university.edu.db";\n'
    '\t\tallow-update { none; };\n'
    '\t};\n'
    '\tzone "168.192.in-addr.arpa" {\n'
    '\t\ttype master;\n'
    '\t\tfile "internal/168.192.in-addr.db";\n'
    '\t\tallow-update { none; };\n'
    '\t};\n'
    '};' % tree_exporter_test_lib.NAMED_DIR)


    # Test named_conf_a
    handle = open(
        '%s/dns1.university.edu/named.conf.a' % self.root_config_dir, 'r')
    dns1_university_edu_named_conf_a_string = handle.read()
    handle.close()
    self.assertEqual(dns1_university_edu_named_conf_a_string,
                     expected_dns1_university_edu_named_conf_a_string)

    # Test dns1 binary named_conf
    expected_binary_dns1_university_edu_named_conf_b_string = (
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s";\n'
        'masterfile-format raw;\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "external" {\n'
        '\tmatch-clients { \n'
        '\t\tpublic;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/university.edu.aa";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "external/4.3.2.in-addr.aa";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "internal" {\n'
        '\tmatch-clients { \n'
        '\t\t!public;\n'
        '\t\tsecret;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "internal/university.edu.aa";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "168.192.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "internal/168.192.in-addr.aa";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tree_exporter_test_lib.NAMED_DIR)

    # Test named_conf_b
    handle = open(
        '%s/dns1.university.edu/named.conf.b' % self.root_config_dir, 'r')
    binary_dns1_university_edu_named_conf_b_string = handle.read()
    handle.close()
    self.assertEqual(binary_dns1_university_edu_named_conf_b_string,
                     expected_binary_dns1_university_edu_named_conf_b_string)

    handle = open(
        '%s/ns1.int.university.edu/named/external/4.3.2.in-addr.db' %
        self.root_config_dir, 'r')
    output = handle.read()
    handle.close()
    self.assertEqual(output,
        '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN 4.3.2.in-addr.arpa.\n'
        '@ 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091226 5 5 5 5\n'
        '1 3600 in ptr computer1.university.edu.\n')

    handle = open(
        '%s/dns1.university.edu/named/external/university.edu.db' %
        self.root_config_dir, 'r')
    output = handle.read()
    handle.close()
    self.assertEqual(output,
        '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        '@ 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091234 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu.\n'
        '@ 3600 in ns ns2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        'computer1 3600 in a 1.2.3.5\n'
        'computer3 3600 in a 1.2.3.6\n')

    handle = open(
        '%s/dns1.university.edu/named/internal/168.192.in-addr.db' %
        self.root_config_dir, 'r')
    output = handle.read()
    handle.close()
    self.assertEqual(output,
        '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN 168.192.in-addr.arpa.\n'
        '@ 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091225 5 5 5 5\n'
        '4 3600 in ptr computer4.university.edu.\n')
    
    handle = open(
        '%s/dns1.university.edu/named/internal/university.edu.db' %
        self.root_config_dir, 'r')
    output = handle.read()
    handle.close()
    self.assertEqual(output,
        '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        '@ 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091229 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu.\n'
        '@ 3600 in ns ns2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        'computer1 3600 in a 192.168.1.1\n'
        'computer2 3600 in a 192.168.1.2\n'
        'computer4 3600 in a 192.168.1.4\n')

    # Test dns4 named_conf
    expected_dns4_university_edu_named_conf_a_string = (
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s";\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "private" {\n'
        '\tmatch-clients { \n'
        '\t\t!secret;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "private/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tree_exporter_test_lib.NAMED_DIR)


    # Test named_conf_a
    handle = open(
        '%s/dns4.university.edu/named.conf.a' % self.root_config_dir, 'r')
    dns4_university_edu_named_conf_a_string = handle.read()
    handle.close()
    self.assertEqual(dns4_university_edu_named_conf_a_string,
                     expected_dns4_university_edu_named_conf_a_string)

    # Test dns4 binary named_conf
    expected_binary_dns4_university_edu_named_conf_b_string = (
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s";\n'
        'masterfile-format raw;\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "private" {\n'
        '\tmatch-clients { \n'
        '\t\t!secret;\n'
        '\t };\n'
        '\trecursion no;\n'
        '\tzone "." {\n'
        '\t\ttype hint;\n'
        '\t\tfile "named.ca";\n'
        '\t};\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "private/university.edu.aa";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tree_exporter_test_lib.NAMED_DIR)

    # Test named_conf_b
    handle = open(
        '%s/dns4.university.edu/named.conf.b' % self.root_config_dir, 'r')
    binary_dns4_university_edu_named_conf_b_string = handle.read()
    handle.close()
    self.assertEqual(binary_dns4_university_edu_named_conf_b_string,
                     expected_binary_dns4_university_edu_named_conf_b_string)

    handle = open(
        '%s/dns4.university.edu/named/private/university.edu.db' %
        self.root_config_dir, 'r')
    output = handle.read()
    handle.close()
    self.assertEqual(output,
        '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        '@ 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091227 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu.\n'
        '@ 3600 in ns ns2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n'
        '@ 3600 in mx 1 mail2.university.edu.\n')

  def testTreeExporterAddToTarFile(self):
    tar_string = (  ## The string was arbitrarily chosen.
        u'options {\n'
        '\tdirectory "/var/domain";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n''\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n''\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n''\n'
        'include "/etc/rndc.key";\n')

    if not (os.path.exists(self.root_config_dir)):
        os.mkdir(self.root_config_dir)
    temp_tar_filename = '%s/temp_file.tar.bz2' % self.root_config_dir
    tar_file = tarfile.open(temp_tar_filename, 'w:bz2')
    self.tree_exporter_instance.AddToTarFile(tar_file, 'tar_string', tar_string)
    tar_file.close()

    tar_file = tarfile.open(temp_tar_filename, 'r:bz2')
    tar_file.extractall(self.root_config_dir)
    tar_file.close()

    handle = open('%s/tar_string' % self.root_config_dir , 'r')
    extracted_tar_string = handle.read()
    handle.close()

    self.assertEqual(extracted_tar_string, tar_string)

  def testNamedHeaderChangeDirectory(self):
    header_string = (  ## The string was arbitrarily chosen.
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff;\n'
        '};\n'
        'options {\n'
        '\tdirectory "/var/domain";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n''\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n''\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n''\n'
        'include "/etc/rndc.key";\n')
    self.assertEqual(self.tree_exporter_instance.NamedHeaderChangeDirectory(
        header_string, '/tmp/newdir'),
        'include "/etc/rndc.key";\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "/tmp/newdir";\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'otherstanza { stuff; };')
    header_string = (  ## The string was arbitrarily chosen.
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff;\n'
        '};\n' # No options stanza
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n''\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n''\n'
        'include "/etc/rndc.key";\n')
    self.assertEqual(self.tree_exporter_instance.NamedHeaderChangeDirectory(
        header_string, '/tmp/newdir'),
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'otherstanza { stuff; };\n'
        'options { directory "/tmp/newdir"; };')
    header_string = (  ## The string was arbitrarily chosen.
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff;\n'
        '};\n'
        'options {\n'
        '};\n''\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n''\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n''\n'
        'include "/etc/rndc.key";\n')
    self.assertEqual(self.tree_exporter_instance.NamedHeaderChangeDirectory(
        header_string, '/tmp/newdir'),
        'include "/etc/rndc.key";\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "/tmp/newdir"; };\n'
        'otherstanza { stuff; };')

    header_string = (  ## The string was arbitrarily chosen.
        'otherstanza{\n'
        '\tstuff;\n'
        '};\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n''\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n''\n'
        'include "/etc/rndc.key";\n')
    self.assertEqual(self.tree_exporter_instance.NamedHeaderChangeDirectory(
        header_string, '/tmp/newdir'),
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'otherstanza { stuff; };\n'
        'options { directory "/tmp/newdir"; };')


if( __name__ == '__main__' ):
  unittest.main()
