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

"""Action flags lib, flags in all ls, mk, rm tools."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import core_flags


class List(core_flags.CoreFlags):
  """Command line ls flags"""
  def SetActionFlags(self):
    """Sets list flags for parser"""
    self.action = 'List'

    self.parser.add_option(
        '--no-header', action='store_true', dest='no_header',
        help='Do not display a header.', default=False)
    self.AddFlagRule('no_header', required=False)


class Remove(core_flags.CoreFlags):
  """Command line rm flags"""
  def SetActionFlags(self):
    """Sets remove flags for parser"""
    self.action = 'Remove'

    self.parser.add_option(
        '-q', '--quiet', action='store_true', dest='quiet',
        help='Suppress program output.', default=False)
    self.AddFlagRule('quiet', required=False)
    self.parser.add_option(
        '--force', action='store_true', dest='force',
        help='Force actions to complete.', default=False)


class Make(core_flags.CoreFlags):
  """Command line mk flags"""
  def SetActionFlags(self):
    """Sets make flags for parser"""
    self.action = 'Make'

    self.parser.add_option(
        '-q', '--quiet', action='store_true', dest='quiet',
        help='Suppress program output.', default=False)
    self.AddFlagRule('quiet', required=False)

class Update(core_flags.CoreFlags):
  """Command line up flags"""
  def SetActionFlags(self):
    """Sets update flags for parser"""
    self.action = 'Update'

    self.parser.add_option('--keep-output', action='store_true',
                           dest='keep_output', help='Keep output file.',
                           default=False)
    self.AddFlagRule('keep_output', required=False, command='update')
    self.AddFlagRule('keep_output', required=False, command='edit')
