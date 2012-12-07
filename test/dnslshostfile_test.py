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

"""Regression test for dnslshostfile

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


import roster_core
import roster_server
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
EXEC='../roster-user-tools/scripts/dnslshostfile'

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

class Testdnslshostfile(unittest.TestCase):

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
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view2')
    self.core_instance.MakeZone(u'ipv6zone', u'master',
                                u'8.0.e.f.f.3.ip6.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'forward_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'forward_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view3')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
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
         u'minimum_seconds': 5}, view_name=u'test_view2')
    self.core_instance.MakeRecord(
        u'aaaa', u'host2', u'forward_zone', {u'assignment_ip':
            u'4321:0000:0001:0002:0003:0004:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host1', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.1'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host2', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.11'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.5'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host4', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.10'},
                                  view_name=u'any')
    self.core_instance.MakeRecord(u'a', u'host5', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.17'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host6', u'forward_zone',
                                  {u'assignment_ip': u'192.168.1.8'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'8',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host6.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'4',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host2.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'5',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host3.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'10',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host4.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'7',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host5.university.edu.'},
                                  view_name=u'test_view2')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testListHostFile(self):
    output = os.popen('python %s -d university.edu -s %s '
                      '-v test_view -u %s -p %s --config-file %s' % (
                       EXEC, self.server_name, USERNAME,
                       PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
            '127.1\tlocalhost loghost\n'
            '192.168.0.1\thost1.university.edu host1\n'
            '192.168.1.5\thost3.university.edu host3\n'
            '192.168.1.8\thost6.university.edu host6\n'
            '192.168.1.10\thost4.university.edu host4\n'
            '4321:0000:0001:0002:0003:0004:0567:89ab\thost2.university.edu host2\n')
    output.close()

    output = os.popen('python %s -d edu -s %s '
                      '-v test_view -u %s -p %s --config-file %s' % (
                       EXEC, self.server_name, USERNAME,
                       PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
            '127.1\tlocalhost loghost\n'
            '192.168.0.1\thost1.university.edu host1.university\n'
            '192.168.1.5\thost3.university.edu host3.university\n'
            '192.168.1.8\thost6.university.edu host6.university\n'
            '192.168.1.10\thost4.university.edu host4.university\n'
            '4321:0000:0001:0002:0003:0004:0567:89ab\thost2.university.edu host2.university\n')
    output.close()

    output = os.popen('python %s -d university.edu -s %s '
                      '-v any -u %s -p %s --config-file %s' % (
                       EXEC, self.server_name, USERNAME,
                       PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        '127.1\tlocalhost loghost\n'
        '192.168.1.10\thost4.university.edu host4\n')
    output.close()

    output = os.popen('python %s -d university.edu -s %s '
                      '-v test_view2 -u %s -p %s --config-file %s' % (
                       EXEC, self.server_name, USERNAME,
                       PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        '127.1\tlocalhost loghost\n'
        '192.168.1.10\thost4.university.edu host4\n')
    output.close()

    output = os.popen('python %s -d university.edu -s %s '
                      '-v test_view3 -u %s -p %s --config-file %s' % (
                       EXEC, self.server_name, USERNAME,
                       PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        '127.1\tlocalhost loghost\n'
        '192.168.1.10\thost4.university.edu host4\n'
        '192.168.1.11\thost2.university.edu host2\n'
        '192.168.1.17\thost5.university.edu host5\n')
    output.close()

  def testCNAMEChaining(self):
    self.core_instance.MakeRecord(u'cname', u'cname1', u'forward_zone', 
        {u'assignment_host': u'host1.university.edu.'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'cname12', u'forward_zone',
        {u'assignment_host': u'cname1.university.edu.'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'cname13', u'forward_zone',
        {u'assignment_host': u'cname12.university.edu.'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'ipv6', u'forward_zone',
        {u'assignment_host': u'host2.university.edu.'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'cname2', u'forward_zone',
        {u'assignment_host': u'host2.university.edu.'}, view_name=u'test_view3')
    self.core_instance.MakeRecord(u'cname', u'cname3', u'forward_zone',
        {u'assignment_host': u'host3.university.edu.'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'cname4', u'forward_zone',
        {u'assignment_host': u'host4.university.edu.'}, view_name=u'any')
    self.core_instance.MakeRecord(u'cname', u'cname4_2', u'forward_zone',
        {u'assignment_host': u'host4.university.edu.'}, view_name=u'any')
    
    output = os.popen('python %s -d university.edu -s %s '
                      '-v test_view -u %s -p %s --config-file %s' % (
                      EXEC, self.server_name, USERNAME,
                      PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
            '127.1\tlocalhost loghost\n'
            '192.168.0.1\thost1.university.edu host1 '
                         'cname1.university.edu cname1 '
                         'cname12.university.edu cname12 '
                         'cname13.university.edu cname13\n'
            '192.168.1.5\thost3.university.edu host3 '
                         'cname3.university.edu cname3\n'
            '192.168.1.8\thost6.university.edu host6\n'
            '192.168.1.10\thost4.university.edu host4 '
                          'cname4_2.university.edu cname4_2 '
                          'cname4.university.edu cname4\n'
            '4321:0000:0001:0002:0003:0004:0567:89ab\thost2.university.edu host2 '
                                                     'ipv6.university.edu ipv6\n')
    output.close()

    output = os.popen('python %s -d university.edu -s %s '
                      '-v test_view3 -u %s -p %s --config-file %s' % (
                      EXEC, self.server_name, USERNAME,
                      PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        '127.1\tlocalhost loghost\n'
        '192.168.1.10\thost4.university.edu host4 '
                     'cname4_2.university.edu cname4_2 '
                     'cname4.university.edu cname4\n'
        '192.168.1.11\thost2.university.edu host2 '
                      'cname2.university.edu cname2\n'
        '192.168.1.17\thost5.university.edu host5\n')
    output.close()

    output = os.popen('python %s -d university.edu -s %s '
                      '-v any -u %s -p %s --config-file %s' % (
                       EXEC, self.server_name, USERNAME,
                       PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
        '127.1\tlocalhost loghost\n'
        '192.168.1.10\thost4.university.edu host4 '
                     'cname4_2.university.edu cname4_2 '
                     'cname4.university.edu cname4\n')
    output.close()

  def testIPv6Addresses(self):
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host1', u'forward_zone',
        {u'assignment_ip': u'4321:0000:0000:0000:0000:0000:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host2', u'forward_zone',
        {u'assignment_ip': u'4321:0000:0000:0000:0000:0000:0567:f8ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host3', u'forward_zone',
        {u'assignment_ip': u'4321:0000:0000:0002:0003:0004:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host4', u'forward_zone',
        {u'assignment_ip': u'4321:0000:0000:0000:0001:0000:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host5', u'forward_zone',
        {u'assignment_ip': u'1234:0000:0000:0000:0000:0000:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host6', u'forward_zone',
        {u'assignment_ip': u'1234:0000:0000:0000:0000:0000:4321:0fed'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host7', u'forward_zone',
        {u'assignment_ip': u'ffff:0000:0000:0000:0000:0000:0000:fffe'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host8', u'forward_zone',
        {u'assignment_ip': u'0000:0000:0000:0000:0000:0000:0000:0001'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host9', u'forward_zone',
        {u'assignment_ip': u'0000:0000:0000:0000:0000:0000:c0a8:0104'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'aaaa', u'ipv6host10', u'forward_zone',
        {u'assignment_ip': u'0000:0000:0000:0000:0000:0000:c0a8:0109'}, view_name=u'test_view')

    output = os.popen('python %s -d university.edu -s %s '
                      '-v test_view -u %s -p %s --config-file %s' % (
                      EXEC, self.server_name, USERNAME,
                      PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 
        '127.1\tlocalhost loghost\n'
        '0000:0000:0000:0000:0000:0000:0000:0001\tipv6host8.university.edu ipv6host8\n'
        '192.168.0.1\thost1.university.edu host1\n'
        '0000:0000:0000:0000:0000:0000:c0a8:0104\tipv6host9.university.edu ipv6host9\n'
        '192.168.1.5\thost3.university.edu host3\n'
        '192.168.1.8\thost6.university.edu host6\n'
        '0000:0000:0000:0000:0000:0000:c0a8:0109\tipv6host10.university.edu ipv6host10\n'
        '192.168.1.10\thost4.university.edu host4\n'
        '1234:0000:0000:0000:0000:0000:0567:89ab\tipv6host5.university.edu ipv6host5\n'
        '1234:0000:0000:0000:0000:0000:4321:0fed\tipv6host6.university.edu ipv6host6\n'
        '4321:0000:0000:0000:0000:0000:0567:89ab\tipv6host1.university.edu ipv6host1\n'
        '4321:0000:0000:0000:0000:0000:0567:f8ab\tipv6host2.university.edu ipv6host2\n'
        '4321:0000:0000:0000:0001:0000:0567:89ab\tipv6host4.university.edu ipv6host4\n'
        '4321:0000:0000:0002:0003:0004:0567:89ab\tipv6host3.university.edu ipv6host3\n'
        '4321:0000:0001:0002:0003:0004:0567:89ab\thost2.university.edu host2\n'
        'ffff:0000:0000:0000:0000:0000:0000:fffe\tipv6host7.university.edu ipv6host7\n')
    output.close()

if( __name__ == '__main__' ):
      unittest.main()
