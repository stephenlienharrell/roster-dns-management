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

"""Common library for DNS management command line tools."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import ConfigParser
import sys
import os
import roster_client_lib

class ArgumentError(Exception):
  pass

class HostsError(Exception):
  pass


DEFAULT_CRED_FILE = '~/.dnscred'


class CliCommonLib:
  """Command line common library"""
  def __init__(self, options):
    """Retrieves configuration

    Inputs:
      options: Options object from optparse
    """
    self.options = options
    self.config_file = ConfigParser.SafeConfigParser()
    if( hasattr(options, 'config_file') and options.config_file is not None ):
      config_file = self.options.config_file
      self.config_file.read(config_file)
      if( hasattr(self.options, 'server') ):
        if( not self.options.server ):
          self.options.server = self.config_file.get('user_tools', 'server')
      if( hasattr(self.options, 'credfile') ):
        if( not options.credfile ):
          self.options.credfile = self.config_file.get('user_tools',
                                                       'cred_file')
    else:
      config_file = ''
      if( 'ROSTER_USER_CONFIG' in os.environ ):
        file_locations = [os.environ['ROSTER_USER_CONFIG']]
      else:
        file_locations = []
      file_locations.extend([os.path.expanduser('~/.rosterrc'),
                             '/etc/roster/roster_user_tools.conf'])
      for config_file in file_locations:
        if( os.path.exists(config_file) ):
          self.config_file.read(config_file)
          if( hasattr(self.options, 'server') ):
            if( not self.options.server ):
              self.options.server = self.config_file.get('user_tools', 'server')
          if( hasattr(self.options, 'credfile') ):
            if( not options.credfile ):
              self.options.credfile = self.config_file.get('user_tools',
                                                           'cred_file')
          break
      else:
        if( hasattr(self.options, 'server') ):
          if( not self.options.server ):
            raise ArgumentError('A server must be specified.')
        if( hasattr(self.options, 'credfile') ):
          if( not self.options.credfile ):
            self.options.credfile = os.path.expanduser(DEFAULT_CRED_FILE)

    roster_client_lib.CheckServerVersionMatch(self.options.server)
    roster_client_lib.CheckCredentials(
        self.options.username, self.options.credfile, self.options.server,
        password=self.options.password)

  def DisallowFlags(self, disallow_list, parser):
    """Dissallows certain command line flags.

    Inputs:
      disallow_list: list of command line flags to block
      parser: parser object from optparse
    """
    defaults = parser.defaults
    error = False
    for flag in parser.option_list[1:]:
      combo = 'self.options.%s' % flag.dest
      if( flag.dest in disallow_list ):
        if( eval(combo) != defaults[flag.dest] ):
          self.DnsError('The %s flag cannot be used.' % flag, 0)
          error = True
    if( error ):
      sys.exit(1)

  ## Function accessors, need to be removed at some point
def SortRecordsDict(records_dictionary, view_name):
  """Retries records from database and sorts them

  Inputs:
    records_dictionary: dictionary of records from core
    view_name: string of view name

  Outputs:
    dict: sorted dictionary of records
  """
  sorted_records = {}
  for ip_address in records_dictionary[view_name]:
    for record in records_dictionary[view_name][ip_address]:
      record['view'] = view_name
      if( ip_address not in sorted_records ):
        sorted_records[ip_address] = {'forward': [], 'reverse': []}
      if( record['forward'] ):
        sorted_records[ip_address]['forward'].append(record)
      else:
        sorted_records[ip_address]['reverse'].append(record)
  return sorted_records

def DnsError(message, exit_status=0):
  """Prints standardized client error message to screen.

  Inputs:
    message: string of message to be displayed on screen
    exit_status: integer of retrun code, assumed not exit if 0
  """
  print "CLIENT ERROR: %s" % message
  if( exit_status ):
    sys.exit(exit_status)

def ServerError(message, uuid_string, exit_status=0):
  """Prints standardized server error message to screen.

  Inputs:
    message: string of message to be displayed on screen
    exit_status: integer of retrun code, assumed not exit if 0
  """
  print "SERVER ERROR: (%s) %s" % (uuid_string, message)
  if( exit_status ):
    sys.exit(exit_status)

def UserError(message, exit_status=0):
  """Prints standardized user error message to screen.

  Inputs:
    message: string of message to be displayed on screen
    exit_status: integer of retrun code, assumed not exit if 0
  """
  print "USER ERROR: %s" % (message)
  if( exit_status ):
    sys.exit(exit_status)

def UnknownError(error_class, uuid_string, message, exit_status=0):
  """Prints standardized unknown error message to screen.

  Inputs:
    message: string of message to be displayed on screen
    exit_status: integer of retrun code, assumed not exit if 0
  """
  print "UNKNOWN ERROR(%s): (%s) %s" % (error_class, uuid_string,
                                        message)
  if( exit_status ):
    sys.exit(exit_status)


def DnsWarning(message):
  """Prints standardized warning message to screen.

  Inputs:
    message: string of message to be displayed on screen
  """
  print "WARNING: %s" % message

def PrintColumns(print_list, first_line_header=False):
  """Prints a table with aligned columns.

  Inputs:
    print_list: list of lists of columns
    file: string of filename
  """
  ## Construct zeros for lengths
  lengths = []
  if( print_list ):
    for column in print_list[0]:
      lengths.append(0)
  ## Get sizes of strings
  for row in print_list:
    for column_index, column in enumerate(row):
      if( len(str(column)) > lengths[column_index] ):
        lengths[column_index] = len(str(column))
  ## Construct string
  print_string_list = []
  for row in print_list:
    string_list = []
    string_args_list = []
    for column_index, column in enumerate(print_list[0]):
      string_list.append('%*s')
      string_args_list.extend([lengths[column_index] * -1, row[column_index]])
    print_line = ' '.join(string_list) % tuple(string_args_list)
    print_string_list.append('%s\n' % print_line.strip())
    if( first_line_header and (print_list.index(row) == 0) ):
      hyphen_list = []
      for _ in range(len(print_line.strip())):
        hyphen_list.append('-')
      print_string_list.append('%s\n' % ''.join(hyphen_list))
  return ''.join(print_string_list)

def PrintRecords(records_dictionary, ip_address_list=None, print_headers=True):
  """Prints records dictionary in a nice usable format.

  Inputs:
    records_dictionary: dictionary of records
    ip_address_list: list of ip_addresses to use
  """
  if ip_address_list is None:
    ip_address_list = []
  if( ip_address_list == [] ):
    for view in records_dictionary:
      ip_address_list.extend(records_dictionary[view].keys())
    ip_address_list = list(set(ip_address_list))

  print_list = []
  if( len(records_dictionary) == 0 ):
    for ip_address in ip_address_list:
      print_list.append([ip_address, '--', '--', '--', '--'])
  else:
    for view in records_dictionary:
      if( print_headers ):
        print_list.append(['View:', view, '', '', ''])
      for ip_address in ip_address_list:
        if( ip_address in records_dictionary[view] ):
          for record in records_dictionary[view][ip_address]:
            direction = 'Reverse'
            if( record['forward'] ):
              direction = 'Forward'
            print_list.append([ip_address, direction, record['host'],
                                    record['record_zone_name'], view])
        else:
          print_list.append([ip_address, '--', '--', '--', '--'])
  return PrintColumns(print_list)

def PrintHosts(records_dictionary, ip_address_list, view_name=None):
  """Prints hosts in an /etc/hosts format

  Inputs:
    records_dictionary: dictionary of records
    ip_address_list: list of ip_addresses
    view_name: string of view_name
  """
  print_list = []
  sorted_records = SortRecordsDict(records_dictionary, view_name)
  for ip_address in ip_address_list:
    if( ip_address not in sorted_records ):
      print_list.append(['#%s' % ip_address, '', '', ''])
      continue
    if( len(sorted_records[ip_address]['reverse']) > 1 ):
      raise HostsError(
          'Multiple reverse records found for %s' % (
              str(sorted_records[ip_address])))
    elif( len(sorted_records[ip_address]['reverse']) == 0 ):
      for record in sorted_records[ip_address]['forward']:
        forward_zone_origin = record['zone_origin'].rstrip('.')
        shorthost = record['host'].rsplit('.%s' % forward_zone_origin, 1)[0]
        longhost = record['host']
        if( longhost.startswith('@.') ):
          longhost = record['host'].lstrip('@.')
        print_list.append(['#%s' % ip_address, longhost,
                           shorthost, '# No reverse assignment'])
    else:
      reverse_record = sorted_records[ip_address]['reverse'][0]
      for record_number, record in enumerate(
          sorted_records[ip_address]['forward']):
        if( record['host'].replace('@.', '') ==
            reverse_record['host'].replace('@.', '') ):
          forward_zone_origin = record['zone_origin'].rstrip('.')
          shorthost = record['host'].rsplit('.%s' % forward_zone_origin, 1)[0]
          longhost = record['host']
          if( longhost.startswith('@.') ):
            longhost = record['host'].lstrip('@.')
          print_list.append([ip_address, longhost, shorthost, ''])
          sorted_records[ip_address]['forward'].pop(record_number)
          break
      else:
        print_list.append(['#%s' % ip_address, reverse_record['host'],
                           '', '# No forward assignment'])
      for record in sorted_records[ip_address]['forward']:
        forward_zone_origin = record['zone_origin'].rstrip('.')
        shorthost = record['host'].rsplit('.%s' % forward_zone_origin, 1)[0]
        longhost = record['host']
        if( longhost.startswith('@.') ):
          longhost = record['host'].lstrip('@.')
        print_list.append(['#%s' % ip_address, longhost,
                           shorthost, '# No reverse assignment'])
  return PrintColumns(print_list)

def EditFile(fname):
  """Opens a file in a text editor in the EDITOR env variable for editing

  Inputs:
    fname: string of filename
  Outputs:
    int: return code from editor
  """
  if( 'EDITOR' not in os.environ ):
    DnsError('EDITOR environment variable not set.', 1)
  closenum = os.system('%s %s' % (os.environ['EDITOR'], fname))

  if( closenum is None ):
    return_code = 0
  else:
    return_code = os.WEXITSTATUS(closenum)

  if( return_code != 0 ):
    DnsError('Error editing file.', 1)

  return return_code
