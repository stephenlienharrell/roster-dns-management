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

"""Regression test for dnsversioncheck"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.18'


import getpass
import os
import sys
import subprocess
import shutil
import socket
import time
import unittest
import re

import roster_core

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnsversioncheck'
CORE_USERNAME = u'sharrell'
TEST_DNS_SERVER = u'localhost'
TESTDIR = u'%s/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/named/' % os.getcwd()
SSH_USER = unicode(getpass.getuser())
DATA_FILE = 'test_data/test_data.sql'

class TestBINDVersion(unittest.TestCase):
  def setUp(self):
    config_instance = roster_core.Config(CONFIG_FILE)
    db_instance = config_instance.GetDb()
    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    core_instance = roster_core.Core(CORE_USERNAME, config_instance)
    core_instance.MakeDnsServer(TEST_DNS_SERVER, SSH_USER, BINDDIR, TESTDIR)

  def testVersion(self):    
    named_command = subprocess.Popen(['service', 'named', 'status'], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    named_command.communicate()

    if( named_command.returncode ):
      print 'Named must be running for this unittest, let me start it for you' 
      os.system('sudo service named start')
      time.sleep(5)

    command = os.popen('python %s --ssh-user-name %s --core-user-name '
                       '%s --config-file %s' % (
            EXEC, SSH_USER, CORE_USERNAME, CONFIG_FILE))
    command_output = command.read()
    lines = command_output.split('\n')
    command.close()

    self.assertTrue('Connecting to "%s"' % TEST_DNS_SERVER in lines)
    #Not making this BIND version specific. 
    self.assertTrue(re.search(
        '%s is running BIND [0-9].[0-9].[0-9]' % TEST_DNS_SERVER, command_output))
    self.assertTrue('All servers are running the same version of BIND' in lines)
    
if( __name__ == '__main__' ):
      unittest.main()
