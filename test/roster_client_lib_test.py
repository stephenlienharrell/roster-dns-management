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

"""Regression test for roster_client_lib

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
  def __init__(self):
    self.stdout = []

  def write(self, text):
    self.stdout.append(text)

  def flush(self):
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

class TestRosterClientLib(unittest.TestCase):
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
    self.daemon_thread.start()
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, PASSWORD, credfile=CREDFILE,
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

  def testRunFunction(self):
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'university.edu.',
                                view_name=u'test_view')

    zones = roster_client_lib.RunFunction(
        u'ListZones', USERNAME, CREDFILE,
        server_name=self.server_name, password=PASSWORD)['core_return']
    self.assertEqual(
        zones,
        {'test_zone': {'test_view': {'zone_type':
            'master', 'zone_options': '', 'zone_origin': 'university.edu.'},
         'any': {'zone_type': 'master', 'zone_options': '',
                 'zone_origin': 'university.edu.'}}})

    credfile_handle = open(CREDFILE, 'w')
    credfile_handle.writelines('invalid_file')
    credfile_handle.close()
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    self.assertRaises(
        SystemExit, roster_client_lib.RunFunction,
        u'ListZones', USERNAME, CREDFILE,
        server_name=self.server_name, password='wrong')

    invalid_credfile = '/fake/credfile'
    self.assertEqual(sys.stdout.flush(),
                     'ERROR: Incorrect username/password.\n')
    self.assertRaises(
        SystemExit, roster_client_lib.RunFunction,
        u'ListZones', USERNAME, CREDFILE,
        server_name=self.server_name, password='wrong')
    self.assertEqual(sys.stdout.flush(),
                     'ERROR: Incorrect username/password.\n')
    sys.stdout = oldstdout

  def testGetCredentials(self):
    credential = roster_client_lib.GetCredentials(
        USERNAME, PASSWORD, CREDFILE, server_name=self.server_name)
    self.assertEqual(len(str(credential)), 36)

  def testCheckCredentials(self):
    self.assertEqual(roster_client_lib.CheckCredentials(
        USERNAME, CREDFILE, self.server_name, password=PASSWORD), None)

  def testIsAuthenticated(self):
    self.assertTrue(roster_client_lib.IsAuthenticated(
        USERNAME, CREDFILE, server_name=self.server_name))


if( __name__ == '__main__' ):
      unittest.main()
