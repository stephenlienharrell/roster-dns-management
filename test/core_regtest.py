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

"""Regression test for core.py

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.9'


import datetime
import unittest
import os

import roster_core
from roster_core import data_validation
from roster_core import core


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'


class TestCore(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    schema = roster_core.embedded_files.SCHEMA_FILE
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

  def testUserMakeRemoveListUpdate(self):
    self.assertEquals(self.core_instance.ListUsers(),
                      {u'shuey': 64, u'jcollins': 32, u'sharrell': 128})
    self.core_instance.MakeUser(u'ahoward', 64)
    self.assertEqual(self.core_instance.ListUsers(user_name=u'ahoward'),
                     {u'ahoward': 64})
    self.assertTrue(self.core_instance.UpdateUser(u'ahoward',
                                                  update_user_name=u'psmith',
                                                  update_access_level=128))
    self.assertFalse(self.core_instance.ListUsers(user_name=u'ahoward'))
    self.assertEqual(self.core_instance.ListUsers(user_name=u'psmith'),
                     {u'psmith': 128})
    self.assertTrue(self.core_instance.RemoveUser(u'psmith'))
    self.assertFalse(self.core_instance.ListUsers(user_name=u'psmith'))

  def testCredentialMakeRemoveListUpdate(self):
    current_time = datetime.datetime.now().replace(microsecond=0)
    self.core_instance._MakeCredential(u'f47ac10b-58cc-4372-a567-0e02b2c3d479',
                                       u'sharrell', last_used=current_time)
    self.assertEqual(self.core_instance._ListCredentials(),
                     {u'f47ac10b-58cc-4372-a567-0e02b2c3d479': {
                          u'last_used_timestamp': current_time,
                          u'user': u'sharrell', u'infinite_cred': 0}})
    self.core_instance._MakeCredential(u'd47ac10b-58cc-4372-a567-0e02b2c3d479',
                                       u'shuey', last_used=current_time)
    self.assertEqual(self.core_instance._ListCredentials(),
                     {u'd47ac10b-58cc-4372-a567-0e02b2c3d479': {
                          u'last_used_timestamp': current_time,
                          u'user': u'shuey', u'infinite_cred': 0},
                      u'f47ac10b-58cc-4372-a567-0e02b2c3d479': {
                          u'last_used_timestamp': current_time,
                      u'user': u'sharrell', u'infinite_cred': 0}})
    self.assertTrue(self.core_instance._RemoveCredential(
        user_name=u'shuey'))
    self.assertEqual(self.core_instance._ListCredentials(),
                     {u'f47ac10b-58cc-4372-a567-0e02b2c3d479': {
                          u'last_used_timestamp': current_time,
                          u'user': u'sharrell', u'infinite_cred': 0}})
    self.core_instance._UpdateCredential(search_user_name=u'sharrell',
                                         update_credential=u'547ac10b-58aa-4372'
                                                           '-a567-0e02b2c3d479')
    credential_list = self.core_instance._ListCredentials()
    self.assertEqual(credential_list['547ac10b-58aa-4372-a567-0e02b2c3d479'][
        'user'],u'sharrell')
    self.assertEqual(credential_list['547ac10b-58aa-4372-a567-0e02b2c3d479'][
        'infinite_cred'],0)

  def testGroupMakeRemoveListUpdate(self):
    self.assertEqual(set(self.core_instance.ListGroups()),
                     set([u'bio', u'eas', u'cs']))
    self.core_instance.MakeGroup(u'other')
    self.assertEqual(set(self.core_instance.ListGroups()),
                     set([u'bio', u'eas', u'cs', u'other']))
    self.assertTrue(self.core_instance.RemoveGroup(u'other'))
    self.assertEqual(set(self.core_instance.ListGroups()),
                     set([u'bio', u'eas', u'cs']))
    self.assertTrue(self.core_instance.UpdateGroup(u'eas', u'eaa'))
    self.assertEqual(set(self.core_instance.ListGroups()),
                     set([u'bio', u'eaa', u'cs']))

  def testServerSetMakeRemoveListUpdate(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSet(u'set2')
    self.core_instance.MakeDnsServerSet(u'set3')
    self.assertEqual(set(self.core_instance.ListDnsServerSets()),
                     set([u'set1', u'set2', u'set3']))
    self.assertTrue(self.core_instance.RemoveDnsServerSet(u'set3'))
    self.assertEqual(set(self.core_instance.ListDnsServerSets()),
                     set([u'set1', u'set2']))
    self.assertTrue(self.core_instance.UpdateDnsServerSet(u'set2', u'set3'))
    self.assertEqual(set(self.core_instance.ListDnsServerSets()),
                     set([u'set1', u'set3']))

  def testDnsServerMakeRemoveUpdate(self):
    self.core_instance.MakeDnsServer(u'dns1')
    self.core_instance.MakeDnsServer(u'dns2')
    self.core_instance.MakeDnsServer(u'dns3')
    self.assertEqual(set(self.core_instance.ListDnsServers()),
                     set([u'dns1', u'dns2', u'dns3']))
    self.assertTrue(self.core_instance.RemoveDnsServer(u'dns3'))
    self.assertEqual(set(self.core_instance.ListDnsServers()),
                     set([u'dns1', u'dns2']))
    self.assertTrue(self.core_instance.UpdateDnsServer(u'dns2', u'dns3'))
    self.assertEqual(set(self.core_instance.ListDnsServers()),
                     set([u'dns1', u'dns3']))

  def testServerSetAssignmentsMakeRemoveListUpdate(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSet(u'set2')
    self.core_instance.MakeDnsServer(u'dns1')
    self.core_instance.MakeDnsServer(u'dns2')
    self.core_instance.MakeDnsServer(u'dns3')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns2', u'set2')
    self.core_instance.MakeDnsServerSetAssignments(u'dns3', u'set2')
    self.assertEqual(self.core_instance.ListDnsServerSetAssignments(),
                     {u'set1': [u'dns1'], u'set2': [u'dns2', u'dns3']})
    self.assertTrue(self.core_instance.RemoveDnsServerSetAssignments(
        u'dns2', u'set2'))
    self.assertEqual(self.core_instance.ListDnsServerSetAssignments(),
                     {u'set1': [u'dns1'], u'set2': [u'dns3']})

  def testUserGroupAssignmentsMakeRemoveList(self):
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'sharrell': [u'cs']})
    self.assertEqual(self.core_instance.ListUserGroupAssignments(
      key_by_group=True), {u'bio': [u'shuey'],
                           u'cs': [u'sharrell', u'shuey']})
    self.core_instance.MakeGroup(u'other')
    self.core_instance.MakeUserGroupAssignment(u'sharrell', u'other')
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'sharrell': [u'cs',
                                                               u'other']})
    self.assertTrue(self.core_instance.RemoveUserGroupAssignment(u'sharrell',
                                                                 u'other'))
    self.assertEqual(self.core_instance.ListUserGroupAssignments(),
                     {u'shuey': [u'bio', u'cs'], u'sharrell': [u'cs']})

  def testDnsServerSetViewAssignmentsMakeRemoveList(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSet(u'set2')
    self.core_instance.MakeDnsServerSet(u'set3')
    self.core_instance.MakeView(u'view1', u'')
    self.core_instance.MakeView(u'view2', u'')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view1', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view2', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view1', u'set2')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view2', u'set3')
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(
      key_by_view=True), {u'view1': [u'set1', u'set2'],
                          u'view2': [u'set1', u'set3']})
    self.core_instance.MakeView(u'view3', u'')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view3', u'set1')
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
                     {u'set1': [u'view1', u'view2', u'view3'],
                      u'set2': [u'view1'], u'set3': [u'view2']})
    self.assertTrue(self.core_instance.RemoveDnsServerSetViewAssignments(
        u'view2', u'set1'))
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
                     {u'set1': [u'view1', u'view3'], u'set2': [u'view1'],
                      u'set3': [u'view2']})

  def testACLMakeRemoveListUpdate(self):
    self.assertEqual(self.core_instance.ListACLs(),
                     {u'any': [{'cidr_block': None, 'range_allowed': 1}]})
    self.core_instance.MakeACL(u'test_acl', u'192.168.0/24', 1)
    self.core_instance.MakeACL(u'test_acl', u'192.168.1/24', 1)
    self.core_instance.MakeACL(u'second_test_acl', u'192.168.0/24', 0)
    self.assertEqual(self.core_instance.ListACLs(),
        {u'any': [{'cidr_block': None, 'range_allowed': 1}],
         u'test_acl': [{'cidr_block': u'192.168.0/24', 'range_allowed': 1},
                       {'cidr_block': u'192.168.1/24', 'range_allowed': 1}],
         u'second_test_acl':
            [{'cidr_block': u'192.168.0/24', 'range_allowed': 0}]})

    self.assertTrue(self.core_instance.RemoveACL(u'second_test_acl'))
    self.assertFalse(self.core_instance.ListACLs(u'second_test_acl'))
    self.assertFalse(self.core_instance.RemoveACL(u'second_test_acl'))

    self.assertTrue(self.core_instance.UpdateACL(
                        search_acl_name=u'test_acl',
                        search_cidr_block=u'192.168.0/24',
                        update_range_allowed=0))
    self.assertEqual(self.core_instance.ListACLs(),
        {u'any': [{'cidr_block': None, 'range_allowed': 1}],
         u'test_acl': [{'cidr_block': u'192.168.0/24', 'range_allowed': 0},
                       {'cidr_block': u'192.168.1/24', 'range_allowed': 1}]})
    self.assertFalse(self.core_instance.UpdateACL(
                         search_acl_name=u'test_acl',
                         search_cidr_block=u'192.168.0/24',
                         update_range_allowed=0))

  def testViewMakeRemoveListUpdate(self):
    self.assertFalse(self.core_instance.ListViews())
    self.core_instance.MakeView(u'test_view', u'')
    self.core_instance.MakeView(u'second_test_view', u'')
    self.assertEquals(self.core_instance.ListViews(),
        {u'second_test_view': u'', u'test_view': u''})
    self.assertTrue(self.core_instance.RemoveView(u'second_test_view'))
    self.assertEquals(self.core_instance.ListViews(), {u'test_view': u''})
    self.assertFalse(self.core_instance.RemoveView(u'second_test_view'))

    self.assertTrue(self.core_instance.UpdateView(u'test_view',
                                                  u'not_test_view'))
    self.assertEquals(self.core_instance.ListViews(), {u'not_test_view': u''})
    self.assertFalse(self.core_instance.UpdateView(u'test_view',
                                                   u'not_test_view'))

  def testViewAssignmentsMakeRemoveList(self):
    self.assertFalse(self.core_instance.ListViewAssignments())
    self.core_instance.MakeView(u'test_view', u'')
    self.core_instance.MakeView(u'second_test_view', u'')
    self.core_instance.MakeViewAssignment(u'test_view', u'second_test_view')

    self.assertEqual(self.core_instance.ListViewAssignments(),
                     {u'second_test_view': [u'any', u'second_test_view'],
                      u'test_view':
                          [u'any', u'second_test_view', u'test_view']})

    self.assertTrue(self.core_instance.RemoveViewAssignment(
        u'test_view', u'second_test_view'))
    self.assertFalse(self.core_instance.ListViewAssignments(
        u'test_view', u'second_test_view'))
    self.assertFalse(self.core_instance.RemoveViewAssignment(
        u'test_view', u'second_test_view'))

  def testViewToACLAssignmentsMakeRemoveList(self):
    self.assertFalse(self.core_instance.ListViewToACLAssignments())
    self.core_instance.MakeView(u'test_view', u'')
    self.core_instance.MakeACL(u'test_acl', u'192.168.0/24', 1)
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'test_acl')
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'test_view', 'acl_name': u'test_acl'}])

    self.core_instance.RemoveView(u'test_view')
    self.assertFalse(self.core_instance.ListViewToACLAssignments())

    self.core_instance.MakeView(u'test_view', u'')
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'test_acl')
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'test_view', 'acl_name': u'test_acl'}])

    self.core_instance.RemoveACL(u'test_acl')
    self.assertFalse(self.core_instance.ListViewToACLAssignments())

    self.core_instance.MakeACL(u'test_acl', u'192.168.0/24', 1)
    self.core_instance.MakeViewToACLAssignments(u'test_view', u'test_acl')
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'test_view', 'acl_name': u'test_acl'}])
    self.core_instance.UpdateView(u'test_view', u'not_test_view')
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'not_test_view', 'acl_name': u'test_acl'}])
    self.core_instance.UpdateACL(search_acl_name=u'test_acl',
                                 update_acl_name=u'not_test_acl')
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'not_test_view',
                       'acl_name': u'not_test_acl'}])
    self.assertTrue(self.core_instance.RemoveViewToACLAssignments(
                    u'not_test_view', u'not_test_acl'))
    self.assertFalse(self.core_instance.ListViewToACLAssignments())
    self.assertFalse(self.core_instance.RemoveViewToACLAssignments(
                     u'not_test_view', u'not_test_acl'))

  def testZoneMakeRemoveListUpdate(self):
    self.core_instance.MakeView(u'test_view')
    self.assertFalse(self.core_instance.ListZones())
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': u'',
                        'zone_origin': u'test_zone.'}}})

    self.assertTrue(self.core_instance.RemoveZone(u'test_zone'))
    self.assertFalse(self.core_instance.ListZones())
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': u'',
                        'zone_origin': u'test_zone.'}}})
    self.assertTrue(self.core_instance.RemoveZone(u'test_zone',
                                                  view_name=u'test_view'))
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': 'test_zone.'}}})

    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertTrue(self.core_instance.UpdateZone(
                    u'test_zone', update_zone_name=u'not_test_zone'))

    self.assertEqual(self.core_instance.ListZones(), {u'not_test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': u'',
                        'zone_origin': u'test_zone.'}}})

    self.assertTrue(self.core_instance.UpdateZone(
                    u'not_test_zone', search_view_name=u'test_view',
                    update_zone_type=u'slave'))

    self.assertEqual(self.core_instance.ListZones(), {u'not_test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'slave', 'zone_options': u'',
                        'zone_origin': u'test_zone.'}}})

  def testReverseRangeZoneAssignmentMakeRemoveListUpdateRemove(self):
    self.core_instance.MakeZone(u'10.in-addr.arpa', u'master',
                                u'10.in-addr.arpa.')
    self.assertFalse(self.core_instance.ListReverseRangeZoneAssignments())
    self.core_instance.MakeReverseRangeZoneAssignment(u'10.in-addr.arpa',
                                                      u'10/8')
    self.assertEqual(self.core_instance.ListReverseRangeZoneAssignments(),
                     {'10.in-addr.arpa': '10/8'})
    self.assertTrue(self.core_instance.RemoveReverseRangeZoneAssignment(
        u'10.in-addr.arpa', u'10/8'))
    self.assertFalse(self.core_instance.ListReverseRangeZoneAssignments())

  def testForwardZonePermissionMakeListRemove(self):
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [
                       {'zone_name': u'bio.university.edu',
                        'access_right': u'rw'}],
                      u'cs': [
                       {'zone_name': u'cs.university.edu',
                        'access_right': u'rw'},
                       {'zone_name': u'eas.university.edu',
                        'access_right': u'r'}]})
    self.core_instance.MakeForwardZonePermission(u'eas.university.edu', u'bio',
                                                 u'r')
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [
                       {'zone_name': u'bio.university.edu',
                        'access_right': u'rw'},
                       {'zone_name': u'eas.university.edu',
                        'access_right': u'r'}],
                      u'cs': [
                       {'zone_name': u'cs.university.edu',
                        'access_right': u'rw'},
                       {'zone_name': u'eas.university.edu',
                        'access_right': u'r'}]})
    self.assertTrue(self.core_instance.RemoveForwardZonePermission(
        u'eas.university.edu', u'bio', u'r'))
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [
                       {'zone_name': u'bio.university.edu',\
                        'access_right': u'rw'}],
                      u'cs': [
                       {'zone_name': u'cs.university.edu',
                        'access_right': u'rw'},
                       {'zone_name': u'eas.university.edu',
                        'access_right': u'r'}]})

  def testReverseRangePermissionsListMakeRemove(self):
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio': [
                       {'zone_name': u'192.168.0.0/24', 'access_right': u'r'},
                       {'zone_name': u'192.168.1.0/24', 'access_right': u'rw'}],
                     u'cs': [
                       {'zone_name': u'192.168.0.0/24',
                        'access_right': u'rw'}]})
    self.core_instance.MakeReverseRangePermission(u'10/8', u'bio',
                                                  u'r')
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio': [
                       {'zone_name': u'192.168.0.0/24', 'access_right': u'r'},
                       {'zone_name': u'192.168.1.0/24', 'access_right': u'rw'},
                       {'zone_name': u'10/8', 'access_right': u'r'}],
                     u'cs': [
                       {'zone_name': u'192.168.0.0/24',
                        'access_right': u'rw'}]})
    self.assertTrue(self.core_instance.RemoveReverseRangePermission(
        u'10/8', u'bio', u'r'))
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio': [
                       {'zone_name': u'192.168.0.0/24', 'access_right': u'r'},
                       {'zone_name': u'192.168.1.0/24', 'access_right': u'rw'}],
                     u'cs': [
                       {'zone_name': u'192.168.0.0/24',
                        'access_right': u'rw'}]})

  def testRecordMakeRemoveListUpdate(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.assertFalse(self.core_instance.ListRecords())
    self.core_instance.MakeRecord(u'mx', u'university.edu.',
                                  u'university.edu',
                                  {u'priority': 10,
                                   u'mail_server': u'smtp.university.edu.'},
                                  ttl=10)
    self.core_instance.MakeRecord(u'mx', u'university.edu.',
                                  u'university.edu',
                                  {u'priority': 20,
                                   u'mail_server': u'smtp-2.university.edu.'},
                                  ttl=10)
    self.assertEquals(self.core_instance.ListRecords(),
                      [{'target': u'university.edu.', 'ttl': 10,
                        u'priority': 10, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp.university.edu.'},
                       {'target': u'university.edu.',
                        'ttl': 10, u'priority': 20, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp-2.university.edu.'}])
    self.core_instance.MakeRecord(u'soa', u'university.edu.',
                                  u'university.edu',
                                  {u'name_server': u'test.',
                                   u'admin_email': u'test.',
                                   u'serial_number': 2,
                                   u'refresh_seconds': 4,
                                   u'retry_seconds': 4,
                                   u'expiry_seconds': 4,
                                   u'minimum_seconds': 4},
                                  ttl=10, view_name=u'any')
    new_args_dict = self.core_instance.GetEmptyRecordArgsDict(u'mx')
    new_args_dict['priority'] = 30
    self.core_instance.UpdateRecord(u'mx', u'university.edu.',
                                    u'university.edu',
                                    {u'priority': 10,
                                     u'mail_server': u'smtp.university.edu.'},
                                    u'any', update_target=u'newtarget.edu.',
                                    update_record_args_dict=new_args_dict)
    self.assertEqual(self.core_instance.ListRecords(record_type=u'mx'),
                      [{'target': u'newtarget.edu.', 'ttl': 10,
                        u'priority': 30, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp.university.edu.'},
                       {'target': u'university.edu.',
                        'ttl': 10, u'priority': 20, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp-2.university.edu.'}])
    args_dict = self.core_instance.GetEmptyRecordArgsDict(u'mx')
    args_dict['priority'] = 30
    self.assertEqual(self.core_instance.ListRecords(
        record_type=u'mx', record_args_dict=args_dict),
        [{'target': u'newtarget.edu.', 'ttl': 10,
          'priority': 30, 'record_type': u'mx',
          'view_name': u'any', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          'mail_server': u'smtp.university.edu.'}])
    self.core_instance.RemoveRecord(u'mx', u'university.edu.',
                                    u'university.edu',
                                    {u'priority': 20,
                                     u'mail_server': u'smtp-2.university.edu.'},
                                     u'any')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'mx'),
                     [{'target': u'newtarget.edu.', 'ttl': 10,
                       u'priority': 30, 'record_type': u'mx',
                       'view_name': u'any', 'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                       u'mail_server': u'smtp.university.edu.'}])
    self.core_instance.MakeReservedWord(u'reserved')
    temp_core_instance = roster_core.Core(u'sharrell', self.config_instance)
    self.assertRaises(data_validation.ReservedWordError,
        temp_core_instance.MakeRecord,
        u'a', u'thisisreserved5', u'university.edu',
        {u'assignment_ip': u'192.168.0.55'}, ttl=10)

    self.core_instance.MakeRecord(u'a', u'computer5',
                                  u'university.edu',
                                  {u'assignment_ip': u'192.168.0.55'},
                                  ttl=10)
    self.assertEqual(self.core_instance.ListRecords(record_type=u'a'),
                     [{'target': u'computer5', 'ttl': 10,
                      'record_type': u'a', 'view_name': u'any',
                      'last_user': u'sharrell', 'zone_name': u'university.edu',
                      u'assignment_ip': u'192.168.0.55'}])
    self.assertRaises(core.RecordError, self.core_instance.MakeRecord,
                      u'cname', u'computer5', u'university.edu',
                      {u'assignment_host': u'c5.university.edu.'}, ttl=10)
    self.assertEqual(self.core_instance.ListRecords(record_type=u'cname'),[])
    self.core_instance.MakeRecord(u'cname', u'c6',
                                  u'university.edu',
                                  {u'assignment_host':
                                   u'computer6.university.edu.'},
                                  ttl=10)
    self.assertRaises(core.RecordError, self.core_instance.UpdateRecord,
                      u'cname', 'c6', 'university.edu',
                      {u'assignment_host': None}, update_target=u'computer5')

  def testSOA(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.core_instance.MakeRecord(u'soa', u'university.edu.',
                                  u'university.edu',
                                  {u'name_server': u'test.',
                                   u'admin_email': u'test.',
                                   u'serial_number': 4294967294,
                                   u'refresh_seconds': 4,
                                   u'retry_seconds': 4,
                                   u'expiry_seconds': 4,
                                   u'minimum_seconds': 4},
                                  ttl=10, view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'soa'),
                     [{'zone_name': u'university.edu', u'refresh_seconds': 4,
                       'target': u'university.edu.', u'name_server': u'test.',
                       'record_type': u'soa', 'last_user': u'sharrell',
                       u'minimum_seconds': 4, u'retry_seconds': 4,
                       'view_name': u'test_view', 'ttl': 10,
                       u'serial_number': 4294967294, u'admin_email': u'test.',
                       u'expiry_seconds': 4}])
    self.core_instance.UpdateRecord(u'soa', u'university.edu.',
                                    u'university.edu',
                                    {u'name_server': u'test.',
                                     u'admin_email': u'test.',
                                     u'serial_number': 4294967294,
                                     u'refresh_seconds': 4,
                                     u'retry_seconds': 4,
                                     u'expiry_seconds': 4,
                                     u'minimum_seconds': 4}, u'test_view',
                                    update_target=u'newtarget.')
    self.assertEqual(self.core_instance.ListRecords(),
                     [{u'serial_number': 4294967295, u'refresh_seconds': 4,
                       'target': u'newtarget.', u'name_server': u'test.',
                       u'retry_seconds': 4, 'ttl': 10, u'minimum_seconds': 4,
                       'record_type': u'soa', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'university.edu',
                       u'admin_email': u'test.', u'expiry_seconds': 4}])
    self.core_instance.db_instance.StartTransaction()
    self.core_instance._IncrementSoa(u'test_view', u'university.edu')
    self.core_instance.db_instance.EndTransaction()
    self.assertEqual(self.core_instance.ListRecords(),
                     [{u'serial_number': 1, u'refresh_seconds': 4,
                       'target': u'newtarget.', u'name_server': u'test.',
                       u'retry_seconds': 4, 'ttl': 10, u'minimum_seconds': 4,
                       'record_type': u'soa', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'university.edu',
                       u'admin_email': u'test.', u'expiry_seconds': 4}])

  def testListRecordArgumentDefinitions(self):
    self.assertEqual(self.core_instance.ListRecordArgumentDefinitions(),
        {u'a': [{'argument_name': u'assignment_ip',
                 'argument_order': 0}],
         u'soa': [{'argument_name': u'name_server',
                   'argument_order': 0},
                  {'argument_name': u'admin_email',
                   'argument_order': 1},
                  {'argument_name': u'serial_number',
                   'argument_order': 2},
                  {'argument_name': u'refresh_seconds',
                   'argument_order': 3},
                  {'argument_name': u'retry_seconds',
                   'argument_order': 4},
                  {'argument_name': u'expiry_seconds',
                   'argument_order': 5},
                  {'argument_name': u'minimum_seconds',
                   'argument_order': 6}],
         u'ns': [{'argument_name': u'name_server',
                  'argument_order': 0}],
         u'ptr': [{'argument_name': u'assignment_host',
                   'argument_order': 0}],
         u'aaaa': [{'argument_name': u'assignment_ip',
                    'argument_order': 0}],
         u'cname': [{'argument_name': u'assignment_host',
                     'argument_order': 0}],
         u'srv': [{'argument_name': u'priority',
                   'argument_order': 0},
                  {'argument_name': u'weight',
                   'argument_order': 1},
                  {'argument_name': u'port',
                   'argument_order': 2},
                  {'argument_name': u'assignment_host',
                   'argument_order': 3}],
         u'hinfo': [{'argument_name': u'hardware',
                     'argument_order': 0},
                    {'argument_name': u'os',
                     'argument_order': 1}],
         u'txt': [{'argument_name': u'quoted_text',
                   'argument_order': 0}],
         u'mx': [{'argument_name': u'priority',
                  'argument_order': 0},
                 {'argument_name': u'mail_server',
                  'argument_order': 1}]})

  def testListZoneTypes(self):
    self.assertEqual(set(self.core_instance.ListZoneTypes()), set([u'forward',
                                                                   u'master',
                                                                   u'slave']))
    self.assertTrue(self.core_instance.RemoveZoneType(u'forward'))
    self.assertEqual(set(self.core_instance.ListZoneTypes()), set([u'master',
                                                                   u'slave']))
    self.core_instance.MakeZoneType(u'newtype')
    self.assertEqual(set(self.core_instance.ListZoneTypes()), set([u'master',
                                                                   u'slave',
                                                                   u'newtype']))

  def testListMakeNamedConfGlobalOptions(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test')
    named_conf_options = self.core_instance.ListNamedConfGlobalOptions()
    self.assertEqual(len(named_conf_options), 1)
    self.assertEqual(named_conf_options[0]['options'], u'test')
    self.assertEqual(named_conf_options[0]['dns_server_set_name'], u'set1')
    self.assertEqual(named_conf_options[0]['id'], 1)

  def testReservedWordMakeRemoveList(self):
    self.core_instance.MakeReservedWord(u'word1')
    self.assertEqual(self.core_instance.ListReservedWords(),
                     [u'damn', u'word1'])
    self.assertTrue(self.core_instance.RemoveReservedWord(u'damn'))
    self.assertEqual(self.core_instance.ListReservedWords(),
                     [u'word1'])


if( __name__ == '__main__' ):
    unittest.main()
