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

"""Client library for XML RPC.

Connects to XML RPC server and runs arbitrary functions.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import os
import sys
import xmlrpclib
import cli_common_lib
import getpass


class InvalidCredentials(Exception):
  pass


def RunFunction(function, user_name, credfile=None, credstring=None,
                args=[], kwargs={}, server_name=None,
                raise_errors=False, password=None):
  """Runs an arbitrary function for SERVER

  Inputs:
    function: name of the function to be run
    user_name: user running the function
    args: list of arguments to be passed to function
    kwargs: dictionary of keyword arguments to be passed to function
    server_name: a string of the server name to connect to
    raise_errors: raise errors rather than printing

  Outputs:
    return from function in core
  """
  # if args is None:
  #   args = []
  # if kwargs is None:
  #   kwargs = {}
  if( credfile is None ):
    credfile = os.path.expanduser('~/.dnscred')
  else:
    credfile = os.path.expanduser(credfile)
  server = xmlrpclib.ServerProxy(server_name, allow_none=True)
  ## Read credential File
  core_return = ''
  if( credstring is None ):
    if( os.path.exists(credfile) ):
      credfile_handle = open(credfile, 'r')
      try:
        credstring = str(credfile_handle.read()).strip('\n')
        credfile_handle.close()
      except OSError:
        pass
    else:
      if( not CheckCredentials(user_name, credfile, server_name,
                               password=password) ):
        print "ERROR: Credential file not found, invalid credentials."
        sys.exit(1)
  try:
    core_return = server.CoreRun(function, user_name, credstring, args, kwargs)
  except xmlrpclib.Fault, e:
    if( raise_errors ):
      raise
    cli_common_lib.ServerError(str(e), 'UNKNOWN', 1) # This should never happen

  if( type(core_return) == dict and core_return['error'] ):
    if( raise_errors ):
      raise xmlrpclib.Fault(1, '(%s) %s' % (core_return['log_uuid_string'],
                                            core_return['error']))
    if( core_return['error_class'] == 'InternalError' ):
      cli_common_lib.ServerError(core_return['error'],
                                 core_return['log_uuid_string'], 1)
    elif( core_return['error_class'] == 'UserError' ):
      cli_common_lib.UserError(core_return['error'], 1)
    else:
      cli_common_lib.UnknownError(
          core_return['error_class'],
          core_return['log_uuid_string'],
          core_return['error'], 1)

  if( core_return == 'ERROR: Invalid Credentials' ):
    if( not CheckCredentials(user_name, credfile, server_name,
                               password=password) ):
      print "ERROR: Credential file not found, invalid credentials."
      sys.exit(1)
  elif( core_return['new_credential'] is not None and
    core_return['new_credential'] != '' ):
    if( os.path.exists(credfile) ):
      credfile_handle = open(credfile, 'w')
      try:
        credfile_handle.writelines(core_return['new_credential'])
      finally:
        credfile_handle.close()

  return core_return


def GetCredentials(user_name, password, credfile=None,
                   server_name=None):
  """Gets credential string from CredCache.

  Inputs:
    user_name: string of user name
    password: string of password (plain text)
    ldap_server_name: string of ldap server url
    credfile: full path of credential file
    server_name: string of xml rpc server url

  Outputs:
    string: credential string
            example: u'be4d4ecf-d670-44a0-b957-770e118e2755'
  """
  server = xmlrpclib.ServerProxy(server_name, allow_none=True)
  credential = server.GetCredentials(user_name, password)
  if( type(credential) == dict ):
    if( 'error' in credential ):
      cli_common_lib.ServerError(credential['error'],
                                 credential['log_uuid_string'], 1)
  if( credfile is not None ):
    credfile = os.path.expanduser(credfile)
    try:
      credfile_handle = open(credfile, 'w')
      try:
        credfile_handle.writelines(credential)
      finally:
        credfile_handle.close()
    except OSError:
      pass
  if( credential == '' ):
    raise InvalidCredentials

  return credential


def IsAuthenticated(user_name, credfile,
                    server_name=None):
  """Checks credential file if it is valid.

  Inputs:
    user_name: string of user name
    credfile: full path of credential file location
    server_name: string of server name

  Outputs:
    bool: whether or not credential file is valid
  """
  credfile = os.path.expanduser(credfile)
  if( os.path.exists(credfile) ):
    try:
      credfile_handle = open(credfile, 'r')
      credstring = str(credfile_handle.read()).strip('\n')
      credfile_handle.close()
    except OSError:
      return False
  else:
    return False
  server = xmlrpclib.ServerProxy(server_name, allow_none=True)
  authenticated = server.IsAuthenticated(user_name, credstring)
  if( type(authenticated) == dict and 'error' in authenticated ):
    cli_common_lib.ServerError(authenticated['error'],
                                authenticated['log_uuid_string'], 1)
  else:
    return authenticated

def CheckCredentials(username, credfile, server, password=None):
  """Checks if credential file is valid.

  Inputs:
    username: string of username
    credfile: string of credential file location
    server: string of server URL
    password: string of password

  Outputs:
    string: string of valid credential
  """
  if( not credfile ):
    self.DnsError('No credential file specified.', 1)
  got_credential = None
  count = 0
  while( count < 3 ):
    valid = IsAuthenticated(username, credfile, server_name=server)
    if( valid ):
      break
    else:
      count += 1
    password = password
    if( password is None ):
      try:
        password = getpass.getpass('Password for %s: ' %  username)
      except KeyboardInterrupt:
        sys.exit(0)
    try:
      got_credential = GetCredentials(username, password, credfile, server)
    except InvalidCredentials:
      if( password is None ):
        count = count + 1
      else:
        print 'ERROR: Incorrect username/password.'
        sys.exit(1)
  else:
    print 'ERROR: Incorrect username/password.'
    sys.exit(1)

  return got_credential

def CheckServerVersionMatch(server_name):
  """Does a version check between this client and server

  Inputs:
    server_name: string name of server to check
  """
  server = xmlrpclib.ServerProxy(server_name, allow_none=True)
  server_version =  server.GetVersion()
  if( server_version != __version__ ):
    print ('user_tools version %s mismatch with server version %s' % (
               __version__, server_version))
    sys.exit(1)
    
