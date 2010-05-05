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

"""Core flags lib, flags in all tools."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import getpass
from optparse import OptionParser

class ArgumentError(Exception):
  pass

class CoreFlags:
  """Command line common library"""
  def __init__(self, usage):
    """Initializes parser, sets flags for all classes"""
    self.parser = OptionParser(version='%%prog (Roster %s)' % __version__,
                               usage=usage)
    self.SetDataFlags()
    self.SetActionFlags()
    self.SetCoreFlags()
    if( hasattr(self, 'SetToolFlags') ):
      self.SetToolFlags()

  def SetCoreFlags(self):
    """Sets core flags for parser"""
    self.parser.add_option(
        '-s', '--server', action='store', dest='server',
        help='XML RPC Server URL.', metavar='<server>', default=None)
    self.parser.add_option(
        '-u', '--username', action='store', dest='username',
        help='Run as different username.', metavar='<username>',
        default=unicode(getpass.getuser()))
    self.parser.add_option(
        '-p', '--password', action='store', dest='password',
        help='Password string, NOTE: It is insecure to use this '
             'flag on the command line.', metavar='<password>', default=None)
    self.parser.add_option(
        '-c', '--cred-file', action='store', dest='credfile',
        help='Location of credential file.', metavar='<cred-file>',
        default=None)
    self.parser.add_option(
        '--cred-string', action='store', dest='credstring',
        help='String of credential.', metavar='<cred-string>', default=None)
    self.parser.add_option(
        '--config-file', action='store', dest='config_file',
        help='Config file location.', metavar='<file>', default=None)

  def GetOptionsObject(self, args):
    """Gets options object that tools use

    Outputs:
      options object
    """
    (options, args) = self.parser.parse_args(args)
    return options
