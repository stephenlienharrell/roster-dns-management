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


"""PAM module for PAM authentication in RosterServer."""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import PAM


class AuthenticationMethod(object):
  """PAM Authentication class.
  
  Most of this code borrowed from
  http://people.debian.org/~goedson/ejabberd/ejabberd_pam_authentication.py
  Which is under the GPL v2 license.
  """
  def __init__(self):
    self.requires = {} 

  def PAMAuthConversation(self, user_name, password):
    """Defines a PAM conversation function to pass user_name and password."""
    def pam_conversation(auth, query_list, userdata):
        """Does the conversation to feed PAM with user_name and password."""
        resp = []
        for i in range(len(query_list)):
            _, query_type = query_list[i]
            if query_type == PAM.PAM_PROMPT_ECHO_ON:
                val = user_name
                resp.append((val, 0))
            elif query_type == PAM.PAM_PROMPT_ECHO_OFF:
                val = password
                resp.append((val, 0))
            else:
                return None
        return resp
    return pam_conversation 


def Authenticate(self, user_name=None, password=None):
    """Check, using PAM, if the user_name and password provided match."""
    auth = PAM.pam()
    auth.start('passwd')
    auth.set_item(PAM.PAM_CONV, self.PAMAuthConversation(user_name, password))
    try:
        auth.authenticate()
    except PAM.error:
        return False
    except:
        return False
    else:
        return True
