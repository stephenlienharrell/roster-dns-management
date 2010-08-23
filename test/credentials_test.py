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


"""Test for Credential cache library."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import unittest
import os

import roster_core
from roster_server import credentials


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'


class TestCredentialsLibrary(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.cred_instance = credentials.CredCache(self.config_instance,
                                               u'sharrell')
    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

  def is_valid_uuid (self, uuid):
    """
    TAKEN FROM THE BLUEZ MODULE

    is_valid_uuid (uuid) -> bool

    returns True if uuid is a valid 128-bit UUID.

    valid UUIDs are always strings taking one of the following forms:
        XXXX
        XXXXXXXX
        XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    where each X is a hexadecimal digit (case insensitive)
    """
    try:
      if len (uuid) == 4:
        if int (uuid, 16) < 0: return False
      elif len (uuid) == 8:
        if int (uuid, 16) < 0: return False
      elif len (uuid) == 36:
        pieces = uuid.split ("-")
        if len (pieces) != 5 or \
              len (pieces[0]) != 8 or \
              len (pieces[1]) != 4 or \
              len (pieces[2]) != 4 or \
              len (pieces[3]) != 4 or \
              len (pieces[4]) != 12:
          return False
        [ int (p, 16) for p in pieces ]
      else:
        return False
    except ValueError:
      return False
    except TypeError:
      return False
    return True

  def testCredentials(self):
    self.assertTrue(self.cred_instance.Authenticate(u'sharrell', 'test'))
    cred_string = self.cred_instance.GetCredentials(u'sharrell', 'test',
                                                    self.core_instance)
    self.assertEqual(self.cred_instance.CheckCredential(cred_string,
                                                        u'sharrell',
                                                       self.core_instance),
                     u'')
    self.assertEqual(self.cred_instance.CheckCredential(u'test', u'sharrell',
                                                        self.core_instance),
                     None)

if( __name__ == '__main__' ):
  unittest.main()
