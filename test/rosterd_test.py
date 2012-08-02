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
__version__ = '0.17'


import os
import shutil
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
INACCESSABLE_LOCKFILE='test_data/lockfiledir/lockfile'

def PickUnusedPort():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((HOST, 0))
  addr, port = s.getsockname()
  s.close()
  return port
PORT = PickUnusedPort()

class StartServer(threading.Thread):
  def __init__(self, lockfile, port=7000):
    threading.Thread.__init__(self)
    self.lockfile = lockfile
    PORT = port;
    self.output = ''
    self.pid = None

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
    self.lockfile = self.config_instance.config_file['server']['lock_file']

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)
    command = os.popen('python %s --config-file %s --stop' % (
      EXEC, CONFIG_FILE))
    output = command.read()
    command.close()
    if( os.path.exists('test_data/lockfiledir') ):
      os.system('chmod 700 test_data/lockfiledir')
      shutil.rmtree('test_data/lockfiledir')

  def testStartServer(self):
    server = StartServer(self.lockfile, PORT)
    server.start()
    time.sleep(1)
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)
    time.sleep(1)
    server.join()
    self.assertEqual(server.getOutput(), '')

  def testKillServer(self):
    server = StartServer(self.lockfile, PORT)
    server.start()
    time.sleep(1)
    os.system('python %s --config-file %s --stop --lock-file %s' % (
      EXEC, CONFIG_FILE, self.lockfile))
    time.sleep(1)
    self.assertFalse(os.path.exists(self.lockfile))
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)
    command = os.popen('python %s --config-file %s --stop --lock-file %s' % (
      EXEC, CONFIG_FILE, self.lockfile))
    self.assertEqual(command.read(), 'ERROR: Lock file "%s" not found, is '
        'rosterd running?\n' % self.config_instance.config_file['server'][
            'lock_file'])
    command.close()

  def testWithLockfile(self):
    open(self.lockfile, 'w').close()
    server = StartServer(self.lockfile, PORT)
    server.start()
    time.sleep(1)
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)
    time.sleep(1)
    server.join()
    self.assertEqual(server.getOutput(),
                     'ERROR: Lockfile exists. Is rosterd running?\n')

  def testStartFakeFile(self):
    os.makedirs('test_data/lockfiledir')
    os.system('chmod 000 test_data/lockfiledir')
    server = StartServer(INACCESSABLE_LOCKFILE)
    server.start()
    time.sleep(1)
    if( os.path.exists(INACCESSABLE_LOCKFILE) ):
      os.remove(INACCESSABLE_self.lockfile)
    time.sleep(1)
    server.join()
    os.system('chmod 700 test_data/lockfiledir')
    os.system('rm -rf test_data/lockfiledir') # Need force flag
    self.assertEqual(server.getOutput(),
                     'ERROR: Could not access lock file '
                     '"test_data/lockfiledir/lockfile". '
                     'Do you have permission?\n')

  def testStartWorldFile(self):
    server = StartServer(self.lockfile, PORT)
    os.system('chmod 777 %s' % CONFIG_FILE)
    server.start()
    time.sleep(1)
    if( os.path.exists(self.lockfile) ):
      os.remove(self.lockfile)
    time.sleep(1)
    server.join()
    os.system('chmod 700 %s' % CONFIG_FILE)
    self.assertEqual(server.getOutput(),
                     'ERROR: Roster will not start if the config file is world '
                     'readable, world executable, or world writable. '
                     'Please change the permissions of '
                     '"%s"\n' % CONFIG_FILE)

if( __name__ == '__main__' ):
      unittest.main()
