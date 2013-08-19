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

"""Classes pertaining to users and authorization for Roster.

Authorization for specific functions and for specific domain/ip range blocks
is handled in this module.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.18'


import IPy

import constants
import errors
import helpers_lib

class User(object):
  """Representation of a user, with basic manipulation methods.
  Note that is it not necessary to authenticate a user to construct this
  class. This class is mainly responsible for authorization.
  """

  def __init__(self, user_name, db_instance, log_instance):
    """
    Inputs:
      user_name:	user's login
      db_instance:	dbAccess instance to use for user verification

    Raises:
      InvalidInputError: No such user.
    """
    self.user_name = user_name
    self.db_instance = db_instance
    self.log_instance = log_instance
    self.zone_origin_cache = {}

    # pull a pile of authentication info from the database here
    self.user_perms = self.db_instance.GetUserAuthorizationInfo(user_name)
    if( not self.user_perms.has_key('user_name') ):
      raise errors.InvalidInputError("No such user: %s" % user_name)

    # More DB crud
    self.groups = self.user_perms['groups']
    self.forward_zones = self.user_perms['forward_zones']
    self.reverse_ranges = self.user_perms['reverse_ranges']
    self.user_access_level = ual = self.user_perms['user_access_level']

    # Pull zone origins for cache
    self.db_instance.StartTransaction()
    try:
      all_zone_origins = self.db_instance.GetZoneOrigins(None, None)
      for zone in self.forward_zones:
        if( zone['zone_name'] in all_zone_origins ):
          self.zone_origin_cache[
              zone['zone_name']] = all_zone_origins[zone['zone_name']]
    finally:
      self.db_instance.EndTransaction()

    # Build a hash of methods, using the supported_method hash
    self.abilities = {}
    for method in constants.SUPPORTED_METHODS.keys():
      if( constants.SUPPORTED_METHODS[method]['access_level'] <= ual ):
        self.abilities[method] = constants.SUPPORTED_METHODS[method]

  def Authorize(self, method, record_data=None, current_transaction=False):
    """Check to see if the user is authorized to run the given operation.

    Inputs:
      method:	what the user's trying to do
      record_data: dictionary of target, zone_name, view_name, record_type, 
                   and record_args_dict for the record that is being modified.
                   {'target': 'test_target',
                    'zone_name': 'test_zone',
                    'view_name': 'test_view',
                    'record_type': 'a',
                    'record_args_dict' : {
                        u'assignment_ip' : '192.168.1.1'
                     }
                   }
      current_transaction: bool of if this function is run from inside a
                           transaction in the db_access class

    Raises:
      MaintenanceError: Roster is currently under maintenance.
      MissingDataTypeError: Incomplete record data provided for access method.
      AuthorizationError: Authorization failure.
    """
    function_name, current_args = helpers_lib.GetFunctionNameAndArgs()

    if( not current_transaction ):
      self.db_instance.StartTransaction()
    try:
      maintenance_mode = self.db_instance.CheckMaintenanceFlag()
      if( record_data and record_data.has_key('zone_name') ):
        if( record_data['zone_name'] ):
          pulled_origin = self.db_instance.GetZoneOrigins(
              record_data['zone_name'], record_data['view_name'])

          #Making sure we pulled something that exists
          if( pulled_origin is not None ):
            self.zone_origin_cache[record_data['zone_name']] = pulled_origin[
                record_data['zone_name']]
          else:
            view_name = record_data['view_name']
            if( view_name.endswith('_dep') ):
              view_name = view_name[:-4] #Strip off '_dep'

            raise errors.UnexpectedDataError('Specified zone-view assignment '
                'does not exist for zone %s view %s' % (
                    record_data['zone_name'], view_name))
    finally:
      if( not current_transaction ):
        self.db_instance.EndTransaction()

    if( maintenance_mode and self.user_perms['user_access_level']
        != constants.ACCESS_LEVELS['dns_admin'] ):
      raise errors.MaintenanceError('Roster is currently under maintenance.')

    if( record_data is not None and record_data.has_key('zone_name') ):
      target_string = ' with %s on %s of type %s' % (record_data['target'],
                                          record_data['zone_name'],
                                          record_data['record_type'])

      user_group_perms = {}
      record_target = record_data['target']

      # Get user group permissions for record zone
      if( record_data['zone_name'] ):
        for origin in self.zone_origin_cache[record_data['zone_name']]:
          user_group_perms[origin] = []
          if( record_target == u'@' ):
            ip_address = helpers_lib.UnReverseIP(origin)
          else:
            ip_address = helpers_lib.UnReverseIP('%s.%s' % (
                record_target,
                origin))

          #Looking for permissions in the forward zones
          for zone in self.user_perms['forward_zones']:
            if( zone['zone_name'] == record_data['zone_name'] ):
              user_group_perms[origin].append(zone['group_permission'])

          #If we haven't found any, look in the reverse ranges
          if( user_group_perms[origin] == [] ):
            validation_instance = self.db_instance.data_validation_instance
            if( validation_instance.isIPv4IPAddress(ip_address) or
                validation_instance.isIPv6IPAddress(ip_address) ):
              for cidr in self.user_perms['reverse_ranges']:
                if( IPy.IP(cidr['cidr_block']).overlaps(ip_address) ):
                  user_group_perms[origin].append(cidr['group_permission'])
    else:
      target_string = ''
    auth_fail_string = ('User %s is not allowed to use %s%s' %
                        (self.user_name, method, target_string))

    #authorizing method
    if( self.abilities.has_key(method) ):
      method_hash = self.abilities[method]
      if( int(self.user_access_level) >= constants.ACCESS_LEVELS['dns_admin'] ):
        return

      if( method_hash['check'] ):
        # Secondary check - ensure the target is in a range delegated to
        # the user
        if( record_data is None ):
          raise errors.MissingDataTypeError(
              'No record data provided for access method '
              '%s' % method)
        elif( not record_data.has_key('zone_name') or
            record_data['zone_name'] is None or
            not record_data.has_key('view_name') or
            record_data['view_name'] is None or
            not record_data.has_key('target') or
            record_data['target'] is None or
            not record_data.has_key('record_type') or
            record_data['record_type'] is None or
            not record_data.has_key('record_args_dict') or
            record_data['record_args_dict'] is None ):
          raise errors.MissingDataTypeError(
              'Incomplete record data provided for access '
              'method %s' % method)
        # If user or less, check permission for zone origin
        elif( int(self.user_access_level) <= constants.ACCESS_LEVELS[
            'unlocked_user'] ):
          user_has_permission = False
          for origin in self.zone_origin_cache[record_data['zone_name']]:
            if( record_data['record_type'] in user_group_perms[origin] ):
              user_has_permission = True

          if( not user_has_permission ):
            raise errors.AuthorizationError(auth_fail_string)

        if( int(self.user_access_level) <
          constants.ACCESS_LEVELS['unlocked_user'] ):

          # if a or aaaa
          if( record_data['record_args_dict'].has_key(u'assignment_ip') ):
            ip = IPy.IP(record_data['record_args_dict'][u'assignment_ip'])
            for reverse_range in self.reverse_ranges:
              if( IPy.IP(reverse_range['cidr_block']).overlaps(ip) ):
                break
            else:
              raise errors.AuthorizationError(auth_fail_string)

          # if cname, mx, ns, or ptr
          elif( record_data['record_args_dict'].has_key(u'assignment_host') or
                record_data['record_args_dict'].has_key(u'mail_server') or
                record_data['record_args_dict'].has_key(u'name_server') ):
            hostname = None
            if( record_data['record_args_dict'].has_key(u'assignment_host') ):
              hostname = record_data['record_args_dict'][u'assignment_host']
            elif( record_data['record_args_dict'].has_key(u'mail_server') ):
              hostname = record_data['record_args_dict'][u'mail_server']
            elif( record_data['record_args_dict'].has_key(u'name_server') ):
              hostname = record_data['record_args_dict'][u'name_server']
            smallest_zone = hostname

            found = False
            while( smallest_zone ):
              for domain in self.zone_origin_cache:
                for origin in self.zone_origin_cache[domain]:
                  if( smallest_zone == origin ):
                    found = True
              if( not found ):
                try:
                  smallest_zone = smallest_zone.split('.', 1)[1]
                except IndexError:
                  break
              else:
                break
            if( not found ):
              raise errors.AuthorizationError(auth_fail_string)

            for zone in self.forward_zones:
              if( self.zone_origin_cache.has_key(zone['zone_name']) ):
                found = False
                for origin in self.zone_origin_cache[zone['zone_name']]:
                  if( smallest_zone == origin ):
                    found = True
                    break
                if( found ):
                  break
            else:
              raise errors.AuthorizationError(auth_fail_string)

        for forward_zone in self.forward_zones:
          if( record_data['zone_name'] == forward_zone['zone_name'] ):
            return

        # Can't find it in forward zones, maybe it's a reverse
        try:
          ip = IPy.IP(ip_address)

          # Good, we have an IP.  See if we hit any delegated ranges.
          for reverse_range in self.reverse_ranges:
            if( IPy.IP(reverse_range['cidr_block']).overlaps(ip) ):
              return

          # fail to find a matching IP range with appropriate perms
          self.log_instance.LogAction(self.user_name, function_name,
                                      current_args, False, current_transaction)
          raise errors.AuthorizationError(auth_fail_string)

        except ValueError:
          # fail to find a matching zone with appropriate perms
          self.log_instance.LogAction(self.user_name, function_name,
                                      current_args, False, current_transaction)
          raise errors.AuthorizationError(auth_fail_string)
      else:
        return
    else:
      # fail to find a matching method
      self.log_instance.LogAction(self.user_name, function_name,
                                  current_args, False, current_transaction)
      raise errors.AuthorizationError(auth_fail_string)

  def GetUserName(self):
    """Return user name for current session.

    Outputs:
      string: user name
    """
    return self.user_perms['user_name']

  def GetPermissions(self):
    """Return permissions and groups for user.

    Outputs:
      dictionary of permissions
        example:
        {'user_access_level': '2',
         'user_name': 'shuey',
         'forward_zones': [
             {'zone_name': 'cs.university.edu', 'group_permission': 'rw'},
             {'zone_name': 'eas.university.edu', 'group_permission': 'r'},
             {'zone_name': 'bio.university.edu', 'group_permission': 'rw'}],
         'groups': ['cs', 'bio'],
         'reverse_ranges': [
             {'cidr_block': '192.168.0.0/24',
              'group_permission': 'rw'},
             {'cidr_block': '192.168.0.0/24',
              'group_permission': 'r'},
             {'cidr_block': '192.168.1.0/24',
              'group_permission': 'rw'}]}
    """
    return self.user_perms


# vi: set ai aw sw=2:
