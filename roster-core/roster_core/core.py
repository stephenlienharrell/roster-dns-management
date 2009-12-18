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

"""Toplevel core API."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.10'


import datetime
import audit_log
import constants
import errors
import user


class RecordError(errors.CoreError):
  pass


class Core(object):
  """Backend Roster interface.

  This class is meant to be the only interface to the database for top
  level programming for a web or xml-rpc interface, or anything else
  that would need to talk to the database.

  All errors raised will be a subclass of CoreError.
  """
  def __init__(self, user_name, config_instance, unittest_timestamp=None):
    """Sets self.db_instance and self.user_instance for usage in the class.

    Inputs:
      user_name: string of user name
      config_instance: instantiated Config class object
      unittest_timestamp: datetime object timestamp for unit testing
    """
    self.unittest_timestamp = unittest_timestamp
    self.db_instance = config_instance.GetDb()
    self.log_instance = audit_log.AuditLog(log_to_syslog=True, log_to_db=True,
                                           db_instance=self.db_instance)
    self.user_instance = user.User(user_name, self.db_instance,
                                   self.log_instance)

  def MakeUser(self, user_name, access_level):
    """Create a user.

    Inputs:
      user_name: string of user name
      access_level: int from 0-255 as defined in user.py

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeUser')
    user_dict = {'user_name': user_name,
                 'access_level': access_level}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('users', user_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, u'MakeUser',
                                  u'user_name: %s access_level: %s' % (
                                      user_name, access_level), success)

  def ListUsers(self, user_name=None, access_level=None):
    """Lists one or many users, if all args are None then list them all.

    Inputs:
      user_name: string of user name
      access_level: int from 0-255 as defined in user.py

    Raises:
      CoreError  Raised for any internal problems.

    Output:
      dictionary: keyed by the user name with value of access_level.
        example: {'sharrell': 128,
                  'shuey': 64}
    """
    self.user_instance.Authorize('ListUsers')
    user_dict = {'user_name': user_name,
                 'access_level': access_level}
    self.db_instance.StartTransaction()
    try:
      users = self.db_instance.ListRow('users', user_dict)
    finally:
      self.db_instance.EndTransaction()

    user_access_level_dict = {}
    for user in users:
      user_access_level_dict[user['user_name']] = user['access_level']

    return user_access_level_dict

  def RemoveUser(self, user_name):
    """Removes a user.

    Inputs:
      user_name: string of user name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveUser')
    search_user_dict = self.db_instance.GetEmptyRowDict('users')
    search_user_dict['user_name'] = user_name
    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        found_user = self.db_instance.ListRow('users', search_user_dict,
                                              lock_rows=True)
        if( found_user ):
          # user_name in users is a unique field so we know there is only one.
          row_count += self.db_instance.RemoveRow('users', found_user[0])
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, u'RemoveUser',
                                  u'user_name: %s' % user_name, success)

    return row_count

  def UpdateUser(self, search_user_name, update_user_name=None,
                 update_access_level=None):
    """Updates a user.

    Inputs:
      search_user_name: string of user name
      update_user_name: string of user name
      update_access_level: int from 0-255 as defined in user.py

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('UpdateUser')
    search_user_dict = self.db_instance.GetEmptyRowDict('users')
    search_user_dict['user_name'] = search_user_name
    update_user_dict = self.db_instance.GetEmptyRowDict('users')
    update_user_dict['user_name'] = update_user_name
    update_user_dict['access_level'] = update_access_level
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.UpdateRow('users', search_user_dict,
                                               update_user_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise

      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, u'UpdateUser',
                                  u'search_user_name: %s update_user_name: %s '
                                  'update_access_level: %s' % (
                                      search_user_name, update_user_name,
                                      update_access_level),
                                  success)
    return row_count

  def ListGroups(self):
    """List all groups.

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      list of groups
        example ['cs', 'bio']
    """
    self.user_instance.Authorize('ListGroups')
    group_dict = self.db_instance.GetEmptyRowDict('groups')
    self.db_instance.StartTransaction()
    try:
      groups = self.db_instance.ListRow('groups', group_dict)
    finally:
      self.db_instance.EndTransaction()

    group_list = []
    for group in groups:
      group_list.append(group['group_name'])

    return group_list

  def MakeGroup(self, group_name):
    """Make group.

    Inputs:
      group_name: string of group name

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeGroup')
    group_dict = self.db_instance.GetEmptyRowDict('groups')
    group_dict['group_name'] = group_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('groups', group_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, u'MakeGroup',
                                  u'group_name: %s' % group_name, success)

  def RemoveGroup(self, group_name):
    """Remove group.

    Inputs:
      group_name: string of group name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveGroup')
    group_dict = self.db_instance.GetEmptyRowDict('groups')
    group_dict['group_name'] = group_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('groups', group_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, u'RemoveGroup',
                                  u'group_name: %s' % group_name, success)
    return row_count

  def UpdateGroup(self, search_group_name, update_group_name):
    """Update group.

    Inputs:
      search_group_name: string of group name
      update_group_name: string of group name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('UpdateGroup')
    search_group_dict = self.db_instance.GetEmptyRowDict('groups')
    search_group_dict['group_name'] = search_group_name

    update_group_dict = self.db_instance.GetEmptyRowDict('groups')
    update_group_dict['group_name'] = update_group_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.UpdateRow('groups', search_group_dict,
                                               update_group_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, u'UpdateGroup',
                                  u'search_group_name: %s '
                                  'update_group_name: %s' % (search_group_name,
                                                             update_group_name),
                                  success)
    return row_count

  def ListUserGroupAssignments(self, user_name=None, group_name=None,
                               key_by_group=False):
    """List user-group assignments.

    Assignments can be given as a dictionary of users with lists of groups or
    as a dictionary of groups as a list of users.

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      dictionarie keyed by group or user with values of lists of groups or users
      depending on key_by_group bool
        example keyed by user: {'sharrell': ['cs', 'bio'],
                                'shuey': ['cs']}
        example keyed by group: {'cs': ['shuey', 'sharrell']
                                 'bio': ['sharrell']
    """
    self.user_instance.Authorize('ListUserGroupAssignments')
    assignment_dict = self.db_instance.GetEmptyRowDict('user_group_assignments')
    assignment_dict['user_group_assignments_group_name'] = group_name
    assignment_dict['user_group_assignments_user_name'] = user_name

    self.db_instance.StartTransaction()
    try:
      assignments = self.db_instance.ListRow('user_group_assignments',
                                             assignment_dict)
    finally:
      self.db_instance.EndTransaction()

    assignments_dict = {}
    for assignment in assignments:
      if( key_by_group ):
        if( not assignment['user_group_assignments_group_name'] in
            assignments_dict ):
          assignments_dict[
              assignment['user_group_assignments_group_name']] = []

        assignments_dict[
            assignment['user_group_assignments_group_name']].append(
                assignment['user_group_assignments_user_name'])
      else:
        if( not assignment['user_group_assignments_user_name'] in
            assignments_dict ):
          assignments_dict[
              assignment['user_group_assignments_user_name']] = []

        assignments_dict[
            assignment['user_group_assignments_user_name']].append(
                assignment['user_group_assignments_group_name'])

    return assignments_dict

  def MakeUserGroupAssignment(self, user_name, group_name):
    """Make user-group assignment.

    Inputs:
      group_name: string of group name
      user_name: string of user name

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeUserGroupAssignment')
    assignment_dict = self.db_instance.GetEmptyRowDict('user_group_assignments')
    assignment_dict['user_group_assignments_group_name'] = group_name
    assignment_dict['user_group_assignments_user_name'] = user_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('user_group_assignments', assignment_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeUserGroupAssignments',
                                  u'user_name: %s group_name: %s' % (
                                      user_name, group_name), success)

  def RemoveUserGroupAssignment(self, user_name, group_name):
    """Remove user-group.

    Inputs:
      group_name: string of group name
      user_name: string of user name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveUserGroupAssignment')
    assignment_dict = self.db_instance.GetEmptyRowDict('user_group_assignments')
    assignment_dict['user_group_assignments_group_name'] = group_name
    assignment_dict['user_group_assignments_user_name'] = user_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('user_group_assignments',
                                               assignment_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      return row_count
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveUserGroupAssignments',
                                  u'user_name: %s group_name: %s' % (
                                      user_name, group_name), success)

  def ListACLs(self, acl_name=None, cidr_block=None, range_allowed=None):
    """List one or many acls, if all args are none it will them all, or just
    search on one more terms.

    Inputs:
      acl_name: string of acl name
      cidr_block: string of valid CIDR block or IP address
      range_allowed: integer boolean of if the acl is allowing or disallowing
                     the ip range

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      dictionary: keyed by the acl name whos value is a list dictionaries with
                  the cidr block and range allowed values.
        example: {'rfc_1918_networks':   [{'cidr_block': '192.168/16',
                                           'range_allowed': 1},
                                          {'cidr_block': '10/8',
                                           'range_allowed': 1}],
                  'university_networks': [{'cidr_block': '1.2.3/24',
                                           'range_allowed': 1},
                                          {'cidr_block': '1.1.1/24',
                                           'range_allowed': 0}]}
    """
    self.user_instance.Authorize('ListACLs')
    acl_dict = self.db_instance.GetEmptyRowDict('acls')
    acl_dict['acl_name'] = acl_name
    acl_dict['acl_cidr_block'] = cidr_block
    acl_dict['acl_range_allowed'] = range_allowed
    self.db_instance.StartTransaction()
    try:
      acls = self.db_instance.ListRow('acls', acl_dict)
    finally:
      self.db_instance.EndTransaction()

    acl_cidr_range_dict = {}
    for acl in acls:
      if( not acl_cidr_range_dict.has_key(acl['acl_name']) ):
        acl_cidr_range_dict[acl['acl_name']] = []
      acl_cidr_range_dict[acl['acl_name']].append(
          {'cidr_block': acl['acl_cidr_block'],
           'range_allowed': acl['acl_range_allowed']})

    return acl_cidr_range_dict

  def MakeACL(self, acl_name, cidr_block, range_allowed):
    """Makes an acl from args.

    Inputs:
      acl_name: string of acl name
      cidr_block: string of valid CIDR block or IP address
      range_allowed: integer boolean of if the acl is allowing or disallowing
                     the ip range

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeACL')
    acls_dict = {'acl_name': acl_name,
                 'acl_cidr_block': cidr_block,
                 'acl_range_allowed': range_allowed}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('acls', acls_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success  = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name, u'MakeACL',
                                  u'acl_name: %s cidr_block: %s '
                                  'range_allowed: %s' % (acl_name, cidr_block,
                                                         range_allowed),
                                  success)

  def RemoveACL(self, acl_name=None, cidr_block=None, range_allowed=None):
    """Removes an acl from args. Will also remove relevant acl-view assignments.

    Inputs:
      acl_name: string of acl name
      cidr_block: string of valid CIDR block or IP address
      range_allowed: integer boolean of if the acl is allowing or disallowing
                     the ip range

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveACL')
    acl_dict = {'acl_name': acl_name,
                'acl_cidr_block': cidr_block,
                'acl_range_allowed': range_allowed}
    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        found_acls = self.db_instance.ListRow('acls', acl_dict, lock_rows=True)
        if( found_acls ):
          for found_acl in found_acls:
            row_count += self.db_instance.RemoveRow('acls', found_acl)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveACL', u'acl_name: %s cidr_block: %s '
                                  'range_allowed: %s' % (acl_name, cidr_block,
                                                         range_allowed),
                                  success)
    return row_count

  def UpdateACL(self, search_acl_name=None, search_cidr_block=None,
                search_range_allowed=None, update_acl_name=None,
                update_cidr_block=None, update_range_allowed=None):
    """Updates an acl from search_dict with params in update_dict.

    Will also update any relevant acl-view assignments.

    It should be known that this table in the database is unique only on
    acl_name and cidr_block as a pair. What this means is that there are
    most likely multiple entries per acl_name and cidr_block.

    Inputs:
      search_acl_name: string of acl name to be modified
      search_cidr_block: string of valid CIDR block or IP address to be modified
      search_range_allowed: integer boolean of if the acl is allowing or
                            disallowing  the ip range to be modified
      update_acl_name: string of acl name to overwrite old value
      update_cidr_block: string of valid CIDR block or IP address to overwrite
                         old value
      update_range_allowed: integer boolean of if the acl is allowing or
                            disallowing the ip range to overwrite old value

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('UpdateACL')
    search_dict = {'acl_name': search_acl_name,
                   'acl_cidr_block': search_cidr_block,
                   'acl_range_allowed': search_range_allowed}
    update_dict = {'acl_name': update_acl_name,
                   'acl_cidr_block': update_cidr_block,
                   'acl_range_allowed': update_range_allowed}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.UpdateRow('acls', search_dict, update_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'UpdateACL', u'search_acl_name: %s '
                                  'search_cidr_block: %s search_range_allowed: '
                                  '%s update_acl_name: %s update_cidr_block: '
                                  '%s update_range_allowed %s' % (
                                      search_acl_name, search_cidr_block,
                                      search_range_allowed, update_acl_name,
                                      update_cidr_block, update_range_allowed),
                                  success)
    return row_count

  def ListDnsServers(self):
    """List dns servers.

    Raises:
      CoreError Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('ListDnsServers')
    dns_server_dict = self.db_instance.GetEmptyRowDict('dns_servers')
    self.db_instance.StartTransaction()
    try:
      dns_servers = self.db_instance.ListRow('dns_servers', dns_server_dict)
    finally:
      self.db_instance.EndTransaction()

    dns_server_list = []
    for dns_server in dns_servers:
      dns_server_list.append(dns_server['dns_server_name'])

    return dns_server_list

  def MakeDnsServer(self, dns_server_name):
    """Makes one dns server

    Inputs:
      dns_server_name: string of the dns server name
    Raises:
      CoreError: Raised for any internal problems
    """
    self.user_instance.Authorize('MakeDnsServer')
    dns_server_dict = self.db_instance.GetEmptyRowDict('dns_servers')
    dns_server_dict['dns_server_name'] = dns_server_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('dns_servers', dns_server_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeDnsServer', u'dns_server_name: %s' % (
                                      dns_server_name), success)

  def RemoveDnsServer(self, dns_server_name):
    """Removes dns server.

    Inputs:
      dns_server_name: string of dns server name

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveDnsServer')
    dns_server_dict = self.db_instance.GetEmptyRowDict('dns_servers')
    dns_server_dict['dns_server_name'] = dns_server_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('dns_servers', dns_server_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveDnsServer', u'dns_server_name: %s' % (
                                      dns_server_name), success)
    return row_count

  def UpdateDnsServer(self, search_dns_server_name, update_dns_server_name):
    """Updates dns server

    Inputs:
      search_dns_server_name: string of dns server name
      update_dns_server_name: new string of dns server name

    Raises:
      CoreError Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('UpdateDnsServer')
    search_dns_server_dict = self.db_instance.GetEmptyRowDict('dns_servers')
    search_dns_server_dict['dns_server_name'] = search_dns_server_name

    update_dns_server_dict = self.db_instance.GetEmptyRowDict('dns_servers')
    update_dns_server_dict['dns_server_name'] = update_dns_server_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.UpdateRow('dns_servers',
                                               search_dns_server_dict,
                                               update_dns_server_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'UpdateDnsServer',
                                  u'search_dns_server_name: %s '
                                  'update_dns_server_name: %s' % (
                                      search_dns_server_name,
                                      update_dns_server_name), success)

    return row_count

  def ListDnsServerSets(self):
    """List all dns server sets


    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
       list of dns server sets
    """
    self.user_instance.Authorize('ListDnsServerSets')
    dns_server_set_dict = self.db_instance.GetEmptyRowDict('dns_server_sets')
    self.db_instance.StartTransaction()
    try:
      dns_server_sets = self.db_instance.ListRow('dns_server_sets',
                                                 dns_server_set_dict)
    finally:
      self.db_instance.EndTransaction()

    dns_server_set_list = []
    for dns_server_set in dns_server_sets:
      dns_server_set_list.append(dns_server_set['dns_server_set_name'])

    return dns_server_set_list

  def MakeDnsServerSet(self, dns_server_set_name):
    """Make dns server set.

    Inputs:
      dns_server_set_name: string of dns server set name

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeDnsServerSet')
    dns_server_set_dict = self.db_instance.GetEmptyRowDict('dns_server_sets')
    dns_server_set_dict['dns_server_set_name'] = dns_server_set_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('dns_server_sets', dns_server_set_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeDnsServerSet',
                                  u'dns_server_set_name: %s' %
                                  dns_server_set_name, success)

  def RemoveDnsServerSet(self, dns_server_set_name):
    """Remove dns server set.

    Inputs:
      dns_server_set_name: string of dns server set name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveDnsServerSet')
    dns_server_set_dict = self.db_instance.GetEmptyRowDict('dns_server_sets')
    dns_server_set_dict['dns_server_set_name'] = dns_server_set_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('dns_server_sets',
                                               dns_server_set_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveDnsServerSet',
                                  u'dns_server_set_name: %s' %
                                  dns_server_set_name, success)
    return row_count

  def UpdateDnsServerSet(self, search_dns_server_set_name,
                         update_dns_server_set_name):
    """Update dns_server_set.

    Inputs:
      search_dns_server_set_name: string of dns_server_set name
      update_dns_server_set_name: string of dns_server_set name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('UpdateDnsServerSet')
    search_dns_server_set_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_sets')
    search_dns_server_set_dict[
        'dns_server_set_name'] = search_dns_server_set_name

    update_dns_server_set_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_sets')
    update_dns_server_set_dict[
        'dns_server_set_name'] = update_dns_server_set_name

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.UpdateRow('dns_server_sets',
                                               search_dns_server_set_dict,
                                               update_dns_server_set_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'UpdateDnsServerSet',
                                  u'search_dns_server_set_name: %s '
                                  'update_dns_server_set_name: %s' % (
                                      search_dns_server_set_name,
                                      update_dns_server_set_name),
                                  success)
    return row_count


  def ListDnsServerSetAssignments(self, dns_server_name=None,
                                  dns_server_set_name=None):
    """List dns server set assignments.
    Inputs:
      dns_server_name: string of dns server name
      dns_server_set_name: string of dns server set name

    Raises:
      CoreError: Raised for internal problems.

    Outputs:
      dictionary keyed by server sets.
    """
    self.user_instance.Authorize('ListDnsServerSetAssignments')
    assignment_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_assignments')
    assignment_dict['dns_server_set_assignments_dns_server_name'] = (
        dns_server_name)
    assignment_dict['dns_server_set_assignments_dns_server_set_name'] = (
        dns_server_set_name)
    self.db_instance.StartTransaction()
    try:
      assignments = self.db_instance.ListRow('dns_server_set_assignments',
                                             assignment_dict)
    finally:
      self.db_instance.EndTransaction()

    assignments_dict = {}
    for assignment in assignments:
      if( not assignment['dns_server_set_assignments_dns_server_set_name'] in
          assignments_dict ):
        assignments_dict[assignment[
            'dns_server_set_assignments_dns_server_set_name']] = []
      assignments_dict[assignment[
          'dns_server_set_assignments_dns_server_set_name']].append(
              assignment['dns_server_set_assignments_dns_server_name'])

    return assignments_dict

  def MakeDnsServerSetAssignments(self, dns_server_name, dns_server_set_name):
    """Make dns server set assignment.

    Inputs:
      dns_server_name: string of dns server name
      dns_server_set_name: string of dns server set name

    Raises:
      CoreError: Raised for internal problems.
    """
    self.user_instance.Authorize('MakeDnsServerSetAssignments')
    assignment_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_assignments')
    assignment_dict['dns_server_set_assignments_dns_server_name'] = (
        dns_server_name)
    assignment_dict['dns_server_set_assignments_dns_server_set_name'] = (
        dns_server_set_name)

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('dns_server_set_assignments', assignment_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeDnsServerSetAssignments',
                                  u'dns_server_name: %s '
                                  'dns_server_set_name: %s' % (
                                      dns_server_name, dns_server_set_name),
                                  success)

  def RemoveDnsServerSetAssignments(self, dns_server_name, dns_server_set_name):
    """Remove a dns server set assignment

    Inputs:
      dns_server_name: string of dns server name
      dns_server_set_name: string of dns server set name

    Raises:
      CoreError: Raised for internal problems.
    """
    self.user_instance.Authorize('RemoveDnsServerSetAssignments')
    assignment_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_assignments')
    assignment_dict['dns_server_set_assignments_dns_server_name'] = (
        dns_server_name)
    assignment_dict['dns_server_set_assignments_dns_server_set_name'] = (
        dns_server_set_name)

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('dns_server_set_assignments',
                                               assignment_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      return row_count
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveDnsServerSetAssignments',
                                  u'dns_server_name: %s '
                                  'dns_server_set_name: %s' % (
                                      dns_server_name, dns_server_set_name),
                                  success)

  def ListDnsServerSetViewAssignments(self, view_name=None,
                                      dns_server_set_name=None,
                                      key_by_view=False):
    """List dns server set view assignments

    Assignments can be given as a dictionary of dns server names with lists of
    view names or as a dictionary of view names with lists of dns server names.

    Raises:
      CoreError Raised for any internal problems.

    Outputs:
      Dictionary keyed by view name or dns server set name with values of
      lists of view names or dns server sets depending on key_by_view bool
        example keyed by view_name: {'view1': ['set1', 'set2'],
                                     'view2': ['set2']}
        example keyed by dns_server_set_name: {'set1': ['view1']
                                               'set2': ['view1', 'view2']}
    """
    self.user_instance.Authorize('ListDnsServerSetViewAssignments')
    assignment_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_view_assignments')
    assignment_dict['dns_server_set_view_assignments_view_name'] = (
        view_name)
    assignment_dict['dns_server_set_view_assignments_dns_server_set_name'] = (
        dns_server_set_name)

    self.db_instance.StartTransaction()
    try:
      assignments = self.db_instance.ListRow('dns_server_set_view_assignments',
                                             assignment_dict)
    finally:
      self.db_instance.EndTransaction()

    assignments_dict = {}
    for assignment in assignments:
      if( key_by_view ):
        if( not assignment['dns_server_set_view_assignments_view_name'] in
            assignments_dict ):
          assignments_dict[
              assignment['dns_server_set_view_assignments_view_name']] = []

        assignments_dict[
            assignment['dns_server_set_view_assignments_view_name']].append(
                assignment[
                    'dns_server_set_view_assignments_dns_server_set_name'])
      else:
         if( not assignment[
               'dns_server_set_view_assignments_dns_server_set_name'] in
               assignments_dict ):
           assignments_dict[
               assignment[
                   'dns_server_set_view_assignments_dns_server_set_name']] = []

         assignments_dict[assignment[
             'dns_server_set_view_assignments_dns_server_set_name']].append(
                 assignment['dns_server_set_view_assignments_view_name'])

    return assignments_dict

  def MakeDnsServerSetViewAssignments(self, view_name, dns_server_set_name):
    """Make dns server set view assignment

    Inputs:
      view_name: string of the view name
      dns_server_set_name: string of the dns server set name

    Raises:
      CoreError: Raised for any internal problems
    """
    self.user_instance.Authorize('MakeDnsServerSetViewAssignments')
    assignment_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_view_assignments')
    assignment_dict['dns_server_set_view_assignments_view_name'] = view_name
    assignment_dict['dns_server_set_view_assignments_dns_server_set_name'] = (
        dns_server_set_name)

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('dns_server_set_view_assignments',
                                 assignment_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeDnsServerSetViewAssignments',
                                  u'view_name: %s dns_server_set_name: %s' % (
                                      view_name, dns_server_set_name), success)

  def RemoveDnsServerSetViewAssignments(self, view_name, dns_server_set_name):
    """Remove dns server set view assignment

    Inputs:
      view_name: string of view name
      dns_server_set_name: string of dns server set name

    Raises:
      CoreError: Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveDnsServerSetViewAssignments')
    assignment_dict = self.db_instance.GetEmptyRowDict(
        'dns_server_set_view_assignments')
    assignment_dict['dns_server_set_view_assignments_view_name'] = view_name
    assignment_dict['dns_server_set_view_assignments_dns_server_set_name'] = (
        dns_server_set_name)

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow(
            'dns_server_set_view_assignments', assignment_dict)

      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      return row_count
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveDnsServerSetViewAssignments',
                                  u'view_name: %s dns_server_set_name: %s' % (
                                      view_name, dns_server_set_name), success)

  def ListViews(self, view_name=None):
    """Lists all views.

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      dictionary: dict keyed by view name with a value of the view args.
        example: {'view_1': 'also-notify {192.168.0.1;}\\nallow-transfer '
                            '{university_networks};;',
                  'view_2': 'other-arg { thing };'}
    """
    self.user_instance.Authorize('ListViews')
    view_dict = self.db_instance.GetEmptyRowDict('views')
    view_dict['view_name'] = view_name
    self.db_instance.StartTransaction()
    try:
      views = self.db_instance.ListRow('views', view_dict)
    finally:
      self.db_instance.EndTransaction()

    view_options_dict = {}
    for view in views:
      view_options_dict[view['view_name']] = view['view_options']

    return view_options_dict

  def MakeView(self, view_name, view_options=None):
    """Makes a view and all of the other things that go with a view.

    For more information about views please see docstring for
    MakeViewAssignments.

    Inputs:
      view_name: string of view name
      view_options: string of view options, defaults to empty string.
        for information on valid view options read:
          http://www.bind9.net/manual/bind/9.3.2/Bv9ARM.ch06.html#view_statement_grammar

    Raises:
      DnsCoreMgmtError  Raises on authorization or DB issues
    """
    self.user_instance.Authorize('MakeView')
    if( view_options is None ):
      view_options = u''

    views_dict = {'view_name': view_name,
                  'view_options': view_options}
    view_dep_name = '%s_dep' % view_name
    view_dependencies_dict = {'view_dependency': view_dep_name}
    view_dependency_assignments_dict = {
        'view_dependency_assignments_view_name': view_name,
        'view_dependency_assignments_view_dependency': view_dep_name}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('views', views_dict)
        self.db_instance.MakeRow('view_dependencies', view_dependencies_dict)
        self.db_instance.MakeRow('view_dependency_assignments',
                                 view_dependency_assignments_dict)

        view_dependency_assignments_dict[
          'view_dependency_assignments_view_dependency'] = u'any'
        self.db_instance.MakeRow('view_dependency_assignments',
                                 view_dependency_assignments_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeView', u'view_name: %s '
                                  'view_options: %s' % (
                                      view_name, view_options),
                                  success)

  def RemoveView(self, view_name):
    """Removes a view.

    Also removes anything attatched to that view. Including any information
    about a specific zone in the view and any records in that view.
    Please point gun away from foot.

    Inputs:
      view_name: string of view name

    Raises:
      DnsCoreMgmtError  Raises on authorization or DB issues

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveView')
    if( view_name == u'any' ):
      raise errors.CoreError('Cannot remove view any')
    search_view_dict = self.db_instance.GetEmptyRowDict('views')
    search_view_dict['view_name'] = view_name
    view_dep_dict = {'view_dependency': '%s_dep' % view_name}
    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        view_dict = self.db_instance.ListRow('views', search_view_dict,
                                             lock_rows=True)
        if( view_dict ):
          # view_name is unique in this table so no need to see if there are
          # multiple rows
          row_count += self.db_instance.RemoveRow('views', view_dict[0])
          row_count += self.db_instance.RemoveRow('view_dependencies',
                                                  view_dep_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveView', u'view_name: %s' % (view_name),
                                  success)
    return row_count

  def UpdateView(self, search_view_name, update_view_name=None,
                 update_view_options=None):
    """Updates a view.

    Also updates anything attatched to that view. Including any information
    about a specific zone in the view and any records in that view.

    Inputs:
      search_view_name: string of view name to be updated
      update_view_name: string of view name to update with
      update_view_options: string of view options, defaults to empty string.
        for information on valid view options read:
          http://www.bind9.net/manual/bind/9.3.2/Bv9ARM.ch06.html#view_statement_grammar

    Raises:
      DnsCoreMgmtError  Raises on authorization or DB issues
    """
    self.user_instance.Authorize('UpdateView')
    if( search_view_name == u'any' ):
      raise errors.CoreError('Cannot update view any')
    search_view_dict = self.db_instance.GetEmptyRowDict('views')
    search_view_dict['view_name'] = search_view_name
    search_view_dep_dict = {'view_dependency': '%s_dep' % search_view_name}
    update_view_dict = {'view_name': update_view_name,
                        'view_options': update_view_options}
    update_view_dep_dict = {'view_dependency': '%s_dep' % update_view_name}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.UpdateRow('views', search_view_dict,
                                               update_view_dict)
        row_count += self.db_instance.UpdateRow('view_dependencies',
                                                search_view_dep_dict,
                                                update_view_dep_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'UpdateView', u'search_view_name: %s '
                                  'update_view_name %s '
                                  'update_view_options %s' % (
                                      search_view_name, update_view_name,
                                      update_view_options),
                                  success)
    return row_count

  def ListViewAssignments(self, view_superset=None, view_subset=None):
    """Lists view assignments.

    For more informaton about view assignments please read the
    MakeViewAssignment docstring.

    Inputs:
      view_superset: string of view name
      view_subset: string of view name

    Raises:
      DnsCoreMgmtError  Raises on authorization or DB issues

    Outputs:
      dictionary keyed by view supersets with values lists of view subsets
    """
    self.user_instance.Authorize('ListViewAssignments')
    view_dependency_assignments_dict = self.db_instance.GetEmptyRowDict(
        'view_dependency_assignments')
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_dependency'] = view_subset
    if( view_subset is not None and view_subset != 'any'):
      view_dependency_assignments_dict[
          'view_dependency_assignments_view_dependency'] = ('%s_dep' %
                                                            view_subset)
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_name'] = view_superset
    self.db_instance.StartTransaction()
    try:
      view_assignments = self.db_instance.ListRow(
          'view_dependency_assignments', view_dependency_assignments_dict)
    finally:
      self.db_instance.EndTransaction()

    view_assignments_dict = {}
    for view_assignment in view_assignments:
      if( not view_assignment['view_dependency_assignments_view_name'] in
          view_assignments_dict ):
        view_assignments_dict[view_assignment[
            'view_dependency_assignments_view_name']] = []

      if( view_assignment[
          'view_dependency_assignments_view_dependency'].endswith('_dep') ):

        view_assignment[
            'view_dependency_assignments_view_dependency'] =  view_assignment[
                'view_dependency_assignments_view_dependency'][:-4:]

      view_assignments_dict[view_assignment[
          'view_dependency_assignments_view_name']].append(view_assignment[
              'view_dependency_assignments_view_dependency'])

    return view_assignments_dict

  def MakeViewAssignment(self, view_superset, view_subset):
    """Assigns a view to view.

    A view contains zones in that view. However zones can be assigned
    to another view that is a superset of views. For example
    an assignment can be made for view_a(view_superset) to also include
    all of view_b's(view_subset) zones(and by proxy, records). This
    prevents having to have duplicate records in each view.

    Most of the time this will not be needed as there is a special
    subset included in all views(unless explicitly deleted) called the
    'any' view. Records in the 'any' view will be in all views that
    have not been explicity changed to remove the 'any' view.

    The 'any' view subset is automatically tied to a view when a
    view is created. Also this is the default view for records
    and zones(again it can be explicitly changed if needed).

    Inputs:
      view_superset: string of view name
      view_subset: string of view name

    Raises:
      DnsCoreMgmtError  Raises on authorization or DB issues
    """
    self.user_instance.Authorize('MakeViewAssignment')
    view_dependency_assignments_dict = {
        'view_dependency_assignments_view_name': view_superset,
        'view_dependency_assignments_view_dependency': '%s_dep' % view_subset}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('view_dependency_assignments',
                                 view_dependency_assignments_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeViewAssignment', u'view_superset: %s '
                                  'view_subset: %s' % (view_superset,
                                                        view_subset), success)

  def RemoveViewAssignment(self, view_superset, view_subset):
    """Removes a view assignment.

    For more informaton about view assignments please read the
    MakeViewAssignment docstring.

    Inputs:
      view_superset: string of view name
      view_subset: string of view name

    Raises:
      DnsCoreMgmtError  Raises on authorization or DB issues
    """
    self.user_instance.Authorize('RemoveViewAssignment')
    view_dependency_assignments_dict = {
        'view_dependency_assignments_view_name': view_superset,
        'view_dependency_assignments_view_dependency': '%s_dep' % view_subset}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('view_dependency_assignments',
                                               view_dependency_assignments_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                   u'RemoveViewAssignemnt',
                                   u'view_superset: %s view_subset %s' % (
                                        view_superset, view_subset), success)
    return row_count

  def ListViewToACLAssignments(self, view_name=None, acl_name=None):
    """Lists some or all view to acl assignments corresponding to the
    given args.

    Inputs:
      view_name: string of view name
      acl_name: string of acl name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      list: list contains dictionaries of assignments
        example: [{'view_name': 'main_view', 'acl_name': 'internal'},
                  {'view_name': 'other_view', 'acl_name': 'external'}]
    """
    self.user_instance.Authorize('ListViewToACLAssignments')
    view_acl_assign_dict = {
        'view_acl_assignments_acl_name': acl_name,
        'view_acl_assignments_view_name': view_name}
    self.db_instance.StartTransaction()
    try:
      view_acl_assignments = self.db_instance.ListRow('view_acl_assignments',
                                                      view_acl_assign_dict)
    finally:
      self.db_instance.EndTransaction()

    assignments_dicts = []
    for view_acl_assignment in view_acl_assignments:
      assignments_dict = {}
      assignments_dict['view_name'] = view_acl_assignment[
          'view_acl_assignments_view_name']
      assignments_dict['acl_name'] = view_acl_assignment[
          'view_acl_assignments_acl_name']
      assignments_dicts.append(assignments_dict)

    return assignments_dicts

  def MakeViewToACLAssignments(self, view_name, acl_name):
    """Makes view to acl assignment

    Inputs:
      view_name: string of view name
      acl_name: string of acl name

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeViewToACLAssignments')
    view_acl_assign_dict = {
        'view_acl_assignments_acl_name': acl_name,
        'view_acl_assignments_view_name': view_name}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('view_acl_assignments', view_acl_assign_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeViewToACLAssignments', u'view_name %s '
                                  'acl_name %s' % (view_name, acl_name),
                                  success)

  def RemoveViewToACLAssignments(self, view_name, acl_name):
    """Removes view to acl assignment

    Inputs:
      view_name: string of view name
      acl_name: string of acl name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveViewToACLAssignments')
    view_acl_assign_dict = {
        'view_acl_assignments_acl_name': acl_name,
        'view_acl_assignments_view_name': view_name}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('view_acl_assignments',
                                               view_acl_assign_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveViewToACLAssignments',
                                  u'view_name: %s acl_name: %s' % (view_name,
                                                                   acl_name),
                                  success)
    return row_count

  def ListZones(self, zone_name=None, zone_type=None, zone_origin=None,
                view_name=None):
    """Lists zones.

    Inputs:
      zone_name: string of zone name
      zone_type: string of zone type
      zone_origin: string of zone origin. ex dept.univiersity.edu.
      view_name: string of view name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      Dictionary of dictionaries. The parent dictionary is keyed by zone name,
      the secondary dictionary is keyed by view name and the third is keyed
      by type of data.
        example:
          {'zone.university.edu': {'internal': {'zone_type': 'master',
                                                'zone_options': 'misc opts',
                                                'zone_origin':
                                                    'university.edu.'},
                                   'any': {'zone_type': 'master'
                                           'zone_options': 'other options',
                                           'zone_origin': 'university.edu.'}},
           'otherzone.university.edu': {'any': {'zone_type': 'slave',
                                                'zone_options': 'options'}}}

    """
    self.user_instance.Authorize('ListZones')
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')

    if( view_name is not None and view_name != u'any' ):
      view_name = '%s_dep' % view_name

    zone_view_assignments_dict['zone_view_assignments_zone_name'] =  zone_name
    zone_view_assignments_dict['zone_view_assignments_zone_type'] =  zone_type
    zone_view_assignments_dict['zone_origin'] =  zone_origin
    zone_view_assignments_dict[
        'zone_view_assignments_view_dependency'] = view_name

    self.db_instance.StartTransaction()
    try:
      zone_view_assignment_rows = self.db_instance.ListRow(
          'zone_view_assignments', zone_view_assignments_dict)
    finally:
      self.db_instance.EndTransaction()

    zone_view_assignments = {}
    for row in zone_view_assignment_rows:
      if( not row['zone_view_assignments_zone_name'] in zone_view_assignments ):
         zone_view_assignments[row['zone_view_assignments_zone_name']] = {}

      if( not row['zone_view_assignments_view_dependency'].replace('_dep', '')
          in zone_view_assignments[row['zone_view_assignments_zone_name']] ):
        zone_view_assignments[row['zone_view_assignments_zone_name']][
            row['zone_view_assignments_view_dependency'].replace(
                '_dep', '')] = {}

      zone_view_assignments[row['zone_view_assignments_zone_name']][
          row['zone_view_assignments_view_dependency'].replace('_dep', '')] = (
              {'zone_type': row['zone_view_assignments_zone_type'],
               'zone_options': row['zone_options'],
               'zone_origin': row['zone_origin']})

    return zone_view_assignments

  def MakeZone(self, zone_name, zone_type, zone_origin, view_name=None,
               zone_options=None, make_any=True):
    """Makes a zone.

    Inputs:
      zone_name: string of zone name
      zone_type: string of zone type
      zone_origin: string of zone origin. ex dept.univiersity.edu.
      zone_options: string of zone_options(defaults to empty string)
                    valid zone options can be found here:
                      http://www.bind9.net/manual/bind/9.3.2/Bv9ARM.ch06.html#zone_statement_grammar
      view_name: string of view name(defaults to 'any')
                 see docstring of MakeViewAssignments as to why 'any' is default
      make_any: regardless of view name, make any as well(default to True)

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeZone')
    if( zone_options is None ):
      zone_options = u''
    if( view_name is None ):
      view_name = u'any'
    else:
      view_name = '%s_dep' % view_name

    zone_dict = {'zone_name': zone_name}
    zone_view_assignments_dict = {
        'zone_view_assignments_zone_name': zone_name,
        'zone_view_assignments_view_dependency': view_name,
        'zone_view_assignments_zone_type': zone_type,
        'zone_origin': zone_origin,
        'zone_options': zone_options}

    search_any_dict = self.db_instance.GetEmptyRowDict('zone_view_assignments')
    search_any_dict['zone_view_assignments_view_dependency'] = u'any'
    search_any_dict['zone_view_assignments_zone_name'] = zone_name
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        if( not self.db_instance.ListRow('zones', zone_dict) ):
          self.db_instance.MakeRow('zones', zone_dict)
        self.db_instance.MakeRow('zone_view_assignments',
                                 zone_view_assignments_dict)
        if( view_name != u'any' and make_any ):
          if( not self.db_instance.ListRow('zone_view_assignments',
                                           search_any_dict) ):
            zone_view_assignments_dict[
                'zone_view_assignments_view_dependency'] = u'any'
            self.db_instance.MakeRow('zone_view_assignments',
                                     zone_view_assignments_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeZone', u'zone_name: %s zone_type: %s '
                                  'zone_origin: %s view_name: %s '
                                  'zone_options: %s make_any %s' % (
                                      zone_name, zone_type, zone_origin,
                                      view_name, zone_options, make_any),
                                  success)

  def RemoveZone(self, zone_name, view_name=None):
    """Removes a zone.

    Inputs:
      zone_name: string of zone name
      view_name: string of view name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows affected
    """
    self.user_instance.Authorize('RemoveZone')
    zone_dict = {'zone_name': zone_name}
    zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = zone_name

    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        zone_assignments_by_name = self.db_instance.ListRow(
            'zone_view_assignments', zone_view_assignments_dict)

        if( view_name is None or len(zone_assignments_by_name) <= 1 ):
          # Because of cascading deletes this should remove anything in the
          # zone_view_assignments table as well
          row_count += self.db_instance.RemoveRow('zones', zone_dict)
        else:
          zone_view_assignments_dict[
              'zone_view_assignments_view_dependency'] = '%s_dep' % view_name
          # Because zone_name/zone_view together are uniquely constrained in
          # this table no need to check if there are more than one.
          found_zone_assignment = self.db_instance.ListRow(
              'zone_view_assignments', zone_view_assignments_dict,
              lock_rows=True)
          if( found_zone_assignment ):
            row_count += self.db_instance.RemoveRow('zone_view_assignments',
                                                    found_zone_assignment[0])
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveZone', u'zone_name: %s '
                                  'view_name: %s' % (zone_name, view_name),
                                  success)
    return row_count

  def UpdateZone(self, search_zone_name, search_view_name=None,
                 update_zone_name=None, update_zone_options=None,
                 update_zone_type=None):
    """Updates zone options or zone type of zone

    Inputs:
      search_zone_name: string of zone name
      search_view_name: string of view name
      update_zone_name: string of zone name
      update_zone_type: string of zone type
      update_zone_options: string of zone options
                           valid zone options can be found here:
                             http://www.bind9.net/manual/bind/9.3.2/Bv9ARM.ch06.html#zone_statement_grammar

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows affected
    """
    self.user_instance.Authorize('UpdateZone')

    if( search_view_name is not None and search_view_name != u'any' ):
      search_view_name = '%s_dep' % search_view_name

    search_zone_dict = {'zone_name': search_zone_name}
    update_zone_dict = {'zone_name': update_zone_name}

    search_zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    search_zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        search_zone_name)
    search_zone_view_assignments_dict[
        'zone_view_assignments_view_dependency'] = search_view_name

    update_zone_view_assignments_dict = self.db_instance.GetEmptyRowDict(
        'zone_view_assignments')
    update_zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        update_zone_name)
    update_zone_view_assignments_dict['zone_view_assignments_zone_type'] = (
        update_zone_type)
    update_zone_view_assignments_dict['zone_options'] = update_zone_options
    success = False
    try:
      self.db_instance.StartTransaction()
      row_count = 0
      try:
        if( update_zone_name is not None and search_view_name is None ):
          row_count += self.db_instance.UpdateRow('zones', search_zone_dict,
                                                  update_zone_dict)
        row_count += self.db_instance.UpdateRow(
            'zone_view_assignments',search_zone_view_assignments_dict,
            update_zone_view_assignments_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'UpdateZone', u'search_zone_name: %s '
                                  'search_view_name: %s update_zone_name: %s '
                                  'update_zone_type: %s '
                                  'update_zone_options %s' % (
                                      search_zone_name, search_view_name,
                                      update_zone_name, update_zone_type,
                                      update_zone_options),
                                  success)
    return row_count

  def ListReverseRangeZoneAssignments(self, zone_name=None, cidr_block=None):
    """Lists reverse range to zone assignments.

    Inputs:
      zone_name: string of zone name
      cidr_block: string of cidr block

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      dictionary: keyed by zone_name with values of cidr blocks
        example: {'10.in-addr.arpa': '10/8',
                  '9.168.192.in-addr.arpa': '192.168.9/24'}
    """
    self.user_instance.Authorize('ListReverseRangeZoneAssignments')
    assignment_dict = {'reverse_range_zone_assignments_zone_name': zone_name,
                       'reverse_range_zone_assignments_cidr_block': cidr_block}

    self.db_instance.StartTransaction()
    try:
      assignment_rows = self.db_instance.ListRow(
          'reverse_range_zone_assignments', assignment_dict)
    finally:
      self.db_instance.EndTransaction()

    reverse_range_dict = {}
    for row in assignment_rows:
      reverse_range_dict[row['reverse_range_zone_assignments_zone_name']] = (
          row['reverse_range_zone_assignments_cidr_block'])

    return reverse_range_dict

  def MakeReverseRangeZoneAssignment(self, zone_name, cidr_block):
    """Makes a reverse range to zone assignment.

    Inputs:
      zone_name: string of zone name
      cidr_block: string of cidr block

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeReverseRangeZoneAssignment')
    assignment_dict = {'reverse_range_zone_assignments_zone_name': zone_name,
                       'reverse_range_zone_assignments_cidr_block': cidr_block}

    self.db_instance.StartTransaction()
    try:
      self.db_instance.MakeRow('reverse_range_zone_assignments',
                               assignment_dict)
    except:
      self.db_instance.EndTransaction(rollback=True)
      raise

    self.db_instance.EndTransaction()

  def RemoveReverseRangeZoneAssignment(self, zone_name, cidr_block):
    """Remove reverse range to zone assignment.

    Inputs:
      zone_name: string of zone name
      cidr_block: string of cidr block

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows affected
    """
    self.user_instance.Authorize('RemoveReverseRangeZoneAssignment')
    assignment_dict = {'reverse_range_zone_assignments_zone_name': zone_name,
                       'reverse_range_zone_assignments_cidr_block': cidr_block}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('reverse_range_zone_assignments',
                                               assignment_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveReverseRangeZoneAssignment',
                                  u'zone_name: %s cidr_block %s' % (zone_name,
                                                                    cidr_block),
                                  success)
    return row_count

  def ListForwardZonePermissions(self, zone_name=None, group_name=None,
                                 access_right=None):
    """List forward zone permisions.

    Inputs:
      zone_name: string of zone name
      group_name: string of group name
      access_right: string of access rights defined as constants.ACCESS_RIGHTS

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      dictionary keyed by group name with values of lists of dictionaries
      containing zone names and access rights
        example: {'dept': [{'zone_name': 'sub.univeristy.edu',
                            'access_right': 'rw'},
                           {'zone_name': 'othersub.university.edu',
                            'access_right': 'r'}],
                  'otherdept': [{'zone_name': 'sub.university.edu',
                                 'access_right': 'rw'}]}
    """
    self.user_instance.Authorize('ListForwardZonePermissions')
    permissions_dict = {'forward_zone_permissions_group_name': group_name,
                        'forward_zone_permissions_zone_name': zone_name,
                        'forward_zone_permissions_access_right': access_right}

    self.db_instance.StartTransaction()
    try:
      permission_rows = self.db_instance.ListRow('forward_zone_permissions',
                                                 permissions_dict)
    finally:
      self.db_instance.EndTransaction()

    forward_zone_perms_dict = {}
    for row in permission_rows:
      if( not row['forward_zone_permissions_group_name'] in
          forward_zone_perms_dict ):
        forward_zone_perms_dict[
            row['forward_zone_permissions_group_name']] = []

      forward_zone_perms_dict[
          row['forward_zone_permissions_group_name']].append(
              {'zone_name': row['forward_zone_permissions_zone_name'],
               'access_right': row['forward_zone_permissions_access_right']})

    return forward_zone_perms_dict

  def MakeForwardZonePermission(self, zone_name, group_name, access_right):
    """Make forward zone permision.

    Inputs:
      zone_name: string of zone name
      group_name: string of group name
      access_right: string of access rights defined as constants.ACCESS_RIGHTS

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeForwardZonePermission')
    permissions_dict = {'forward_zone_permissions_group_name': group_name,
                        'forward_zone_permissions_zone_name': zone_name,
                        'forward_zone_permissions_access_right': access_right}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('forward_zone_permissions',
                                 permissions_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeForwardZonePermission',
                                  u'zone_name: %s group_name: %s '
                                  'access_right: %s' % (zone_name, group_name,
                                                        access_right), success)

  def RemoveForwardZonePermission(self, zone_name, group_name, access_right):
    """Remove forward zone permisions.

    Inputs:
      zone_name: string of zone name
      group_name: string of group name
      access_right: string of access rights defined as constants.ACCESS_RIGHTS

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows affected
    """
    self.user_instance.Authorize('RemoveForwardZonePermission')
    permissions_dict = {'forward_zone_permissions_group_name': group_name,
                        'forward_zone_permissions_zone_name': zone_name,
                        'forward_zone_permissions_access_right': access_right}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('forward_zone_permissions',
                                               permissions_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveForwardZonePermission',
                                  u'zone_name: %s group_name %s '
                                  'access_right: %s' % (zone_name, group_name,
                                                        access_right), success)
    return row_count


  def ListReverseRangePermissions(self, cidr_block=None, group_name=None,
                                 access_right=None):
    """List reverse range permisions.

    Inputs:
      cidr_block: string of cidr block
      group_name: string of group name
      access_right: string of access rights defined as constants.ACCESS_RIGHTS

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      dictionary keyed by group name with values of lists of dictionaries
      containing reverse ranges and access rights
        example: {'dept': [{'cidr_block': '192.168.0/24',
                            'access_right': 'rw'},
                           {'cidr_block': '192.168.1/24',
                            'access_right': 'r'}],
                  'otherdept': [{'cidr_block': '192.168.1/24',
                                 'access_right': 'rw'}]}
    """
    self.user_instance.Authorize('ListReverseRangePermissions')
    permissions_dict = {'reverse_range_permissions_group_name': group_name,
                        'reverse_range_permissions_cidr_block': cidr_block,
                        'reverse_range_permissions_access_right': access_right}

    self.db_instance.StartTransaction()
    try:
      permission_rows = self.db_instance.ListRow('reverse_range_permissions',
                                                 permissions_dict)
    finally:
      self.db_instance.EndTransaction()

    reverse_range_perms_dict = {}
    for row in permission_rows:
      if( not row['reverse_range_permissions_group_name'] in
          reverse_range_perms_dict ):
        reverse_range_perms_dict[
            row['reverse_range_permissions_group_name']] = []

      reverse_range_perms_dict[
          row['reverse_range_permissions_group_name']].append(
              {'zone_name': row['reverse_range_permissions_cidr_block'],
               'access_right': row['reverse_range_permissions_access_right']})

    return reverse_range_perms_dict

  def MakeReverseRangePermission(self, cidr_block, group_name, access_right):
    """Make reverse range permisions.

    Inputs:
      cidr_block: string of cidr block
      group_name: string of group name
      access_right: string of access rights defined as constants.ACCESS_RIGHTS

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeReverseRangePermission')
    permissions_dict = {'reverse_range_permissions_group_name': group_name,
                        'reverse_range_permissions_cidr_block': cidr_block,
                        'reverse_range_permissions_access_right': access_right}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('reverse_range_permissions',
                                 permissions_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeReverseRangePermission',
                                  u'cidr_block: %s group_name: %s '
                                  'access_right: %s' % (cidr_block, group_name,
                                                        access_right), success)

  def RemoveReverseRangePermission(self, cidr_block, group_name, access_right):
    """Remove reverse range permisions.

    Inputs:
      cidr_block: string of cidr block
      group_name: string of group name
      access_right: string of access rights defined as constants.ACCESS_RIGHTS

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows affected
    """
    self.user_instance.Authorize('RemoveReverseRangePermission')
    permissions_dict = {'reverse_range_permissions_group_name': group_name,
                        'reverse_range_permissions_cidr_block': cidr_block,
                        'reverse_range_permissions_access_right': access_right}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.RemoveRow('reverse_range_permissions',
                                               permissions_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveReverseRangePermission',
                                  u'cidr_block: %s group_name: %s '
                                  'access_right: %s' % (cidr_block, group_name,
                                                        access_right), success)
    return row_count

  def GetEmptyRecordArgsDict(self, record_type):
    """Gets record args dict for the record_type.

    Inputs:
      record_type: string of record type (example: u'mx')

    Outputs:
      dictionary: which is different for each record type.
                 (example: {u'priority': 10,
                            u'mail_server': 'mail.sub.university.edu.'})
    """
    return self.db_instance.GetEmptyRecordArgsDict(record_type)

  def ListRecords(self, record_type=None, target=None, zone_name=None,
                  view_name=None, ttl=None, record_args_dict={}):
    """Lists records.

    Inputs:
      record_type: string of record type (example: u'mx')
      target: string of target (example u'machine-01.sub.univeristy.edu.')
      zone_name: string of zone name (example u'sub.university.edu')
      ttl: int of time to live per record
      view_name: string of view name (example u'internal')
      record_args_dict: dictionary, which is different for each record type.
                        an example dictionary can be obtained with the
                        GetEmptyRecordArgsDict function in this class
                        (example: {u'priority': 10,
                                   u'mail_server': 'mail.sub.university.edu.'})

    Outputs:
      list of record dictionaries
        Each dictionary can have different args depending on record type.
        All of them will include record_type, target, zone_name, ttl, and
        view_name regardless of record type. Below is an example of an mx
        record search.
        example: [{'record_type': 'mx', 'target': 'university.edu.',
                   'zone_name': 'university.edu', ttl: 3600,
                   'view_name': 'external', 'priority': 10,
                   'mail_server': 'smtp-01.university.edu.',
                   'last_user': 'sharrell},
                  {'record_type': 'mx', 'target': 'university.edu.',
                   'zone_name': 'university.edu', ttl: 3600,
                   'view_name': 'external', 'priority': 20,
                   'mail_server': 'smtp-02.university.edu.'},
                   'last_user': 'sharrell}]
    """
    self.user_instance.Authorize('ListRecords', target=target)
    if( view_name is not None and view_name != u'any' and not
          view_name.endswith('_dep') ):
      view_name = '%s_dep' % view_name
    records_dict = self.db_instance.GetEmptyRowDict('records')
    record_args_assignment_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments_records_assignments')
    records_dict['record_type'] =  record_type
    records_dict['record_target'] = target
    records_dict['record_ttl'] = ttl
    records_dict['record_zone_name'] = zone_name
    records_dict['record_view_dependency'] =  view_name

    if( record_args_dict ):
      if( record_type is None ):
        raise RecordError('Must specify record_type with record_args_dict')
      self.db_instance.ValidateRecordArgsDict(record_type, record_args_dict,
                                              none_ok=True)
    else:
      record_args_dict = {}



    self.db_instance.StartTransaction()
    try:
      records = self.db_instance.ListRow('records', records_dict,
                                         'record_arguments_records_assignments',
                                         record_args_assignment_dict)
    finally:
      self.db_instance.EndTransaction()

    full_record_dicts = {}
    del_id_list = []
    for record in records:
      if( record['record_arguments_records_assignments_argument_name'] in
          record_args_dict and 
          record_args_dict[record[
              'record_arguments_records_assignments_argument_name']] is 
          not None and
          unicode(record_args_dict[record[
            'record_arguments_records_assignments_argument_name']]) !=
          record['argument_value'] ):
        del_id_list.append(record['records_id'])

      if( not record['record_arguments_records_assignments_record_id'] in
          full_record_dicts ):
        full_record_dicts[
            record['record_arguments_records_assignments_record_id']] = {}

        full_record_dicts[
            record['record_arguments_records_assignments_record_id']][
                'record_type'] = record['record_type']

        full_record_dicts[
            record['record_arguments_records_assignments_record_id']][
                'zone_name'] = record['record_zone_name']
        if( record['record_view_dependency'].endswith('_dep') ):
          record['record_view_dependency'] = record[
              'record_view_dependency'][:-4:]
        full_record_dicts[
            record['record_arguments_records_assignments_record_id']][
                'view_name'] = record['record_view_dependency']

        full_record_dicts[
            record['record_arguments_records_assignments_record_id']][
                'target'] = record['record_target']

        full_record_dicts[
            record['record_arguments_records_assignments_record_id']][
                'ttl'] = record['record_ttl']

        full_record_dicts[
            record['record_arguments_records_assignments_record_id']][
                'last_user'] = record['record_last_user']

      if( record['argument_value'].isdigit() ):
        record['argument_value'] = int(record['argument_value'])

      full_record_dicts[
          record['record_arguments_records_assignments_record_id']][record[
              'record_arguments_records_assignments_argument_name']] = record[
              'argument_value']
    for record_id in set(del_id_list):
      del full_record_dicts[record_id]

    return full_record_dicts.values()

  def MakeRecord(self, record_type, target, zone_name, record_args_dict,
                 view_name=None, ttl=None):
    """Makes a record.

    Raises:
      CoreError  Raised for any internal problems.

    Inputs:
      record_type: string of record type (example: u'mx')
      target: string of target (example u'machine-01')
      zone_name: string of zone name (example u'sub.university.edu')
      ttl: int of time to live per record
      view_name: string of view name (example u'internal')
      record_args_dict: dictionary, which is different for each record type.
                        an example dictionary can be obtained with the
                        GetEmptyRecordArgsDict function in this class
                        (example: {u'priority': 10,
                                   u'mail_server': 'mail.sub.university.edu.'})
    """
    self.user_instance.Authorize('MakeRecord', target=target)
    self.db_instance.ValidateRecordArgsDict(record_type, record_args_dict)
    if( view_name is None or view_name == u'any'):
      view_name = u'any'
    else:
      view_name = '%s_dep' % view_name

    if( ttl is None ):
      ttl = constants.DEFAULT_TTL

    records_dict = {'records_id': None,
                    'record_target': target,
                    'record_type': None,
                    'record_ttl': ttl,
                    'record_zone_name': zone_name,
                    'record_view_dependency': view_name,
                    'record_last_user': self.user_instance.GetUserName()}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        if( record_type == 'a' or record_type == 'cname' ):
          current_records = self.db_instance.ListRow('records', records_dict)
          for record in current_records:
            if( (record['record_type'] == 'a' and record_type == 'cname') or
                record['record_type'] == 'cname' ):
              raise RecordError('Record already exists with that target '
                                'target: %s type: %s' %
                                (record['record_type'],
                                 record['record_target']))

        records_dict['record_type'] = record_type
        record_id = self.db_instance.MakeRow('records', records_dict)
        for k in record_args_dict.keys():
          record_argument_assignments_dict = {
             'record_arguments_records_assignments_record_id': record_id,
             'record_arguments_records_assignments_type': record_type,
             'record_arguments_records_assignments_argument_name': k,
             'argument_value': unicode(record_args_dict[k])}
          self.db_instance.MakeRow('record_arguments_records_assignments',
                                   record_argument_assignments_dict)
        if( record_type != u'soa' ):
          self._IncrementSoa(view_name, zone_name)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeRecord', u'record_type: %s target: %s '
                                  'zone_name: %s record_args_dict: %s '
                                  'view_name: %s ttl: %s' % (record_type,
                                                             target, zone_name,
                                                             record_args_dict,
                                                             view_name, ttl),
                                  success)

  def UpdateRecord(self, search_record_type, search_target, search_zone_name,
                   search_record_args_dict, search_view_name=None,
                   search_ttl=None, update_target=None, update_zone_name=None,
                   update_record_args_dict={}, update_view_name=None,
                   update_ttl=None):
    """Update record.

    Inputs:
      search_record_type: type of record
      search_target: target
      search_zone_name: name of zone
      search_record_args_dict: dictionary of record arguments
      search_view_name: name of view
      search_ttl: time to live
      update_target: target
      update_zone_name: name of zone
      update_record_args_dict: dictionary of record arguments
      update_view_name: name of view
      update_ttl: time to live

    Raises:
      CoreError Raised for any internal problems.
    """
    self.user_instance.Authorize('UpdateRecord', target=search_target)
    self.user_instance.Authorize('UpdateRecord', target=update_target)

    search_records_dict = self.db_instance.GetEmptyRowDict('records')
    search_records_dict['record_type'] = search_record_type
    search_records_dict['record_zone_name'] = search_zone_name
    if( search_view_name is None ):
      search_view_name = u'any'
    if( not search_view_name.endswith('_dep') and search_view_name != u'any'):
      search_view_name = '%s_dep' % search_view_name
    search_records_dict['record_view_dependency'] = search_view_name
    search_records_dict['record_ttl'] = search_ttl
    search_args_list = []

    self.db_instance.ValidateRecordArgsDict(search_record_type, 
                                            search_record_args_dict,
                                            none_ok=True)

    for search_argument in search_record_args_dict:
      if( search_record_args_dict[search_argument] is None ):
        continue
      search_args_list.append(
          {u'record_arguments_records_assignments_argument_name':
              search_argument,
           u'record_arguments_records_assignments_type': search_record_type,
           u'argument_value': unicode(search_record_args_dict[search_argument]),
           u'record_arguments_records_assignments_record_id': None})

    update_records_dict = self.db_instance.GetEmptyRowDict('records')
    update_records_dict['record_target'] = update_target
    update_records_dict['record_zone_name'] = update_zone_name
    update_records_dict['record_view_dependency'] = update_view_name
    update_records_dict['record_ttl'] = update_ttl
    update_args_list = []

    if( update_record_args_dict ):
      self.db_instance.ValidateRecordArgsDict(search_record_type, 
                                              update_record_args_dict,
                                              none_ok=True)

    for update_argument in update_record_args_dict:
      if( update_record_args_dict[update_argument] is None ):
        continue
      update_args_list.append(
          {u'record_arguments_records_assignments_argument_name':
              update_argument,
           u'record_arguments_records_assignments_type': search_record_type,
           u'argument_value': unicode(update_record_args_dict[update_argument]),
           u'record_arguments_records_assignments_record_id': None})

    success = False
    try:
      self.db_instance.StartTransaction()
      row_count = 0
      try:
        if( update_target is not None and update_target != search_target and
            (search_record_type == 'a' or search_record_type == 'cname') ):
          current_records = self.db_instance.ListRow('records',
                                                     update_records_dict)      
          for record in current_records:
            if( (record['record_type'] == 'a' and search_record_type == 'cname')
                or record['record_type'] == 'cname' ):
              raise RecordError('Record already exists with that '
                                'target type: %s target: %s' %
                                (record['record_type'],
                                 record['record_target']))
        args_search_list = []
        record_ids = []
        final_id = []
        record_id_dict = {}
        for arg in search_args_list:
          args_search_list.append(self.db_instance.ListRow(
              'record_arguments_records_assignments', arg))
        for index, search_record_args in enumerate(args_search_list):
          record_ids.append([])
          for search_args_dict in search_record_args:
            record_ids[index].append(search_args_dict[
                u'record_arguments_records_assignments_record_id'])
        for id_list in record_ids:
          for search_id in id_list:
            if( search_id in record_id_dict ):
              record_id_dict[search_id] += 1
            else:
              record_id_dict[search_id] = 1
        for record_id in record_id_dict:
          if( record_id_dict[record_id] == len(search_args_list) ):
            final_id.append(record_id)
        if( len(final_id) == 0 ):
          raise errors.CoreError('No records found.')
        elif( len(final_id) == 1 ):
          search_records_dict['records_id'] = final_id[0]
          new_records = self.db_instance.ListRow('records',
                                                 search_records_dict)
          row_count += self.db_instance.UpdateRow('records', new_records[0],
                                                  update_records_dict)
          for update_args in update_args_list:
            for search_args in search_args_list:
              if( search_args[
                  'record_arguments_records_assignments_argument_name'] == (
                      update_args[
                  'record_arguments_records_assignments_argument_name']) ):
                row_count += self.db_instance.UpdateRow(
                    'record_arguments_records_assignments',
                    search_args, update_args)
        else:
          raise errors.CoreError('Duplicate records found.')
        if( update_view_name is None ):
          update_view_name = search_view_name
        if( update_zone_name is None ):
          update_zone_name = search_zone_name
        self._IncrementSoa(update_view_name, update_zone_name)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(
          self.user_instance.user_name, u'UpdateRecord',
          u'search_record_type: %s search_target: %s update_target %s '
           'search_zone_name: %s update_zone_name: %s '
           'search_record_args_dict: %s update_record_args_dict: %s '
           'search_view_name: %s update_view_name %s' % (
               search_record_type, search_target, update_target,
               search_zone_name, update_zone_name, search_record_args_dict,
               update_record_args_dict, search_view_name, update_view_name),
           success)

  def RemoveRecord(self, record_type, target, zone_name, record_args_dict,
                   view_name, ttl=None):
    """Remove record.

    Inputs:
      record_type: type of record
      target: target name
      zone_name: name of zone
      record_args_dict: dictionary of record arguments
      view_name: name of view
      ttl: time to live

    Raises:
      CoreError Raised for any internal problems.
    """
    self.user_instance.Authorize('RemoveRecord', target=target)
    records_dict = self.db_instance.GetEmptyRowDict('records')
    records_dict['record_type'] = record_type
    records_dict['record_target'] = target
    records_dict['record_zone_name'] = zone_name
    if( not view_name.endswith('_dep') and view_name != u'any'):
      view_name = '%s_dep' % view_name
    records_dict['record_view_dependency'] = view_name
    records_dict['record_ttl'] = ttl

    self.db_instance.ValidateRecordArgsDict(record_type, record_args_dict)

    args_list = []
    for argument in record_args_dict:
      args_list.append(
          {u'record_arguments_records_assignments_argument_name': argument,
           u'record_arguments_records_assignments_type': record_type,
           u'argument_value': unicode(record_args_dict[argument]),
           u'record_arguments_records_assignments_record_id': None})
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        args_search_list = []
        record_ids = []
        final_id = []
        record_id_dict = {}
        for arg in args_list:
          args_search_list.append(self.db_instance.ListRow(
              'record_arguments_records_assignments', arg))
        for index, record_args in enumerate(args_search_list):
          record_ids.append([])
          for args_dict in record_args:
            record_ids[index].append(args_dict[
                u'record_arguments_records_assignments_record_id'])
        for id_list in record_ids:
          for search_id in id_list:
            if( search_id in record_id_dict ):
              record_id_dict[search_id] += 1
            else:
              record_id_dict[search_id] = 1
        for record_id in record_id_dict:
          if( record_id_dict[record_id] == len(args_list) ):
            final_id.append(record_id)
        if( len(final_id) == 0 ):
          raise errors.CoreError('No records found.')
        elif( len(final_id) == 1 ):
          records_dict['records_id'] = final_id[0]
          new_records = self.db_instance.ListRow('records', records_dict)
          if( len(new_records) == 0 ):
            raise errors.CoreError(
                'Tried to find record with ID "%s" type "%s" target "%s" '
                'zone_name "%s" view "%s" ttl "%s" but could not.' % (
                    final_id[0], records_dict['record_type'],
                    records_dict['record_target'],
                    records_dict['record_zone_name'],
                    records_dict['record_view_dependency'],
                    records_dict['record_ttl']))
          if( len(new_records) > 1 ):
            raise errors.CoreError(
                'Tried to find record with ID "%s" type "%s" target "%s" '
                'zone_name "%s" view "%s" ttl "%s" but found multiple.' % (
                    final_id[0], records_dict['record_type'],
                    records_dict['record_target'],
                    records_dict['record_zone_name'],
                    records_dict['record_view_dependency'],
                    records_dict['record_ttl']))
          self.db_instance.RemoveRow('records', new_records[0])
        else:
          raise errors.CoreError('Duplicate records found.')
        self._IncrementSoa(view_name, zone_name)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveRecord',
                                  u'record_type: %s target: %s '
                                   'zone_name: %s record_args_dict: %s '
                                   'view_name: %s' % (record_type, target,
                                                      zone_name,
                                                      record_args_dict,
                                                      view_name), success)


  def ListRecordArgumentDefinitions(self, record_type=None):
    """List record argument definitions. This is mainly for the exporter to
    programtically construct records for exporting.

    This function is duplicated in
    roster-config-manager/roster_config_manager/tree_exporter.py

    Inputs:
      record_type: string of record type

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
    self.user_instance.Authorize('ListRecordArgumentDefinitions')

    search_record_arguments_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments')
    search_record_arguments_dict['record_arguments_type'] = record_type

    self.db_instance.StartTransaction()
    try:
      record_arguments = self.db_instance.ListRow('record_arguments',
                                                  search_record_arguments_dict)
    finally:
      self.db_instance.EndTransaction()

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

  def ListZoneTypes(self):
    """Lists zone types.

       Outputs:
         list: list of zone types, example: ['master', 'slave', 'forward']
    """
    self.user_instance.Authorize('ListZoneTypes')
    zone_types_dict = self.db_instance.GetEmptyRowDict('zone_types')
    self.db_instance.StartTransaction()
    try:
      zone_types = self.db_instance.ListRow('zone_types', zone_types_dict)
    finally:
      self.db_instance.EndTransaction()
      type_list = []
    for zone_type in zone_types:
      type_list.append(zone_type['zone_type'])
    return type_list

  def MakeZoneType(self, zone_type):
    """Makes a new zone type.

    Inputs:
      zone_type: string of zone type

    Raises:
      CoreError: Raised for any internal problems
    """
    self.user_instance.Authorize('MakeZoneType')
    zone_types_dict = {'zone_type': zone_type}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('zone_types', zone_types_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeZoneType',
                                  u'zone_type: %s' % zone_type, success)

  def RemoveZoneType(self, zone_type):
    """Removes a zone type.

    Inputs:
      zone_type: string of zone type

    Raises:
      CoreError: Raised for any internal problems

    Outputs:
      int: number of rows affected
    """
    self.user_instance.Authorize('RemoveZoneType')
    search_zone_type_dict = self.db_instance.GetEmptyRowDict('zone_types')
    search_zone_type_dict['zone_type'] = zone_type
    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        found_zone_type = self.db_instance.ListRow('zone_types',
                                                   search_zone_type_dict,
                                                   lock_rows=True)
        if( found_zone_type ):
          row_count += self.db_instance.RemoveRow('zone_types',
                                                  found_zone_type[0])
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveZoneType',
                                  u'zone_type: %s' % zone_type, success)
    return row_count

  def ListNamedConfGlobalOptions(self, option_id=None, dns_server_set=None,
                                 timestamp=None):
    """Lists named conf global options

    Inputs:
      option_id: integer of named conf global option id
      dns_server_set: string of the dns server set name
      timestamp: datetime object of timestamp to search

    Raises:
      CoreError: Raised for any internal problems
    """
    self.user_instance.Authorize('ListNamedConfGlobalOptions')
    named_conf_global_options_dict = self.db_instance.GetEmptyRowDict(
        'named_conf_global_options')
    named_conf_global_options_dict['named_conf_global_options_id'] = option_id
    named_conf_global_options_dict[
        'named_conf_global_options_dns_server_set_name'] = dns_server_set
    named_conf_global_options_dict['options_created'] = timestamp
    self.db_instance.StartTransaction()
    try:
      named_conf_options = self.db_instance.ListRow(
          'named_conf_global_options', named_conf_global_options_dict)
    finally:
      self.db_instance.EndTransaction()

    named_conf_list = []
    for named_conf_option in named_conf_options:
      named_conf_list.append(
          {'id': named_conf_option['named_conf_global_options_id'],
           'dns_server_set_name': named_conf_option[
               'named_conf_global_options_dns_server_set_name'],
           'timestamp': named_conf_option['options_created'],
           'options': named_conf_option['global_options']})

    return named_conf_list

  def MakeNamedConfGlobalOption(self, dns_server_set, options):
    """Makes named conf global option

    Inputs:
      dns_server_set: string of name of dns server set
      options: string of named conf file

    Raises:
      CoreError: Raised for any internal problems
    """
    self.user_instance.Authorize('MakeNamedConfGlobalOption')
    named_conf_global_options_dict = self.db_instance.GetEmptyRowDict(
        'named_conf_global_options')
    named_conf_global_options_dict[
        'named_conf_global_options_dns_server_set_name'] = dns_server_set
    named_conf_global_options_dict['global_options'] = options
    timestamp = self.unittest_timestamp
    if( self.unittest_timestamp is None ):
      timestamp = datetime.datetime.now()
    named_conf_global_options_dict['options_created'] = timestamp

    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('named_conf_global_options',
                                 named_conf_global_options_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeNamedConfGlobalOption',
                                  u'dns_server_set: %s timestamp: %s' % (
                                      dns_server_set, timestamp),
                                  success)

  def MakeReservedWord(self, reserved_word):
    """Create a reserved word.

    Inputs:
      reserved_word: string of reserved word

    Raises:
      CoreError  Raised for any internal problems.
    """
    self.user_instance.Authorize('MakeReservedWord')
    reserved_word_dict = {'reserved_word': reserved_word}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('reserved_words', reserved_word_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'MakeReservedWord',
                                  u'reserved_word: %s' % reserved_word,
                                  success)

  def ListReservedWords(self):
    """Lists reserved words.

    Raises:
      CoreError  Raised for any internal problems.

    Output:
      list: list of reserved words
            ex: ['reservedword1', 'reservedword2']
    """
    self.user_instance.Authorize('ListReservedWords')
    reserved_word_dict = self.db_instance.GetEmptyRowDict('reserved_words')
    self.db_instance.StartTransaction()
    try:
      reserved_words = self.db_instance.ListRow('reserved_words',
          reserved_word_dict)
    finally:
      self.db_instance.EndTransaction()

    reserved_word_list = []
    for reserved_word in reserved_words:
      reserved_word_list.append(reserved_word['reserved_word'])

    return reserved_word_list

  def RemoveReservedWord(self, reserved_word):
    """Removes a reserved word.

    Inputs:
      reserved_word: string of reserved word

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    self.user_instance.Authorize('RemoveReservedWord')
    search_reserved_word_dict = self.db_instance.GetEmptyRowDict(
        'reserved_words')
    search_reserved_word_dict['reserved_word'] = reserved_word
    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        found_reserved_word = self.db_instance.ListRow(
            'reserved_words', search_reserved_word_dict, lock_rows=True)
        if( found_reserved_word ):
          row_count += self.db_instance.RemoveRow('reserved_words',
              found_reserved_word[0])
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'RemoveReservedWord',
                                  u'reserved_word: %s' % reserved_word,
                                  success)

    return row_count

  def _IncrementSoa(self, view_name, zone_name, missing_ok=True):
    """Increments soa serial number.

    Inputs:
      view_name: string of view name
      zone_name: string of view namea
      missing_ok: boolean of whether or not missing SOA records are allowed

    Raises:
      CoreError: raised for having multiple SOA records

    Outputs:
      int: number of rows modified
    """
    soa_dict = self.db_instance.GetEmptyRowDict('records')
    soa_arguments_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments_records_assignments')

    soa_dict['record_type'] = u'soa'
    if( view_name is None ):
      view_name = u'any'
    if( view_name != u'any' and not view_name.endswith('_dep') ):
      view_name = '%s_dep' % view_name
    soa_dict['record_view_dependency'] = view_name
    soa_dict['record_zone_name'] = zone_name
    soa_records_list = self.db_instance.ListRow('records', soa_dict)
    row_count = 0

    if( len(soa_records_list) > 1 ):
      raise errors.CoreError('Multiple SOA records found.')

    if( len(soa_records_list) == 0 ):
      if( not missing_ok ):
        raise errors.CoreError('No SOA record found.')
    else:
      soa_records_list = soa_records_list[0]
      soa_arguments_dict[
          'record_arguments_records_assignments_record_id'] = (
              soa_records_list['records_id'])
      soa_record_arguments = self.db_instance.ListRow(
          'record_arguments_records_assignments', soa_arguments_dict)
      for argument in soa_record_arguments:
        if( argument[
            'record_arguments_records_assignments_argument_name'] == (
                u'serial_number') ):
          serial_number = int(argument['argument_value'])
          search_soa_dict = argument

      if( serial_number >= constants.MAX_SOA_SERIAL ):
        soa_arguments_dict[u'argument_value'] = u'1'
      else:
        soa_arguments_dict[u'argument_value'] = unicode(serial_number + 1)

      row_count += self.db_instance.UpdateRow(
          'record_arguments_records_assignments', search_soa_dict,
          soa_arguments_dict)
    return row_count

  def _MakeCredential(self, credential, user_name, last_used=None,
                      infinite_cred=False):
    """Create a credential.

    Inputs:
      user_name: string of user name
      credential: a 36 character uuid string
      infinite_cred: bool of infinite time to live
      last_used: datetime of access

    Raises:
      CoreError  Raised for any internal problems.
    """
    if( last_used is None ):
      last_used = datetime.datetime.now()
    infinite_cred = int(infinite_cred)
    credential_dict = {'credential': credential,
                       'credential_user_name': user_name,
                       'infinite_cred': infinite_cred,
                       'last_used_timestamp': last_used}
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        self.db_instance.MakeRow('credentials', credential_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'_MakeCredential',
                                  u'credential: %s user_name: %s '
                                  'infinite_cred: %s' % (
                                      credential, user_name, infinite_cred),
                                  success)

  def _ListCredentials(self, credential=None, user_name=None,
                       infinite_cred=None, key_by_user=False):
    """Lists one or many credentials, if all args are None then list them all.

    Inputs:
      credential: uuid string of credential
      user_name: string of user name
      infinite_cred: boolean of infinite time to live
      key_by_user: boolean to key by user rather than credential

    Raises:
      CoreError  Raised for any internal problems.

    Output:
      dictionary: keyed_by_user=False, a dictionary keyed
        by credential string.
        example: {'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx':
                     {'user_name': 'sharrell',
                      'last_used_timestamp': 1970-10-10 23:00:00,
                      'infinite_cred': True}}

        keyed by the user name
        example: {'sharrell':
            {'credential': 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx',
             'last_used_timestamp': 1970:10-10 23:00:00,
             'infinite_cred': True}}
    """
    credential_dict = {'credential': credential,
                       'credential_user_name': user_name,
                       'last_used_timestamp': None,
                       'infinite_cred': infinite_cred}
    self.db_instance.StartTransaction()
    try:
      credentials = self.db_instance.ListRow('credentials', credential_dict)
    finally:
      self.db_instance.EndTransaction()

    credentials_dict = {}
    if( key_by_user ):
      for credential in credentials:
        credentials_dict.update({credential['credential_user_name']:
            {u'credential': credential['credential'],
             u'last_used_timestamp': credential['last_used_timestamp'],
             u'infinite_cred': credential['infinite_cred']}})
    else:
      for credential in credentials:
        credentials_dict.update({credential['credential']:
            {u'user': credential['credential_user_name'],
             u'last_used_timestamp': credential['last_used_timestamp'],
             u'infinite_cred': credential['infinite_cred']}})

    return credentials_dict

  def _RemoveCredential(self, credential=None, user_name=None):
    """Removes a credential.

    Inputs:
      credential: uuid strong of credential
      user_name: string of user name

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    search_credential_dict = self.db_instance.GetEmptyRowDict('credentials')
    if ( credential is not None ):
      search_credential_dict['credential'] = credential
    else:
      search_credential_dict['credential_user_name'] = user_name
    row_count = 0
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        found_credential = self.db_instance.ListRow('credentials',
                                              search_credential_dict,
                                              lock_rows=True)
        if( found_credential ):
          # credential is a unique field, we know there is only one.
          row_count += self.db_instance.RemoveRow('credentials',
                                                  found_credential[0])
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise
      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'_RemoveCredential',
                                  u'credential: %s user_name: %s' % (
                                      credential, user_name),
                                  success)

    return row_count

  def _UpdateCredential(self, search_credential=None, search_user_name=None,
                        update_credential=None):
    """Updates a credential.

    Inputs:
      search_credential: uuid string of credential
      search_user_name: string of user name
      update_credential: uuid string of credential

    Raises:
      CoreError  Raised for any internal problems.

    Outputs:
      int: number of rows modified
    """
    search_credential_dict = self.db_instance.GetEmptyRowDict('credentials')
    update_credential_dict = self.db_instance.GetEmptyRowDict('credentials')
    if( search_credential is not None ):
      search_credential_dict['credential'] = search_credential
    else:
      search_credential_dict['credential_user_name'] = search_user_name
    update_credential_dict['credential'] = update_credential
    success = False
    try:
      self.db_instance.StartTransaction()
      try:
        row_count = self.db_instance.UpdateRow('credentials',
                                               search_credential_dict,
                                               update_credential_dict)
      except:
        self.db_instance.EndTransaction(rollback=True)
        raise

      self.db_instance.EndTransaction()
      success = True
    finally:
      self.log_instance.LogAction(self.user_instance.user_name,
                                  u'_UpdateCredential',
                                  u'search_credential: %s search_user_name: '
                                  u'%s update_credential: %s' % (
                                      search_credential, search_user_name,
                                      update_credential), success)

    return row_count

# vi: set ai aw sw=2:
