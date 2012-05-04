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

"""Regression test for roster_user_tools_bootstrap"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import os
import subprocess
import sys
import unittest


USER_CONFIG = 'test_data/roster_user_tools_test.conf'
EXEC = '../roster-user-tools/scripts/roster_user_tools_bootstrap'


class TestBootstrapper(unittest.TestCase):
  def testBootstrapper(self):
    output = os.popen('python %s -s https://localhost:8000 -c ~/.dnscred '
                      '--config-file %s' % (
                          EXEC, USER_CONFIG))
    output.close()

    config_file = open(USER_CONFIG, 'r')
    self.assertEqual(config_file.read(),
        '[user_tools]\n'
        'cred_file = %s/.dnscred\n'
        'server = https://localhost:8000\n\n' % os.path.expanduser('~'))
    config_file.close()

    os.remove(USER_CONFIG)

  def testBootstrapperMissingConfigFileArgument(self):
    command = subprocess.Popen('python %s -s https://localhost:8000 '
                               '-c ~/.dnscred' % (EXEC), shell=True,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    stdout = command.communicate()[0]
    self.assertEqual(stdout, 'ERROR: Config file MUST be specified with '
                             '--config-file\n')

  def testBootstrapperMissingServerArgument(self):
    command = subprocess.Popen('python %s -c ~/.dnscred --config-file %s' % (
                                   EXEC, USER_CONFIG), shell=True,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    stdout = command.communicate()[0]
    self.assertEqual(stdout, 'ERROR: Server MUST be specified with --server to '
                             'write the config file\n')

  def testBootstrapperMissingServerAndConfigFileArgument(self):
    command = subprocess.Popen('python %s -c ~/.dnscred' % (
                                   EXEC), shell=True,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    stdout = command.communicate()[0]
    self.assertEqual(stdout, 'ERROR: Server MUST be specified with --server to '
                             'write the config file\nERROR: Config file MUST '
                             'be specified with --config-file\n')

if( __name__ == '__main__' ):
      unittest.main()
