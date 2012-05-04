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

"""Server library for XML RPC
Allows client to connect and run arbitrary functions in core.py.
"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import datetime
import os
import inspect
import SocketServer
import StringIO
import time
import traceback
import uuid
import xmlrpclib

import roster_core

import credentials
from ssl_xml_rpc_lib import SecureXMLRPCServer
from ssl_xml_rpc_lib import SecureXMLRpcRequestHandler


roster_core.core.CheckCoreVersionMatches(__version__)


class ArgumentError(roster_core.CoreError):
  pass

class FunctionError(roster_core.CoreError):
  pass

class ServerError(roster_core.CoreError):
  pass

class ThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SecureXMLRPCServer):
  pass

class Server(object):
  """Daemon library used to serve commands to the client."""
  def __init__(self, config_instance, keyfile=None, certfile=None,
               inf_renew_time=None, core_die_time=None,
               clean_time=None, unittest_timestamp=None,
               unit_test=False):
    """Sets up config instance. Stores core instances.

    Inputs:
       config_instance: instance of Config
       keyfile: key file used for ssl
       certfile: cert file used for ssl
       inf_renew_time: time to refresh infinite credentials (seconds)
       core_die_time: time for each core instance to die (seconds)
       clean_time: time to wait between core instance cleanings (seconds)
       unit_test: boolean indicating a unit-test is being run.
    """
    self.config_instance = config_instance
    self.keyfile = keyfile
    if( keyfile is None ):
      self.keyfile = self.config_instance.config_file['server'][
          'ssl_key_file']
    self.certfile = certfile
    if( certfile is None ):
      self.certfile = self.config_instance.config_file['server'][
          'ssl_cert_file']
    self.inf_renew_time = inf_renew_time
    self.port = self.config_instance.config_file['server'][
        'port']
    self.server_name = self.config_instance.config_file['server'][
        'host']
    self.core_store_cleanup_running = False
    if( inf_renew_time is None ):
      self.inf_renew_time = self.config_instance.config_file['server'][
          'inf_renew_time']
    self.core_die_time = core_die_time
    if( core_die_time is None ):
      self.core_die_time = self.config_instance.config_file['server'][
          'core_die_time']
    self.log_file = self.config_instance.config_file['server'][
        'server_log_file']
    self.get_credentials_wait_increment = self.config_instance.config_file[
        'server']['get_credentials_wait_increment']
    self.server_killswitch = self.config_instance.config_file['server'][
        'server_killswitch']
    self.clean_time = clean_time
    if( clean_time is None ):
      self.clean_time = self.core_die_time
    self.cred_cache_instance = credentials.CredCache(self.config_instance,
                                   inf_renew_time, unit_test)
    self.unittest_timestamp = unittest_timestamp
    self.core_store = [] # {'user': user, 'last_used': last_used, 'instance': }
    self.get_credentials_wait = {} # {'user1': 3, 'user2': 4}
    self.last_cleaned = datetime.datetime.now()
    self.LogMessage('Roster server started on port %s' % self.port, 'rosterd')

  def LogException(self, function, args, kwargs, user_name):
    """Save functions traceback to logfile

    Inputs:
      function: string of function name
      args: args list
      kwargs: keyword args dict
      user_name: username string

    Outputs:
      str: uuid string from logfile
    """
    uuid_string = str(uuid.uuid4())
    log_file_contents = []
    exception_string = StringIO.StringIO()
    traceback.print_exc(None, exception_string)
    log_file_contents.append('\n\n---------------------\n')
    log_file_contents.append(uuid_string)
    log_file_contents.append('\n')
    log_file_contents.append('FUNCTION: %s\n' % function)
    log_file_contents.append('ARGS: %s\n' % args)
    log_file_contents.append('KWARGS: %s\n' % kwargs)
    log_file_contents.append('USER: %s\n' % user_name)
    log_file_contents.append('TIMESTAMP: %s\n\n' % (
        datetime.datetime.now().isoformat()))
    log_file_contents.append(exception_string.getvalue())
    log_file_contents.append('\n---------------------\n')
    try:
      log_file_handle = open(self.log_file, 'a')
      log_file_handle.writelines(''.join(log_file_contents))
    finally:
      log_file_handle.close()

    return uuid_string

  def LogMessage(self, log_message, user_name):
    """Save a message to the logfile

    Inputs:
      log_message: string of the log message
      user_name: username string

    Outputs:
      str: uuid string from logfile
    """
    uuid_string = str(uuid.uuid4())
    log_file_contents = []
    log_file_contents.append('\n\n---------------------\n')
    log_file_contents.append(uuid_string)
    log_file_contents.append('\n')
    log_file_contents.append('MESSAGE: %s\n' % log_message)
    log_file_contents.append('USER: %s\n' % user_name)
    log_file_contents.append('TIMESTAMP: %s' % (
        datetime.datetime.now().isoformat()))
    log_file_contents.append('\n---------------------\n')
    try:
      log_file_handle = open(self.log_file, 'a')
      log_file_handle.writelines(''.join(log_file_contents))
    finally:
      log_file_handle.close()

    return uuid_string
  
  def CleanupCoreStore(self):
    """Cleans up expired instances in core_store"""
    delete_list = []
    if( self.last_cleaned + datetime.timedelta(seconds=self.clean_time) < (
          datetime.datetime.now()) ):
      self.last_cleaned = datetime.datetime.now()
      for core_instance in self.core_store:
        if( core_instance['last_used'] + datetime.timedelta(
                seconds=self.core_die_time) < datetime.datetime.now() ):
          delete_list.append(core_instance)
      for instance in delete_list:
        self.core_store.remove(instance)

  def StringToUnicode(self, object_to_convert):
    """Converts objects recursively into strings.

    Inputs:
      object_to_convert: the object that needs to be converted to unicode
    Outputs:
      converted_object: object can vary type, but all strings will be unicode
    """
    converted_object = object_to_convert
    if( isinstance(object_to_convert, str) ):
      converted_object = unicode(object_to_convert)
    elif( isinstance(object_to_convert, dict) ):
      new_dict = {}
      for key, value in object_to_convert.iteritems():
        new_dict[unicode(key)] = self.StringToUnicode(value)
      converted_object = new_dict
    elif( isinstance(object_to_convert, list) ):
      for index, item in enumerate(object_to_convert):
        object_to_convert[index] = self.StringToUnicode(item)
      converted_object = object_to_convert
    elif( isinstance(object_to_convert, xmlrpclib.DateTime) ):
      converted_object = datetime.datetime.strptime(
          object_to_convert.value, "%Y%m%dT%H:%M:%S")
    return converted_object

  def GetCoreInstance(self, user_name):
    """Finds core instance in core store, if one cannot be found
       it will be created.

    Inputs:
      user_name: string of user name

    Outputs:
      instance: instance of dnsmgmtcore
    """
    core_instance_dict = {}
    for core_instance_dict in self.core_store:
      if( core_instance_dict['user_name'] == user_name ):
        break
    else:
      new_core_instance = roster_core.Core(user_name, self.config_instance,
                                           unittest_timestamp=(
                                               self.unittest_timestamp))
      core_instance_dict = {'user_name': user_name,
                            'last_used': datetime.datetime.now(),
                            'core_instance': new_core_instance}
      self.core_store.append(core_instance_dict)

    return core_instance_dict['core_instance']

  def CoreRun(self, function, user_name, credfile, args = None, kwargs = None):
    """Runs a function in core_instance with arbitrary parameters

    Inputs:
      function: name of the function to be run
      user_name: user running the function
      args: list of arguments to be passed to function
      kwargs: dictionary of keyword arguments to be passed to function

    Outputs:
      dictionary:  dictionary of return from function run and new cred string
                   example: {'core_return': returned_data,
                             'new_credential': u'
                                 be4d4ecf-d670-44a0-b957-770e118e2755'}
    """
    if args is None:
      args = []
    if kwargs is None:
      kwargs = {}
    uuid_string = None
    credfile = unicode(credfile)
    user_name = unicode(user_name)
    ## Instantiate the core instance
    core_instance = self.GetCoreInstance(user_name)
    core_helper_instance = roster_core.CoreHelpers(core_instance)
    cred_status = self.cred_cache_instance.CheckCredential(credfile, user_name,
                                                           core_instance)
    if( cred_status is not None ):
      ## Fix non unicode strings containing no unicode characters
      args = self.StringToUnicode(args)
      kwargs = self.StringToUnicode(kwargs)

      ## Fix unicoded kwargs keys
      new_kwargs = {}
      for key in kwargs:
        new_kwargs[str(key)] = kwargs[key]
      kwargs = new_kwargs

      if( function.startswith('_') ):
        raise FunctionError('Function does not exist.')
      elif( hasattr(core_instance, function) ):
        run_func = getattr(core_instance, function)
      elif( hasattr(core_helper_instance, function) ):
        run_func = getattr(core_helper_instance, function)
      else:
        raise FunctionError('Function does not exist.')

      types = inspect.getargspec(run_func)
      error_class = None
      try:
        ## Figure out what each function is expecting
        if( types[3] is None and len(types[0]) == 1 ):
          # Nothing in core function
          core_return = run_func()
        elif( types[3] is None and len(types[0]) != 1 ):
          # Arguments only in core function
          core_return = run_func(*args)
        elif( types[3] is not None and (len(types[0]) - len(types[3])) == 1 ):
          # KWArguments only in core function
          core_return = run_func(**kwargs)
        elif( types[3] is not None and (len(types[0]) - len(types[3])) != 1 ):
          # Both kwargs and args in core function
          core_return = run_func(*args, **kwargs)
        else:
          raise ArgumentError('Arguments do not match.')
      except roster_core.errors.InternalError, error:
        uuid_string = self.LogException(function, args, kwargs, user_name)
        error_class = 'InternalError'
      except roster_core.errors.UserError, error:
        error_class = 'UserError'
      except Exception, error:
        uuid_string = self.LogException(function, args, kwargs, user_name)
        error_class = error.__class__.__name__
      if( error_class is not None ):
        return {'log_uuid_string': uuid_string, 'error': str(error),
                'error_class': error_class, 'core_return': None, 'new_credential': None}
      core_return = {'core_return': core_return, 'new_credential': cred_status,
                     'log_uuid_string': uuid_string, 'error': None}
    else:
      core_return = 'ERROR: Invalid Credentials'
    return core_return

  def GetCredentials(self, user_name, password):
    """Connects to credential cache and gets a credential file.

    Inputs:
      user_name: string of user name
      password: string of password (plaintext)

    Outputs:
      string: string of credential
              example: u'be4d4ecf-d670-44a0-b957-770e118e2755'
    """
    error_class = None
    try:
      user_name = unicode(user_name)
      core_instance = self.GetCoreInstance(user_name)
      cred_string = self.cred_cache_instance.GetCredentials(user_name, password,
                                                            core_instance)
      if( cred_string == '' ):
        if( not self.get_credentials_wait.has_key(user_name) ):
          self.get_credentials_wait.update({user_name: 0})
        time.sleep(self.get_credentials_wait[user_name])
        self.get_credentials_wait[user_name] = self.get_credentials_wait[
            user_name] + self.get_credentials_wait_increment
      elif( self.get_credentials_wait.has_key(user_name) ):
        self.get_credentials_wait.pop(user_name)
    except Exception, error:
      uuid_string = self.LogException(
          'GetCredentials', [user_name, '<password>'], {}, user_name)
      error_class = error.__class__.__name__
      if( error_class is not None ):
        return {'log_uuid_string': uuid_string, 'error': str(error),
                'error_class': error_class, 'core_return': None, 'new_credential': None}
      return {'log_uuid_string': uuid_string, 'error': str(error),
              'core_return': None, 'new_credential': None}

    return cred_string

  def IsAuthenticated(self, user_name, credstring):
    """Checks if string is valid.

    Inputs:
      credstring: string of credential

    Outputs:
      bool: bool of valid string
    """
    error_class = None
    try:
      user_name = unicode(user_name)
      credstring = unicode(credstring)
      core_instance = self.GetCoreInstance(user_name)
      valid = self.cred_cache_instance.CheckCredential(
          credstring, user_name, core_instance)
    except Exception, error:
      uuid_string = self.LogException(
          'IsAuthenticated', [user_name, '<credstring>'], {}, user_name)
      error_class = error.__class__.__name__
      if( error_class is not None ):
        return {'log_uuid_string': uuid_string, 'error': str(error),
                'error_class': error_class, 'core_return': None, 'new_credential': None}
      return {'log_uuid_string': uuid_string, 'error': str(error),
              'core_return': None, 'new_credential': None}
    if( valid == '' ):
      return True
    return False

  def GetVersion(self):
    return __version__

  def Serve(self, server_name=None, port=None):
    """Main server function

    Inputs:
      server_name: name of server you wish to create
      port: listening port number of server
    """
    if( not os.path.exists ):
      try:
        open(self.log_file, 'w').close()
      except:
        raise ServerError('Could not write to logfile "%s"' % self.log_file)
    if( not port ):
      port = self.port
    if( not server_name ):
      server_name = self.server_name
    if( self.server_killswitch ):
      raise ServerError('"server_killswitch" must be set to "off" in "%s" '
                        'to allow the XML-RPC server to run.' % (
          self.config_instance.config_file_path))
    self.server = ThreadedXMLRPCServer((server_name, port),
                                        SecureXMLRpcRequestHandler,
                                        self.keyfile, self.certfile)
    self.server.register_function(self.CoreRun)
    self.server.register_function(self.GetCredentials)
    self.server.register_function(self.IsAuthenticated)
    self.server.register_function(self.GetVersion)
    try:
      while 1:
        self.server.handle_request()
        if( not self.core_store_cleanup_running ):
          self.core_store_cleanup_running = True
          self.CleanupCoreStore()
          self.core_store_cleanup_running = False
    except KeyboardInterrupt:
      print "Stopped by user."
