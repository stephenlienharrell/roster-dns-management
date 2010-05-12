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

"""Regression test for flags

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""


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


class TestCoreHelpers(unittest.TestCase):

  def setUp(self):
    pass

  def testListAclArgs(self):
    usage = "test usage"

    args_instance = ListAclArgs(usage)
    
    args_instance.parser.set_default('username', USERNAME)
    self.assertEqual(args_instance.parser.get_default_values(),
        {'username': 'sharrell', 'deny': None, 'config_file': None,
         'credfile': None, 'no_header': False, 'server': None,
         'credstring': None, 'allow': None, 'cidr_block': None,
         'password': None, 'acl': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    args_instance.parser.print_help()
    self.assertEqual(sys.stdout.flush(),
         "Usage: test usage\n\n"
         "Options:\n"
         "  --version             show program's version number and exit\n"
         "  -h, --help            show this help message and exit\n"
         "  -a ACL, --acl=ACL     ACL name\n"
         "  --cidr-block=CIDR_BLOCK\n"
         "                        Cidr block or single IP address.\n"
         "  --allow               Search for allowed ACLs.\n"
         "  --deny                Search for denied ACLs.\n"
         "  --no-header           Do not display a header.\n"
         "  -s <server>, --server=<server>\n"
         "                        XML RPC Server URL.\n"
         "  -u <username>, --username=<username>\n"
         "                        Run as different username.\n"
         "  -p <password>, --password=<password>\n"
         "                        Password string, NOTE: It is insecure to "
         "use this flag\n"
         "                        on the command line.\n"
         "  -c <cred-file>, --cred-file=<cred-file>\n"
         "                        Location of credential file.\n"
         "  --cred-string=<cred-string>\n"
         "                        String of credential.\n"
         "  --config-file=<file>  Config file location.\n")
    sys.stdout = oldstdout
    args = ['-a', 'test']
    options = args_instance.GetOptionsObject(args)
    self.assertEqual(set(dir(options)), set(
        ['__cmp__', '__doc__', '__init__', '__module__', '__repr__', '__str__',
         '_update', '_update_careful', '_update_loose', 'acl', 'allow',
         'cidr_block', 'config_file', 'credfile', 'credstring', 'deny',
         'ensure_value', 'no_header', 'password', 'read_file', 'read_module',
         'server', 'username']))
    self.assertEqual(options.username, USERNAME)
    self.assertEqual(options.server, None)

  def testMakeAclArgs(self):
    usage = "test usage"

    args_instance = MakeAclArgs(usage)
    
    args_instance.parser.set_default('username', USERNAME)
    self.assertEqual(args_instance.parser.get_default_values(),
        {'username': u'sharrell', 'deny': None, 'config_file': None,
         'credfile': None, 'quiet': False, 'server': None,
         'credstring': None, 'allow': None, 'cidr_block': None,
         'password': None, 'acl': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    args_instance.parser.print_help()
    self.assertEqual(sys.stdout.flush(),
         "Usage: test usage\n\n"
         "Options:\n"
         "  --version             show program's version number and exit\n"
         "  -h, --help            show this help message and exit\n"
         "  -a ACL, --acl=ACL     ACL name\n"
         "  --cidr-block=CIDR_BLOCK\n"
         "                        Cidr block or single IP address.\n"
         "  --allow               Search for allowed ACLs.\n"
         "  --deny                Search for denied ACLs.\n"
         "  --quiet               Suppress program output.\n"
         "  -s <server>, --server=<server>\n"
         "                        XML RPC Server URL.\n"
         "  -u <username>, --username=<username>\n"
         "                        Run as different username.\n"
         "  -p <password>, --password=<password>\n"
         "                        Password string, NOTE: It is insecure to use "
         "this flag\n"
         "                        on the command line.\n"
         "  -c <cred-file>, --cred-file=<cred-file>\n"
         "                        Location of credential file.\n"
         "  --cred-string=<cred-string>\n"
         "                        String of credential.\n"
         "  --config-file=<file>  Config file location.\n")
    sys.stdout = oldstdout
    args = ['-a', 'test']
    options = args_instance.GetOptionsObject(args)
    self.assertEqual(set(dir(options)), set(
        ['__cmp__', '__doc__', '__init__', '__module__', '__repr__', '__str__',
         '_update', '_update_careful', '_update_loose', 'acl', 'allow',
         'cidr_block', 'config_file', 'credfile', 'credstring', 'deny',
         'ensure_value', 'password', 'quiet', 'read_file', 'read_module',
         'server', 'username']))
    self.assertEqual(options.username, USERNAME)
    self.assertEqual(options.server, None)

  def testRemoveAclArgs(self):
    usage = "test usage"

    args_instance = RemoveAclArgs(usage)
    
    args_instance.parser.set_default('username', USERNAME)
    self.assertEqual(args_instance.parser.get_default_values(),
        {'username': u'sharrell', 'deny': None, 'config_file': None,
          'credfile': None, 'quiet': False, 'force': False, 'server': None,
         'credstring': None, 'allow': None, 'cidr_block': None,
         'password': None, 'acl': None})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    args_instance.parser.print_help()
    self.assertEqual(sys.stdout.flush(),
         "Usage: test usage\n\n"
         "Options:\n"
         "  --version             show program's version number and exit\n"
         "  -h, --help            show this help message and exit\n"
         "  -a ACL, --acl=ACL     ACL name\n"
         "  --cidr-block=CIDR_BLOCK\n"
         "                        Cidr block or single IP address.\n"
         "  --allow               Search for allowed ACLs.\n"
         "  --deny                Search for denied ACLs.\n"
         "  --quiet               Suppress program output.\n"
         "  --force               Force actions to complete.\n"
         "  -s <server>, --server=<server>\n"
         "                        XML RPC Server URL.\n"
         "  -u <username>, --username=<username>\n"
         "                        Run as different username.\n"
         "  -p <password>, --password=<password>\n"
         "                        Password string, NOTE: It is insecure to use "
         "this flag\n"
         "                        on the command line.\n"
         "  -c <cred-file>, --cred-file=<cred-file>\n"
         "                        Location of credential file.\n"
         "  --cred-string=<cred-string>\n"
         "                        String of credential.\n"
         "  --config-file=<file>  Config file location.\n")
    sys.stdout = oldstdout
    args = ['-a', 'test']
    options = args_instance.GetOptionsObject(args)
    self.assertEqual(set(dir(options)), set(
        ['__cmp__', '__doc__', '__init__', '__module__', '__repr__', '__str__',
         '_update', '_update_careful', '_update_loose', 'acl', 'allow',
         'cidr_block', 'config_file', 'credfile', 'credstring', 'deny',
         'ensure_value', 'password', 'quiet', 'force', 'read_file',
         'read_module', 'server', 'username']))
    self.assertEqual(options.username, USERNAME)
    self.assertEqual(options.server, None)

if( __name__ == '__main__' ):
      unittest.main()
