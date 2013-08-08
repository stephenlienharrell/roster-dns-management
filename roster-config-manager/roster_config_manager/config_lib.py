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

"""This module conains all of the logic to check dns servers."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'

import ConfigParser
import datetime
import iscpy
import os
import roster_core
import shutil
import tarfile

from fabric import api as fabric_api
from fabric import network as fabric_network
from fabric import state as fabric_state
from fabric.exceptions import NetworkError as FabricNetworkError
from roster_core import config
from roster_core import errors


roster_core.core.CheckCoreVersionMatches(__version__)

class ConfigManagerError(errors.CoreError):
  pass

class ExporterNoFileError(ConfigManagerError, errors.UserError):
  pass

class ExporterFileError(ConfigManagerError, errors.UserError):
  pass

class ExporterFileNameError(ExporterFileError):
  pass

class ExporterListFileError(ExporterFileError):
  pass

class ExporterAuditIdError(ConfigManagerError, errors.UserError):
  pass

class ServerCheckError(ConfigManagerError, errors.UserError):
  pass

class QueryCheckError(ConfigManagerError, errors.UserError):
  pass

class ConfigLib(object):
  """This class checks a DNS server for the functionality required to push
  zone files to it"""

  ToolList = ['named-checkzone', 'named-compilezone', 
              'named-checkconf', 'tar']

  COMMANDS_CONVERT_DICT = {
    'check-dup-records': {'fail': 'fail', 'warn': 'warn', 'ignore': 'ignore'},
    'check-mx':          {'fail': 'fail', 'warn': 'warn', 'ignore': 'ignore'},
    'check-mx-cname':    {'fail': 'fail', 'warn': 'warn', 'ignore': 'ignore'},
    'check-srv-cname':   {'fail': 'fail', 'warn': 'warn', 'ignore': 'ignore'},
    'check-wildcard':    {'yes': 'warn', 'no': 'ignore'},

    'check-names':       {'flag': '-k', 'default': 'fail'},
    'check-integrity':   {'yes': 'full', 'no': 'none'}
  }

  CHECKZONE_ARGS_DICT = {
    'check-dup-records': {'flag': '-r', 'arg': 'warn'},
    'check-mx':          {'flag': '-m', 'arg': 'warn'},
    'check-mx-cname':    {'flag': '-M', 'arg': 'warn'},
    'check-srv-cname':   {'flag': '-S', 'arg': 'warn'},

    'check-wildcard':    {'flag': '-W', 'arg': 'warn'},
    'check-names':       {'flag': '-k', 'arg': 'fail'},
    'check-integrity':   {'flag': '-i', 'arg': 'full'}
  }

  #Option clauses that we're interested in, and their default BIND value.
  BIND_OPTION_CLAUSES = {
    'check-dup-records': 'warn',
    'check-mx':          'warn',
    'check-mx-cname':    'warn',
    'check-srv-cname':   'warn',
    'check-wildcard':    'yes',
    'check-names':       'warn',
    'check-integrity':   'yes',
    'check-siblings':    'yes'
  }

  def __init__(self, config_file):
    """
    """
    self.config_file = ConfigParser.SafeConfigParser()
    self.config_file.read(config_file)
    self.root_config_dir = self.config_file.get(
        'exporter', 'root_config_dir').rstrip('/')
    self.backup_dir = self.config_file.get(
        'exporter', 'backup_dir').rstrip('/')
    self.max_threads = int(self.config_file.get(
        'exporter', 'max_threads'))
  
  def UnTarDnsTree(self, audit_log_id=None):
    """Uncompresses the compressed Dns Tree to the 
    root configuration directory.

    Inputs:
      audit_log_id: id of the audit log of a compressed dns tree

    Outputs:
      audit_log_id: int - the same as the input, unless the input is None.
      In which case, the most recent audit log will be returned.

    Raises:
      ExporterFileError Compressed files will not be extracted to /root/config.
    """
    if( audit_log_id is None ):
      audit_log_id, filename = self.FindNewestDnsTreeFilename()
    else:
      filename = self.FindDnsTreeFilename(audit_log_id)
    if( filename is None ):
      raise ExporterNoFileError('Could not find a DNS tree for audit %s.' % 
                              audit_log_id)
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    try:
      tar_file = tarfile.open('%s/%s' % (self.backup_dir, filename), 'r:bz2')
      tar_file.extractall(path=self.root_config_dir)
    except tarfile.TarError:
      raise ExporterFileError('Could not extract the DNS tree %s/%s to %s.' % (
          self.backup_dir, filename, self.root_config_dir))
    tar_file.close()
    return audit_log_id

  def TarDnsTree(self, audit_log_id):
    """Compresses the uncompressed Roster Tree in the root configuration
        directory to the compressed Roster Tree in the Bind Directory.

    Inputs:
      audit_log_id: id of the audit log to a backup tree

    Raises:
      ExporterAuditIdError No audit log id supplied.
      ExporterFileError Can not list files in /dir
    """
    if( audit_log_id is None):
      raise ExporterAuditIdError('No audit log id supplied.')
    filename = self.FindDnsTreeFilename(audit_log_id)

    self.backup_dir = self.backup_dir.rstrip('/')
    self.root_config_dir = self.root_config_dir.rstrip('/')

    try:
      dns_server_files = os.listdir(self.root_config_dir)
    except OSError:
      raise ExporterListFileError('Can not list files in %s.' % 
                                  self.root_config_dir)
    temp_tar_name = 'tmp_dns_tree.tar.bz2'
    tar_file = tarfile.open('%s/%s' % (self.root_config_dir, temp_tar_name), 
                            'w:bz2')

    try:
      # Files in /root_config_dir
      #   All directories
      for server_dir in dns_server_files:
        if( os.path.isdir('%s/%s' % (self.root_config_dir, server_dir)) ):
          #Check next directory level for files, and named
          try:
            server_files = os.listdir('%s/%s' % (self.root_config_dir, 
                                                 server_dir))
          except OSError:
            raise ExporterListFileError('Can not list files in %s/%s.' % 
                                    (self.root_config_dir, server_dir))
          # Files in /root_config_dir/server
          #   One directory (named)
          #   A few files (named_not_compiled.conf, named_compiled.conf, 
          #     server.info)
          for server_file in server_files:
            if( os.path.isdir('%s/%s/%s' % (self.root_config_dir, server_dir, 
                                            server_file)) ):
              try:
                named_files = os.listdir('%s/%s/%s' % (self.root_config_dir, 
                    server_dir, server_file))
              except OSError:
                raise ExporterListFileError('Can not list files in %s/%s/%s.' %
                    (self.root_config_dir, server_dir, server_file))
              # Files in /root_config_dir/server/named
              #   All directories
              for view in named_files:
                self.__AddToTarFile__('%s/%s/%s' % (server_dir, server_file,
                    view), self.root_config_dir, tar_file)
                if( view == 'named.ca' ):
                  continue
                try:
                  view_files = os.listdir('%s/%s/%s/%s' % (self.root_config_dir,
                      server_dir, server_file, view))
                except OSError:
                  raise ExporterListFileError('Can not list files in '
                      '%s/%s/%s/%s.' % (self.root_config_dir, server_dir,
                                        server_file, view))
                      
                # Files in /root_config_dir/server/named/view
                #   All files
                for zone in view_files:
                  self.__AddToTarFile__('%s/%s/%s/%s' % (server_dir,
                      server_file, view, zone), self.root_config_dir, tar_file)
            else:
              self.__AddToTarFile__('%s/%s' % (server_dir, server_file),
                  self.root_config_dir, tar_file)
    except ExporterFileError:
      # Removes the temporary tarfile that was created.
      tar_file.close()
      os.remove('%s/%s' % (self.root_config_dir, temp_tar_name))
      raise
    tar_file.close()

    # Temporarily moves the original audit file (if htere was one)
    #   in case something happens in transfering the new DNS tree.
    if( filename is not None ):
      shutil.move('%s/%s' % (self.backup_dir, filename),
                  '%s/%s.tmp' % (self.backup_dir, filename))
    date = datetime.datetime
    tar_file_name = 'dns_tree_%s-%s.tar.bz2' % (
        date.now().strftime('%d_%m_%yT%H_%M'), audit_log_id)
    try:
      shutil.move('%s/%s' % (self.root_config_dir, temp_tar_name),
                  '%s/%s' % (self.backup_dir, tar_file_name))
    except shutil.Error as err:
      if( filename is not None ):
        shutil.move('%s/%s.tmp' % (self.backup_dir, filename),
                    '%s/%s' % (self.backup_dir, filename))
      os.remove('%s/%s' % (self.root_config_dir, temp_tar_name))
      raise ExporterFileError('Unable to move the new DNS tree tar file to '
                              '%s/%s.' % (self.backup_dir, tar_file_name))
    if( filename is not None ):
      os.remove('%s/%s.tmp' % (self.backup_dir, filename))
    shutil.rmtree(self.root_config_dir)

  def __AddToTarFile__(self, filename, base_directory, tar_file):
    """Adds file object to tarfile object

    Inputs:
      tarfile: tarfile object
      file_name: path to file object
    """
    tar_file.add('%s/%s' % (base_directory, filename), arcname=filename)

  def FindAllDnsServers(self):
    """Finds and returns the names of all the DNS servers that we are exporting.

    This must be run after the bind trees are untarred to the 
    root_config_dir."""
    server_list = []
    try:
      server_list = os.listdir(self.root_config_dir)
    except OSError:
      raise ExporterNoFileError('DNS tree does not exist or has not been '
                                'exported yet.')
    for server in server_list:
      if( not os.path.isdir('%s/%s' % (self.root_config_dir, server)) ):
        raise ExporterFileError('%s is not a server; '
                                'invalid DNS tree format.' % server)
    return server_list

  def FindDnsTreeFilename(self, audit_log_id):
    """Finds the filename of the Dns Tree from the audit log id given.

    Inputs:
      audit_log_id: id of the requested audit log.  

    Raises:
      ExporterAuditIdError: No audit log id supplied.
      ExporterFileError: Can not list files in /dir.
      ExporterFileError: DNS Tree file /dir/filename is not named correctly.

    Outputs:
      string: filename of DNS Tree file
    """
    if( audit_log_id is None ):
      raise ExporterAuditIdError('No audit log id supplied.')
    audit_log_id = '%s' % audit_log_id
    file_list = []
    try:
      file_list = os.listdir(self.backup_dir)
    except OSError:
      raise ExporterListFileError('Can not list files in %s.' % self.backup_dir)
    dns_tree_filename = None
    for file_name in file_list:
      if( not file_name.startswith('dns_tree') ):
        continue
      try:
        file_audit_id = int(file_name.split('-')[1].split('.')[0])
      except IndexError:
        raise ExporterFileNameError('DNS Tree file %s/%s is not named '
            'correctly.' % (self.backup_dir, file_name))
      if( audit_log_id=='%s' % file_audit_id ):
        dns_tree_filename = file_name
        newest = file_audit_id
        break
    else:
      dns_tree_filename = None
    return dns_tree_filename

  def FindNewestDnsTreeFilename(self):
    """Finds the filename of the newest Dns Tree file in the backup directory.

    Raises:
      ExporterListFileError: Can not list files in /dir.
      ExporterNoFileError: Backup directory /dir does not contain any files
                           or directories.
      ExporterFileNameError: DNS Tree file /dir/filename is not named correctly.
      ExporterNoFileError: Could not find a DNS Tree file in /dir.

    Outputs:
      tuple: id of audit log, name of Dns Tree file for audit log id
    """
    file_list = []
    try:
      file_list = os.listdir(self.backup_dir)
    except OSError:
      raise ExporterListFileError('Can not list files in %s.' % self.backup_dir)
    if( file_list == [] ):
      raise ExporterNoFileError('Backup directory %s does not contain any files'
                                ' or directories.' % self.backup_dir)
    newest = -1
    newest_file_name = None
    for file_name in file_list:
      if( not file_name.startswith('dns_tree') ):
        continue
      try:
        id = int(file_name.split('-')[1].split('.')[0])
      except IndexError:
        raise ExporterFileNameError('DNS Tree file %s/%s is not named '
                                    'correctly.' % (self.backup_dir, file_name))
      if( id > newest ):
        newest_file_name = file_name
        newest = id
    if( newest_file_name is None ):
      raise ExporterNoFileError('Could not find a DNS Tree file in %s.' %
                              self.backup_dir)
    return newest, newest_file_name

  def GetDnsServerInfo(self, dns_server):
    """Gets the information about a DNS server from the dns_server.info file

    Inputs:
      dns_server: name of DNS server

    Raises:
      ExporterNoFileError: DNS tree does not exist or has not been 
                           exported yet.
      ServerCheckError: DNS server server_name does not exist.
      ServerCheckError: DNS server metadata file does not exist.
      ServerCheckError: DNS server metadata file incorrectly written.

    Outputs:
      dict: {'server_info': {
                'server_name': 'university.lcl',
                'server_user': 'user',
                'bind_dir': '/etc/bind/',
                'test_dir': '/etc/bind/test/',
                'bind_version': 'UNKNOWN'},
             'tools': {
                'tar': 'True'}}
    """
    if( not os.path.exists(self.root_config_dir) ):
      raise ExporterNoFileError('DNS tree does not exist or has not been '
                                'exported yet.')
    if( not os.path.exists('%s/%s' % (self.root_config_dir, dns_server)) ):
      raise ServerCheckError('DNS server %s does not exist.' % dns_server)
    if( not os.path.exists('%s/%s/%s.info' % (self.root_config_dir, dns_server,
                                              dns_server)) ):
      # Right now we raise if the server.info file doesn't exist.
      # Should we just return an empty dictionary {} ?
      raise ServerCheckError('DNS server metadata file does not exist.')
    dns_server_info = ConfigParser.SafeConfigParser()
    dns_server_info.read('%s/%s/%s.info' % (self.root_config_dir, dns_server,
                                            dns_server))
    if( not dns_server_info.has_section('server_info') ):
      raise ServerCheckError('DNS server metadata file incorrectly written.')
    dns_server_options = dns_server_info.options('server_info')
    if( 'server_name' not in dns_server_options or
        dns_server_info.get('server_info','server_name') != dns_server or
        'server_user' not in dns_server_options or
        'bind_dir' not in dns_server_options or
        'test_dir' not in dns_server_options or
        'bind_version' not in dns_server_options ):
      raise ServerCheckError('DNS server metadata file incorrectly written.')

    server_info_dict = {}
    for section in dns_server_info.sections():
      if( section not in server_info_dict ):
        server_info_dict[section] = {}
      for option in dns_server_info.options(section):
        value = dns_server_info.get(section, option)
        if( value.lower() == 'true' ):
          server_info_dict[section][option] = True
        elif( value.lower() == 'false' ):
          server_info_dict[section][option] = False
        else:
          server_info_dict[section][option] = value

    return server_info_dict

  def WriteDnsServerInfo(self, server_info_dict):
    """Writes the information about a DNS server to the dns_server.info file.

    Inputs:
      server_info_dict: dict of the DNS server's information
                        Example:
                          {'server_info': {
                              'server_name': 'university.lcl',
                              'server_user': 'user',
                              'bind_dir': '/etc/bind/',
                              'test_dir': '/etc/bind/test/',
                              'bind_version': 'UNKNOWN'},
                           'tools': {
                              'tar': 'True'}}

    Raises:
      ExporterNoFileError: DNS tree does not exist or has not been
                           exported yet.
      ServerCheckError: DNS server server_name does not exist.
      ServerCheckError: Invalid DNS server information supplied.
    """
    if( 'server_info' not in server_info_dict or
        'server_name' not in server_info_dict['server_info'] or
        'server_user' not in server_info_dict['server_info'] or
        'bind_dir'    not in server_info_dict['server_info'] or
        'test_dir'    not in server_info_dict['server_info'] or
        'bind_version' not in server_info_dict['server_info'] ):
      raise ServerCheckError('Invalid DNS server information supplied.')
    dns_server = server_info_dict['server_info']['server_name']

    if( not os.path.exists(self.root_config_dir) ):
      raise ExporterNoFileError('DNS tree does not exist or has not been '
                                'exported yet.')
    if( not os.path.exists('%s/%s' % (self.root_config_dir, dns_server)) ):
      raise ServerCheckError('DNS server %s does not exist.' % dns_server)

    dns_server_info = ConfigParser.SafeConfigParser()
    for section in server_info_dict:
      dns_server_info.add_section(section)
      for option in server_info_dict[section]:
        if( server_info_dict[section][option] == True ):
          dns_server_info.set(section, option, 'true')
        elif( server_info_dict[section][option] == False ):
          dns_server_info.set(section, option, 'false')
        else:
          dns_server_info.set(section, option, 
                              server_info_dict[section][option])
    dns_server_info_file = open('%s/%s/%s.info' % (self.root_config_dir,
                                                  dns_server, dns_server), 'w')
    dns_server_info.write(dns_server_info_file)
    dns_server_info_file.close()
      
  def CheckDnsServer(self, dns_server, tools_check_list):
    """Checks a DNS server for connection, that necessary directories are
    created, that BIND is installed, and availability of tools.

    Inputs:
      dns_server: name of DNS server to check
      tools_check_list: list of tools to check

    Raises:
      ExporterFileError: Can not list files in /dir.
      ServerCheckError: DNS server 1.2.3.4 does not exist.
      ServerCheckError: DNS server metadata file incorrectly written or does
                        not exist.
      ServerCheckError: Can not connect to 1.2.3.4 via SSH.
      ServerCheckError: Unable to run 'named' on 1.2.3.4.  Is BIND installed
                        on the remote server?
      ServerCheckError: The remote test directory /etc/bind/test does not exist
                        or the user someone does not have permission.
      ServerCheckError: The remote BIND directory /etc/bind does not exist or
                        the user someone does not have permission.
    """
    for output in fabric_state.output:
      fabric_state.output[output] = False

    dns_server_data = {}
    try:
      dns_servers = os.listdir(self.root_config_dir)
    except OSError:
      raise ExporterListFileError('Can not list files in %s.' % 
                                  self.root_config_dir)
    if( dns_server not in dns_servers ):
      raise ServerCheckError('DNS server %s does not exist.' % dns_server)
    
    dns_server_info = self.GetDnsServerInfo(dns_server)
    ssh_host = '%s@%s:22' % (dns_server_info['server_info']['server_user'],
                             dns_server_info['server_info']['server_name'])
    try:
      fabric_api.env.warn_only = False

      # Testing for server connection through SSH
      fabric_api.env.host_string = ssh_host
      test_return = fabric_api.run('echo "Test"')
      if( test_return != 'Test' ):
        raise ServerCheckError('Can not connect to %s via SSH.' % dns_server)
    
      fabric_api.env.warn_only = True

      # Testing for BIND installation
      result = fabric_api.run('named -v')
      if( 'command not found' in result ):
        raise ServerCheckError('Unable to run \'named\' on %s.  Is BIND '
                               'installed on the remote server?' % dns_server)
      dns_server_info['server_info']['bind_version'] = result.lstrip('BIND ')

      # Testing for directories
      result = fabric_api.run('ls %s' % 
                              dns_server_info['server_info']['bind_dir'])
      if( 'No such file or directory' in result ):
        raise ServerCheckError('The remote BIND directory %s does not exist '
            'or the user %s does not have permission.' % 
            (dns_server_info['server_info']['bind_dir'],
             dns_server_info['server_info']['server_user']))

      result = fabric_api.run('ls %s' % 
                              dns_server_info['server_info']['test_dir'])
      if( 'No such file or directory' in result ):
        raise ServerCheckError('The remote test directory %s does not exist '
            'or the user %s does not have permission.' % 
            (dns_server_info['server_info']['test_dir'], 
             dns_server_info['server_info']['server_user']))
    
      # Testing for tools
      if( 'tools' not in dns_server_info ):
        dns_server_info['tools'] = {}
      for tool in tools_check_list:
        if( tool not in self.ToolList ):
          raise errors.FunctionError('Provided tool %s is not in tool list.'
                                     % tool)
        result = fabric_api.run(tool)
        if( 'command not found' in result ):
          dns_server_info['tools'][tool] = False
        else:
          dns_server_info['tools'][tool] = True
      self.WriteDnsServerInfo(dns_server_info)
    except FabricNetworkError:
      raise ServerCheckError('Could not connect to %s via SSH.' % dns_server)
    except ConfigParser.Error:
      raise ServerCheckError('Can not write to %s info file.' % dns_server)
    finally:
      fabric_network.disconnect_all()

  def TarDnsBindFiles(self, dns_server):
    """Tars the BIND tree for a DNS server.
    
    Inputs:
      dns_server: name of dns_server
    """
    if( not os.path.exists(self.root_config_dir) ):
      raise ExporterNoFileError('DNS tree does not exist or has not been '
                                'exported yet.')
    if( not os.path.exists('%s/%s' % (self.root_config_dir, dns_server)) ):
      raise ServerCheckError('DNS server %s does not exist.' % dns_server)
    dns_tar_file = tarfile.open('%s/%s/%s.tar.bz2' % (self.root_config_dir,
        dns_server,dns_server), 'w:bz2')

    try:
      server_files = os.listdir('%s/%s' % (self.root_config_dir, dns_server))
      for server_file in server_files:
        if( os.path.isdir('%s/%s/%s' % (self.root_config_dir, dns_server, 
                                        server_file)) ):
          try:
            named_files = os.listdir('%s/%s/%s' % (self.root_config_dir,
                dns_server, server_file))
          except OSError:
            raise ExporterListFileError('Can not list files in %s/%s/%s.' %
                (self.root_config_dir, dns_server, server_file))
          for view in named_files:
            if( view == 'named.ca' ):
              self.__AddToTarFile__('%s/%s' % (server_file, view),
                  '%s/%s' % (self.root_config_dir, dns_server), dns_tar_file)
              continue
            try:
              view_files = os.listdir('%s/%s/%s/%s' % (self.root_config_dir,
                  dns_server, server_file, view))
            except OSError:
              raise ExporterListFileError('Invalid tree format, can not list '
                  'files in %s/%s/%s/%s.' % (self.root_config_dir, dns_server,
                                             server_file, view))
            for zone in view_files:
              self.__AddToTarFile__('%s/%s/%s' % (server_file,
                  view, zone), '%s/%s' % (self.root_config_dir, dns_server), 
                  dns_tar_file)
        else:
          self.__AddToTarFile__(server_file, '%s/%s' % ( 
              self.root_config_dir, dns_server), dns_tar_file)
    except ExporterFileError:
      dns_tar_file.close()
      os.remove('%s/%s/%s.tar.bz2' % (self.root_config_dir, dns_server, 
                                      dns_server))
      raise
    dns_tar_file.close()

  # There are 2 ways to get zones.  By reading the zone files, or by named.conf
  #   This uses the first.  Opens more files, but has less room for mistakes
  #   because there is less parsing that is done.
  def GetZoneList(self, dns_server):
    """Gets all of the zones from a BIND tree for a DNS server.

    Inputs:
      dns_server: name of a DNS server

    Outputs:
      dict: {'view1': {'zone1.lcl': 'zone.db', 'zone2'.lcl: 'zone.db'},
             'view2': {'zone3.lcl': 'zone.db', 'zone4.lcl': 'zone.db'}}
    """
    try:
      views = os.listdir('%s/%s/named/' % (self.root_config_dir, dns_server))
      zone_dict = {}
      for view in views:
        if( view == 'named.ca' ):
          continue
        if( view not in zone_dict ):
          zone_dict[view] = {}
        zone_files = os.listdir('%s/%s/named/%s' % (self.root_config_dir, 
                                               dns_server, view))
        for zone_file_name in zone_files:
          zone_file = open('%s/%s/named/%s/%s' % (self.root_config_dir, 
              dns_server, view, zone_file_name))
          zone_origin = ''
          for line in zone_file:
            if( 'ORIGIN' in line ):
              zone_origin = line.lstrip('$ORIGIN ').rstrip('.\n')
              break
          else:
            zone_file.close()
            raise errors.FunctionError('Invalid zone file format for %s.' % 
                                       zone_file_name)
          zone_file.close()
          zone_dict[view][zone_origin] = zone_file_name
    except OSError as err:
      raise ServerCheckError('Can not list files in %s.' % err.filename)
    return zone_dict

  def MergeOptionsDicts(self, global_options_dict, view_dict, zone_dict):
    """Merges the options of 3 dictionaries, according to precendence.
    zone_dict is the most importantce, while global_options_dict has the "least"
    importantance.
    
      Inputs:
        global_options_dict: dict of the options defined globally in named.conf
        view_dict: dict of the options defined in a single view of named.conf
        zone_dict: dict of the options defined in a single zone of named.conf

      Outputs:
        single_options_dict: dict of the merged options
    """

    single_options_dict = {}

    #Go in order of least important to most important
    for options_dict in [global_options_dict, view_dict, zone_dict]:
      for key in options_dict.keys():
        if( key in self.BIND_OPTION_CLAUSES ):
          single_options_dict[key] = options_dict[key]

    #If we didn't fill in any of the options, we want to fill in their defaults
    for key in self.BIND_OPTION_CLAUSES:
      if( key not in single_options_dict.keys() ):
        single_options_dict[key] = self.BIND_OPTION_CLAUSES[key]

    return single_options_dict

  def GenerateAdditionalNamedCheckzoneArgs(self, bind_options_dict):
    """Generates additional named-checkzone command line flags and arguments based
    on the BIND options supplied in bind_options_dict.
    
    Inputs:
      bind_options_dict: dict of BIND options parsed from named.conf
      
    Outputs:
      args: list of flags and their args.
    """
     
    args = []
    check_siblings = False

    for option_key, option_value in bind_options_dict.items():
      if( option_key != 'check-siblings' ):
        checkzone_arg = None
        if( option_value in self.COMMANDS_CONVERT_DICT[option_key] ):
          checkzone_arg = self.COMMANDS_CONVERT_DICT[option_key][option_value]
        else:
          #These checks are for global and view options
          #In some clauses, fail, warn, and ignore are not enough.
          #master/slave/response warn/fail/ignore is the correct syntax.
          if( 'fail' in option_value ):
            checkzone_arg = 'fail'
          elif( 'warn' in option_value ):
            checkzone_arg = 'warn'
          elif( 'ignore' in option_value ):
            checkzone_arg = 'ignore'
          else:
            print 'ERROR: Unknown option "%s %s"' % (option_key, option_value)
            sys.exit(1)

        self.CHECKZONE_ARGS_DICT[option_key]['arg'] = checkzone_arg
      else:
        if( option_value == 'yes' ):
          check_siblings = True

    #if we want to check siblings, and if we are checking integrity,
    #append '-sibling' to the -i arg of the CHECKZONE_ARGS_DICT
    if( check_siblings and 
        self.CHECKZONE_ARGS_DICT['check-integrity']['arg'] != 'none' ):
      self.CHECKZONE_ARGS_DICT['check-integrity']['arg'] = '%s-sibling' % (
        self.CHECKZONE_ARGS_DICT['check-integrity']['arg'])

    #Transferring everything from CHECKZONE_ARGS_DICT to args list
    for key in self.CHECKZONE_ARGS_DICT:
      flag = self.CHECKZONE_ARGS_DICT[key]['flag']
      arg = self.CHECKZONE_ARGS_DICT[key]['arg']

      args.extend([flag, arg])

    return args

  def GetNamedZoneToolArgs(self, dns_server, view, zone_file_name):
    """Generates the arg flags for named-checkzone and named-compilezone
    for a specific zone-view-server combination.
     
     Inputs:
       dns_server: name of a DNS server
       view: name of a view
       zone_file_name: the file name of a zone
     
     Outputs:
       string: string of the command flags and their values for named-checkzone
               and named-compilezone.
    """
    zone_name = zone_file_name.rstrip('.db')
    server_directory = '%s/%s' % (self.root_config_dir, dns_server)
    named_file_name = '%s/named.conf.a' % server_directory
    try:
      named_file_handle = open(named_file_name, 'r')
      named_file_string = named_file_handle.read()
    finally:
      named_file_handle.close()

    named_file_dict = iscpy.ParseISCString(named_file_string)
    global_options_dict = named_file_dict['options']

    if( 'view "%s"' % view not in named_file_dict ):
      raise ConfigManagerError('Could not find view %s in named.conf' % view)
    view_dict = named_file_dict['view "%s"' % view]
    
    zone_dict = None
    for zone in view_dict:
      #Making sure we're checking a dictionary
      if( type(view_dict[zone]) == type({}) ):
        if( 'file' in view_dict[zone].keys() ):
          if( view_dict[zone]['file'].strip('"').endswith(zone_file_name) ):
            zone_dict = view_dict[zone]
            break
    else:
      raise ConfigManagerError('Could not find zone %s in view %s within named.conf' % (zone_name, view))

    options_dict = self.MergeOptionsDicts(
        global_options_dict, view_dict, zone_dict)
    additional_args = self.GenerateAdditionalNamedCheckzoneArgs(options_dict)

    return ' '.join(additional_args)
