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

"""Regression test for rosterd

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.12'


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
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC='../roster-server/scripts/rosterd'
LOCKFILE='test_data/lockfile'

class StartServer(threading.Thread):
  def __init__(self, lockfile):
    threading.Thread.__init__(self)
    self.lockfile = lockfile
    self.output = ''

  def run(self):
    command = os.popen(
        'python %s -c %s -k %s --config-file %s --lock-file %s '
        '-H localhost -p 7000' % (
            EXEC, CERTFILE, KEYFILE, CONFIG_FILE, self.lockfile))
    self.output = command.read()
    command.close()

  def getOutput(self):
    return self.output

class TestRosterd(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    schema = roster_core.embedded_files.SCHEMA_FILE
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()
    open(LOCKFILE, 'w').close()

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testStartServer(self):
    server = StartServer(LOCKFILE)
    os.system('chmod 700 %s' % LOCKFILE)
    server.start()
    time.sleep(1)
    if( os.path.exists(LOCKFILE) ):
      os.remove(LOCKFILE)
    time.sleep(1)
    server.join()
    self.assertEqual(server.getOutput(), '')

  def testStartFakeFile(self):
    server = StartServer(LOCKFILE)
    os.system('chmod 000 %s' % LOCKFILE)
    server.start()
    time.sleep(1)
    if( os.path.exists(LOCKFILE) ):
      os.remove(LOCKFILE)
    time.sleep(1)
    server.join()
    self.assertEqual(server.getOutput(),
                     'ERROR: Could not access lock file "test_data/lockfile". '
                     'Do you have permission?\n')

  def testStartWorldFile(self):
    server = StartServer(LOCKFILE)
    os.system('chmod 777 %s' % CONFIG_FILE)
    server.start()
    time.sleep(1)
    if( os.path.exists(LOCKFILE) ):
      os.remove(LOCKFILE)
    time.sleep(1)
    server.join()
    os.system('chmod 700 %s' % CONFIG_FILE)
    self.assertEqual(server.getOutput(),
                     'ERROR: Roster will not start with a world writable '
                     'config file. Please change the permissions of '
                     '"%s"\n' % CONFIG_FILE)

if( __name__ == '__main__' ):
      unittest.main()
