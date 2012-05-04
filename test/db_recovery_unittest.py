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
__version__ = '0.16'


import datetime
import unittest
import time
import MySQLdb
import os
import sys
import threading

from roster_core import audit_log
import roster_config_manager
import roster_core
from roster_config_manager import db_recovery
from roster_config_manager import tree_exporter
from roster_core import data_validation
from roster_core import core


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'

class StdOutStream():
  """Std out redefined"""
  def __init__(self):
    """Appends stdout to stdout array
    
       Inputs:
         text: String of stdout
    """
    self.stdout = []

  def write(self, text):
    """Appends stdout to stdout array
    
    Inputs:
      text: String of stdout
    """
    self.stdout.append(text)

  def flush(self):
    """Flushes stdout array and outputs string of contents

    Outputs:
      String: String of stdout
    """
    std_array = self.stdout
    self.stdout = []
    return ''.join(std_array)

class TestdbAccess(unittest.TestCase):

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
    self.db_recovery_instance = db_recovery.Recover(u'sharrell',
                                                    self.config_instance)
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
        u'soa', u'@', u'university.edu',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 2, u'refresh_seconds': 5, 'target': u'@',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5}])
    self.core_instance.MakeDnsServer(u'dns1')
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()

    self.core_instance.MakeRecord(
        u'mx', u'department', u'university.edu',
        {u'priority': 20, u'mail_server': u'smtp.university.edu.'}, ttl=10)

    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 3, u'refresh_seconds': 5, 'target': u'@',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
         {'target': u'department', 'ttl': 10, u'priority': 20,
          'record_type': u'mx', 'view_name': u'any', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'mail_server': u'smtp.university.edu.'}])

    old_stdout = sys.stdout
    sys.stdout = StdOutStream()
    self.db_recovery_instance.PushBackup(9)
    self.assertEqual(sys.stdout.flush(),
                     'Loading database from backup with ID 9\n')
    sys.stdout = old_stdout

    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 2, u'refresh_seconds': 5, 'target': u'@',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5}])

  def testRunAuditStep(self):
    self.core_instance.MakeView(u'test_view')
    self.assertEqual(self.core_instance.ListViews(), {u'test_view': ''})
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.assertEqual(
        self.core_instance.ListZones(),
        {u'university.edu':
            {u'test_view': {'zone_type': u'master', 'zone_options': '',
                            'zone_origin': u'university.edu.'},
             u'any': {'zone_type': u'master', 'zone_options': '',
                      'zone_origin': u'university.edu.'}}})
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.RemoveView(u'test_view')
    self.core_instance.RemoveView(u'test_view2')
    self.core_instance.RemoveZone(u'university.edu')
    self.assertEqual(self.core_instance.ListViews(), {})
    self.assertEqual(self.core_instance.ListZones(), {})
    old_stdout = sys.stdout
    sys.stdout = StdOutStream()
    self.db_recovery_instance.RunAuditStep(1)
    self.db_recovery_instance.RunAuditStep(2)
    self.assertEqual(
        sys.stdout.flush(),
        u"Replaying action with id 1: MakeView\n"
         "with arguments: [u'test_view', None]\n"
         "Replaying action with id 2: MakeZone\n"
         "with arguments: [u'university.edu', u'master', "
         "u'university.edu.', u'test_view', None, True]\n")
    sys.stdout = old_stdout
    self.assertEqual(self.core_instance.ListViews(), {u'test_view': ''})
    self.assertEqual(
        self.core_instance.ListZones(),
        {u'university.edu':
            {u'test_view': {'zone_type': u'master', 'zone_options': '',
                            'zone_origin': u'university.edu.'},
             u'any': {'zone_type': u'master', 'zone_options': '',
                      'zone_origin': u'university.edu.'}}})
  def testRunAuditRange(self):
    self.assertFalse(self.core_instance.ListRecords())
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'@', u'university.edu',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(), 
        [{u'serial_number': 2, u'refresh_seconds': 5, 'target': u'@',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5}])
    self.core_instance.MakeDnsServer(u'dns1')
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()

    self.core_instance.MakeView(u'test_view2')
    self.core_instance.MakeView(u'bad_view')
    old_stdout = sys.stdout
    sys.stdout = StdOutStream()
    self.db_recovery_instance.RunAuditRange(10)
    self.assertEqual(sys.stdout.flush(),
        'Loading database from backup with ID 9\n')
    sys.stdout = old_stdout
    self.assertEqual(self.core_instance.ListRecords(), 
        [{u'serial_number': 2, u'refresh_seconds': 5, 'target': u'@',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5}])
    self.assertEqual(self.core_instance.ListViews(), {u'test_view': ''})
    self.tree_exporter_instance.ExportAllBindTrees()
    old_stdout = sys.stdout
    sys.stdout = StdOutStream()
    self.db_recovery_instance.RunAuditStep(12)
    self.assertEqual(sys.stdout.flush(),
        u'Not replaying action with id 12, action not allowed.\n')
    sys.stdout = old_stdout

    log_instance = audit_log.AuditLog(log_to_syslog=False, log_to_db=True,
                                           db_instance=self.db_instance)

    log_id = log_instance.LogAction(
        u'sharrell', u'failed', {u'audit_args': {u'arg1': 1},
        u'replay_args': [1]}, 0)
    old_stdout = sys.stdout
    sys.stdout = StdOutStream()
    self.db_recovery_instance.RunAuditStep(log_id)
    self.assertEqual(sys.stdout.flush(),
        'Not replaying action with id 13, action was unsuccessful.\n')
    sys.stdout = old_stdout

if( __name__ == '__main__' ):
    unittest.main()
