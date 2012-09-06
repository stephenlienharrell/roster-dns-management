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
__version__ = '#TRUNK#'

import dns.zone
import unittest

from roster_core import errors
from roster_core import helpers_lib

FORWARD_ZONE = 'test_data/test_zone.db'
REVERSE_ZONE = 'test_data/test_reverse_zone.db'
REVERSE_IPV6_ZONE = 'test_data/test_reverse_ipv6_zone.db'

class TestHelpersLib(unittest.TestCase):

  def testGetFunctionNameAndArgs(self, test_flag='test', other_flag=1):
    function, args = helpers_lib.GetFunctionNameAndArgs()
    self.assertEqual(function, 'testGetFunctionNameAndArgs')
    self.assertEqual(args, 
        {'replay_args': ['test', 1],
         'audit_args': {'test_flag': 'test', 'other_flag': 1}})

  def testFixHostname(self):
    self.assertEqual(helpers_lib.FixHostname(u'host', u'sub.university.lcl.'),
        u'host.sub.university.lcl.')
    self.assertEqual(helpers_lib.FixHostname(u'@', u'sub.university.lcl.'),
        u'sub.university.lcl.')
    self.assertEqual(helpers_lib.FixHostname(u'university.lcl.', 
        u'sub.university.lcl.'), u'university.lcl.')

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
    self.assertEqual(helpers_lib.UnReverseIP('google.com'), 'google.com')

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

  def testUnExpandIPV6(self):
    self.assertEqual(
        helpers_lib.UnExpandIPV6(u'4321:0000:0001:0002:0003:0004:0567:89ab'), 
        u'4321::1:2:3:4:567:89ab')
    self.assertEqual(
        helpers_lib.UnExpandIPV6(u'4321:0:0:0:0:0:567:89ab'),
        u'4321::567:89ab')
    self.assertEqual(
        helpers_lib.UnExpandIPV6(u'4321:0000:0000:0000:0000:0000:567:89ab'),
        u'4321::567:89ab')
    self.assertRaises(errors.InvalidInputError, helpers_lib.UnExpandIPV6,
        u'invalid') 

  def testCreateRecordsFromZoneObject(self):
    forward_zone_handle = open(FORWARD_ZONE, 'r')
    reverse_zone_handle = open(REVERSE_ZONE, 'r')
    reverse_ipv6_zone_handle = open(REVERSE_IPV6_ZONE, 'r')

    forward_zone_string = forward_zone_handle.read()
    reverse_zone_string = reverse_zone_handle.read()
    reverse_ipv6_zone_string = reverse_ipv6_zone_handle.read()

    forward_zone_handle.close()
    reverse_zone_handle.close()
    reverse_ipv6_zone_handle.close()
  
    forward_zone_object = dns.zone.from_text(forward_zone_string, 
        check_origin=False)
    reverse_zone_object = dns.zone.from_text(reverse_zone_string,
        check_origin=False)
    reverse_ipv6_zone_object = dns.zone.from_text(reverse_ipv6_zone_string,
        check_origin=False)

    self.assertEqual(
        helpers_lib.CreateRecordsFromZoneObject(forward_zone_object),
        [{u'record_arguments': {u'refresh_seconds': 10800L, 
                                u'expiry_seconds': 3600000L, 
                                u'name_server': u'ns.university.lcl.', 
                                u'minimum_seconds': 86400L, 
                                u'retry_seconds': 3600L, 
                                u'serial_number': 794L, 
                                u'admin_email': u'hostmaster.ns.university.lcl.'},
          u'record_type': u'soa', 
          u'ttl': 3600L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 

         {u'record_arguments': {u'name_server': u'ns.sub.university.lcl.'}, 
          u'record_type': u'ns', 
          u'ttl': 3600L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'name_server': u'ns2.sub.university.lcl.'}, 
          u'record_type': u'ns', 
          u'ttl': 3600L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'priority': 10, 
                                u'mail_server': u'mail1.sub.university.lcl.'}, 
          u'record_type': u'mx', 
          u'ttl': 3600L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'priority': 20, 
                                u'mail_server': u'mail2.sub.university.lcl.'}, 
          u'record_type': u'mx', 
          u'ttl': 3600L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'quoted_text': u'"Contact 1:  Stephen Harrell (sharrell@university.lcl)"'}, 
          u'record_type': u'txt', 
          u'ttl': 3600L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_ip': u'192.168.0.1'}, 
          u'record_type': u'a', 
          u'ttl': 3600L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_ip': u'192.168.1.103'}, 
          u'record_type': u'a', 
          u'ttl': 3600L, 
          u'record_target': u'ns', 
          u'record_zone_name': None, 
          u'record_view_dependency': None},
          
         {u'record_arguments': {u'assignment_ip': u'3ffe:0800:0000:0000:02a8:79ff:fe32:1982'}, 
          u'record_type': u'aaaa', 
          u'ttl': 3600L, 
          u'record_target': u'desktop-1', 
          u'record_zone_name': None, 
          u'record_view_dependency': None},
          
         {u'record_arguments': {u'assignment_ip': u'192.168.1.100'}, 
          u'record_type': u'a', 
          u'ttl': 3600L, 
          u'record_target': u'desktop-1', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_ip': u'192.168.1.104'}, 
          u'record_type': u'a', 
          u'ttl': 3600L, 
          u'record_target': u'ns2', 
          u'record_zone_name': None, 
          u'record_view_dependency': None},
          
         {u'record_arguments': {u'hardware': u'PC', u'os': u'NT'}, 
          u'record_type': u'hinfo', 
          u'ttl': 3600L, 
          u'record_target': u'ns2', 
          u'record_zone_name': None, 
          u'record_view_dependency': None},
          
         {u'record_arguments': {u'assignment_host': u'sub.university.lcl.'}, 
          u'record_type': u'cname', 
          u'ttl': 3600L, 
          u'record_target': u'www', 
          u'record_zone_name': None, 
          u'record_view_dependency': None},
          
         {u'record_arguments': {u'assignment_ip': u'127.0.0.1'}, 
          u'record_type': u'a', 
          u'ttl': 3600L, 
          u'record_target': u'localhost', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_host': u'ns.university.lcl.'}, 
          u'record_type': u'cname', 
          u'ttl': 3600L, 
          u'record_target': u'www.data', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_ip': u'192.168.1.101'}, 
          u'record_type': u'a', 
          u'ttl': 3600L, 
          u'record_target': u'mail1', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_ip': u'192.168.1.102'}, 
          u'record_type': u'a', 
          u'ttl': 3600L, 
          u'record_target': u'mail2', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}])

    self.assertEqual(
        helpers_lib.CreateRecordsFromZoneObject(reverse_zone_object),
        [{u'record_arguments': {u'refresh_seconds': 10800L, 
                                u'expiry_seconds': 3600000L, 
                                u'name_server': u'ns.university.lcl.', 
                                u'minimum_seconds': 86400L, 
                                u'retry_seconds': 3600L, 
                                u'serial_number': 4L, 
                                u'admin_email': u'hostmaster.university.lcl.'}, 
          u'record_type': u'soa', 
          u'ttl': 86400L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'name_server': u'ns.university.lcl.'}, 
          u'record_type': u'ns', 
          u'ttl': 86400L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
         
         {u'record_arguments': {u'name_server': u'ns2.university.lcl.'}, 
          u'record_type': u'ns', 
          u'ttl': 86400L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
         
         {u'record_arguments': {u'assignment_host': u'router.university.lcl.'}, 
          u'record_type': u'ptr', 
          u'ttl': 86400L, 
          u'record_target': u'1', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_host': u'desktop-1.university.lcl.'},
          u'record_type': u'ptr', 
          u'ttl': 86400L, 
          u'record_target': u'11', 
          u'record_zone_name': None, 
          u'record_view_dependency': None},
        
         {u'record_arguments': {u'assignment_host': u'desktop-2.university.lcl.'},
          u'record_type': u'ptr', 
          u'ttl': 86400L, 
          u'record_target': u'12', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}])

    self.assertEqual(
        helpers_lib.CreateRecordsFromZoneObject(reverse_ipv6_zone_object),
        [{u'record_arguments': {u'refresh_seconds': 10800L, 
                                u'expiry_seconds': 3600000L, 
                                u'name_server': u'ns.university.lcl.', 
                                u'minimum_seconds': 86400L, 
                                u'retry_seconds': 3600L, 
                                u'serial_number': 4L, 
                                u'admin_email': u'hostmaster.university.lcl.'},
          u'record_type': u'soa', 
          u'ttl': 86400L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'name_server': u'ns.university.lcl.'}, 
          u'record_type': u'ns', 
          u'ttl': 86400L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'name_server': u'ns2.university.lcl.'}, 
          u'record_type': u'ns', 
          u'ttl': 86400L, 
          u'record_target': u'@', 
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_host': u'router.university.lcl.'}, 
          u'record_type': u'ptr', 
          u'ttl': 86400L, 
          u'record_target': u'2.8.9.1.2.3.e.f.f.f.9.7.8.a.2.0.0.0.0.0.0.0.0.0.0.0',
          u'record_zone_name': None, 
          u'record_view_dependency': None}, 
          
         {u'record_arguments': {u'assignment_host': u'desktop-1.university.lcl.'},
          u'record_type': u'ptr', 
          u'ttl': 86400L, 
          u'record_target': u'0.8.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0',
          u'record_zone_name': None, 
          u'record_view_dependency': None}])

if( __name__ == '__main__' ):
  unittest.main()
