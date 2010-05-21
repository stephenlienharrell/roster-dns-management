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

"""Regression test for flags"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import datetime
import time
import unittest
import os
import sys

from roster_user_tools import data_flags
from roster_user_tools import action_flags


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
USERNAME = u'sharrell'


class StdOutStream():
    def __init__(self):
      self.stdout = []

    def write(self, text):
      self.stdout.append(text)

    def flush(self):
      std_array = self.stdout
      self.stdout = []
      return ''.join(std_array)

class ListAclArgs(action_flags.List, data_flags.Acl):
  pass

class MakeAclArgs(action_flags.Make, data_flags.Acl):
  pass

class RemoveAclArgs(action_flags.Remove, data_flags.Acl):
  pass


class ListRecordArgs(action_flags.List, data_flags.Record):
  pass

class MakeRecordArgs(action_flags.Make, data_flags.Record):
  pass

class RemoveRecordArgs(action_flags.Remove, data_flags.Record):
  pass


class TestCoreHelpers(unittest.TestCase):

  def setUp(self):
    pass

  def testListAclArgs(self):
    args = ['-a', 'test']
    usage = "test usage"

    args_instance = ListAclArgs('list', ['list'], args, usage)
    
    args_instance.parser.set_default('username', USERNAME)
    args_instance.options.username = USERNAME
    self.assertEqual(args_instance.parser.get_default_values(),
        {'username': 'sharrell', 'deny': None, 'config_file': None,
         'credfile': None, 'no_header': False, 'server': None,
         'credstring': None, 'allow': None, 'cidr_block': None,
         'password': None, 'acl': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    self.assertEqual(set(dir(args_instance.options)), set(
        ['__cmp__', '__doc__', '__init__', '__module__', '__repr__', '__str__',
         '_update', '_update_careful', '_update_loose', 'acl', 'allow',
         'cidr_block', 'config_file', 'credfile', 'credstring', 'deny',
         'ensure_value', 'no_header', 'password', 'read_file', 'read_module',
         'server', 'username']))
    self.assertEqual(args_instance.options.username, USERNAME)
    self.assertEqual(args_instance.options.server, None)

  def testMakeAclArgs(self):
    args = ['-a', 'test', '--cidr-block', 'test', '--allow']
    usage = "test usage"

    args_instance = MakeAclArgs('make', ['make'], args, usage)
    
    args_instance.parser.set_default('username', USERNAME)
    args_instance.options.username = USERNAME
    self.assertEqual(args_instance.parser.get_default_values(),
        {'username': u'sharrell', 'deny': None, 'config_file': None,
         'credfile': None, 'quiet': False, 'server': None,
         'credstring': None, 'allow': None, 'cidr_block': None,
         'password': None, 'acl': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    self.assertEqual(set(dir(args_instance.options)), set(
        ['__cmp__', '__doc__', '__init__', '__module__', '__repr__', '__str__',
         '_update', '_update_careful', '_update_loose', 'acl', 'allow',
         'cidr_block', 'config_file', 'credfile', 'credstring', 'deny',
         'ensure_value', 'password', 'quiet', 'read_file', 'read_module',
         'server', 'username']))
    self.assertEqual(args_instance.options.username, USERNAME)
    self.assertEqual(args_instance.options.server, None)

  def testRemoveAclArgs(self):
    args = ['-a', 'test']
    usage = "test usage"

    args_instance = RemoveAclArgs('remove', ['remove'], args, usage)
    
    args_instance.parser.set_default('username', USERNAME)
    args_instance.options.username = USERNAME
    self.assertEqual(args_instance.parser.get_default_values(),
        {'username': u'sharrell', 'deny': None, 'config_file': None,
          'credfile': None, 'quiet': False, 'force': False, 'server': None,
         'credstring': None, 'allow': None, 'cidr_block': None,
         'password': None, 'acl': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    self.assertEqual(set(dir(args_instance.options)), set(
        ['__cmp__', '__doc__', '__init__', '__module__', '__repr__', '__str__',
         '_update', '_update_careful', '_update_loose', 'acl', 'allow',
         'cidr_block', 'config_file', 'credfile', 'credstring', 'deny',
         'ensure_value', 'password', 'quiet', 'force', 'read_file',
         'read_module', 'server', 'username']))
    self.assertEqual(args_instance.options.username, USERNAME)
    self.assertEqual(args_instance.options.server, None)

  def testListRecordArgs(self):
    args = ['--assignment-ip', 'test', '-t', 'test', '-z', 'test']
    usage = "test usage"

    args_instance = ListRecordArgs('a',
        ['a', 'ptr', 'aaaa', 'cname', 'hinfo', 'txt', 'soa', 'srv', 'ns', 'mx',
         'all'],
        args, usage)
    
    args_instance.parser.set_default('username', USERNAME)
    args_instance.options.username = USERNAME
    self.assertEqual(args_instance.parser.get_default_values(),
        {'refresh_seconds': None, 'weight': None, 'minimum_seconds': None,
         'hardware': None, 'credstring': None, 'ttl': 3600, 'zone_name': None,
         'port': None, 'expiry_seconds': None, 'priority': None,
         'retry_seconds': None, 'serial_number': None, 'assignment_host': None,
         'username': u'sharrell', 'credfile': None, 'config_file': None,
         'name_server': None, 'quoted_text': None, 'password': None,
         'target': None, 'os': None, 'no_header': False, 'server': None,
         'view_name': 'any', 'mail_server': None, 'admin_email': None,
         'assignment_ip': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    self.assertEqual(set(dir(args_instance.options)), set(
        ['__module__', '_update', 'refresh_seconds', 'weight', '__str__',
         'minimum_seconds', 'hardware', 'credstring', 'read_file', 'ttl',
         'zone_name', 'port', '_update_careful', '_update_loose',
         'ensure_value', 'expiry_seconds', '__cmp__', 'priority',
         'retry_seconds', '__init__', 'read_module', 'serial_number',
         'assignment_host', '__doc__', 'username', 'credfile', 'config_file',
         'name_server', 'quoted_text', 'password', 'target', 'os', 'no_header',
         'server', 'view_name', '__repr__', 'mail_server', 'admin_email',
         'assignment_ip']))
    self.assertEqual(args_instance.options.username, USERNAME)
    self.assertEqual(args_instance.options.server, None)

  def testMakeRecordArgs(self):
    args = ['--assignment-ip', 'test', '-t', 'test', '-z', 'test']
    usage = "test usage"

    args_instance = MakeRecordArgs('a',
        ['a', 'ptr', 'aaaa', 'cname', 'hinfo', 'txt', 'soa', 'srv', 'ns', 'mx'],
        args, usage)
    
    args_instance.parser.set_default('username', USERNAME)
    args_instance.options.username = USERNAME
    self.assertEqual(args_instance.parser.get_default_values(),
        {'refresh_seconds': None, 'weight': None, 'minimum_seconds': None,
         'hardware': None, 'credstring': None, 'ttl': 3600, 'zone_name': None,
         'port': None, 'expiry_seconds': None, 'priority': None,
         'retry_seconds': None, 'serial_number': None, 'assignment_host': None,
         'username': u'sharrell', 'credfile': None, 'config_file': None,
         'name_server': None, 'quoted_text': None, 'password': None,
         'target': None, 'os': None, 'quiet': False, 'server': None,
         'view_name': 'any', 'mail_server': None, 'admin_email': None,
         'assignment_ip': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    self.assertEqual(set(dir(args_instance.options)), set(
        ['__module__', '_update', 'refresh_seconds', 'weight', '__str__',
         'minimum_seconds', 'hardware', 'credstring', 'read_file', 'ttl',
         'zone_name', 'port', '_update_careful', '_update_loose',
         'ensure_value', 'expiry_seconds', '__cmp__', 'priority',
         'retry_seconds', '__init__', 'read_module', 'serial_number',
         'assignment_host', '__doc__', 'username', 'credfile', 'config_file',
         'name_server', 'quoted_text', 'password', 'target', 'assignment_ip',
         'quiet', 'server', 'view_name', '__repr__', 'mail_server',
         'admin_email', 'os']))
    self.assertEqual(args_instance.options.username, USERNAME)
    self.assertEqual(args_instance.options.server, None)

  def testRemoveRecordArgs(self):
    args = ['--assignment-ip', 'test', '-t', 'test', '-z', 'test']
    usage = "test usage"

    args_instance = RemoveRecordArgs('a',
        ['a', 'ptr', 'aaaa', 'cname', 'hinfo', 'txt', 'soa', 'srv', 'ns', 'mx'],
        args, usage)
    
    args_instance.parser.set_default('username', USERNAME)
    args_instance.options.username = USERNAME
    self.assertEqual(args_instance.parser.get_default_values(),
        {'force': False, 'weight': None, 'minimum_seconds': None,
         'hardware': None, 'credstring': None, 'refresh_seconds': None,
         'ttl': 3600, 'zone_name': None, 'port': None, 'expiry_seconds': None,
         'priority': None, 'retry_seconds': None, 'serial_number': None,
         'assignment_host': None, 'username': u'sharrell', 'credfile': None,
         'config_file': None, 'name_server': None, 'quoted_text': None,
         'password': None, 'target': None, 'os': None, 'quiet': False,
         'server': None, 'view_name': 'any', 'mail_server': None,
         'admin_email': None, 'assignment_ip': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    self.assertEqual(set(dir(args_instance.options)), set(
        ['__module__', '_update', 'force', 'weight', '__str__',
         'minimum_seconds', 'hardware', 'credstring', 'read_file', 'ttl',
         'refresh_seconds', 'port', '_update_careful', '_update_loose',
         'ensure_value', 'expiry_seconds', '__cmp__', 'priority',
         'retry_seconds', '__init__', 'read_module', 'serial_number',
         'assignment_host', '__doc__', 'username', 'credfile', 'config_file',
         'name_server', 'quoted_text', 'password', 'zone_name', 'target', 'os',
         'quiet', 'server', 'view_name', '__repr__', 'mail_server',
         'admin_email', 'assignment_ip']))
    self.assertEqual(args_instance.options.username, USERNAME)
    self.assertEqual(args_instance.options.server, None)

  def testSetCommands(self):
    args = ['--assignment-ip', 'test', '-t', 'test', '-z', 'test']
    usage = "test usage"

    args_instance = RemoveRecordArgs('a',
        ['a', 'ptr', 'aaaa', 'cname', 'hinfo', 'txt', 'soa', 'srv', 'ns', 'mx'],
        args, usage)


    self.assertEqual(args_instance.functions_dict,
        {'a': {'independent_args': [],
               'args': {'username': False, 'credfile': False,
                        'config_file': False, 'target': True, 'quiet': False,
                        'server': False, 'credstring': False,
                        'view_name': False, 'ttl': False, 'zone_name': True,
                        'password': False, 'assignment_ip': True},
               'dependent_args': [], 'forbidden_args': {}},
         'soa': {'independent_args': [],
                 'args': {'refresh_seconds': True, 'expiry_seconds': True,
                          'name_server': True, 'ttl': False,
                          'minimum_seconds': True, 'retry_seconds': True,
                          'view_name': False, 'zone_name': True,
                          'serial_number': True, 'admin_email': True,
                          'target': True},
                 'dependent_args': [], 'forbidden_args': {}},
         'ns': {'independent_args': [],
                'args': {'zone_name': True, 'view_name': False, 'target': True,
                         'name_server': True, 'ttl': False},
                'dependent_args': [], 'forbidden_args': {}},
         'mx': {'independent_args': [],
                'args': {'target': True, 'priority': True, 'view_name': False,
                         'ttl': False, 'zone_name': True, 'mail_server': True},
                'dependent_args': [], 'forbidden_args': {}},
         'aaaa': {'independent_args': [],
                  'args': {'zone_name': True, 'view_name': False,
                           'assignment_ip': True, 'target': True, 'ttl': False},
                  'dependent_args': [], 'forbidden_args': {}},
         'cname': {'independent_args': [],
                   'args': {'zone_name': True, 'view_name': False,
                            'assignment_host': True, 'target': True,
                            'ttl': False},
                   'dependent_args': [], 'forbidden_args': {}},
         'srv': {'independent_args': [],
                 'args': {'target': True, 'weight': True, 'priority': True,
                          'view_name': False, 'ttl': False, 'zone_name': True,
                          'assignment_host': True, 'port': True},
                 'dependent_args': [], 'forbidden_args': {}},
         'hinfo': {'independent_args': [],
                   'args': {'target': True, 'hardware': True,
                            'view_name': False, 'ttl': False, 'zone_name': True,
                            'os': True},
                   'dependent_args': [], 'forbidden_args': {}},
         'txt': {'independent_args': [],
                 'args': {'quoted_text': True, 'view_name': False, 'ttl': False,
                          'target': True, 'zone_name': True},
                 'dependent_args': [], 'forbidden_args': {}},
         'ptr': {'independent_args': [],
                 'args': {'zone_name': True, 'view_name': False,
                          'assignment_host': True, 'target': True,
                          'ttl': False},
                 'dependent_args': [], 'forbidden_args': {}}})

  def testCheckDataFlags(self):
    usage = "test usage"
    args = ['-a', 'test', '--cidr-block', 'test', '--allow']
    args_instance = MakeAclArgs('make', ['make'], args, usage)

    args_instance.functions_dict['make']['args'] = {
        'acl': True, 'cidr_block': True}
    args_instance.functions_dict['make']['independent_args'] = [
        {'allow': True, 'deny': True}]
    args_instance.args = ['-a', 'test', '--allow']
    args_instance.options = args_instance.parser.parse_args(
        args_instance.args)[0]

    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    self.assertRaises(SystemExit, args_instance.CheckDataFlags)
    self.assertEqual(sys.stdout.flush(),
        'CLIENT ERROR: The --cidr-block flag is required.\n')
    sys.stdout = oldstdout

    args = ['-a', 'test', '--cidr-block', '192.168.1/24', '--allow']
    args_instance = MakeAclArgs('make', ['make'], args, usage)
    args_instance.functions_dict['make']['args'] = {'acl': True, 'cidr_block': True}
    args_instance.functions_dict['make']['independent_args'] = [{'allow': True, 'deny': True}]
    args_instance.args = ['-a', 'test', '--cidr-block', '192.168.1/24']
    args_instance.options = args_instance.parser.parse_args(
        args_instance.args)[0]

    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    self.assertRaises(SystemExit, args_instance.CheckDataFlags)
    self.assertEqual(sys.stdout.flush(),
        'CLIENT ERROR: Either --allow or --deny must be used.\n')
    sys.stdout = oldstdout

    args = ['-a', 'test', '--cidr-block', '192.168.1/24', '--allow']
    args_instance = MakeAclArgs('make', ['make'], args, usage)
    args_instance.functions_dict['make']['args'] = {'acl': True, 'cidr_block': True}
    args_instance.functions_dict['make']['independent_args'] = [{'allow': True, 'deny': True}]
    args_instance.args = ['-a', 'test', '--cidr-block', '192.168.1/24',\
                          '--allow', '--deny']
    args_instance.options = args_instance.parser.parse_args(
        args_instance.args)[0]

    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    self.assertRaises(SystemExit, args_instance.CheckDataFlags)
    self.assertEqual(sys.stdout.flush(),
        'CLIENT ERROR: --allow and --deny cannot be used simultaneously.\n')
    sys.stdout = oldstdout

    args = ['-a', 'test', '--cidr-block', '192.168.1/24', '--allow']
    args_instance = MakeAclArgs('make', ['make'], args, usage)
    args_instance.functions_dict['make']['args'] = {'acl': True, 'cidr_block': True}
    args_instance.functions_dict['make']['independent_args'] = [{'allow': True, 'deny': True}]

    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    args_instance.CheckDataFlags()
    self.assertEqual(sys.stdout.flush(), '')
    sys.stdout = oldstdout

    args_instance.functions_dict['make']['args'] = {'acl': True, 'cidr_block': True}
    args_instance.functions_dict['make']['dependent_args'] = [{'allow': True, 'deny': True}]

    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    self.assertRaises(SystemExit, args_instance.CheckDataFlags)
    self.assertEqual(sys.stdout.flush(),
        'CLIENT ERROR: --allow and --deny must be used together.\n')
    sys.stdout = oldstdout

    args_instance.functions_dict['make']['args'] = {'cidr_block': True}
    args_instance.functions_dict['make']['dependent_args'] = []
    args_instance.functions_dict['make']['independent_args'] = [{'allow': True, 'deny': True}]

    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    self.assertRaises(SystemExit, args_instance.CheckDataFlags)
    self.assertEqual(sys.stdout.flush(),
        'CLIENT ERROR: The -a/--acl flag cannot be used with the make '
        'command.\n')
    oldstdout = sys.stdout

  def testSetAll(self):
    usage = "test usage"
    args = ['-a', 'test', '--cidr-block', 'test', '--allow']
    args_instance = MakeAclArgs('make', ['make', 'list', 'remove'], args, usage)


    args_instance.SetAllFlagRule('zone_name')

    self.assertEqual(args_instance.functions_dict,
        {'make': {'independent_args': [{'deny': True, 'allow': True}],
                  'args': {'username': False, 'credfile': False,
                           'config_file': False, 'quiet': False,
                           'server': False, 'credstring': False,
                           'zone_name': True, 'cidr_block': True,
                           'password': False, 'acl': True},
                  'dependent_args': [], 'forbidden_args': {}},
         'list': {'independent_args': [], 'args': {'zone_name': True},
                  'dependent_args': [], 'forbidden_args': {}},
         'remove': {'independent_args': [], 'args': {'zone_name': True},
                    'dependent_args': [], 'forbidden_args': {}}})

if( __name__ == '__main__' ):
      unittest.main()