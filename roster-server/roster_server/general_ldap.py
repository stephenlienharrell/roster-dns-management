import ldap

class GeneralLDAPConfigError(Exception):
  pass

class AuthenticationMethod:
  """General LDAP authentication method,
  should work for most LDAP applications.
  """
  def __init__(self):
    self.requires = {'binddn': {'type': 'str', 'default': None},
                     'server': {'type': 'str', 'default': None},
                     'tls': {'type': 'str', 'default': 'on'},
                     'cert_file': {'type': 'str', 'default': None},
                     'version': {'type': 'str', 'default': None}}

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
    if( tls == 'on' ):
      ldap.set_option(ldap.OPT_X_TLS, 1)
      ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, cert_file)
    elif( tls.lower() != 'off' ):
      raise GeneralLDAPConfigError(
          'Option "tls" must be set to "on" or "off", '
          '"%s" is an invalid option.' % tls)

    ldap_server = ldap.initialize(server)
    ldap_server.protocol_version = getattr(ldap, version)
    try:
      ldap_server.simple_bind_s(binddn, password)
      authenticated = True
    except ldap.LDAPError, e:
      authenticated = False
    finally:
      ldap_server.unbind_s()

    return authenticated
