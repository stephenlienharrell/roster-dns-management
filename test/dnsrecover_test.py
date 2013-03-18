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

"""Regression test for dnsrecover

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import subprocess
import shlex
import os
import sys
import socket
import threading
import time
import getpass
import shutil

import unittest
from roster_core import audit_log
from roster_config_manager import tree_exporter
from roster_config_manager import db_recovery
import roster_core
import roster_server
from roster_user_tools import roster_client_lib

USER_CONFIG = 'test_data/roster.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-config-manager/scripts/dnsrecover'
TESTDIR = u'%s/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/named/' % os.getcwd()
TEST_DNS_SERVER = u'localhost'
SSH_USER = unicode(getpass.getuser())

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

class TestDnsRecover(unittest.TestCase):

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
    self.tree_exporter_instance = tree_exporter.BindTreeExport(CONFIG_FILE)
    self.db_instance = db_instance

    if( os.path.exists(self.tree_exporter_instance.backup_dir) ):
      shutil.rmtree(self.tree_exporter_instance.backup_dir)

  def testFullRecovery(self):
    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')
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
    self.core_instance.MakeDnsServer(u'dns1', SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1', u'set1')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'#options')

    self.tree_exporter_instance.ExportAllBindTrees()
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.MakeView(u'bad_view')

    command = shlex.split(str('python %s -i 10 -u %s --config-file %s' % (
                               EXEC, USERNAME, USER_CONFIG)))
    output = subprocess.Popen(command, stdout=subprocess.PIPE, 
        stdin=subprocess.PIPE)
    self.assertEqual(output.communicate('y\n'), 
        ("Loading database from backup with ID 12\n"
         "%s\n"
         "Would you like to run dnstreeexport now? [y/n] \n"
         "Running dnstreeexport\n"
         "dnstreeexport has completed successfully\n" % (
            db_recovery.WARNING_STRING), None))

    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 2, u'refresh_seconds': 5, 'target': u'@',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'university.edu',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5}])
    self.assertEqual(self.core_instance.ListViews(), [u'test_view'])

    command = shlex.split(str('python %s -i 12 --single -u %s --config-file %s' % (
                               EXEC, USERNAME, USER_CONFIG)))
    output = subprocess.Popen(command, stdout=subprocess.PIPE, 
        stdin=subprocess.PIPE)
    self.assertEqual(output.communicate('n\n'),
        ('Not replaying action with id 12, action not allowed.\n'
         '%s\n'
         'Would you like to run dnstreeexport now? [y/n] ' % (
            db_recovery.WARNING_STRING), None))

    log_instance = audit_log.AuditLog(log_to_syslog=False, log_to_db=True,
                                           db_instance=self.db_instance)
    log_id = log_instance.LogAction(
        u'sharrell', u'failed', {u'audit_args': {u'arg1': 1},
        u'replay_args': [1]}, 0)
    command = shlex.split(str('python %s -i %s --single '
                              '-u %s --config-file %s' % (
                               EXEC, log_id, USERNAME, USER_CONFIG)))
    output = subprocess.Popen(command, stdout=subprocess.PIPE, 
        stdin=subprocess.PIPE)
    self.assertEqual(output.communicate('n\n'),
        ('Not replaying action with id 16, action was unsuccessful.\n'
         '%s\n'
         'Would you like to run dnstreeexport now? [y/n] ' % (
            db_recovery.WARNING_STRING), None))

  def testRunAuditStep(self):
    for zone in self.core_instance.ListZones():
        self.core_instance.RemoveZone(zone)
    self.core_instance.MakeView(u'test_view')
    self.assertEqual(self.core_instance.ListViews(), [u'test_view'])
    self.core_instance.MakeZone(u'university.edu', u'master',
                                u'university.edu.', view_name=u'test_view')
    self.assertEqual(
        self.core_instance.ListZones(),
        {u'university.edu':
            {u'test_view': {'zone_type': u'master', 'zone_options': u'',
                            'zone_origin': u'university.edu.'},
             u'any': {'zone_type': u'master', 'zone_options': u'',
                      'zone_origin': u'university.edu.'}}})
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.RemoveView(u'test_view')
    self.core_instance.RemoveView(u'test_view2')
    self.core_instance.RemoveZone(u'university.edu')
    self.assertEqual(self.core_instance.ListViews(), [])
    self.assertEqual(self.core_instance.ListZones(), {})
    command = shlex.split(str('python %s -i 4 --single '
                              '-u %s --config-file %s' % (
                              EXEC, USERNAME, USER_CONFIG)))
    output = subprocess.Popen(command, stdout=subprocess.PIPE, 
                              stdin=subprocess.PIPE)
    self.assertEqual(output.communicate('n\n'),
        ("Replaying action with id 4: MakeView\n"
         "with arguments: [u'test_view']\n"
         "%s\n"
         "Would you like to run dnstreeexport now? [y/n] " % (
            db_recovery.WARNING_STRING), None))
    self.assertEqual(self.core_instance.ListViews(), [u'test_view'])
    command = shlex.split(str('python %s -i 5 --single '
                              '-u %s --config-file %s' % (
                              EXEC, USERNAME, USER_CONFIG)))
    output = subprocess.Popen(command, stdout=subprocess.PIPE, 
                              stdin=subprocess.PIPE)
    #Also testing invalid input response for dnsrecover
    self.assertEqual(output.communicate('x\nn\n'),
        ("Replaying action with id 5: MakeZone\n"
         "with arguments: [u'university.edu', u'master', u'university.edu.', "
         "u'test_view', None, True]\n"
         "%s\n"
         "Would you like to run dnstreeexport now? [y/n] " #User inputs x
         "Would you like to run dnstreeexport now? [y/n] " % (
            db_recovery.WARNING_STRING), None))
    self.assertEqual(self.core_instance.ListViews(), [u'test_view'])
    self.assertEqual(
        self.core_instance.ListZones(),
        {u'university.edu':
            {u'test_view': {'zone_type': u'master', 'zone_options': u'',
                            'zone_origin': u'university.edu.'},
             u'any': {'zone_type': u'master', 'zone_options': u'',
                      'zone_origin': u'university.edu.'}}})

  def testErrors(self):
    output = os.popen('python %s --single '
                      '-u %s --config-file %s' % (
                          EXEC, USERNAME, USER_CONFIG))
    self.assertEqual(output.read(),
        'ERROR: An audit log ID must be specified to recover Roster.\n')
    output.close()

  def testPreventDuplicateRecordBug(self):
    for zone in self.core_instance.ListZones():
        self.core_instance.RemoveZone(zone)
    self.core_instance.MakeDnsServer(TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServerSet(u'set1')
    self.core_instance.MakeDnsServerSetAssignments(TEST_DNS_SERVER, u'set1')
    self.core_instance.MakeNamedConfGlobalOption(u'set1', u'options { pid-file "test_data/named.pid"; };')

    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeDnsServerSetViewAssignments(u'test_view', 1, u'set1')

    self.core_instance.MakeZone(u'test_zone', u'master', u'university.lcl.', u'test_view')
    self.core_instance.MakeRecord(u'soa', u'@', u'test_zone', {u'name_server': u'ns.university.lcl.', u'admin_email': '%s.university.lcl.' % USERNAME,
        u'refresh_seconds': 5, u'expiry_seconds': 5, u'minimum_seconds': 5, u'retry_seconds': 5, u'serial_number': 999}, u'test_view')
    self.core_instance.MakeRecord(u'ns', u'@', u'test_zone', {u'name_server': u'ns.university.lcl.'}, u'test_view')

    # Extracted as ID 13
    self.tree_exporter_instance.ExportAllBindTrees()

    self.core_instance.MakeRecord(u'a', u'record02', u'test_zone', {u'assignment_ip': u'192.168.1.2'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record03', u'test_zone', {u'assignment_ip': u'192.168.1.3'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record04', u'test_zone', {u'assignment_ip': u'192.168.1.4'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record05', u'test_zone', {u'assignment_ip': u'192.168.1.5'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record06', u'test_zone', {u'assignment_ip': u'192.168.1.6'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record07', u'test_zone', {u'assignment_ip': u'192.168.1.7'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record08', u'test_zone', {u'assignment_ip': u'192.168.1.8'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record09', u'test_zone', {u'assignment_ip': u'192.168.1.9'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'record10', u'test_zone', {u'assignment_ip': u'192.168.1.10'}, u'test_view')

    # Extracted as ID 23
    self.tree_exporter_instance.ExportAllBindTrees()

    # Recover to audit id 19
    output = os.popen('python %s --config-file %s -u %s -i 19 --auto-export' % (EXEC, 
        CONFIG_FILE, USERNAME))
    lines = output.read().split('\n')
    output.close()

    self.assertEqual(lines, ['Loading database from backup with ID 13',
        'Replaying action with id 14: MakeRecord',
        "with arguments: [u'a', u'record02', u'test_zone', {u'assignment_ip': u'192.168.1.2'}, u'test_view', None]",
        'Replaying action with id 15: MakeRecord',
        "with arguments: [u'a', u'record03', u'test_zone', {u'assignment_ip': u'192.168.1.3'}, u'test_view', None]",
        'Replaying action with id 16: MakeRecord',
        "with arguments: [u'a', u'record04', u'test_zone', {u'assignment_ip': u'192.168.1.4'}, u'test_view', None]",
        'Replaying action with id 17: MakeRecord',
        "with arguments: [u'a', u'record05', u'test_zone', {u'assignment_ip': u'192.168.1.5'}, u'test_view', None]",
        'Replaying action with id 18: MakeRecord',
        "with arguments: [u'a', u'record06', u'test_zone', {u'assignment_ip': u'192.168.1.6'}, u'test_view', None]",
        '',
        'Running dnstreeexport',
        'dnstreeexport has completed successfully',
        ''])

    # Check to see if we only have the records we want now
    records = self.core_instance.ListRecords(record_type=u'a')
    self.assertEqual(records, [
        {'target': u'record02', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': USERNAME, 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.2'},
        {'target': u'record03', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': USERNAME, 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.3'},
        {'target': u'record04', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': USERNAME, 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.4'},
        {'target': u'record05', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': USERNAME, 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.5'},
        {'target': u'record06', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': USERNAME, 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.6'}])
    # Records 'record07-10' are no longer here.  Perfect, this is what we want.

    # Making some more records
    self.core_instance.MakeRecord(u'a', u'roster01', u'test_zone', {u'assignment_ip': u'192.168.2.1'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster02', u'test_zone', {u'assignment_ip': u'192.168.2.2'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster03', u'test_zone', {u'assignment_ip': u'192.168.2.3'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster04', u'test_zone', {u'assignment_ip': u'192.168.2.4'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster05', u'test_zone', {u'assignment_ip': u'192.168.2.5'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster06', u'test_zone', {u'assignment_ip': u'192.168.2.6'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster07', u'test_zone', {u'assignment_ip': u'192.168.2.7'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster08', u'test_zone', {u'assignment_ip': u'192.168.2.8'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster09', u'test_zone', {u'assignment_ip': u'192.168.2.9'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster10', u'test_zone', {u'assignment_ip': u'192.168.2.10'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster11', u'test_zone', {u'assignment_ip': u'192.168.2.11'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster12', u'test_zone', {u'assignment_ip': u'192.168.2.12'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster13', u'test_zone', {u'assignment_ip': u'192.168.2.13'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster14', u'test_zone', {u'assignment_ip': u'192.168.2.14'}, u'test_view')
    self.core_instance.MakeRecord(u'a', u'roster15', u'test_zone', {u'assignment_ip': u'192.168.2.15'}, u'test_view')

    # Only wanted the first 6 of those
    # Recover to audit id 35
    output = os.popen('python %s --config-file %s -u %s -i 35 --auto-export' % (EXEC, 
        CONFIG_FILE, USERNAME))
    lines = output.read().split('\n')
    output.close()

    # Confirm output (will change when dnsrecover changes)
    self.assertEqual(lines, ['Loading database from backup with ID 29',
        'Replaying action with id 30: MakeRecord',
        "with arguments: [u'a', u'roster01', u'test_zone', {u'assignment_ip': u'192.168.2.1'}, u'test_view', None]",
        'Replaying action with id 31: MakeRecord',
        "with arguments: [u'a', u'roster02', u'test_zone', {u'assignment_ip': u'192.168.2.2'}, u'test_view', None]",
        'Replaying action with id 32: MakeRecord',
        "with arguments: [u'a', u'roster03', u'test_zone', {u'assignment_ip': u'192.168.2.3'}, u'test_view', None]",
        'Replaying action with id 33: MakeRecord',
        "with arguments: [u'a', u'roster04', u'test_zone', {u'assignment_ip': u'192.168.2.4'}, u'test_view', None]",
        'Replaying action with id 34: MakeRecord',
        "with arguments: [u'a', u'roster05', u'test_zone', {u'assignment_ip': u'192.168.2.5'}, u'test_view', None]",
        '',
        'Running dnstreeexport',
        'dnstreeexport has completed successfully',
        ''])

    # Checking that proper records are in database (currently breaks)
    records = self.core_instance.ListRecords(record_type=u'a')
    self.assertEqual(records, [{'target': u'record02', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.2'},
        {'target': u'record03', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.3'},
        {'target': u'record04', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.4'},
        {'target': u'record05', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.5'},
        {'target': u'record06', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.6'},
        {'target': u'roster01', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.2.1'},
        {'target': u'roster02', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.2.2'},
        {'target': u'roster03', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.2.3'},
        {'target': u'roster04', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.2.4'},
        {'target': u'roster05', 'ttl': 3600, 'record_type': u'a', 'view_name': u'test_view', 'last_user': u'sharrell', 'zone_name': u'test_zone', u'assignment_ip': u'192.168.2.5'}])

if( __name__ == '__main__' ):
      unittest.main()
