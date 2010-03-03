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

"""This module contains all of the logic for the zone importer.

It should be only called by the importer.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.12'


import dns.zone
import dns.rdatatype
from dns.exception import DNSException
import IPy
import roster_core


class Error(Exception):
  pass


class ZoneImport(object):
  """This class will only import one zone per init. It will load the zone
  from a file using dns.zone and then use the core API to put it in 
  the database.
  """
  def __init__(self, zone_file_name, config_file_name, user_name, zone_view,
               records_view=None):
    """Sets self.core_instance, self.zone self.domain and self.view.

    Inputs:
      zone_file_name: name of zone file to impport
      config_file_name: name of config file to load db info from
      user_name: username of person running the script
      view: view name if needed
    """
    config_instance = roster_core.Config(file_name=config_file_name)
    self.core_instance = roster_core.Core(user_name, config_instance)
    self.zone = dns.zone.from_file(zone_file_name)
    self.origin = unicode(self.zone.origin)
    self.zone_name = self.origin.strip('.')
    self.view = records_view
    self.zone_view = zone_view

  def MakeViewAndZone(self):
    """Makes view and zone.
    
    Inputs:
      self.zone_name: unicode of zone name
    """
    if( self.zone_view is not None and
        not self.core_instance.ListViews(view_name=self.zone_view) ):
      self.core_instance.MakeView(self.zone_view)
   
    existing_zones = self.core_instance.ListZones(zone_origin=self.origin)
    if( not existing_zones ):
      self.core_instance.MakeZone(self.zone_name, u'master',
                                  self.origin, view_name=self.zone_view)
    else:
      self.zone_name = existing_zones.keys()[0]

  def ReverseZoneToCIDRBlock(self):
    """Creates CIDR block from reverse zone name.
    
    Outputs:
      string of cidr block
    """
    if( self.origin.endswith('in-addr.arpa.') ):
      ip_parts = self.origin.split('.in-')[0].split('.')
      ip_parts.reverse()
      for ip_part in ip_parts:
        if( not ip_part.isdigit() ):
          raise Error('%s is not a reverse zone.' % self.zone_name)

      cidr_block = '.'.join(ip_parts)
      ip_octets = len(ip_parts)

      if( ip_octets > 3 or ip_octets < 1 ):
        raise Error('%s is not a reverse zone.' % self.zone_name)

      cidr_block = '%s/%s' % (cidr_block, ip_octets * 8)

    elif( self.origin.endswith('ip6.arpa.') ):
      ip_parts = self.origin.split('.ip6')[0].split('.')
      ip_parts.reverse()
      ip_quartets = len(ip_parts)

      for ip_part in ip_parts:
        try:
          int(ip_part, 16)
        except ValueError:
          raise Error('Invalid hexidecimal number in ipv6 origin: %s' % 
                      self.origin)
      # fill out the rest of the ipv6 address
      ip_parts.extend(['0' for x in range(32-ip_quartets)])
       
      for x in range(1,8):
        # Put colons every 4 quartets
        ip_parts.insert((x*4)+(x-1), ':')
      cidr_block = ''.join(ip_parts)

      cidr_block = '%s/%s' % (cidr_block, ip_quartets * 4)

    else:
        raise Error('%s is not a reverse zone.' % self.zone_name)

    return cidr_block

  def FixHostname(self, host_name):
    """Checks name and returns fqdn.

    Inputs:
      string of host name

    Outputs:
      string of fully qualified domain name
    """
    if( host_name == u'@' ):
      host_name = self.origin
    elif( not host_name.endswith('.') ):
      host_name = '%s.%s' % (host_name, self.origin)
    return host_name

  def MakeRecordsFromZone(self):
    """Makes records in the database from dns.zone class.
    
    Outputs:
      int: Amount of records added to db.
    """
    record_count = 0
    self.MakeViewAndZone()
    if( self.origin.endswith('in-addr.arpa.') or
        self.origin.endswith('ip6.arpa.') ):
      cidr_block = self.ReverseZoneToCIDRBlock()
      self.core_instance.MakeReverseRangeZoneAssignment(self.zone_name,
                                                        cidr_block)
    make_record_args_list = []
    for record_tuple in self.zone.items():
      record_target = unicode(record_tuple[0])

      for record_set in record_tuple[1].rdatasets:
        ttl = record_set.ttl
        for record_object in record_set.items:

          if( record_object.rdtype == dns.rdatatype.PTR ):
            record_type = u'ptr'
            assignment_host = self.FixHostname(unicode(record_object))
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
            assignment_host = self.FixHostname(unicode(record_object))
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
            mail_server = self.FixHostname(unicode(record_object.exchange))
            record_args_dict = {u'priority': record_object.preference,
                                u'mail_server': mail_server}

          elif( record_object.rdtype == dns.rdatatype.NS ):
            record_type = u'ns'
            name_server = self.FixHostname(unicode(record_object))
            record_args_dict = {u'name_server': name_server}

          elif( record_object.rdtype == dns.rdatatype.SRV ):
            record_type = u'srv'
            assignment_host = self.FixHostname(unicode(record_object.target))
            record_args_dict = {u'priority': record_object.priority,
                                u'weight': record_object.weight,
                                u'port': record_object.port,
                                u'assignment_host': assignment_host}
                                       
          elif( record_object.rdtype == dns.rdatatype.SOA ):
            record_type = u'soa'
            name_server = self.FixHostname(unicode(record_object.mname))
            admin_email = self.FixHostname(unicode(record_object.rname))
            record_args_dict = {u'name_server': name_server,
                                u'admin_email': admin_email,
                                u'serial_number': record_object.serial,
                                u'retry_seconds': record_object.retry,
                                u'refresh_seconds': record_object.refresh,
                                u'expiry_seconds': record_object.expire,
                                u'minimum_seconds': record_object.minimum}

          else:
            print 'Unkown record type: %s.\n %s' % (record_object.rdtype,
                                                    record_object)
            continue

          if( record_type == u'soa' ):
            make_record_args_list.insert(0, (record_type, record_target,
                                             self.zone_name, record_args_dict,
                                             self.zone_view, ttl))
          else:
            make_record_args_list.append((record_type, record_target,
                                          self.zone_name, record_args_dict,
                                          self.view, ttl))

    for make_record_args in make_record_args_list:
      self.core_instance.MakeRecord(*make_record_args)
      record_count += 1

    return record_count
