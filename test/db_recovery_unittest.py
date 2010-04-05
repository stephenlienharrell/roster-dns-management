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

"""Unittest for db_recovery.py

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

import roster_config_manager
import roster_core
from roster_config_manager import db_recovery
from roster_config_manager import tree_exporter
from roster_core import data_validation
from roster_core import core


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'


class TestdbAccess(unittest.TestCase):

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
    self.db_recovery_instance = db_recovery.Recover(self.config_instance)
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    self.db_instance = db_instance

  def tearDown(self):
    for fname in os.listdir('.'):
      if( fname.endswith('.bz2') ):
        os.remove(fname)

  def testPushBackup(self):
    self.assertFalse(self.core_instance.ListRecords())
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'university.edu',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(), 
        [{u'serial_number': 2, u'refresh_seconds': 5, 'target': u'soa1',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5}])
    self.tree_exporter_instance.ExportAllBindTrees()

    self.core_instance.MakeRecord(
        u'mx', u'university.edu.', u'university.edu',
        {u'priority': 20, u'mail_server': u'smtp.university.edu.'}, ttl=10)

    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
         {'target': u'university.edu.', 'ttl': 10, u'priority': 20,
          'record_type': u'mx', 'view_name': u'any', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'mail_server': u'smtp.university.edu.'}])

    self.db_recovery_instance.PushBackup(4)

    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 2, u'refresh_seconds': 5, 'target': u'soa1',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5}])

if( __name__ == '__main__' ):
    unittest.main()
