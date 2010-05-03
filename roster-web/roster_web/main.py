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

"""This is a page used for mod_python. It lists records of a given CIDR"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


from mod_python import apache
from mod_python import util
import roster_core
from roster_core import core_helpers
from roster_web import web_lib

CONFIG_FILE = '/etc/roster/roster_web.conf'

# set this variable from whatever authentication system that is used
authenticated_user = u'sharrell'

def handler(request):
  """Apache handler

  Inputs:
    request: apache request object
  """
  request_file = request.filename.split('/')[-1]

  if( request_file == 'edit_records.py' ):
    request.content_type = "text/html"


    html_page = web_lib.MakeHtmlHeader()

    post_get_dict = util.FieldStorage(request)

    if( 'edit' in post_get_dict ):
      cidr_block = unicode(post_get_dict['cidr_block'])
      view_name = unicode(post_get_dict['view_name'])
      error_ips = {}

      core_instance = roster_core.Core(authenticated_user,
                                       roster_core.Config(
                                           CONFIG_FILE))

      helper_instance = roster_core.CoreHelpers(core_instance)

      records_dict = web_lib.ProcessPostDict(post_get_dict)

      add_dict, remove_dict, errors_to_show = web_lib.MakeChangelist(
          records_dict, post_get_dict)

      html_page.append('\n'.join(errors_to_show))
      all_ips = helper_instance.CIDRExpand(cidr_block)
      error_ips.update(web_lib.CheckChanges(remove_dict, core_instance,
                                            view_name, action='remove'))
      error_ips.update(web_lib.CheckChanges(add_dict, core_instance, view_name,
                                            action='add'))
      records = helper_instance.ListRecordsByCIDRBlock(cidr_block,
                                                       view_name=view_name) 
      if( len(error_ips) == 0 ):
        new_error_ips = web_lib.PushChanges(add_dict, remove_dict, error_ips,
                                            html_page, core_instance,
                                            helper_instance, view_name)
        for ip_address in new_error_ips:
          AddError(ip_address, new_error_ips[ip_address], error_ips)
      else:
        html_page.append("<b>ADDED: 0 forward 0 reverse,"
                         " REMOVED: 0 forward 0 reverse, ERRORS: %s</b>" % (
            len(error_ips)))
      changed_records = {'add': add_dict, 'remove': remove_dict}
      html_page.extend(web_lib.PrintAllRecordsPage(
                           view_name, records, all_ips, cidr_block,
                           error_ips=error_ips,
                           changed_records=changed_records))

    elif( not 'cidr_block' in post_get_dict ):
      html_page.extend(web_lib.PrintGetCIDRPage())

    else:
      cidr_block = unicode(post_get_dict['cidr_block'])
      view_name = unicode(post_get_dict['view_name'])

      core_instance = roster_core.Core(authenticated_user,
                                       roster_core.Config(
                                           CONFIG_FILE))

      helper_instance = roster_core.CoreHelpers(core_instance)
      records = helper_instance.ListRecordsByCIDRBlock(cidr_block,
                                                       view_name=view_name) 
  
      if( not view_name in records ):
        html_page.append('No records found for view "%s"' % view_name)

      else:
        all_ips = helper_instance.CIDRExpand(cidr_block)
        html_page.extend(web_lib.PrintAllRecordsPage(view_name, records,
                         all_ips, cidr_block))
      

    html_page.append('</body>')
    html_page.append('</html>')
    

    request.write('\n'.join(html_page))

    return apache.OK

  else:
    return apache.HTTP_NOT_FOUND
