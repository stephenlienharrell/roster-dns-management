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
         "  -q, --quiet           Suppress program output.\n"
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
         "  -q, --quiet           Suppress program output.\n"
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

  def testListRecordArgs(self):
    usage = "test usage"

    args_instance = ListRecordArgs(usage)
    
    args_instance.parser.set_default('username', USERNAME)
    self.assertEqual(args_instance.parser.get_default_values(),
        {'soa': False, 'soa_expiry_seconds': None, 'soa_admin_email': None,
         'aaaa': False, 'credstring': None, 'mx_priority': None, 'ttl': 3600,
         'zone_name': None, 'srv_priority': None, 'txt': False, 'ptr': False,
         'hinfo_hardware': None, 'a_assignment_ip': None,
         'aaaa_assignment_ip': None, 'hinfo_os': None,
         'ptr_assignment_host': None, 'soa_retry_seconds': None,
         'hinfo': False, 'srv_port': None, 'ns_name_server': None,
         'username': u'sharrell', 'credfile': None,
         'soa_minimum_seconds': None, 'config_file': None, 'no_header': False,
         'srv_assignment_host': None, 'password': None, 'mx_mail_server': None,
         'soa_serial_number': None, 'a': False, 'ns': False, 'target': None,
         'cname_assignment_host': None, 'txt_quoted_text': None,
         'soa_refresh_seconds': None, 'server': None, 'view_name': 'any',
         'cname': False, 'srv': False, 'srv_weight': None,
         'soa_name_server': None, 'mx': False})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    args_instance.parser.print_help()
    self.assertEqual(sys.stdout.flush(),
         'Usage: test usage\n'
         '\n'
         'Options:\n'
         '  --version             show program\'s version number and exit\n'
         '  -h, --help            show this help message and exit\n'
         '  --a                   Set the record type to A record.\n'
         '  --a-assignment-ip=<assignment-ip>\n'
         '                        String of the IPv4 address\n'
         '  --aaaa                Set the record type to AAAA record.\n'
         '  --aaaa-assignment-ip=<assignment-ip>\n'
         '                        String of the IPv6 address.\n'
         '  --hinfo               Set the record type to HINFO record.\n'
         '  --hinfo-hardware=<hardware>\n'
         '                        String of the hardware type.\n'
         '  --hinfo-os=<os>       String of the OS type.\n'
         '  --txt                 Set the record type to TXT record.\n'
         '  --txt-quoted-text=<quoted-text>\n'
         '                        String of quoted text.\n'
         '  --cname               Set the record type to CNAME record.\n'
         '  --cname-assignment-host=<hostname>\n'
         '                        String of the CNAME hostname.\n'
         '  --soa                 Set the record type to SOA record.\n'
         '  --soa-name-server=<name-server>\n'
         '                        String of the hostname of the SOA name '
         'server.\n'
         '  --soa-admin-email=<name-server>\n'
         '                        String of the admin email address.\n'
         '  --soa-serial-number=<serial-number>\n'
         '                        String of the serial number.\n'
         '  --soa-refresh-seconds=<refresh-seconds>\n'
         '                        Number of seconds to refresh.\n'
         '  --soa-retry-seconds=<retry-seconds>\n'
         '                        Number of seconds to retry.\n'
         '  --soa-expiry-seconds=<expiry-seconds>\n'
         '                        Number of seconds to expire.\n'
         '  --soa-minimum-seconds=<minumum-seconds>\n'
         '                        Minium number of seconds to refresh.\n'
         '  --srv                 Set the record type to SRV record.\n'
         '  --srv-priority=<priority>\n'
         '                        Integerof priority between 0-65535.\n'
         '  --srv-weight=<weight>\n'
         '                        Integer of weight between 0-65535.\n'
         '  --srv-port=<port>     Port number.\n'
         '  --srv-assignment-host=<hostname>\n'
         '                        String of the SRV assignment hostname.\n'
         '  --ns                  Set the record type to NS record.\n'
         '  --ns-name-server=<hostname>\n'
         '                        String of the hostname of the NS name '
         'server.\n'
         '  --mx                  Set the record type to MX record.\n'
         '  --mx-priority=<priority>\n'
         '                        Integer of priority between 0-65535.\n'
         '  --mx-mail-server=<hostname>\n'
         '                        String of mail server hostname.\n'
         '  --ptr                 Set the record type to PTR record.\n'
         '  --ptr-assignment-host=<hostname>\n'
         '                        String of PTR hostname.\n'
         '  -z <zone-name>, --zone-name=<zone-name>\n'
         '                        String of the <zone-name>. Example:\n'
         '                        "sub.university.edu"\n'
         '  -t <target>, --target=<target>\n'
         '                        String of the target. "A" record example:\n'
         '                        "machine-01", "PTR" record example: '
         '192.168.1.1\n'
         '  --ttl=<ttl>           Integer of time to live <ttl> per record.\n'
         '  -v <view-name>, --view-name=<view-name>\n'
         '                        String of the view name <view-name>. '
         'Example:\n'
         '                        "internal"\n'
         '  --no-header           Do not display a header.\n'
         '  -s <server>, --server=<server>\n'
         '                        XML RPC Server URL.\n'
         '  -u <username>, --username=<username>\n'
         '                        Run as different username.\n'
         '  -p <password>, --password=<password>\n'
         '                        Password string, NOTE: It is insecure to use '
         'this flag\n'
         '                        on the command line.\n'
         '  -c <cred-file>, --cred-file=<cred-file>\n'
         '                        Location of credential file.\n'
         '  --cred-string=<cred-string>\n'
         '                        String of credential.\n'
         '  --config-file=<file>  Config file location.\n')
    sys.stdout = oldstdout
    args = ['--a', 'test']
    options = args_instance.GetOptionsObject(args)
    self.assertEqual(set(dir(options)), set(
        ['soa', '__module__', '_update', '__str__', 'ttl', 'soa_admin_email',
         'aaaa', 'credstring', 'read_file', 'mx_priority', 'soa_expiry_seconds',
         'zone_name', 'srv_priority', 'txt', 'ptr', '_update_careful',
         'hinfo_hardware', '_update_loose', 'ensure_value',
         'aaaa_assignment_ip', '__cmp__', 'hinfo_os', 'ptr_assignment_host',
         '__init__', 'soa_retry_seconds', 'read_module', 'hinfo', 'ns',
         '__doc__', 'ns_name_server', 'username', 'credfile',
         'soa_minimum_seconds', 'config_file', 'a_assignment_ip', 'srv_weight',
         'srv_assignment_host', 'password', 'mx_mail_server',
         'soa_serial_number', 'a', 'soa_refresh_seconds', 'srv_port', 'target',
         'cname_assignment_host', 'txt_quoted_text', 'no_header', 'server',
         'view_name', 'cname', 'srv', '__repr__', 'soa_name_server', 'mx']))
    self.assertEqual(options.username, USERNAME)
    self.assertEqual(options.server, None)

  def testMakeRecordArgs(self):
    usage = "test usage"

    args_instance = MakeRecordArgs(usage)
    
    args_instance.parser.set_default('username', USERNAME)
    self.assertEqual(args_instance.parser.get_default_values(),
        {'soa': False, 'soa_expiry_seconds': None, 'soa_admin_email': None,
         'aaaa': False, 'credstring': None, 'mx_priority': None, 'ttl': 3600,
         'zone_name': None, 'srv_priority': None, 'txt': False, 'ptr': False,
         'hinfo_hardware': None, 'a_assignment_ip': None,
         'aaaa_assignment_ip': None, 'hinfo_os': None,
         'ptr_assignment_host': None, 'soa_retry_seconds': None,
         'hinfo': False, 'srv_port': None, 'ns_name_server': None,
         'username': u'sharrell', 'credfile': None, 'soa_minimum_seconds': None,
         'config_file': None, 'soa_name_server': None,
         'srv_assignment_host': None, 'password': None, 'mx_mail_server': None,
         'soa_serial_number': None, 'a': False, 'ns': False, 'target': None,
         'cname_assignment_host': None, 'txt_quoted_text': None, 'quiet': False,
         'soa_refresh_seconds': None, 'server': None, 'view_name': 'any',
         'cname': False, 'srv': False, 'srv_weight': None, 'mx': False})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    args_instance.parser.print_help()
    self.assertEqual(sys.stdout.flush(),
        'Usage: test usage\n'
        '\n'
        'Options:\n'
        '  --version             show program\'s version number and exit\n'
        '  -h, --help            show this help message and exit\n'
        '  --a                   Set the record type to A record.\n'
        '  --a-assignment-ip=<assignment-ip>\n'
        '                        String of the IPv4 address\n'
        '  --aaaa                Set the record type to AAAA record.\n'
        '  --aaaa-assignment-ip=<assignment-ip>\n'
        '                        String of the IPv6 address.\n'
        '  --hinfo               Set the record type to HINFO record.\n'
        '  --hinfo-hardware=<hardware>\n'
        '                        String of the hardware type.\n'
        '  --hinfo-os=<os>       String of the OS type.\n'
        '  --txt                 Set the record type to TXT record.\n'
        '  --txt-quoted-text=<quoted-text>\n'
        '                        String of quoted text.\n'
        '  --cname               Set the record type to CNAME record.\n'
        '  --cname-assignment-host=<hostname>\n'
        '                        String of the CNAME hostname.\n'
        '  --soa                 Set the record type to SOA record.\n'
        '  --soa-name-server=<name-server>\n'
        '                        String of the hostname of the SOA name server.\n'
        '  --soa-admin-email=<name-server>\n'
        '                        String of the admin email address.\n'
        '  --soa-serial-number=<serial-number>\n'
        '                        String of the serial number.\n'
        '  --soa-refresh-seconds=<refresh-seconds>\n'
        '                        Number of seconds to refresh.\n'
        '  --soa-retry-seconds=<retry-seconds>\n'
        '                        Number of seconds to retry.\n'
        '  --soa-expiry-seconds=<expiry-seconds>\n'
        '                        Number of seconds to expire.\n'
        '  --soa-minimum-seconds=<minumum-seconds>\n'
        '                        Minium number of seconds to refresh.\n'
        '  --srv                 Set the record type to SRV record.\n'
        '  --srv-priority=<priority>\n'
        '                        Integerof priority between 0-65535.\n'
        '  --srv-weight=<weight>\n'
        '                        Integer of weight between 0-65535.\n'
        '  --srv-port=<port>     Port number.\n'
        '  --srv-assignment-host=<hostname>\n'
        '                        String of the SRV assignment hostname.\n'
        '  --ns                  Set the record type to NS record.\n'
        '  --ns-name-server=<hostname>\n'
        '                        String of the hostname of the NS name server.\n'
        '  --mx                  Set the record type to MX record.\n'
        '  --mx-priority=<priority>\n'
        '                        Integer of priority between 0-65535.\n'
        '  --mx-mail-server=<hostname>\n'
        '                        String of mail server hostname.\n'
        '  --ptr                 Set the record type to PTR record.\n'
        '  --ptr-assignment-host=<hostname>\n'
        '                        String of PTR hostname.\n'
        '  -z <zone-name>, --zone-name=<zone-name>\n'
        '                        String of the <zone-name>. Example:\n'
        '                        "sub.university.edu"\n'
        '  -t <target>, --target=<target>\n'
        '                        String of the target. "A" record example:\n'
        '                        "machine-01", "PTR" record example: 192.168.1.1\n'
        '  --ttl=<ttl>           Integer of time to live <ttl> per record.\n'
        '  -v <view-name>, --view-name=<view-name>\n'
        '                        String of the view name <view-name>. Example:\n'
        '                        "internal"\n'
        '  -q, --quiet           Suppress program output.\n'
        '  -s <server>, --server=<server>\n'
        '                        XML RPC Server URL.\n'
        '  -u <username>, --username=<username>\n'
        '                        Run as different username.\n'
        '  -p <password>, --password=<password>\n'
        '                        Password string, NOTE: It is insecure to use this flag\n'
        '                        on the command line.\n'
        '  -c <cred-file>, --cred-file=<cred-file>\n'
        '                        Location of credential file.\n'
        '  --cred-string=<cred-string>\n'
        '                        String of credential.\n'
        '  --config-file=<file>  Config file location.\n')
    sys.stdout = oldstdout
    args = ['--a', 'test']
    options = args_instance.GetOptionsObject(args)
    self.assertEqual(set(dir(options)), set(
        ['soa', '__module__', '_update', '__str__', 'ttl', 'soa_admin_email',
         'aaaa', 'credstring', 'read_file', 'mx_priority', 'soa_expiry_seconds',
         'zone_name', 'srv_priority', 'txt', 'ptr', '_update_careful',
         'hinfo_hardware', '_update_loose', 'ensure_value',
         'aaaa_assignment_ip', '__cmp__', 'hinfo_os', 'ptr_assignment_host',
         '__init__', 'soa_retry_seconds', 'read_module', 'hinfo', 'ns',
         '__doc__', 'ns_name_server', 'username', 'credfile',
         'soa_minimum_seconds', 'config_file', 'a_assignment_ip', 'srv_weight',
         'srv_assignment_host', 'password', 'mx_mail_server',
         'soa_serial_number', 'a', 'srv_port', 'target',
         'cname_assignment_host', 'txt_quoted_text', 'quiet',
         'soa_refresh_seconds', 'server', 'view_name', 'cname', 'srv',
         '__repr__', 'soa_name_server', 'mx']))
    self.assertEqual(options.username, USERNAME)
    self.assertEqual(options.server, None)

  def testRemoveRecordArgs(self):
    usage = "test usage"

    args_instance = RemoveRecordArgs(usage)
    
    args_instance.parser.set_default('username', USERNAME)
    self.assertEqual(args_instance.parser.get_default_values(),
        {'soa': False, 'force': False, 'soa_expiry_seconds': None,
         'soa_admin_email': None, 'aaaa': False, 'credstring': None,
         'mx_priority': None, 'ttl': 3600, 'zone_name': None,
         'srv_priority': None, 'txt': False, 'ptr': False,
         'hinfo_hardware': None, 'a_assignment_ip': None,
         'aaaa_assignment_ip': None, 'hinfo_os': None,
         'ptr_assignment_host': None, 'soa_retry_seconds': None, 'hinfo': False,
         'srv_port': None, 'ns_name_server': None, 'username': u'sharrell',
         'credfile': None, 'soa_minimum_seconds': None, 'config_file': None,
         'soa_name_server': None, 'srv_assignment_host': None, 'password': None,
         'mx_mail_server': None, 'soa_serial_number': None, 'a': False,
         'ns': False, 'target': None, 'cname_assignment_host': None,
         'txt_quoted_text': None, 'quiet': False,
         'soa_refresh_seconds': None, 'server': None, 'view_name': 'any',
         'cname': False, 'srv': False, 'srv_weight': None, 'mx': False})
    self.assertEqual(args_instance.parser.get_usage(),
        'Usage: test usage\n')
    oldstdout = sys.stdout
    sys.stdout = StdOutStream()
    args_instance.parser.print_help()
    self.assertEqual(sys.stdout.flush(),
        'Usage: test usage\n'
        '\n'
        'Options:\n'
        '  --version             show program\'s version number and exit\n'
        '  -h, --help            show this help message and exit\n'
        '  --a                   Set the record type to A record.\n'
        '  --a-assignment-ip=<assignment-ip>\n'
        '                        String of the IPv4 address\n'
        '  --aaaa                Set the record type to AAAA record.\n'
        '  --aaaa-assignment-ip=<assignment-ip>\n'
        '                        String of the IPv6 address.\n'
        '  --hinfo               Set the record type to HINFO record.\n'
        '  --hinfo-hardware=<hardware>\n'
        '                        String of the hardware type.\n'
        '  --hinfo-os=<os>       String of the OS type.\n'
        '  --txt                 Set the record type to TXT record.\n'
        '  --txt-quoted-text=<quoted-text>\n'
        '                        String of quoted text.\n'
        '  --cname               Set the record type to CNAME record.\n'
        '  --cname-assignment-host=<hostname>\n'
        '                        String of the CNAME hostname.\n'
        '  --soa                 Set the record type to SOA record.\n'
        '  --soa-name-server=<name-server>\n'
        '                        String of the hostname of the SOA name '
        'server.\n'
        '  --soa-admin-email=<name-server>\n'
        '                        String of the admin email address.\n'
        '  --soa-serial-number=<serial-number>\n'
        '                        String of the serial number.\n'
        '  --soa-refresh-seconds=<refresh-seconds>\n'
        '                        Number of seconds to refresh.\n'
        '  --soa-retry-seconds=<retry-seconds>\n'
        '                        Number of seconds to retry.\n'
        '  --soa-expiry-seconds=<expiry-seconds>\n'
        '                        Number of seconds to expire.\n'
        '  --soa-minimum-seconds=<minumum-seconds>\n'
        '                        Minium number of seconds to refresh.\n'
        '  --srv                 Set the record type to SRV record.\n'
        '  --srv-priority=<priority>\n'
        '                        Integerof priority between 0-65535.\n'
        '  --srv-weight=<weight>\n'
        '                        Integer of weight between 0-65535.\n'
        '  --srv-port=<port>     Port number.\n'
        '  --srv-assignment-host=<hostname>\n'
        '                        String of the SRV assignment hostname.\n'
        '  --ns                  Set the record type to NS record.\n'
        '  --ns-name-server=<hostname>\n'
        '                        String of the hostname of the NS name '
        'server.\n'
        '  --mx                  Set the record type to MX record.\n'
        '  --mx-priority=<priority>\n'
        '                        Integer of priority between 0-65535.\n'
        '  --mx-mail-server=<hostname>\n'
        '                        String of mail server hostname.\n'
        '  --ptr                 Set the record type to PTR record.\n'
        '  --ptr-assignment-host=<hostname>\n'
        '                        String of PTR hostname.\n'
        '  -z <zone-name>, --zone-name=<zone-name>\n'
        '                        String of the <zone-name>. Example:\n'
        '                        "sub.university.edu"\n'
        '  -t <target>, --target=<target>\n'
        '                        String of the target. "A" record example:\n'
        '                        "machine-01", "PTR" record example: '
        '192.168.1.1\n'
        '  --ttl=<ttl>           Integer of time to live <ttl> per record.\n'
        '  -v <view-name>, --view-name=<view-name>\n'
        '                        String of the view name <view-name>. '
        'Example:\n'
        '                        "internal"\n'
        '  -q, --quiet           Suppress program output.\n'
        '  --force               Force actions to complete.\n'
        '  -s <server>, --server=<server>\n'
        '                        XML RPC Server URL.\n'
        '  -u <username>, --username=<username>\n'
        '                        Run as different username.\n'
        '  -p <password>, --password=<password>\n'
        '                        Password string, NOTE: It is insecure to use '
        'this flag\n'
        '                        on the command line.\n'
        '  -c <cred-file>, --cred-file=<cred-file>\n'
        '                        Location of credential file.\n'
        '  --cred-string=<cred-string>\n'
        '                        String of credential.\n'
        '  --config-file=<file>  Config file location.\n')
    sys.stdout = oldstdout
    args = ['--a', 'test']
    options = args_instance.GetOptionsObject(args)
    self.assertEqual(set(dir(options)), set(
        ['soa', '__module__', '_update', 'force', '__str__', 'ttl',
         'soa_admin_email', 'aaaa', 'credstring', 'read_file', 'mx_priority',
         'soa_expiry_seconds', 'zone_name', 'srv_priority', 'txt', 'ptr',
         '_update_careful', 'hinfo_hardware', '_update_loose', 'ensure_value',
         'aaaa_assignment_ip', '__cmp__', 'hinfo_os', 'ptr_assignment_host',
         '__init__', 'soa_retry_seconds', 'read_module', 'hinfo', 'ns',
         '__doc__', 'ns_name_server', 'username', 'credfile',
         'soa_minimum_seconds', 'config_file', 'a_assignment_ip', 'srv_weight',
         'srv_assignment_host', 'password', 'mx_mail_server',
         'soa_serial_number', 'a', 'srv_port', 'target',
         'cname_assignment_host', 'txt_quoted_text', 'quiet',
         'soa_refresh_seconds', 'server', 'view_name', 'cname', 'srv',
         '__repr__', 'soa_name_server', 'mx']))
    self.assertEqual(options.username, USERNAME)
    self.assertEqual(options.server, None)

if( __name__ == '__main__' ):
      unittest.main()
