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

"""Regression test for core_helper.py

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import datetime
import time
import unittest
import os

import roster_core


CONFIG_FILE = '%s/.rosterrc' % os.path.expanduser('~') # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'


class TestCoreHelpers(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    schema = open(SCHEMA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.CommitTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.CommitTransaction()
    db_instance.close()

    self.unittest_timestamp = datetime.datetime.now().replace(microsecond=0)
    self.core_instance = roster_core.Core(u'sharrell', self.config_instance,
        unittest_timestamp=self.unittest_timestamp)
    self.core_helper_instance = roster_core.CoreHelpers(
        self.core_instance)

    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.MakeView(u'test_view3')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'university.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'university.edu.',
                                view_name=u'test_view3')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view2')
    self.core_instance.MakeZone(u'ipv6zone', u'master',
                                u'ipv6.net.', view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host2', u'ipv6zone', {u'assignment_ip':
            u'4321:0000:0001:0002:0003:0004:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host1', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.1'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host2', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.11'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.5'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host4', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.10'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host5', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.17'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host6', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.8'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'8',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host6.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'11',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host2.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'5',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host3.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'10',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host4.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'7',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host5.university.edu.'},
                                  view_name=u'test_view2')

  def testListRecordByIPAddress(self):
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.1.0/24')
    self.assertEqual(self.core_helper_instance.ListRecordsByCIDRBlock(
      u'192.168.1.17', view_name=u'test_view3'),
      {u'test_view3': {u'192.168.1.17':
          [{u'forward': True, u'host': u'host5.university.edu',
            u'zone_origin': u'university.edu.', u'zone': u'forward_zone'}]}})
    self.assertEqual(self.core_helper_instance.ListRecordsByCIDRBlock(
        u'192.168.1.7', view_name=u'test_view2'),
        {u'test_view2': {u'192.168.1.7':
            [{u'forward': False, u'host': u'host5.university.edu',
              u'zone_origin': u'1.168.192.in-addr.arpa.',
              u'zone': u'reverse_zone'}]}})
    self.assertEqual(self.core_helper_instance.ListRecordsByCIDRBlock(
      u'192.168.1.8', view_name=u'test_view'),
      {u'test_view': {u'192.168.1.8':
          [{u'forward': False, u'host': u'host6.university.edu',
            u'zone_origin': u'1.168.192.in-addr.arpa.',
            u'zone': u'reverse_zone'},
           {u'forward': True, u'host': u'host6.university.edu',
            u'zone_origin': u'university.edu.', u'zone': u'forward_zone'}]}})
    self.assertEqual(self.core_helper_instance.ListRecordsByCIDRBlock(
      u'4321:0000:0001:0002:0003:0004:0567:89ab', view_name=u'test_view'),
      {u'test_view': {u'4321:0000:0001:0002:0003:0004:0567:89ab':
          [{u'forward': True, u'host': u'host2.ipv6.net',
            u'zone_origin': u'ipv6.net.', u'zone': u'ipv6zone'}]}})

  def testListRecordsByCIDRBlock(self):
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.1.0/24')

    self.assertEqual(self.core_helper_instance.ListRecordsByCIDRBlock(
        u'192.168.1.4/30'),
        {u'test_view2':
            {u'192.168.1.7':
                 [{u'forward': False, u'host': u'host5.university.edu',
                   u'zone_origin': u'1.168.192.in-addr.arpa.',
                   u'zone': u'reverse_zone'}],
             u'192.168.1.5':
                 [{u'forward': False, u'host': u'host3.university.edu',
                   u'zone_origin': u'1.168.192.in-addr.arpa.',
                   u'zone': u'reverse_zone'}]},
         u'any':
            {u'192.168.1.5': [{u'forward': True,
                u'host': u'host3.university.edu',
                u'zone_origin': u'university.edu.',
                u'zone': u'forward_zone'}]}})

  def testUnReverseIP(self):
    self.assertEqual(self.core_helper_instance.UnReverseIP(
        'b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1.0.0.0.0.0.0.0.1.2.3.4.'
        'ip6.arpa.'), '4321:0000:0001:0002:0003:0004:0567:89ab')
    self.assertEqual(self.core_helper_instance.UnReverseIP(
        '4.1.168.192.in-addr.arpa.'), '192.168.1.4')

  def testListAccessRights(self):
    self.assertEqual(self.core_helper_instance.ListAccessRights(), ['rw', 'r'])

  def testRevertNamedConfig(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test_options2')
    self.assertEqual(self.core_instance.ListNamedConfGlobalOptions(),
                     [{'timestamp': self.unittest_timestamp,
                       'options': u'test_options', 'id': 1,
                       'dns_server_set_name': u'set1'},
                      {'timestamp': self.unittest_timestamp,
                       'options': u'test_options2', 'id': 2,
                       'dns_server_set_name': u'set1'}])
    self.core_helper_instance.RevertNamedConfig(u'set1', 1)
    self.assertEqual(self.core_instance.ListNamedConfGlobalOptions(),
                     [{'timestamp': self.unittest_timestamp,
                       'options': u'test_options', 'id': 1,
                       'dns_server_set_name': u'set1'},
                      {'timestamp': self.unittest_timestamp,
                       'options': u'test_options2', 'id': 2,
                       'dns_server_set_name': u'set1'},
                      {'timestamp': self.unittest_timestamp,
                       'options': u'test_options', 'id': 3,
                       'dns_server_set_name': u'set1'}])
    config_dict = self.core_instance.db_instance.GetEmptyRowDict(
        'named_conf_global_options')
    config_dict['named_conf_global_options_id'] = 3
    update_config_dict = self.core_instance.db_instance.GetEmptyRowDict(
        'named_conf_global_options')
    time_difference = self.unittest_timestamp + datetime.timedelta(seconds=1)
    update_config_dict['options_created'] = time_difference
    self.core_instance.db_instance.StartTransaction()
    try:
      self.core_instance.db_instance.UpdateRow('named_conf_global_options',
                                               config_dict, update_config_dict)
    except:
      self.core_instance.db_instance.RollbackTransaction()
      raise
    self.core_instance.db_instance.CommitTransaction()
    time.sleep(2)
    self.assertEqual(self.core_helper_instance.ListLatestNamedConfig(u'set1'),
                     {'timestamp': time_difference, 'options': u'test_options',
                      'id': 3, 'dns_server_set_name': u'set1'})

  def testListZoneByIPAddress(self):
    self.core_instance.MakeReverseRangeZoneAssignment(u'forward_zone',
                                                      u'192.168.1.0/24')
    self.assertEqual(
        self.core_helper_instance.ListZoneByIPAddress(u'192.168.1.1'),
        u'forward_zone')

  def testRemoveCNamesByAssignmentHost(self):
    self.assertEqual(self.core_instance.ListRecords(record_type=u'cname'), [])
    self.core_instance.MakeRecord(
        u'cname', u'cname_host2', u'forward_zone',
        {u'assignment_host': u'host2.university.edu.'},
        view_name=u'test_view3')
    self.core_instance.MakeRecord(
        u'cname', u'cname2_host2', u'forward_zone',
        {u'assignment_host': u'host2.university.edu.'},
        view_name=u'test_view3')
    self.core_instance.MakeRecord(
        u'cname', u'cname3_host2', u'forward_zone',
        {u'assignment_host': u'host1.university.edu.'},
        view_name=u'test_view3')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'cname'),
                     [{'target': u'cname_host2', 'ttl': 3600,
                       'record_type': u'cname', 'view_name': u'test_view3',
                       'last_user': u'sharrell', 'zone_name': u'forward_zone',
                       u'assignment_host': u'host2.university.edu.'},
                      {'target': u'cname2_host2', 'ttl': 3600,
                       'record_type': u'cname', 'view_name': u'test_view3',
                       'last_user': u'sharrell', 'zone_name': u'forward_zone',
                       u'assignment_host': u'host2.university.edu.'},
                      {'target': u'cname3_host2', 'ttl': 3600,
                       'record_type': u'cname', 'view_name': u'test_view3',
                       'last_user': u'sharrell', 'zone_name': u'forward_zone',
                       u'assignment_host': u'host1.university.edu.'}])
    self.core_helper_instance.RemoveCNamesByAssignmentHost(
        u'host2.university.edu.', u'test_view3', u'forward_zone')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'cname'),
                     [{'target': u'cname3_host2', 'ttl': 3600,
                       'record_type': u'cname', 'view_name': u'test_view3',
                       'last_user': u'sharrell', 'zone_name': u'forward_zone',
                       u'assignment_host': u'host1.university.edu.'}])

  def testProcessRecordsBatch(self):
    self.assertEqual(
        self.core_instance.ListRecords(record_type=u'a', target=u'host1'),
        [{'target': u'host1', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.0.1'}])
    self.assertEqual(
        self.core_helper_instance.ProcessRecordsBatch(delete_records=[{
            'record_type': u'a', 'record_target': u'host1',
            'record_zone_name': u'forward_zone', u'view_name': u'test_view',
            'record_arguments': {u'assignment_ip': u'192.168.0.1'}}],
            add_records=[{'record_type': u'a', 'record_target': u'blah',
                          'record_zone_name': u'forward_zone',
                          u'view_name': u'test_view', 'record_arguments':
                              {u'assignment_ip': u'192.168.0.88'}}]), 2)
    self.assertEqual(
        self.core_instance.ListRecords(record_type=u'a', target=u'host1'),
        [])
    self.assertEqual(
        self.core_instance.ListRecords(record_type=u'a', target=u'blah'),
        [{'target': u'blah', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.0.88'}])

if( __name__ == '__main__' ):
      unittest.main()
