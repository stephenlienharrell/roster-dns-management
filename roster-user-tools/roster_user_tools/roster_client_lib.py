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
__version__ = '0.8'


import os
import sys
import xmlrpclib
import cli_common_lib


class InvalidCredentials(Exception):
  pass


def RunFunction(function, user_name, credfile=None, credstring=None,
                args=[], kwargs={}, server_name=None,
                raise_errors=False):
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
      raise InvalidCredentials('Credential file not found.')
  try:
    core_return = server.CoreRun(function, user_name, credstring, args, kwargs)
  except xmlrpclib.Fault, e:
    if( raise_errors ):
      raise
    print "SERVER ERROR: %s" % e.faultString
    sys.exit(1)


  if( core_return == 'ERROR: Invalid Credentials' ):
    raise InvalidCredentials('Credential file is invalid.')
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
  return server.IsAuthenticated(user_name, credstring)
