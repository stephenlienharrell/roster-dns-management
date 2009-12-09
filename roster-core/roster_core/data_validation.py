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

"""This module contains static methods for validating different kinds of data.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.9'


import constants
import datetime
import errors
import re

import IPy

import table_enumeration


class UnexpectedDataError(errors.DbAccessError):
  pass


class InvalidInputError(errors.DbAccessError):
  pass


class MissingDataTypeError(errors.DbAccessError):
  pass


class ReservedWordError(errors.DbAccessError):
  pass


class DataValidation(object):

  def __init__(self, reserved_words):
    self.reserved_words = reserved_words

  def isUnicodeString(self, u_string):
    """Checks that a string is unicode.
  
    Inputs:
      u_string: unicode string
    
    Outputs:
      bool: bool if string or not
    """
    if( not isinstance(u_string, unicode) ):
      return False

    for word in self.reserved_words:
      if( u_string.lower().find(word.lower()) != -1 ):
        raise ReservedWordError('Reserved word %s found, unable to complete '
                                'request' % word)

    return True

  def isReservedWord(self, u_string):
    """Checks that a string is unicode. Ignores reserved words.
  
    Inputs:
      u_string: unicode string
    
    Outputs:
      bool: bool if string or not
    """
    if( not isinstance(u_string, unicode) ):
      return False
    return True

  def isAccessRight(self, access_right):
    """Checks to make sure that the string is a valid access right.
  
    Inputs:
      access_right: unicode string, and in constants.ACCESS_RIGHTS

    Outputs:
      bool: if access right is valid or not
    """
    if( self.isUnicodeString(access_right) and access_right in
        constants.ACCESS_RIGHTS ):
      return True
    return False

  def isAccessLevel(self, access_level):
    """Checks to make sure that the string is a valid access level.

    Inputs:
      access_level: unisgned int that is in constants.ACCESS_LEVELS 

    Outputs:
      bool: if access level is valid or not
    """
    if( self.isUnsignedInt(access_level) and access_level in
        constants.ACCESS_LEVELS.values()):
      return True
    return False


  def isIPv4IPAddress(self, ip_address):
    """Checks that a string is an ipv4 IP Address.
  
    Inputs:
      ip_address: string of an ipv4 ip address

    Outputs:
      bool: if string is valid ip address
    """
    if( not isinstance(ip_address, basestring) or
        re.search(r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
                  r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
                  r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
                  r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
                  ip_address) is None ):
      return False
    return True


  def isIPv6IPAddress(self, ip_address):
    """Checks that a string is an ipv6 IP Address.
  
    Inputs:
      ip_address: string of ipv6 ip address

    Outputs:
      bool: if string is valid ip address
    """
    if( not isinstance(ip_address, basestring) or 
        not ip_address.find('/') == -1 ):
      return False
    try:
      ip = IPy.IP(ip_address)
    except ValueError:
      return False
    if( not str(ip.netmask()) == 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff' or
        not ip.version() == 6 ):
      return False
    return True


  def isCIDRBlock(self, cidr_block):
    """Checks that a string is a CIDR block.

    http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing

    Inputs:
      cidr_block: string of CIDR block

    Outputs:
      bool: if it is valid CIDR block
    """
    if( not isinstance(cidr_block, basestring) or
        cidr_block.isdigit() ):
      return False
    try:
      IPy.IP(cidr_block)
    except ValueError:
      return False
    return True


  def isIntBool(self, int_bool):
    """Checks that int_bool is only 1 or 0 and nothing else.

    Inputs:
      int_bool: 1 or 0

    Outputs:
      bool: if it is a valid int bool
    """
    if( int_bool in (0, 1) and not isinstance(int_bool, bool) ):
      return True
    return False


  def isUnsignedInt(self, unsigned_int):
    """Checks that unsigned_int is of int class and is 0 or higher.

    Inputs:
      unsigned_int: integer

    Outputs:
      bool: if it is a valid unsigned int
    """
    if( (isinstance(unsigned_int, int) or isinstance(unsigned_int, long)) and 
        unsigned_int >= 0 and not isinstance(unsigned_int, bool) ):
      return True
    return False


  def isHostname(self, host_name):
    """Checks that is a unicode string and that is properly dotted.

    Inputs:
      host_name: string of properly dotted time stamp

    Outputs:
      bool: if it is a valid hostname
    """
    if( self.isUnicodeString(host_name) and host_name.endswith('.') and
        host_name.split('.') > 2 and not host_name.startswith('.') ):
      return True
    return False


  def isDateTime(self, date_time):
    """Checks that is a unicode string and that is a valid time stamp.

    Inputs:
      date_time: string of date in format YYYY-MM-DD HH:MM:SS

    Outputs:
      bool: if it is a valid date
    """
    if( isinstance(date_time, datetime.datetime) ):
      return True
    return False


  def ValidateRowDict(self, table_name, row_dict, none_ok=False,
                      all_none_ok=False):
    """Checks row dictionaries for correctness in reference to know data types
      and column names in the coresponding table.
  
    Input:
      table_name: string of table name
      row_dict: dict of row
      none_ok: bool of allowance of None as a value in the dict
      all_none_ok: bool of allowance of None as every value in the dict

    Raises:
      InvalidInputError: Missing key in dictionary
      MissingDataType: No Function to check data type
      UnexpectedDataError: Invalid data type
      UnexpectedDataError: Need to fill out at least one value in dict
    """
    main_dict = table_enumeration.GetRowDict(table_name)

    for k in main_dict.iterkeys():
      if( k not in row_dict ):
        raise InvalidInputError('Missing key %s in dictionary' % k)

    for k, v in row_dict.iteritems():
      if( k not in main_dict ):
        raise InvalidInputError('Dictionary has extra key that is not used: %s'
                              % k)

      if( not 'is%s' % main_dict[k] in dir(self) ):
          raise MissingDataTypeError('No function to check data type: %s' %
                                   main_dict[k])

      if( not getattr(self, 'is%s' % main_dict[k])(v) ):
        if( (not none_ok and not k.endswith('_id')) or 
            (none_ok and v is not None) ):
          raise UnexpectedDataError('Invalid data type %s for %s: %s' % (
              main_dict[k], k, v))

    if( none_ok and not all_none_ok ):
      for value in row_dict.values():
        if( value is not None ):
          return
      raise UnexpectedDataError('Need to fill out at least one value in dict')
          

# vi: set ai aw sw=2:
