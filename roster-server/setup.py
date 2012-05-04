#!/usr/bin/env python

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

"""Setup script for the roster xmlrpc daemon."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

current_version = __version__
if( __version__.startswith('#') ):
  current_version = '1000'

setup(name='RosterServer',
      version=current_version,
      description='RosterServer is a XML/RPC Server for Roster.',
      long_description='Roster is DNS management software for use with Bind 9. '
                       'Roster is written in Python and uses a MySQL database '
                       'with an XML-RPC front-end. It contains a set of '
                       'command line user tools that connect to the XML-RPC '
                       'front-end. The config files for Bind are generated '
                       'from the MySQL database so a live MySQL database is '
                       'not needed.',
      maintainer='Roster Development Team',
      maintainer_email='roster-discussion@googlegroups.com',
      url='http://code.google.com/p/roster-dns-management/',
      packages=['roster_server'],
      license=__license__,
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: No Input/Output (Daemon)',
                   'Intended Audience :: System Administrators',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python :: 2.5',
                   'Topic :: Internet :: Name Service (DNS)'],
      install_requires = ['python-ldap>=2.2.0', 'pyOpenSSL>=0.9',
                          'pam==0.1.4',
                          'RosterCore>=%s' % current_version],
      scripts = ['scripts/rosterd'],
     )
