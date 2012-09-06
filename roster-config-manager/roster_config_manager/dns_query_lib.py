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
import dns.exception

import roster_core
from roster_core import helpers_lib

roster_core.core.CheckCoreVersionMatches(__version__)

def DnsQuery(records, dns_server, dns_port, zone_origin):
  """Queries a DNS server for all the records contained within the
  supplied list of records.
 
  Input:
    records: list of record dictionaries
    dns_server: IP Address or hostname of DNS server.
    dns_port: int of port to query DNS server on.
    zone_origin: string of zone_origin
 
    Output:
      (good_records, bad_records): a tuple of 2 lists,
      the first being all the records that were able to 
      be verified, the second being all the records unable
      to be verified."""
  if( dns_server == 'localhost' ):
    dns_server = '127.0.0.1'

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
      return ([], records)

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
          if( record_arguments[u'quoted_text'] == u'"%s"' % (
                answer.strings[0]) ):
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
