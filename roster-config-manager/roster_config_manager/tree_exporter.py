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
__version__ = '#TRUNK#'


import bz2
import ConfigParser
import datetime
import os
import StringIO
import shutil
import tarfile

from roster_core import audit_log
from roster_core import config
from roster_core import constants
from roster_core import core
from roster_core import errors
from roster_core import helpers_lib
from roster_config_manager import zone_exporter_lib


class Error(errors.CoreError):
  pass


class MaintenanceError(Error):
  pass


class ChangesNotFoundError(Error):
  pass


class BindTreeExport(object):
  """This class exports zones"""
  def __init__(self, config_file_name, directory=None, dnssec=None,
               kskfile=None, zskfile=None):
    """Sets self.db_instance

    Inputs:
      config_file_name: name of config file to load db info from
    """
    self.tar_file_name = ''
    config_instance = config.Config(file_name=config_file_name)
    self.db_instance = config_instance.GetDb()
    self.raw_data = {}
    self.cooked_data = {}
    self.root_config_dir = config_instance.config_file['exporter'][
        'root_config_dir']
    if( directory ):
      self.named_dir = directory
    else:
      self.named_dir = config_instance.config_file['exporter']['named_dir']
    self.backup_dir = config_instance.config_file['exporter']['backup_dir']
    self.log_instance = audit_log.AuditLog(log_to_syslog=True, log_to_db=True,
                                           db_instance=self.db_instance)
    if( dnssec is None ):
      self.dnssec = config_instance.config_file['dnssec']['dnssec']
    else:
      self.dnssec = dnssec
    self.dnssec_signzone_exec = config_instance.config_file[
        'dnssec']['dnssec_signzone_exec']
    self.dnssec_keygen_exec = config_instance.config_file[
        'dnssec']['dnssec_keygen_exec']
    self.random = config_instance.config_file['dnssec']['random']
    self.encryption_algorithm = config_instance.config_file[
        'dnssec']['encryption']
    self.kskfile = kskfile
    self.zskfile = zskfile
    self.temp_zone_file = config_instance.config_file[
        'dnssec']['temp_zone_file']

  def MakeKey(self, zone_name, ksk=False):
    """Makes a zsk or ksk

    Inputs:
      ksk: boolean of whether or not to make a ksk key
    Outputs:
      str: key file name
    """
    command_array = [self.dnssec_keygen_exec]
    if( self.random ):
      command_array.append('-r %s' % self.random)
    if( ksk ):
      command_array.append('-f KSK -b 4096')
    else:
      command_array.append('-b 1024')
    command_array.append('-a %s' % self.encryption_algorithm)
    command_array.append('-n ZONE %s' % zone_name)

    key_handle = os.popen(' '.join(command_array))
    key_file = key_handle.read().strip()
    key_handle.close()

    return '%s.key' % key_file

  def SignZone(self, zone_file_string, zone_name):
    """Makes a zone file string into a signed zone

    Inputs:
      zone_file_string: string of zone file

    Outputs:
      str: string of signed zone file
    """
    closed = False
    if( not self.kskfile ):
      kskfile = self.MakeKey(zone_name, ksk=True)
    else:
      kskfile = self.kskfile
    if( not self.zskfile ):
      zskfile = self.MakeKey(zone_name)
    else:
      zskfile = self.zskfile
    ksk_string = open(kskfile).read()
    zsk_string = open(zskfile).read()

    zone_file_string = '%s%s%s' % (zone_file_string, ksk_string, zsk_string)
    try:
      temp_handle = open(self.temp_zone_file, 'w')
      temp_handle.writelines(zone_file_string)
      temp_handle.close()
      closed = True
      sign_zone_string = '%s -o %s -N INCREMENT -k %s %s %s' % (
          self.dnssec_signzone_exec, zone_name, kskfile,
          self.temp_zone_file, zskfile)
      output = os.popen3(sign_zone_string.split())
      new_zone_file = output[1].read()
      err = output[2].read()
      new_zone_file_contents = open(new_zone_file.strip()).read()
      return new_zone_file_contents
    except:
      raise
    finally:
      if( not closed ):
        temp_handle.close()
      if( os.path.exists(self.temp_zone_file) ):
        os.remove(self.temp_zone_file)

  def NamedHeaderChangeDirectory(self, named_conf_header, new_directory):
    """Adds/Changes directory in named.conf header

    Inputs:
      namedconf: string of namedconf header
    
    Outputs:
      string: string of namedconf header
    """
    namedconflines = named_conf_header.split('\n')
    found_options = False
    in_comment = False

    for line_number, line in enumerate(namedconflines):
      if( line.strip().startswith('#') ):
        continue
      elif( line.strip().startswith('//') ):
        continue
      elif( line.strip().startswith('/*') ):
        in_comment = True
      elif( '*/' in line and in_comment ):
        in_comment = False
        continue
      if( in_comment ):
        continue
      elif( line.strip().startswith('directory ') ):
        namedconflines.pop(line_number)
      elif( line.strip().startswith('options') ):
        found_options = True

    if( found_options ):
      for line_number, line in enumerate(namedconflines):
        if( line.strip().startswith('#') ):
          continue
        elif( line.strip().startswith('//') ):
          continue
        elif( line.strip().startswith('/*') ):
          in_comment = True
        elif( '*/' in line and in_comment ):
          in_comment = False
          continue
        if( in_comment ):
          continue
        for char in range(len(line)):
          if( line[char] == 'o' ):
            if( line[char:char + len('options')] == 'options' ):
              if( '{' not in line ):
                temp = char 
                while( '{' not in namedconflines[temp] ):
                  temp += 1
                else:
                  line = namedconflines[temp]
                  char += 1
              char_temp = 0
              while( char_temp < len(line) ):
                if( line[char_temp] == '{' ):
                  newline = '\tdirectory "%s";' % new_directory.rstrip('/')
                  namedconflines.insert(line_number + 1, newline)
                  return '\n'.join(namedconflines)
                if( line[char_temp] == '}' ):
                  return None
                char_temp += 1
              return None
    else:
      namedconflines.insert(-1, 'options\n{\n\tdirectory "%s";\n};\n' % (
          new_directory))
      return '\n'.join(namedconflines)


  def AddToTarFile(self, tar_file, file_name, file_string):
    """Adds file string to tarfile object

    Inputs:
      tarfile: tarfile object
      file_name: string of filename to add
      file_string: string of file
    """
    info = tarfile.TarInfo(name=file_name)
    info.size = len(file_string)
    tar_file.addfile(info, StringIO.StringIO(file_string))

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

  def ExportAllBindTrees(self, force=False):
    """Exports bind trees to files
    
    Inputs:
      force: boolean of if the export should continue if no changes are found
             in the database
    """
    function_name, current_args = helpers_lib.GetFunctionNameAndArgs()
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.LockDb()
        try:
          if( not force ):
            if( self.db_instance.CheckMaintenanceFlag() ):
              raise MaintenanceError('Database currently under maintenance.')
            audit_log_dict = self.db_instance.GetEmptyRowDict('audit_log')
            audit_log_dict['action'] = u'ExportAllBindTrees'
            audit_log_dict['success'] = 1
            audit_rows = self.db_instance.ListRow('audit_log', audit_log_dict)
            if( audit_rows ):
              audit_rows = self.db_instance.ListRow(
                  'audit_log', self.db_instance.GetEmptyRowDict('audit_log'),
                  date_column='audit_log_timestamp',
                  date_range=(audit_rows[-1]['audit_log_timestamp'],
                              datetime.datetime.now()))
              for row in audit_rows:
                if( row['action'] != u'ExportAllBindTrees' ):
                  break
              else:
                raise ChangesNotFoundError('No changes have been made to the '
                                           'database since last export, '
                                           'no export needed.')
          data, raw_dump = self.GetRawData()
          current_time = self.db_instance.GetCurrentTime()
        finally:
          self.db_instance.UnlockDb()
      finally:
          self.db_instance.EndTransaction()
      cooked_data = self.CookData(data)
      zone_view_assignments = {}
      for zone_view_assignment in data['zone_view_assignments']:
        if( not zone_view_assignment['zone_view_assignments_zone_name']
            in zone_view_assignments):
          zone_view_assignments[zone_view_assignment[
              'zone_view_assignments_zone_name']] = []
        zone_view_assignments[zone_view_assignment[
            'zone_view_assignments_zone_name']].append(zone_view_assignment[
            'zone_view_assignments_view_dependency'].split('_dep')[0])
      for zone_view_assignment in zone_view_assignments:
        if( zone_view_assignments[zone_view_assignment] == [u'any'] ):
          raise Error('Zone "%s" has no view assignments.' %
                      zone_view_assignment)

      record_arguments = data['record_arguments']
      record_argument_definitions = self.ListRecordArgumentDefinitions(
          record_arguments)

      temp_tar_file_name = 'temp_file.tar.bz2'
      tar_file = tarfile.open(temp_tar_file_name, 'w:bz2')
      if( len(cooked_data) == 0 ):
        raise Error('No dns server sets found.')
      for dns_server_set in cooked_data:
        dummy_config_file = StringIO.StringIO()
        config_parser = ConfigParser.SafeConfigParser()
        ## Make Files
        named_directory = '%s/%s_servers' % (
            self.root_config_dir.rstrip('/'), dns_server_set)
        if( not os.path.exists(named_directory) ):
          os.makedirs(named_directory)
        dns_server_set_directory = ('%s/%s_servers/named' % 
                                   (self.root_config_dir.rstrip('/'),
                                    dns_server_set))
        if( not os.path.exists(dns_server_set_directory) ):
          os.makedirs(dns_server_set_directory)
        config_file = '%s/%s_config' % (dns_server_set_directory,
                                        dns_server_set)
        config_parser.add_section('dns_server_set_parameters')
        config_parser.set('dns_server_set_parameters', 'dns_servers', ','.join(
            cooked_data[dns_server_set]['dns_servers']))
        config_parser.set('dns_server_set_parameters', 'dns_server_set_name',
                          dns_server_set)
        config_parser.write(dummy_config_file)
        self.AddToTarFile(tar_file, config_file, dummy_config_file.getvalue())
        if( len(cooked_data[dns_server_set]['views']) == 0 ):
          raise Error('Server set %s has no views.' % dns_server_set)
        for view in cooked_data[dns_server_set]['views']:
          view_directory = '%s/%s' % (dns_server_set_directory, view)
          if( not os.path.exists(view_directory) ):
            os.makedirs(view_directory)
          if( len(cooked_data[dns_server_set]['views'][view]['zones']) == 0 ):
            raise Error('Server set %s has no zones in %s view.' % (
              dns_server_set, view))
          for zone in cooked_data[dns_server_set]['views'][view]['zones']:
            if( view not in zone_view_assignments[zone] ):
              continue
            if( self.dnssec ):
              zone_file = '%s/%s/%s.db.signed' % (
                  dns_server_set_directory, view, zone)
            else:
              zone_file = '%s/%s/%s.db' % (dns_server_set_directory, view, zone)
            zone_file_string = zone_exporter_lib.MakeZoneString(
                cooked_data[dns_server_set]['views'][view]['zones'][zone][
                    'records'],
                cooked_data[dns_server_set]['views'][view]['zones'][zone][
                    'zone_origin'],
                record_argument_definitions, zone, view)

            if( self.dnssec ):
              zone_file_string = self.SignZone(zone_file_string, zone)

            self.AddToTarFile(tar_file, zone_file, zone_file_string)
        named_conf_file = '%s/named.conf' % named_directory.rstrip('/')
        named_conf_file_string = self.MakeNamedConf(data, cooked_data,
                                                    dns_server_set)
        self.AddToTarFile(tar_file, named_conf_file, named_conf_file_string)

      audit_log_replay_dump, full_database_dump = self.CookRawDump(raw_dump)

      success = True
      tar_file.close()
    finally:
      log_id = self.log_instance.LogAction(u'tree_export_user',
                                           function_name,
                                           current_args,
                                           success)


    self.tar_file_name = '%s/dns_tree_%s-%s.tar.bz2' % (
        self.backup_dir, current_time.strftime("%d_%m_%yT%H_%M"), log_id)
    if( not os.path.exists(self.backup_dir) ):
      os.makedirs(self.backup_dir)
    shutil.move(temp_tar_file_name, self.tar_file_name)

    audit_log_replay_dump_file = bz2.BZ2File(
        '%s/audit_log_replay_dump-%s.bz2' % (self.backup_dir, log_id),

        'w')
    try:
      audit_log_replay_dump_file.writelines(audit_log_replay_dump)
    finally:
      audit_log_replay_dump_file.close()
                                          
    full_dump_file = bz2.BZ2File('%s/full_database_dump-%s.bz2' % 
                                 (self.backup_dir, log_id), 'w')
    try:
      full_dump_file.writelines(full_database_dump)
    finally:
      full_dump_file.close()

    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)

  def CookRawDump(self, raw_dump):
    """This takes raw data from the database and turns it into a 
    mysqldump-like output.

    Inputs:
      raw_dump: list of dictionaries that contain all of the tables
                and their associated metadata

    Outputs:
      list: tuple of list of strings to be concatenated into mysql dump files
    """
    # Stole these lines from mysqldump output, not sure all are needed
    header = ['SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT;\n',
              'SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS;\n',
              'SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION;\n',
              'SET NAMES utf8;\n'
              'SET @OLD_TIME_ZONE=@@TIME_ZONE;\n',
              "SET TIME_ZONE='+00:00';\n",
              'SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS;\n',
              'SET UNIQUE_CHECKS=0;\n',
              'SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS;\n',
              'SET FOREIGN_KEY_CHECKS=0;\n',
              'SET @OLD_SQL_MODE=@@SQL_MODE;\n',
              "SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n",
              'SET @OLD_SQL_NOTES=@@SQL_NOTES;\n'
              'SET SQL_NOTES=0;\n']

    footer = ['SET SQL_MODE=@OLD_SQL_MODE;\n',
              'SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;\n',
              'SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;\n',
              'SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT;\n',
              'SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS;\n',
              'SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION;\n',
              'SET SQL_NOTES=@OLD_SQL_NOTES;\n']

    full_database_dump = []
    full_database_dump.extend(header)
    audit_log_replay_dump = []
    audit_log_replay_dump.extend(header)

    for table_name, table_data in raw_dump.iteritems():
      table_lines = [] 
      table_lines.append('DROP TABLE IF EXISTS `%s`;\n' % table_name)
      table_lines.append(table_data['schema'])
      table_lines[-1] = '%s;' % table_lines[-1]
      for row in table_data['rows']:
        insert_row = "INSERT INTO %s (%s) VALUES (%%(%s)s);\n" % (
            table_name, ','.join(table_data['columns']),
            ")s, %(".join(table_data['columns']))
        table_lines.append(insert_row % row)

      full_database_dump.extend(table_lines)
      if( table_name not in constants.TABLES_NOT_AUDIT_LOGGED ):
        audit_log_replay_dump.extend(table_lines)

    full_database_dump.extend(footer)
    audit_log_replay_dump.extend(footer)

    return (audit_log_replay_dump, full_database_dump)

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
    named_conf_header = self.ListLatestNamedConfGlobalOptions(data, dns_server_set)
    if( not named_conf_header ):
      raise Error('Named conf global options missing for server set "%s"' % (
          dns_server_set))
    named_conf_header = self.NamedHeaderChangeDirectory(
        named_conf_header, '%s/named' % self.named_dir.rstrip('/'))
    named_conf_lines.append(named_conf_header)
    for acl_range in data['acl_ranges']:
      if( not acl_range['acl_ranges_acl_name'] in acl_dict ):
        acl_dict[acl_range['acl_ranges_acl_name']] = {}
      if( acl_range['acl_range_cidr_block'] is None ):
        acl_dict[acl_range['acl_range_cidr_block']] = None
      else:
        if( not acl_range['acl_range_cidr_block'] in
            acl_dict[acl_range['acl_ranges_acl_name']] ):
          acl_dict[
              acl_range['acl_ranges_acl_name']][acl_range[
                  'acl_range_cidr_block']] = {}
        acl_dict[
            acl_range['acl_ranges_acl_name']][acl_range[
              'acl_range_cidr_block']] = acl_range['acl_range_allowed']

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
          if( self.dnssec ):
            named_conf_lines.append('\t\tfile "%s/named/%s/%s.db.signed";' % (
                self.named_dir.rstrip('/'), view_name, zone))
          else:
            named_conf_lines.append('\t\tfile "%s/named/%s/%s.db";' % (
                self.named_dir.rstrip('/'), view_name, zone))
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
      tuple of two dictionaries:
        dictionary of raw data keyed by data name with values of dicts 
            containing values of that type's attributes
        dictionary of the raw dump keyed by data name with values of
            dicts containing the db dump keyed by row, column, and schema
      example:
        ({'view_acl_assignments': ({
          'view_acl_assignments_view_name': u'external',
          'view_acl_assignments_acl_name': u'public'})},
        { u'zones':
          {'rows':[{}],
           'columns': [u'zones_id', u'zone_name'],
           'schema':(
               u'CREATE TABLE `zones` (\n  `zones_id` mediumint(8) ',
               'unsigned NOT NULL auto_increment,\n  `zone_name` varchar(255) ',
               'NOT NULL,\n  PRIMARY KEY  (`zones_id`),\n  UNIQUE KEY ;
               '`zone_name` (`zone_name`),\n  KEY `zone_name_1` '
               '(`zone_name`)\n) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT ',
               'CHARSET=utf8')}}),
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

    acl_ranges_dict = self.db_instance.GetEmptyRowDict('acl_ranges')
    data['acl_ranges'] = self.db_instance.ListRow('acl_ranges', acl_ranges_dict)

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
    raw_dump = self.db_instance.DumpDatabase()

    return (data, raw_dump)

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
      arg_name = record[
          'record_arguments_records_assignments_argument_name']

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

      sorted_records[(zone_name, view_dep)][record_id][arg_name] = record[
              'argument_value']

      if( sorted_records[(zone_name, view_dep)][record_id][
          arg_name].isdigit() ):
        sorted_records[(zone_name, view_dep)][record_id][arg_name] = int(
            sorted_records[(zone_name, view_dep)][record_id][arg_name])

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

              for zone in data['zone_view_assignments']:
                view_dependency_name = view_dependency[
                    'view_dependency_assignments_view_dependency']
                zone_name = zone['zone_view_assignments_zone_name']
                if( view_dependency_name == zone[
                      'zone_view_assignments_view_dependency'] and
                      (zone_name, view_dependency_name) in sorted_records ):
                  if( not zone_name in cooked_data[
                        dns_server_set_name]['views'][view_name]['zones'] ):
                    cooked_data[dns_server_set_name]['views'][view_name][
                        'zones'][zone_name]= {}
                  if( 'records' not in cooked_data[dns_server_set_name][
                          'views'][view_name]['zones'][zone_name] ):
                      cooked_data[dns_server_set_name]['views'][view_name][
                          'zones'][zone_name]['records'] = []

                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['records'].extend(sorted_records[(
                          zone_name, view_dependency_name)].values())
                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['zone_origin'] = zone['zone_origin']

                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['zone_options'] = zone['zone_options']

                  cooked_data[dns_server_set_name]['views'][view_name][
                      'zones'][zone_name]['zone_type'] = zone[
                          'zone_view_assignments_zone_type']

    return cooked_data

