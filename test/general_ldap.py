import ldap

class AuthenticationMethod:
  """General LDAP authentication method,
  should work for most LDAP applications.
  """
  def Authenticate(self, user_name=None, password=None, binddn=None, cert_file=None,
                   server=None, version=None, tls=None):
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
    print server
    binddn = binddn % user_name
    print binddn
    if( tls == 'on' ):
      tls = 'True'
    elif( tls == 'off' ):
      tls = 'False'
    if( eval(tls) ):
      print "TLS"
      ldap.set_option(ldap.OPT_X_TLS, 1)
      ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, cert_file)
    ldap_server = ldap.initialize(server)
    ldap_server.protocol_version = eval('ldap.%s' % version)
    try:
      ldap_server.simple_bind_s(binddn, password)
      authenticated = True
    except ldap.LDAPError, e:
      print e
      authenticated = False
    finally:
      ldap_server.unbind_s()

    return authenticated
    
