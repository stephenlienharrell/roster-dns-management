#! /usr/bin/env python
#
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

"""This module contains all the logic for querying a DNS server.
It is used by dnsquerycheck."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.18'

import random
import socket
import dns.zone
import dns.query

import roster_core
from roster_config_manager import config_lib
from roster_core import errors
from roster_core import helpers_lib

roster_core.core.CheckCoreVersionMatches(__version__)

def DnsQuery(records, dns_server, dns_port, zone_origin):
  """Queries a DNS server for all the records contained within the
  supplied list of records.
 
  Input:
    records: list of record dictionaries.
    dns_server: string of IP Address or hostname of DNS server.
    dns_port: int of port to query DNS server on.
    zone_origin: string of zone origin.
 
    Output:
      (good_records, bad_records): a tuple of 2 lists,
      the first being all the records that were able to 
      be verified, the second being all the records unable
      to be verified.

      example: ([u'0.168.192.in-addr.arpa. 86400 IN NS ns2.university.lcl.',
                 u'1.0.168.192.in-addr.arpa. 86400 IN PTR router.university.lcl.',
                 u'11.0.168.192.in-addr.arpa. 86400 IN PTR desktop-1.university.lcl.',
                 u'12.0.168.192.in-addr.arpa. 86400 IN PTR desktop-2.university.lcl.'],

                [u'13.0.168.192.in-addr.arpa. 86400 IN PTR desktop-3.university.lcl.'])

    Raises:
          errors.UnexpectedDataError: No zone origin supplied.
          errors.UnexpectedDataError: Invalid record type.
          errors.UnexpectedDataError: Invalid record class."""

  try:
    dns_server = socket.gethostbyname(dns_server)
  except socket.gaierror:
    raise config_lib.ConfigManagerError('ERROR: Could not find address '
        'associated with %s.' % dns_server)

  good_records = []
  record_types = {
    u'a':     dns.rdatatype.A,
    u'aaaa':  dns.rdatatype.AAAA,
    u'cname': dns.rdatatype.CNAME,
    u'soa':   dns.rdatatype.SOA,
    u'mx':    dns.rdatatype.MX,
    u'ns':    dns.rdatatype.NS,
    u'ptr':   dns.rdatatype.PTR,
    u'txt':   dns.rdatatype.TXT,
    u'hinfo': dns.rdatatype.HINFO,
    u'srv':   dns.rdatatype.SRV
  }

  #Main loop, going through the zone records, querying the DNS server for them
  for record in records:
    server_responses = []
    record_type = record['record_type']
    rdtype = record_types[record_type]
    record_arguments = record['record_arguments']

    if( 'record_target' in record ):
      record_target = record['record_target']
    else:
      record_target = record['target']

    #Setting query 
    if( record_target == '@' ):
      query = zone_origin
    else:
      query = '%s.%s' % (record_target, zone_origin)
 
    message = dns.message.make_query(query, rdtype=rdtype)

    try:
      response = dns.query.udp(message, dns_server, 
          port=int(dns_port), one_rr_per_rrset=False, timeout=10)
    except dns.exception.Timeout:
      raise config_lib.QueryCheckError('Querying DNS server timed out.')
    except dns.exception.SyntaxError:
      raise config_lib.QueryCheckError('Invalid DNS server address.')
    except dns.exception.DNSException:
      raise config_lib.QueryCheckError('Unknown error during DNS query '
                                       'process.')

    answers = response.answer

    #checking that record type and target match
    for answer in answers:
      if( int(answer.rdtype) == int(rdtype) and 
          unicode(answer.name) == unicode(query) ):
        break
    else:
      continue

    for answer_set in answers:
      for answer in answer_set:
        if( record_type == u'soa' ):
          if( record_arguments[u'refresh_seconds'] == answer.refresh and 
              record_arguments[u'expiry_seconds']  == answer.expire  and
              record_arguments[u'minimum_seconds'] == answer.minimum and
              record_arguments[u'retry_seconds']   == answer.retry   and
              record_arguments[u'name_server'] == unicode(answer.mname) and 
              record_arguments[u'admin_email'] == unicode(answer.rname) ):
            good_records.append(record)
            break

        elif( record_type == u'a' ):
          if( record_arguments[u'assignment_ip'] == answer.address ):
            good_records.append(record)
            break

        elif( record_type == u'aaaa' ):
          if( record_arguments[u'assignment_ip'] == helpers_lib.ExpandIPV6(
                unicode(answer.address)) ):
            good_records.append(record)
            break

        elif( record_type == u'cname' ):
          if( record_arguments[u'assignment_host'] == unicode(answer.target) ):
            good_records.append(record)
            break

        elif( record_type == u'ptr' ):
          if( record_arguments[u'assignment_host'] == unicode(answer.target) ):
            good_records.append(record)
            break

        elif( record_type == u'mx' ):
          if( record_arguments[u'priority']    == answer.preference and
              record_arguments[u'mail_server'] == unicode(answer.exchange) ):
            good_records.append(record)
            break

        elif( record_type == u'ns' ):
          if( record_arguments[u'name_server'] == unicode(answer.target) ):
            good_records.append(record)
            break

        elif( record_type == u'hinfo' ):
          if( record_arguments[u'hardware'] == unicode(answer.cpu) and
              record_arguments[u'os']       == unicode(answer.os) ):
            good_records.append(record)
            break

        elif( record_type == u'txt' ):
          quoted_text = unicode(' '.join(
            ['"%s"' % answer_string for answer_string in answer.strings]))
          if( record_arguments[u'quoted_text'] == quoted_text ):
            good_records.append(record)
            break
        elif( record_type == u'srv' ):
          if( record_arguments['weight'] == answer.weight and
              record_arguments['priority'] == answer.priority and 
              record_arguments['assignment_host'] == unicode(answer.target) ):
            good_records.append(record)
            break

  #Takes all the records that never made it into good_records, and declares
  #them as bad_records.
  for record in good_records:
    records.remove(record)

  bad_records = records
 
  #This is purely for asthetic reasons. If you were to print bad_records,
  #you'd see a bunch of None's which doesn't help you. It just clutters
  #the screen.
  for record in bad_records:
    if( u'record_zone_name' in record ):
      if( record[u'record_zone_name'] is None ):
        del record[u'record_zone_name']

  return (good_records, bad_records)

def QueryFromZoneFile(zone_file_name, dns_server, port, records_to_query, 
    view_name=None):
  """Queries a DNS server for a number of records contained within the
  supplied zone file.

  Inputs:
    zone_file_name: string of zone file path. e.g. - '/tmp/forward_zone_1.db'
    dns_server: string of IP Address or hostname of DNS server.
    port: int of port to query DNS server on. 
    num_records_to_query: int of the number of records to randomly select and 
      query.
    view_name: string of view that zone_file_name is in.

  Outputs:
    True if all records queried, query correctly."""
  zone_name = zone_file_name.split('/').pop().split('.')[0]
  try:
    zone_file_handle = open(zone_file_name, 'r')
    zone_file_string = zone_file_handle.read()
    zone_file_handle.close()
  except IOError:
    raise config_lib.QueryCheckError('Unable to open zone file '
                                     '%s' % zone_file_name)

  try:
    zone_object = dns.zone.from_text(
        str(zone_file_string), check_origin=False)
  except dns.zone.NoSOA:
    raise config_lib.QueryCheck('Zone has no SOA record.')
  except dns.zone.NoNS:
    raise config_lib.QueryCheckError('Zone has no A/AAAA record for NS')

  zone_origin = zone_object.origin
  try:
    all_zone_records_list = helpers_lib.CreateRecordsFromZoneObject(
        zone_object, zone_name=zone_name, view_name=view_name)
  except errors.UnexpectedDataError as e:
    raise config_lib.QueryCheckError('Unexpected Data - %s' % e.message())
  zone_records_list = []

  #Generating list of random records to query
  if( records_to_query == 0 ):
    zone_records_list = all_zone_records_list
  else:
    for i in range(records_to_query):
      #If we've run out of records to pop, break out of the loop
      if( len(all_zone_records_list) == 0 ):
        break

      random_record_index = random.randint(0, len(all_zone_records_list) - 1)
      random_record = all_zone_records_list.pop(random_record_index) 
      zone_records_list.append(random_record)

  (good_records, bad_records) = DnsQuery(
      zone_records_list, dns_server, port, zone_origin)

  if( len(bad_records) != 0 ):
    return False
  return True

