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


import unittest
import MySQLdb

import roster_core
from roster_core import data_validation
from roster_core import db_access
from roster_core import table_enumeration


CONFIG_FILE = os.path.expanduser('~/.rosterrc') # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'


class TestdbAccess(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    self.db_instance = self.config_instance.GetDb()

    schema = open(SCHEMA_FILE, 'r').read()
    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(schema)
    self.db_instance.CommitTransaction()

    data = open(DATA_FILE, 'r').read()
    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(data)
    self.db_instance.CommitTransaction()

  def tearDown(self):
    self.db_instance.close()

  def testTransactions(self):
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.CommitTransaction)
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.RollbackTransaction)
    self.db_instance.StartTransaction()
    self.assertRaises(db_access.TransactionError,
                      self.db_instance.StartTransaction)
    self.db_instance.CommitTransaction()
    self.db_instance.StartTransaction()
    self.db_instance.RollbackTransaction()

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

  def testInitDataValidation(self):
    self.db_instance.InitDataValidation()
    self.assertEqual(self.db_instance.data_validation_instance.reserved_words, 
                     [u'damn'])

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

    self.db_instance.MakeRow('acls', {'acl_name': u'test',
                                      'acl_range_allowed': 1,
                                      'acl_cidr_block': '192.168.0/24'})

    rows = self.db_instance.ListRow('acls', search_dict)
    self.assertNotEquals(rows, ())
    self.assertEquals(len(rows), 1)
    self.assertEquals(rows[0]['acl_range_allowed'], 1)

    update_dict = self.db_instance.GetEmptyRowDict('acls')
    update_dict['acl_range_allowed'] = 0
    self.db_instance.UpdateRow('acls', search_dict, update_dict)
    rows = self.db_instance.ListRow('acls', search_dict)
    self.assertNotEquals(rows, ())
    self.assertEquals(len(rows), 1)
    self.assertEquals(rows[0]['acl_range_allowed'], 0)

    self.assertTrue(self.db_instance.RemoveRow('acls', rows[0]))

    self.assertFalse(self.db_instance.ListRow('acls', search_dict))

    users_dict = self.db_instance.GetEmptyRowDict('users')
    user_group_assignments_dict = (
        self.db_instance.GetEmptyRowDict('user_group_assignments'))
    forward_zone_permissions_dict = (
        self.db_instance.GetEmptyRowDict('forward_zone_permissions'))
    self.assertEqual(self.db_instance.ListRow('users', users_dict,
                                              'user_group_assignments',
                                              user_group_assignments_dict,
                                              'forward_zone_permissions',
                                              forward_zone_permissions_dict),
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
            'forward_zone_permissions_zone_name': u'bio.university.edu'}))
                                              
    self.db_instance.CommitTransaction()

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
    tables = table_enumeration.GetValidTables()
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

    self.db_instance.cursor.execute('show tables')
    table_dicts = self.db_instance.cursor.fetchall()
    db_tables = []
    for table_dict in table_dicts:
      db_tables.append(table_dict[
          'Tables_in_%s' % self.config_instance.config_file['database'][
              'database']])

    for db_table in db_tables:
      self.assertTrue(db_table in tables)

    self.db_instance.CommitTransaction()

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
    self.assertEqual(self.db_instance.TableRowCount('users'), 3)


if( __name__ == '__main__' ):
    unittest.main()
