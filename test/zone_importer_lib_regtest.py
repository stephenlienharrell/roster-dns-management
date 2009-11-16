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

"""Regression test for zone_importer_lib.py

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.6'


import unittest
import os

from roster_config_manager import zone_importer_lib
import roster_core


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
ZONE_FILE = 'test_data/test_zone.db'
REVERSE_ZONE_FILE = 'test_data/test_reverse_zone.db'
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'

class TestZoneImport(unittest.TestCase):

  def setUp(self):
    config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = config_instance.GetDb()

    schema = open(SCHEMA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.core_instance = roster_core.Core(u'sharrell', config_instance)

  def testMakeViewAndZone(self):
    importer_instance = zone_importer_lib.ZoneImport(ZONE_FILE,
                                                            CONFIG_FILE,
                                                            u'sharrell')
    self.assertFalse(self.core_instance.ListViews())
    self.assertFalse(self.core_instance.ListZones())
    importer_instance.view = u'internal'
    importer_instance.MakeViewAndZone()
    self.assertTrue(self.core_instance.ListViews())
    self.assertTrue(self.core_instance.ListZones())
    importer_instance.MakeViewAndZone()

  def testReverseZoneToCIDRBlock(self):
    importer_instance = zone_importer_lib.ZoneImport(ZONE_FILE,
                                                            CONFIG_FILE,
                                                            u'sharrell')
    self.assertRaises(zone_importer_lib.Error,
                      importer_instance.ReverseZoneToCIDRBlock)
    importer_instance.origin = '0.0.0.10.in-addr.arpa.'
    self.assertRaises(zone_importer_lib.Error,
                      importer_instance.ReverseZoneToCIDRBlock)
    importer_instance.origin = '0.10.in-addr.arpa.'
    self.assertEqual(importer_instance.ReverseZoneToCIDRBlock(), '10.0/16')

  def testFixHostname(self):
    importer_instance = zone_importer_lib.ZoneImport(ZONE_FILE,
                                                            CONFIG_FILE,
                                                            u'sharrell')
    self.assertEqual(importer_instance.FixHostname(u'host'),
                     u'host.sub.university.edu.')
    self.assertEqual(importer_instance.FixHostname(u'@'),
                     u'sub.university.edu.')
    self.assertEqual(importer_instance.FixHostname(u'university.edu.'),
                     u'university.edu.')

  def testMakeRecordsFromForwardZone(self):
    importer_instance = zone_importer_lib.ZoneImport(ZONE_FILE,
                                                            CONFIG_FILE,
                                                            u'sharrell')
    importer_instance.MakeRecordsFromZone()
    self.assertEquals(self.core_instance.ListRecords(record_type=u'soa'),
                      [{u'serial_number': 804, u'refresh_seconds': 10800,
                        'target': u'@',
                        u'name_server': u'ns.university.edu.',
                        u'retry_seconds': 3600, 'ttl': 3600,
                        u'minimum_seconds': 86400, 'record_type': u'soa',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu',
                        u'admin_email': u'hostmaster.ns.university.edu.',
                        u'expiry_seconds': 3600000}])
    self.assertEquals(self.core_instance.ListRecords(record_type=u'ns'),
                      [{'target': u'@',
                        u'name_server': u'ns.university.edu.', 'ttl': 3600,
                        'record_type': u'ns', 'view_name': u'any',
                        'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu'},
                       {'target': u'@',
                        u'name_server': u'ns2.university.edu.', 'ttl': 3600,
                        'record_type': u'ns', 'view_name': u'any',
                        'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu'}])
    self.assertEquals(self.core_instance.ListRecords(record_type=u'mx'),
                      [{'target': u'@', 'ttl': 3600,
                        u'priority': 10, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu',
                        u'mail_server': u'mail1.university.edu.'},
                       {'target': u'@', 'ttl': 3600,
                        u'priority': 20, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu',
                        u'mail_server': u'mail2.university.edu.'}])
    self.assertEquals(self.core_instance.ListRecords(record_type=u'txt'),
                      [{'target': u'@', 'ttl': 3600,
                        'record_type': u'txt', 'view_name': u'any',
                        'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu',
                        u'quoted_text': u'"Contact 1:  Stephen Harrell '
                                        u'(sharrell@university.edu)"'}])
    records_list = self.core_instance.ListRecords(record_type=u'a')
    self.assertTrue({'target': u'localhost', 'ttl': 3600,
                     'record_type': u'a', 'view_name': u'any',
                     'last_user': u'sharrell',
                     'zone_name': u'sub.university.edu',
                     u'assignment_ip': u'127.0.0.1'} in records_list)
    self.assertTrue({'target': u'desktop-1', 'ttl': 3600,
                     'record_type': u'a', 'view_name': u'any',
                     'last_user': u'sharrell',
                     'zone_name': u'sub.university.edu',
                     u'assignment_ip': u'192.168.1.100'} in records_list)
    self.assertTrue({'target': u'@', 'ttl': 3600,
                      'record_type': u'a', 'view_name': u'any',
                      'last_user': u'sharrell',
                      'zone_name': u'sub.university.edu',
                      u'assignment_ip': u'192.168.0.1'} in records_list)
    self.assertEquals(self.core_instance.ListRecords(record_type=u'cname'),
                      [{'target': u'www', 'ttl': 3600,
                        'record_type': u'cname', 'view_name': u'any',
                        'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu',
                        u'assignment_host': u'sub.university.edu.'}])
    self.assertEquals(self.core_instance.ListRecords(record_type=u'hinfo'), 
                      [{'target': u'desktop-1', 'ttl': 3600,
                        u'hardware': u'PC', 'record_type': u'hinfo',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'sub.university.edu', u'os': u'NT'}])

  def testMakeRecordsFromReverseZone(self):
    importer_instance = zone_importer_lib.ZoneImport(REVERSE_ZONE_FILE,
                                                            CONFIG_FILE,
                                                            u'sharrell')
    importer_instance.MakeRecordsFromZone()
    self.assertEquals(self.core_instance.ListReverseRangeZoneAssignments(),
                      {u'0.168.192.in-addr.arpa': u'192.168.0/24'})
    self.assertEqual(self.core_instance.ListRecords(record_type=u'ptr'),
                      [{'target': u'1', 'ttl': 86400,
                        'record_type': u'ptr', 'view_name': u'any',
                        'last_user': u'sharrell',
                        'zone_name': u'0.168.192.in-addr.arpa',
                        u'assignment_host': u'router.university.edu.'}, 
                       {'target': u'11', 'ttl': 86400,
                        'record_type': u'ptr', 'view_name': u'any',
                        'last_user': u'sharrell',
                        'zone_name': u'0.168.192.in-addr.arpa',
                        u'assignment_host': u'desktop-1.university.edu.'},
                       {'target': u'12', 'ttl': 86400,
                        'record_type': u'ptr', 'view_name': u'any',
                        'last_user': u'sharrell',
                        'zone_name': u'0.168.192.in-addr.arpa',
                        u'assignment_host': u'desktop-2.university.edu.'}])

if( __name__ == '__main__' ):
  unittest.main()

