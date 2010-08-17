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

"""Regression test for dnsrmrecord

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import os
import sys
import socket
import threading
import time
import getpass

import unittest
sys.path.append('../')

import roster_core
from roster_user_tools import roster_client_lib
import roster_server

USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC = '../roster-user-tools/scripts/dnsrmrecord'

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

class Testdnsrmrecord(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    self.db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_thread = DaemonThread(self.config_instance, self.port)
    self.daemon_thread.start()
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def retCode(self, code):
    if( code is None ):
      return 0
    return os.WEXITSTATUS(code)

  def testARemove(self):
    command = os.popen('python %s '
                       'a --assignment-ip="10.10.10.0" -t '
                       'machine1 -v test_view -z test_zone -u %s -p %s '
                       '--config-file %s -s %s' % (
                           EXEC, USERNAME, self.password,
                           USER_CONFIG, self.server_name))
    self.assertEqual(command.read(), 'CLIENT ERROR: View does not exist!\n')
    self.assertTrue(self.retCode(command.close()))
    self.core_instance.MakeView(u'test_view')
    command = os.popen('python %s '
                       'a --assignment-ip="10.10.10.0" -t '
                       'machine1 -v test_view -z test_zone -u %s -p %s '
                       '--config-file %s -s %s' % (
                           EXEC, USERNAME, self.password,
                           USER_CONFIG, self.server_name))
    self.assertEqual(command.read(), 'CLIENT ERROR: Zone does not exist!\n')
    self.assertTrue(self.retCode(command.close()))
    self.assertFalse(self.core_instance.ListZones())
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': u'',
                        'zone_origin': u'test_zone.'}}})
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.0'},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'a'),
                     [{'target': u'machine1', 'ttl': 3600, 'record_type': u'a',
                       'view_name': u'test_view', 'last_user': u'sharrell',
                       'zone_name': u'test_zone',
                       u'assignment_ip': u'10.10.10.0'}])
    command = os.popen('python %s '
                       'a --assignment-ip="10.10.10.0" -t '
                       'machine1 -v test_view -z test_zone -u %s -p %s '
                       '--config-file %s '
                       '-s %s' % (EXEC, USERNAME, self.password, USER_CONFIG,
                                  self.server_name))
    self.assertEqual(command.read(),
        'REMOVED A: machine1 zone_name: test_zone view_name: test_view '
        'ttl: 3600\n'
        '    assignment_ip: 10.10.10.0\n')
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'a'), [])

  def testAAAARemove(self):
    command = os.popen('python %s aaaa '
                       '--assignment-ip=" fe80::200:f8ff:fe21:67cf" '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(), 'CLIENT ERROR: View does not exist!\n')
    self.assertTrue(self.retCode(command.close()))
    self.core_instance.MakeView(u'test_view')
    command = os.popen('python %s aaaa '
                       '--assignment-ip=" fe80::200:f8ff:fe21:67cf" '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(), 'CLIENT ERROR: Zone does not exist!\n')
    self.assertTrue(self.retCode(command.close()))
    self.assertFalse(self.core_instance.ListZones())
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': u'',
                        'zone_origin': u'test_zone.'}}})
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'machine1', u'test_zone',
        {u'assignment_ip': u'fe80:0000:0000:0000:0200:f8ff:fe21:67cf'},
        view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'aaaa'),
                     [{'target': u'machine1', 'ttl': 3600,
                       'record_type': u'aaaa', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'test_zone',
                       u'assignment_ip':
                           u'fe80:0000:0000:0000:0200:f8ff:fe21:67cf'}])
    command = os.popen('python %s '
                       'aaaa --assignment-ip="fe80::200:f8ff:fe21:67cf" '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'aaaa'), [])

  def testHINFORemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'hinfo', u'machine1', u'test_zone',
                                  {u'hardware': u'Pear', u'os': u'ipear'},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'hinfo'),
                     [{'target': u'machine1', 'ttl': 3600, u'hardware': u'Pear',
                       'record_type': u'hinfo', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'test_zone',
                       u'os': u'ipear'}])
    command = os.popen('python %s '
                       'hinfo --hardware Pear --os ipear '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(
        command.read(),
        'REMOVED HINFO: machine1 zone_name: test_zone view_name: test_view '
        'ttl: 3600\n'
        '    hardware: Pear os: ipear\n')
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'hinfo'), [])

  def testTXTRemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'txt', u'machine1', u'test_zone',
                                  {u'quoted_text': u'et tu brute'},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'txt'),
                     [{'target': u'machine1', 'ttl': 3600,
                       'record_type': u'txt', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'test_zone',
                       u'quoted_text': u'et tu brute'}])
    command = os.popen('python %s '
                       'txt --quoted-text "et tu brute" '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'txt'), [])

  def testCNAMERemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine1', u'test_zone',
                                  {u'assignment_host': u'university.edu.'},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'cname'),
                     [{'target': u'machine1', 'ttl': 3600,
                       'record_type': u'cname', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'test_zone',
                       u'assignment_host': u'university.edu.'}])
    command = os.popen('python %s '
                       'cname --assignment-host="university.edu." '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'cname'), [])

  def testSOARemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(u'soa', u'machine1', u'test_zone',
                                  {u'name_server': u'ns.university.edu.',
                                   u'admin_email': u'university.edu.',
                                   u'serial_number': 123456789,
                                   u'refresh_seconds': 30,
                                   u'retry_seconds': 30, u'expiry_seconds': 30,
                                   u'minimum_seconds': 30},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'soa'),
                     [{u'serial_number': 123456790, u'refresh_seconds': 30,
                       'target': u'machine1',
                       u'name_server': u'ns.university.edu.',
                       u'retry_seconds': 30, 'ttl': 3600,
                       u'minimum_seconds': 30, 'record_type': u'soa',
                       'view_name': u'test_view', 'last_user': u'sharrell',
                       'zone_name': u'test_zone',
                       u'admin_email': u'university.edu.',
                       u'expiry_seconds': 30}])
    command = os.popen('python %s '
                       'soa --name-server="ns.university.edu." '
                       '--admin-email="university.edu." '
                       '--serial-number=123456790 --refresh-seconds=30 '
                       '--retry-seconds=30 --minimum-seconds=30 '
                       '--expiry-seconds=30 --ttl 3600 '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'soa'), [])

  def testSRVRemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'srv', u'machine1', u'test_zone',
                                  {u'priority': 5, u'weight': 6, u'port': 80,
                                   u'assignment_host': u'university.edu.'},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'srv'),
                     [{'target': u'machine1', u'weight': 6, 'ttl': 3600,
                       u'priority': 5, 'record_type': u'srv',
                       'view_name': u'test_view', 'last_user': u'sharrell',
                       'zone_name': u'test_zone',
                       u'assignment_host': u'university.edu.', u'port': 80}])
    command = os.popen('python %s srv '
                       '--priority 5 --weight 6 --port 80 '
                       '--assignment-host="university.edu." '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'srv'), [])

  def testNSRemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'ns', u'machine1', u'test_zone',
                                  {u'name_server': u'university.edu.'},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'ns'),
                     [{'target': u'machine1',
                       u'name_server': u'university.edu.',
                       'ttl': 3600, 'record_type': u'ns',
                       'view_name': u'test_view', 'last_user': u'sharrell',
                       'zone_name': u'test_zone'}])
    command = os.popen('python %s '
                       'ns --name-server="university.edu." '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'ns'), [])

  def testMXRemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'mx', u'machine1', u'test_zone',
                                  {u'mail_server': u'university.edu.',
                                   u'priority': 5},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'mx'),
                     [{'target': u'machine1', 'ttl': 3600, u'priority': 5,
                       'record_type': u'mx', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'test_zone',
                       u'mail_server': u'university.edu.'}])
    command = os.popen('python %s mx '
                       '--mail-server="university.edu." --priority 5 '
                       '-q -t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'mx'), [])

  def testPTRRemove(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(u'test_zone',
                                                      u'192.168.1/24')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'1', u'test_zone',
                                  {u'assignment_host': u'm.university.edu.'},
                                  view_name=u'test_view')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'ptr'),
                     [{'target': u'1', 'ttl': 3600,
                       'record_type': u'ptr', 'view_name': u'test_view',
                       'last_user': u'sharrell', 'zone_name': u'test_zone',
                       u'assignment_host': u'm.university.edu.'}])
    command = os.popen('python %s '
                       'ptr --assignment-host="m.university.edu." '
                       '-q -t 192.168.1.1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertFalse(self.retCode(command.close()))
    self.assertEqual(self.core_instance.ListRecords(record_type=u'ptr'), [])

  def testErrors(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'test_zone.',
                                view_name=u'test_view')
    command = os.popen('python %s a -t t -v any -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'CLIENT ERROR: The -z/--zone-name flag is required.\n')
    command.close()
    command = os.popen('python %s a -z test_zone --assignment-ip test -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'CLIENT ERROR: The -t/--target flag is required.\n')
    command.close()
    command = os.popen3('python %s soa -z z -t t --serial-number number '
                       '--refresh-seconds 3 --retry-seconds 3 '
                       '--expiry-seconds 3 --minimum-seconds 3 '
                       '-u %s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))[2]
    self.assertEqual(command.read().split('\n')[-2],
        "dnsrmrecord: error: option --serial-number: invalid integer value: "
        "'number'")
    command.close()
    command = os.popen('python %s soa -z z -t t --serial-number 3 '
                       '-u %s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'CLIENT ERROR: The --admin-email flag is required.\n')
    command.close()
    command = os.popen3('python %s mx -z z -t t --priority number '
                       '-u %s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))[2]
    self.assertEqual(command.read().split('\n')[-2],
        "dnsrmrecord: error: option --priority: invalid integer value: "
        "'number'")
    command.close()
    command = os.popen('python %s mx -z z -t t '
                       '-u %s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'CLIENT ERROR: The --priority flag is required.\n')
    command.close()


if( __name__ == '__main__' ):
    unittest.main()
