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

"""Regression test for dnsmassadd

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import os
import sys
import socket
import subprocess
import threading
import time
import getpass

import unittest
sys.path.append('../')

import roster_core
from roster_user_tools  import roster_client_lib
import roster_server

USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
DATA_FILE = 'test_data/test_data.sql'
TEST_FILE = 'test_data/test_massadd'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-user-tools/scripts/dnsmassadd'

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

class TestDnsMassAdd(unittest.TestCase):

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
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.MakeView(u'test_view3')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'university.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'university.edu.',
                                view_name=u'test_view3')
    self.core_instance.MakeZone(u'foward_zone_ipv6', u'master',
                                u'university2.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(
        u'reverse_zone_ipv6', u'master',
        u'0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.'
        '0.0.0.1.2.3.4.ip6.arpa.', view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone_ipv6',
                                                  u'4321::/32')

    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view2')
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                  u'192.168.1/24')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'forward_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'foward_zone_ipv6',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone_ipv6',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host2', u'foward_zone_ipv6', {u'assignment_ip':
            u'4321:0000:0001:0002:0003:0004:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.5'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'www.host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.5'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'5',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host2.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'4',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host3.university.edu.'},
                                  view_name=u'test_view')


  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testMassAdd(self):
    ## Check initial records
    self.assertEqual(
        self.core_instance.ListRecords(view_name=u'test_view'),
            [{u'serial_number': 4, u'refresh_seconds': 5, 'target': u'soa1',
            u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
            'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
            'view_name': u'test_view', 'last_user': u'sharrell',
            'zone_name': u'forward_zone', u'admin_email': u'admin.university.edu.',
            u'expiry_seconds': 5},
             {u'serial_number': 4, u'refresh_seconds': 5, 'target': u'soa1',
             u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
             'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone', u'admin_email': u'admin.university.edu.',
             u'expiry_seconds': 5},
             {u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
             u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
             'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'foward_zone_ipv6',
             u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
             {u'serial_number': 2, u'refresh_seconds': 5, 'target': u'soa1',
             u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
             'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone_ipv6', u'admin_email': u'admin.university.edu.',
             u'expiry_seconds': 5},
             {'target': u'host2', 'ttl': 3600, 'record_type': u'aaaa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'foward_zone_ipv6',
             u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
             {'target': u'host3', 'ttl': 3600, 'record_type': u'a',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
             {'target': u'www.host3', 'ttl': 3600, 'record_type': u'a',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
             {'target': u'5', 'ttl': 3600, 'record_type': u'ptr',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone', u'assignment_host': u'host2.university.edu.'},
             {'target': u'4', 'ttl': 3600, 'record_type': u'ptr',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone', u'assignment_host': u'host3.university.edu.'}])

    ## Get test_file
    handle = open(TEST_FILE, 'r')
    try:
      file_contents = handle.read()
    finally:
      handle.close()

    self.assertEqual(file_contents,
        '192.168.1.5 computer1\n'
        '4321::1:2:3:4:567:89ab computer2\n'
        '4321::1:2:3:4:567:89ac computer3\n')
    
    ## Run script against running database with no-commit flag
    command = os.popen(('python %s -v %s -z %s --no-commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, 'test_view', 'forward_zone', TEST_FILE,
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))

    ## Check output of replaced hosts
    self.assertEqual(command.read(), (
        'Commit flag not specified. Changes will not be made to the database.\n\n'
        'HOSTS TO BE REMOVED: \n'
        '# type target    zone         view\n'
        '----------------------------------\n'
        '0 ptr  5         forward_zone test_view\n'
        '1 a    host3     forward_zone test_view\n'
        '2 a    www.host3 forward_zone test_view\n'
        '3 aaaa host2     forward_zone test_view\n\n\n'
        'HOSTS TO BE ADDED: \n'
        '# type target                                    zone         view\n'
        '------------------------------------------------------------------\n'
        '0 a    computer1                                 forward_zone test_view\n'
        '1 ptr  5                                         forward_zone test_view\n'
        '2 aaaa computer2                                 forward_zone test_view\n'
        '3 ptr  b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1 forward_zone test_view\n'
        '4 aaaa computer3                                 forward_zone test_view\n'
        '5 ptr  c.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1 forward_zone test_view\n\n\n'
        'Commit flag not specified. Changes will not be made to the database.\n'))

    command.close()

    ## Ensure nothing got changed
    self.assertEqual(
        self.core_instance.ListRecords(view_name=u'test_view'),
          [{u'serial_number': 4, u'refresh_seconds': 5, 'target': u'soa1',
            u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
            'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
            'view_name': u'test_view', 'last_user': u'sharrell',
            'zone_name': u'forward_zone', u'admin_email': u'admin.university.edu.',
            u'expiry_seconds': 5},
             {u'serial_number': 4, u'refresh_seconds': 5, 'target': u'soa1',
             u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
             'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone', u'admin_email': u'admin.university.edu.',
             u'expiry_seconds': 5},
             {u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
             u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
             'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'foward_zone_ipv6',
             u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
             {u'serial_number': 2, u'refresh_seconds': 5, 'target': u'soa1',
             u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
             'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone_ipv6', u'admin_email': u'admin.university.edu.',
             u'expiry_seconds': 5},
             {'target': u'host2', 'ttl': 3600, 'record_type': u'aaaa',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'foward_zone_ipv6',
             u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
             {'target': u'host3', 'ttl': 3600, 'record_type': u'a',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
             {'target': u'www.host3', 'ttl': 3600, 'record_type': u'a',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
             {'target': u'5', 'ttl': 3600, 'record_type': u'ptr',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone', u'assignment_host': u'host2.university.edu.'},
             {'target': u'4', 'ttl': 3600, 'record_type': u'ptr',
             'view_name': u'test_view', 'last_user': u'sharrell',
             'zone_name': u'reverse_zone', u'assignment_host': u'host3.university.edu.'}])

    ## Run script against running database
    command = os.popen(('python %s -v %s -z %s --commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'test_view', u'forward_zone', TEST_FILE,
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    
    self.assertEqual(command.read(), (
        'HOSTS TO BE REMOVED: \n'
        '# type target    zone         view\n'
        '----------------------------------\n'
        '0 ptr  5         forward_zone test_view\n'
        '1 a    host3     forward_zone test_view\n'
        '2 a    www.host3 forward_zone test_view\n'
        '3 aaaa host2     forward_zone test_view\n\n\n'
        'HOSTS TO BE ADDED: \n'
        '# type target                                    zone         view\n'
        '------------------------------------------------------------------\n'
        '0 a    computer1                                 forward_zone test_view\n'
        '1 ptr  5                                         forward_zone test_view\n'
        '2 aaaa computer2                                 forward_zone test_view\n'
        '3 ptr  b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1 forward_zone test_view\n'
        '4 aaaa computer3                                 forward_zone test_view\n'
        '5 ptr  c.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1 forward_zone test_view\n\n'))

    command.close()
    
    ## Check output of replaced hosts
    self.assertEqual(
        self.core_instance.ListRecords(view_name=u'test_view'),
        [{u'serial_number': 5, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
        'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'admin_email': u'admin.university.edu.',
        u'expiry_seconds': 5},
        {u'serial_number': 5, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5, 'ttl': 3600,
        u'minimum_seconds': 5, 'record_type': u'soa', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone',
        u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
        {u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5, 'ttl': 3600,
        u'minimum_seconds': 5, 'record_type': u'soa', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'foward_zone_ipv6',
        u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
        {u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5, 'ttl': 3600,
        u'minimum_seconds': 5, 'record_type': u'soa', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone_ipv6',
        u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
        {'target': u'4', 'ttl': 3600, 'record_type': u'ptr',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'reverse_zone', u'assignment_host': u'host3.university.edu.'},
        {'target': u'computer1', 'ttl': 3600, 'record_type': u'a',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
        {'target': u'5', 'ttl': 3600, 'record_type': u'ptr',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'reverse_zone', u'assignment_host': u'computer1.university.edu'},
        {'target': u'computer2', 'ttl': 3600, 'record_type': u'aaaa',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'assignment_ip': u'4321::1:2:3:4:567:89ab'},
        {'target': u'b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1',
        'ttl': 3600, 'record_type': u'ptr', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone_ipv6',
        u'assignment_host': u'computer2.university.edu'},
        {'target': u'computer3', 'ttl': 3600, 'record_type': u'aaaa',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'assignment_ip': u'4321::1:2:3:4:567:89ac'},
        {'target': u'c.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1', 'ttl': 3600,
        'record_type': u'ptr', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone_ipv6',
        u'assignment_host': u'computer3.university.edu'}])

    ## Run script against running database, but fail
    command = os.popen(('python %s -v %s -z %s --commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'test_view', u'forward_zone', TEST_FILE,
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    lines = command.read()
    self.assertTrue(
        'SERVER ERROR:' in lines and
        'Duplicate record found' in lines)

    ## Check output of a failed run, make sure nothing changed.
    self.assertEqual(
        self.core_instance.ListRecords(view_name=u'test_view'),
        [{u'serial_number': 5, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
        'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'admin_email': u'admin.university.edu.',
        u'expiry_seconds': 5},
        {u'serial_number': 5, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5, 'ttl': 3600,
        u'minimum_seconds': 5, 'record_type': u'soa', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone',
        u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
        {u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5, 'ttl': 3600,
        u'minimum_seconds': 5, 'record_type': u'soa', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'foward_zone_ipv6',
        u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
        {u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
        u'name_server': u'ns1.university.edu.', u'retry_seconds': 5, 'ttl': 3600,
        u'minimum_seconds': 5, 'record_type': u'soa', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone_ipv6',
        u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
        {'target': u'4', 'ttl': 3600, 'record_type': u'ptr',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'reverse_zone', u'assignment_host': u'host3.university.edu.'},
        {'target': u'computer1', 'ttl': 3600, 'record_type': u'a',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
        {'target': u'5', 'ttl': 3600, 'record_type': u'ptr',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'reverse_zone', u'assignment_host': u'computer1.university.edu'},
        {'target': u'computer2', 'ttl': 3600, 'record_type': u'aaaa',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'assignment_ip': u'4321::1:2:3:4:567:89ab'},
        {'target': u'b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1',
        'ttl': 3600, 'record_type': u'ptr', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone_ipv6',
        u'assignment_host': u'computer2.university.edu'},
        {'target': u'computer3', 'ttl': 3600, 'record_type': u'aaaa',
        'view_name': u'test_view', 'last_user': u'sharrell',
        'zone_name': u'forward_zone', u'assignment_ip': u'4321::1:2:3:4:567:89ac'},
        {'target': u'c.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1', 'ttl': 3600,
        'record_type': u'ptr', 'view_name': u'test_view',
        'last_user': u'sharrell', 'zone_name': u'reverse_zone_ipv6',
        u'assignment_host': u'computer3.university.edu'}])

    command.close()

  def testMassAddErrors(self):
    ## Required flags
    command = os.popen(('python %s -v %s --commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'test_view', TEST_FILE,
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    self.assertEquals(command.read(),
        'CLIENT ERROR: The -z/--zone-name flag is required.\n')
    
    command = os.popen(('python %s -z %s --commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'forward_zone', TEST_FILE,
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    self.assertEquals(command.read(),
        'CLIENT ERROR: The -v/--view-name flag is required.\n')
    
    command = os.popen(('python %s -v %s -z %s --commit '
                       '-s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'test_view', u'forward_zone',
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    self.assertEquals(command.read(),
        'CLIENT ERROR: The -f/--file flag is required.\n')
    
    ## Errors
    command = os.popen(('python %s -v %s -z %s --commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'bad_view', u'forward_zone', TEST_FILE,
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    self.assertEquals(command.read(),
        'CLIENT ERROR: Zone "forward_zone" not found in "bad_view" view.\n')
    
    command = os.popen(('python %s -v %s -z %s --commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'test_view', u'bad_zone', TEST_FILE,
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    self.assertEquals(command.read(),
        'CLIENT ERROR: Zone "bad_zone" does not exist.\n')
    
    command = os.popen(('python %s -v %s -z %s --commit '
                       '-f %s -s %s -u %s -p %s --config-file %s' % (
                         EXEC, u'test_view', u'test_zone', 'bad_file',
                         self.server_name, USERNAME, PASSWORD, USER_CONFIG)))
    self.assertEquals(command.read(),
        'Specified file, bad_file, does not exist\n')

if( __name__ == '__main__' ):
  unittest.main()
