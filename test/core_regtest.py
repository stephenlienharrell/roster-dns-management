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
__version__ = '#TRUNK#'


import cPickle
import datetime
import MySQLdb
import time
import unittest
import os

import roster_core
from roster_core import data_validation
from roster_core import core
from roster_core import errors


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'


class TestCore(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

  def testUserMakeRemoveListUpdate(self):
    self.assertEquals(self.core_instance.ListUsers(),
                      {u'shuey': 64, u'jcollins': 32, 'tree_export_user': 0,
                       u'sharrell': 128})
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

  def testMakeDuplicateDnsServerSetAssignmentError(self):
    self.core_instance.MakeDnsServer(u'myserver_name', u'some_ssh_name', 
        u'/some_bind_dir/', u'/some_test_dir/')
    self.core_instance.MakeDnsServerSet(u'some_set1')
    self.core_instance.MakeDnsServerSet(u'some_set2')

    self.core_instance.MakeDnsServerSetAssignments(u'myserver_name', 
        u'some_set1')
    self.assertRaises(MySQLdb.IntegrityError, 
        self.core_instance.MakeDnsServerSetAssignments, 
        u'myserver_name', 
        u'some_set2')

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
    self.assertRaises(errors.CoreError, self.core_instance._RemoveCredential)

    credential_list = self.core_instance.ListCredentials()
    self.assertEqual(len(credential_list), 1)
    self.assertEqual(credential_list['sharrell']['credential'],
                     '547ac10b-58aa-4372-a567-0e02b2c3d479')
    self.core_instance.MakeInfiniteCredential(u'shuey')
    credential_list = self.core_instance.ListCredentials()
    self.assertEqual(len(credential_list), 2)
    self.core_instance.RemoveCredential(user_name=u'shuey')
    credential_list = self.core_instance.ListCredentials()
    self.assertEqual(len(credential_list), 1)
    self.core_instance.RemoveCredential(
        credential=u'547ac10b-58aa-4372-a567-0e02b2c3d479')
    credential_list = self.core_instance.ListCredentials()
    self.assertFalse(credential_list)

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
    self.assertEqual(set(self.core_instance.ListDnsServerSets(u'set3')),
                     set([u'set3']))
    self.assertTrue(self.core_instance.RemoveDnsServerSet(u'set3'))
    self.assertEqual(set(self.core_instance.ListDnsServerSets()),
                     set([u'set1', u'set2']))
    self.assertTrue(self.core_instance.UpdateDnsServerSet(u'set2', u'set3'))
    self.assertEqual(set(self.core_instance.ListDnsServerSets()),
                     set([u'set1', u'set3']))

  def testDnsServerMakeRemoveUpdate(self):
    self.core_instance.MakeDnsServer(u'dns1', u'user', 
                                     u'/etc/bind/', u'/etc/bind/test/')
    self.core_instance.MakeDnsServer(u'dns2', u'user', 
                                     u'/etc/bind/', u'/etc/bind/test/')
    self.core_instance.MakeDnsServer(u'dns3', u'user', 
                                     u'/etc/dns/bind/', u'/etc/dns/bind/test/')
    self.assertEqual(self.core_instance.ListDnsServers(),
                     {u'dns1': 
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/bind/test/',
                          'bind_dir': u'/etc/bind/'},
                      u'dns2': 
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/bind/test/',
                          'bind_dir': u'/etc/bind/'},
                      u'dns3':
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/dns/bind/test/',
                          'bind_dir': u'/etc/dns/bind/'}})
    self.assertEqual(self.core_instance.ListDnsServers(u'dns3'),
                     {u'dns3': 
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/dns/bind/test/',
                          'bind_dir': u'/etc/dns/bind/'}
                     })
    self.assertTrue(self.core_instance.RemoveDnsServer(u'dns3'))
    self.assertEqual(self.core_instance.ListDnsServers(),
                     {u'dns1': 
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/bind/test/',
                          'bind_dir': u'/etc/bind/'},
                      u'dns2': 
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/bind/test/',
                          'bind_dir': u'/etc/bind/'}})
    self.assertTrue(self.core_instance.UpdateDnsServer(u'dns2', u'dns3',
        u'user', u'/etc/bind/', u'/etc/bind/test/'))
    self.assertEqual(self.core_instance.ListDnsServers(),
                     {u'dns1': 
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/bind/test/',
                          'bind_dir': u'/etc/bind/'},
                      u'dns3': 
                         {'ssh_username': u'user',
                          'test_dir': u'/etc/bind/test/',
                          'bind_dir': u'/etc/bind/'}})

  def testServerSetAssignmentsMakeRemoveListUpdate(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSet(u'set2')
    self.core_instance.MakeDnsServer(u'dns1', u'user', 
                                     u'/etc/bind/', u'/etc/bind/test/')
    self.core_instance.MakeDnsServer(u'dns2', u'user', 
                                     u'/etc/bind/', u'/etc/bind/test/')
    self.core_instance.MakeDnsServer(u'dns3', u'user', 
                                     u'/etc/dns/bind/', u'/etc/dns/bind/test/')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns2', u'set2')
    self.core_instance.MakeDnsServerSetAssignments(u'dns3', u'set2')
    self.assertEqual(self.core_instance.ListDnsServerSetAssignments(),
                     {u'set1': [u'dns1'], u'set2': [u'dns2', u'dns3']})
    self.assertEqual(self.core_instance.ListDnsServerSetAssignments(
        dns_server_set_name=u'set2'),
        {u'set2': [u'dns2', u'dns3']})
    self.assertEqual(self.core_instance.ListDnsServerSetAssignments(
        dns_server_set_name=u'set2', dns_server_name=u'dns2'),
        {u'set2': [u'dns2']})
    self.assertTrue(self.core_instance.RemoveDnsServerSetAssignments(
        u'dns2', u'set2'))
    self.assertEqual(self.core_instance.ListDnsServerSetAssignments(),
                     {u'set1': [u'dns1'], u'set2': [u'dns3']})
    self.assertRaises(errors.InvalidInputError,
        self.core_instance.MakeDnsServerSetAssignments, u'dns1', u'set1')

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
    self.core_instance.MakeView(u'view1')
    self.core_instance.MakeView(u'view2')
    self.core_instance.MakeView(u'view3')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view1', 1, u'set1', 
        u'some_view_option True;')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view1', 1, u'set2',
        u'some_other_view_option True;')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view2', 2, u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'view2', 2, u'set3')

    # try duplicate view orders on the same set
    self.assertRaises(MySQLdb.IntegrityError,
                      self.core_instance.MakeDnsServerSetViewAssignments,
                      u'view3', 1, u'set1')

    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(
      key_by_view=True), {u'view1': [(u'set1', 1, u'some_view_option True;'), 
                                     (u'set2', 1, u'some_other_view_option True;')],
                          u'view2': [(u'set1', 2, u''), (u'set3', 2, u'')]})
    self.core_instance.MakeDnsServerSetViewAssignments(u'view3', 3, u'set1')
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
           {u'set1': [(u'view1', 1, u'some_view_option True;'), 
                      (u'view2', 2, u''), 
                      (u'view3', 3, u'')],
            u'set2': [(u'view1', 1, u'some_other_view_option True;')], 
            u'set3': [(u'view2', 2, u'')]})
    self.assertTrue(self.core_instance.RemoveDnsServerSetViewAssignments(
        u'view2', u'set1'))
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
                     {u'set1': [(u'view1', 1, u'some_view_option True;'), 
                                (u'view3', 3, u'')], 
                      u'set2': [(u'view1', 1, u'some_other_view_option True;')],
                      u'set3': [(u'view2', 2, u'')]})

  def testACLMakeRemoveListUpdate(self):
    self.assertEqual(self.core_instance.ListACLs(),
                     {u'any': [{'cidr_block': None}]})
    self.core_instance.MakeACL(u'test_acl', u'192.168.0/24')
    self.core_instance.MakeACL(u'test_acl', u'192.168.1/24')
    self.core_instance.MakeACL(u'second_test_acl', u'192.168.0/24')
    self.assertEqual(self.core_instance.ListACLs(),
        {u'any': [{'cidr_block': None}],
         u'test_acl': [{'cidr_block': u'192.168.0/24'},
                       {'cidr_block': u'192.168.1/24'}],
         u'second_test_acl':
            [{'cidr_block': u'192.168.0/24'}]})

    self.assertTrue(self.core_instance.RemoveACL(u'second_test_acl'))
    self.assertFalse(self.core_instance.ListACLs(u'second_test_acl'))
    self.assertFalse(self.core_instance.RemoveACL(u'second_test_acl'))

    self.assertTrue(self.core_instance.RemoveCIDRBlockFromACL(
                    u'test_acl', u'192.168.0/24'))
    self.core_instance.MakeACL(u'test_acl', u'192.168.0/24')
    self.assertEqual(self.core_instance.ListACLs(),
        {u'any': [{'cidr_block': None}],
         u'test_acl': [{'cidr_block': u'192.168.0/24'},
                       {'cidr_block': u'192.168.1/24'}]})
    self.assertFalse(self.core_instance.RemoveCIDRBlockFromACL(u'test_acl',
                     u'192.168.3/24'))

  def testViewMakeRemoveListUpdate(self):
    self.assertFalse(self.core_instance.ListViews())
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeView(u'second_test_view')
    self.assertEquals(self.core_instance.ListViews(),
        [u'second_test_view', u'test_view'])
    self.assertTrue(self.core_instance.RemoveView(u'second_test_view'))
    self.assertEquals(self.core_instance.ListViews(), [u'test_view'])
    self.assertFalse(self.core_instance.RemoveView(u'second_test_view'))
    self.assertTrue(self.core_instance.UpdateView(u'test_view',
                                                  u'not_test_view'))
    self.assertEquals(self.core_instance.ListViews(), [u'not_test_view'])
    self.assertFalse(self.core_instance.UpdateView(u'test_view',
                                                   u'not_test_view'))

  def testUpdateDnsServerSetAssignments(self):
    self.assertEqual(self.core_instance.ListViewAssignments(), {})
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeDnsServer(u'server_name', u'ssh_username',
        u'/etc/bind_dir/', u'/etc/test_dir/')
    self.core_instance.MakeDnsServerSet(u'set_name')
    self.core_instance.MakeDnsServerSetAssignments(u'server_name', u'set_name')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set_name',
        view_options='recursion no;')

    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
        {u'set_name': [(u'test_view', 1, u'recursion no;')]})

    #updating nothing
    self.core_instance.UpdateDnsServerSetViewAssignments(u'set_name', u'test_view')
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
        {u'set_name': [(u'test_view', 1, u'recursion no;')]})

    #updating view order
    self.core_instance.UpdateDnsServerSetViewAssignments(u'set_name', u'test_view', 
        update_view_order=2)
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
        {u'set_name': [(u'test_view', 2, u'recursion no;')]})
  
    #updating view options
    self.core_instance.UpdateDnsServerSetViewAssignments(u'set_name', u'test_view',
        update_view_options=u'recursion yes;')
    self.assertEqual(self.core_instance.ListDnsServerSetViewAssignments(),
        {u'set_name': [(u'test_view', 2, u'recursion yes;')]})

  #This tests what happens a user attempts to create a record in a zone-view
  #combo that does not exist.
  def testZoneViewAssignmentsError(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeView(u'troll_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
        view_name=u'test_view')

    #The reason why we try this twice, (first here, and after we create an SOA)
    #is because earlier in our testing, we encountered different errors
    #depending on whether or not a record was present in the zone. To make sure
    #that doesn't happen again, we assertRaises twice.
    self.assertRaises(errors.UnexpectedDataError, self.core_instance.MakeRecord,
        u'a', u'www2', u'test_zone', {u'assignment_ip': u'192.168.0.2'}, 
        view_name=u'troll_view')

    soa_dict =  self.core_instance.GetEmptyRecordArgsDict(u'soa')

    #This stuff doesn't matter really for the test, 
    #just has to pass the Roster checks.
    soa_dict['refresh_seconds'] = 1
    soa_dict['expiry_seconds'] = 2
    soa_dict['minimum_seconds'] = 3
    soa_dict['retry_seconds'] = 4
    soa_dict['serial_number'] = 5
    soa_dict['name_server'] = '.'
    soa_dict['admin_email'] = '.'

    self.core_instance.MakeRecord(u'soa', u'@', u'test_zone', soa_dict, 
        view_name=u'test_view')

    self.assertRaises(errors.UnexpectedDataError, self.core_instance.MakeRecord,
        u'a', u'www2', u'test_zone', {u'assignment_ip': u'192.168.0.2'}, 
        view_name=u'troll_view')

  def testViewAssignmentsMakeRemoveList(self):
    self.assertFalse(self.core_instance.ListViewAssignments())
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeView(u'second_test_view')
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
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeACL(u'test_acl', u'192.168.0/24')
    self.core_instance.MakeDnsServerSet(u'test_dns_server_set')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view',
        1, u'test_dns_server_set')
    self.core_instance.MakeViewToACLAssignments(u'test_view',
        u'test_dns_server_set', u'test_acl', 1)
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'test_view', 'acl_range_allowed': 1,
                       'acl_name': u'test_acl', 'dns_server_set_name': u'test_dns_server_set'}])

    self.core_instance.RemoveView(u'test_view')
    self.assertFalse(self.core_instance.ListViewToACLAssignments())

    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view',
        1, u'test_dns_server_set')
    self.core_instance.MakeViewToACLAssignments(u'test_view',
        u'test_dns_server_set', u'test_acl', 1)
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'test_view', 'acl_range_allowed': 1,
                       'acl_name': u'test_acl', 'dns_server_set_name': u'test_dns_server_set'}])

    self.core_instance.RemoveACL(u'test_acl')
    self.assertFalse(self.core_instance.ListViewToACLAssignments())

    self.core_instance.MakeACL(u'test_acl', u'192.168.0/24')
    self.core_instance.MakeViewToACLAssignments(u'test_view',
        u'test_dns_server_set', u'test_acl', 1)
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'test_view', 'acl_range_allowed': 1,
                       'acl_name': u'test_acl', 'dns_server_set_name': u'test_dns_server_set'}])
    self.core_instance.UpdateView(u'test_view', u'not_test_view')
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'not_test_view', 'acl_range_allowed': 1,
                       'acl_name': u'test_acl', 'dns_server_set_name': u'test_dns_server_set'}])
    self.assertEqual(self.core_instance.ListViewToACLAssignments(),
                     [{'view_name': u'not_test_view', 'acl_range_allowed': 1,
                       'acl_name': u'test_acl', 'dns_server_set_name': u'test_dns_server_set'}])
    self.assertTrue(self.core_instance.RemoveViewToACLAssignments(
                    u'not_test_view', u'test_dns_server_set', u'test_acl', 1))
    self.assertFalse(self.core_instance.ListViewToACLAssignments())
    self.assertFalse(self.core_instance.RemoveViewToACLAssignments(
                     u'not_test_view', u'test_dns_server_set', u'test_acl', 1))

  def testZoneMakeRemoveListUpdate(self):
    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')
    self.core_instance.MakeView(u'test_view')
    self.assertFalse(self.core_instance.ListZones())
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': '',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': '',
                        'zone_origin': u'test_zone.'}}})

    self.assertTrue(self.core_instance.RemoveZone(u'test_zone'))
    self.assertFalse(self.core_instance.ListZones())
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': '',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': '',
                        'zone_origin': u'test_zone.'}}})
    self.assertTrue(self.core_instance.RemoveZone(u'test_zone',
                                                  view_name=u'test_view'))
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': '',
                  'zone_origin': 'test_zone.'}}})

    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertTrue(self.core_instance.UpdateZone(
                    u'test_zone', update_zone_name=u'not_test_zone'))

    self.assertEqual(self.core_instance.ListZones(), {u'not_test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': '',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': '',
                        'zone_origin': u'test_zone.'}}})

    self.assertEqual(self.core_instance.ListZones(), {u'not_test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': '',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': '',
                        'zone_origin': u'test_zone.'}}})
    self.assertRaises(errors.CoreError, self.core_instance.MakeZone,
                      u'test_zone', u'wrongtype', u'test_zone.')

  def testUpdateGroupForwardPermission(self):
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
        {u'cs': [{'zone_name': u'cs.university.edu', 'group_permission':
                    [u'a', u'aaaa', u'cname', u'ns', u'soa']},
                 {'zone_name': u'eas.university.edu', 'group_permission':
                    [u'a', u'aaaa', u'cname']}],
        u'bio': [{'zone_name': u'bio.university.edu', 'group_permission':
                    [u'a', u'aaaa']}]})

    #adding permissions
    self.core_instance.UpdateGroupForwardPermission(u'cs.university.edu', u'cs',
                               [u'a', u'aaaa', u'cname', u'ns', u'soa', u'mx'])

    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
        {u'cs': [{'zone_name': u'cs.university.edu', 'group_permission':
                    [u'a', u'aaaa', u'cname', u'ns', u'soa', u'mx']},
                 {'zone_name': u'eas.university.edu', 'group_permission':
                    [u'a', u'aaaa', u'cname']}],
        u'bio': [{'zone_name': u'bio.university.edu', 'group_permission':
                    [u'a', u'aaaa']}]})

    #removing permissions
    self.core_instance.UpdateGroupForwardPermission(u'cs.university.edu', u'cs',
                                                  [u'a', u'aaaa'])

    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
        {u'cs': [{'zone_name': u'cs.university.edu', 'group_permission':
                    [u'a', u'aaaa']},
                 {'zone_name': u'eas.university.edu', 'group_permission':
                    [u'a', u'aaaa', u'cname']}],
        u'bio': [{'zone_name': u'bio.university.edu', 'group_permission':
                    [u'a', u'aaaa']}]})

    #testing a zone that cs doesn't have access to
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.assertRaises(errors.AuthorizationError, 
        self.core_instance.UpdateGroupForwardPermission, 
        u'test_zone', u'cs', [u'a', u'aaaa'])

    #testing a group that doesn't exist
    self.assertRaises(errors.AuthorizationError, 
        self.core_instance.UpdateGroupForwardPermission, 
        u'cs.university.edu', u'bad_group', [u'a', u'aaaa'])

    #testing a record type that doesn't exist
    self.assertRaises(errors.UnexpectedDataError, 
        self.core_instance.UpdateGroupForwardPermission, 
        u'cs.university.edu', u'cs', [u'fake'])

    #testing a zone that doens't exist
    self.assertRaises(errors.AuthorizationError, 
        self.core_instance.UpdateGroupForwardPermission, 
        u'fake_zone', u'cs', [u'a', u'aaaa'])

  def testUpdateGroupReversePermission(self):
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
        {u'cs': [{'group_permission': [u'cname', u'ns', u'ptr', u'soa'],
                       'cidr_block': u'192.168.0.0/24'}],
         u'bio': [{'group_permission': [u'cname', u'ptr'],                                             'cidr_block': u'192.168.0.0/24'},
                  {'group_permission': [u'ptr'],
                       'cidr_block': u'192.168.1.0/24'}]})

    #testing adding permissions
    self.core_instance.UpdateGroupReversePermission(u'192.168.0.0/24', u'cs',
                                    [u'cname', u'ns', u'ptr', u'soa', u'aaaa'])

    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
       {u'cs': [{'group_permission': [u'cname', u'ns', u'ptr', u'soa', u'aaaa'],
                       'cidr_block': u'192.168.0.0/24'}],
         u'bio': [{'group_permission': [u'cname', u'ptr'],                                             'cidr_block': u'192.168.0.0/24'},
                  {'group_permission': [u'ptr'],
                       'cidr_block': u'192.168.1.0/24'}]})

    #testing removing permissions
    self.core_instance.UpdateGroupReversePermission(u'192.168.0.0/24', u'cs',
                                                   [u'cname', u'ptr'])

    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
       {u'cs': [{'group_permission': [u'cname', u'ptr'],
                       'cidr_block': u'192.168.0.0/24'}],
         u'bio': [{'group_permission': [u'cname', u'ptr'],                                             'cidr_block': u'192.168.0.0/24'},
                  {'group_permission': [u'ptr'],
                       'cidr_block': u'192.168.1.0/24'}]})

    #testing a cidr that cs doesn't have access to
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.assertRaises(errors.AuthorizationError,
        self.core_instance.UpdateGroupReversePermission, 
        u'192.168.1.0/24', u'cs', [u'cname', u'ptr', u'ns'])

    #testing a record type that doesn't exist
    self.assertRaises(errors.UnexpectedDataError,
        self.core_instance.UpdateGroupReversePermission, 
        u'192.168.0.0/24', u'cs', [u'fake'])

    #testing a group that doesn't exist
    self.assertRaises(errors.AuthorizationError,
        self.core_instance.UpdateGroupReversePermission, 
        u'192.168.0.0/24', u'no_group', [u'ptr', u'cname'])

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
                        'group_permission': [u'a', u'aaaa']}],
                      u'cs': [
                       {'zone_name': u'cs.university.edu',
                        'group_permission': [u'a', u'aaaa', u'cname', u'ns',
                                             u'soa']},
                       {'zone_name': u'eas.university.edu',
                        'group_permission': [u'a', u'aaaa', u'cname']}]})
    self.core_instance.MakeForwardZonePermission(u'eas.university.edu', u'bio',
                                                 [u'a', u'aaaa', u'ns'])
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [
                       {'zone_name': u'bio.university.edu',
                        'group_permission': [u'a', u'aaaa']},
                       {'zone_name': u'eas.university.edu',
                        'group_permission': [u'a', u'aaaa', u'ns']}],
                      u'cs': [
                       {'zone_name': u'cs.university.edu',
                        'group_permission': [u'a', u'aaaa', u'cname', u'ns',
                                             u'soa']},
                       {'zone_name': u'eas.university.edu',
                        'group_permission': [u'a', u'aaaa', u'cname']}]})
    self.assertTrue(self.core_instance.RemoveForwardZonePermission(
        u'eas.university.edu', u'bio', [u'a', u'aaaa', u'ns']))
    self.assertEqual(self.core_instance.ListForwardZonePermissions(),
                     {u'bio': [
                       {'zone_name': u'bio.university.edu',\
                        'group_permission': [u'a', u'aaaa']}],
                      u'cs': [
                       {'zone_name': u'cs.university.edu',
                        'group_permission': [u'a', u'aaaa', u'cname', u'ns',
                                             u'soa']},
                       {'zone_name': u'eas.university.edu',
                        'group_permission': [u'a', u'aaaa', u'cname']}]})

  def testReverseRangePermissionsListMakeRemove(self):
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio': [
                         {'cidr_block': u'192.168.0.0/24',
                          'group_permission': [u'cname', u'ptr']},
                         {'cidr_block': u'192.168.1.0/24',
                          'group_permission': [u'ptr']}],
                      u'cs': [
                          {'cidr_block': u'192.168.0.0/24',
                           'group_permission': [u'cname', u'ns', u'ptr',
                                                u'soa']}]})
    self.core_instance.MakeReverseRangePermission(u'10/8', u'bio',
                                                  [u'cname', u'ns', u'ptr'])
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio': [
                         {'cidr_block': u'10/8',
                          'group_permission': [u'cname', u'ns', u'ptr']},
                         {'cidr_block': u'192.168.0.0/24',
                          'group_permission': [u'cname', u'ptr']},
                         {'cidr_block': u'192.168.1.0/24',
                          'group_permission': [u'ptr']}],
                      u'cs': [
                          {'cidr_block': u'192.168.0.0/24',
                           'group_permission': [u'cname', u'ns', u'ptr',
                                                u'soa']}]})
    self.assertTrue(self.core_instance.RemoveReverseRangePermission(
        u'10/8', u'bio', [u'cname', u'ns', u'ptr']))
    self.assertEqual(self.core_instance.ListReverseRangePermissions(),
                     {u'bio': [
                         {'cidr_block': u'192.168.0.0/24',
                          'group_permission': [u'cname', u'ptr']},
                         {'cidr_block': u'192.168.1.0/24',
                          'group_permission': [u'ptr']}],
                      u'cs': [
                          {'cidr_block': u'192.168.0.0/24',
                           'group_permission': [u'cname', u'ns', u'ptr',
                                                u'soa']}]})

  def testRecordMakeRemoveListUpdate(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.core_instance.MakeZone(u'university.edu_rev', u'master',
                                u'0.168.192.in-addr.arpa.')
    self.core_instance.MakeZone(u'university_slave.edu', u'slave', 
                                u'university_slave.edu.')
    self.assertFalse(self.core_instance.ListRecords())
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'university.edu',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')

    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                       u'a', u'target', u'university_slave.edu',
                      {u'assignment_ip': u'192.168.0.55'})
    self.assertRaises(errors.UnexpectedDataError, self.core_instance.MakeRecord,
                                  u'ns', u'test-target', u'university.edu',
                                  {u'name_server' : u'192.168.1.2'})
    self.core_instance.MakeRecord(u'mx', u'university_edu',
                                  u'university.edu',
                                  {u'priority': 10,
                                   u'mail_server': u'smtp.university.edu.'},
                                  ttl=10)
    self.core_instance.MakeRecord(u'mx', u'university_edu',
                                  u'university.edu',
                                  {u'priority': 20,
                                   u'mail_server': u'smtp-2.university.edu.'},
                                  ttl=10)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                      u'mx', u'university_edu', u'university.edu',
                      {u'priority': 20,
                       u'mail_server': u'smtp-2.university.edu.'},
                      ttl=10)
    self.assertEquals(self.core_instance.ListRecords(),
                      [{u'serial_number': 4, u'refresh_seconds': 5,
                        u'target': u'soa1',
                        u'name_server': u'ns1.university.edu.',
                        u'retry_seconds': 5, 'ttl': 3600,
                        u'minimum_seconds': 5, 'record_type': u'soa',
                        'view_name': u'test_view', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'admin_email': u'admin.university.edu.',
                        u'expiry_seconds': 5},
                       {'target': u'university_edu', 'ttl': 10,
                        u'priority': 10, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp.university.edu.'},
                       {'target': u'university_edu',
                        'ttl': 10, u'priority': 20, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp-2.university.edu.'}])
    new_args_dict = self.core_instance.GetEmptyRecordArgsDict(u'mx')
    new_args_dict['priority'] = 30
    self.core_instance.UpdateRecord(u'mx', u'university_edu',
                                    u'university.edu',
                                    {u'priority': 10,
                                     u'mail_server': u'smtp.university.edu.'},
                                    u'any', update_target=u'newtarget_edu',
                                    update_record_args_dict=new_args_dict)
    self.assertEqual(self.core_instance.ListRecords(record_type=u'mx'),
                      [{'target': u'newtarget_edu', 'ttl': 10,
                        u'priority': 30, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp.university.edu.'},
                       {'target': u'university_edu',
                        'ttl': 10, u'priority': 20, 'record_type': u'mx',
                        'view_name': u'any', 'last_user': u'sharrell',
                        'zone_name': u'university.edu',
                        u'mail_server': u'smtp-2.university.edu.'}])
    args_dict = self.core_instance.GetEmptyRecordArgsDict(u'mx')
    args_dict['priority'] = 30
    self.assertEqual(self.core_instance.ListRecords(
        record_type=u'mx', record_args_dict=args_dict),
        [{'target': u'newtarget_edu', 'ttl': 10,
          'priority': 30, 'record_type': u'mx',
          'view_name': u'any', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          'mail_server': u'smtp.university.edu.'}])
    self.core_instance.RemoveRecord(u'mx', u'university_edu',
                                    u'university.edu',
                                    {u'priority': 20,
                                     u'mail_server': u'smtp-2.university.edu.'},
                                     u'any')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'mx'),
                     [{'target': u'newtarget_edu', 'ttl': 10,
                       u'priority': 30, 'record_type': u'mx',
                       'view_name': u'any', 'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                       u'mail_server': u'smtp.university.edu.'}])
    self.core_instance.MakeReservedWord(u'reserved')
    temp_core_instance = roster_core.Core(u'sharrell', self.config_instance)
    self.assertRaises(errors.ReservedWordError, temp_core_instance.MakeRecord,
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
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                      u'cname', u'computer5', u'university.edu',
                      {u'assignment_host': u'c5.university.edu.'}, ttl=10)
    self.assertEqual(self.core_instance.ListRecords(record_type=u'cname'),[])
    self.core_instance.MakeRecord(u'cname', u'c.6',
                                  u'university.edu',
                                  {u'assignment_host':
                                   u'computer6.university.edu.'},
                                  ttl=10)
    self.assertRaises(errors.InvalidInputError, self.core_instance.UpdateRecord,
                      u'cname', 'c6', u'university.edu',
                      {u'assignment_host': None}, update_target=u'computer5')
    self.assertRaises(errors.InvalidInputError, self.core_instance.UpdateRecord,
                      u'cname', 'c6', u'university.edu',
                      {u'assignment_host': None}, update_target=u'computer5.')
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                      u'a', u'computer5.net.', u'university.edu',
                      {u'assignment_ip': u'10.0.1.1'}, ttl=10)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                      u'soa', u'computer5.net.', u'university.edu',
                      {u'assignment_ip': u'10.0.1.1'}, ttl=10)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                      u'soa', u'university_edu', u'university.edu',
                      {u'name_server': u'test.', u'admin_email': u'test.',
                       u'serial_number': 2, u'refresh_seconds': 4,
                       u'retry_seconds': 4, u'expiry_seconds': 4,
                       u'minimum_seconds': 4}, ttl=10, view_name=u'any')
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                      u'soa', u'university_edu', u'university.edu',
                      {u'name_server': u'test.', u'admin_email': u'test.',
                       u'serial_number': 2, u'refresh_seconds': 4,
                       u'retry_seconds': 4, u'expiry_seconds': 4,
                       u'minimum_seconds': 4}, ttl=10, view_name=None)
    self.core_instance.MakeRecord(u'mx', u'university_edu',
                                  u'university.edu',
                                  {u'priority': 20,
                                   u'mail_server': u'smtp-2.university.edu.'},
                                  ttl=10)
    self.core_instance.MakeRecord(u'mx', u'university_edu',
                                  u'university.edu',
                                  {u'priority': 20,
                                   u'mail_server': u'smtp-1.university.edu.'},
                                  ttl=10)
    self.assertRaises(errors.InvalidInputError, self.core_instance.UpdateRecord,
                      u'mx', u'university_edu', u'university.edu',
                      {u'priority': 20,
                       u'mail_server': u'smtp-1.university.edu.'},
                      search_ttl=10, update_record_args_dict={
                      u'priority': 20,
                      u'mail_server': u'smtp-2.university.edu.'})
    self.assertEqual(self.core_instance.ListRecords(record_type=u'mx',
                                                    target=u'university_edu'),
                     [{'target': u'university_edu', 'ttl': 10, u'priority': 20,
                       'record_type': u'mx', 'view_name': u'any',
                       'last_user': u'sharrell', 'zone_name': u'university.edu',
                       u'mail_server': u'smtp-2.university.edu.'},
                      {'target': u'university_edu', 'ttl': 10, u'priority': 20,
                       'record_type': u'mx', 'view_name': u'any',
                       'last_user': u'sharrell', 'zone_name': u'university.edu',
                       u'mail_server': u'smtp-1.university.edu.'}])
    self.core_instance.MakeZone(u'ipv6_zone', u'master', u'ipv6.net.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'ipv6_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host1', u'ipv6_zone',
        {u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
        view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host1', u'ipv6_zone',
        {u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ac'},
        view_name=u'test_view')
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
        u'aaaa', u'host1', u'ipv6_zone',
        {u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
        view_name=u'test_view')
    self.assertRaises(errors.InvalidInputError, self.core_instance.UpdateRecord,
        u'aaaa', u'host1', u'ipv6_zone',
        {u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ac'},
        search_view_name=u'test_view', update_record_args_dict={
            u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'})
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
        u'cname', u'university_edu', u'university.edu',
        {u'assignment_host': u'somehost.'})
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
                      u'a', u'c.6', u'university.edu',
                      {u'assignment_ip': u'10.0.1.1'}, ttl=10)
    self.assertRaises(errors.InvalidInputError, self.core_instance.UpdateRecord,
                      u'cname', 'c6', u'university.edu',
                      {u'assignment_host': None},
                      update_target=u'university_edu')
    self.assertRaises(errors.InvalidInputError, self.core_instance.UpdateRecord,
                      u'a', 'computer5', u'university.edu',
                      {u'assignment_ip': u'192.168.0.55'},
                      update_target=u'c.6')
    self.assertRaises(
        errors.UnexpectedDataError, self.core_instance.MakeRecord,
        u'a', u'computer 5', u'university.edu',
        {u'assignment_ip': u'192.168.0.55'}, ttl=10)
    self.assertRaises(
        errors.UnexpectedDataError, self.core_instance.MakeRecord,
        u'ptr', u'5', u'university.edu_rev',
        {u'assignment_host': u'computer 5'}, ttl=10)

    self.core_instance.MakeRecord(u'a', u'test_duplicate', u'university.edu',
        {u'assignment_ip': u'192.168.1.26'}, view_name=u'test_view', ttl=583)
    self.core_instance.MakeRecord(u'a', u'test_duplicate', u'university.edu',
        {u'assignment_ip': u'192.168.1.126'}, view_name=u'any', ttl=583)
    self.core_instance.MakeRecord(u'aaaa', u'test_duplicate', u'university.edu',
        {u'assignment_ip': u'6fd1:0000:0000:0000:0000:0000:0120:0126'}, view_name=u'test_view', ttl=583)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
        u'cname', u'test_duplicate', u'university.edu', {u'assignment_host': u'tester.university.edu.'},
        view_name=u'test_view', ttl=400)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
        u'cname', u'test_duplicate', u'university.edu', {u'assignment_host': u'tester.university.edu.'},
        view_name=u'any', ttl=400)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
        u'a', u'test_duplicate', u'university.edu', {u'assignment_ip': u'192.168.1.26'},
        view_name=u'any', ttl=400)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord,
        u'a', u'test_duplicate', u'university.edu', {u'assignment_ip': u'192.168.1.26'},
        view_name=u'test_view', ttl=400)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord, 
        u'aaaa', u'test_duplicate', u'university.edu',
        {u'assignment_ip': u'6fd1:0000:0000:0000:0000:0000:0120:0126'}, view_name=u'test_view', ttl=583)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord, 
        u'aaaa', u'test_duplicate', u'university.edu',
        {u'assignment_ip': u'6fd1:0000:0000:0000:0000:0000:0120:0126'}, view_name=u'any', ttl=583)
    self.assertRaises(errors.InvalidInputError, self.core_instance.MakeRecord, u'a',
        u'test_duplicate', u'university.edu', {u'assignment_ip': u'192.168.1.126'},
        view_name=u'test_view', ttl=400)

  def testSOA(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'university_edu', u'university.edu',
        {u'name_server': u'test.', u'admin_email': u'test.',
         u'serial_number': 4294967294, u'refresh_seconds': 4,
         u'retry_seconds': 4, u'expiry_seconds': 4, u'minimum_seconds': 4},
        ttl=10, view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'soa'),
                     [{'zone_name': u'university.edu', u'refresh_seconds': 4,
                       'target': u'university_edu', u'name_server': u'test.',
                       'record_type': u'soa', 'last_user': u'sharrell',
                       u'minimum_seconds': 4, u'retry_seconds': 4,
                       'view_name': u'test_view', 'ttl': 10,
                       u'serial_number': 4294967295, u'admin_email': u'test.',
                       u'expiry_seconds': 4}])
    self.core_instance.UpdateRecord(u'soa', u'university_edu',
                                    u'university.edu',
                                    {u'name_server': u'test.',
                                     u'admin_email': u'test.',
                                     u'serial_number': 4294967295,
                                     u'refresh_seconds': 4,
                                     u'retry_seconds': 4,
                                     u'expiry_seconds': 4,
                                     u'minimum_seconds': 4}, u'test_view',
                                    update_target=u'newtarget')
    self.assertEqual(self.core_instance.ListRecords(),
                     [{u'serial_number': 1, u'refresh_seconds': 4,
                       'target': u'newtarget', u'name_server': u'test.',
                       u'retry_seconds': 4, 'ttl': 10, u'minimum_seconds': 4,
                       'record_type': u'soa', 'view_name': u'test_view',
                       'last_user': u'sharrell',
                       'zone_name': u'university.edu',
                       u'admin_email': u'test.', u'expiry_seconds': 4}])
    self.core_instance.db_instance.StartTransaction()
    self.core_instance._IncrementSoa(u'test_view', u'university.edu')
    self.core_instance.db_instance.EndTransaction()
    self.assertEqual(self.core_instance.ListRecords(),
                     [{u'serial_number': 2, u'refresh_seconds': 4,
                       'target': u'newtarget', u'name_server': u'test.',
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
                                                                   u'slave',
                                                                   u'hint']))
    self.assertTrue(self.core_instance.RemoveZoneType(u'forward'))
    self.assertEqual(set(self.core_instance.ListZoneTypes()), set([u'master',
                                                                   u'slave',
                                                                   u'hint']))
    self.core_instance.MakeZoneType(u'newtype')
    self.assertEqual(set(self.core_instance.ListZoneTypes()), set([u'master',
                                                                   u'slave',
                                                                   u'hint',
                                                                   u'newtype']))

  def testListMakeNamedConfGlobalOptions(self):
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'test;')
    named_conf_options = self.core_instance.ListNamedConfGlobalOptions()
    self.assertEqual(len(named_conf_options), 1)
    self.assertEqual(named_conf_options[0]['options'], u'test;')
    self.assertEqual(named_conf_options[0]['dns_server_set_name'], u'set1')
    self.assertEqual(named_conf_options[0]['id'], 1)

  def testReservedWordMakeRemoveList(self):
    self.core_instance.MakeReservedWord(u'word1')
    self.assertEqual(self.core_instance.ListReservedWords(),
                     [u'word1'])
    self.assertTrue(self.core_instance.RemoveReservedWord(u'word1'))
    self.assertEqual(self.core_instance.ListReservedWords(),
                     [])

  def testListAuditLog(self):
    begin_time = datetime.datetime.now().replace(microsecond=0)
    self.core_instance.MakeReservedWord(u'word1')
    time.sleep(0.1)
    end_time = datetime.datetime.now().replace(microsecond=0)
    time.sleep(1.1)
    self.core_instance.MakeZone(u'test_zone', u'master', u'university.edu.')
    log_list = self.core_instance.ListAuditLog(begin_timestamp=begin_time,
                                               end_timestamp=end_time)
    self.assertEqual(len(log_list), 1)
    self.assertEqual(log_list[0]['action'], u'MakeReservedWord')
    self.assertEqual(cPickle.loads(str(log_list[0]['data'])),
                     {'replay_args': [u'word1'],
                      'audit_args': {'reserved_word': u'word1'}})
    self.assertEqual(log_list[0]['audit_log_timestamp'], begin_time)
    self.assertEqual(log_list[0]['audit_log_user_name'], u'sharrell')
    self.assertEqual(log_list[0]['success'], 1)

    self.core_instance.MakeView(u'test_view')
    self.assertEqual(len(self.core_instance.ListAuditLog(action=u'MakeView')),
                     1)
    self.assertEqual(len(self.core_instance.ListAuditLog(action=u'Action')),
                     0)
    self.assertEqual(len(self.core_instance.ListAuditLog(
        user_name=u'sharrell')), 3)

  def testSetCheckMaintenanceFlag(self):
    self.assertFalse(self.core_instance.CheckMaintenanceFlag())

    self.core_instance.SetMaintenanceFlag(True)

    self.assertTrue(self.core_instance.CheckMaintenanceFlag())

    self.core_instance.SetMaintenanceFlag(False)

    self.assertFalse(self.core_instance.CheckMaintenanceFlag())

  def testCheckCoreVersionMatches(self):
    core.CheckCoreVersionMatches(core.__version__)
    self.assertRaises(errors.VersionDiscrepancyError,
                      core.CheckCoreVersionMatches, 00)

  def testListViewDependencies(self):
    self.assertEqual(self.core_instance.ListViewDependencies(),
                     [u'any'])
    self.core_instance.MakeView(u'view1')
    self.core_instance.MakeView(u'view2')
    self.core_instance.MakeView(u'view3')
    self.assertEqual(self.core_instance.ListViewDependencies(),
                     [u'any', u'view1_dep', u'view2_dep', u'view3_dep'])


if( __name__ == '__main__' ):
    unittest.main()
