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

"""Regression test for dnsaddrecords

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


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

USER_CONFIG = 'test_data/roster_user_tools.conf' # Example in test data
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-user-tools/scripts/dnsaddformattedrecords'

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

class TestDnsZoneImport(unittest.TestCase):

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
    self.core_instance.MakeZone(u'sub.university.edu', u'master',
                                u'sub.university.edu.', view_name=u'test_view')
    self.core_instance.MakeZone(u'0.168.192.in-addr.arpa', u'master',
                                u'0.168.192.in-addr.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'8.0.e.f.f.3.ip6.arpa', u'master',
                                u'8.0.e.f.f.3.ip6.arpa.', view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(
        u'0.168.192.in-addr.arpa', u'192.168.0/24')
    self.core_instance.MakeReverseRangeZoneAssignment(
        u'8.0.e.f.f.3.ip6.arpa', u'3ffe:0800:0000:0000:0000:0000:0000:0000/24')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)


  def testAddFormattedRecords(self):
    self.assertEqual(self.core_instance.ListRecords(), [])
    self.core_instance.MakeRecord(
        u'soa', u'sub_university_edu', u'sub.university.edu',
        {u'name_server': u'test.', u'admin_email': u'test.',
         u'serial_number': 12345, u'refresh_seconds': 4,
         u'retry_seconds': 4, u'expiry_seconds': 4, u'minimum_seconds': 4},
        view_name=u'test_view')
    output = os.popen('python %s -f test_data/test_records.db -v test_view -z test_zone '
                      '-u %s --config-file %s -z sub.university.edu '
                      '-s %s -p %s'% (
                          EXEC, USERNAME, USER_CONFIG, self.server_name, PASSWORD))
    self.assertEqual(output.read(),
                     'ADDED 8 records to sub.university.edu.\n')
    output.close()
    self.assertEqual(self.core_instance.ListRecords(),
        [{u'serial_number': 12347, u'refresh_seconds': 4,
          'target': u'sub_university_edu', u'name_server': u'test.',
          u'retry_seconds': 4, 'ttl': 3600, u'minimum_seconds': 4,
          'record_type': u'soa', 'view_name': u'test_view',
          'last_user': u'sharrell', 'zone_name': u'sub.university.edu',
          u'admin_email': u'test.', u'expiry_seconds': 4},
         {'target': u'university.edu', u'weight': 5, 'ttl': 0,
          u'priority': 0, 'record_type': u'srv', 'view_name': u'test_view',
          'last_user': u'sharrell', 'zone_name': u'sub.university.edu',
          u'assignment_host': u'test.sub.university.edu.', u'port': 80},
         {'target': u'desktop-1', 'ttl': 0, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'sub.university.edu', u'assignment_ip': u'192.168.1.100'},
         {'target': u'ns2', 'ttl': 0, 'record_type': u'a', 'view_name': u'test_view',
          'last_user': u'sharrell', 'zone_name': u'sub.university.edu',
          u'assignment_ip': u'192.168.1.104'},
         {'target': u'www', 'ttl': 0, 'record_type': u'cname', 'view_name': u'test_view',
          'last_user': u'sharrell', 'zone_name': u'sub.university.edu',
          u'assignment_host': u'sub.university.edu.'},
         {'target': u'ns', 'ttl': 0, 'record_type': u'a', 'view_name': u'test_view',
          'last_user': u'sharrell', 'zone_name': u'sub.university.edu',
          u'assignment_ip': u'192.168.1.103'},
         {'target': u'www.data', 'ttl': 0, 'record_type': u'cname',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'sub.university.edu',
          u'assignment_host': u'ns.university.edu.'},
         {'target': u'mail1', 'ttl': 0, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'sub.university.edu', u'assignment_ip': u'192.168.1.101'},
         {'target': u'mail2', 'ttl': 0, 'record_type': u'a', 'view_name': u'test_view',
          'last_user': u'sharrell', 'zone_name': u'sub.university.edu',
          u'assignment_ip': u'192.168.1.102'}])

if( __name__ == '__main__' ):
      unittest.main()
