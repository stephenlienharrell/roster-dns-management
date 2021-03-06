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
# SERVICES: LOSS OF USE, DATA, OR PROFITS: OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Regression test for dnslsauditlog

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import cPickle
import os
import sys
import socket
import threading
import time
import getpass

import unittest
import roster_core
import roster_server
from roster_user_tools import roster_client_lib

USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-user-tools/scripts/dnslsauditlog'

class options(object):
  password = u'test'
  username = u'sharrell'
  server = None
  ldap = u'ldaps://ldap.cs.university.edu:636'
  credfile = CREDFILE
  view_name = None
  ip_address = None
  target = u'machine1'
  ttl = 64

class DaemonThread(threading.Thread):
  def __init__(self, config_instance, port):
    threading.Thread.__init__(self)
    self.config_instance = config_instance
    self.port = port
    self.daemon_instance = None

  def run(self):
    self.daemon_instance = roster_server.Server(self.config_instance, KEYFILE,
                                                CERTFILE)
    self.daemon_instance.Serve(port=self.port)

class Testdnslsauditlog(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_thread = DaemonThread(self.config_instance, self.port)
    self.daemon_thread.daemon = True
    self.daemon_thread.start()
    self.db_instance = db_instance
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.core_helper_instance = roster_core.CoreHelpers(self.core_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testListAuditLog(self):
    audit_dict = {'audit_log_id': None, 'audit_log_user_name': None,
                  'action': None, 'data': None, 'success': None,
                  'audit_log_timestamp': None}

    self.core_instance.MakeACL(u'acl1', u'192.168.1/24')
    audit_dict['data'] = cPickle.dumps({'replay_args':
                                            [u'acl1', u'192.168.1/24'],
                                        'audit_args':
                                            {'cidr_block': u'192.168.1/24',
                                             'acl_name': u'acl1'}})

    self.db_instance.StartTransaction()
    try:
      entry1 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry1_timestamp = str(entry1[0]['audit_log_timestamp']).replace(' ', 'T')

    time.sleep(2)
    self.core_instance.MakeACL(u'acl2', u'10.10.1/24')

    audit_dict['data'] = cPickle.dumps({'replay_args':
                                            [u'acl2', u'10.10.1/24'],
                                        'audit_args':
                                            {'cidr_block': u'10.10.1/24',
                                             'acl_name': u'acl2'}})
    self.db_instance.StartTransaction()
    try:
      entry2 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry2_timestamp = str(entry2[0]['audit_log_timestamp']).replace(' ', 'T')

    self.core_instance.MakeView(u'test_view')

    audit_dict['data'] = cPickle.dumps({'replay_args':
                                            [u'test_view'],
                                        'audit_args':
                                            {'view_name': u'test_view'}})
    self.db_instance.StartTransaction()
    try:
      entry3 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry3_timestamp = str(entry3[0]['audit_log_timestamp']).replace(' ', 'T')

    command = os.popen('python %s '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        "ID Action   Timestamp           Username Success Data\n"
        "-----------------------------------------------------\n"
        "1  MakeACL  %s sharrell 1       "
            "{'cidr_block': u'192.168.1/24', 'acl_name': u'acl1'}\n"
        "2  MakeACL  %s sharrell 1       "
            "{'cidr_block': u'10.10.1/24', 'acl_name': u'acl2'}\n"
        "3  MakeView %s sharrell 1       "
            "{'view_name': u'test_view'}\n\n" % (
            entry1_timestamp, entry2_timestamp, entry3_timestamp))
    command.close()
    command = os.popen('python %s -b %s -e %s '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, entry2_timestamp, entry3_timestamp,
                                  USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        "ID Action   Timestamp           Username Success Data\n"
        "-----------------------------------------------------\n"
        "2  MakeACL  %s sharrell 1       "
            "{'cidr_block': u'10.10.1/24', 'acl_name': u'acl2'}\n"
        "3  MakeView %s sharrell 1       "
          "{'view_name': u'test_view'}\n\n" % (
          entry2_timestamp, entry3_timestamp))
    command.close()
    command = os.popen('python %s -a MakeACL '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        "ID Action  Timestamp           Username Success Data\n"
        "----------------------------------------------------\n"
        "1  MakeACL %s sharrell 1       "
            "{'cidr_block': u'192.168.1/24', 'acl_name': u'acl1'}\n"
        "2  MakeACL %s sharrell 1       "
            "{'cidr_block': u'10.10.1/24', 'acl_name': u'acl2'}\n\n" % (
              entry1_timestamp, entry2_timestamp))
    command.close()
    command = os.popen('python %s -a MakeACL --success 0 '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        'ID Action Timestamp Username Success Data\n'
        '-----------------------------------------\n\n')
    command.close()
    command = os.popen('python %s -U sharrell '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(
        command.read(),
        "ID Action   Timestamp           Username Success Data\n"
        "-----------------------------------------------------\n"
        "1  MakeACL  %s sharrell 1       "
            "{'cidr_block': u'192.168.1/24', 'acl_name': u'acl1'}\n"
        "2  MakeACL  %s sharrell 1       "
            "{'cidr_block': u'10.10.1/24', 'acl_name': u'acl2'}\n"
        "3  MakeView %s sharrell 1       "
            "{'view_name': u'test_view'}\n\n" % (
            entry1_timestamp, entry2_timestamp, entry3_timestamp))
    command.close()
    
    self.core_instance.MakeZone(u'forward_zone', u'forward', u'university.lcl.', view_name=u'test_view')
    audit_dict['data'] = None
    audit_dict['action'] = u'MakeZone'
    self.db_instance.StartTransaction()
    try:
      entry4 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry4_timestamp = str(entry4[0]['audit_log_timestamp']).replace(' ', 'T')

    self.core_helper_instance.ProcessRecordsBatch(add_records = \
        [{'record_ttl': 3600, 'record_type': u'soa', 'records_id': 19, 'record_target': u'@', 'record_last_user': u'sharrell', 'record_view_dependency': u'test_view_dep', 'record_zone_name': u'forward_zone', 'record_arguments': {u'refresh_seconds': 5, u'expiry_seconds': 5, u'name_server': u'ns.university.lcl.', u'minimum_seconds': 5, u'retry_seconds': 5, u'serial_number': 999, u'admin_email': u'admin.university.lcl.'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 20, 'record_target': u'record20', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.20'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 21, 'record_target': u'record21', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.21'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 22, 'record_target': u'record22', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.22'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 23, 'record_target': u'record23', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.23'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 24, 'record_target': u'record24', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.24'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 25, 'record_target': u'record25', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.25'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 26, 'record_target': u'record26', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.26'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 27, 'record_target': u'record27', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.27'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 28, 'record_target': u'record28', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.28'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 29, 'record_target': u'record29', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.29'}},
        {'record_ttl': 3600, 'record_type': u'a', 'records_id': 30, 'record_target': u'record30', 'record_last_user': u'sharrell', 'record_view_dependency': u'any', 'record_zone_name': u'forward_zone', 'record_arguments': {u'assignment_ip': u'192.168.1.30'}}])
    audit_dict['action'] = u'ProcessRecordsBatch'
    self.db_instance.StartTransaction()
    try:
      entry5 = self.db_instance.ListRow('audit_log', audit_dict)
    finally:
      self.db_instance.EndTransaction()
    entry5_timestamp = str(entry5[0]['audit_log_timestamp']).replace(' ', 'T')

    command = os.popen('python %s -U sharrell '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        "ID Action              Timestamp           Username Success Data\n"
        "----------------------------------------------------------------\n"
        "1  MakeACL             %s sharrell 1       {'cidr_block': u'192.168.1/24', 'acl_name': u'acl1'}\n"
        "2  MakeACL             %s sharrell 1       {'cidr_block': u'10.10.1/24', 'acl_name': u'acl2'}\n"
        "3  MakeView            %s sharrell 1       {'view_name': u'test_view'}\n"
        "4  MakeZone            %s sharrell 1       {'zone_options': None, 'make_any': True, 'view_name': u'test_view', 'zone_type': u'forward', 'zone_name': u'forward_zone', 'zone_origin': u'university.lcl.'}\n"
        "5  ProcessRecordsBatch %s sharrell 1       {'add_records': [{'record_ttl': 3600, 'record_arguments': {u'refresh_seconds': 5, u'expiry_seconds': 5, u'name_server': u'ns.university.lcl.', u'minimum_seconds': 5, u'retry_seconds': 5, u'serial_number': 999, u'admin_email': u'admin.university.lcl.'}, 'record_type': u'soa', 'records_id': 19, 'record_target': u'@', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'test_view_dep'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.20'}, 'record_type': u'a', 'records_id': 20, 'record_target': u'record20', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.21'}, 'record_type': u'a', 'records_id': 21, 'record_target': u'record21', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.22'}, 'record_type': u'a', 'records_id': 22, 'record_target': u'record22', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.23'}, 'record_type': u'a', 'records_id': 23, 'record_target': u'record23', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.24'}, 'record_type': u'a', 'records_id': 24, 'record_target': u'record24', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.25'}, 'record_type': u'a', 'records_id': 25, 'record_target': u'record25', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.26'}, 'record_type': u'a', 'records_id': 26, 'record_target': u'record26', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.27'}, 'record_type': u'a', 'records_id': 27, 'record_target': u'record27', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.28'}, 'record_type': u'a', 'records_id': 28, 'record_target': u'record28', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, "
            "{'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.29'}, 'record_type': u'a', 'records_id': 29, 'record_target': u'record29', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}, {'record_ttl': 3600, 'record_arguments': {u'assignment_ip': u'192.168.1.30'}, 'record_type': u'a', 'records_id': 30, 'record_target': u'record30', 'record_zone_name': u'forward_zone', 'record_last_user': u'sharrell', 'record_view_dependency': u'any'}], 'delete_records': [], 'zone_import': False}\n\n" % (entry1_timestamp,
            entry2_timestamp, entry3_timestamp, entry4_timestamp, entry5_timestamp))

    command = os.popen('python %s -U sharrell '
                       '-u %s -p %s --config-file %s -s %s --omit-data '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        "ID Action              Timestamp           Username Success\n"
        "-----------------------------------------------------------\n"
        "1  MakeACL             %s sharrell 1\n"
        "2  MakeACL             %s sharrell 1\n"
        "3  MakeView            %s sharrell 1\n"
        "4  MakeZone            %s sharrell 1\n"
        "5  ProcessRecordsBatch %s sharrell 1\n\n" % ( entry1_timestamp,
            entry2_timestamp, entry3_timestamp, entry4_timestamp, entry5_timestamp))
    command.close()

  def testErrors(self):
    command = os.popen('python %s --success 2 '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: --success must be a 1 or 0\n')
    command = os.popen('python %s -e time1 -b time0 '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: Improperly formatted timestamps.\n')
    command.close()
    command = os.popen('python %s -e tTime1 -b tTime0 '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: Improperly formatted timestamps.\n')
    command.close()
    command = os.popen('python %s -U sharrell -e time '
                       '-u %s -p %s --config-file %s -s %s '
                       '-c %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name, CREDFILE))
    self.assertEqual(command.read(),
        'CLIENT ERROR: -b/--begin-time and -e/--end-time must be used '
        'together.\n')

if( __name__ == '__main__' ):
      unittest.main()
