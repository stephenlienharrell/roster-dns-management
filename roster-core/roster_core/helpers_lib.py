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

"""This is a library of static helper functions for Roster."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import inspect
import IPy
import math

import constants
import copy


def GetFunctionNameAndArgs():
  """Grabs the current frame and adjacent frames then finds the calling
  function name and arguments and returns them.

  Outputs:
    tuple: function name and current args
      ex: ('MakeUser', {'replay_args': [u'ahoward', 64],
                        'audit_args': {'access_level': 64,
                                       'user_name': u'ahoward'}}
  """
  current_frame = inspect.currentframe()
  try:
    outer_frames = inspect.getouterframes(current_frame)
    try:
      function_name = unicode(outer_frames[1][3])
      calling_frame = outer_frames[1][0]
      try:
        arg_values = inspect.getargvalues(calling_frame)
      finally:
        del calling_frame
    finally:
      del outer_frames
  finally:
    del current_frame
  replay_args = []
  audit_args = {}
  for arg in arg_values[0]:
    if( arg == 'self' ):
      continue
    else:
      audit_args[arg] = arg_values[3][arg]
      replay_args.append(arg_values[3][arg])
  current_args = {'audit_args': audit_args, 'replay_args': replay_args}
  return (function_name, current_args)


def GetValidTables():
  """Returns all of the tables in the database that are enumerated in this
  modules.

  Outputs:
    list: list of valid tables.
      example: ['acls', 'records', 'etc']
  """
  return constants.TABLES.keys()


def GetRowDict(table_name):
  """Returns a specific dictionary keyed off of table name. 

  Inputs:
    table_name: string of table name from db
  
  Outputs:
    dictionary: dict of row that was requested (see constants above)
  """
  row_dict = {}
  if( table_name in constants.TABLES.keys() ):
    row_dict = copy.copy(constants.TABLES[table_name])
  return row_dict


def ListAccessRights():
  """Lists access rights.

  Output:
    list: list of access rights. ex: ['rw', 'r']
  """
  return constants.ACCESS_RIGHTS


def ReverseIP(ip_address):
  """Reverse an IP address

  Inputs:
    ip_address: either an ipv4 or ipv6 string

  Outputs:
    string: reverse ip address
  """
  ip_object = IPy.IP(ip_address)
  reverse_ip_string = ip_object.reverseName()
  if( ip_object.version() == 4 ):
    ip_parts = reverse_ip_string.split('.')
    if( '-' in ip_parts[0] ):
      range = ip_parts.pop(0).split('-')
      num_ips = int(range[1]) - int(range[0]) + 1
      netmask = int(32 - (math.log(num_ips) / math.log(2)))
      last_octet = ip_parts.pop(0)
      reverse_ip_string = '.'.join(ip_parts)
      reverse_ip_string = '%s/%s.%s' % (last_octet, netmask,
                                        reverse_ip_string)
  return unicode(reverse_ip_string)


def UnReverseIP(ip_address):
  """Un-Reverses reversed IP addresses

  Inputs:
    ip_address: either an ipv4 or ipv6 string (reversed)

  Outputs:
    string: forward ip address
  """
  mask = 0
  ip_address = ip_address.lower()
  cidr_parts = ip_address.split('/')
  if( len(cidr_parts) == 2 ):
    mask = cidr_parts[1].split('.')[0]
    ip_address = ip_address.replace('/%s' % mask, '')
  if( ip_address.endswith('in-addr.arpa.') ):
    octets = 0
    ip_array = ip_address.split('.')
    ip_parts = []
    while len(ip_array):
      ip_part = ip_array.pop()
      if( ip_part.isdigit() ):
        ip_parts.append(ip_part)
        octets += 1
    new_ip = '.'.join(ip_parts)
    if( mask ):
      new_ip = '%s/%s' % (new_ip, mask)
    elif( octets < 4 ):
      new_ip = '%s/%s' % (new_ip, octets * 8)
  elif( ip_address.endswith('ip6.arpa.') ):
    ip_array = ip_address.split('.')[:-3]
    ip_parts = []
    while len(ip_array):
      ip_parts.append('%s%s%s%s' % (ip_array.pop(), ip_array.pop(),
                                    ip_array.pop(), ip_array.pop()))
    new_ip = ':'.join(ip_parts)
  else:
    new_ip = ip_address

  return new_ip


def CIDRExpand(cidr_block):
    """Expands a cidr block to a list of ip addreses

    Inputs:
      cidr_block: string of cidr_block

    Outputs:
      list: list of ip addresses in strings
    """
    cidr_block = IPy.IP(cidr_block)
    ip_address_list = []
    for ip_address in cidr_block:
      ip_address_list.append(unicode(ip_address.strFullsize()))

    return ip_address_list


def ExpandIPV6(ip_address):
  """Expands a shorthand ipv6 address to a full ipv6 address

  Inputs:
    ip_address: string of ipv6 address

  Outputs:
    string: string of long ipv6 address
  """
  ipv6_address = IPy.IP(ip_address)
  if( ipv6_address.version() != 6 ):
    raise errors.CoreError('"%s" is not a valid IPV6 address.' % ipv6_address)
  return ipv6_address.strFullsize()


# vi: set ai aw sw=2:
