#!/usr/bin/python

# Copyright (c) 2010, Purdue University
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
# SERVICES; LOSS OF USjjE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Punycode and Unicode convertor module for Roster"""


__copyright__ = 'Copyright (C) 2010, Purdue University'
__license__ = 'BSD'
__version__ = "0.16"


def Uni2Puny(unicode_string=None):
  """Converts a unicode domain into a punycoded domain.

  Inputs:
    unicode/string: String or unicode of domain.

  Outputs:
    string: A punycoded domain string.
  """
  if( unicode_string == None ):
    return
  else:
    try:
      unicode_string = unicode_string.decode('utf-8')
    except UnicodeEncodeError:
      pass

  ## Split the domain name into levels.
  unicode_string = unicode_string.split('.')

  ## For each level of the domain, check if it is unicode.
  ## If it is, Punycode the level.
  punycode_string = ''
  for level in unicode_string:
    is_unicode = False
    if( punycode_string != '' ):
      punycode_string = '%s.' % (punycode_string)
    for char in level:
      if( ord(char) > 127 ):
        is_unicode = True
        break
    if( is_unicode ):
      punycode_string = 'xn--%s' % (punycode_string)
      punycode_string = '%s%s' % (punycode_string, level.encode('punycode'))
    else:
      punycode_string = '%s%s' % (punycode_string, level.encode('utf-8'))
  return punycode_string

def Puny2Uni(punycode_string=None):
  """Converts a Punycoded domain into a unicode domain.

  Inputs:
    string: Punycoded domain.

  Outputs:
    unicode: Decoded punycode domain.
  """
  if( punycode_string == None ):
    return

  ## Split the domain name into levels.
  punycode_string = punycode_string.split('.')

  ## For each level of the domain, check if it is Punycode.
  ## If it is, decode it to unicode.
  unicode_string = u''
  for level in punycode_string:
    if( unicode_string != '' ):
      unicode_string = '%s.' % (unicode_string)
    if( level.find('xn--') == 0 ):
      level = level.replace('xn--','')
      unicode_string = '%s%s' % (unicode_string, level.decode('punycode'))
    else:
      unicode_string = '%s%s' % (unicode_string, level)
  return unicode_string

