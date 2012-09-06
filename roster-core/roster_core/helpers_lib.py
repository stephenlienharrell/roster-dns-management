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
import dns.zone

import constants
import copy
import errors


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


def ReverseIP(ip_address):
  """Reverse an IP address

  Inputs:
    ip_address: either an ipv4 or ipv6 string

  Raises:
    InvalidInputError: Not a valid IP address.

  Outputs:
    string: reverse ip address
  """
  try:
    ip_object = IPy.IP(ip_address)
  except ValueError:
    raise errors.InvalidInputError('%s is not a valid IP address' % ip_address)
  reverse_ip_string = ip_object.reverseName()
  if( ip_object.version() == 4 ):
    ip_parts = reverse_ip_string.split('.')
    if( '-' in ip_parts[0] ):
      ip_range = ip_parts.pop(0).split('-')
      num_ips = int(ip_range[1]) - int(ip_range[0]) + 1
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
    if( len(ip_address.split('.')[:-3]) == 32 ):
      ip_array = ip_address.split('.')[:-3]
      ip_parts = []
      while len(ip_array):
        ip_parts.append('%s%s%s%s' % (ip_array.pop(), ip_array.pop(),
                                      ip_array.pop(), ip_array.pop()))

      new_ip = ':'.join(ip_parts)
    else:
      ip_array = ip_address.split('.')[:-3]
      ip_parts = []
      while( len(ip_array) > 3 ): 
        ip_parts.append('%s%s%s%s' % (ip_array.pop(), ip_array.pop(),
                                      ip_array.pop(), ip_array.pop()))
      if( len(ip_array) > 0 ):
        ip_parts.append('%s' % (''.join(ip_array[::-1])))

      new_ip = ':'.join(ip_parts)
      new_ip = '%s::/%s' % (new_ip, len(ip_address.split('.')[:-3] * 4))
  else:
    new_ip = ip_address
 
  return new_ip


def CIDRExpand(cidr_block, begin=None, end=None):
  """Expands a cidr block to a list of ip addreses
     from begin (integer) to end (integer).

  Inputs:
    cidr_block: string of cidr_block
    begin: integer of ip address to start
    end: integer of ip address to end

  Raises:
    InvalidInputError: Not a valid CIDR block.

  Outputs:
    list: list of ip addresses in strings
  """
  try:
    cidr_block = IPy.IP(cidr_block)
  except ValueError:
    raise errors.InvalidInputError('%s is not a valid cidr block' % cidr_block)
  ip_address_list = []
  end_count = -1
  length = cidr_block.len()
  count = 0
  start_ip = cidr_block.int()
  if( begin ):
    start_ip = cidr_block.int() + begin
  if( begin and end ):
    end_count = end - begin
  elif( end ):
    end_count = end
  while( count != end_count and count != length and IPy.IP(start_ip + count) in cidr_block ):
    ip_address_list.append(unicode(IPy.IP(start_ip + count).strFullsize()))
    count += 1

  return ip_address_list


def ExpandIPV6(ip_address):
  """Expands a shorthand ipv6 address to a full ipv6 address

  Inputs:
    ip_address: string of short ipv6 address

  Raises:
    InvalidInputError: Not a valid IP address.
    InvalidInputError: Not a valid IPV6 address.

  Outputs:
    string: string of long ipv6 address
  """
  try:
    ipv6_address = IPy.IP(ip_address)
  except ValueError:
    raise errors.InvalidInputError('%s is not a valid IP address' % ip_address)
  if( ipv6_address.version() != 6 ):
    raise errors.InvalidInputError('"%s" is not a valid IPV6 address.' % (
        ipv6_address))

  return ipv6_address.strFullsize()

def UnExpandIPV6(ip_address):
  """Unexpands a full ipv6 address to a shorthand ipv6 address

  Inputs:
    ip_address: string of long ipv6 address

  Raises:
    InvalidInputError: Not a valid IP address.
    InvalidInputError: Not a valid IPV6 address.

  Outputs:
    string: string of short ipv6 address
  """
  try:
    ipv6_address = IPy.IP(ip_address)
  except ValueError:
    raise errors.InvalidInputError('%s is not a valid IP address' % ip_address)
  if( ipv6_address.version() != 6 ):
    raise errors.InvalidInputError('"%s" is not a valid IPV6 address.' % (
        ipv6_address))

  new_address = str(ipv6_address)
  new_address_parts = new_address.split(':')

  #What this does is changes 4321:0:1:2:3:4:567:89ab into 4321::1:2:3:4:567:89ab
  while( '0' in new_address_parts ):
    zero_index = new_address_parts.index('0')
    new_address_parts.pop(zero_index)
    new_address_parts.insert(zero_index, '')

  return u':'.join(new_address_parts)

def FixHostname(host_name, origin):
  """Checks name and returns fqdn.

  Inputs:
    host_name: string of host name
    origin: string of the zone origin

  Outputs:
    string of fully qualified domain name
  """
  if( host_name == u'@' ):
    host_name = origin
  elif( not host_name.endswith('.') ):
    host_name = '%s.%s' % (host_name, origin)
  return unicode(host_name)

def CreateRecordsFromZoneObject(zone_object, zone_name=None, 
                view_name=None, zone_origin=None, views_list=None):
  """Creates a list of record dictionaries from a dns.zone object

  Inputs:
    zone_object: a dns.zone object
    zone_origin: a string of the zone origin
    zone_name: string of zone name
    view_name: string of view name
    views_list: list of view dictionaries. 
      Note: This is only necessary if being called by AddFormattedRecords.

  Output:
    make_record_args_list: list of dictionaries of records"""
  if(zone_origin is None):
    zone_origin = str(zone_object.origin)

  make_record_args_list = []
  for record_tuple in zone_object.items():
    record_target = unicode(record_tuple[0])

    for record_set in record_tuple[1].rdatasets:
      ttl = record_set.ttl
      for record_object in record_set.items:
        if( record_object.rdtype == dns.rdatatype.PTR ):
          record_type = u'ptr'
          assignment_host = FixHostname(unicode(record_object), 
              zone_origin)
          record_args_dict = {u'assignment_host': assignment_host}

        elif( record_object.rdtype == dns.rdatatype.A ):
          record_type = u'a'
          record_args_dict = {u'assignment_ip': unicode(record_object)}

        elif( record_object.rdtype == dns.rdatatype.AAAA ):
          record_type = u'aaaa'
          record_args_dict = {u'assignment_ip':
                                  unicode(IPy.IP(str(
                                      record_object)).strFullsize())}

        elif( record_object.rdtype == dns.rdatatype.CNAME ):
          record_type = u'cname'
          assignment_host = FixHostname(unicode(record_object), 
              zone_origin)
          record_args_dict = {u'assignment_host': assignment_host}

        elif( record_object.rdtype == dns.rdatatype.HINFO ):
          record_type = u'hinfo'
          record_args_dict = {u'hardware': unicode(record_object.cpu),
                              u'os': unicode(record_object.os)}

        elif( record_object.rdtype == dns.rdatatype.TXT ):
          record_type = u'txt'
          record_args_dict = {u'quoted_text': unicode(record_object)}

        elif( record_object.rdtype == dns.rdatatype.MX ):
          record_type = u'mx'
          mail_server = FixHostname(unicode(record_object.exchange),
              zone_origin)
          record_args_dict = {u'priority': record_object.preference,
                              u'mail_server': mail_server}

        elif( record_object.rdtype == dns.rdatatype.NS ):
          record_type = u'ns'
          name_server = FixHostname(unicode(record_object), 
              zone_origin)
          record_args_dict = {u'name_server': name_server}

        elif( record_object.rdtype == dns.rdatatype.SRV ):
          record_type = u'srv'
          assignment_host = FixHostname(unicode(record_object.target),
              zone_origin)
          record_args_dict = {u'priority': record_object.priority,
                              u'weight': record_object.weight,
                              u'port': record_object.port,
                              u'assignment_host': assignment_host}

        elif( record_object.rdtype == dns.rdatatype.SOA ):
          record_type = u'soa'
          name_server = FixHostname(unicode(record_object.mname), 
              zone_origin)
          admin_email = FixHostname(unicode(record_object.rname), 
              zone_origin)
          record_args_dict = {u'name_server': name_server,
                              u'admin_email': admin_email,
                              u'serial_number': record_object.serial,
                              u'retry_seconds': record_object.retry,
                              u'refresh_seconds': record_object.refresh,
                              u'expiry_seconds': record_object.expire,
                              u'minimum_seconds': record_object.minimum}

        else:
          raise errors.UnexpectedDataError(
              'Unkown record type: %s.\n %s' % (
                  dns.rdatatype.to_text(record_object.rdtype), record_object))

        if( record_object.rdtype == dns.rdatatype.SOA and 
            view_name == u'any' and views_list ):
          for single_view in views_list:
            if( single_view != u'any' ):
              make_record_args_list.append(
                {u'record_type': record_type,
                 u'record_target': record_target,
                 u'record_zone_name': zone_name,
                 u'record_arguments': record_args_dict,
                 u'record_view_dependency': single_view,
                 u'ttl': ttl})
        else:
          make_record_args_list.append(
              {u'record_type': record_type,
               u'record_target': record_target,
               u'record_zone_name': zone_name,
               u'record_arguments': record_args_dict,
               u'record_view_dependency': view_name,
               u'ttl': ttl})

  return make_record_args_list


def GetRecordsFromRecordRowsAndArgumentRows(record_data, record_args_dict):
  """Takes data from joined records and record_arguments_record_assignments
  and creates record rows that are combined.

  Inputs:
    record_data: List of rows from ListRow with records and
                 records_arguments_record_assignments joined.

  Outputs:
    list of record dictionaries
      Each dictionary can have different args depending on record type.
      All of them will include record_type, target, zone_name, ttl, and
      view_name regardless of record type. Below is an example of an mx
      record search.
      example: [{'record_type': 'mx', 'target': 'university.edu.',
                 'zone_name': 'university.edu', ttl: 3600,
                 'view_name': 'external', 'priority': 10,
                 'mail_server': 'smtp-01.university.edu.',
                 'last_user': 'sharrell},
                {'record_type': 'mx', 'target': 'university.edu.',
                 'zone_name': 'university.edu', ttl: 3600,
                 'view_name': 'external', 'priority': 20,
                 'mail_server': 'smtp-02.university.edu.'},
                 'last_user': 'sharrell}]
  """
  full_record_dicts = {}
  del_id_list = []
  for record in record_data:
    if( record['record_arguments_records_assignments_argument_name'] in
        record_args_dict and
        record_args_dict[record[
            'record_arguments_records_assignments_argument_name']] is
        not None and
        unicode(record_args_dict[record[
          'record_arguments_records_assignments_argument_name']]) !=
        record['argument_value'] ):
      del_id_list.append(record['records_id'])

    if( not record['record_arguments_records_assignments_record_id'] in
        full_record_dicts ):
      full_record_dicts[
          record['record_arguments_records_assignments_record_id']] = {}

      full_record_dicts[
          record['record_arguments_records_assignments_record_id']][
              'record_type'] = record['record_type']

      full_record_dicts[
          record['record_arguments_records_assignments_record_id']][
              'zone_name'] = record['record_zone_name']
      if( record['record_view_dependency'].endswith('_dep') ):
        record['record_view_dependency'] = record[
            'record_view_dependency'][:-4:]
      full_record_dicts[
          record['record_arguments_records_assignments_record_id']][
              'view_name'] = record['record_view_dependency']

      full_record_dicts[
          record['record_arguments_records_assignments_record_id']][
              'target'] = record['record_target']

      full_record_dicts[
          record['record_arguments_records_assignments_record_id']][
              'ttl'] = record['record_ttl']

      full_record_dicts[
          record['record_arguments_records_assignments_record_id']][
              'last_user'] = record['record_last_user']

    if( record['argument_value'].isdigit() ):
      record['argument_value'] = int(record['argument_value'])

    full_record_dicts[
        record['record_arguments_records_assignments_record_id']][record[
            'record_arguments_records_assignments_argument_name']] = record[
            'argument_value']

  for record_id in set(del_id_list):
    del full_record_dicts[record_id]

  return full_record_dicts.values()

def UnicodeString(string):
  """Returns unicode string if object is a string

  Inputs:
    string: string to unicode

  Outputs:
    unicode string: if input is a string
  """
  if( type(string) == str ):
    return unicode(string)
  return string


# vi: set ai aw sw=2:
