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

"""Unittest for helpers_lib.py"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import unittest

from roster_core import errors
from roster_core import helpers_lib


class TestHelpersLib(unittest.TestCase):

  def testGetFunctionNameAndArgs(self, test_flag='test', other_flag=1):
    function, args = helpers_lib.GetFunctionNameAndArgs()
    self.assertEqual(function, 'testGetFunctionNameAndArgs')
    self.assertEqual(args, 
        {'replay_args': ['test', 1],
         'audit_args': {'test_flag': 'test', 'other_flag': 1}})

  def testGetRowDict(self):
    self.assertEqual(helpers_lib.GetRowDict('acls'), 
                     {'acl_name': 'UnicodeString'})
    self.assertEqual(helpers_lib.GetRowDict('notvalid'), {}) 

  def testReverseIP(self):
    self.assertEqual(helpers_lib.ReverseIP(
        u'192.168.0/26'), u'0/26.168.192.in-addr.arpa.')
    self.assertEqual(helpers_lib.ReverseIP(
        u'192.168.0/31'), u'0/31.168.192.in-addr.arpa.')
    self.assertEqual(helpers_lib.ReverseIP(
        u'192.168.0.3'), u'3.0.168.192.in-addr.arpa.')
    self.assertEqual(helpers_lib.ReverseIP(
        u'4321:0000:0001:0002:0003:0004:0567:89ab'),
        u'b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1.0.0.0.0.0.0.0.1.2.3.4.'
         'ip6.arpa.')
    self.assertEqual(helpers_lib.ReverseIP(
      u'4321:0000:0001:0002:0003:0004:0567::'),
      u'0.0.0.0.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1.0.0.0.0.0.0.0.1.2.3.4.'
       'ip6.arpa.')
    self.assertRaises(errors.CoreError, helpers_lib.ReverseIP, 'notavalidip')

  def testUnReverseIP(self):
    self.assertEqual(helpers_lib.UnReverseIP(
        'b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1.0.0.0.0.0.0.0.1.2.3.4.'
        'ip6.arpa.'),
        '4321:0000:0001:0002:0003:0004:0567:89ab')
    self.assertEqual(helpers_lib.UnReverseIP(
        '4.1.168.192.in-addr.arpa.'), '192.168.1.4')
    self.assertEqual(helpers_lib.UnReverseIP(
        '64/27.23.168.192.in-addr.arpa.'), '192.168.23.64/27')
    self.assertEqual(helpers_lib.UnReverseIP(
        '0.168.192.in-addr.arpa.'), '192.168.0/24')
    self.assertEqual(helpers_lib.UnReverseIP(
        '168.192.in-addr.arpa.'), '192.168/16')
    self.assertEqual(helpers_lib.UnReverseIP('notvalid'), 'notvalid')

  def testCIDRExpand(self):
    self.assertEquals(helpers_lib.CIDRExpand('192.168.0/31'),
                      [u'192.168.0.0', u'192.168.0.1'])
    self.assertEquals(helpers_lib.CIDRExpand('192.168.0.1'),
                      [u'192.168.0.1'])
    self.assertRaises(errors.CoreError, helpers_lib.CIDRExpand, 'notavalidip')

  def testExpandIPV6(self):
    self.assertEqual(
        helpers_lib.ExpandIPV6(u'4321:0000:0001:0002:0003:0004:0567:89ab'),
        u'4321:0000:0001:0002:0003:0004:0567:89ab')
    self.assertEqual(
        helpers_lib.ExpandIPV6(u'4321:0000:0001:0002::0567:89ab'),
        u'4321:0000:0001:0002:0000:0000:0567:89ab')
    self.assertRaises(errors.CoreError, helpers_lib.ExpandIPV6, 'notavalidip')
    self.assertRaises(errors.CoreError, helpers_lib.ExpandIPV6, '192.168.0.1')


if( __name__ == '__main__' ):
  unittest.main()
