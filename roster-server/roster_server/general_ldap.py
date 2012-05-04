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


"""General LDAP module for LDAP authentication in RosterServer."""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import ldap


class GeneralLDAPConfigError(Exception):
  pass


class AuthenticationMethod(object):
  """General LDAP authentication method,
  should work for most LDAP applications.
  """
  def __init__(self, ldap_module=ldap):
    self.requires = {'binddn': {'type': 'str', 'default': None,
                                'optional': False},
                     'server': {'type': 'str', 'default': None,
                                'optional': False},
                     'tls': {'type': 'str', 'default': 'on',
                             'optional': False},
                     'cert_file': {'type': 'str', 'default': None,
                                   'optional': True},
                     'version': {'type': 'str', 'default': None,
                                'optional': False}}
    self.ldap_module = ldap_module

  def Authenticate(self, user_name=None, password=None, binddn=None,
                   cert_file=None, server=None, version=None, tls=None):
    """Authenticate method for LDAP

    Inputs:
      user_name: string of user name
      password: string of password
      binddn: string of binddn line
      cert_file: string of cert file location
      server: string of server url
      version: string of version constant from ldap module
      tls: string of tls enabled or not

    Outputs:
      boolean: authenticated or not
    """
    binddn = binddn % user_name
    if( tls.lower() == 'on' ):
      self.ldap_module.set_option(self.ldap_module.OPT_X_TLS, 1)
      if( cert_file ):
        self.ldap_module.set_option(self.ldap_module.OPT_X_TLS_CACERTFILE,
                                    cert_file)
    elif( tls.lower() != 'off' ):
      raise GeneralLDAPConfigError(
          'Option "tls" must be set to "on" or "off", '
          '"%s" is an invalid option.' % tls)

    ldap_server = self.ldap_module.initialize(server)
    try:
      ldap_server.protocol_version = getattr(self.ldap_module, version)
    except AttributeError:
      raise GeneralLDAPConfigError(
          'Version must be set to "VERSION1, VERSION2, VERSION3, VERSION_MAX '
          'or VERSION_MIN" in user config file. Not "%s".' % version)
    try:
      ldap_server.simple_bind_s(binddn, password)
      authenticated = True
    except self.ldap_module.LDAPError:
      authenticated = False
    finally:
      ldap_server.unbind_s()

    return authenticated
