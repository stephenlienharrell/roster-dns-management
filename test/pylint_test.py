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

"""pylint unit test
  Checks code for style errors.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'

import unittest
import subprocess
import shlex
import os
import re


PYLINT_CMD = 'pylint --rcfile pylint.rc'
CORE_DIR = '../roster-core/roster_core'
SERVER_DIR = '../roster-server/roster_server'
CONFIG_DIR = '../roster-config-manager/roster_config_manager'
USER_DIR = '../roster-user-tools/roster_user_tools'
TEST_DIR = '.'


def pylint_dir(directory, mask='.py$'):
  """
    Input:
      directory (string): a string of the directory file is in
      mask (string): a regexp to match files
    Output:
      (list): a list of all the outputs generated
  """
  file_list = os.listdir(directory)
  lint_output_list = []
  for filename in file_list:
    if re.search(mask, filename) and filename != '.svn':
      lint_command = shlex.split('%s %s/%s' % (PYLINT_CMD, directory, filename))
      lint_process = subprocess.Popen(lint_command, stderr=subprocess.STDOUT,
          stdout=subprocess.PIPE)
      lint_output = lint_process.communicate()
      if lint_output[0] != '':
        lint_output_list.append(lint_output[0])
  return lint_output_list


class TestPythonStyle(unittest.TestCase):
  def test_core(self):
    lint_output = pylint_dir(CORE_DIR)
    for output in lint_output:
      print(output)
    lint_output2 = pylint_dir('%s/../scripts' % CORE_DIR, '')
    for output in lint_output2:
      print(output)
    self.assertEqual(0, len(lint_output))
    self.assertEqual(0, len(lint_output2))

  def test_server(self):
    lint_output = pylint_dir(SERVER_DIR)
    for output in lint_output:
      print(output)
    lint_output2 = pylint_dir('%s/../scripts' % SERVER_DIR, '')
    for output in lint_output2:
      print(output)
    self.assertEqual(0, len(lint_output))
    self.assertEqual(0, len(lint_output2))

  def test_config_manager(self):
    lint_output = pylint_dir(CONFIG_DIR)
    for output in lint_output:
      print(output)
    lint_output2 = pylint_dir('%s/../scripts' % CONFIG_DIR, '')
    for output in lint_output2:
      print(output)
    self.assertEqual(0, len(lint_output))
    self.assertEqual(0, len(lint_output2))

  def test_user_tools(self):
    lint_output = pylint_dir(USER_DIR)
    for output in lint_output:
      print(output)
    lint_output2 = pylint_dir('%s/../scripts' % USER_DIR, '')
    for output in lint_output2:
      print(output)
    self.assertEqual(0, len(lint_output))
    self.assertEqual(0, len(lint_output2))

  ## this one currently blocks execution
  ## Presumably when it is checking the file running
  # def test_tests(self):
  #   lint_output = pylint_dir(TEST_DIR)
  #   for output in lint_output:
  #     print(output)

if( __name__ == '__main__' ):
  unittest.main()