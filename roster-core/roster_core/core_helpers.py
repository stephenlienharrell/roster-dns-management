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

"""Core helper functions."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.17'


import constants
import errors
import helpers_lib

import datetime
import dns.zone
import IPy

class CoreHelpers(object):
  """Library of helper functions that extend the core functions."""
  def __init__(self, core_instance):
    """Sets up core instance

    Inputs:
       core_instance: instance of RosterCore
    """
    self.core_instance = core_instance
    self.db_instance = core_instance.db_instance
    self.user_instance = core_instance.user_instance
    self.log_instance = core_instance.log_instance

  ### These functions just expose helpers_lib functions for the 
  ### XML-RPC server. For doc strings see helpers_lib
  def ListGroupPermissions(self):
    return self.db_instance.data_validation_instance.ListGroupPermissions()

  def ReverseIP(self, ip_address):
    return helpers_lib.ReverseIP(ip_address)

  def UnReverseIP(self, ip_address):
    return helpers_lib.UnReverseIP(ip_address)

  def CIDRExpand(self, cidr_block, begin=None, end=None):
    return helpers_lib.CIDRExpand(cidr_block, begin, end)

  def ExpandIPV6(self, ip_address):
    return helpers_lib.ExpandIPV6(ip_address)

  def GetViewsByUser(self, username):
    """Lists view names available to given username

    Inputs:
        username: string of user name

    Outputs:
        list: list of view name strings
    """
    function_name, current_args = helpers_lib.GetFunctionNameAndArgs()
    self.user_instance.Authorize(function_name)
    views = set([])
    success = False

    users_dict = self.db_instance.GetEmptyRowDict('users')
    users_dict['user_name'] = username
    user_group_assignments_dict = self.db_instance.GetEmptyRowDict(
        'user_group_assignments')
    groups_dict = self.db_instance.GetEmptyRowDict('groups')
    forward_zone_permissions_dict = self.db_instance.GetEmptyRowDict(
        'forward_zone_permissions')
    zones_dict = self.db_instance.GetEmptyRowDict('zones')
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    self.db_instance.StartTransaction()
    try:
      joined_list = self.db_instance.ListRow(
          'users', users_dict, 'user_group_assignments',
          user_group_assignments_dict,
          'groups', groups_dict, 'forward_zone_permissions',
          forward_zone_permissions_dict, 'zones', zones_dict,
          'zone_view_assignments', zone_view_assignments_dict)
    finally:
      self.db_instance.EndTransaction()
    for view_dict in joined_list:
      views.add(view_dict['zone_view_assignments_view_dependency'].split(
          '_dep')[0])
    success = True

    return views

  def _FixHostname(self, host_name, origin):
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

  def AddFormattedRecords(self, zone_name, zone_file_string,
                          view):
    """Adds records from a string of a partial zone file

    Inputs:
      zone_name: string of zone name
      zone_file_string: string of the file contents
      view: string of view name

    Outputs:
      int: Amount of records added to db.
    """
    origin = self.core_instance.ListZones(zone_name=zone_name)[
          zone_name][view][u'zone_origin']

    zone = None
    #If the file doesn't have an origin, we need to give it something
    #otherwise dns.zone will raise an UnknownOrigin exception
    if( zone_file_string.find("$ORIGIN") == -1 ):
      zone = dns.zone.from_text(str(zone_file_string), check_origin=False,
        origin=origin)
    else:
      zone = dns.zone.from_text(str(zone_file_string), check_origin=False)   

    make_record_args_list = []
    for record_tuple in zone.items():
      record_target = unicode(record_tuple[0])

      for record_set in record_tuple[1].rdatasets:
        ttl = record_set.ttl
        for record_object in record_set.items:
          if( record_object.rdtype == dns.rdatatype.PTR ):
            record_type = u'ptr'
            assignment_host = self._FixHostname(unicode(record_object), origin)
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
            assignment_host = self._FixHostname(unicode(record_object), origin)
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
            mail_server = self._FixHostname(unicode(record_object.exchange), origin)
            record_args_dict = {u'priority': record_object.preference,
                                u'mail_server': mail_server}

          elif( record_object.rdtype == dns.rdatatype.NS ):
            record_type = u'ns'
            name_server = self._FixHostname(unicode(record_object), origin)
            record_args_dict = {u'name_server': name_server}

          elif( record_object.rdtype == dns.rdatatype.SRV ):
            record_type = u'srv'
            assignment_host = self._FixHostname(unicode(record_object.target), origin)
            record_args_dict = {u'priority': record_object.priority,
                                u'weight': record_object.weight,
                                u'port': record_object.port,
                                u'assignment_host': assignment_host}

          elif( record_object.rdtype == dns.rdatatype.SOA ):
            record_type = u'soa'
            name_server = self._FixHostname(unicode(record_object.mname), origin)
            admin_email = self._FixHostname(unicode(record_object.rname), origin)
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

          if( record_object.rdtype == dns.rdatatype.SOA and view == u'any'):
            all_views = self.core_instance.ListZones(zone_name=zone_name)[zone_name]

            for single_view in all_views:
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
                 u'record_view_dependency': view,
                 u'ttl': ttl})

    self.ProcessRecordsBatch(add_records=make_record_args_list, zone_import=True)
    return len(make_record_args_list)

  def GetCIDRBlocksByView(self, view, username):
    """Lists CIDR blocks available to a username in a given view

    Inputs:
        view: string of view name
        username: string of user name

    Outputs:
        list: list of cidr block strings
    """
    self.user_instance.Authorize('GetCIDRBlocksByView')
    cidrs = set([])
    users_dict = self.db_instance.GetEmptyRowDict('users')
    users_dict['user_name'] = username
    views_dict = self.db_instance.GetEmptyRowDict('views')
    views_dict['view_name'] = view

    user_group_assignments_dict = self.db_instance.GetEmptyRowDict(
        'user_group_assignments')
    groups_dict = self.db_instance.GetEmptyRowDict('groups')
    reverse_range_permissions_dict = self.db_instance.GetEmptyRowDict(
        'reverse_range_permissions')
    zones_dict = self.db_instance.GetEmptyRowDict('zones')
    reverse_range_zone_assignments_dict = self.db_instance.GetEmptyRowDict(
        'reverse_range_zone_assignments')
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    self.db_instance.StartTransaction()
    try:
      joined_list = self.db_instance.ListRow(
          'views', views_dict,
          'users', users_dict, 'user_group_assignments',
          user_group_assignments_dict,
          'groups', groups_dict, 'reverse_range_permissions',
          reverse_range_permissions_dict, 'zones', zones_dict,
          'zone_view_assignments', zone_view_assignments_dict,
          'reverse_range_zone_assignments', reverse_range_zone_assignments_dict)
    finally:
      self.db_instance.EndTransaction()
    for cidr_dict in joined_list:
      cidrs.add(cidr_dict['reverse_range_zone_assignments_cidr_block'])

    return cidrs

  def GetAssociatedCNAMEs(self, hostname, view_name, zone_name,
                          recursive=False):
    """Lists cname's by assignment hostname.

    Inputs:
      hostname: string of hostname
      view_name: string of view name
      zone_name: string of zone name

    Outputs:
      list: list of found cname dictionaries
    """
    self.user_instance.Authorize('GetAssociatedCNAMEs')
    record_arguments_record_assignments_dict = (
        self.db_instance.GetEmptyRowDict(
            'record_arguments_records_assignments'))
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = unicode(
         zone_name)
    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
         unicode('%s_dep' % view_name))

    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'cname'
    record_arguments_record_assignments_dict[
        'argument_value'] = hostname
    records_dict = self.db_instance.GetEmptyRowDict(
        'records')
    records_dict['record_type'] = u'cname'
    records_dict['record_view_dependency'] = '%s_dep' % view_name
    records_dict['record_zone_name'] = zone_name
    self.db_instance.StartTransaction()
    try:
      found_records = self.db_instance.ListRow(
          'records', records_dict,
          'record_arguments_records_assignments',
          record_arguments_record_assignments_dict,
          'zone_view_assignments', zone_view_assignments_dict)
    finally:
      self.db_instance.EndTransaction()
    cnames = []
    for record in found_records:
      new_record = {}
      new_record['record_type'] = record[
          'record_arguments_records_assignments_type']
      new_record['zone_name'] = record['record_zone_name']
      new_record['target'] = record['record_target']
      new_record['ttl'] = record['record_ttl']
      new_record['view_name'] = record[
          'record_view_dependency'].rsplit('_dep')[0]
      new_record['assignment_host'] = record['argument_value']
      new_record['last_user'] = record['record_last_user']
      new_record['zone_origin'] = record['zone_origin']
      cnames.append(new_record)

    if( not recursive ):
      return cnames
    new_cnames = []
    for record in cnames:
      new_cnames.extend(self.GetAssociatedCNAMEs(
          '%s.%s' % (record['target'], record['zone_origin']),
          record['view_name'], record['zone_name'], recursive=recursive))
    cnames.extend(new_cnames)
    del new_cnames
    del found_records

    return cnames

  def ListLatestNamedConfig(self, dns_server_set):
    """Lists the latest named config string given dns server set

    This function is duplicated in
    roster-config-manager/roster_config_manager/tree_exporter.py

    Inputs:
      dns_server_set: string of dns server set name

    Outputs:
      dict: dictionary of latest named config
    """
    named_configs = self.core_instance.ListNamedConfGlobalOptions(
        dns_server_set=dns_server_set)
    current_timestamp = datetime.datetime.now()
    smallest_time_differential = datetime.timedelta(weeks=100000)
    newest_config = None
    for named_config in named_configs:
      time_differential = current_timestamp - named_config['timestamp']
      if( time_differential < smallest_time_differential ):
        smallest_time_differential = time_differential
        newest_config = named_config

    return newest_config

  def RevertNamedConfig(self, dns_server_set, option_id):
    """Revert a Named Config file

    Inputs:
      option_id: the id of config to replicate
      dns_server_set: string of dns server set name
    
    Raises:
      InvalidInputError: DNS server set does not contain id.
      UnexpectedDataError: Multiple configurations found.
    """
    named_config = self.core_instance.ListNamedConfGlobalOptions(
        dns_server_set=dns_server_set, option_id=option_id)
    if( len(named_config) == 0 ):
      raise errors.InvalidInputError(
        'DNS server set "%s" does not contain id "%s"' % (
            dns_server_set, option_id))
    elif( len(named_config) == 1 ):
      self.core_instance.MakeNamedConfGlobalOption(
          dns_server_set, named_config[0]['options'])
    else:
      raise errors.UnexpectedDataError('Multiple configurations found.')

  def MakeAAAARecord(self, target, zone_name, record_args_dict,
                     view_name=None, ttl=None):
    """Makes an AAAA record.

    Inputs:
      target: string of target
      zone_name: string of zone name
      record_args_dict: dictionary of record arguments
      view_name: string of view name
      ttl: time to live
    """
    record_args_dict['assignment_ip'] = unicode(IPy.IP(record_args_dict[
        'assignment_ip']).strFullsize())
    self.core_instance.MakeRecord(u'aaaa', target, zone_name, record_args_dict,
                                  view_name, ttl)

  def MakeSubdomainDelegation(self, zone_name, subdomain_name, nameserver, 
                              view_name=u'any'):
    """"Makes a Delegated Subdomain
    Assumes delegation zone is created

    Inputs:
      view_name: string of view name
      zone_name: string of zone name
      subdomain_name: string of subdomain name 
      nameserver: string of fully qualified nameserver
    Raises:
      InvalidInputError: Zone does not exist.
    """
    self.core_instance.MakeRecord(u'ns', subdomain_name, zone_name,
                                  {u'name_server':nameserver}, view_name)

  def GetPTRTarget(self, long_target, view_name=u'any'):
    """Gets the short PTR target given the long PTR target
    Inputs:
      long_target: String of long PTR target
      view_name: String of view name

    Raises:
      InvalidInputError: No suitable reverse range zone assignments found.
    Outputs:
      string: String of short PTR target
    """
    if( not long_target.endswith('in-addr.arpa.') and not
        long_target.endswith('ip6.arpa.') ):
      long_target = self.ReverseIP(long_target)
    zone_assignment = None
    reverse_range_zone_assignments = (
        self.core_instance.ListReverseRangeZoneAssignments())
    ip_address = IPy.IP(self.UnReverseIP(long_target))
    for zone_assignment in reverse_range_zone_assignments:
      if( zone_assignment in reverse_range_zone_assignments ):
        if( ip_address in IPy.IP(
            reverse_range_zone_assignments[zone_assignment]) ):
          break
    else:
      raise errors.InvalidInputError(
          'No suitable reverse range zone assignments found.')
    zone_detail = self.core_instance.ListZones(view_name=view_name)
    zone_origin = zone_detail[zone_assignment][view_name]['zone_origin']
    # Count number of characters in zone origin, add one to count the extra
    # period and remove that number of characters from the target.
    zone_origin_length = len(zone_origin) + 1
    short_target = long_target[:-zone_origin_length]

    return (short_target, zone_assignment)

  def MakePTRRecord(self, target, record_args_dict,
                    view_name=u'any', ttl=None):
    """Makes a ptr record.

    Inputs:
      target: string of target
      record_args_dict: dictionary of record arguments
      view_name: string of view name
      ttl: string of ttl
    """
    target, zone_assignment = self.GetPTRTarget(target, view_name)
    if( record_args_dict['assignment_host'].startswith('@.') ):
      record_args_dict['assignment_host'] = record_args_dict[
          'assignment_host'].lstrip('@.')
    self.core_instance.MakeRecord(u'ptr', target, zone_assignment,
                                  record_args_dict, view_name, ttl)

  def RemovePTRRecord(self, record_type, target, zone_name, record_args_dict,
                      view_name, ttl=None):
    """Removes a ptr record.

    Inputs:
      target: string of target
      record_args_dict: dictionary of record arguments
      view_name: string of view name
      ttl: string of ttl
    """
    if( record_args_dict['assignment_host'].startswith('@.') ):
      record_args_dict['assignment_host'] = record_args_dict[
          'assignment_host'].lstrip('@.')
    self.core_instance.RemoveRecord(record_type, target, zone_name,
                                    record_args_dict, view_name, ttl)

  def MakeIPv4ClasslessReverseDelegation(self, name_server, cidr_block,
                                     view_name=u'any', ttl=None):
    """Creates classless forwarding for reverse DNS lookups

    Inputs:
      name_server: nameserver to add for reverse delegation
      cidr_block: string of CIDR block
      view_name: string of view for the reverse zone, defaults to 'any'
      ttl: time-to-live for the newly added records, defaults to zone ttl

    Raises:
      InvalidInputError: nameserver required
      InvalidInputError: cidr block range required
      InvalidInputError: Not a valid zone name or CIDR block
    """
    view_dep = '%s_dep' % view_name
    cidr_octets = cidr_block.split('.')
    num_octets = len(cidr_octets)
    if( num_octets != 4 ):
      raise errors.InvalidInputError('Invalid CIDR octet number')
    cidr_block_target = cidr_octets[-1]
    broadcast_last_octet = cidr_block_target.split('/')[0]
    netmask = cidr_block_target.split('/')[1]
    if( str.isdigit(str(broadcast_last_octet)) and str.isdigit(str(netmask))):
      if( int(netmask) < 25 or int(netmask) > 31 ):
        raise errors.InvalidInputError('Invalid CIDR netmask: %s' % netmask)
      if( int(broadcast_last_octet) < 0 or int(broadcast_last_octet) > 255):
        raise errors.InvalidInputError('Invalid CIDR last octet')
    else:
      raise errors.InvalidInputError('Invalid CIDR last octet/netmask')

    for i in range(1, len(cidr_octets) - 1):
      if( str.isdigit(str(cidr_octets[i])) ):
        if( int(cidr_octets[i]) < 0 or int(cidr_octets[i]) > 255):
          raise errors.InvalidInputError('Invalid CIDR octet %s' %
                                         cidr_octets[i])
      else:
          raise errors.InvalidInputError('Invalid CIDR octet %s' %
                                         cidr_octets[i])

    cidr_for_ipy = cidr_octets[0]
    for i in range(1, num_octets - 1):
      cidr_for_ipy = '%s.%s' % (cidr_for_ipy, cidr_octets[i])
    cidr_for_ipy = '%s.%s/%s' % (cidr_for_ipy, '0', netmask)
    expanded_cidr = self.CIDRExpand(cidr_for_ipy,
                                    begin=long(broadcast_last_octet))
    expanded_cidr.remove(expanded_cidr[-1])

    zone_name = self.ListZoneByIPAddress(cidr_block)
    if( zone_name is None ):
      raise errors.InvalidInputError(
          'ERROR: zone that includes cidr block %s not found' % cidr_block)

    records = self.core_instance.ListRecords(zone_name=zone_name)
    for record in records:
      for ip in expanded_cidr:
        if( self.ReverseIP(ip).split('.')[0] == record['target'] ):
          raise errors.InvalidInputError('ERROR: existing record(s) with '
                                         'target: %s overlaps given cidr: %s' %
                                         (record['target'], cidr_block))

    records_batch = []
    cidr_last_target = int(broadcast_last_octet) + pow(2, 32 - int(netmask))
    ns_target = cidr_block_target
    ns_args_dict = self.core_instance.GetEmptyRecordArgsDict(u'ns')
    ns_args_dict['name_server'] = name_server
    ns_record = {'record_type': u'ns', 'record_target': ns_target,
                 'record_zone_name': zone_name, 'view_name': view_name,
                 'record_view_dependency': view_dep,
                 'record_arguments': ns_args_dict}
    records_batch.append(ns_record)

    for ip in expanded_cidr:
      reverse_ip = self.ReverseIP(ip)
      split_reverse_ip = reverse_ip.split('.')
      target = split_reverse_ip[0]
      reverse_ip_for_record = '%s.%s' % (target, cidr_block_target)
      for i in range(1, len(split_reverse_ip)):
        reverse_ip_for_record = '%s.%s' % (reverse_ip_for_record,
                                           split_reverse_ip[i])
      if( target == broadcast_last_octet or target == unicode(
             cidr_last_target - 1) ):
        continue
      cname_args_dict = self.core_instance.GetEmptyRecordArgsDict(u'cname')
      cname_args_dict['assignment_host'] = unicode(reverse_ip_for_record)
      cname_record = {'record_type': u'cname', 'record_target': unicode(target),
                      'record_zone_name': zone_name, 'view_name': view_name,
                      'record_view_dependency': view_dep,
                      'record_arguments': cname_args_dict}
      records_batch.append(cname_record)

    self.ProcessRecordsBatch(add_records=records_batch)

  def MakeIPv4ClasslessReverseDelegatedTargetZone(self, cidr_block):
    """Creates a delegated reverse zone

    Inputs:
      cidr_block: string of IPv4 cidr block

    Raises:
      InvalidInputError: Not a valid cidr block
    """
    cidr_octets = cidr_block.split('.')
    cidr_block_target = cidr_octets[-1]
    broadcast_last_octet = cidr_block_target.split('/')[0]
    netmask = cidr_block_target.split('/')[1]

    if( str.isdigit(str(broadcast_last_octet)) and str.isdigit(str(netmask))):
      if( int(netmask) < 25 or int(netmask) > 31 or
          int(broadcast_last_octet) < 0 or int(broadcast_last_octet) > 255 ):
        raise errors.InvalidInputError('Invalid CIDR block')
    else:
      raise errors.InvalidInputError('Invalid CIDR block')

    for i in range(1, len(cidr_octets) - 1):
      if( str.isdigit(str(cidr_octets[i])) ):
        if( int(cidr_octets[i]) < 0 or int(cidr_octets[i]) > 255):
          raise errors.InvalidInputError('Invalid CIDR block')
      else:
          raise errors.InvalidInputError('Invalid CIDR block')

    zone_name = u'in-addr.arpa'
    for i in range(0, len(cidr_octets)):
      zone_name = u'%s.%s' % (cidr_octets[i], zone_name)
    zone_type = u'master'
    zone_origin = u'%s.' % zone_name
    self.core_instance.MakeZone(zone_name, zone_type, zone_origin)

  def ListAccessLevels(self):
    """Lists access levels from constants for both integer and string keys

    Outputs:
      dict: dictionary of access levels with both string and integer-string keys

    Example:
      {'32': 32, '64': 64, '128': 128, 'user': 32, 'unlocked_user': 64,
       'dns_admin': 128}
    """
    access_levels_dict = {}
    for key, value in constants.ACCESS_LEVELS.iteritems():
      access_levels_dict[str(value)] = value
      access_levels_dict[key] = value
    return access_levels_dict

  def ListAvailableIpsInCIDR(self, cidr_block, num_ips=1, view_name=None,
                             zone_name=None):
    """Finds first available ips. Only lists as many IPs as are available.
    Returns empty list if no IPs are available in given cidr block and a
    truncated list if only a portion of IPs are available.

    Inputs:
      cidr_block: string of ipv4 or ipv6 cidr block

    Raises:
      InvalidInputError: IP is in a reserved IP space.
      InvalidInputError: Not a valid cidr block
    Outputs:
      list: list of strings of ip addresses
    """
    try:
      cidr_block_ipy = IPy.IP(cidr_block)
    except ValueError:
      raise errors.InvalidInputError(
          '%s is not a valid cidr block' % cidr_block)
    reserved_ips = []
    if( cidr_block_ipy.version() == 6 ):
      reserved = constants.RESERVED_IPV6
    elif( cidr_block_ipy.version() == 4 ):
      reserved = constants.RESERVED_IPV4
    for cidr in reserved:
      reserved_ips.append(IPy.IP(cidr))
    for reserved_ip in reserved_ips:
      if( IPy.IP(cidr_block) in reserved_ip ):
        raise errors.InvalidInputError(
            '%s is in a reserved IP space' % cidr_block)
    records = self.ListRecordsByCIDRBlock(cidr_block, view_name=view_name,
                                          zone_name=zone_name)
    taken_ips = []
    avail_ips = []
    for view in records:
      for ip in records[view]:
        taken_ips.append(ip)
    count = 0L
    while( count < cidr_block_ipy.len() ):
      if( len(avail_ips) >= num_ips ):
        break
      if( cidr_block_ipy[count].strFullsize() not in taken_ips ):
        avail_ips.append(cidr_block_ipy[count].strFullsize())
      count += 1L
    return avail_ips

  def ListRecordsByCIDRBlock(self, cidr_block, view_name=None, zone_name=None):
    """Lists records in a given cidr block.

    Inputs:
      cidr_block: string of ipv4 or ipv6 cidr block
      view_name: string of the view
      zone_name: string of the zone
    
    Raise:
      InvalidInputError: The CIDR block specified does not contain a valid IP
      IPIndexError: Record type not indexable by IP
      IPIndexError: Record type unknown. Missing ipv4 or ipv6 dec index

    Outputs:
      dict: A dictionary Keyed by view, keyed by IP, listed by record.
            example:
                {u'test_view':
                    {u'192.168.1.8':
                        [{u'forward': True,
                          u'host': u'host6.university.edu',
                          u'zone': u'forward_zone',
                          u'zone_origin': u'university.edu.'},
                         {u'forward': False,
                          u'host': u'host6.university.edu',
                          u'zone': u'reverse_zone',
                          u'zone_origin': u'1.168.192.in-addr.arpa.'}]}}
    """
    self.user_instance.Authorize('ListRecordsByCIDRBlock')
    record_list = {}
    try:
      IPy.IP(cidr_block)
    except ValueError:
      raise errors.InvalidInputError(
          'The CIDR block specified does not contain a valid IP: %s' % (
          cidr_block))
    cidr_block = IPy.IP(cidr_block).strFullsize(1)
    if( cidr_block.find('/') != -1 ):
      cidr_ip = IPy.IP(cidr_block.split('/')[0])
      cidr_size = int(cidr_block.split('/')[1])
    else:
      cidr_ip = IPy.IP(cidr_block)
      if( cidr_ip.version() == 4 ):
        cidr_size = 32
      elif( cidr_ip.version() == 6 ):
        cidr_size = 128
      else:
        raise errors.InvalidInputError(
            'The CIDR block specified does not contain a valid IP: %s' % (
            cidr_block))
    records_dict = self.db_instance.GetEmptyRowDict('records')
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    zone_dict = self.db_instance.GetEmptyRowDict('zones')
    record_arguments_records_assignments_dict = (
        self.db_instance.GetEmptyRowDict(
            'record_arguments_records_assignments'))

    if( view_name is not None and
        view_name.endswith('_dep') or view_name == u'any' ):
      records_dict['record_view_dependency'] = view_name
    elif( view_name is not None ):
      records_dict['record_view_dependency'] = '%s_dep' % view_name

    zone_dict['zone_name'] = zone_name

    if( cidr_ip.version() == 4 ):
      decimal_ip = int( cidr_ip.strDec() )
      decimal_ip_lower = (
          (decimal_ip >> (32 - cidr_size) ) << (32 - cidr_size))
      decimal_ip_upper = ( pow(2, 32 - cidr_size) - 1 ) | decimal_ip
      self.db_instance.StartTransaction()
      ip_index_dict = self.db_instance.GetEmptyRowDict('ipv4_index')
      try:
        record_list = self.db_instance.ListRow(
            'ipv4_index', ip_index_dict,
            'records', records_dict,
            'zones', zone_dict,
            'zone_view_assignments', zone_view_assignments_dict,
            'record_arguments_records_assignments', 
            record_arguments_records_assignments_dict,
            column='ipv4_dec_address',
            range_values=(decimal_ip_lower, decimal_ip_upper))
      finally:
        self.db_instance.EndTransaction()
    elif( cidr_ip.version() == 6 ):
      ip_index_dict = self.db_instance.GetEmptyRowDict('ipv6_index')
      if( cidr_size >= 64 ):
        try:
          ip_index_dict[u'ipv6_dec_upper'] = int(cidr_ip.strHex(0)[:-16], 0)
        except ValueError:
          ip_index_dict[u'ipv6_dec_upper'] = 0
        decimal_ip_lower = int('0x%s' % cidr_ip.strHex(0)[18:], 0)
        decimal_ip_lower_lower = (
            (decimal_ip_lower >> (128 - cidr_size)) <<
            (128 - cidr_size))
        decimal_ip_lower_upper = (
            (pow(2,128 - cidr_size) - 1 ) | decimal_ip_lower)
        column = 'ipv6_dec_lower'
        range_values = (decimal_ip_lower_lower, decimal_ip_lower_upper)
      elif( cidr_size < 64 ):
        try:
          decimal_ip_upper = int(cidr_ip.strHex()[:-16], 0)
        except ValueError:
          decimal_ip_upper = 0
        decimal_ip_upper_lower = (
            (decimal_ip_upper >> (64 - cidr_size)) << (64 - cidr_size))
        decimal_ip_upper_upper = (
            (pow(2,64 - cidr_size) - 1 ) | decimal_ip_upper)
        column = 'ipv6_dec_upper'
        range_values = (decimal_ip_upper_lower, decimal_ip_upper_upper)
      self.db_instance.StartTransaction()
      try:
        record_list = self.db_instance.ListRow(
            'ipv6_index', ip_index_dict,
            'records', records_dict,
            'zones', zone_dict,
            'zone_view_assignments', zone_view_assignments_dict,
            'record_arguments_records_assignments',
            record_arguments_records_assignments_dict,
            column=column,
            range_values=range_values)
      finally:
        self.db_instance.EndTransaction()

    ## Parse returned list
    parsed_record_dict = {}
    for _, record_entry in enumerate(record_list):
      if( record_entry[u'record_type'] not in
          constants.RECORD_TYPES_INDEXED_BY_IP ):
        raise errors.IPIndexError('Record type not indexable by '
                                  'IP: %s' % record_entry)
      if( record_entry[u'record_view_dependency'].endswith('_dep') ):
        record_view = record_entry[u'record_view_dependency'][:-4]
      else:
        record_view = record_entry[u'record_view_dependency']
      if( record_view not in parsed_record_dict ):
        parsed_record_dict[record_view] = {}
      if( u'ipv4_dec_address' in record_entry ):
        record_ip = u'%s' % (
            IPy.IP(record_entry[u'ipv4_dec_address']).strNormal(1))
        if( record_ip not in parsed_record_dict[record_view] ):
          parsed_record_dict[record_view][record_ip] = []
      elif( u'ipv6_dec_upper' in record_entry ):
        decimal_ip = (
            (record_entry[u'ipv6_dec_upper'] << 64) +
            (record_entry[u'ipv6_dec_lower']) )
        record_ip = u'%s' % IPy.IP(decimal_ip).strFullsize(0)
        if( record_ip not in parsed_record_dict[record_view] ):
          parsed_record_dict[record_view][record_ip] = []
      else:
        raise errors.IPIndexError(
            'Record type unknown. Missing ipv4 or ipv6 dec index: %s' % (
            record_entry))
      record_item = {}
      record_item['records_id'] = record_entry['records_id']
      record_item['record_type'] = record_entry['record_type']
      record_item['record_target'] = record_entry['record_target']
      record_item['record_ttl'] = record_entry['record_ttl']
      record_item['record_zone_name'] = record_entry['record_zone_name']
      record_item[u'zone_origin'] = record_entry[u'zone_origin']
      record_item['record_view_dependency'] = record_entry[
          'record_view_dependency']
      #record_item['record_last_updated'] = record_entry['record_last_updated']
      record_item['record_last_user'] = record_entry['record_last_user']
      if record_entry[u'record_view_dependency'].endswith('_dep'):
        record_item[u'view_name'] = record_entry[u'record_view_dependency'][:-4]
      else:
        record_item[u'view_name'] = record_entry[u'record_view_dependency']
      if( record_entry[u'record_type'] == u'a' or
          record_entry[u'record_type'] == u'aaaa' ):
        record_item[u'forward'] = True
        record_item[u'host'] = '%s.%s' % (
            record_entry[u'record_target'],
            record_entry[u'zone_origin'][:-1])
        record_item[u'zone_origin'] = record_entry['zone_origin']
        record_item[u'record_target'] = record_entry['record_target']
        record_item[u'record_args_dict'] = {
            'assignment_ip': record_entry['argument_value']}
        parsed_record_dict[record_view][record_ip].append( record_item )
      elif( record_entry[u'record_type'] == u'ptr' ):
        record_item[u'zone_origin'] = record_entry['zone_origin']
        record_item[u'record_target'] = record_entry['record_target']
        record_item[u'forward'] = False
        record_item[u'host'] = record_entry[u'argument_value'][:-1]
        assignment_ip = helpers_lib.UnReverseIP(
            '%s.%s' % (
                record_entry['record_target'],record_entry['zone_origin']))
        record_item[u'record_args_dict'] = {'assignment_ip': assignment_ip}
        parsed_record_dict[record_view][record_ip].insert(0, record_item )

    return parsed_record_dict

  def ListRecordsByZone(self, zone_name, view_name=None):
    """Lists records in a given zone.

    Inputs:
      zone_name: name of the zone
      view_name: name of the view
    
    Output:
      dict: A dictionary Keyed by view, keyed by IP, listed by record.
            example:
                {u'test_view':
                    {u'192.168.1.8':
                        [{u'forward': True,
                          u'host': u'host6.university.edu',
                          u'zone': u'forward_zone',
                          u'zone_origin': u'university.edu.'},
                         {u'forward': False,
                          u'host': u'host6.university.edu',
                          u'zone': u'reverse_zone',
                          u'zone_origin': u'1.168.192.in-addr.arpa.'}]}}
    """
    self.user_instance.Authorize('ListRecordsByZone')
    record_list = {}
    
    records_dict = self.db_instance.GetEmptyRowDict('records')
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    zone_dict = self.db_instance.GetEmptyRowDict('zones')
    zone_dict['zone_name'] = zone_name
    record_arguments_records_assignments_dict = (
        self.db_instance.GetEmptyRowDict(
            'record_arguments_records_assignments'))
    ipv4_index_dict = self.db_instance.GetEmptyRowDict('ipv4_index')
    ipv6_index_dict = self.db_instance.GetEmptyRowDict('ipv6_index')
    if( view_name is not None and
        view_name.endswith('_dep') or view_name == u'any' ):
      records_dict['record_view_dependency'] = view_name
    elif( view_name is not None ):
      records_dict['record_view_dependency'] = '%s_dep' % view_name

    args_ipv4 = ['zone_view_assignments', zone_view_assignments_dict,
                 'zones', zone_dict, 'records', records_dict,
                 'record_arguments_records_assignments',
                 record_arguments_records_assignments_dict]
    args_ipv6 = args_ipv4 + ['ipv6_index', ipv6_index_dict]
    args_ipv4.append('ipv4_index')
    args_ipv4.append(ipv4_index_dict)
    self.db_instance.StartTransaction()
    try:
      record_list = self.db_instance.ListRow(*args_ipv4)
      record_list = record_list + self.db_instance.ListRow(*args_ipv6)
    finally:
      self.db_instance.EndTransaction()
    #Parsing Records
    parsed_record_dict = {}
    for record_entry in record_list:
      if( record_entry[u'record_type'] not in 
          constants.RECORD_TYPES_INDEXED_BY_IP ):
        raise errors.IPIndexError('Record type not indexable by '
                                  'IP: %s' % record_entry)
      if( record_entry[u'record_view_dependency'].endswith('_dep') ):
        record_view = record_entry[u'record_view_dependency'][:-4]
      else:
        record_view = record_entry[u'record_view_dependency']
      if( record_view not in parsed_record_dict ):
          parsed_record_dict[record_view] = {}
      if( u'ipv4_dec_address' in record_entry ):
        record_ip = u'%s' % (
            IPy.IP(record_entry[u'ipv4_dec_address']).strNormal(1))
        if( record_ip not in parsed_record_dict[record_view] ):
          parsed_record_dict[record_view][record_ip] = []
      elif( u'ipv6_dec_upper' in record_entry ):
        decimal_ip = (
            (record_entry[u'ipv6_dec_upper'] << 64) +
            (record_entry[u'ipv6_dec_lower']) )
        record_ip = u'%s' % IPy.IP(decimal_ip).strFullsize(0)
        if( record_ip not in parsed_record_dict[record_view] ):
          parsed_record_dict[record_view][record_ip] = []
      else:
        raise errors.IPIndexError(
            'Record type unknown. Missing ipv4 or ipv6 dec index: %s' % (
            record_entry))
      record_item = {}
      record_item['records_id'] = record_entry['records_id']
      record_item['record_type'] = record_entry['record_type']
      record_item['record_target'] = record_entry['record_target']
      record_item['record_ttl'] = record_entry['record_ttl']
      record_item['record_zone_name'] = record_entry['record_zone_name']
      record_item[u'zone_origin'] = record_entry[u'zone_origin']
      record_item['record_view_dependency'] = record_entry[
                                              'record_view_dependency']
      record_item['record_last_user'] = record_entry['record_last_user']
      if record_entry[u'record_view_dependency'].endswith('_dep'):
        record_item[u'view_name'] = record_entry[u'record_view_dependency'][:-4]
      else:
        record_item[u'view_name'] = record_entry[u'record_view_dependency']
      if( record_entry[u'record_type'] == u'a' or
          record_entry[u'record_type'] == u'aaaa' ):
        record_item[u'forward'] = True
        record_item[u'host'] = '%s.%s' % (
            record_entry[u'record_target'],
            record_entry[u'zone_origin'][:-1])
        record_item[u'zone_origin'] = record_entry['zone_origin']
        record_item[u'record_target'] = record_entry['record_target']
        record_item[u'record_args_dict'] = {
            'assignment_ip': record_entry['argument_value']}
        parsed_record_dict[record_view][record_ip].append(record_item)
      elif( record_entry[u'record_type'] == u'ptr' ):
        record_item[u'zone_origin'] = record_entry['zone_origin']
        record_item[u'record_target'] = record_entry['record_target']
        record_item[u'forward'] = False
        record_item[u'host'] = record_entry[u'argument_value'][:-1]
        assignment_ip = helpers_lib.UnReverseIP(
            '%s.%s' % (
                record_entry['record_target'],record_entry['zone_origin']))
        record_item[u'record_args_dict'] = {'assignment_ip': assignment_ip}
        parsed_record_dict[record_view][record_ip].insert(0, record_item )
    return parsed_record_dict

  def SortRecordsByHost(self, records_dict):
    """Generates an IP list sorted by record's host
    Inputs:
      record_dict: dictionary keyed by view, then keyed by IP
                   dictionary from ListRecordsByCIDRBlock
                   and from ListRecordsByZone

    Outputs:
      sorted_list: list of sorted records
    """
    sorted_list = []
    target_sort = []
    for view in records_dict:
      for ip in records_dict[view]:
        for record in records_dict[view][ip]:
          target_sort.append(dict({'ip_address':IPy.IP(ip).strFullsize()}.items() + 
                                  record.items()))
    sorted_list = sorted(target_sort, key=lambda x: x['host'])
    return sorted_list

  def ListNamedConfGlobalOptionsClient(self, option_id=None,
                                       dns_server_set=None, timestamp=None):
    """Converts XMLRPC datetime to datetime object and runs
    ListNamedConfGlobalOptions

    Inputs:
      option_id: integer of the option id
      dns_server_set: string of the dns server set name
      timestamp: XMLRPC datetime timestamp

    Outputs:
      list: list of dictionarires from ListNamedConfGlobalOptions
    """
    success = False
    named_conf_global_options = None

    named_conf_global_options = self.core_instance.ListNamedConfGlobalOptions(
        option_id, dns_server_set, timestamp)
    success = True

    return named_conf_global_options

  def ListZoneByIPAddress(self, ip_address):
    """Lists zone name given ip_address

    Inputs:
      ip_address: string of ip address

    Outputs:
      string: string of zone name, ex: 'test_zone'
    """
    user_ip = IPy.IP(ip_address)
    reverse_range_zone_assignments = (
        self.core_instance.ListReverseRangeZoneAssignments())
    for reverse_range_zone_assignment in reverse_range_zone_assignments:
      db_cidr = IPy.IP(reverse_range_zone_assignments[
          reverse_range_zone_assignment])
      if( user_ip in db_cidr ):
        return reverse_range_zone_assignment

  def RemoveCNamesByAssignmentHost(self, hostname, view_name, zone_name):
    """Removes cname's by assignment hostname, will not remove cnames
    that the user does not have permissin to remove. The function will continue
    and pass over that cname.

    Inputs:
      hostname: string of hostname
      view_name: string of view name
      zone_name: string of zone name
    
    Raises:
      UnexpectedDataError: Incorrect number of records found

    Outputs:
      int: number of rows modified
    """
    function_name, current_args = helpers_lib.GetFunctionNameAndArgs()
    row_count = 0
    record_arguments_record_assignments_dict = (
        self.db_instance.GetEmptyRowDict(
            'record_arguments_records_assignments'))
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'cname'
    record_arguments_record_assignments_dict[
        'argument_value'] = hostname
    records_dict = self.db_instance.GetEmptyRowDict(
        'records')
    records_dict['record_type'] = u'cname'
    records_dict['record_view_dependency'] = '%s_dep' % view_name
    records_dict['record_zone_name'] = zone_name
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        found_record_arguments = self.db_instance.ListRow(
            'record_arguments_records_assignments',
            record_arguments_record_assignments_dict)
        remove_record_dict = {}
        for record_argument in found_record_arguments:
          remove_record_dict[record_argument[
              'record_arguments_records_assignments_record_id']] = {
                  'assignment_host': record_argument['argument_value']}
        for record_id in remove_record_dict:
          records_dict['records_id'] = record_id
          found_records_dict = self.db_instance.ListRow(
              'records', records_dict)
          if( len(found_records_dict) != 1 ):
            raise errors.UnexpectedDataError(
                'Incorrect number of records found!')
          try:
            self.core_instance.user_instance.Authorize(
                function_name,
                 record_data=
                     {'target': found_records_dict[0]['record_target'],
                      'zone_name': records_dict['record_zone_name'],
                      'view_name': records_dict['record_view_dependency'],
                      'record_type': records_dict['record_type']},

                current_transaction=True)
          except errors.AuthorizationError:
            continue
          row_count += self.db_instance.RemoveRow(
              'records', found_records_dict[0])
          remove_record_dict[record_id].update({
              'cname_host': found_records_dict[0]['record_target']})
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
      log_list = []
      for record_id in remove_record_dict:
        log_list.append('record_id:')
        log_list.append(str(record_id))
        for record in remove_record_dict[record_id]:
          log_list.append('%s:' % record)
          log_list.append(remove_record_dict[record_id][record])
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, function_name,
                                  current_args, success)
    return row_count

  def ConstructRecordArgsDictFromRecordID(self, record_id):
    """Constructs the records_arg_dict from the Roster database given only 
    the record id.

    Inputs:
    record_id: int of record id

    Outputs:
    record_args_dict: dictionary of arguments and their values
    """

    record_args_db_row = self.db_instance.GetEmptyRowDict(
      'record_arguments_records_assignments')
    record_args_db_row[
        'record_arguments_records_assignments_record_id'] = record_id
    record_args_db_dict = self.db_instance.ListRow(
      'record_arguments_records_assignments', record_args_db_row)

    record_args_dict = {}
    for key in record_args_db_dict:
      key_entry = key['argument_value']
      if( key_entry.isdigit() ):
        key_entry = int(key_entry)
      record_args_dict[
        key['record_arguments_records_assignments_argument_name']] = key_entry

    return record_args_dict

  def ProcessRecordsBatch(self, delete_records=None, add_records=None,
                          zone_import=False):
    """Proccess batches of records

    Inputs:
      delete_records: list of dictionaries of records
                      ex: {'record_ttl': 3600, 'record_type': u'a',
                          'records_id': 10, 'record_target': u'host1',
                          'record_zone_name': u'forward_zone',
                          'record_last_user': u'sharrell',
                          'record_view_dependency': u'test_view_dep'}
                          {'record_type': 'ptr', 'record_target': 'target',
                          'view_name': 'view', 'zone_name': 'zone'}
      add_records: list of dictionaries of records
    
    Raises: 
      RecordsBatchError: Record specification too broad
      RecordsBatchError: No record found
      RecordsBatchError: Record already exists
      RecordsBatchError: CNAME already exists
      RecordsBatchError: Duplicate record found

    Outputs:
      int: row count
    """
    if delete_records is None:
      delete_records = []
    if add_records is None:
      add_records = []
    function_name, current_args = helpers_lib.GetFunctionNameAndArgs()
    log_dict = {'delete': [], 'add': []}
    row_count = 0
    changed_view_dep = []
    success = False
    try:
      for record in add_records:
        self.db_instance.ValidateRecordArgsDict(record[u'record_type'], 
                                                record[u'record_arguments'])

      self.db_instance.StartTransaction()
      try:
        # REMOVE RECORDS
        for record in delete_records:
          record_dict = self.db_instance.GetEmptyRowDict('records')
          record_dict['records_id'] = record['records_id']
          record_dict['record_type'] = record['record_type']
          record_dict['record_target'] = record['record_target']
          record_dict['record_ttl'] = record['record_ttl']
          if( record['record_view_dependency'].endswith('_dep') or
              record['record_view_dependency'] == u'any' ):
            record_dict['record_view_dependency'] = record[
                'record_view_dependency']
          else:
            record_dict['record_view_dependency'] = (
                '%s_dep' % record['record_view_dependency'])
          record_dict['record_zone_name'] = record['record_zone_name']
          record_dict['record_last_user'] = record['record_last_user']
          record_args_dict = self.ConstructRecordArgsDictFromRecordID(
              record['records_id'])

          self.user_instance.Authorize('ProcessRecordsBatch',
              record_data = {
                  'target': record['record_target'],
                  'zone_name': record['record_zone_name'],
                  'view_name': record_dict['record_view_dependency'],
                  'record_type': record['record_type'],
                  'record_args_dict': record_args_dict},
              current_transaction=True)

          rows_deleted = self.db_instance.RemoveRow('records', record_dict)
          log_dict['delete'].append(record)
          row_count += 1
          if( rows_deleted > 1 ):
            raise errors.RecordsBatchError(
                  'Record specification too broad, '
                  'found %d matching records for %s.' % (
                      rows_deleted, record_dict))
          elif( rows_deleted == 0 ):
            raise errors.RecordsBatchError(
                  'No record found for :%s' % record_dict)

        # ADD RECORDS
        for record in add_records:

          #Target length check
          if( not self.db_instance.data_validation_instance.isTarget(
              record[u'record_target']) ):
            raise errors.InvalidInputError('Target hostname is invalid. %s' % (
                record[u'record_target']))

          view_name = record['record_view_dependency']
          if( not record['record_view_dependency'].endswith('_dep') and record[
                'record_view_dependency'] != u'any'):
            view_name = '%s_dep' % record['record_view_dependency']
          self.user_instance.Authorize('ProcessRecordsBatch',
              record_data = {
                  'target': record['record_target'],
                  'zone_name': record['record_zone_name'],
                  'view_name': view_name,
                  'record_type': record['record_type'],
                  'record_args_dict': record['record_arguments']},
              current_transaction=True)
          if( record['record_type'] == u'ptr' ):
            if( record['record_arguments'][
                'assignment_host'].startswith('@.') ):
              record['record_arguments']['assignment_host'] = record[
                  'record_arguments']['assignment_host'].lstrip('@.')
          changed_view_dep.append((view_name, record['record_zone_name']))
          ttl = None
          if( 'ttl' in record ):
            ttl = record['ttl']
          if( ttl is None ):
            ttl = constants.DEFAULT_TTL

          records_dict = {'records_id': None,
                          'record_target': record['record_target'],
                          'record_type': None,
                          'record_ttl': None,
                          'record_zone_name': record['record_zone_name'],
                          'record_view_dependency': view_name,
                          'record_last_user': None}

          if( record['record_type'] == 'cname' ):
            all_records = self.db_instance.ListRow('records', records_dict)
            if( len(all_records) > 0 ):
              raise errors.RecordsBatchError(
                  'Record already exists with target %s.' % (
                  record['record_target']))
          records_dict['record_type'] = u'cname'
          cname_records = self.db_instance.ListRow('records', records_dict)
          if( len(cname_records) > 0 ):
            raise errors.RecordsBatchError('CNAME already exists with target '
                                           '%s.' % (record['record_target']))

          record_args_assignment_dict = self.db_instance.GetEmptyRowDict(
              'record_arguments_records_assignments')
          records_dict['record_type'] = record['record_type']
          raw_records = self.db_instance.ListRow(
              'records', records_dict, 'record_arguments_records_assignments',
              record_args_assignment_dict)
          records_dict['record_last_user'] = self.user_instance.GetUserName()
          records_dict['record_ttl'] = ttl
          current_records = (
              helpers_lib.GetRecordsFromRecordRowsAndArgumentRows(
              raw_records, record['record_arguments']))
          for current_record in current_records:
            for arg in record['record_arguments'].keys():
              if( arg not in current_record ):
                break
              if( record['record_arguments'][arg] is None ):
                continue
              if( record['record_arguments'][arg] != current_record[arg] ):
                break
            else:
              raise errors.RecordsBatchError('Duplicate record found: %s' %
                                             current_record)


          records_dict['record_type'] = record['record_type']
          record_id = self.db_instance.MakeRow('records', records_dict)
          for arg in record['record_arguments'].keys():
            record_argument_assignments_dict = {
               'record_arguments_records_assignments_record_id': record_id,
               'record_arguments_records_assignments_type': record[
                   'record_type'],
               'record_arguments_records_assignments_argument_name': arg,
               'argument_value': unicode(record['record_arguments'][arg])}
            self.db_instance.MakeRow('record_arguments_records_assignments',
                                     record_argument_assignments_dict)
            log_dict['add'].append(record)
            row_count += 1
          if( records_dict['record_type'] in
              constants.RECORD_TYPES_INDEXED_BY_IP ):
            self.core_instance._AddRecordToIpIndex(
                records_dict['record_type'], records_dict['record_zone_name'],
                records_dict['record_view_dependency'],
                record_id, records_dict['record_target'],
                record['record_arguments'])
        changed_view_dep = set(changed_view_dep)
        for view_dep_pair in changed_view_dep:
          self.core_instance._IncrementSoa(*view_dep_pair, missing_ok=zone_import)

      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, function_name,
                                  current_args, success)
    return row_count

  def ListSortedHostsByZone(self, zone_name, view_name=None):
    records_dict = self.ListRecordsByZone(zone_name, view_name=view_name)
    sorted_records = self.SortRecordsByHost(records_dict)
    hosts_dict = {}
    for record in sorted_records:
      direction = 'Reverse'
      if( record['forward'] ):
        direction = 'Forward'
      if( not hosts_dict.has_key(record[u'view_name']) ):
        hosts_dict.update({record[u'view_name']: []})
      new_record = record.copy()
      new_record['direction'] = direction
      hosts_dict[record[u'view_name']].append(new_record)
    return hosts_dict

  def ListSortedHostsByCIDR(self, cidr, zone_name=None, view_name=None):
    records_dict = self.ListRecordsByCIDRBlock(cidr, zone_name=zone_name, 
      view_name=view_name)
    ip_address_list = self.CIDRExpand(cidr)
    
    if ip_address_list is None:
      ip_address_list = []
    if( ip_address_list == [] ):
      for view in records_dict:
        ip_address_list.extend(records_dict[view].keys())
      ip_address_list = list(set(ip_address_list))

    hosts_dict = {}
    if( len(records_dict) == 0 ):
      hosts_dict['--'] = []
      for ip_address in ip_address_list:
        hosts_dict['--'].append(
            {'host': '--', 'direction': '--',
             'ip_address': ip_address, 'record_zone_name': '--'})
    else:
      for view in records_dict:
        if( not hosts_dict.has_key(view) ):
          hosts_dict.update({view: []})
        for ip_address in ip_address_list:
          if( ip_address in records_dict[view] ):
            for record in records_dict[view][ip_address]:
              direction = 'Reverse'
              if( record['forward'] ):
                direction = 'Forward'
              new_record = record.copy()
              new_record['direction'] = direction
              new_record['ip_address'] = ip_address
              hosts_dict[view].append(new_record)
          else:
            hosts_dict[view].append(
                {'ip_address': ip_address, 'direction': '--', 'host': '--',
                 'record_zone_name': '--'})
    return hosts_dict
# vi: set ai aw sw=2:
