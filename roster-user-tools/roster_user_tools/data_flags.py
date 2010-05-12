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
__version__ = '#TRUNK#'


import core_flags

class Acl(core_flags.CoreFlags):
  """Command line acl flags"""
  def SetDataFlags(self):
    """Sets flags for parser"""
    self.parser.add_option('-a', '--acl', action='store', dest='acl',
                           help='ACL name', default=None)
    self.parser.add_option('--cidr-block', action='store', dest='cidr_block',
                           help='Cidr block or single IP address.',
                           default=None)
    self.parser.add_option('--allow', action='store_true', dest='allow',
                           help='Search for allowed ACLs.', default=None)
    self.parser.add_option('--deny', action='store_true', dest='deny',
                           help='Search for denied ACLs.', default=None)


class Record(core_flags.CoreFlags):
  """Command line record flags"""
  def SetDataFlags(self):
    self.parser.add_option('--a', action='store_true', dest='a', default=False,
                           help='Set the record type to A record.')
    self.parser.add_option('--a-assignment-ip', action='store',
                           dest='a_assignment_ip', help='String of the IPv4 address',
                           metavar='<assignment-ip>')

    self.parser.add_option('--aaaa', action='store_true', dest='aaaa',
                           default=False,
                           help='Set the record type to AAAA record.')
    self.parser.add_option('--aaaa-assignment-ip', action='store',
                           dest='aaaa_assignment_ip',
                           help='String of the IPv6 address.',
                           metavar='<assignment-ip>')

    self.parser.add_option('--hinfo', action='store_true', dest='hinfo',
                           default=False,
                           help='Set the record type to HINFO record.')
    self.parser.add_option('--hinfo-hardware', action='store',
                           dest='hinfo_hardware', metavar='<hardware>',
                           help='String of the hardware type.')
    self.parser.add_option('--hinfo-os', action='store', dest='hinfo_os',
                           help='String of the OS type.', metavar='<os>')

    self.parser.add_option('--txt', action='store_true', dest='txt',
                           default=False,
                           help='Set the record type to TXT record.')
    self.parser.add_option('--txt-quoted-text', action='store',
                           dest='txt_quoted_text', metavar='<quoted-text>',
                           help='String of quoted text.')

    self.parser.add_option('--cname', action='store_true', dest='cname',
                           default=False,
                           help='Set the record type to CNAME record.')
    self.parser.add_option('--cname-assignment-host', action='store',
                           dest='cname_assignment_host', metavar='<hostname>',
                           help='String of the CNAME hostname.')

    self.parser.add_option('--soa', action='store_true', dest='soa',
                           default=False,
                           help='Set the record type to SOA record.')
    self.parser.add_option('--soa-name-server', action='store',
                           dest='soa_name_server',
                           help='String of the hostname of the SOA name server.',
                           metavar='<name-server>')
    self.parser.add_option('--soa-admin-email', action='store',
                           dest='soa_admin_email',
                           help='String of the admin email address.',
                           metavar='<name-server>')
    self.parser.add_option('--soa-serial-number', action='store',
                           dest='soa_serial_number',
                           help='String of the serial number.',
                           metavar='<serial-number>')
    self.parser.add_option('--soa-refresh-seconds', action='store',
                           dest='soa_refresh_seconds',
                           help='Number of seconds to refresh.',
                           metavar='<refresh-seconds>')
    self.parser.add_option('--soa-retry-seconds', action='store',
                           dest='soa_retry_seconds',
                           help='Number of seconds to retry.',
                           metavar='<retry-seconds>')
    self.parser.add_option('--soa-expiry-seconds', action='store',
                           dest='soa_expiry_seconds',
                           help='Number of seconds to expire.',
                           metavar='<expiry-seconds>')
    self.parser.add_option('--soa-minimum-seconds', action='store',
                           dest='soa_minimum_seconds',
                           help='Minium number of seconds to refresh.',
                           metavar='<minumum-seconds>')

    self.parser.add_option('--srv', action='store_true', dest='srv',
                           default=False,
                           help='Set the record type to SRV record.')
    self.parser.add_option('--srv-priority', action='store', dest='srv_priority',
                           help='Integerof priority between 0-65535.',
                           metavar='<priority>')
    self.parser.add_option('--srv-weight', action='store', dest='srv_weight',
                           help='Integer of weight between 0-65535.',
                           metavar='<weight>')
    self.parser.add_option('--srv-port', action='store', dest='srv_port',
                           help='Port number.', metavar='<port>')
    self.parser.add_option('--srv-assignment-host', action='store',
                           dest='srv_assignment_host',
                           help='String of the SRV assignment hostname.',
                           metavar='<hostname>')

    self.parser.add_option('--ns', action='store_true', dest='ns', default=False,
                           help='Set the record type to NS record.')
    self.parser.add_option('--ns-name-server', action='store',
                           dest='ns_name_server',
                           help='String of the hostname of the NS name server.',
                           metavar='<hostname>')

    self.parser.add_option('--mx', action='store_true', dest='mx', default=False,
                          help='Set the record type to MX record.')
    self.parser.add_option('--mx-priority', action='store', dest='mx_priority',
                           help='Integer of priority between 0-65535.',
                           metavar='<priority>')
    self.parser.add_option('--mx-mail-server', action='store',
                           dest='mx_mail_server',
                           help='String of mail server hostname.',
                           metavar='<hostname>')

    self.parser.add_option('--ptr', action='store_true', dest='ptr',
                           default=False,
                           help='Set the record type to PTR record.')
    self.parser.add_option('--ptr-assignment-host', action='store',
                           dest='ptr_assignment_host',
                           help='String of PTR hostname.', metavar='<hostname>')

    self.parser.add_option('-z', '--zone-name', action='store', dest='zone_name',
                           help=('String of the <zone-name>. Example: '
                                 '"sub.university.edu"'), metavar='<zone-name>',
                           default=None)
    self.parser.add_option('-t', '--target', action='store', dest='target',
                           help='String of the target. "A" record example: '
                                '"machine-01", "PTR" record example: 192.168.1.1',
                           metavar='<target>', default=None)
    self.parser.add_option('--ttl', action='store', dest='ttl',
                           help='Integer of time to live <ttl> per record.',
                           metavar='<ttl>', default=3600)
    self.parser.add_option('-v', '--view-name', action='store', dest='view_name',
                           help=('String of the view name <view-name>. Example: '
                                 '"internal"'), metavar='<view-name>',
                           default='any')
