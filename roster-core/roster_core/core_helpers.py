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
__version__ = '0.9'


import datetime
import IPy
import constants
import core
import errors
import math

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

  def ListAccessRights(self):
    """Lists access rights.

    Output:
      list: list of access rights. ex: ['rw', 'r']
    """
    return constants.ACCESS_RIGHTS

  def ReverseIP(self, ip_address):
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

  def UnReverseIP(self, ip_address):
    """Un-Reverses reversed IP addresses

    Inputs:
      ip_address: either an ipv4 or ipv6 string (reversed)

    Outputs:
      string: forward ip address
    """
    mask = 0
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

  def CIDRExpand(self, cidr_block):
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
    """
    named_config = self.core_instance.ListNamedConfGlobalOptions(
        dns_server_set=dns_server_set, option_id=option_id)
    if( len(named_config) == 0 ):
      raise errors.CoreError('DNS server set "%s" does not contain id "%s"' % (
          dns_server_set, option_id))
    elif( len(named_config) == 1 ):
      self.core_instance.MakeNamedConfGlobalOption(
          dns_server_set, named_config[0]['options'])
    else:
      raise errors.CoreError('Multiple configurations found.')

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

  def ExpandIPV6(self, ip_address):
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

  def GetPTRTarget(self, long_target, view_name=u'any'):
    """Gets the short PTR target given the long PTR target

    Inputs:
      long_target: String of long PTR target
      view_name: String of view name

    Ouptuts:
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
      raise errors.CoreError(
          'No suitable reverse range zone assignments found.')
    zone_detail = self.core_instance.ListZones(view_name=view_name)
    zone_origin = zone_detail[zone_assignment][view_name]['zone_origin']
    # Count number of characters in zone origin, add one to count the extra
    # period and remove that number of characters from the target.
    zone_origin_length = len(zone_origin) + 1
    short_target = long_target[:-zone_origin_length:]

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
    self.core_instance.MakeRecord(u'ptr', target, zone_assignment,
                                  record_args_dict, view_name, ttl)

  def ListRecordsByCIDRBlock(self, cidr_block, view_name=None):
    """Lists records in user given cidr block.

    Inputs:
      cidr_block: string of ipv4 or ipv6 cidr block

    Outputs:
      dict: dictionary keyed by ip address example:
            {u'192.168.1.7': {u'a': False, u'host': u'host5.',
                              u'ptr': True, u'zone': u'test_zone',
                              u'view': u'test_view2'},
             u'192.168.1.5': {u'a': True, u'host': u'host3.',
             u'ptr': True, u'zone': u'test_zone', u'view': u'test_view2'}}
    """
    user_cidr = IPy.IP(cidr_block)
    record_type = u'a'
    if( user_cidr.version() == 6 ):
      record_type = u'aaaa'
    zones = self.core_instance.ListZones()
    if( not view_name ):
      view_name = u'any'

    ptr_record_list = []
    fwd_record_list = []
    zone_list = []

    ptr_dict = self.db_instance.GetEmptyRowDict('records')
    ptr_dict['record_type'] = u'ptr'
    ptr_args_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments_records_assignments')

    zone_dict = self.db_instance.GetEmptyRowDict(
        'reverse_range_zone_assignments')

    fwd_dict = self.db_instance.GetEmptyRowDict('records')
    fwd_dict['record_type'] = record_type
    fwd_args_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments_records_assignments')
    fwd_args_dict['record_arguments_records_assignments_argument_name'] = (
        u'assignment_ip')
    self.db_instance.StartTransaction()
    try:
      reverse_range_zone_assignments_db = (
          self.db_instance.ListRow(
              'reverse_range_zone_assignments', zone_dict))
      for reverse_range_zone_assignment in reverse_range_zone_assignments_db:
        db_zone = reverse_range_zone_assignment[
            'reverse_range_zone_assignments_zone_name']
        db_cidr = IPy.IP(reverse_range_zone_assignment[
            'reverse_range_zone_assignments_cidr_block'])
        if( user_cidr in db_cidr ):
          zone_list = [db_zone]
          break
        if( db_cidr in user_cidr ):
          zone_list.append(db_zone)
      for zone in zone_list:
        ptr_dict['record_zone_name'] = zone
        ptr_record_list.extend(self.db_instance.ListRow(
            'records', ptr_dict, 'record_arguments_records_assignments',
            ptr_args_dict))
      num_records = self.db_instance.TableRowCount('records')
      ratio = num_records / float(user_cidr.len())
      if( ratio > constants.RECORD_RATIO ):
        for ip_address in user_cidr:
          fwd_args_dict['argument_value'] = unicode(ip_address.strFullsize())
          fwd_record_list.extend(self.db_instance.ListRow(
              'records', fwd_dict, 'record_arguments_records_assignments',
              fwd_args_dict))
      else:
        fwd_record_list = self.db_instance.ListRow('records',
            fwd_dict, 'record_arguments_records_assignments', fwd_args_dict)
    finally:
      self.db_instance.EndTransaction()
    records_dict = {}
    for record in ptr_record_list:
      zone_name = record['record_zone_name']
      db_view_name = record['record_view_dependency'].rsplit('_dep', 1)[0]
      if( db_view_name != view_name and view_name != 'any'):
        continue
      if( db_view_name not in zones[zone_name]  ):
        raise errors.CoreError('No zone view combination found for '
                               '"%s" zone and "%s" view.' % (
                                   zone_name, db_view_name))
      zone_origin = zones[zone_name][db_view_name]['zone_origin']
      reverse_ip_address = '%s.%s' % (record['record_target'], zone_origin)
      ip_address = self.UnReverseIP(reverse_ip_address)
      if( IPy.IP(ip_address) in user_cidr ):
        if( not db_view_name in records_dict ):
          records_dict[db_view_name] = {}
        if( not ip_address in records_dict[db_view_name] ):
          records_dict[db_view_name][ip_address] = []
        records_dict[db_view_name][ip_address].append({
            u'forward': False, u'host': record['argument_value'].rstrip('.'),
            u'zone': record['record_zone_name'], 'zone_origin': zone_origin})
    for record in fwd_record_list:
      ip_address = record['argument_value']
      zone_name = record['record_zone_name']
      db_view_name = record['record_view_dependency'].rsplit('_dep', 1)[0]
      if( db_view_name != view_name and view_name != 'any'):
        continue
      zone_origin = zones[zone_name][db_view_name]['zone_origin']
      if( IPy.IP(ip_address) in user_cidr ):
        if( not view_name in records_dict ):
          records_dict[view_name] = {}
        if( not ip_address in records_dict[view_name] ):
           records_dict[view_name][ip_address] = []
        records_dict[view_name][ip_address].append({
            u'forward': True, u'host': '%s.%s' % (
                record['record_target'], zone_origin.rstrip('.')),
            u'zone': record['record_zone_name'],
            u'zone_origin': zone_origin})
    return records_dict

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
    if( timestamp is not None ):
      timestamp = datetime.datetime.strptime(timestamp.value,
                                             "%Y%m%dT%H:%M:%S")
    return self.core_instance.ListNamedConfGlobalOptions(
        option_id, dns_server_set, timestamp)

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

    Outputs:
      int: number of rows modified
    """
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
        row_count = 0
        for record_id in remove_record_dict:
          records_dict['records_id'] = record_id
          found_records_dict = self.db_instance.ListRow(
              'records', records_dict)
          if( len(found_records_dict) != 1 ):
            raise errors.CoreError('Incorrect number of records found!')
          try:
            self.core_instance.user_instance.Authorize(
                'RemoveRecord', target=found_records_dict[0]['record_target'])
          except self.core_instance.user_instance.AuthError:
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
      remove_record_string = ''
      log_list = []
      for record_id in remove_record_dict:
        log_list.append('record_id:')
        log_list.append(str(record_id))
        for record in remove_record_dict[record_id]:
          log_list.append('%s:' % record)
          log_list.append(remove_record_dict[record_id][record])
      if( log_list ):
        remove_record_string = ' '.join(log_list)
    finally:
      self.core_instance.log_instance.LogAction(
          self.core_instance.user_instance.user_name,
          u'RemoveCNamesByAssignmentHost',
          u'hostname: %s cnames_removed: (%s)' % (
              hostname, remove_record_string), success)

    return row_count

  def ProcessRecordsBatch(self, delete_records=[], add_records=[]):
    """Proccess batches of records

    Inputs:
      delete_records: list of dictionaries of records
                      ex: {'record_type': 'a', 'record_target': 'target',
                           'view_name': 'view', 'zone_name': 'zone',
                           'record_arguments': {'assignment_ip': '1.2.3.4'}}
      add_records: list of dictionaries of records

    Outputs:
      int: row count
    """
    log_dict = {'delete': [], 'add': []}
    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        # REMOVE RECORDS
        for record in delete_records:
          self.user_instance.Authorize('RemoveRecord', target=record[
              'record_target'])
          records_dict = self.db_instance.GetEmptyRowDict('records')
          records_dict['record_type'] = record['record_type']
          records_dict['record_target'] = record['record_target']
          records_dict['record_zone_name'] = record['record_zone_name']
          view_name = record['view_name']
          if( not record['view_name'].endswith('_dep') and record[
                'view_name'] != u'any'):
            view_name = '%s_dep' % record['view_name']
          records_dict['record_view_dependency'] = view_name
          if( 'record_ttl' in record ):
            records_dict['record_ttl'] = record['record_ttl']
          args_list = []
          for argument in record['record_arguments']:
            if( record['record_arguments'][argument] is None ):
              raise errors.CoreError('"%s" cannot be None' % argument)
            args_list.append(
                {u'record_arguments_records_assignments_argument_name':
                     argument,
                 u'record_arguments_records_assignments_type':
                     record['record_type'],
                 u'argument_value': record['record_arguments'][argument],
                 u'record_arguments_records_assignments_record_id': None})
          args_search_list = []
          record_ids = []
          final_id = []
          record_id_dict = {}
          for arg in args_list:
            args_search_list.append(self.db_instance.ListRow(
                'record_arguments_records_assignments', arg))
          for index, record_args in enumerate(args_search_list):
            record_ids.append([])
            for args_dict in record_args:
              record_ids[index].append(args_dict[
                  u'record_arguments_records_assignments_record_id'])
          for id_list in record_ids:
            for search_id in id_list:
              if( search_id in record_id_dict ):
                record_id_dict[search_id] += 1
              else:
                record_id_dict[search_id] = 1
          for record_id in record_id_dict:
            if( record_id_dict[record_id] == len(args_list) ):
              final_id.append(record_id)
          if( len(final_id) == 1 ):
            records_dict['records_id'] = final_id[0]
            new_records = self.db_instance.ListRow('records', records_dict)
            rows_deleted = self.db_instance.RemoveRow('records', new_records[0])
            if( not rows_deleted ):
              raise core.RecordError('Record with record_id %s not found' %
                                     final_id)
            log_dict['delete'].append(record)
            row_count += 1

        # ADD RECORDS
        for record in add_records:
          self.user_instance.Authorize('MakeRecord', target=record[
              'record_target'])
          view_name = record['view_name']
          if( not record['view_name'].endswith('_dep') and record[
                'view_name'] != u'any'):
            view_name = '%s_dep' % record['view_name']
          ttl = None
          if( 'ttl' in record ):
            ttl = record['ttl']
          if( ttl is None ):
            ttl = constants.DEFAULT_TTL

          records_dict = {'records_id': None,
                          'record_target': record['record_target'],
                          'record_type': None,
                          'record_ttl': ttl,
                          'record_zone_name': record['record_zone_name'],
                          'record_view_dependency': view_name,
                          'record_last_user': self.user_instance.GetUserName()}
          if( record['record_type'] == 'a' or record['record_type'] == 'cname' ):
            current_records = self.db_instance.ListRow('records', records_dict)
            for record in current_records:
              if( record['record_type'] == 'a' or
                  record['record_type'] == 'cname' ):
                raise RecordError('Record already exists with that target '
                                  'target: %s type: %s' %
                                  (record['record_type'],
                                   record['record_target']))

          records_dict['record_type'] = record['record_type']
          record_id = self.db_instance.MakeRow('records', records_dict)
          for k in record['record_arguments'].keys():
            record_argument_assignments_dict = {
               'record_arguments_records_assignments_record_id': record_id,
               'record_arguments_records_assignments_type': record[
                   'record_type'],
               'record_arguments_records_assignments_argument_name': k,
               'argument_value': unicode(record['record_arguments'][k])}
            self.db_instance.MakeRow('record_arguments_records_assignments',
                                     record_argument_assignments_dict)
            log_dict['add'].append(record)
            row_count += 1

          if( record['record_type'] != u'soa' ):
            self.core_instance._IncrementSoa(record['view_name'],
                                             record['record_zone_name'])

      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      for operation in log_dict:
        for record in log_dict[operation]:
          self.log_instance.LogAction(self.user_instance.user_name,
                                      u'ProcessRecordsBatch(%s)' % operation,
                                      u'record_type: %s target: %s '
                                       'zone_name: %s record_args_dict: %s '
                                       'view_name: %s' % (
                                           record['record_type'],
                                           record['record_target'],
                                           record['record_zone_name'],
                                           record['record_arguments'],
                                           record['view_name']), success)
    return row_count

  def CIDRtoOrigin(self, cidr_block):
    ip = IPy.IP(cidr_block)

