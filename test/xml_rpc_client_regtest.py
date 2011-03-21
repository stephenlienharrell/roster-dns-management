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


"""Test for XML client and server.

The server must be running to run this test.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import os
import socket
import sys
import threading
import time
import unittest

import fake_credentials

import roster_core
from roster_user_tools import roster_client_lib
import roster_server
from roster_server import credentials
from roster_config_manager import tree_exporter

CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='test_data/dnscred'
PASSWORD='test'

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

class DaemonThread(threading.Thread):
  def __init__(self, config_instance, port, daemon_instance):
    threading.Thread.__init__(self)
    self.config_instance = config_instance
    self.port = port
    self.daemon_instance = daemon_instance

  def run(self):
    self.daemon_instance.Serve(port=self.port)

class TestXMLServerClient(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.cred_instance = credentials.CredCache(self.config_instance, 5)

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_instance = roster_server.Server(self.config_instance, KEYFILE,
                                                CERTFILE,
                                                inf_renew_time=5,
                                                core_die_time=5, clean_time=0)

    self.daemon_thread = DaemonThread(self.config_instance, self.port,
                                      self.daemon_instance)
    self.daemon_thread.daemon = True
    self.daemon_thread.start()
    time.sleep(1)
    ## Will create a core_instance in core_store
    self.credential = roster_client_lib.GetCredentials(
        USERNAME, PASSWORD, server_name=self.server_name)
    self.daemon_instance.core_store = [] # Clear out core instance from above

    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testCredFile(self):
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    self.assertRaises(
        SystemExit, roster_client_lib.RunFunction, u'ListUsers', USERNAME,
        server_name=self.server_name, password=PASSWORD, credfile=CREDFILE)
    self.assertEqual(sys.stdout.flush(),
                     'ERROR: Credential file not found, invalid credentials.\n')
    sys.stdout = oldstdout
    # create credential file for RunFunction
    roster_client_lib.GetCredentials(u'shuey', u'testpass',
                                     server_name=self.server_name,
                                     credfile=CREDFILE)
    # using file from function above
    self.assertEqual(roster_client_lib.RunFunction(
                         u'ListUsers', u'shuey', credfile=CREDFILE,
                         server_name=self.server_name,
                         password=PASSWORD)['core_return'],
                     {'shuey': 64, 'tree_export_user': 0, 'jcollins': 32,
                      'sharrell': 128})

  def testCredsStrings(self):
    credstring = u'81ffc6ea-4b38-45e2-8fce-e24636672b27'
    self.core_instance._MakeCredential(credstring, u'shuey', infinite_cred=True)
    self.assertEqual(roster_client_lib.RunFunction(
        u'ListUsers', USERNAME, credstring=credstring,
        server_name=self.server_name, password=PASSWORD)['core_return'],
                     {u'shuey': 64, u'tree_export_user': 0, u'jcollins': 32,
                      u'sharrell': 128})
    self.assertEqual(roster_client_lib.RunFunction(
        u'ListUsers', USERNAME, credstring=credstring,
        server_name=self.server_name, password=PASSWORD)['core_return'],
                     {u'shuey': 64, 'tree_export_user': 0, u'jcollins': 32,
                      u'sharrell': 128})
    time.sleep(10)
    function_return = roster_client_lib.RunFunction(
        u'ListUsers', USERNAME,credstring=credstring,
        server_name=self.server_name, password=PASSWORD)
    self.assertEqual(function_return['core_return'],
                     {u'shuey': 64, 'tree_export_user': 0, u'jcollins': 32,
                      u'sharrell': 128})
    if( function_return['new_credential'] != u'' ):
      credstring = function_return['new_credential']
    self.assertEqual(roster_client_lib.RunFunction(
        u'ListUsers', USERNAME, credstring=credstring,
        server_name=self.server_name, password=PASSWORD)['core_return'],
                     {u'shuey': 64, 'tree_export_user': 0, u'jcollins': 32,
                      u'sharrell': 128})

  def testNoArgsClient(self):
    self.assertEqual(roster_client_lib.RunFunction(
        u'ListUsers', USERNAME, credstring=self.credential,
        server_name=self.server_name, password=PASSWORD)['core_return'],
                     {u'shuey': 64, 'tree_export_user': 0, u'jcollins': 32,
                      u'sharrell': 128})

  def testArgsOnlyClient(self):
    roster_client_lib.RunFunction(u'MakeUser', USERNAME, args=[u'jake\xc6', 64],
                                  credstring=self.credential,
                                  server_name=self.server_name,
                                  password=PASSWORD)
    self.assertEqual(roster_client_lib.RunFunction(
        u'ListUsers', USERNAME, credstring=self.credential,
        server_name=self.server_name, password=PASSWORD)['core_return'],
        {u'shuey': 64, u'tree_export_user': 0, u'jcollins': 32,
         u'sharrell': 128, u'jake\xc6': 64})
    self.assertTrue(roster_client_lib.RunFunction(
        u'RemoveUser', USERNAME, args=[u'shuey'], credstring=self.credential,
        server_name=self.server_name, password=PASSWORD)['core_return'])
    self.assertEqual(roster_client_lib.RunFunction(
        u'ListUsers', USERNAME, credstring=self.credential,
        server_name=self.server_name, password=PASSWORD)['core_return'],
        {u'jcollins': 32, u'tree_export_user': 0, u'jake\xc6': 64,
         u'sharrell': 128})

  def testKWArgsOnlyClient(self):
    self.assertEqual(roster_client_lib.RunFunction(
        u'ListUserGroupAssignments', USERNAME, credstring=self.credential,
        kwargs={'key_by_group': True}, server_name=self.server_name,
        password=PASSWORD)['core_return'],
        {'bio': ['shuey'], 'cs': ['sharrell', 'shuey']})

  def testKWArgsAndArgsClient(self):
    roster_client_lib.RunFunction(
          u'MakeUserGroupAssignment', USERNAME, credstring=self.credential,
          args=[u'sharrell', u'bio'], server_name=self.server_name,
          password=PASSWORD)['core_return']
    self.assertEqual(
        roster_client_lib.RunFunction(
            u'ListUserGroupAssignments', USERNAME, credstring=self.credential,
            kwargs={'key_by_group': True}, server_name=self.server_name,
            password=PASSWORD)['core_return'], {'bio': ['sharrell', 'shuey'],
                               'cs': ['sharrell', 'shuey']})

  def testMultipleThreadedConnections(self):
    self.daemon_instance.core_die_time = 7200
    roster_client_lib.RunFunction(u'MakeZone', USERNAME,
                                  credstring=self.credential,
                                  args=['new_zone', 'forward',
                                        'zone.com.'],
                                  server_name=self.server_name,
                                  password=PASSWORD)
    client_threads = []
    for current_number in range(50):
      new_client_thread = ClientRecordModifyThread(
          USERNAME, '192.168.0.%s' % current_number,
          'host%s' % current_number, self.credential, self)
      new_client_thread.daemon = True
      new_client_thread.start()
      client_threads.append(new_client_thread)

    for old_thread in client_threads:
      old_thread.join()

  def testMultipleThreadedConnectionsWithDifferentUsers(self):
    data_exporter = tree_exporter.BindTreeExport(CONFIG_FILE)
    self.daemon_instance.core_die_time = 7200
    roster_client_lib.RunFunction(u'MakeZone', USERNAME,
                                  credstring=self.credential,
                                  args=['new_zone', 'forward',
                                        'zone.com.'],
                                  server_name=self.server_name,
                                  password=PASSWORD)

    cred_dict = {}
    for user_number in range(40):

      roster_client_lib.RunFunction(u'MakeUser', USERNAME,
                                    credstring=self.credential,
                                    args=['user%s' % user_number, 128],
                                    server_name=self.server_name)
      cred_dict['user%s' % user_number] = roster_client_lib.GetCredentials(
          'user%s' % user_number, 'tost', server_name=self.server_name)

    client_threads = []
    for record_number in range(5):
      for user_number in range(40):
        new_client_thread = ClientRecordModifyThread(
            'user%s' % user_number, '192.168.%s.%s' % (
                user_number, record_number),
            'host%s-%s' % (user_number, record_number),
            cred_dict['user%s' % user_number], self)
        new_client_thread.daemon = True
        new_client_thread.start()
        client_threads.append(new_client_thread)
      data_exporter.db_instance.StartTransaction()
      try:
        data_exporter.db_instance.LockDb()
        try:
          data_exporter.GetRawData()
        finally:
          data_exporter.db_instance.UnlockDb()
      finally:
        data_exporter.db_instance.EndTransaction()

    for old_thread in client_threads:
      old_thread.join()

class ClientRecordModifyThread(threading.Thread):
  def __init__(self, user_name, ip_address, host_name, credential,
               test_instance):
    threading.Thread.__init__(self)
    self.ip_address = ip_address
    self.host_name = host_name
    self.test_instance = test_instance
    self.user_name = user_name
    self.credential = credential
    self.thread_name = user_name + host_name + ip_address
    self.setName(self.thread_name)

  def run(self):
    self.test_instance.assertEqual(
        roster_client_lib.RunFunction(
            u'ListRecords', self.user_name,
            credstring=self.credential,
            kwargs={'target': self.host_name},
            server_name=self.test_instance.server_name)['core_return'], [])

    roster_client_lib.RunFunction(
        u'MakeRecord', self.user_name, credstring=self.credential,
        args=['a', self.host_name, 'new_zone',
              {'assignment_ip': self.ip_address}],
        server_name=self.test_instance.server_name)

    self.test_instance.assertEqual(
        roster_client_lib.RunFunction(
            u'ListRecords', self.user_name,
            credstring=self.credential,
            kwargs={'target': self.host_name},
            server_name=self.test_instance.server_name)['core_return'],
        [{'target': self.host_name, 'ttl': 3600, 'record_type': 'a',
          'view_name': 'any', 'last_user': self.user_name,
          'zone_name': 'new_zone', 'assignment_ip': self.ip_address}])

    roster_client_lib.RunFunction(
        u'RemoveRecord', self.user_name,
        credstring=self.credential,
        args=['a', self.host_name, 'new_zone',
              {'assignment_ip': self.ip_address}, 'any'],
        server_name=self.test_instance.server_name)

    self.test_instance.assertEqual(
        roster_client_lib.RunFunction(
            u'ListRecords', self.user_name,
            credstring=self.credential,
            kwargs={'target': self.host_name},
            server_name=self.test_instance.server_name)['core_return'], [])

if( __name__ == '__main__' ):
  unittest.main()
