#!/usr/bin/env python

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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Fake smtplib module to use with testing dnsexportconfig for Roster"""

__copyright__ = 'Copyright (C) 2012, Dovahkiin'
__license__ = 'BAMF'
__version__ = '0.18'

import os
import socket

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class SMTPConnectError(Exception):
  pass

class SMTPRecipientsRefused(Exception):
  pass

class SMTP(object):
  """Fake SMTP class

  THIS IS A FAKE CLASS AND IS NOT MEANT TO BE USED FOR PRODUCTION

  The purpose of this class is to provide a fake smtplib class
  for Roster testing purposes only.
  """
  error = None
  def __init__(self, server):
    self.error = os.getenv('ROSTERTESTSMTPERROR')
    if( self.error == 'server_error' ):
      raise socket.gaierror()
    elif( self.error == 'connect_error' ):
      raise SMTPConnectError()

  def sendmail(self, from_address, to_addresses, message):
    if( self.error == 'message_error' ):
      raise SMTPRecipientsRefused()
    print 'Email: \n%s' % message

  def quit(self):
    pass
