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

"""Unittest for data_validation.py"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.18'


import datetime
import unittest

from roster_core import data_validation
from roster_core import helpers_lib
from roster_core import errors
from roster_core import punycode_lib

class TestDataValidation(unittest.TestCase):

  def setUp(self):
    reserved_words = ['blue']
    group_permissions = [u'a', u'aaaa', u'cname', u'ns', u'ptr', u'soa', u'srv']
    self.data_validation_instance = data_validation.DataValidation(
        reserved_words, group_permissions)

  def testisUnicodeString255(self):
    self.assertFalse(self.data_validation_instance.isUnicodeString255(
      12))
    self.assertTrue(self.data_validation_instance.isUnicodeString255(
      u'unicode_string'))
    self.assertTrue(self.data_validation_instance.isUnicodeString255(
      u'super_long_string_super_long_string_super_long_string_super_'
       'long_string_super_long_string_super_long_string_super_long_'
       'string_super_long_string_super_long_string_super_long_string_'
       'super_long_string_super_long_string_super_long_string_super_'
       'long_string_sup'))
    self.assertFalse(self.data_validation_instance.isUnicodeString255(
      u'super_long_string_super_long_string_super_long_string_super_'
       'long_string_super_long_string_super_long_string_super_long_'
       'string_super_long_string_super_long_string_super_long_string_'
       'super_long_string_super_long_string_super_long_string_super_'
       'long_string_supe'))

  def testisUnicodeString(self):
    self.assertTrue(self.data_validation_instance.isUnicodeString(
        u'unicode_string'))
    self.assertFalse(self.data_validation_instance.isUnicodeString(
        'not_unicode_string'))
    self.assertRaises(errors.ReservedWordError, 
        self.data_validation_instance.isUnicodeString, u'blue')
    self.assertRaises(errors.ReservedWordError, 
        self.data_validation_instance.isUnicodeString,
        u'thisincludesthewordblueandotherwordstoo')
    self.assertRaises(errors.ReservedWordError, 
        self.data_validation_instance.isUnicodeString,
        u'thisincludesthewordBluEeandotherwordstoo')

  def testisIPv4IPAddress(self):
    self.assertTrue(self.data_validation_instance.isIPv4IPAddress(
        '192.168.1.1'))
    self.assertFalse(self.data_validation_instance.isIPv4IPAddress(
        '192.168.1.256'))
    self.assertFalse(self.data_validation_instance.isIPv4IPAddress(
        '192.168.1.-1'))
    self.assertFalse(self.data_validation_instance.isIPv4IPAddress(192))
    self.assertFalse(self.data_validation_instance.isIPv4IPAddress('192.4'))

  def testisIPv6IPAddress(self):
    self.assertTrue(self.data_validation_instance.isIPv6IPAddress(
        '2001:0db8:0000:0000:0000:0000:1428:57ab'))
    self.assertFalse(self.data_validation_instance.isIPv6IPAddress(
        '2001:0db8:0000:0000:0000:0000:1428:57ab/64'))
    self.assertFalse(self.data_validation_instance.isIPv6IPAddress(
        '2001:db8::1428:57ab'))
    self.assertFalse(self.data_validation_instance.isIPv6IPAddress(
        '2001:db8::1428:57ab/64'))
    self.assertFalse(self.data_validation_instance.isIPv6IPAddress(
        '192.168.1.1'))
    self.assertFalse(self.data_validation_instance.isIPv6IPAddress(
        '2001:db8::1428:57abx'))

  def testisCIDRBlock(self):
    self.assertTrue(self.data_validation_instance.isCIDRBlock('192.168/16'))
    self.assertTrue(self.data_validation_instance.isCIDRBlock('192.168.1.1'))
    self.assertTrue(self.data_validation_instance.isCIDRBlock('192.168.1.0/24'))
    self.assertFalse(self.data_validation_instance.isCIDRBlock(
        '192.168.0.1/24'))
    self.assertFalse(self.data_validation_instance.isCIDRBlock('192.348/16'))
    self.assertFalse(self.data_validation_instance.isCIDRBlock(15))
    self.assertFalse(self.data_validation_instance.isCIDRBlock(None))
    self.assertFalse(self.data_validation_instance.isCIDRBlock('not_valid'))

  def testisIntBool(self):
    self.assertTrue(self.data_validation_instance.isIntBool(1))
    self.assertTrue(self.data_validation_instance.isIntBool(0))
    self.assertFalse(self.data_validation_instance.isIntBool(True))
    self.assertFalse(self.data_validation_instance.isIntBool(None))
    self.assertFalse(self.data_validation_instance.isIntBool(8))
    self.assertFalse(self.data_validation_instance.isIntBool('not_valid'))

  def testisUnsignedInt(self):
    self.assertTrue(self.data_validation_instance.isUnsignedInt(50))
    self.assertFalse(self.data_validation_instance.isUnsignedInt(True))
    self.assertFalse(self.data_validation_instance.isUnsignedInt(-1))
    self.assertFalse(self.data_validation_instance.isUnsignedInt('not_valid'))

  def testisUnixDirectory(self):
    self.assertTrue(self.data_validation_instance.isUnixDirectory(u'/etc/bind/'))
    self.assertFalse(self.data_validation_instance.isUnixDirectory(u'/etc/bind'))
    self.assertFalse(self.data_validation_instance.isUnixDirectory(u'etc/bind/'))
    self.assertFalse(self.data_validation_instance.isUnixDirectory(u'etc/bind'))
    self.assertFalse(self.data_validation_instance.isUnixDirectory(None))

  def testisTarget(self):
    #Despite what I have written in these targets, don't actually read them
    #and believe what they say.
    target_too_long = '%s' % ('this.is.a.super.long.target.host.name.that.'
                              'should.trip.the.length.check.in.core.helpers.'
                              'and.if.it.doesnt.we.have.problems.and.need.to.'
                              'fix.something.or.roster.will.ship.with.bugs.but.'
                              'software.has.been.shipped.with.bugs.before.so.'
                              'maybe.it.wont.be.too.bad.com')

    ok_target_1 = '%s' % ('this.is.a.super.long.target.host.name.that.should.'
                          'trip.the.length.check.in.core.helpers.and.if.it.'
                          'doesnt.we.have.problems.and.need.to.fix.something.'
                          'or.roster.will.ship.with.bugs.but.software.has.been.'
                          'shipped.with.bugs.before.so.maybe.it.wont.be.too.'
                          'bad.co')

    target_component_too_long = '%s' % ('thisisanothersuperlongtargethostname'
                                        'thatshouldtripthecheckincore.helpers.'
                                        'for.having.a.component.that.is.too.'
                                        'long')

    ok_target_2 = '%s' % ('thisisanothersuperlongtargethostnamethatshouldtrip'
                          'thecheckincor.helpers.for.having.a.component.that.'
                          'is.too.long')

    self.assertEqual(len(punycode_lib.Uni2Puny(ok_target_1)), 255)
    self.assertTrue(self.data_validation_instance.isTarget(ok_target_1))

    self.assertEqual(len(punycode_lib.Uni2Puny(target_too_long)), 256)
    self.assertFalse(self.data_validation_instance.isTarget(target_too_long))

    self.assertEqual(len(punycode_lib.Uni2Puny(ok_target_2.split('.')[0])), 63)
    self.assertTrue(self.data_validation_instance.isTarget(ok_target_2))

    self.assertEqual(
      len(punycode_lib.Uni2Puny(target_component_too_long.split('.')[0])), 64)
    self.assertFalse(
      self.data_validation_instance.isTarget(target_component_too_long))

    #Now we basically do the entire test over again but with unicode targets, 
    #just to make sure. (I don't think it's necessary but whatever)

    self.assertEqual(len(punycode_lib.Uni2Puny(unicode(ok_target_1))), 255)
    self.assertTrue(self.data_validation_instance.isTarget(ok_target_1))

    self.assertEqual(len(punycode_lib.Uni2Puny(unicode(target_too_long))), 256)
    self.assertFalse(self.data_validation_instance.isTarget(target_too_long))

    self.assertEqual(
        len(punycode_lib.Uni2Puny(unicode(ok_target_2).split('.')[0])), 63)
    self.assertTrue(self.data_validation_instance.isTarget(ok_target_2))

    self.assertEqual(len(punycode_lib.Uni2Puny(
        unicode(target_component_too_long).split('.')[0])), 64)
    self.assertFalse(
      self.data_validation_instance.isTarget(target_component_too_long))

  def testIsHostname(self):
    self.assertTrue(self.data_validation_instance.isHostname(
        u'university.edu.'))
    self.assertTrue(self.data_validation_instance.isHostname(
        u'blah.university.edu.'))
    self.assertFalse(self.data_validation_instance.isHostname(
        u'university.edu'))
    self.assertFalse(self.data_validation_instance.isHostname(u'.edu.'))
    self.assertFalse(self.data_validation_instance.isHostname(u'not_valid'))
    self.assertFalse(self.data_validation_instance.isHostname(2))

    #Despite what I have written in these hostnames, don't actually read them
    #and believe what they say.
    ok_hostname_1 = '%s' % (u'this.is.a.super.long.target.host.name.'
                             'that.should.trip.the.length.check.in.'
                             'core.helpers.and.if.it.doesnt.we.have.'
                             'problems.and.need.to.fix.something.or.'
                             'roster.will.ship.with.bugs.but.software.'
                             'has.been.shipped.with.bugs.before.so.'
                             'maybe.it.wont.be.too.awful.')

    hostname_too_long = '%s' % (u'this.is.a.super.long.target.host.name.'
                                 'that.should.trip.the.length.check.in.'
                                 'core.helpers.and.if.it.doesnt.we.have.'
                                 'problems.and.need.to.fix.something.or.'
                                 'roster.will.ship.with.bugs.but.software.'
                                 'has.been.shipped.with.bugs.before.so.'
                                 'maybe.it.wont.be.tooo.awful.')

    ok_hostname_2 = '%s' % (u'thisisanothersuperlongtargethostnamethat'
                             'shouldtripthecheckincor.helpers.for.'
                             'having.a.component.that.is.too.long.')

    hostname_component_too_long = '%s' % (u'thisisanothersuperlongtargethost'
                                           'namethatshouldtripthecheckincore.'
                                           'helpers.for.having.a.component.'
                                           'that.is.to.long.')

    #Just long enough to be valid
    self.assertEqual(len(punycode_lib.Uni2Puny(ok_hostname_1)), 255)
    self.assertTrue(self.data_validation_instance.isHostname(ok_hostname_1))

    #Just long enough to be invalid
    self.assertEqual(len(punycode_lib.Uni2Puny(hostname_too_long)), 256)
    self.assertFalse(
        self.data_validation_instance.isHostname(hostname_too_long))

    #First component is just long enough to be valid
    self.assertEqual(len(punycode_lib.Uni2Puny(ok_hostname_2.split('.')[0])), 
      63)
    self.assertTrue(self.data_validation_instance.isHostname(ok_hostname_2))

    #First component is just long enough to be invalid
    self.assertEqual(
        len(punycode_lib.Uni2Puny(hostname_component_too_long.split('.')[0])), 
        64)
    self.assertFalse(
        self.data_validation_instance.isHostname(hostname_component_too_long))

  def testIsGroupPermission(self):
    self.assertTrue(self.data_validation_instance.isGroupPermission(u'a'))
    self.assertTrue(self.data_validation_instance.isGroupPermission(u'soa'))
    self.assertTrue(self.data_validation_instance.isGroupPermission(u'ptr'))

    self.assertFalse(self.data_validation_instance.isGroupPermission(u'x'))
    self.assertFalse(self.data_validation_instance.isGroupPermission(u'123'))
    self.assertFalse(self.data_validation_instance.isGroupPermission(u'bbbb'))

    self.assertTrue(self.data_validation_instance.isGroupPermission(u'srv'))
    self.assertTrue(self.data_validation_instance.isGroupPermission(u'ns'))
    self.assertTrue(self.data_validation_instance.isGroupPermission(u'aaaa'))

    self.assertFalse(self.data_validation_instance.isGroupPermission(u'r'))
    self.assertFalse(self.data_validation_instance.isGroupPermission(u'128'))
    self.assertFalse(self.data_validation_instance.isGroupPermission(u'deny'))

  def testIsDateTime(self):
    self.assertTrue(self.data_validation_instance.isDateTime(
                        datetime.datetime.now()))
    self.assertFalse(self.data_validation_instance.isDateTime(
        '09-06-04 05:25:30'))

  def testValidateAclsDict(self):
    acl_ranges_dict = {'acl_range_cidr_block': None}
    self.assertRaises(errors.UnexpectedDataError,
                      self.data_validation_instance.ValidateRowDict,
                      'acl_ranges', acl_ranges_dict)

    acl_ranges_dict['acl_ranges_acl_name'] = None

    self.assertRaises(errors.UnexpectedDataError,
                      self.data_validation_instance.ValidateRowDict,
                      'acl_ranges', acl_ranges_dict, True)

    self.data_validation_instance.ValidateRowDict('acl_ranges', acl_ranges_dict,
                                                  none_ok=True,
                                                  all_none_ok=True)

    self.assertRaises(errors.UnexpectedDataError,
                      self.data_validation_instance.ValidateRowDict,
                      'acl_ranges', acl_ranges_dict, False)

    acl_ranges_dict['acl_range_cidr_block'] = '192.168.0.1'

    self.assertRaises(errors.UnexpectedDataError,
                      self.data_validation_instance.ValidateRowDict,
                      'acl_ranges', acl_ranges_dict, False)
    self.data_validation_instance.ValidateRowDict('acl_ranges',
                                                  acl_ranges_dict, 
                                                  none_ok=True)    

    acl_ranges_dict['acl_ranges_acl_name'] = u'name'
    
    self.data_validation_instance.ValidateRowDict('acl_ranges', acl_ranges_dict,
                                                  none_ok=True)

    acl_ranges_dict['acl_range_cidr_block'] = None

    self.assertRaises(errors.UnexpectedDataError,
                      self.data_validation_instance.ValidateRowDict,
                      'acl_ranges', acl_ranges_dict, False)
    self.data_validation_instance.ValidateRowDict('acl_ranges', acl_ranges_dict,
                                                  none_ok=True)

  def testTableEnumerationAndValidationConsistency(self):
    data_types = []
    tables = helpers_lib.GetValidTables()
    for table in tables:
      row_dict = helpers_lib.GetRowDict(table)

      for v in row_dict.values():
        if( not v in data_types ):
          data_types.append(v)
    data_validation_methods = dir(data_validation.DataValidation([], [])) 

    for data_type in data_types:
      # This means youa are missing a method in data_validation or 
      # you mis-typed something in table_enumeration
      # Uncomment this to figure out what
      # print data_type
      self.assertTrue('is%s' % data_type in data_validation_methods)


if( __name__ == '__main__' ):
    unittest.main()

# vi: set ai aw sw=2:
