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


"""Test PAM module."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import getpass

import unittest

import fakepam
import roster_core
import roster_server
from roster_server import auth_pam

CONFIG_FILE = 'test_data/roster.conf'

class TestPAMModule(unittest.TestCase):
  def setUp(self):
    pass
  def tearDown(self):
    pass
  def testPAMModule(self):
    pam_instance = auth_pam.AuthenticationMethod(
        module=fakepam)
    self.assertTrue(pam_instance.Authenticate(
        user_name=u'jcollins', password=u'test'))
    self.assertFalse(pam_instance.Authenticate(
        user_name=u'jcollins', password=u'wrongpass'))
    self.assertFalse(pam_instance.Authenticate(
        user_name=u'wronguser', password=u'wrongpass'))
    self.assertFalse(pam_instance.Authenticate(
        user_name=u'wronguser', password=u'test'))

  ## This tests the login user and password against PAM.
  ## This is commented out because it requires the user to
  ## interactively enter their login name and password during
  ## a unittest.
  ## def testPAMAuth(self):
  ##  user_name = getpass.getpass('Enter your login username: ')
  ##  password = getpass.getpass('Enter your login password: ')
  ##  AuthModule = auth_pam.AuthenticationMethod()
  ##  self.assertTrue(AuthModule.Authenticate(
  ##    user_name, password))

if( __name__ == '__main__' ):
  unittest.main()
