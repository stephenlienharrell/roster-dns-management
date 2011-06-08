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

"""Regression test for cli_record_lib

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.15'


import os
import sys
import socket
import threading
import time
import getpass
import unittest


import roster_core
import roster_server
from roster_user_tools  import cli_common_lib
from roster_user_tools  import cli_record_lib
from roster_user_tools  import roster_client_lib

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

class options(object):
  password = u'test'
  username = u'sharrell'
  server = None
  ldap = u'ldaps://ldap.cs.university.edu:636'
  credfile = CREDFILE
  view_name = None
  ip_address = None
  target = u'server'
  ttl = 3600

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

class DnsErrorException(Exception):
  pass

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

class TestCliRecordLib(unittest.TestCase):
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

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def newDnsError(self, string, errorcode=None):
    """New dns error that doesnt sys exit

    Inputs:
      string: string of error
    """
    print "ERROR: %s" % string
    raise DnsErrorException

  def testMakeRecord(self):
    options.server = self.server_name
    options.zone_name = u'test_zone'
    options.view_name = u'test_view'

    old_stdout = sys.stdout

    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    cli_common_lib_instance.DnsError = self.newDnsError
    cli_record_lib_instance = cli_record_lib.CliRecordLib(
        cli_common_lib_instance)

    sys.stdout = StdOutStream()

    self.assertRaises(DnsErrorException, cli_record_lib_instance.MakeRecord,
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(sys.stdout.flush(), 'ERROR: View does not exist!\n')

    sys.stdout = old_stdout
    self.core_instance.MakeView(options.view_name)
    sys.stdout = StdOutStream()

    self.assertRaises(DnsErrorException, cli_record_lib_instance.MakeRecord,
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(sys.stdout.flush(), 'ERROR: Zone does not exist!\n')

    self.core_instance.MakeZone(options.zone_name, u'master',
                                u'university.edu.',
                                view_name=options.view_name)
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    cli_record_lib_instance.MakeRecord(
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(
        sys.stdout.flush(),
         u'ADDED A: server zone_name: test_zone view_name: test_view ttl: 3600'
          '\n    assignment_ip: 192.168.1.1\n')

    self.assertRaises(DnsErrorException, cli_record_lib_instance.MakeRecord,
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(sys.stdout.flush(), 'ERROR: Duplicate record!\n')

    options.zone_name = u'reverse_zone'
    self.core_instance.MakeZone(options.zone_name, u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=options.view_name)
    self.core_instance.MakeReverseRangeZoneAssignment(
        options.zone_name, u'192.168.1/24')
    options.target = '192.168.1.6'
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    cli_record_lib_instance.MakeRecord(
        u'ptr', options, {u'assignment_host': u'server.university.edu.'})
    self.assertEqual(sys.stdout.flush(),
                     u'ADDED PTR: 192.168.1.6 zone_name: reverse_zone '
                      'view_name: test_view ttl: 3600\n    assignment_host: '
                      'server.university.edu.\n')

    options.zone_name = u'ipv6_zone'
    self.core_instance.MakeZone(options.zone_name, u'master',
                                u'university2.edu.',
                                view_name=options.view_name)
    options.target = u'ipv6host'
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'ipv6_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    cli_record_lib_instance.MakeRecord(
        u'aaaa', options, {u'assignment_ip': u'2001:db8::1428:57ab'})
    self.assertEqual(sys.stdout.flush(),
                     u'ADDED AAAA: ipv6host zone_name: ipv6_zone view_name: '
                      'test_view ttl: 3600\n    assignment_ip: '
                      '2001:0db8:0000:0000:0000:0000:1428:57ab\n')

    sys.stdout = old_stdout

  def testRemoveRecord(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'university.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'a', u'server', u'test_zone',
        {u'assignment_ip': u'192.168.1.1'}, view_name=u'test_view', ttl=3600)

    options.server = self.server_name
    old_stdout = sys.stdout

    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    cli_common_lib_instance.DnsError = self.newDnsError
    cli_record_lib_instance = cli_record_lib.CliRecordLib(
        cli_common_lib_instance)

    sys.stdout = StdOutStream()
    options.ttl = 3600
    options.target = u'server'
    options.zone_name = u'fake_zone'

    self.assertRaises(DnsErrorException,cli_record_lib_instance.RemoveRecord,
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(sys.stdout.flush(),
                     'ERROR: Zone does not exist!\n')

    options.zone_name = u'test_zone'
    options.view_name = u'fake_view'

    self.assertRaises(DnsErrorException,cli_record_lib_instance.RemoveRecord,
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(sys.stdout.flush(),
                     'ERROR: View does not exist!\n')

    options.view_name = u'test_view'

    cli_record_lib_instance.RemoveRecord(
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(sys.stdout.flush(),
                     u'REMOVED A: server zone_name: test_zone view_name: '
                     'test_view ttl: 3600\n    assignment_ip: 192.168.1.1\n')

    sys.stdout = old_stdout

  def testListRecords(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'university.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'a', u'server', u'test_zone',
        {u'assignment_ip': u'192.168.1.1'}, view_name=u'test_view', ttl=3600)

    options.server = self.server_name

    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    cli_common_lib_instance.DnsError = self.newDnsError
    cli_record_lib_instance = cli_record_lib.CliRecordLib(
        cli_common_lib_instance)

    options.ttl = 3600
    options.target = u'server'
    options.view_name = u'test_view'
    options.zone_name = u'test_zone'
    options.no_header = False

    records = cli_record_lib_instance.ListRecords(
        u'a', options, {u'assignment_ip': u'192.168.1.1'})
    self.assertEqual(
        records,
        'target ttl  record_type view_name last_user zone_name assignment_ip\n'
        '-------------------------------------------------------------------\n'
        'server 3600 a           test_view sharrell  test_zone 192.168.1.1\n')


if( __name__ == '__main__' ):
      unittest.main()
