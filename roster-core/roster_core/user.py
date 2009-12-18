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

"""Classes pertaining to users and authorization for dnsManagement.

Authorization for specific functions and for specific domain/ip range blocks
is handled in this module.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.10'


import constants
import IPy
import errors


class UserError(errors.CoreError):
  pass


class AuthError(errors.CoreError):
  pass


class User(object):
  """Representation of a user, with basic manipulation methods.
  Note that is it not necessary to authenticate a user to construct a
  DNSdb_user - this is intended to be a part of the server API.
  """

  def __init__(self, user_name, db_instance, log_instance):
    """
    Inputs:
      user_name:	user's login
      db_instance:	dbAccess instance to use for user verification

    Raises:
      UserError on non-existent user
    """
    self.user_name = user_name
    self.db_instance = db_instance
    self.log_instance = log_instance


    # pull a pile of authentication info from the database here
    self.user_perms = self.db_instance.GetUserAuthorizationInfo(user_name)
    if( not self.user_perms.has_key('user_name') ):
      raise UserError("No such user: %s" % user_name)

    # More DB crud
    self.groups = self.user_perms['groups']
    self.forward_zones = self.user_perms['forward_zones']
    self.reverse_ranges = self.user_perms['reverse_ranges']
    self.user_access_level = ual = self.user_perms['user_access_level']

    # Build a hash of methods, using the supported_method hash
    self.abilities = {}
    for method in constants.SUPPORTED_METHODS.keys():
      if( constants.SUPPORTED_METHODS[method]['access_level'] <= ual ):
        self.abilities[method] = constants.SUPPORTED_METHODS[method]


  def Authenticate(self, passwd):
    """Attempt to authenticate the user using the given password.

    Inputs:
      passwd:	password to attempt

    Raises:
      AuthError on Authenticate failure

    Outputs:
      bool, set to True (failures raise an error)
    """
    pass


  def Authorize(self, method, target=None):
    """Check to see if the user is authorized to run the given operation.

    Inputs:
      method:	what the user's trying to do
      target:	what the user is trying to modify, if applicable (e.g.,
		          a host name, domain name, IPv4 or IPv6 address, etc.)

    Raises:
      UserError if no target is provided (and one is required)
      AuthError on authorization failure
    """
    if( target is not None ):
      target_string = ' on %s' % target
    else:
      target_string = ''
    auth_fail_string = ('User %s is not allowed to use %s%s' %
                        (self.user_name, method, target_string))
    if( self.abilities.has_key(method) ):
      method_hash = self.abilities[method]
      if( int(self.user_access_level) >= constants.ACCESS_LEVELS['dns_admin'] ):
        return
      if( method_hash['check'] ):
        # Secondary check - ensure the target is in a range delegated to
        # the user
        if( target is None ):
          raise UserError('No target provided for access method %s' % method)
        try:
          i = IPy.IP(target)

          # Good, we have an IP.  See if we hit any delegated ranges.
          for reverse_range in self.reverse_ranges:
            if( IPy.IP(reverse_range['cidr_block']).overlaps(i) ):
              return

          # fail to find a matching IP range with appropriate perms
          self.log_instance.LogAction(self.user_name, u'Authorize',
                                      auth_fail_string, False)
          raise AuthError(auth_fail_string)

        except ValueError:
          # oops, that was a hostname
          for zone in self.forward_zones:
            if( target.endswith(zone['zone_name']) ):
              return

          # fail to find a matching zone with appropriate perms
          self.log_instance.LogAction(self.user_name, u'Authorize',
                                      auth_fail_string, False)
          raise AuthError(auth_fail_string)
      else:
        return
    else:
      # fail to find a matching method
      self.log_instance.LogAction(self.user_name, u'Authorize',
                                  auth_fail_string, False)
      raise AuthError(auth_fail_string)

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
             {'zone_name': 'cs.university.edu', 'access_right': 'rw'},
             {'zone_name': 'eas.university.edu', 'access_right': 'r'},
             {'zone_name': 'bio.university.edu', 'access_right': 'rw'}],
         'groups': ['cs', 'bio'],
         'reverse_ranges': [
             {'cidr_block': '192.168.0.0/24',
              'access_right': 'rw'},
             {'cidr_block': '192.168.0.0/24',
              'access_right': 'r'},
             {'cidr_block': '192.168.1.0/24',
              'access_right': 'rw'}]}
    """
    return self.user_perms


# vi: set ai aw sw=2:
