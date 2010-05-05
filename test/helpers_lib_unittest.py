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

"""Unittest for helper_lib.py"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import unittest
from roster_core import helpers_lib


class TestCoreHelpers(unittest.TestCase):

  def testUnReverseIP(self):
    self.assertEqual(helpers_lib.UnReverseIP(
        'b.a.9.8.7.6.5.0.4.0.0.0.3.0.0.0.2.0.0.0.1.0.0.0.0.0.0.0.1.2.3.4.'
        'ip6.arpa.'), '4321:0000:0001:0002:0003:0004:0567:89ab')
    self.assertEqual(helpers_lib.UnReverseIP(
        '4.1.168.192.in-addr.arpa.'), '192.168.1.4')
    self.assertEqual(helpers_lib.UnReverseIP(
        '64/27.23.168.192.in-addr.arpa.'), '192.168.23.64/27')
    self.assertEqual(helpers_lib.UnReverseIP(
        '0.168.192.in-addr.arpa.'), '192.168.0/24')
    self.assertEqual(helpers_lib.UnReverseIP(
        '168.192.in-addr.arpa.'), '192.168/16')

  def testReverseIP(self):
    self.assertEqual(helpers_lib.ReverseIP(
        u'192.168.0/26'), u'0/26.168.192.in-addr.arpa.')
    self.assertEqual(helpers_lib.ReverseIP(
        u'192.168.0/31'), u'0/31.168.192.in-addr.arpa.')

  def testListAccessRights(self):
    self.assertEqual(helpers_lib.ListAccessRights(), ['rw', 'r'])


if( __name__ == '__main__' ):
      unittest.main()
