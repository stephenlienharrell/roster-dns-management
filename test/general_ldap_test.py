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


"""Test general_ldap module."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.17'


import unittest

import fakeldap
from roster_server import general_ldap


class TestGeneralLdapModule(unittest.TestCase):
  def testGeneralLdapModule(self):
    general_ldap_instance = general_ldap.AuthenticationMethod(
        ldap_module=fakeldap)
    self.assertTrue(general_ldap_instance.Authenticate(
        user_name=u'jcollins', password=u'test',
        binddn='uid=%s,ou=People,dc=dc,dc=university,dc=edu',
        cert_file=None, server=None, version='VERSION3', tls='on'))
    self.assertFalse(general_ldap_instance.Authenticate(
        user_name=u'jcollins', password=u'wrongpass',
        binddn='uid=%s,ou=People,dc=dc,dc=university,dc=edu',
        cert_file=None, server=None, version='VERSION3', tls='on'))
    self.assertFalse(general_ldap_instance.Authenticate(
        user_name=u'wronguser', password=u'wrongpass',
        binddn='uid=%s,ou=People,dc=dc,dc=university,dc=edu',
        cert_file=None, server=None, version='VERSION3', tls='on'))
    self.assertFalse(general_ldap_instance.Authenticate(
        user_name=u'jcollins', password=u'wrongpass',
        binddn='uid=%s,ou=Wrong,dc=dc,dc=university,dc=edu',
        cert_file=None, server=None, version='VERSION3', tls='on'))
    self.assertRaises(general_ldap.GeneralLDAPConfigError,
        general_ldap_instance.Authenticate,
        user_name=u'jcollins', password=u'test',
        binddn='uid=%s,ou=Wrong,dc=dc,dc=university,dc=edu',
        cert_file=None, server=None, version='3', tls='on')
    self.assertRaises(general_ldap.GeneralLDAPConfigError,
        general_ldap_instance.Authenticate,
        user_name=u'jcollins', password=u'test',
        binddn='uid=%s,ou=Wrong,dc=dc,dc=university,dc=edu',
        cert_file=None, server=None, version='VERSION3', tls='1')

if( __name__ == '__main__' ):
  unittest.main()
