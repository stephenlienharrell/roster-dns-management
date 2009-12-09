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

"""This module is an API to access the dnsManagement database.

This module should only be run by servers with authentication layers
that are active. This module does not include authentication, but does
include authorization.

The api that will be exposed by this module is meant for use in a web
application or rpc server. This module is not for use in command line tools.

The two primary uses of this class are: 
1. to use convience functions to get large amounts of data out of the db 
  without large amounts of db queries. For usage on this consult the pydoc
  on the individual functions.

2. to Make/Remove/List rows in the database. The method that is used in this
  class is based on generic Make/Remove/Lock functions that take specifc
  dictionaries that correspond to the table that is being referenced. 

  Here is an example of how to remove rows from the acls table:

  acls_dict = db_instance.GetEmptyRowDict('acls')
  acls_dict['acl_name'] = 'test_acl'
  db_instance.StartTransaction()
  try:
    matching_rows = db_instance.ListRow('acls', acls_dict)
    for row in matching_rows:
      db_instance.RemoveRow('acls', row)
  except Exception:
    db_instance.EndTransaction(rollback=True)
  else:
    db_instance.EndTransaction()

Note: MySQLdb.Error can be raised in almost any function in this module. Please
      keep that in mind when using this module.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.9'


import datetime
import Queue
import threading
import time
import uuid

import MySQLdb
import MySQLdb.cursors

import constants
import data_validation
import errors
import table_enumeration


class TransactionError(errors.DbAccessError):
  pass


class UnexpectedDataError(data_validation.UnexpectedDataError):
  pass


class InvalidInputError(data_validation.InvalidInputError):
  pass


class MissingDataTypeError(data_validation.MissingDataTypeError):
  pass


class dbAccess(object):
  """This class provides the primary interface for connecting and interacting
   with the roster database.
   """

  def __init__(self, db_host, db_user, db_passwd, db_name, big_lock_timeout,
               big_lock_wait, thread_safe=True):
    """Instantiates the db_access class.

    Inputs:
      db_host: string of the database host name
      db_user: string of the user name used to connect to mysql
      db_passwd: string of password used to connect to mysql
      db_name: string of name of database in mysql server to use
      big_lock_timeout: integer of how long the big lock should be valid for
      big_lock_wait: integer of how long to wait for proccesses to finish
                     before locking the database
      thread_safe: boolean of if db_acceess should be thread safe
    """
    # Do some better checking of these args
    self.db_host = db_host
    self.db_user = db_user
    self.db_passwd = db_passwd
    self.db_name = db_name
    self.big_lock_timeout = big_lock_timeout
    self.big_lock_wait = big_lock_wait
    self.transaction_init = False
    self.connection = None
    self.cursor = None
    # This is generated only when ListRow is called and is then cached for
    # the life of the object.
    self.foreign_keys = []
    self.data_validation_instance = None
    self.locked_db = False
    self.thread_safe = thread_safe
    self.queue = Queue.Queue()
    self.now_serving = None
    self.queue_update_lock = threading.Lock()

  def close(self):
    """Closes a connection that has been opened. 

    A new connection will be created on StartTransaction.
    """
    if( self.connection is not None ):
      self.connection.close()
    self.connection = None
    
  def StartTransaction(self):
    """Starts a transaction.

    Also it starts a db connection if none exists or it times out.
    Always creates a new cursor.
    
    This function also serializes all requests on this object and if the 
    big lock has been activated will wait for it to be released.

    Raises:
      TransactionError: Cannot start new transaction last transaction not
                        committed or rolled-back.
    """
    if( self. thread_safe ):
      unique_id = uuid.uuid4()
      self.queue.put(unique_id)

      while_sleep = 0
      while( unique_id != self.now_serving ):
        time.sleep(while_sleep)
        self.queue_update_lock.acquire()
        if( self.now_serving is None ):
          self.now_serving = self.queue.get()
        self.queue_update_lock.release()
        while_sleep = 0.005

    else:
      if( self.transaction_init ):
        raise TransactionError('Cannot start new transaction last transaction '
                               'not committed or rolled-back.')

    if( self.connection is not None ):
      try:
        self.cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)
      except MySQLdb.OperationalError:
        self.connection = None

    if( self.connection is None ):
      self.connection = MySQLdb.connect(host=self.db_host, user=self.db_user,
                                        passwd=self.db_passwd, db=self.db_name,
                                        use_unicode=True)
      self.cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)

    while_sleep = 0
    db_lock_locked = 1
    while( db_lock_locked ):
      time.sleep(while_sleep)
      try:
        self.cursor.execute('SELECT `locked`, `lock_last_updated`, '
                            'NOW() as `now` from `locks` WHERE '
                            '`lock_name`="db_lock_lock"')
        rows = self.cursor.fetchall()
      except MySQLdb.ProgrammingError:
        break
      if( not rows ):
        break
      lock_last_updated = rows[0]['lock_last_updated']
      db_lock_locked = rows[0]['locked']
      now = rows[0]['now']
      if( (now - lock_last_updated).seconds > self.big_lock_timeout ):
        break
      while_sleep = 1

    self.transaction_init = True

  def EndTransaction(self, rollback=False):
    """Ends a transaction.

    Also does some simple checking to make sure a connection was open first
    and releases itself from the current queue.

    Inputs:
      rollback: boolean of if the transaction should be rolled back

    Raises:
      TransactionError: Must run StartTansaction before EndTransaction.
    """
    if( not self.thread_safe ):
      if( not self.transaction_init ):
        raise TransactionError('Must run StartTansaction before '
                               'EndTransaction.')

    try:
      self.cursor.close()
      if( rollback ):
        self.connection.rollback()
      else:
        self.connection.commit()

    finally:
      self.transaction_init = False
      if( self.thread_safe ):
        if( not self.queue.empty() ):
          self.now_serving = self.queue.get()
        else:
          self.now_serving = None

  def LockDb(self):
    """This function is to lock the whole database for consistent data
    retrevial.

    This function expects for self.db_instance.cursor to be instantiated and
    valid.
    """
    if( self.locked_db is True ):
      raise TransactionError('Must unlock tables before re-locking them')
    self.cursor.execute('UPDATE `locks` SET `locked`=1 WHERE '
                        '`lock_name`="db_lock_lock"')
    time.sleep(self.big_lock_wait)
    self.cursor.execute(
        'LOCK TABLES %s READ' % ' READ, '.join(constants.TABLES.keys()))
    self.locked_db = True

  def UnlockDb(self):
    """This function is to unlock the whole database.

    This function expects for self.db_instance.cursor to be instantiated and
    valid. It also expects all tables to be locked.
    """
    if( self.locked_db is False ):
      raise TransactionError('Must lock tables before unlocking them')
    self.cursor.execute('UNLOCK TABLES')
    self.cursor.execute('UPDATE `locks` SET `locked`=0 WHERE '
                        '`lock_name`="db_lock_lock"')
    self.locked_db = False

  def InitDataValidation(self):
    """Get all reserved words and return them.

    Outputs:
      list of reserved words.
        example: ['cordova', 'jischke']
    """
    cursor = self.connection.cursor()
    try:
      cursor.execute('SELECT reserved_word FROM reserved_words')
      rows = cursor.fetchall()
    finally:
      cursor.close()

    words = [row[0] for row in rows]

    self.data_validation_instance = data_validation.DataValidation(words)

  def GetUserAuthorizationInfo(self, user):
    """Grabs authorization data from the db and returns a dict.

    This function does two selects on the db, one for forward and one for
    reverse zones. It also parses the data into a dict for ease of use.

    Inputs:
      user: string of username

    Raises:
      UnexpectedDataError: Row did not contain
                           reverse_range_permissions_access_right or
                           forward_zone_permissions_access_right

    Outputs:
      dict: dict with all the relevant information
        example:
        {'user_access_level': '2',
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
              'access_right': 'rw'}]}
    """
    auth_info_dict = {}
    db_data = []

    users_dict = self.GetEmptyRowDict('users')
    users_dict['user_name'] = user
    user_group_assignments_dict = self.GetEmptyRowDict('user_group_assignments')
    forward_zone_permissions_dict = self.GetEmptyRowDict(
        'forward_zone_permissions')
    reverse_range_permissions_dict = self.GetEmptyRowDict(
        'reverse_range_permissions')

    auth_info_dict['user_name'] = user
    auth_info_dict['groups'] = []
    auth_info_dict['forward_zones'] = []
    auth_info_dict['reverse_ranges'] = []

    self.StartTransaction()
    try:
      db_data.extend(self.ListRow('users', users_dict, 'user_group_assignments',
                                  user_group_assignments_dict,
                                  'forward_zone_permissions',
                                  forward_zone_permissions_dict))

      db_data.extend(self.ListRow('users', users_dict, 'user_group_assignments',
                                  user_group_assignments_dict,
                                  'reverse_range_permissions',
                                  reverse_range_permissions_dict))
      if( not db_data ):
        self.cursor.execute('SELECT access_level FROM users '
                            'WHERE user_name="%s"' % user)
        db_data.extend(self.cursor.fetchall())

        if( db_data ):
          auth_info_dict['user_access_level'] = db_data[0]['access_level']
          return auth_info_dict
        else:
          return {}
    finally:
      self.EndTransaction()

    auth_info_dict['user_access_level'] = db_data[0]['access_level']
    for row in db_data:
      if( row.has_key('forward_zone_permissions_access_right') ):
        if( not row['user_group_assignments_group_name'] in
            auth_info_dict['groups'] ):
          auth_info_dict['groups'].append(
              row['user_group_assignments_group_name'])

        if( not {'zone_name': row['forward_zone_permissions_zone_name'],
                 'access_right': row['forward_zone_permissions_access_right']}
            in (auth_info_dict['forward_zones']) ):
          auth_info_dict['forward_zones'].append(
              {'zone_name': row['forward_zone_permissions_zone_name'],
               'access_right': row['forward_zone_permissions_access_right']})
      elif( row.has_key('reverse_range_permissions_access_right') ):
        if( not row['user_group_assignments_group_name'] in
            auth_info_dict['groups'] ):
          auth_info_dict['groups'].append(
              row['user_group_assignments_group_name'])

        if( not {'cidr_block': row['reverse_range_permissions_cidr_block'],
                 'access_right': row['reverse_range_permissions_access_right']}
            in auth_info_dict['reverse_ranges'] ):
          auth_info_dict['reverse_ranges'].append(
              {'cidr_block': row['reverse_range_permissions_cidr_block'],
               'access_right': row['reverse_range_permissions_access_right']})
      else:
        raise UnexpectedDataError('Row did not contain '
                                  'reverse_range_permissions_access_right or '
                                  'forward_zone_permissions_access_right.')
    return auth_info_dict

  def MakeRow(self, table_name, row_dict):
    """Creates a row in the database using the table name and row dict
    
    Inputs:
      table_name: string of valid table name from table_enumeration
      row_dict: dictionary that coresponds to table_name

    Raises:
      InvalidInputError: Table name not valid
      TransactionError: Must run StartTansaction before inserting

    Outputs:
      int: last insert id
    """
    if( not table_name in table_enumeration.GetValidTables() ):
      raise InvalidInputError('Table name not valid: %s' % table_name)
    if( not self.transaction_init ):
      raise TransactionError('Must run StartTansaction before inserting.')
    if( self.data_validation_instance is None ):
      self.InitDataValidation()
    self.data_validation_instance.ValidateRowDict(table_name, row_dict) 

    column_names = []
    column_assignments = []
    for k in row_dict.iterkeys():
      column_names.append(k)
      column_assignments.append('%s%s%s' % ('%(', k, ')s'))

    query = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name, 
                                                 ','.join(column_names),
                                                 ','.join(column_assignments))
    self.cursor.execute(query, row_dict)
    return self.cursor.lastrowid

  def TableRowCount(self, table_name):
    """Counts the amount of records in a table and returns it.

    Inputs:
      table_name: string of valid table name from table_enumeration

    Raises:
      InvalidInputError: Table name not valid
      TransactionError: Must run StartTansaction before getting row count.

    Outputs:
      int: number of rows found
    """

    if( not table_name in table_enumeration.GetValidTables() ):
      raise InvalidInputError('Table name not valid: %s' % table_name)
    if( not self.transaction_init ):
      raise TransactionError('Must run StartTansaction before getting row '
                             'count.')
    self.cursor.execute('SELECT COUNT(*) FROM %s' % table_name)
    row_count = self.cursor.fetchone()
    return row_count['COUNT(*)']

  def RemoveRow(self, table_name, row_dict):
    """Removes a row in the database using the table name and row dict

    Inputs:
      table_name: string of valid table name from table_enumeration
      row_dict: dictionary that coresponds to table_name

    Raises:
      InvalidInputError: Table name not valid
      TransactionError: Must run StartTansaction before deleting

    Outputs:
      int: number of rows affected
    """
    if( not table_name in table_enumeration.GetValidTables() ):
      raise InvalidInputError('Table name not valid: %s' % table_name)
    if( not self.transaction_init ):
      raise TransactionError('Must run StartTansaction before deleting.')
    if( self.data_validation_instance is None ):
      self.InitDataValidation()
    self.data_validation_instance.ValidateRowDict(table_name, row_dict) 

    where_list = []
    for k in row_dict.iterkeys():
      where_list.append('%s=%s%s%s' % (k, '%(', k, ')s'))

    query = 'DELETE FROM %s WHERE %s' % (table_name, ' AND '.join(where_list))
    self.cursor.execute(query, row_dict)
    return self.cursor.rowcount

  def UpdateRow(self, table_name, search_row_dict, update_row_dict):
    """Updates a row in the database using search and update dictionaries.

    Inputs:
      table_name: string of valid table name from table_enumeration
      search_row_dict: dictionary that coresponds to table_name containing
                       search args
      update_row_dict: dictionary that coresponds to table_name containing
                       update args

    Raises:
      InvalidInputError: Table name not valid
      TransactionError: Must run StartTansaction before inserting

    Outputs:
      int: number of rows affected
    """
    if( not table_name in table_enumeration.GetValidTables() ):
      raise InvalidInputError('Table name not valid: %s' % table_name)
    if( not self.transaction_init ):
      raise TransactionError('Must run StartTansaction before deleting.')
    if( self.data_validation_instance is None ):
      self.InitDataValidation()
    self.data_validation_instance.ValidateRowDict(table_name, search_row_dict,
                                                  none_ok=True)
    self.data_validation_instance.ValidateRowDict(table_name, update_row_dict,
                                                  none_ok=True)
    
    query_updates = []
    query_searches = []
    combined_dict = {}
    for k, v in update_row_dict.iteritems():
      if( v is not None ):
        query_updates.append('%s%s%s%s' % (k, '=%(update_', k, ')s'))
        combined_dict['update_%s' % k] = v

    for k, v in search_row_dict.iteritems():
      if( v is not None ):
        query_searches.append('%s=%s%s%s' % (k, '%(search_', k, ')s'))
        combined_dict['search_%s' % k] = v

    query = 'UPDATE %s SET %s WHERE %s' % (table_name, ','.join(query_updates),
                                           ' AND '.join(query_searches))
    self.cursor.execute(query, combined_dict)
    return self.cursor.rowcount

  def ListRow(self, *args, **kwargs):
    """Lists rows in the database using a dictionary of tables. Then returns 
    the rows found. Joins are auto generated on the fly based on foreign keys
    in the database.

    Inputs:
      args: pairs of string of table name and dict of rows
      kwargs: lock_rows: default False

      example usage: ListRow('users', user_row_dict,
                             'user_group_assignments', user_assign_row_dict,
                             lock_rows=True)

    Raises:
      InvalidInputError: Table name not valid
      TransactionError: Must run StartTansaction before inserting

    Outputs:
      tuple of row dicts consisting of all the tables that were in the input.
      all column names in the db are unique so no colisions occour
        example: ({'user_name': 'sharrell', 'access_level': 10, 
                   'user_group_assignments_group_name: 'cs',
                   'user_group_assignments_user_name: 'sharrell'},
                  {'user_name': 'sharrell', 'access_level': 10, 
                   'user_group_assignments_group_name: 'eas',
                   'user_group_assignments_user_name: 'sharrell'})
    """
    if( not self.transaction_init ):
      raise TransactionError('Must run StartTansaction before getting data.')
    if( self.data_validation_instance is None ):
      self.InitDataValidation()

    valid_tables = table_enumeration.GetValidTables()
    tables = {}
    table_names = []
    lock_rows = False
    if( kwargs ):
      if( 'lock_rows' in kwargs ):
        lock_rows=kwargs['lock_rows']
        del kwargs['lock_rows']
      if( kwargs ):
        raise InvalidInputError('Found unknown option(s): %s' % kwargs.keys())

    if( not args ):
      raise InvalidInputError('No args given, must at least have on pair of '
                              'table name and row dict')
    if( len(args) % 2 ):
      raise InvalidInputError('Number of unnamed args is not even. Args '
                              'should be entered in pairs of table name and '
                              'row dict.')
    count = 0
    for arg in args:
      count += 1
      if( count % 2 ):
        if( not arg in valid_tables ):
          raise InvalidInputError('Table name not valid: %s' % arg)
        current_table_name = arg
      else:
        # do checking in validate row dict to check if it is a dict
        self.data_validation_instance.ValidateRowDict(current_table_name, arg,
                                                      none_ok=True,
                                                      all_none_ok=True)
        tables[current_table_name] = arg
        table_names.append(current_table_name)
     
    query_where = []
    if( len(tables) > 1 ):
      if( not self.foreign_keys ):
        self.cursor.execute('select table_name, column_name, '
                            'referenced_table_name, referenced_column_name '
                            'from information_schema.key_column_usage where '
                            'referenced_table_name is not null')
        self.foreign_keys = self.cursor.fetchall()

      for key in self.foreign_keys:
        if( key['table_name'] in table_names and
            key['referenced_table_name'] in table_names ):
          query_where.append('(%(table_name)s.%(column_name)s='
                             '%(referenced_table_name)s.'
                             '%(referenced_column_name)s)' % key)

      if( not query_where ):
        raise InvalidInputError('Multiple tables were passed in but no joins '
                                'were found')

    column_names = []
    search_dict = {}
    for table_name, row_dict in tables.iteritems():
      for k, v in row_dict.iteritems():
        column_names.append('%s.%s' % (table_name, k))
        if( v is not None ):
          search_dict[k] = v
          query_where.append('%s%s%s%s' % (k, '=%(', k, ')s'))

    query_end = ''
    if( query_where ):
      query_end = 'WHERE %s' % ' AND '.join(query_where)
    if( lock_rows ):
      query_end = '%s FOR UPDATE' % query_end

    query = 'SELECT %s FROM %s %s' % (','.join(column_names),
                                      ','.join(table_names),
                                      query_end)
    self.cursor.execute(query, search_dict)
    return self.cursor.fetchall()

  def GetEmptyRowDict(self, table_name):
    """Gives a dict that has all the members needed to interact with the
    the given table using the Make/Remove/ListRow functions.

    Inputs:
      table_name: string of valid table name from table_enumeration

    Raises:
      InvalidInputError: Table name not valid

    Outputs:
      dictionary: of empty row for specificed table.
        example acls dict:
        {'acl_name': None
         'acl_range_allowed: None,
         'acl_cidr_block': None }
    """
    row_dict = table_enumeration.GetRowDict(table_name)
    if( not row_dict ):
      raise InvalidInputError('Table name not valid: %s' % table_name)
    for k in row_dict.iterkeys():
      row_dict[k] = None
    return row_dict

  # Not sure this is needed, buuuuut.
  def GetValidTables(self):
    """Export this function to the top level of the db_access stuff so
    it can be used without importing un-needed classes.

    Outputs:
      list: valid table names
    """
    table_enumeration.GetValidTables()

  def GetRecordArgsDict(self, record_type):
    """Get args for a specific record type from the db and shove them into
    a dictionary.

    Inputs:
      record_type: string of record type

    Outputs:
      dictionary: keyed by argument name with values of data type of that arg
        example: {'mail_host': 'Hostname'
                  'priority': 'UnsignedInt'}
    """
    search_record_arguments_dict = self.GetEmptyRowDict('record_arguments')
    search_record_arguments_dict['record_arguments_type'] = record_type

    self.StartTransaction()
    try:
      record_arguments = self.ListRow('record_arguments',
                                      search_record_arguments_dict)
    finally:
      self.EndTransaction()

    record_arguments_dict = {}
    if( not record_arguments ):
      raise InvalidInputError('Unknown record type: %s' % record_type)
    for record_argument in record_arguments:
      record_arguments_dict[record_argument['argument_name']] = (
          record_argument['argument_data_type'])
    
    return record_arguments_dict

  def GetEmptyRecordArgsDict(self, record_type):
    """Gets empty args dict for a specific record type

    Inputs:
      record_type: string of record type

    Outputs:
      dictionary: keyed by argument name with values of None
        example: {'mail_host': None
                  'priority': None}
    """

    args_dict = self.GetRecordArgsDict(record_type)
    for k in args_dict.iterkeys():
      args_dict[k] = None

    return args_dict

  def ValidateRecordArgsDict(self, record_type, record_args_dict,
                             none_ok=False):
    """Type checks record args dynamically.

    Inputs:
      record_type: string of record_type
      record_args_dict: dictionary for args keyed by arg name.
                        a filled out dict from GetEmptyRecordArgsDict()
      none_ok: boolean of if None types should be acepted.

    Raises:
      InvalidInputError: dict for record type should have these keys
      UnexpectedDataError: Invalid data type
    """
    record_type_dict = self.GetRecordArgsDict(record_type)
    if( not set(record_type_dict.keys()) == set(record_args_dict.keys()) ):
      raise InvalidInputError('dict for record type %s should have these '
                              'keys: %s' % (record_type, record_type_dict))
    if( self.data_validation_instance is None ):
      self.InitDataValidation()
    
    data_validation_methods = dir(data_validation.DataValidation([]))
    for record_arg_name in record_args_dict.keys():
      if( not 'is%s' % record_type_dict[record_arg_name] in
          data_validation_methods ):
        raise MissingDataTypeError('No function to check data type %s' %
                                   record_type_dict[record_arg_name])
      if( none_ok and record_args_dict[record_arg_name] is None ):
        continue

      if( not getattr(self.data_validation_instance, 'is%s' %
          record_type_dict[record_arg_name])(
              record_args_dict[record_arg_name]) ):
        raise UnexpectedDataError('Invalid data type %s: %s' %
                                  (record_type_dict[record_arg_name],
                                   record_args_dict[record_arg_name]))
  def ListTableNames(self):
    """Lists all tables in the database.

    Outputs:
      List: List of tables
    """
    query = 'SHOW TABLES'
    self.cursor.execute(query)
    tables = self.cursor.fetchall()
    table_list = []
    for table_dict in tables:
      for table in table_dict:
        table_list.append(table_dict[table])
    return table_list

# vi: set ai aw sw=2:
