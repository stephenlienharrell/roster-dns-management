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

"""Unittest for user.py"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.9'


import unittest
import fake_db_access

from roster_core import audit_log
from roster_core import user


class TestUser(unittest.TestCase):

  # Use a FakeDbAccess, so we don't need to beat up a DB during testing
  def setUp(self):
    self.db_access = fake_db_access.FakeDbAccess(None,None,None,None)
    self.log_instance = audit_log.AuditLog(log_to_syslog=True)

  def testBadMethod(self):
    gooduser = user.User('jcollins', self.db_access, self.log_instance)
    self.assertRaises(user.AuthError, gooduser.Authorize, 'nomethod')

  def testBadUser(self):
    self.assertRaises(user.UserError, user.User, 'nobody', self.db_access,
                      self.log_instance)

  def testNoOp(self):
    gooduser = user.User('jcollins', self.db_access, self.log_instance)
    gooduser.Authorize('noop')
  
  def testMakeRecordGoodZone(self):
    gooduser = user.User('shuey', self.db_access, self.log_instance)
    gooduser.Authorize('MakeRecord', 'foo.mrzone.com')
  
  def testMakeRecordBadZone(self):
    gooduser = user.User('shuey', self.db_access, self.log_instance)
    self.assertRaises(user.AuthError, gooduser.Authorize, 'MakeRecord',
                      'foo.norights.com')
  
  def testMakeRecordGoodV4(self):
    gooduser = user.User('shuey', self.db_access, self.log_instance)
    gooduser.Authorize('MakeRecord', '128.211.130.37')
  
  def testMakeRecordBadV4(self):
    gooduser = user.User('shuey', self.db_access, self.log_instance)
    self.assertRaises(user.AuthError, gooduser.Authorize, 'MakeRecord',
                      '9.9.9.9')
  
  def testMakeRecordGoodV6(self):
    gooduser = user.User('shuey', self.db_access, self.log_instance)
    gooduser.Authorize('MakeRecord', '1000:2000::4')
  
  def testMakeRecordBadV6(self):
    gooduser = user.User('shuey', self.db_access, self.log_instance)
    self.assertRaises(user.AuthError, gooduser.Authorize, 'MakeRecord',
                      '2000::4')


if( __name__ == '__main__' ):
    unittest.main()
