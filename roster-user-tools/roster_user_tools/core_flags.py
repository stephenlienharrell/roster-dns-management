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

"""Core flags lib, flags in all tools."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


from copy import deepcopy
import getpass
from optparse import OptionParser
from roster_user_tools import cli_common_lib

class FlagsError(Exception):
  pass

class CoreFlags:
  """Command line common library"""
  def __init__(self, command, commands, args, usage, bootstrapper=False):
    """Initializes parser, sets flags for all classes"""
    self.parser = OptionParser(version='%%prog (Roster %s)' % __version__,
                               usage=usage)
    self.bootstrapper = bootstrapper
    self.args = args
    self.command = command
    self.SetCommands(commands)
    if( self.command and self.command not in self.functions_dict ):
      cli_common_lib.DnsError(
          'This tool does not have a %s command.' % self.command, 1)
    self.SetCoreFlags()
    self.SetActionFlags()
    self.SetDataFlags()
    if( hasattr(self, 'SetToolFlags') ):
      self.SetToolFlags()

    ## Organize flags into dict {'flag_name': '-f/--flag-name'}
    self.avail_flags = {}
    for flag in self.parser.option_list[2:]:
      self.avail_flags[flag.dest] = flag

    self.options = self.parser.parse_args(self.args)[0]
    self.CheckDataFlags()

  def SetCoreFlags(self):
    """Sets core flags for parser"""
    if( not self.bootstrapper ):
      self.parser.add_option(
          '-u', '--username', action='store', dest='username',
          help='Run as different username.', metavar='<username>',
          default=unicode(getpass.getuser()))
      self.SetAllFlagRule('username', required=False)
      self.parser.add_option(
          '-p', '--password', action='store', dest='password',
          help='Password string, NOTE: It is insecure to use this '
               'flag on the command line.', metavar='<password>', default=None)
      self.SetAllFlagRule('password', required=False)
      self.parser.add_option(
          '--cred-string', action='store', dest='credstring',
          help='String of credential.', metavar='<cred-string>', default=None)
      self.SetAllFlagRule('credstring', required=False)

    self.parser.add_option(
        '-s', '--server', action='store', dest='server',
        help='XML RPC Server URL.', metavar='<server>', default=None)
    self.SetAllFlagRule('server', required=False)
    self.parser.add_option(
        '-c', '--cred-file', action='store', dest='credfile',
        help='Location of credential file.', metavar='<cred-file>',
        default=cli_common_lib.DEFAULT_CRED_FILE)
    self.SetAllFlagRule('credfile', required=False)
    self.parser.add_option(
        '--config-file', action='store', dest='config_file',
        help='Config file location.', metavar='<file>', default=None)
    self.SetAllFlagRule('config_file', required=False)

  def CheckDataFlags(self):
    """Returns the action the tool should perform

    Inputs:
      function: string of function, must be in functions
      functions: dictionary of uses from tool

    Outputs:
      string: string from uses keys of correct action
    """
    if( not self.command ):
      cli_common_lib.DnsError('A command must be specified.', 1)
      ## Possilby print help
    elif( self.command and self.command not in self.functions_dict ):
      cli_common_lib.DnsError(
          'This tool does not have a %s command.' % self.command, 1)
      ## Possilby print help

    ## Find used flags {'flag_name': 'flag_value'}
    used_flags = {}
    for flag in self.parser.option_list[2:]:
      option_var = eval('self.options.%s' % flag.dest)
      if( option_var != self.parser.defaults[flag.dest] ):
        used_flags[flag.dest] = option_var

    ## Find irrelevant flags
    for used_flag in used_flags:
      found = False
      for flag_type in self.functions_dict[self.command]:
        if( flag_type in ['dependent_args', 'independent_args'] ):
          for group in self.functions_dict[self.command][flag_type]:
            if( used_flag in group ):
              found = True
        if( used_flag in self.functions_dict[self.command][flag_type] ):
          found = True
      if( not found ):
        cli_common_lib.DnsError(
            'The %s flag cannot be used with the %s command.' % (
                self.avail_flags[used_flag], self.command), 1)

    ## Check if all required arguments are used
    for flag in self.functions_dict[self.command]['args']:
      if( flag not in used_flags and self.functions_dict[self.command]['args'][
            flag] ):
        cli_common_lib.DnsError(
            'The %s flag is required.' % (self.avail_flags[flag]), 1)
        ## Possilby print help

    ## Check independent arguments
    for flags in self.functions_dict[self.command]['independent_args']:
      if( len(flags) == 0 ):
        continue
      flags_real = [] # Real flags strings like -a/--acl
      for flag in flags:
        flags_real.append(str(self.avail_flags[flag]))
      independent_flags = 0 
      for flag in flags:
        if( flag in used_flags ):
          independent_flags += 1
        if( independent_flags > 1 ):
          cli_common_lib.DnsError('%s cannot be used simultaneously.' % ( 
              ' and '.join(sorted(flags_real))), 1)
      if( independent_flags == 0 and flags[flag] ):
        cli_common_lib.DnsError('Either %s must be used.' % ( 
            ' or '.join(sorted(flags_real))), 1)

    ## Check dependent arguments
    used = 0
    unused = 0
    for flags in self.functions_dict[self.command]['dependent_args']:
      if( len(flags) == 0 ):
        continue
      flags_real = [] # Real flags strings like -a/--acl
      for flag in flags:
        flags_real.append(str(self.avail_flags[flag]))
      for flag in flags:
        if( flag in used_flags ):
          used += 1
        else:
          unused += 1
      if( used != 0 and unused != 0 ):
        cli_common_lib.DnsError('%s must be used together.' % (
          ' and '.join(sorted(flags_real))), 1)

  def SetCommands(self, functions):
    """Sets self.functions_dict according to functions list

    Inputs:
      functions: list of strings of functions

      Sets the self.functions_dict
      ex:
        {'list': {'args': {}, 'forbidden_args':{}, 'independent_args': [],
                  'dependent_args': []},
        {'remove': {'args': {}, 'forbidden_args':{}, 'independent_args': [],
                    'dependent_args': []}}

      The list portion of the dictionary may be populated as shown below:

        {'list': {'args': {'user': True, 'verbose': False},
                  'forbidden_args': {'make_all': False},
                  'independent_args': [{'allow': False, 'deny': False},
                                       {'quiet': False, 'verbose': False}],
                  'dependent_args': [{'allow': False, 'allow_level': True}]}}

      Where 'user' is a required argument. The value represents whether or not
      the argument is required: True/False. Note 'user' is the name given in
      optparse, NOT the flag '-u/--user'. Verbose is not a required argument,
      but is listed in args and should be in case of any code changes. All
      args should be represented in portions of this dictionary. If 'user'
      is not supplied, the function will exit with error. 'make_all' is a
      forbidden argument. If it is used in this certain portion of a function,
      the user is probably mistaking what is happening with the command and
      the function will exit with error. Independent args must not be given
      simultaneously otherwise the function will exit with error. If these args
      are required, it will exit with error if one or the other is not
      specified. Dependent args are arguments that depend on each other,
      the function will error out if both are not supplied simultaneously.
    """
    self.functions_dict = {} # Reset if not empty
    functions_dict = {'args': {}, 'forbidden_args': {},
                           'independent_args': [], 'dependent_args': []}
    for function in functions:
      self.functions_dict[function] = deepcopy(functions_dict)

  def SetDefaultFlags(self):
    """Sets all availible default flags to not required
       
       for use with one command functions such as list functions
    """
    for flag in self.parser.defaults:
      self.AddFlagRule(flag, required=False)

  def AddFlagRule(self, flag_name, command=None, required=True,
                  flag_type='args'):
    """Adds a key to functions dict

    Inputs:
      flag_name: string of flag name
      command: string of command (defaults to self.command)
      required: boolean of required flag (defaults to true)
      flag_type: type of flag (defaults to 'args')
    """
    if( command is None and self.command is None):
      return
    if( command is None):
      command = self.command

    if( flag_type in ['independent_args', 'dependent_args']
        and type(flag_name) == tuple ):
      new_dict = {}
      for flag_n in flag_name:
        new_dict[flag_n] = required
      self.functions_dict[command][flag_type].append(new_dict)

    elif( type(flag_name) == str ):
      self.functions_dict[command][flag_type][flag_name] = required

    else:
      raise FlagsError('flag_name type and flag_type mismatch.')

  def SetAllFlagRule(self, flag_name, required=True, flag_type='args'):
    """Adds a key to all args portions of functions dicts

    Inputs:
      flag_name: string of optparse flag name
      required: boolean of required flag (defaults to True)
      flag_type: type of flag (defaults to 'args')
    """
    for command in self.functions_dict:
      self.AddFlagRule(flag_name, command=command, required=required,
                       flag_type=flag_type)
