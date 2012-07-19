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

"""Regression test for dnslsrecord

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
from roster_user_tools import roster_client_lib

USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC = '../roster-user-tools/scripts/dnslsrecord'

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

class TestDnslsRecord(unittest.TestCase):

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

    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')
    self.core_instance.MakeView(u'test_view')
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

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def retCode(self, code):
    if( code is None ):
      return 0
    return os.WEXITSTATUS(code)

  def testListAll(self):
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.0'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'machine2', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.1'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'hinfo', u'machine1', u'test_zone',
                                  {u'hardware': u'Pear', u'os': u'ipear'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine3', u'test_zone',
                                  {u'assignment_host':
                                       u'machine1.university.edu.'},
                                  view_name=u'test_view')
    command = os.popen('python %s all -v test_view -z test_zone -u %s '
                       '-p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'zone_name refresh_seconds target   name_server        record_type '
        'last_user minimum_seconds retry_seconds view_name ttl  serial_number '
        'admin_email     expiry_seconds\n'
        '------------------------------------------------------------------'
        '---------------------------------------------------------------------'
        '------------------------------\n'
        'test_zone 30              machine1 ns.university.edu. soa         '
        'sharrell  30              30            test_view 3600 123456794     '
        'university.edu. 30\n\n'
        'target   ttl  record_type view_name last_user zone_name '
        'assignment_ip\n'
        '--------------------------------------------------------'
        '-------------\n'
        'machine1 3600 a           test_view sharrell  test_zone 10.10.10.0\n'
        'machine2 3600 a           test_view sharrell  test_zone 10.10.10.1\n\n'
        'target   ttl  record_type view_name last_user zone_name '
        'assignment_host\n'
        '--------------------------------------------------------'
        '---------------\n'
        'machine3 3600 cname       test_view sharrell  test_zone '
        'machine1.university.edu.\n\n'
        'target   ttl  hardware record_type view_name last_user zone_name os\n'
        '-------------------------------------------------------------------\n'
        'machine1 3600 Pear     hinfo       test_view sharrell  test_zone '
        'ipear\n\n')
    command.close()

  def testListSameRecord(self):
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.0'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.1'},
                                  view_name=u'test_view')
    command = os.popen('python %s a -v test_view -z test_zone -u %s '
                       '--assignment-ip 10.10.10.0 '
                       '-p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name '
        'assignment_ip\n'
        '--------------------------------------------------------'
        '-------------\n'
        'machine1 3600 a           test_view sharrell  test_zone 10.10.10.0\n\n')
    command.close()

  def testAList(self):
    self.assertEqual(self.core_instance.ListZones(), {u'test_zone':
        {u'any': {'zone_type': u'master', 'zone_options': u'',
                  'zone_origin': u'test_zone.'},
         u'test_view': {'zone_type': u'master', 'zone_options': u'',
                        'zone_origin': u'test_zone.'}}})
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.0'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'machine2', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.1'},
                                  view_name=u'test_view')
    command = os.popen('python %s '
                       'a --assignment-ip="10.10.10.0" -t '
                       'machine1 -v test_view -z test_zone -u %s -p %s '
                       '--config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name '
        'assignment_ip\n'
        '--------------------------------------------------------'
        '-------------\n'
        'machine1 3600 a           test_view sharrell  test_zone 10.10.10.0\n\n')
    command.close()
    command = os.popen('python %s a -z test_zone -v test_view -u %s -p %s '
                       '--config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name '
        'assignment_ip\n'
        '--------------------------------------------------------'
        '-------------\n'
        'machine1 3600 a           test_view sharrell  test_zone 10.10.10.0\n'
        'machine2 3600 a           test_view sharrell  test_zone 10.10.10.1\n\n')
    command.close()

  def testAListNoHeader(self):
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.0'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'machine2', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.1'},
                                  view_name=u'test_view')
    command = os.popen('python %s a -z test_zone -v test_view -u %s -p %s '
                       '--config-file %s -s '
                       '%s --no-header' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'machine1 3600 a test_view sharrell test_zone 10.10.10.0\n'
        'machine2 3600 a test_view sharrell test_zone 10.10.10.1\n\n')
    command.close()

  def testAAAAList(self):
    self.core_instance.MakeRecord(
        u'aaaa', u'machine1', u'test_zone',
        {u'assignment_ip': u'fe80:0000:0000:0000:0200:f8ff:fe21:67cf'},
        view_name=u'test_view')
    command = os.popen('python %s '
                       'aaaa --assignment-ip="fe80::200:f8ff:fe21:67cf" '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name '
        'assignment_ip\n'
        '--------------------------------------------------------'
        '-------------\n'
        'machine1 3600 aaaa        test_view sharrell  test_zone '
        'fe80:0000:0000:0000:0200:f8ff:fe21:67cf\n\n')
    command.close()

  def testHINFOList(self):
    self.core_instance.MakeRecord(u'hinfo', u'machine1', u'test_zone',
                                  {u'hardware': u'Pear', u'os': u'ipear'},
                                  view_name=u'test_view')
    command = os.popen('python %s '
                       'hinfo --hardware Pear --os ipear '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
         'target   ttl  hardware record_type view_name last_user zone_name os\n'
         '-------------------------------------------------------------------\n'
         'machine1 3600 Pear     hinfo       test_view sharrell  test_zone '
         'ipear\n\n')
    command.close()

  def testTXTList(self):
    self.core_instance.MakeRecord(u'txt', u'machine1', u'test_zone',
                                  {u'quoted_text': u'et tu brute'},
                                  view_name=u'test_view')
    command = os.popen('python %s '
                       'txt --quoted-text "et tu brute" '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name quoted_text\n'
        '-------------------------------------------------------------------\n'
        'machine1 3600 txt         test_view sharrell  test_zone '
        'et tu brute\n\n')
    command.close()

  def testCNAMEList(self):
    self.core_instance.MakeRecord(u'cname', u'machine2', u'test_zone',
                                  {u'assignment_host': u'university.edu.'},
                                  view_name=u'test_view')
    command = os.popen('python %s '
                       'cname --assignment-host="university.edu." '
                       '-t machine2 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   ttl  record_type view_name last_user zone_name '
        'assignment_host\n'
        '--------------------------------------------------------'
        '---------------\n'
        'machine2 3600 cname       test_view sharrell  test_zone '
        'university.edu.\n\n')
    command.close()

  def testSOAList(self):
    command = os.popen('python %s '
                       'soa --name-server="ns.university.edu." '
                       '--serial-number=123456790 --refresh-seconds=30 '
                       '--retry-seconds=30 --minimum-seconds=30 '
                       '--expiry-seconds=30 --ttl=3600 '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'zone_name refresh_seconds target   name_server        record_type '
        'last_user minimum_seconds retry_seconds view_name ttl  serial_number '
        'admin_email     expiry_seconds\n'
        '------------------------------------------------------------------'
        '---------------------------------------------------------------------'
        '------------------------------\n'
        'test_zone 30              machine1 ns.university.edu. soa         '
        'sharrell  30              30            test_view 3600 123456790     '
        'university.edu. 30\n\n')
    command.close()

  def testSRVList(self):
    self.core_instance.MakeRecord(u'srv', u'machine1', u'test_zone',
                                  {u'priority': 5, u'weight': 6, u'port': 80,
                                   u'assignment_host': u'university.edu.'},
                                  view_name=u'test_view')
    command = os.popen('python %s srv '
                       '--priority 5 --weight 6 --port 80 '
                       '--assignment-host="university.edu." '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   weight last_user priority record_type view_name ttl  '
        'zone_name assignment_host port\n'
        '--------------------------------------------------------------'
        '------------------------------\n'
        'machine1 6      sharrell  5        srv         test_view 3600 '
        'test_zone university.edu. 80\n\n')
    command.close()

  def testNSList(self):
    self.core_instance.MakeRecord(u'ns', u'machine1', u'test_zone',
                                  {u'name_server': u'university.edu.'},
                                  view_name=u'test_view')
    command = os.popen('python %s '
                       'ns --name-server="university.edu." '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   name_server     ttl  record_type view_name last_user '
        'zone_name\n'
        '--------------------------------------------------------------'
        '---------\n'
        'machine1 university.edu. 3600 ns          test_view sharrell  '
        'test_zone\n\n')
    command.close()

  def testMXList(self):
    self.core_instance.MakeRecord(u'mx', u'machine1', u'test_zone',
                                  {u'mail_server': u'university.edu.',
                                   u'priority': 5},
                                  view_name=u'test_view')
    command = os.popen('python %s mx '
                       '--mail-server="university.edu." --priority 5 '
                       '-t machine1 -v test_view -z test_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
        'target   ttl  priority record_type view_name last_user zone_name '
        'mail_server\n'
        '-----------------------------------------------------------------'
        '-----------\n'
        'machine1 3600 5        mx          test_view sharrell  test_zone '
        'university.edu.\n\n')
    command.close()

  def testPTRList(self):
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'1.168.192.in-addr.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.1.4/30')
    self.core_instance.MakeRecord(u'ptr', u'4', u'reverse_zone',
                                  {u'assignment_host': u'university.edu.'},
                                  view_name=u'test_view')
    command = os.popen('python %s '
                       'ptr --assignment-host="university.edu." '
                       '-t 192.168.1.4 -v test_view -z reverse_zone -u '
                       '%s -p %s --config-file %s -s %s' % (
                           EXEC, USERNAME, self.password, USER_CONFIG,
                           self.server_name))
    self.assertEqual(command.read(),
         'target ttl  record_type view_name last_user zone_name    '
         'assignment_host\n'
         '---------------------------------------------------------'
         '---------------\n'
         '4      3600 ptr         test_view sharrell  reverse_zone '
         'university.edu.\n\n')
    command.close()

if( __name__ == '__main__' ):
    unittest.main()
