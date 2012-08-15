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
It is used by dnszoneverify and dnsquerycheck."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import dns.zone
import dns.query

import roster_core
from roster_core import errors
from roster_core import helpers_lib

roster_core.core.CheckCoreVersionMatches(__version__)

def DnsQuery(zone_file_string, dns_server, dns_port, zone_origin=None):
  """Queries a DNS server for all the records contained within the
  supplied zone_file_string.
 
  Input:
    zone_file_string: string of a zone file.
    dns_server: IP Address or hostname of DNS server.
    dns_port: int of port to query DNS server on.
    zone_origin: string of zone_origin to replace 
      the $ORIGIN in zone_file_string.
 
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

  if( dns_server == 'localhost' ):
    dns_server = '127.0.0.1'

  #If the ORIGIN redirective is not found, we ask for it
  if( '$ORIGIN' not in zone_file_string and zone_origin is None ):
    raise errors.UnexpectedDataError('No zone origin supplied.')

  #Constructing the Zone object
  else:
    zone = dns.zone.from_text(zone_file_string, check_origin=False,
        origin=zone_origin)

  good_records = []
  bad_records = []
  zone_origin = str(zone.origin)
  reverse_zone = False

  #Determining if the zone is forward or reverse.
  if( zone_origin.endswith('in-addr.arpa.') or
      zone_origin.endswith('ip6.arpa.') ):
    reverse_zone = True

  #Making lookup tables so we can use the string values later
  record_classes = {
                     dns.rdataclass.IN:   'IN',
                     dns.rdataclass.CH:   'CH',
                     dns.rdataclass.HS:   'HS',
                     dns.rdataclass.NONE: 'NONE',
                     dns.rdataclass.ANY:  'ANY'
                   }

  record_types =   {
                     dns.rdatatype.A:     'A',
                     dns.rdatatype.AAAA:  'AAAA',
                     dns.rdatatype.CNAME: 'CNAME',
                     dns.rdatatype.SOA:   'SOA',
                     dns.rdatatype.MX:    'MX',
                     dns.rdatatype.NS:    'NS',
                     dns.rdatatype.PTR:   'PTR',
                     dns.rdatatype.TXT:   'TXT',
                     dns.rdatatype.HINFO: 'HINFO',
                     dns.rdatatype.SRV:   'SRV'
                   }

  #Main loop, going through the zone records, querying the DNS server for them
  for record_tuple in zone.items():
    record_target = unicode(record_tuple[0])

    for record_set in record_tuple[1].rdatasets:
      server_responses = []
      for record_object in record_set.items:

        #Setting record type, (example - TXT)
        if( record_object.rdtype in record_types ):
          record_type = record_types[record_object.rdtype]
        else:
          raise errors.UnexpectedDataError(
              'Unknown record type: %s.\n %s' % (
              dns.rdatatype.to_text(record_object.rdtype), record_object))

        #Setting class type, (example - IN)
        if( record_object.rdclass in record_classes ):
          record_class = record_classes[record_object.rdclass]
        else:
          raise errors.UnexpectedDataError(
              'Unknown class type: %s.\n %s' % (
              dns.rdatatype.to_text(record_object.rdclass), record_object))

        #Setting query 
        if( record_target == '@' ):
          query = zone_origin
        else:
          query = '%s.%s' % (record_target, zone_origin)
 
        message = dns.message.make_query(query, rdtype=record_object.rdtype)
        response = str(dns.query.udp(message, dns_server, 
            port=int(dns_port), one_rr_per_rrset=True, timeout=60)).split('\n')
        answers = response[
            response.index(';ANSWER') + 1:response.index(';AUTHORITY')]
        for answer in answers:

          #Stripping out the TTL because we don't care about it
          answer_parts = answer.split(' ')
          answer_parts.remove(answer_parts[1])
          answer = ' '.join(answer_parts)
          server_responses.append(answer)

      #Building the "good response" string that we'll seach for later
      #in the server responses. Certain record types require special syntax

      if( record_type == 'AAAA' ):
        #We need to do this so the server response looks the same as the
        #good_response. I.e. 3fff:::::: is the same ip address as 3FFF::::::
        #but '3fff:::::' != '3FFF::::::'
        ip_address = helpers_lib.UnExpandIPV6(str(record_object).lower())
        good_response = '%s %s %s %s' % (query, record_class, 
            record_type, ip_address)

      elif( record_type == 'SOA' and not reverse_zone ):
        record_parts = str(record_object).split(' ')
        if( record_parts[0].endswith('.') and record_parts[1].endswith('.') ):
          good_response = '%s %s %s %s' % (query, record_class, 
              record_type, str(record_object))
        else:
          record_parts[0] = '%s.%s' % (record_parts[0], zone_origin)
          record_parts[1] = '%s.%s' % (record_parts[1], zone_origin)
          new_record_object = ' '.join(record_parts)
          good_response = '%s %s %s %s' % (query, record_class, 
              record_type, str(new_record_object))

      elif( record_type == 'SOA' and reverse_zone ):
        good_response = '%s %s %s %s' % (query, record_class, 
            record_type, str(record_object))

      elif( record_type == 'CNAME' and not reverse_zone ):
        if( str(record_object) == '@' ):
          good_response = '%s %s %s %s' % (query, record_class, 
              record_type, zone_origin)
        else:
          if( str(record_object).endswith('.') ):
            good_response = '%s %s %s %s' % (query, record_class, 
                record_type, str(record_object))
          else:
            good_response = '%s %s %s %s.%s' % (query, record_class, 
                record_type, str(record_object), zone_origin)

      elif( record_type in ['SRV', 'NS', 'MX'] and not reverse_zone ):
        good_response = '%s %s %s %s.%s' % (query, record_class, 
            record_type, str(record_object), zone_origin)

      elif( record_type == 'PTR' ):
        if( str(record_object).endswith('.') ):
          good_response = '%s %s %s %s' % (query, record_class, 
              record_type, str(record_object))
        else:
          good_response = '%s %s %s %s.%s' % (query, record_class, 
              record_type, str(record_object), zone_origin)

      else:
        good_response = '%s %s %s %s' % (query, record_class, 
            record_type, str(record_object))

      #Checking for good_response
      found_good_response = False
      for server_response in server_responses:

        #Removing the soa serial because it might be incremented,
        #so we don't compare it.
        if( record_type == 'SOA' ):
          good_response_parts = good_response.split(' ')
          good_response_parts.remove(good_response_parts[5])
          good_response = ' '.join(good_response_parts)

          server_response_parts = server_response.split(' ')
          server_response_parts.remove(server_response_parts[5])
          server_response = ' '.join(server_response_parts)

        if( good_response == server_response ):
          found_good_response = True

      if( found_good_response ):
        good_records.append(unicode(good_response))
      else:
        bad_records.append(unicode(good_response))

  return (good_records, bad_records)
