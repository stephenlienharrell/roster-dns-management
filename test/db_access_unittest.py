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

"""Unittest for db_access.py

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import cPickle
import datetime
import unittest
import time
import MySQLdb
import os
import threading

import roster_core
from roster_core import data_validation
from roster_core import db_access
from roster_core import helpers_lib


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
DATA_FILE = 'test_data/test_data.sql'


class DbAccessThread(threading.Thread):
  def __init__(self, db_instance, test_instance, num1, num2):
    self.db_instance = db_instance
    self.test_instance = test_instance
    self.view_name = u'test_view%s-%s' % (num1, num2)
    threading.Thread.__init__(self)
  def run(self):
    self.db_instance.StartTransaction()
    self.test_instance.assertEqual(self.db_instance.ListRow(
        'views',self.db_instance.GetEmptyRowDict('views')), ())
    self.test_instance.assertTrue(self.db_instance.MakeRow(
        'views', {'view_options': u'', 'view_name': self.view_name}))
    self.test_instance.assertEqual(self.db_instance.ListRow(
        'views',self.db_instance.GetEmptyRowDict('views')),
        ({'view_options': u'', 'view_name': self.view_name},))
    self.test_instance.assertTrue(self.db_instance.RemoveRow(
        'views', {'view_options': u'', 'view_name': self.view_name}))
    self.test_instance.assertEqual(self.db_instance.ListRow(
        'views',self.db_instance.GetEmptyRowDict('views')), ())
    self.db_instance.EndTransaction()

class DbLockThread(threading.Thread):
  def __init__(self, db_instance):
    self.db_instance = db_instance
    threading.Thread.__init__(self)
  def run(self):
    self.db_instance.StartTransaction()
    self.db_instance.LockDb()
    time.sleep(1)
    self.db_instance.UnlockDb()
    self.db_instance.EndTransaction()


class TestdbAccess(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    self.db_instance = self.config_instance.GetDb()

    self.db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(data)
    self.db_instance.EndTransaction()

  def tearDown(self):
    self.db_instance.close()

  def testThread(self):
    for i in range(10):
      new_db_instance = self.config_instance.GetDb()
      lock_thread = DbLockThread(new_db_instance)
      lock_thread.start()
      lock_thread.join()
      new_db_instance = self.config_instance.GetDb()
      for j in range(20):
        thread = DbAccessThread(new_db_instance, self, i, j)
        thread.start()
        thread.join()

  def testTransactions(self):
    self.db_instance.thread_safe = False
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.EndTransaction)
    self.db_instance.StartTransaction()
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.StartTransaction)
    self.db_instance.EndTransaction()

  def testDbLocking(self):
    self.db_instance.StartTransaction()
    self.assertRaises(db_access.TransactionError, self.db_instance.UnlockDb)
    self.db_instance.LockDb()
    users_dict = self.db_instance.GetEmptyRowDict('users')
    users_dict['user_name'] = u'test'
    users_dict['access_level'] = 32
    self.assertRaises(MySQLdb.OperationalError, self.db_instance.MakeRow,
                      'users', users_dict)
    self.assertRaises(db_access.TransactionError, self.db_instance.LockDb)
    self.db_instance.UnlockDb()
    self.db_instance.MakeRow('users', users_dict)
    self.db_instance.EndTransaction()

  def testInitDataValidation(self):
    self.db_instance.InitDataValidation()
    self.assertEqual(self.db_instance.data_validation_instance.reserved_words, 
                     [])

  def testGetUserAuthorizationInfo(self):
    self.assertEquals(self.db_instance.GetUserAuthorizationInfo(u'notindb'), {})

    self.assertEquals(self.db_instance.GetUserAuthorizationInfo(u'jcollins'),
        {'user_access_level': 32,
         'user_name': 'jcollins',
         'forward_zones': [],
         'groups': [],
         'reverse_ranges': []})

    self.assertEquals(self.db_instance.GetUserAuthorizationInfo(u'shuey'),
        {'user_access_level': 64,
         'user_name': 'shuey',
         'forward_zones': [
             {'zone_name': 'cs.university.edu', 'access_right': 'rw'},
             {'zone_name': 'eas.university.edu', 'access_right': 'r'},
             {'zone_name': 'bio.university.edu', 'access_right': 'rw'}],
         'groups': ['cs', 'bio'],
         'reverse_ranges': [
             {'cidr_block': '192.168.0.0/24',
              'access_right': 'rw'},
             {'cidr_block': '192.168.0.0/24',
              'access_right': 'r'},
             {'cidr_block': '192.168.1.0/24',
              'access_right': 'rw'}]})

  def testRowFuncs(self):
    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.MakeRow, 'notinlist', {})
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.MakeRow, 'acls', {})
    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.RemoveRow, 'notinlist', {})
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.RemoveRow, 'acls', {})
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.ListRow, 'acls', {})

    self.db_instance.StartTransaction()
    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.ListRow, 'notinlist', {})

    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.ListRow)

    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.ListRow, 'onearg')

    audit_log_dict = {'audit_log_id': None,
                      'audit_log_user_name': u'sharrell',
                      'action': u'DoThis',
                      'data': cPickle.dumps('I did it'),
                      'success': 1,
                      'audit_log_timestamp': datetime.datetime(2001, 1, 1, 1)}

    self.db_instance.MakeRow('audit_log', audit_log_dict)
    audit_log_dict['audit_log_timestamp'] = datetime.datetime(2001, 1, 1, 2)
    self.db_instance.MakeRow('audit_log', audit_log_dict)
    audit_log_dict['audit_log_timestamp'] = datetime.datetime(2001, 1, 1, 3)
    audit_log_dict['data'] = cPickle.dumps('You did it')
    self.db_instance.MakeRow('audit_log', audit_log_dict)
    audit_log_dict['audit_log_timestamp'] = datetime.datetime(2001, 1, 1, 4)
    self.db_instance.MakeRow('audit_log', audit_log_dict)

    search_dict = self.db_instance.GetEmptyRowDict('audit_log')
    simple_date = datetime.datetime(2001,1,1,1)
    self.assertRaises(db_access.InvalidInputError, self.db_instance.ListRow,
                      'audit_log', search_dict,
                      date_column='audit_log_timestamp')
    self.assertRaises(db_access.InvalidInputError, self.db_instance.ListRow,
                      'audit_log', search_dict,
                      date_range='audit_log_timestamp')
    self.assertRaises(db_access.InvalidInputError, self.db_instance.ListRow,
                      'audit_log', search_dict, date_column='action',
                      date_range=(simple_date, simple_date))
    self.assertRaises(db_access.InvalidInputError, self.db_instance.ListRow,
                      'audit_log', search_dict, date_column='not_there',
                      date_range=(simple_date, simple_date))
    self.assertRaises(db_access.InvalidInputError, self.db_instance.ListRow,
                      'audit_log', search_dict, date_column='not_there',
                      date_range=('bleh', simple_date))
    self.assertEquals(self.db_instance.ListRow(
        'audit_log', search_dict, date_column='audit_log_timestamp',
        date_range=(datetime.datetime(2001, 1, 1, 2),
                    datetime.datetime(2001, 1, 1, 3))),
        ({'action': u'DoThis',
          'audit_log_timestamp': datetime.datetime(2001, 1, 1, 2, 0),
          'data': u"S'I did it'\np1\n.", 'audit_log_user_name': u'sharrell',
          'audit_log_id': 2L, 'success': 1},
         {'action': u'DoThis',
          'audit_log_timestamp': datetime.datetime(2001, 1, 1, 3, 0),
          'data': u"S'You did it'\np1\n.", 'audit_log_user_name': u'sharrell',
          'audit_log_id': 3L, 'success': 1}))

    search_dict['data'] = cPickle.dumps('I did it')
    self.assertEquals(self.db_instance.ListRow(
        'audit_log', search_dict, date_column='audit_log_timestamp',
        date_range=(datetime.datetime(2001, 1, 1, 2),
                    datetime.datetime(2001, 1, 1, 3))),
        ({'action': u'DoThis',
          'audit_log_timestamp': datetime.datetime(2001, 1, 1, 2, 0),
          'data': u"S'I did it'\np1\n.", 'audit_log_user_name': u'sharrell',
          'audit_log_id': 2L, 'success': 1},))

    search_dict = self.db_instance.GetEmptyRowDict('acls')
    second_search_dict = self.db_instance.GetEmptyRowDict('users')
    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.ListRow, 'acls', search_dict,
                      invalid_kwarg=True)
    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.ListRow, 'acls', search_dict,
                      'users', second_search_dict)

    search_dict['acl_name'] = u'test'
    self.assertEquals((), self.db_instance.ListRow('acls', search_dict))

    self.db_instance.MakeRow('acls', {'acl_name': u'test'})

    rows = self.db_instance.ListRow('acls', search_dict)
    self.assertNotEquals(rows, ())
    self.assertEquals(len(rows), 1)
    self.assertEquals(rows[0]['acl_name'], u'test')

    update_dict = self.db_instance.GetEmptyRowDict('acls')
    update_dict['acl_name'] = u'test2'
    self.db_instance.UpdateRow('acls', search_dict, update_dict)
    rows = self.db_instance.ListRow('acls', update_dict)
    self.assertNotEquals(rows, ())
    self.assertEquals(len(rows), 1)
    self.assertFalse(self.db_instance.ListRow('acls', search_dict))

    self.assertTrue(self.db_instance.RemoveRow('acls', rows[0]))

    self.assertFalse(self.db_instance.ListRow('acls', update_dict))

    users_dict = self.db_instance.GetEmptyRowDict('users')
    user_group_assignments_dict = (
        self.db_instance.GetEmptyRowDict('user_group_assignments'))
    forward_zone_permissions_dict = (
        self.db_instance.GetEmptyRowDict('forward_zone_permissions'))
    self.assertEqual(sorted(self.db_instance.ListRow(
                            'users', users_dict,
                            'user_group_assignments',
                            user_group_assignments_dict,
                            'forward_zone_permissions',
                            forward_zone_permissions_dict)),
        sorted(
        ({'user_group_assignments_user_name': u'sharrell',
          'forward_zone_permissions_group_name': u'cs', 'access_level': 128,
          'forward_zone_permissions_access_right': u'rw', 'user_name':
          u'sharrell', 'user_group_assignments_group_name': u'cs',
          'forward_zone_permissions_zone_name': u'cs.university.edu'},
          {'user_group_assignments_user_name': u'shuey',
            'forward_zone_permissions_group_name': u'cs', 'access_level': 64,
            'forward_zone_permissions_access_right': u'rw', 'user_name':
            u'shuey', 'user_group_assignments_group_name': u'cs',
            'forward_zone_permissions_zone_name': u'cs.university.edu'},
          {'user_group_assignments_user_name': u'shuey',
            'forward_zone_permissions_group_name': u'cs', 'access_level': 64,
            'forward_zone_permissions_access_right': u'rw', 'user_name':
            u'shuey', 'user_group_assignments_group_name': u'bio',
            'forward_zone_permissions_zone_name': u'cs.university.edu'},
          {'user_group_assignments_user_name': u'sharrell',
            'forward_zone_permissions_group_name': u'cs', 'access_level': 128,
            'forward_zone_permissions_access_right': u'r', 'user_name':
            u'sharrell', 'user_group_assignments_group_name': u'cs',
            'forward_zone_permissions_zone_name': u'eas.university.edu'},
          {'user_group_assignments_user_name': u'shuey',
            'forward_zone_permissions_group_name': u'cs', 'access_level': 64,
            'forward_zone_permissions_access_right': u'r', 'user_name':
            u'shuey', 'user_group_assignments_group_name': u'cs',
            'forward_zone_permissions_zone_name': u'eas.university.edu'},
          {'user_group_assignments_user_name': u'shuey',
            'forward_zone_permissions_group_name': u'cs', 'access_level': 64,
            'forward_zone_permissions_access_right': u'r', 'user_name':
            u'shuey', 'user_group_assignments_group_name': u'bio',
            'forward_zone_permissions_zone_name': u'eas.university.edu'},
          {'user_group_assignments_user_name': u'sharrell',
            'forward_zone_permissions_group_name': u'bio', 'access_level': 128,
            'forward_zone_permissions_access_right': u'rw', 'user_name':
            u'sharrell', 'user_group_assignments_group_name': u'cs',
            'forward_zone_permissions_zone_name': u'bio.university.edu'},
          {'user_group_assignments_user_name': u'shuey',
            'forward_zone_permissions_group_name': u'bio', 'access_level': 64,
            'forward_zone_permissions_access_right': u'rw', 'user_name':
            u'shuey', 'user_group_assignments_group_name': u'cs',
            'forward_zone_permissions_zone_name': u'bio.university.edu'},
          {'user_group_assignments_user_name': u'shuey',
            'forward_zone_permissions_group_name': u'bio', 'access_level': 64,
            'forward_zone_permissions_access_right': u'rw', 'user_name':
            u'shuey', 'user_group_assignments_group_name': u'bio',
            'forward_zone_permissions_zone_name': u'bio.university.edu'})))
                                              
    self.db_instance.EndTransaction()

  def testGetRecordArgsDict(self):
    self.assertEquals(self.db_instance.GetRecordArgsDict(u'mx'),
                      {u'priority': u'UnsignedInt',
                       u'mail_server': u'Hostname'})
    self.assertRaises(db_access.InvalidInputError,
                      self.db_instance.GetRecordArgsDict, u'not_a_record_type')

  def testValidateRecordArgsDict(self):
    record_args_dict = self.db_instance.GetEmptyRecordArgsDict(u'mx')
    self.assertRaises(db_access.UnexpectedDataError, 
                      self.db_instance.ValidateRecordArgsDict, u'mx',
                      record_args_dict)
    record_args_dict.pop('priority')
    self.assertRaises(db_access.InvalidInputError, 
                      self.db_instance.ValidateRecordArgsDict, u'mx',
                      record_args_dict)
    record_args_dict = {'priority': 10,
                        'mail_server': u'mail.university.edu.'}
    self.db_instance.ValidateRecordArgsDict(u'mx', record_args_dict)
    record_args_dict['priority'] = None
    self.db_instance.ValidateRecordArgsDict(u'mx', record_args_dict,
                                            none_ok=True)

  def testTableEnumerationDatabaseconsistency(self):
    self.db_instance.StartTransaction()
    tables = helpers_lib.GetValidTables()
    for table in tables:
       self.db_instance.cursor.execute('describe %s' % table)
       db_elements = self.db_instance.cursor.fetchall()
       row_dict = self.db_instance.GetEmptyRowDict(table)

       fields = []
       for db_element in db_elements:
         fields.append(db_element['Field'])

       for column in row_dict.iterkeys():
         # Use this line to track down what is wrong
         # print 'testing %s in %s\n' % (column, fields)
         self.assertTrue(column in fields)

    db_tables = self.db_instance.ListTableNames()
    for db_table in db_tables:
      if( not db_table == 'locks' ):
        self.assertTrue(db_table in tables)

    self.db_instance.EndTransaction()

  def testDataTypeValidation(self):
    self.db_instance.StartTransaction()
    search_data_type_dict = self.db_instance.GetEmptyRowDict('data_types')
    data_type_dicts = self.db_instance.ListRow('data_types',
                                               search_data_type_dict)
    data_validation_methods = dir(data_validation.DataValidation([]))
    for data_type_dict in data_type_dicts:
      # If something goes wrong uncomment this next line to see what happened.
      # print 'Searching for %s tester' % data_type_dict['data_type']
      self.assertTrue('is%s' % data_type_dict['data_type'] in
                      data_validation_methods)

  def testTableRowCount(self):
    self.db_instance.StartTransaction()
    self.assertEqual(self.db_instance.TableRowCount('users'), 4)

  def testListTables(self):
    self.db_instance.StartTransaction()
    self.assertEqual(
      self.db_instance.ListTableNames(),
      [u'acl_ranges', u'acls', u'audit_log', u'credentials', u'data_types',
       u'dns_server_set_assignments', u'dns_server_set_view_assignments',
       u'dns_server_sets', u'dns_servers', u'forward_zone_permissions',
       u'groups', u'locks', u'named_conf_global_options', u'record_arguments',
       u'record_arguments_records_assignments', u'record_types', u'records',
       u'reserved_words', u'reverse_range_permissions',
       u'reverse_range_zone_assignments', u'user_group_assignments', u'users',
       u'view_acl_assignments', u'view_dependencies',
       u'view_dependency_assignments', u'views', u'zone_types',
       u'zone_view_assignments', u'zones'])
    self.db_instance.EndTransaction()


  def testCheckMaintenanceFlag(self):
    self.db_instance.StartTransaction()
    try:
      self.assertFalse(self.db_instance.CheckMaintenanceFlag())
    finally:
      self.db_instance.EndTransaction()
    self.db_instance.StartTransaction()
    cursor = self.db_instance.connection.cursor()
    try:
      cursor.execute(
          'UPDATE locks SET locked = 1 WHERE lock_name = "maintenance"')
    finally:
      cursor.close()
    self.db_instance.EndTransaction()
    self.db_instance.StartTransaction()
    try:
      self.assertTrue(self.db_instance.CheckMaintenanceFlag())
    finally:
      self.db_instance.EndTransaction()

  def testGetCurrentTime(self):
    self.db_instance.StartTransaction()
    time = self.db_instance.GetCurrentTime()
    self.db_instance.EndTransaction()
    self.assertTrue(isinstance(time, datetime.datetime))

  def testCreateRosterDatabase(self):
    self.db_instance.CreateRosterDatabase()

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute('SHOW TABLES')
    table_names = self.db_instance.cursor.fetchall()
    self.db_instance.cursor.execute('SET FOREIGN_KEY_CHECKS=0')
    for table in table_names:
      table_name = table.values()[0]
      self.db_instance.cursor.execute('DROP TABLE %s' %
                                      table_name)
    self.db_instance.cursor.execute('SET FOREIGN_KEY_CHECKS=1')
    self.db_instance.EndTransaction()
 
    self.db_instance.CreateRosterDatabase()

  def testDumpDatabase(self):
    self.db_instance.StartTransaction()
    dump = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()

    self.assertTrue('acls' in dump)

    self.assertEquals(dump['data_types']['schema'], (
        'CREATE TABLE `data_types` (\n  '
        '`data_types_id` smallint(5) unsigned NOT NULL auto_increment,\n  '
        '`data_type` varchar(255) NOT NULL,\n  '
        'PRIMARY KEY  (`data_types_id`),\n  '
        'UNIQUE KEY `data_type` (`data_type`),\n  '
        'KEY `data_types_1` (`data_type`)\n'
        ') ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8'))

    self.assertEquals(dump['groups']['columns'], [u'group_id', u'group_name'])

    self.assertEquals(dump['users']['rows'][0],
                      {'users_id': '1',
                       'access_level': '0',
                       'user_name': "'tree_export_user'"})

if( __name__ == '__main__' ):
    unittest.main()
