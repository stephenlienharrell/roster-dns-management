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

"""Data flags lib, flags for each group of tools."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


DEFAULT_TTL = 3600


import core_flags

class Acl(core_flags.CoreFlags):
  """Command line acl flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.data = 'Acl'
    not_list = self.action != 'List'

    self.parser.add_option('-a', '--acl', action='store', dest='acl',
                           help='String of access control list name.',
                           default=None)
    self.AddFlagRule('acl', required=not_list)
    self.parser.add_option('--cidr-block', action='store', dest='cidr_block',
                           help='String of CIDR block or single IP address.',
                           default=None)
    self.AddFlagRule('cidr_block', required=self.action=='Make')
    if( self.action == 'Remove' ):
      # Not required since tool handles the error
      self.AddFlagRule(('force', 'cidr_block'), flag_type='independent_args',
                       required=False)

    self.parser.add_option('--allow', action='store_true', dest='allow',
                           help='Allow CIDR block in ACL.', default=None)
    self.parser.add_option('--deny', action='store_true', dest='deny',
                           help='Deny CIDR block in ACL.', default=None)
    self.AddFlagRule(('allow', 'deny'), required=self.action=='Make',
                     flag_type='independent_args')


class Record(core_flags.CoreFlags):
  """Command line record flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.data = 'Record'
    not_list = self.action != 'List'

    self.parser.add_option(
        '--assignment-ip', action='store', dest='assignment_ip',
        help='(A, AAAA) String of the IP address', metavar='<assignment-ip>')
    self.AddFlagRule('assignment_ip', command='a', required=not_list)
    self.AddFlagRule('assignment_ip', command='aaaa', required=not_list)

    self.parser.add_option('--hardware', action='store',
                           dest='hardware', metavar='<hardware>',
                           help='(HINFO) String of the hardware type.')
    self.AddFlagRule('hardware', command='hinfo', required=not_list)
    self.parser.add_option('--os', action='store', dest='os',
                           help='(HINFO) String of the OS type.',
                           metavar='<os>')
    self.AddFlagRule('os', command='hinfo', required=not_list)

    self.parser.add_option('--quoted-text', action='store',
                           dest='quoted_text', metavar='<quoted-text>',
                           help='(TXT) String of quoted text.')
    self.AddFlagRule('quoted_text', command='txt', required=not_list)

    self.parser.add_option('--assignment-host', action='store',
                           dest='assignment_host', metavar='<hostname>',
                           help='(CNAME, PTR, SRV) String of the hostname.')
    self.AddFlagRule('assignment_host', command='cname', required=not_list)
    self.AddFlagRule('assignment_host', command='ptr', required=not_list)
    self.AddFlagRule('assignment_host', command='srv', required=not_list)

    self.parser.add_option('--name-server', action='store',
                           dest='name_server',
                           help='(SOA,NS) String of the hostname of the name '
                                'server.',
                           metavar='<name-server>')
    self.AddFlagRule('name_server', command='soa', required=not_list)
    self.AddFlagRule('name_server', command='ns', required=not_list)
    self.parser.add_option('--admin-email', action='store',
                           dest='admin_email',
                           help='(SOA) String of the admin email address.',
                           metavar='<admin-email>')
    self.AddFlagRule('admin_email', command='soa', required=not_list)
    self.parser.add_option('--serial-number', action='store',
                           dest='serial_number', type='int',
                           help='(SOA) Integer of the serial number.',
                           metavar='<serial-number>')
    self.AddFlagRule('serial_number', command='soa', required=not_list)
    self.parser.add_option('--refresh-seconds', action='store',
                           dest='refresh_seconds', type='int',
                           help='(SOA) Integer of number of seconds to '
                                'refresh.',
                           metavar='<refresh-seconds>')
    self.AddFlagRule('refresh_seconds', command='soa', required=not_list)
    self.parser.add_option('--retry-seconds', action='store',
                           dest='retry_seconds', type='int',
                           help='(SOA) Integer of number of seconds to retry.',
                           metavar='<retry-seconds>')
    self.AddFlagRule('retry_seconds', command='soa', required=not_list)
    self.parser.add_option('--expiry-seconds', action='store',
                           dest='expiry_seconds', type='int',
                           help='(SOA) Integer of number of seconds to expire.',
                           metavar='<expiry-seconds>')
    self.AddFlagRule('expiry_seconds', command='soa', required=not_list)
    self.parser.add_option('--minimum-seconds', action='store',
                           dest='minimum_seconds', type='int',
                           help='(SOA) Integer of minium number of seconds '
                                'to refresh.',
                           metavar='<minumum-seconds>')
    self.AddFlagRule('minimum_seconds', command='soa', required=not_list)

    self.parser.add_option('--priority', action='store', dest='priority',
                           help='(SRV, MX) Integer of priority between '
                                '0-65535.',
                           type='int', metavar='<priority>')
    self.AddFlagRule('priority', command='srv', required=not_list)
    self.AddFlagRule('priority', command='mx', required=not_list)
    self.parser.add_option('--weight', action='store', dest='weight',
                           help='(SRV) Integer of weight between 0-65535.',
                           type='int', metavar='<weight>')
    self.AddFlagRule('weight', command='srv', required=not_list)
    self.parser.add_option('--port', action='store', dest='port',
                           help='(SRV) Integer of port number.',
                           metavar='<port>', type='int')
    self.AddFlagRule('port', command='srv', required=not_list)

    self.parser.add_option('--mail-server', action='store',
                           dest='mail_server',
                           help='(MX) String of mail server hostname.',
                           metavar='<hostname>')
    self.AddFlagRule('mail_server', command='mx', required=not_list)

    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name',
                           help=('String of the <zone-name>. Example: '
                                 '"sub.university.edu"'), metavar='<zone-name>',
                           default=None)
    self.SetAllFlagRule('zone_name', required=not_list)
    self.parser.add_option('-t', '--target', action='store', dest='target',
                           help='String of the target. "A" record example: '
                                '"machine-01", "PTR" record example: '
                                '192.168.1.1',
                           metavar='<target>', default=None)
    self.SetAllFlagRule('target', required=not_list)
    self.parser.add_option('--ttl', action='store', dest='ttl',
                           help='Time for host to be cached before being '
                                'refreshed.',
                           metavar='<ttl>', default=DEFAULT_TTL)
    self.SetAllFlagRule('ttl', required=False)
    default_view = None
    if( self.action == 'Make' ):
      default_view = u'any'
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name',
                           help='String of view name.', metavar='<view-name>',
                           default=default_view)
    self.SetAllFlagRule('view_name', required=self.action == 'Remove')
    self.AddFlagRule('view_name', required=self.action == 'Make', command='soa')

class FormattedRecords(core_flags.CoreFlags):
  """Command line formattedrecords flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    default_view = None
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name',
                           help='String of view name.', default=default_view)
    self.AddFlagRule('view_name', required=False)
    self.parser.add_option('-f', '--records-file', action='store',
                           dest='records_file',
                           help='Records file location.', default=default_view)
    self.AddFlagRule('records_file', required=True)
    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name', help='String of zone name.',
                           default=None)
    self.AddFlagRule('zone_name', required=True)

class Zone(core_flags.CoreFlags):
  """Command line zone flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    make = self.action == 'Make'
    # All flags
    default_view = None
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name',
                           help='String of view name.', default=default_view)
    self.AddFlagRule('view_name', command='forward', required=make)
    self.AddFlagRule('view_name', command='reverse', required=make)
    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name', help='String of zone name.',
                           default=None)
    self.AddFlagRule('zone_name', command='forward',
                     required=self.action!='List')
    self.AddFlagRule('zone_name', command='reverse',
                     required=self.action!='List')

    # Just Remove
    if( self.action == 'Remove' ):
      # Not required since tool handles the error
      self.AddFlagRule(('force', 'view_name'), flag_type='independent_args',
                       required=False)

    # List and Make
    if( self.action != 'Remove' ):
      self.parser.add_option('-o', '--options', action='store', dest='options',
                             help='String of extra zone/view options, '
                                  'standard bind view clause syntax.',
                             metavar='<view-options>', default=None)
      self.AddFlagRule('options', command='forward', required=False)
      self.AddFlagRule('options', command='reverse', required=False)
      self.parser.add_option('--origin', action='store', dest='origin',
                              help='String of zone origin.', metavar='<origin>',
                              default=None)
      self.AddFlagRule('origin', required=make, command='forward')
      self.parser.add_option('-t', '--type', action='store', dest='type',
                             help='String of zone type. '
                             '(master, slave, forward)', metavar='<type>',
                             default=None)
      self.AddFlagRule('type', required=make, command='forward')
      self.AddFlagRule('type', required=make, command='reverse')
      self.parser.add_option('--cidr-block', action='store', dest='cidr_block',
                             help='String of CIDR block for reverse zones.',
                             metavar='<cidr-block>', default=None)
      # Not required since tool handles the error
      self.AddFlagRule(('cidr_block', 'origin'), required=self.action!='List',
                       command='reverse', flag_type='independent_args')

    # Just Make
    if( self.action == 'Make' ):
      self.parser.add_option('--dont-make-any', action='store_false',
                             dest='dont_make_any',
                             help='Make a zone in a view other than any, must '
                                  'specify view name.',
                             default=True)
      self.SetAllFlagRule('dont_make_any', required=False)


class View(core_flags.CoreFlags):
  """Command line view flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    not_list = self.action != 'List'
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name', help='String of view.',
                           default=None)
    self.SetAllFlagRule('view_name', required=not_list)
    self.parser.add_option('-V', '--view-dep', action='store',
                           dest='view_subset', default=None,
                           help='String of view dependency.')
    self.AddFlagRule('view_subset', required=not_list, command='view_subset')
    self.parser.add_option('-o', '--options', action='store', dest='options',
                           help='View options.', metavar='<options>',
                           default=None)
    self.AddFlagRule('options', required=False, command='view')
    self.parser.add_option('-e', '--dns-server-set', action='store',
                           dest='dns_server_set', default=None,
                           help='String of dns server set name.')
    self.AddFlagRule('dns_server_set', required=not_list,
                     command='dns_server_set')
    self.parser.add_option('-a', '--acl', action='store', dest='acl',
                           help='String of access control list name.',
                           default=None)
    if( self.action != 'Remove' ):
      self.AddFlagRule('acl', required=not_list, command='view')
    self.AddFlagRule('acl', required=not_list, command='acl')


class Host(core_flags.CoreFlags):
  """Command line view flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    not_list = self.action != 'List'
    if( not_list ):
      self.parser.add_option('-i', '--ip-address', action='store',
                             dest='ip_address', default=None,
                             help='Full IP address of machine.',
                             metavar='<ip-address>')
      if( self.action == 'Make' ):
        self.AddFlagRule('ip_address', required=not_list, command='add')
      else:
        self.AddFlagRule('ip_address', required=not_list)
      self.parser.add_option('-t', '--target', action='store', dest='target',
                             help='String of machine host name. (Not FQDN)',
                             metavar='<target>', default=None)
      self.AddFlagRule('target', required=not_list)
      self.parser.add_option('--ttl', action='store', dest='ttl',
                             help='Time for host to live before being '
                             'refreshed.', metavar='<ttl>', default=DEFAULT_TTL)
      self.AddFlagRule('ttl', required=False)
    self.parser.add_option('--cidr-block', action='store', dest='cidr_block',
                           help='Get target ip address from cidr block '
                                'automatically.',
                           metavar='<cidr-block>', default=None)
    if( self.action == 'Make' ):
      self.AddFlagRule('cidr_block', required=True, command='findfirst')
    else:
      self.AddFlagRule('cidr_block', required=False)
    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name', help='String of the zone name.',
                           metavar='<zone-name>', default=None)
    self.AddFlagRule('zone_name', required=not_list)
    if( not_list ):
      default_view = u'any'
    else:
      default_view = None
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name',
                           help=('String of the view name <view-name>. '
                                 'Example: "internal"'),
                           metavar='<view-name>',
                           default=default_view)
    self.AddFlagRule('view_name', required=False)


class DnsServer(core_flags.CoreFlags):
  """Command line dns_server flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    not_list = self.action != 'List'
    self.parser.add_option('-d', '--dns-server', action='store',
                           dest='dns_server', help='DNS server.',
                           default=None)
    self.AddFlagRule('dns_server', required=not_list, command='dns_server')
    self.AddFlagRule('dns_server', required=not_list, command='assignment')
    self.parser.add_option('-e', '--dns-server-set', action='store',
                           dest='dns_server_set',
                           help='DNS server set.', default=None)
    self.AddFlagRule('dns_server_set', required=not_list,
                     command='dns_server_set')
    self.AddFlagRule('dns_server_set', required=not_list, command='assignment')


class User(core_flags.CoreFlags):
  """Command line user flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    not_list = self.action != 'List'
    self.parser.add_option('-n', '--new-user', action='store', dest='new_user',
                           help='String of the new user to create.',
                           metavar='<new-user>', default=None)
    self.AddFlagRule('new_user', required=not_list, command='user')
    self.AddFlagRule('new_user', required=not_list, command='assignment')
    self.parser.add_option('-a', '--access-level', action='store',
                           dest='access_level',
                           help='Access level of new user.',
                           metavar='<access-level>', default=None, type='int')
    self.AddFlagRule('access_level', required=self.action=='Make',
                     command='user')
    self.parser.add_option('-g', '--group', action='store', dest='group',
                           help='String of the group name to create or assign.',
                           metavar='<group>', default=None)
    self.AddFlagRule('group', required=not_list, command='group')
    self.AddFlagRule('group', required=not_list, command='assignment')
    self.AddFlagRule('group', required=not_list, command='forward')
    self.AddFlagRule('group', required=not_list, command='reverse')
    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name',
                           help='String of the zone name (optional)',
                           metavar='<zone>', default=None)
    self.AddFlagRule('zone_name', required=not_list, command='forward')
    self.AddFlagRule('zone_name', required=not_list, command='reverse')
    self.parser.add_option('--access-right', action='store',
                           dest='access_right',
                           help='String of the access right (r/rw)',
                           metavar='r|rw', default=None)
    self.AddFlagRule('access_right', required=not_list, command='forward')
    self.AddFlagRule('access_right', required=not_list, command='reverse')
    self.parser.add_option('-b', '--cidr-block', action='store',
                           dest='cidr_block', help='String of CIDR block.',
                           metavar='<cidr-block>', default=None)
    self.AddFlagRule('cidr_block', required=not_list, command='reverse')


class Hosts(core_flags.CoreFlags):
  """Command line uphost flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('--commit', action='store_true', dest='commit',
                           help='Commits changes of hosts file without '
                                'confirmation.', default=False)
    self.parser.add_option('--no-commit', action='store_true', dest='no_commit',
                           help='Suppresses changes of hosts file.',
                           default=False)
    self.AddFlagRule(('no_commit', 'commit'), required=False, command='update',
                     flag_type='independent_args')
    self.AddFlagRule(('no_commit', 'commit'), required=False, command='edit',
                     flag_type='independent_args')
    self.parser.add_option('-r', '--range', action='store', dest='range',
                           help='CIDR block range of IP addresses. Assumes -l, '
                                'will only print a list of ip addresses. '
                                'Example: 10.10.0.0/24', metavar='<range>',
                           default=None)
    self.AddFlagRule('range', required=True, command='dump')
    self.AddFlagRule('range', required=True, command='edit')
    self.parser.add_option('--ttl', action='store', dest='ttl',
                           help='Time to live.', metavar='<ttl>', default=3600)
    self.AddFlagRule('ttl', required=False, command='update')
    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name', help='String of the zone name.',
                           metavar='<zone-name>', default=None)
    self.SetAllFlagRule('zone_name', required=False)
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name',
                           help=('String of the view name <view-name>. Example: '
                                 '"internal"'), metavar='<view-name>',
                           default='any')
    self.SetAllFlagRule('view_name', required=False)

    self.parser.add_option('-f', '--file', action='store', dest='file',
                           help='File name of hosts file to write to database.',
                           metavar='<file-name>', default='hosts_out')
    self.SetAllFlagRule('file', required=False)


class CNAME(core_flags.CoreFlags):
  """Command line CNAME flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('--hostname', action='store', dest='hostname',
                           help='String of hostname', metavar='hostname',
                           default=None)
    self.AddFlagRule('hostname', required=True)
    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name', help='String of the zone name.',
                           metavar='<zone-name>', default=None)
    self.SetAllFlagRule('zone_name', required=True)
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name',
                           help=('String of the view name <view-name>. '
                                 'Example: "internal"'), metavar='<view-name>',
                           default='any')
    self.SetAllFlagRule('view_name', required=True)
    self.parser.add_option('-r', '--recursive', action='store_true',
                           dest='recursive', help='Use recursion during lookup',
                           metavar='<recursive>', default=False)
    self.SetAllFlagRule('recursive', required=False)


class MassAdd(core_flags.CoreFlags):
  """Command line uphost flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('--commit', action='store_true', dest='commit',
                           help='Commits changes of hosts file without '
                                'confirmation.', default=False)
    self.parser.add_option('--no-commit', action='store_true', dest='no_commit',
                           help='Suppresses changes of hosts file.',
                           default=False)
    self.AddFlagRule(('no_commit', 'commit'), required=False,
                     flag_type='independent_args')
    self.parser.add_option('-z', '--zone-name', action='store',
                           dest='zone_name', help='String of the zone name.',
                           metavar='<zone-name>', default=None)
    self.SetAllFlagRule('zone_name', required=True)
    self.parser.add_option('-v', '--view-name', action='store',
                           dest='view_name',
                           help=('String of the view name <view-name>. '
                                 'Example: '
                                 '"internal"'), metavar='<view-name>',
                           default='any')
    self.SetAllFlagRule('view_name', required=True)

    self.parser.add_option('-f', '--file', action='store', dest='file',
                           help='File name of hosts file to write to database.',
                           metavar='<file-name>', default='hosts_out')
    self.SetAllFlagRule('file', required=True)


class NamedGlobals(core_flags.CoreFlags):
  """Command line named global flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('-d', '--dns-server-set', action='store',
                           dest='dns_server_set',
                           help='String of the dns server set name.',
                           metavar='<dns-server-set>', default=None)
    self.AddFlagRule('dns_server_set', required=False, command='dump')
    self.AddFlagRule('dns_server_set', required=True, command='update')
    self.AddFlagRule('dns_server_set', required=True, command='list')
    self.AddFlagRule('dns_server_set', required=True, command='revert')
    self.AddFlagRule('dns_server_set', required=True, command='edit')
    self.parser.add_option('-i', '--option-id', action='store',
                           dest='option_id',
                           help='Integer of option id.', metavar='<option-id>',
                           default=None)
    self.AddFlagRule('option_id', required=False, command='list')
    self.AddFlagRule('option_id', required=False, command='dump')
    self.AddFlagRule('option_id', required=True, command='revert')
    self.parser.add_option('-t', '--timestamp', action='store',
                           dest='timestamp',
                           help='String of timestamp in YYYY/MM/DD/HH/MM/SS '
                                'format.', metavar='<timestamp>', default=None)
    self.AddFlagRule('timestamp', required=False, command='list')
    self.AddFlagRule('timestamp', required=False, command='dump')
    self.AddFlagRule('timestamp', required=False, command='edit')
    self.parser.add_option('-q', '--quiet', action='store_true', dest='quiet',
                           help='Suppress program output.', default=False)
    self.SetAllFlagRule('quiet', required=False)

    self.parser.add_option('-f', '--file', action='store', dest='file',
                           help='File name of named header dump.',
                           metavar='<file-name>', default='named_header')
    self.AddFlagRule('file', required=False, command='dump')
    self.AddFlagRule('file', required=False, command='update')
    self.AddFlagRule('file', required=False, command='edit')

    self.parser.add_option(
        '--no-header', action='store_true', dest='no_header',
        help='Do not display a header.', default=False)
    self.AddFlagRule('no_header', required=False)



class Credential(core_flags.CoreFlags):
  """Command line credential flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('-U', '--user-credential', action='store',
                      dest='user_credential',
                      help='Username to apply credential to.',
                      metavar='<user-credential>', default=None)
    self.AddFlagRule('user_credential', command='make_infinite')
    self.AddFlagRule('user_credential', command='remove')
    self.AddFlagRule('user_credential', required=False, command='list')
    self.parser.add_option('--no-header', action='store_true', dest='no_header',
                      help='Do not display a header.', default=False)
    self.AddFlagRule('no_header', required=False, command='list')

  def SetActionFlags(self):
    """Method to set action variable since credential has no action class"""
    self.action = 'Credential'


class AuditLog(core_flags.CoreFlags):
  """Command line audit log flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('-U', '--roster-user', action='store',
                           dest='roster_user', help='Roster username.',
                           metavar='<roster-user>', default=None)
    self.AddFlagRule('roster_user', required=False)
    self.parser.add_option('-a', '--action', action='store', dest='action',
                           help='Specify action run on Roster.',
                           metavar='<action>', default=None)
    self.AddFlagRule('action', required=False)
    self.parser.add_option('--success', action='store', dest='success',
                           help='Integer 1 or 0 of action success.',
                           metavar='<success>', default=None, type='int')
    self.AddFlagRule('success', required=False)
    self.parser.add_option('-b', '--begin-time', action='store',
                           dest='begin_time',
                           help='Beginning time stamp in format '
                                'YYYY-MM-DDThh:mm:ss.', metavar='<begin-time>',
                           default=None)
    self.parser.add_option('-e', '--end-time', action='store', dest='end_time',
                           help='Ending time stamp in format '
                                'YYYY-MM-DDThh:mm:ss.', metavar='<end-time>',
                           default=None)
    self.AddFlagRule(('begin_time', 'end_time'), required=False,
                     flag_type='dependent_args')
    self.parser.add_option('--no-header', action='store_true', dest='no_header',
                           help='Do not display a header.', default=False)
    self.AddFlagRule('no_header', required=False)

  def SetActionFlags(self):
    """Method to set action variable since credential has no action class"""
    self.action = 'AuditLog'

class ReservedWord(core_flags.CoreFlags):
  """Command line reserved word flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('-w', '--word', action='store', dest='word',
                           help='The reserved word.', metavar='<word>',
                           default=None)
    self.SetAllFlagRule('word', required=self.action!='List')


class SetMaintenance(core_flags.CoreFlags):
  """Command line set maintenenace flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    self.parser.add_option('--on', action='store_true', dest='on',
                           help='Turn Roster maintenance mode on.',
                           default=False)
    self.parser.add_option('--off', action='store_true', dest='off',
                           help='Turn Roster maintenance mode off.',
                           default=False)
    self.AddFlagRule(('on', 'off'), required=True, command='set',
                     flag_type='independent_args')

  def SetActionFlags(self):
    """Method to set action variable since set maintenance has no action
    class
    """
    self.action = 'SetMaintenance'


class Bootstrap(core_flags.CoreFlags):
  """Command line bootstrap flags"""
  def SetDataFlags(self):
    """Sets flags for self.parser"""
    pass
  def SetActionFlags(self):
    """Method to set action variable since set maintenance has no action
    class
    """
    self.action = 'Bootstrap'
