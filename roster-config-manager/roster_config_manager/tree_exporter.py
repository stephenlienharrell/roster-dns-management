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


"""This module is used for exporting data in the database for all hosts
to a BIND readable text form.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.6'


import os
import ConfigParser
import datetime

from roster_core import config
from roster_core import constants
from roster_config_manager import zone_exporter_lib


class Error(Exception):
  pass

class BindTreeExport(object):
  """This class exports zones"""
  def __init__(self, config_file_name, root_config_dir):
    """Sets self.db_instance

    Inputs:
      config_file_name: name of config file to load db info from
    """
    config_instance = config.Config(file_name=config_file_name)
    self.db_instance = config_instance.GetDb()
    self.raw_data = {}
    self.cooked_data = {}
    self.root_config_dir = root_config_dir

  def ListRecordArgumentDefinitions(self, record_arguments):
    """Lists record argument definitions given table from database

    This function is duplicated in roster-core/roster_core/core.py

    Inputs:
      record_arguments: record arguments from database

    Outputs:
      dictionary keyed by record type with values of lists
        of lists of record arguments sorted by argument order.
        example: {'mx': [{'argument_name': u'priority',
                          'record_arguments_type': u'mx',
                          'argument_data_type': u'UnsignedInt',
                          'argument_order': 0},
                         {'argument_name': u'mail_server',
                          'record_arguments_type': u'mx',
                          'argument_data_type': u'Hostname',
                          'argument_order': 1}]}
    """
    sorted_record_arguments = {}
    for record_argument in record_arguments:
      current_record_type = record_argument['record_arguments_type']
      del record_argument['record_arguments_type']
      del record_argument['argument_data_type']
      if( not current_record_type in sorted_record_arguments ):
        sorted_record_arguments[current_record_type] = []
      sorted_record_arguments[current_record_type].append(record_argument)
    for record_argument in sorted_record_arguments:
      sorted_record_arguments[record_argument] = sorted(
          sorted_record_arguments[record_argument],
          key=lambda k: k['argument_order'])
    return sorted_record_arguments

  def ExportAllBindTrees(self):
    """Exports bind trees to files"""
    self.db_instance.StartTransaction()
    try:
      self.db_instance.LockDb()
      try:
        data = self.GetRawData()
      finally:
        self.db_instance.UnlockDb()
    finally:
        self.db_instance.EndTransaction()
    cooked_data = self.CookData(data)

    record_arguments = data['record_arguments']
    record_argument_definitions = self.ListRecordArgumentDefinitions(
        record_arguments)
    for dns_server_set in cooked_data:
      config_parser = ConfigParser.SafeConfigParser()
      ## Make Files
      dns_server_set_directory = '%s/%s_servers' % (self.root_config_dir,
          dns_server_set)
      if( not os.path.exists(dns_server_set_directory) ):
        os.makedirs(dns_server_set_directory)
      config_file = '%s/%s_config' % (dns_server_set_directory, dns_server_set)
      config_parser.add_section('dns_server_set_parameters')
      config_parser.set('dns_server_set_parameters', 'dns_servers', ','.join(
          cooked_data[dns_server_set]['dns_servers']))
      config_parser.set('dns_server_set_parameters', 'dns_server_set_name',
                        dns_server_set)
      config_parser_file = open(config_file, 'wb')
      config_parser.write(config_parser_file)
      for view in cooked_data[dns_server_set]['views']:
        view_directory = '%s/%s' % (dns_server_set_directory, view)
        if( not os.path.exists(view_directory) ):
          os.makedirs(view_directory)
        for zone in cooked_data[dns_server_set]['views'][view]['zones']:
          zone_file = '%s/%s/%s.db' % (dns_server_set_directory, view, zone)
          zone_file_string = zone_exporter_lib.MakeZoneString(
              cooked_data[dns_server_set]['views'][view]['zones'][zone][
                  'records'],
              cooked_data[dns_server_set]['views'][view]['zones'][zone][
                  'zone_origin'],
              record_argument_definitions)
          zone_file_handle = open(zone_file, 'w')
          try:
            zone_file_handle.writelines(zone_file_string)
          finally:
            zone_file_handle.close()
      named_conf_file = '%s/named.conf' % dns_server_set_directory
      named_conf_file_string = self.MakeNamedConf(data, cooked_data,
                                                  dns_server_set)
      named_conf_file_handle = open(named_conf_file, 'w')
      try:
        named_conf_file_handle.writelines(named_conf_file_string)
      finally:
        named_conf_file_handle.close()

  def ListLatestNamedConfGlobalOptions(self, data, dns_server_set):
    """Lists latest named.conf global options

    This function is duplicated in roster-core/roster_core/core_helpers.py

    Inputs:
      data: data from GetRawData
      dns_server_set: string of dns server set name

    Outputs:
      string: string of latest named.conf global options
    """
    current_timestamp = datetime.datetime.now()
    smallest_time_differential = datetime.timedelta(weeks=100000)
    newest_config = None
    for named_config in data['named_conf_global_options']:
      time_differential = current_timestamp - named_config['options_created']
      if( named_config['named_conf_global_options_dns_server_set_name'] == (
            dns_server_set) ):
        if( time_differential < smallest_time_differential ):
          smallest_time_differential = time_differential
          newest_config = named_config['global_options']

    return newest_config

  def MakeNamedConf(self, data, cooked_data, dns_server_set):
    """Makes named.conf file strings

    Inputs:
      data: data from GetRawData
      cooked_data: data from cooked_data
      dns_server_set: string of dns_server_set

    Outputs:
      string: string of named.conf file
    """
    acl_dict = {}
    named_conf_lines = ['#This named.conf file is autogenerated. DO NOT EDIT']
    named_conf_lines.append(self.ListLatestNamedConfGlobalOptions(
        data, dns_server_set))
    for acl in data['acls']:
      if( not acl['acl_name'] in acl_dict ):
        acl_dict[acl['acl_name']] = {}
      if( acl['acl_cidr_block'] is None ):
        acl_dict[acl['acl_cidr_block']] = None
      else:
        if( not acl['acl_cidr_block'] in acl_dict[acl['acl_name']] ):
          acl_dict[acl['acl_name']][acl['acl_cidr_block']] = {}
        acl_dict[acl['acl_name']][acl['acl_cidr_block']] = acl[
            'acl_range_allowed']
    for acl in acl_dict:
      if( acl_dict[acl] is not None and acl != 'any' ):
        named_conf_lines.append('acl %s {' % acl)
        for cidr in acl_dict[acl]:
          if( acl_dict[acl][cidr] ):
            named_conf_lines.append('\t%s;' % cidr)
          else:
            named_conf_lines.append('\t!%s;' % cidr)
        named_conf_lines.append('};\n')

    for view_name in cooked_data[dns_server_set]['views']:
      named_conf_lines.append('view "%s" {' % view_name)
      clients = []
      found_acl = False
      for acl_name in cooked_data[dns_server_set]['views'][view_name]['acls']:
        clients.append('%s;' % acl_name)
      if( clients == [] and found_acl ):
        clients = [u'any;']
      named_conf_lines.append('\tmatch-clients { %s };' % ' '.join(clients))
      for zone in cooked_data[dns_server_set]['views'][view_name]['zones']:
          named_conf_lines.append('\tzone "%s" {' % (
              cooked_data[dns_server_set]['views'][view_name]['zones'][zone][
                  'zone_origin'].rstrip('.')))
          named_conf_lines.append('\t\ttype %s;' % cooked_data[
              dns_server_set]['views'][view_name]['zones'][zone]['zone_type'])
          named_conf_lines.append('\t\tfile "%s/%s.db";' % (view_name, zone))
          zone_options = cooked_data[dns_server_set]['views'][view_name][
              'zones'][zone]['zone_options'].replace('\n', '\n\t\t')
          named_conf_lines.append('\t\t%s' % zone_options.rsplit('\n\t\t', 1)[0])
          named_conf_lines.append('\t};')
      named_conf_lines.append('};')
    return '\n'.join(named_conf_lines)

  def ListACLNamesByView(self, data, view):
    """Lists acl names

    Inputs:
      data: data from GetRawData
      view: string of view name

    Outputs:
      list: list of acl names ex:
            ['private', 'public']
    """
    acl_list = []
    for view_acl_assignment in data['view_acl_assignments']:
      if( view_acl_assignment['view_acl_assignments_view_name'] == view ):
        acl_list.append(view_acl_assignment['view_acl_assignments_acl_name'])
    return acl_list

  def GetRawData(self):
    """Gets raw data from database

    Outputs:
      dict: dictionary keyed by table name
    """
    data = {}
    named_conf_global_options_dict = self.db_instance.GetEmptyRowDict(
        'named_conf_global_options')
    data['named_conf_global_options'] = self.db_instance.ListRow(
        'named_conf_global_options', named_conf_global_options_dict)

    dns_server_set_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_view_assignments')
    data['dns_server_set_view_assignments'] = self.db_instance.ListRow(
        'dns_server_set_view_assignments', dns_server_set_view_assignments_dict)

    dns_server_set_assignments_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_assignments')
    data['dns_server_set_assignments'] = self.db_instance.ListRow(
        'dns_server_set_assignments', dns_server_set_assignments_dict)

    dns_server_set_dict = self.db_instance.GetEmptyRowDict('dns_server_sets')
    data['dns_server_sets'] = self.db_instance.ListRow('dns_server_sets',
                                                       dns_server_set_dict)

    view_dependency_assignments_dict = self.db_instance.GetEmptyRowDict(
        'view_dependency_assignments')
    data['view_dependency_assignments'] = self.db_instance.ListRow(
        'view_dependency_assignments', view_dependency_assignments_dict)

    view_acl_assignments_dict = self.db_instance.GetEmptyRowDict(
        'view_acl_assignments')
    data['view_acl_assignments'] = self.db_instance.ListRow(
        'view_acl_assignments', view_acl_assignments_dict)

    acls_dict = self.db_instance.GetEmptyRowDict('acls')
    data['acls'] = self.db_instance.ListRow('acls', acls_dict)

    record_arguments_records_assignments_dict = (
        self.db_instance.GetEmptyRowDict(
          'record_arguments_records_assignments'))
    data['record_arguments_records_assignments'] = self.db_instance.ListRow(
        'record_arguments_records_assignments',
        record_arguments_records_assignments_dict)

    records_dict = self.db_instance.GetEmptyRowDict('records')
    data['records'] = self.db_instance.ListRow(
        'records', records_dict, 'record_arguments_records_assignments',
        record_arguments_records_assignments_dict)

    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    data['zone_view_assignments'] = self.db_instance.ListRow(
        'zone_view_assignments', zone_view_assignments_dict)

    record_arguments_dict = self.db_instance.GetEmptyRowDict('record_arguments')
    data['record_arguments'] = self.db_instance.ListRow('record_arguments',
                                                        record_arguments_dict)

    return data

  def SortRecords(self, records):
    """Sorts records for zone exporter

    Inputs:
      records: list of records

    Outputs:
      dict: dictionary keyed by tuple (zone, view_dep)
      ex:
      {(u'university.edu', u'internal_dep'):
          {11: {'target': u'computer4', 'ttl': 3600, 'record_type': u'a',
                'view_name': u'internal', 'last_user': u'sharrell',
                'zone_name': u'university.edu',
                u'assignment_ip': u'192.168.1.4'},
           12: {u'serial_number': 20091225, u'refresh_seconds': 5,
                'target': u'university.edu.',
                u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
                'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
                'view_name': u'internal', 'last_user': u'sharrell',
                'zone_name': u'university.edu',
                u'admin_email': u'admin@university.edu.',
                u'expiry_seconds': 5}}}
    """
    sorted_records = {}
    for record in records:
      zone_name =  record['record_zone_name']
      view_dep = record['record_view_dependency']
      record_id = record['record_arguments_records_assignments_record_id']

      if( not sorted_records.has_key((zone_name, view_dep)) ):
        sorted_records[(zone_name, view_dep)] = {}
      if( not sorted_records[(zone_name, view_dep)].has_key(record_id) ):
        sorted_records[(zone_name, view_dep)][record_id] = {}

        sorted_records[(zone_name, view_dep)][record_id]['record_type'] = (
            record['record_type'])

        sorted_records[(zone_name, view_dep)][record_id]['zone_name'] = (
            record['record_zone_name'])

        sorted_records[(zone_name, view_dep)][record_id]['view_name'] = (
            record['record_view_dependency'].rsplit('_dep', 1)[0])

        sorted_records[(zone_name, view_dep)][record_id]['target'] = (
            record['record_target'])

        sorted_records[(zone_name, view_dep)][record_id]['ttl'] = (
            record['record_ttl'])

        sorted_records[(zone_name, view_dep)][record_id]['last_user'] = (
            record['record_last_user'])

      if( record['argument_value'].isdigit() ):
        record['argument_value'] = int(record['argument_value'])

      sorted_records[(zone_name, view_dep)][record_id][record[
          'record_arguments_records_assignments_argument_name']] = record[
              'argument_value']

    return sorted_records

  def CookData(self, data):
    """Cooks data for zone exporter

    Inputs:
      data: dictionary of raw data from database

    Outputs:
      dict: dictionary keyed by dns_server_set ex:
      {u'external_dns': {
          'dns_servers': [u'[ns1.university.edu]', u'[dns2.university.edu]',
                          u'[dns3.university.edu]'],
          'views': {u'external':
              {u'university.edu': {'records':
                  [{u'serial_number': 20091227, u'refresh_seconds': 5,
                    'target': u'university.edu.',
                    u'name_server': u'ns1.university.edu.', u'retry_seconds': 5,
                    'ttl': 3600, u'minimum_seconds': 5, 'record_type': u'soa',
                    'view_name': u'external', 'last_user': u'sharrell',
                    'zone_name': u'university.edu',
                    u'admin_email': u'admin@university.edu.',
                    u'expiry_seconds': 5},
                   {'target': u'computer1', 'ttl': 3600, 'record_type': u'a',
                    'view_name': u'external', 'last_user': u'sharrell',
                    'zone_name': u'university.edu',
                    u'assignment_ip': u'1.2.3.5'},
                    'zone_origin': u'example.', 'zone_type': u'master'}}}}}
    """
    cooked_data = {}
    sorted_records = self.SortRecords(data['records'])

    for dns_server_set in data['dns_server_sets']:
      dns_server_set_name = dns_server_set['dns_server_set_name']

      if( not dns_server_set_name in cooked_data ):
        cooked_data[dns_server_set_name] = {}
      if( not 'dns_servers' in cooked_data[dns_server_set_name] ):
        cooked_data[dns_server_set_name]['dns_servers'] = []
      if( not 'views' in cooked_data[dns_server_set_name] ):
        cooked_data[dns_server_set_name]['views'] = {}

      for dns_server_set_assignment in data['dns_server_set_assignments']:
        if( dns_server_set_assignment[
            'dns_server_set_assignments_dns_server_set_name'] ==
            dns_server_set['dns_server_set_name'] and
            dns_server_set_assignment[
                'dns_server_set_assignments_dns_server_name']
            not in cooked_data[dns_server_set_name]['dns_servers'] ):

          cooked_data[dns_server_set_name]['dns_servers'].append(
              dns_server_set_assignment[
                  'dns_server_set_assignments_dns_server_name'])

      for dns_server_set_view_assignment in data[
            'dns_server_set_view_assignments']:
        dns_server_set_name = dns_server_set_view_assignment[
            'dns_server_set_view_assignments_dns_server_set_name']
        view_name = dns_server_set_view_assignment[
            'dns_server_set_view_assignments_view_name']
        if( dns_server_set_name == dns_server_set['dns_server_set_name'] ):

          for view_dependency in data['view_dependency_assignments']:
            if( view_name == view_dependency[
                  'view_dependency_assignments_view_name'] ):

              for zone in data['zone_view_assignments']:
                view_dependency_name = view_dependency[
                    'view_dependency_assignments_view_dependency']
                zone_name = zone['zone_view_assignments_zone_name']
                if( view_dependency_name == zone[
                      'zone_view_assignments_view_dependency'] and
                         (zone_name, view_dependency_name) in sorted_records ):
                  if( not view_name in cooked_data[
                        dns_server_set_name]['views'] ):
                    cooked_data[dns_server_set_name]['views'][view_name] = {}
                  if( not 'acls' in cooked_data[
                        dns_server_set_name]['views'][view_name] ):
                    cooked_data[dns_server_set_name]['views'][view_name][
                        'acls'] = self.ListACLNamesByView(data, view_name)
                  if( not 'zones' in cooked_data[
                        dns_server_set_name]['views'][view_name] ):
                    cooked_data[dns_server_set_name]['views'][view_name][
                        'zones'] = {}
                  if( not zone_name in cooked_data[
                        dns_server_set_name]['views'][view_name] ):
                    cooked_data[dns_server_set_name]['views'][view_name][
                        'zones'][zone_name]= {}

                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['records'] = sorted_records[(
                          zone_name, view_dependency_name)].values()

                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['zone_origin'] = zone['zone_origin']

                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['zone_options'] = zone['zone_options']

                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['zone_type'] = zone[
                          'zone_view_assignments_zone_type']

    return cooked_data
