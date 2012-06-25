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
__version__ = '#TRUNK#'


import getpass
import os
import sys
import subprocess
import shutil
import socket
import time
import unittest

import roster_core

CONFIG_FILE = 'test_data/roster.conf'
EXEC = '../roster-config-manager/scripts/dnsversioncheck'
CORE_USERNAME = u'sharrell'
SSH_USERNAME = getpass.getuser()
TEST_DNS_SERVER = u'localhost'
CURRENT_BIND_VERSION = '9.9.0'

class TestBINDVersion(unittest.TestCase):
  def setUp(self):
    config_instance = roster_core.Config(CONFIG_FILE)
    core_instance = roster_core.Core(CORE_USERNAME, config_instance)

    if( TEST_DNS_SERVER not in core_instance.ListDnsServers() ):
      core_instance.MakeDnsServer(TEST_DNS_SERVER)

  def testVersion(self):    
    command = os.popen('service named status')
    words = command.read().strip('\n').split(' ')

    if( 'running...' not in words ):
      print 'named is not running, let me start it for you'
      os.system('sudo service named start')

    command = os.popen('python %s --ssh-user-name %s --core-user-name '
                       '%s --config-file %s' % (
            EXEC, SSH_USERNAME, CORE_USERNAME, CONFIG_FILE))
    lines = command.read().split('\n')

    self.assertTrue('Connecting to "%s"' % TEST_DNS_SERVER in lines)
    self.assertTrue('%s is running BIND %s' % (TEST_DNS_SERVER, 
                                               CURRENT_BIND_VERSION) in lines)
    self.assertTrue('All servers are running the same version of BIND' in lines)
    command.close()
    
if( __name__ == '__main__' ):
      unittest.main()
