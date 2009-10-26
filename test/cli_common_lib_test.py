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

"""Regression test for dnslshost

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import os
from optparse import OptionParser
import sys
import socket
import threading
import time
import getpass
import unittest


import roster_core
import roster_server
from roster_user_tools  import cli_common_lib
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
  target = u'machine1'
  ttl = 64

class DnsError(Exception):
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

class Testdnslshost(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    schema = open(SCHEMA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.CommitTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.CommitTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_thread = DaemonThread(self.config_instance, self.port)
    self.daemon_thread.start()
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def NewDnsError(self, message, exit_status=0):
    raise DnsError('ERROR: %s\n' % message)

  def testPrintColumns(self):
    options.server = self.server_name
    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    cli_common_lib_instance.DnsError = self.NewDnsError
    self.assertEqual(cli_common_lib_instance.PrintColumns(
        [['1', '2', '3'], ['long line', 'b', 'c']]),
        '1         2 3\nlong line b c\n')
    self.assertEqual(cli_common_lib_instance.PrintColumns(
        [['1', '2', '3'], ['long line', 'b', 'c']], first_line_header=True),
        '1         2 3\n-------------\nlong line b c\n')

  def testPrintRecords(self):
    records_dictionary = {
        'test_view': {'192.168.1.5': [
            {'forward': False, 'host': 'host3.university.edu',
             'zone_origin': '1.168.192.in-addr.arpa.',
             'zone': 'reverse_zone'}]},
        'any': {'192.168.1.5': [
            {'forward': True, 'host': 'host3.university.edu',
             'zone_origin': 'university.edu.', 'zone': 'forward_zone'}]}}
    options.server = self.server_name
    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    self.assertEqual(cli_common_lib_instance.PrintRecords(records_dictionary),
                     '192.168.1.5 Reverse host3.university.edu reverse_zone '
                     'test_view\n192.168.1.5 Forward host3.university.edu '
                     'forward_zone any\n')
    self.assertEqual(cli_common_lib_instance.PrintRecords(
        records_dictionary, [u'192.168.1.5']),
        u'192.168.1.5 Reverse host3.university.edu reverse_zone test_view\n'
        '192.168.1.5 Forward host3.university.edu forward_zone any\n')

  def testPrintHosts(self):
    records_dictionary = {
        'test_view': {'192.168.1.5': [
            {'forward': False, 'host': 'host3.university.edu',
             'zone_origin': '1.168.192.in-addr.arpa.',
             'zone': 'reverse_zone'}]},
        'any': {'192.168.1.5': [
            {'forward': True, 'host': 'host3.university.edu',
             'zone_origin': 'university.edu.', 'zone': 'forward_zone'}]}}
    options.server = self.server_name
    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    self.assertEqual(cli_common_lib_instance.PrintHosts(
        records_dictionary, [u'192.168.1.5'], view_name='any'),
        u'192.168.1.5 host3.university.edu host3 # No reverse assignment\n')

  def testCheckCredentials(self):
    options.server = self.server_name
    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    cli_common_lib_instance.DnsError = self.NewDnsError
    self.assertEqual(cli_common_lib_instance.CheckCredentials(), None)

    cli_common_lib_instance.options.credfile = None
    self.assertRaises(DnsError, cli_common_lib_instance.CheckCredentials)

    cli_common_lib_instance.options.credfile = options.credfile
    cli_common_lib_instance.username = u'fakeuser'
    self.assertRaises(DnsError, cli_common_lib_instance.CheckCredentials)

  def testDisallowFlags(self):
    parser = OptionParser()
    parser.add_option('-u', '--username', action='store', dest='username')

    options.server = self.server_name
    cli_common_lib_instance = cli_common_lib.CliCommonLib(options)
    cli_common_lib_instance.DnsError = self.NewDnsError

    self.assertRaises(DnsError, cli_common_lib_instance.DisallowFlags,
                      ['username'], parser)


if( __name__ == '__main__' ):
      unittest.main()
