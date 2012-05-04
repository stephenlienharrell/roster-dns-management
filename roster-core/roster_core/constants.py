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

"""Module to handle all constants."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


# These are reserved ipv6 addresses.
RESERVED_IPV6 = ('::', '::1/128', 'fe80::/10', 'ff01::1', 'ff02::1', 'ff01::2',
                 'ff05::2', '3fff::/16', '2000::/16', '::/8')
RESERVED_IPV4 = ('223/8', '224/3')


# This is the default TTL for all records inserted into the database.
DEFAULT_TTL = 3600


# This is the highest serial number that a zone can have.
MAX_SOA_SERIAL = 4294967295

# This ratio will determine if ListRecordsByCIDRBlock should read the entire
# database of records or read each record individually
RECORD_RATIO = 20

# These are access levels in enum like variables for readability. These
# access levels are primarilly for the user table and it's type checking.
# Any access level used in the code should be listed here.
# Access levels are represented as an unsigned small int in the database.
ACCESS_LEVELS = {'dns_admin': 128,
                 'domain_admin': 64,
                 'user': 32,
                 'noop': 0}

# Valid access rights for forward or reverse perms in the database.
ACCESS_RIGHTS = ['rw', 'r']

# This is a list of tables that are not audit logged when changes are made.
# it is important not to overwrite these tables when doing a partial replay
TABLES_NOT_AUDIT_LOGGED = ['audit_log', 'locks']

# This is a list of ronly ecord types that can be modified by user level.
USER_LEVEL_RECORDS = ['a', 'aaaa', 'ptr', 'cname']

# This is a list of record types that can be indexed by IP address.
RECORD_TYPES_INDEXED_BY_IP = ['ptr', 'a', 'aaaa']

# This is the default config file location for roster server
SERVER_CONFIG_FILE_LOCATION = '/etc/roster/roster_server.conf'

# The SUPPORTED_METHODS hash contains a hash for every supported method.
# 'check' indicates whether the target zone/IP range should be checked.
# 'write' indicates whether the method requires write access.
# 'access_level' is the minimum user access level required to use this method.
SUPPORTED_METHODS = {
    'ListRecords':  {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['user']},

    'ListRecordsByCIDRBlock':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['user']},

    'MakeRecord':   {'check': True,
                     'write': True,
                     'access_level': ACCESS_LEVELS['user']},

    'RemoveRecord': {'check': True,
                     'write': True,
                     'access_level': ACCESS_LEVELS['user']},

    'UpdateRecord': {'check': True,
                     'write': True,
                     'access_level': ACCESS_LEVELS['user']},
    'ListZoneTypes':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['user']},

    'MakeZoneType': {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveZoneType':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListViews':    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'GetViewsByUser':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['user']},

    'MakeView':     {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveView':   {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'UpdateView':   {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListViewAssignments':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeViewAssignment':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveViewAssignment':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListDnsServers':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeDnsServer':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveDnsServer':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'UpdateDnsServer':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListDnsServerSets':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeDnsServerSet':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveDnsServerSet':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'UpdateDnsServerSet':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListDnsServerSetViewAssignments':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeDnsServerSetViewAssignments':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveDnsServerSetViewAssignments':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListDnsServerSetAssignments':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeDnsServerSetAssignments':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveDnsServerSetAssignments':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'GetAssociatedCNAMEs':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['user']},

    'RemoveCNamesByAssignmentHost':
                    {'check': True,
                     'write': True,
                     'access_level': ACCESS_LEVELS['user']},

    'ListACLs':     {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeACL':      {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveACL':    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveCIDRBlockFromACL':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListViewToACLAssignments':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeViewToACLAssignments':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveViewToACLAssignments':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListReverseRangeZoneAssignments':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeReverseRangeZoneAssignment':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveReverseRangeZoneAssignment':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListForwardZonePermissions':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeForwardZonePermission':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveForwardZonePermission':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListReverseRangePermissions':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeReverseRangePermission':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveReverseRangePermission':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'GetCIDRBlocksByView':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['user']},

    'ProcessRecordsBatch':
                    {'check': True,
                     'write': True,
                     'access_level': ACCESS_LEVELS['user']},

    'ListZones':    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeZone':     {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveZone':   {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'UpdateZone':   {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListUsers':    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeUser':     {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveUser':   {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'UpdateUser':   {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListGroups':   {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeGroup':    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveGroup':  {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'UpdateGroup':  {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListUserGroupAssignments':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeUserGroupAssignment':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveUserGroupAssignment':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListNamedConfGlobalOptions':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'MakeNamedConfGlobalOption':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListReservedWords':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['domain_admin']},

    'MakeReservedWord':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveReservedWord':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListRecordArgumentDefinitions':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListAuditLog':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'ListCredentials':
                    {'check': False,
                     'write': False,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'MakeInfiniteCredential':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'RemoveCredential':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']},

    'SetMaintenanceFlag':
                    {'check': False,
                     'write': True,
                     'access_level': ACCESS_LEVELS['dns_admin']}}



# These are a subset of tables in the dtabase. They are enumerated here to
# enable dynamic type checking in data_validation.py
TABLES = {
    'record_types':      {'record_type': 'UnicodeString'},

    'data_types':        {'data_type': 'UnicodeString'},

    'record_arguments':  {'record_arguments_type': 'UnicodeString',
                          'argument_name': 'UnicodeString',
                          'argument_order': 'UnsignedInt',
                          'argument_data_type': 'UnicodeString'},

    'users':             {'user_name': 'UnicodeString',
                          'access_level': 'AccessLevel'},

    'credentials':       {'credential_user_name': 'UnicodeString',
                          'credential': 'UnicodeString',
                          'last_used_timestamp': 'DateTime',
                          'infinite_cred': 'IntBool'},

    'zones':             {'zone_name': 'UnicodeString'},

    'view_dependencies': {'view_dependency': 'UnicodeString'},

    'zone_types':        {'zone_type': 'UnicodeString'},

    'zone_view_assignments':
        {'zone_view_assignments_zone_name': 'UnicodeString',
         'zone_view_assignments_view_dependency': 'UnicodeString',
         'zone_view_assignments_zone_type': 'UnicodeString',
         'zone_origin': 'Hostname',
         # This should probably be it's own data type
         'zone_options': 'UnicodeString'},

    'records':           {'records_id': 'UnsignedInt',
                          'record_type': 'UnicodeString',
                          'record_target': 'UnicodeStringNoSpaces',
                          'record_ttl': 'UnsignedInt',
                          'record_zone_name': 'UnicodeString',
                          'record_view_dependency': 'UnicodeString',
                          'record_last_user': 'UnicodeString'},

    'record_arguments_records_assignments':
        {'record_arguments_records_assignments_record_id': 'UnsignedInt',
         'record_arguments_records_assignments_type': 'UnicodeString',
         'record_arguments_records_assignments_argument_name': 'UnicodeString',
         'argument_value': 'UnicodeString'},

    'acls':              {'acl_name': 'UnicodeString'},

    'acl_ranges':        {'acl_ranges_acl_name': 'UnicodeString',
                          'acl_range_allowed': 'IntBool',
                          'acl_range_cidr_block': 'CIDRBlock'},

    'views':             {'view_name': 'UnicodeString',
                          # This should probably be it's own data type
                          'view_options': 'UnicodeString'},

    'view_acl_assignments':
                         {'view_acl_assignments_acl_name': 'UnicodeString',
                          'view_acl_assignments_view_name': 'UnicodeString'},

    'view_dependency_assignments':
        {'view_dependency_assignments_view_name': 'UnicodeString',
         'view_dependency_assignments_view_dependency': 'UnicodeString'},

    'dns_servers':        {'dns_server_name': 'UnicodeString'},

    'dns_server_sets':    {'dns_server_set_name': 'UnicodeString'},

    'dns_server_set_assignments':
        {'dns_server_set_assignments_dns_server_name': 'UnicodeString',
         'dns_server_set_assignments_dns_server_set_name': 'UnicodeString'},

    'dns_server_set_view_assignments':
        {'dns_server_set_view_assignments_dns_server_set_name': 'UnicodeString',
         'dns_server_set_view_assignments_view_name': 'UnicodeString'},

    'groups':            {'group_name': 'UnicodeString'},

    'user_group_assignments':
        {'user_group_assignments_group_name': 'UnicodeString',
         'user_group_assignments_user_name': 'UnicodeString'},

    'forward_zone_permissions':
        {'forward_zone_permissions_group_name': 'UnicodeString',
         'forward_zone_permissions_zone_name': 'UnicodeString',
         'forward_zone_permissions_access_right': 'AccessRight'},

    'reverse_range_permissions':
        {'reverse_range_permissions_group_name': 'UnicodeString',
         'reverse_range_permissions_cidr_block': 'CIDRBlock',
          'reverse_range_permissions_access_right': 'AccessRight'},

    'reverse_range_zone_assignments':
        {'reverse_range_zone_assignments_zone_name': 'UnicodeString',
         'reverse_range_zone_assignments_cidr_block': 'CIDRBlock'},

    'named_conf_global_options':
        {'named_conf_global_options_id': 'UnsignedInt',
         'global_options': 'UnicodeString',
         'named_conf_global_options_dns_server_set_name': 'UnicodeString',
         'options_created': 'DateTime'},

    'reserved_words':
                         {'reserved_word': 'ReservedWord'},

    'audit_log':
                         {'audit_log_id': 'UnsignedInt',
                          'audit_log_user_name': 'UnicodeString',
                          'action': 'UnicodeString',
                          'data': 'PickleString',
                          'success': 'IntBool',
                          'audit_log_timestamp': 'DateTime'},
    'locks':
        {'lock_name': 'UnicodeString', 'locked': 'IntBool'},

    'ipv4_index':
        {'ipv4_dec_address': 'UnsignedInt',
         'ipv4_index_record_id': 'UnsignedInt'},

    'ipv6_index':
        {'ipv6_dec_upper': 'UnsignedInt',
         'ipv6_dec_lower': 'UnsignedInt',
         'ipv6_index_record_id': 'UnsignedInt'}}


# vi: set ai aw sw=2:
