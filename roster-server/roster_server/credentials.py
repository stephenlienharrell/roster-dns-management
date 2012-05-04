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


"""Credential caching for XMLRPC services."""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import datetime
import inspect
import uuid
import sys


class ConfigError(Exception):
  pass


class CredCache(object):
  """Credentials cache for XMLRPC services.

  Authenticated users are given a time-limited credential.  Credentials map
  to Core instances, and can be used for repeated calls from a client.

  CredCaches also handle verifying credentials, and invoking API calls as
  those credentials.
  """

  # This will need a config option for the core objects, probably
  def __init__(self, config_instance, inf_renew_time, unit_test=False):
    """Constructs a new credential cache.
    Inputs:
      config_instance: instance of Config
      inf_renew_time: the that each credential is renewed (seconds)
      unit_test: boolean indicating a unit-test is being run.
    """
    self.config_instance = config_instance
    self.exp_time = self.config_instance.config_file['credentials']['exp_time']
    if( unit_test ):
      sys.path.append('./')
    self.authentication_method = self.config_instance.config_file[
       'credentials']['authentication_method']
    self.inf_renew_time = inf_renew_time
    self.unit_test = unit_test

    # garbage_collector contains cred strings in insertion order, to be walked
    # when it's time to remove potentially expired Credentials.
    self.garbage_collector = []

  def Authenticate(self, user_name, password):
    """Authenticates user against authentication method

    Inputs:
      user_name: string of user name
      password: string of password

    Outputs:
      boolean of whether or not user is authenticated
    """
    try:
      authenticate_module = __import__(
          'roster_server.%s' % self.authentication_method)
      authentication_module = getattr(
          authenticate_module, self.authentication_method)
    except ImportError:
      authentication_module = __import__(self.authentication_method)
    authentication_module_instance = (
        authentication_module.AuthenticationMethod())
    authenticate_module_args = inspect.getargspec(
        authentication_module_instance.Authenticate)[0]
    if( authenticate_module_args[0] == 'self' ):
      authenticate_module_args.pop(0)
    for authenticate_module_arg in authenticate_module_args:
      if( authenticate_module_arg == 'user_name' or
          authenticate_module_arg == 'password' ):
        continue
      if( authenticate_module_arg not in self.config_instance.config_file[
          self.authentication_method] ):
        raise ConfigError(
            'Could not find "%s" value in "%s" in the "%s" section.' % (
                authenticate_module_arg, self.config_instance.config_file_path,
                self.authentication_method))
    kwargs_dict = {}
    for authenticate_module_arg in authenticate_module_args:
      if( authenticate_module_arg == 'user_name' ):
        kwargs_dict['user_name'] = user_name
      elif( authenticate_module_arg == 'password' ):
        kwargs_dict['password'] = password
      else:
        kwargs_dict[authenticate_module_arg] = (
            self.config_instance.config_file[self.authentication_method][
                authenticate_module_arg])

    return authentication_module_instance.Authenticate(**kwargs_dict)

  def CheckCredential(self, credential, user_name, core_instance):
    """Checks users credential against database.

    Inputs:
      credential: string of credential
      core_instance: instance of Core

    Outputs:
      string or None, None if not authenticated, empty string if
      authenticated, string with new uuid if infinite key is being
      refreshed
      example: None, u'', u'be4d4ecf-d670-44a0-b957-770e118e2755'
    """
    current_timestamp = datetime.datetime.now()
    try:
      credential_dict = core_instance._ListCredentials(credential=credential)[
          credential]
    except KeyError:
      return None # Key not in database
    db_timestamp = credential_dict['last_used_timestamp'] + datetime.timedelta(
        minutes=self.exp_time)
    if( credential_dict['infinite_cred'] ):
      inf_renew = credential_dict['last_used_timestamp'] + datetime.timedelta(
          seconds=self.inf_renew_time)
      if( inf_renew < current_timestamp ):
        make_new_cred = True
        while( make_new_cred ):
          new_cred = unicode(uuid.uuid4())
          if( not core_instance._ListCredentials(new_cred) ):
            core_instance._UpdateCredential(search_credential=credential,
                                            update_credential=new_cred)
            make_new_cred = False
            return new_cred # Infinite key re issued
      return u'' # Infinite key is valid
    elif( db_timestamp > current_timestamp ):
      if( credential_dict['user'] != user_name ):
        return None
      core_instance._UpdateCredential(search_credential=credential,
                                      update_credential=credential)
      return u'' # Key is valid
    core_instance._RemoveCredential(credential=credential)

    return None # Key is expired

  def GetCredentials(self, user_name, password, core_instance):
    """Return a valid credential string given a username and password.

    Inputs:
      user_name: strin of login for a user
      password: string of user's password
      core_instance: instance of Core

    Outputs:
      string: credential string
              example: u'be4d4ecf-d670-44a0-b957-770e118e2755'

    Raises:
      AuthError         Raised on invalid username/password combination
    """
    user_name = unicode(user_name)
    cred_string = ''
    if( self.Authenticate(user_name, password) ):
      current = core_instance._ListCredentials(user_name=user_name)
      if( current ):
        return current.keys()[0]
      make_new_cred = True
      while( make_new_cred ):
        cred_string = unicode(uuid.uuid4())
        if( not core_instance._ListCredentials(cred_string) ):
          core_instance._MakeCredential(cred_string, user_name)
          make_new_cred = False

    return cred_string
# vi: set ai aw sw=2:
