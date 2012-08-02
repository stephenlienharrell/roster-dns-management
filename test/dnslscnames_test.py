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

"""Regression test for dnslscnames

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.17'


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
EXEC = '../roster-user-tools/scripts/dnslscnames'

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

    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'university.edu.',
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

  def testListCNAMEsNonRecursive(self):
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.0'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'machine2', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.1'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine3', u'test_zone',
                                  {u'assignment_host':
                                   u'machine1.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine4', u'test_zone',
                                  {u'assignment_host':
                                   u'machine2.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine5', u'test_zone',
                                  {u'assignment_host':
                                   u'machine1.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine5a', u'test_zone',
                                  {u'assignment_host':
                                   u'machine5.university.edu.'},
                                  view_name=u'test_view')
    command = os.popen('python %s cname -v test_view -z test_zone '
                       '--hostname %s -u %s -p %s --config-file %s -s %s' % (
                           EXEC, u'machine1.university.edu.', USERNAME,
                           self.password, USER_CONFIG, self.server_name))
    self.assertEqual(command.read(),
        'target   assignment_host\n'
        '------------------------\n'
        'machine3 machine1.university.edu.\n'
        'machine5 machine1.university.edu.\n\n')
    command.close()

  def testListCNAMEsRecursive(self):
    self.core_instance.MakeRecord(u'a', u'machine1', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.0'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'machine2', u'test_zone',
                                  {u'assignment_ip': u'10.10.10.1'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine3', u'test_zone',
                                  {u'assignment_host':
                                   u'machine1.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine4', u'test_zone',
                                  {u'assignment_host':
                                   u'machine2.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine5', u'test_zone',
                                  {u'assignment_host':
                                   u'machine1.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine5a', u'test_zone',
                                  {u'assignment_host':
                                   u'machine5.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'cname', u'machine4a', u'test_zone',
                                  {u'assignment_host':
                                   u'machine4.university.edu.'},
                                  view_name=u'test_view')
    command = os.popen('python %s cname -v test_view -z test_zone '
                       '--hostname %s -u %s -p %s --config-file %s -s %s -r' % (
                           EXEC, u'machine1.university.edu.', USERNAME,
                           self.password, USER_CONFIG, self.server_name))
    output = command.read()
    self.assertEqual(output,
        'target    assignment_host\n'
        '-------------------------\n'
        'machine3  machine1.university.edu.\n'
        'machine5  machine1.university.edu.\n'
        'machine5a machine5.university.edu.\n\n')
    command.close()

    command = os.popen('python %s cname -v test_view -z test_zone '
                       '--hostname %s -u %s -p %s --config-file %s -s %s -r' % (
                           EXEC, u'machine2.university.edu.', USERNAME,
                           self.password, USER_CONFIG, self.server_name))
    output = command.read()
    self.assertEqual(output,
        'target    assignment_host\n'
        '-------------------------\n'
        'machine4  machine2.university.edu.\n'
        'machine4a machine4.university.edu.\n\n')
    command.close()

if( __name__ == '__main__' ):
    unittest.main()
