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
__version__ = '#TRUNK#'


import datetime
import unittest

from roster_core import data_validation
from roster_core import helpers_lib
from roster_core import errors


class TestDataValidation(unittest.TestCase):

  def setUp(self):
    reserved_words = ['blue']
    self.data_validation_instance = data_validation.DataValidation(
        reserved_words)

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

  def testIsDateTime(self):
    self.assertTrue(self.data_validation_instance.isDateTime(
                        datetime.datetime.now()))
    self.assertFalse(self.data_validation_instance.isDateTime(
        '09-06-04 05:25:30'))

  def testValidateAclsDict(self):
    acl_ranges_dict = {'acl_range_allowed': None,
                       'acl_range_cidr_block': None}
    self.assertRaises(errors.InvalidInputError,
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

    self.assertRaises(errors.UnexpectedDataError,
                      self.data_validation_instance.ValidateRowDict,
                      'acl_ranges',
                      acl_ranges_dict, False)
    self.data_validation_instance.ValidateRowDict('acl_ranges', acl_ranges_dict,
                                                  none_ok=True)

    acl_ranges_dict['acl_range_allowed'] = 1
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
    data_validation_methods = dir(data_validation.DataValidation([])) 

    for data_type in data_types:
      # This means youa are missing a method in data_validation or 
      # you mis-typed something in table_enumeration
      # Uncomment this to figure out what
      # print data_type
      self.assertTrue('is%s' % data_type in data_validation_methods)


if( __name__ == '__main__' ):
    unittest.main()

# vi: set ai aw sw=2:
