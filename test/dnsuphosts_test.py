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

"""Regression test for dnsuphost

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.18'


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
TEST_FILE = 'test_data/test_hosts'
TEST_FILE_IPV6 = 'test_data/test_hosts_ipv6'
INVALID_HOSTS = 'test_data/invalid_hosts'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-user-tools/scripts/dnsuphosts'

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

class TestDnsMkHost(unittest.TestCase):

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
    self.core_instance.MakeZone(u'ipv6_zone', u'master',
                                u'university2.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(
        u'ipv6_zone_rev', u'master',
        u'0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.'
        '0.0.0.1.0.0.2.ip6.arpa.', view_name=u'test_view')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view2')
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
        u'aaaa', u'host2', u'forward_zone', {u'assignment_ip':
            u'4321:0000:0001:0002:0003:0004:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.5'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'www.host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.5'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'4',
                                  u'reverse_zone',
                                  {u'assignment_host': u'host2.university.edu.'},
                                  view_name=u'test_view')


  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testReadFileFromDB(self):
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone_rev',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'ipv6host', u'ipv6_zone', {u'assignment_ip':
          u'2001:0000:0000:0000:0000:0000:0000:0001'}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host_ipv6', u'ipv6_zone', {u'assignment_ip':
          u'2001:0000:0000:0000:0000:0000:0000:0001'}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host_ipv6', u'ipv6_zone', {u'assignment_ip':
          u'2001:0000:0000:0000:0000:0000:0000:0002'}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'ptr', u'1', u'ipv6_zone_rev', {u'assignment_host':
          u'ipv6host.university2.edu.'}, view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.1.0/24')
    self.core_instance.MakeReverseRangeZoneAssignment(u'ipv6_zone_rev',
                                                      u'2001::/124')
    output = os.popen('python %s dump -r 192.168.1.4/30 -f %s '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG))
    output.close()
    handle = open(TEST_FILE, 'r')
    self.assertEqual(
        handle.read(),
        '#:range:192.168.1.4/30\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#192.168.1.4 host2.university.edu               '
        '# No forward assignment\n'
        '#192.168.1.5 host3.university.edu     host3     '
        '# No reverse assignment\n'
        '#192.168.1.5 www.host3.university.edu www.host3 '
        '# No reverse assignment\n'
        '#192.168.1.6\n'
        '#192.168.1.7\n')
    handle.close()
    output = os.popen('python %s dump -r 2001::/124 -f %s -z ipv6_zone '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE_IPV6, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG))
    output.close()
    handle = open(TEST_FILE_IPV6, 'r')
    self.assertEqual(handle.read(),
        '#:range:2001::/124\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#2001:0000:0000:0000:0000:0000:0000:0000\n'
        '2001:0000:0000:0000:0000:0000:0000:0001  ipv6host.university2.edu  ipv6host\n'
        '#2001:0000:0000:0000:0000:0000:0000:0001 host_ipv6.university2.edu host_ipv6 # No reverse assignment\n'
        '#2001:0000:0000:0000:0000:0000:0000:0002 host_ipv6.university2.edu host_ipv6 # No reverse assignment\n'
        '#2001:0000:0000:0000:0000:0000:0000:0003\n'
        '#2001:0000:0000:0000:0000:0000:0000:0004\n'
        '#2001:0000:0000:0000:0000:0000:0000:0005\n'
        '#2001:0000:0000:0000:0000:0000:0000:0006\n'
        '#2001:0000:0000:0000:0000:0000:0000:0007\n'
        '#2001:0000:0000:0000:0000:0000:0000:0008\n'
        '#2001:0000:0000:0000:0000:0000:0000:0009\n'
        '#2001:0000:0000:0000:0000:0000:0000:000a\n'
        '#2001:0000:0000:0000:0000:0000:0000:000b\n'
        '#2001:0000:0000:0000:0000:0000:0000:000c\n'
        '#2001:0000:0000:0000:0000:0000:0000:000d\n'
        '#2001:0000:0000:0000:0000:0000:0000:000e\n'
        '#2001:0000:0000:0000:0000:0000:0000:000f\n')
    handle.close()

  def testWriteIPV6ToDB(self):
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone_rev',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'ipv6host', u'ipv6_zone', {u'assignment_ip':
          u'2001:0000:0000:0000:0000:0000:0000:0001'}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host_ipv6', u'ipv6_zone', {u'assignment_ip':
          u'2001:0000:0000:0000:0000:0000:0000:0002'}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'ptr', u'1', u'ipv6_zone_rev', {u'assignment_host':
          u'ipv6host.university2.edu.'}, view_name=u'test_view')
    output = os.popen('python %s dump -r 2001::/124 -f %s -z ipv6_zone '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG))
    output.close()
    handle = open(TEST_FILE_IPV6, 'r')
    try:
      contents = handle.read()
    finally:
      handle.close()

    contents = contents.replace('host_ipv6', 'newhost')

    handle = open(TEST_FILE_IPV6, 'w')
    try:
      handle.writelines(contents)
    finally:
      handle.close()
    handle = open(TEST_FILE_IPV6, 'r')
    self.assertEqual(handle.read(),
        '#:range:2001::/124\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#2001:0000:0000:0000:0000:0000:0000:0000\n'
        '2001:0000:0000:0000:0000:0000:0000:0001  ipv6host.university2.edu  ipv6host\n'
        '#2001:0000:0000:0000:0000:0000:0000:0001 newhost.university2.edu newhost # No reverse assignment\n'
        '#2001:0000:0000:0000:0000:0000:0000:0002 newhost.university2.edu newhost # No reverse assignment\n'
        '#2001:0000:0000:0000:0000:0000:0000:0003\n'
        '#2001:0000:0000:0000:0000:0000:0000:0004\n'
        '#2001:0000:0000:0000:0000:0000:0000:0005\n'
        '#2001:0000:0000:0000:0000:0000:0000:0006\n'
        '#2001:0000:0000:0000:0000:0000:0000:0007\n'
        '#2001:0000:0000:0000:0000:0000:0000:0008\n'
        '#2001:0000:0000:0000:0000:0000:0000:0009\n'
        '#2001:0000:0000:0000:0000:0000:0000:000a\n'
        '#2001:0000:0000:0000:0000:0000:0000:000b\n'
        '#2001:0000:0000:0000:0000:0000:0000:000c\n'
        '#2001:0000:0000:0000:0000:0000:0000:000d\n'
        '#2001:0000:0000:0000:0000:0000:0000:000e\n'
        '#2001:0000:0000:0000:0000:0000:0000:000f\n')
    handle.close()

  def testWriteFileToDB(self):
    # Check initial records
    self.assertEqual(
        self.core_instance.ListRecords(view_name=u'test_view'),
        [{u'serial_number': 5, u'refresh_seconds': 5, 'target': u'soa1',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
         {u'serial_number': 3, u'refresh_seconds': 5, 'target': u'soa1',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
         {'target': u'host2', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone',
          u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
         {'target': u'host3', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
         {'target': u'www.host3', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
         {'target': u'4', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'host2.university.edu.'}])

    # Get file previously written
    handle = open(TEST_FILE, 'r')
    try:
      file_contents = handle.read()
    finally:
      handle.close()

    self.assertEqual(file_contents,
        '#:range:192.168.1.4/30\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#192.168.1.4 host2.university.edu               '
        '# No forward assignment\n'
        '#192.168.1.5 host3.university.edu     host3     '
        '# No reverse assignment\n'
        '#192.168.1.5 www.host3.university.edu www.host3 '
        '# No reverse assignment\n'
        '#192.168.1.6\n'
        '#192.168.1.7\n')

    # Replace some information in the file
    new_file_contents = file_contents.replace(
        '#192.168.1.5', '192.168.1.5')
    new_file_contents = new_file_contents.replace('host2', 'host7')
    new_file_contents = new_file_contents.replace('host3.', '')
    new_file_contents = new_file_contents.replace('host3', '@')
    handle = open(TEST_FILE, 'w')
    try:
      handle.writelines(new_file_contents)
    finally:
      handle.close()

    # Check file contents
    handle = open(TEST_FILE, 'r')
    self.assertEqual(handle.read(),
        '#:range:192.168.1.4/30\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#192.168.1.4 host7.university.edu               '
        '# No forward assignment\n'
        '192.168.1.5 university.edu     @     # No reverse assignment\n'
        '192.168.1.5 www.university.edu www.@ # No reverse assignment\n'
        '#192.168.1.6\n'
        '#192.168.1.7\n')
    handle.close()

    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.1.0/24')
    handle = open(TEST_FILE, 'r')
    file_contents = handle.read()
    handle.close()
    # Run updater
    output = os.popen('python %s update -f %s -z forward_zone -v test_view -s '
                      '%s -u %s -p %s --config-file %s --commit' % (
                          EXEC, TEST_FILE, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: Host with IP 192.168.1.5 cannot be uncommented\n')
    output.close()

    new_file_contents = new_file_contents.replace(
        '192.168.1.5', '#192.168.1.5')
    handle = open(TEST_FILE, 'w')
    try:
      handle.writelines(new_file_contents)
    finally:
      handle.close()

    handle = open(TEST_FILE, 'r')
    file_contents = handle.read()
    handle.close()

    new_file_contents = new_file_contents.replace(
        '#192.168.1.6', '192.168.1.6 new_host.university.edu new_host')

    handle = open(TEST_FILE, 'w')
    handle.writelines(new_file_contents)
    handle.close()

    output = os.popen('python %s update -f %s -z forward_zone -v test_view -s '
                      '%s -u %s -p %s --config-file %s --commit' % (
                          EXEC, TEST_FILE, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'Host: new_host.university.edu with ip address 192.168.1.6 '
        'will be ADDED\n')
    output.close()

    # Check final records
    self.assertEqual(
        self.core_instance.ListRecords(view_name=u'test_view'),
        [{u'serial_number': 6, u'refresh_seconds': 5, 'target': u'soa1',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
         {u'serial_number': 4, u'refresh_seconds': 5, 'target': u'soa1',
          u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
          'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'admin_email': u'admin.university.edu.', u'expiry_seconds': 5},
         {'target': u'host2', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone',
          u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
         {'target': u'host3', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
         {'target': u'www.host3', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.5'},
         {'target': u'4', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'host2.university.edu.'},
         {'target': u'new_host', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone', u'assignment_ip': u'192.168.1.6'},
         {'target': u'6', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'reverse_zone',
          u'assignment_host': u'new_host.university.edu.'}])

    output = os.popen('python %s dump -r 192.168.1.4/30 -f %s '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG))
    output.close()

    # Write another hosts file and check its contents
    handle = open(TEST_FILE, 'r')
    self.assertEqual(handle.read(),
        '#:range:192.168.1.4/30\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#192.168.1.4 host2.university.edu               '
        '# No forward assignment\n'
        '#192.168.1.5 host3.university.edu     host3     '
        '# No reverse assignment\n'
        '#192.168.1.5 www.host3.university.edu www.host3 '
        '# No reverse assignment\n'
        '192.168.1.6  new_host.university.edu  new_host\n'
        '#192.168.1.7\n')
    handle.close()

    handle = open(TEST_FILE, 'r')
    file_contents = handle.read()
    handle.close()

    file_contents = file_contents.replace('192.168.1.6', '#192.168.1.6')

    handle = open(TEST_FILE, 'w')
    handle.writelines(file_contents)
    handle.close()

    output = os.popen('python %s update -f %s -z forward_zone -v test_view -s '
                      '%s -u %s -p %s --config-file %s --commit' % (
                          EXEC, TEST_FILE, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'Host: new_host.university.edu with ip address 192.168.1.6 '
        'will be REMOVED\n')
    output.close()

    output = os.popen('python %s dump -r 192.168.1.4/30 -f %s '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG))
    output.close()

    # Write another hosts file and check its contents
    handle = open(TEST_FILE, 'r')
    self.assertEqual(handle.read(),
        '#:range:192.168.1.4/30\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#192.168.1.4 host2.university.edu               '
        '# No forward assignment\n'
        '#192.168.1.5 host3.university.edu     host3     '
        '# No reverse assignment\n'
        '#192.168.1.5 www.host3.university.edu www.host3 '
        '# No reverse assignment\n'
        '#192.168.1.6\n'
        '#192.168.1.7\n')
    handle.close()

    if( os.path.exists(TEST_FILE) ):
      os.remove(TEST_FILE)

  def testErrors(self):
    file_contents = ('#:range:192.168.1.4/30\n'
                     '#:view_dependency:test_view_dep\n'
                     '# Do not delete any lines in this file!\n'
                     '# To remove a host, comment it out, to add a host,\n'
                     '# uncomment the desired ip address and specify a\n'
                     '# hostname. To change a hostname, edit the hostname\n'
                     '# next to the desired ip address.\n'
                     '#192.168.1.4\n'
                     '192.168.1.5  host3.university.edu host3 3 # No reverse '
                     'assignment\n'
                     '#192.168.1.6\n'
                     '192.168.1.7  host5.university.edu host5 # No reverse '
                     'assignment\n')
    handle = open(INVALID_HOSTS, 'w')
    handle.writelines(file_contents)
    handle.close()
    output = os.popen('python %s update -f %s -v test_view -s %s -u %s '
                      '--commit -p %s --config-file %s' % (
                          EXEC, INVALID_HOSTS,
                          self.server_name, USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Line "192.168.1.5  host3.university.edu '
                     'host3 3 '
                     '# No reverse assignment" is incorrectly formatted in '
                     '"%s"\n' % INVALID_HOSTS)
    output.close()
    file_contents = ('#:range:192.168.1.4/30\n'
                     '#:view_dependency:test_view_dep\n'
                     '# Do not delete any lines in this file!\n'
                     '# To remove a host, comment it out, to add a host,\n'
                     '# uncomment the desired ip address and specify a\n'
                     '# hostname. To change a hostname, edit the hostname\n'
                     '# next to the desired ip address.\n'
                     '#192.168.1.4\n'
                     '5            host3.university.edu host3 '
                     '# No reverse assignment\n'
                     '#192.168.1.6                               \n'
                     '192.168.1.7  host5.university.edu host5 '
                     '# No reverse assignment\n')
    handle = open(INVALID_HOSTS, 'w')
    handle.writelines(file_contents)
    handle.close()
    output = os.popen('python %s update -f %s -v test_view -s %s -u %s -p '
                      '%s --config-file %s '
                      '--commit' % (
                          EXEC, INVALID_HOSTS, self.server_name, USERNAME,
                          PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
                     'CLIENT ERROR: Invalid ip address "5" in file '
                     '"test_data/invalid_hosts"\n')
    output.close()

  def testEdit(self):
    os.environ['EDITOR'] = ('python fake_editor.py "#192.168.1.6" '
                            '"192.168.1.6 host6.university.edu host6"')
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone_rev',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'ipv6host', u'ipv6_zone', {u'assignment_ip':
          u'2001:0000:0000:0000:0000:0000:0000:0001'}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host_ipv6', u'ipv6_zone', {u'assignment_ip':
          u'2001:0000:0000:0000:0000:0000:0000:0002'}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'ptr', u'1', u'ipv6_zone_rev', {u'assignment_host':
          u'ipv6host.university2.edu.'}, view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.1.0/24')
    self.core_instance.MakeReverseRangeZoneAssignment(u'ipv6_zone_rev',
                                                      u'2001::/124')
    output = os.popen(('python %s edit -r 192.168.1.4/30 -f %s --commit '
                       '--keep-output '
                      '-v test_view -s %s -u %s -p %s --config-file %s' % (
                           EXEC, TEST_FILE, self.server_name, USERNAME,
                           PASSWORD, USER_CONFIG)))
    self.assertEqual(output.read(),
        'Host: host6.university.edu with ip '
        'address 192.168.1.6 will be ADDED\n')
    output.close()
    handle = open(TEST_FILE, 'r')
    self.assertEqual(
        handle.read(),
        '#:range:192.168.1.4/30\n'
        '#:view_dependency:test_view_dep\n'
        '# Do not delete any lines in this file!\n'
        '# To remove a host, comment it out, to add a host,\n'
        '# uncomment the desired ip address and specify a\n'
        '# hostname. To change a hostname, edit the hostname\n'
        '# next to the desired ip address.\n'
        '#\n'
        '# The "@" symbol in the host column signifies inheritance\n'
        '# of the origin of the zone, this is just shorthand.\n'
        '# For example, @.university.edu. would be the same as\n'
        '# university.edu.\n'
        '#\n'
        '# Columns are arranged as so:\n'
        '# Ip_Address Fully_Qualified_Domain Hostname\n'
        '#192.168.1.4 host2.university.edu               '
        '# No forward assignment\n'
        '#192.168.1.5 host3.university.edu     host3     '
        '# No reverse assignment\n'
        '#192.168.1.5 www.host3.university.edu www.host3 '
        '# No reverse assignment\n'
        '192.168.1.6 host6.university.edu host6\n'
        '#192.168.1.7\n')

if( __name__ == '__main__' ):
  unittest.main()

