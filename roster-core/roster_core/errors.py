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

"""Central collection of base error classes in the RosterCore."""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'

PARSABLE_MYSQL_ERRORS = [1452]

class CoreError(Exception):
  """Error class that all Roster errors are 
  sub-classed from
  """
  pass

class InternalError(CoreError):
  """Error class that all internal/code errors
  sub-class from.
  """
  pass

class UserError(CoreError):
  """Error class that all User errors
  sub-class from.
  """
  pass

class AuthenticationError(UserError):
  pass

class AuthorizationError(UserError):
  pass

class ConfigError(UserError):
  pass

class InvalidInputError(UserError):
  pass

class ReservedWordError(UserError):
  pass

class IPIndexError(InternalError):
  pass

class MaintenanceError(InternalError):
  pass

class UnexpectedDataError(UserError):
  pass

class DatabaseError(UserError):
  """Raised when DatabaseError is raised and changes its value
     to be more readable
  """
  def __init__(self, value):
    """Sets instance variable for value"""
    self.value = value
  def __str__(self):
    """Python standard string method, makes value string
       easier to understand.

    Outputs:
      str: reformatted error string
    """
    array = self.value[1].split(' ')
    if( self.value[0] == 1452 ):
      foreign_index = array.index('FOREIGN')
      attribute = array[-2].strip('(`)')
      if( attribute == 'view_dependency' ):
        attribute = 'view'
      elif( attribute == 'zone_view_assignments' ):
        attribute = 'zone or view'
      self.value = "Specified %s does not exist." % attribute
    return self.value

class RecordError(InternalError):
  pass

class RecordsBatchError(InternalError):
  pass

class FunctionError(InternalError):
  pass

class VersionDiscrepancyError(InternalError):
  pass

class DbAccessError(InternalError):
  pass

class TransactionError(DbAccessError):
  pass

class MissingDataTypeError(DbAccessError):
  pass
