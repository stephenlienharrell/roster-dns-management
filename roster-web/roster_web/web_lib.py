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

"""Roster web library"""


__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.14'


from roster_core import core_helpers


def MakeHtmlHeader():
  """Makes html page header
  
  Outputs:
    list: list of html_page strings
      ex: ['<html><head><title>Roster Web</title></head>',
           '<body>', '<style>\ntable{ \n  border-collapse: colapse;\n'
                     '}\ntd {\n  border: 1px solid #000000;\n}\n'
                     'body {\n  font-family: Arial;\n}\n</style>']
  """
  html_page = ['<html><head><title>Roster Web</title></head>']
  html_page.append('<body>')
  html_page.append(
      '<style>\n'
      'table {\n'
      '  border-collapse: collapse;\n'
      '}\n'
      'td {\n'
      '  border: 1px solid #000000;\n'
      '}\n'
      'body {\n'
      '  font-family: Arial;\n'
      '}\n'
      '</style>')
  html_page.append('<b><u>Roster Web</b></u><br /><br />')

  return html_page


def MakeChangelist(records_dict, post_get_dict):
  """Makes organized lists of record changes from users changes

  Inputs:
    records_dict: dictionary of records
    post_get_dict: dictionary of postdata from apache

  Outputs:
    tuple: (add_dict, remove_dict, errors_to_show)
      ex: ({'192.168.1.1': {
        'forward': '1', 'reverse': '0', 'default_forward': '1',
        'default_reverse': '0', 'fqdn': 'newfqdn.',
        'default_fqdn': 'oldfqdn.', 'default_host': 'oldhost',
        'host': 'newhost'}},
        {'192.168.1.1': {
        'forward': '0', 'reverse': '1', 'default_forward': '0',
        'default_reverse': '1', 'fqdn': 'newfqdn.',
        'default_fqdn': 'oldfqdn.', 'default_host': 'oldhost',
        'host': 'newhost'}},
        ['Error messages', 'here'])
  """
  add_dict = {}
  remove_dict = {}
  errors_to_show = []
  valid_keys = [('default_forward', 'forward'),
                ('default_reverse', 'reverse'),
                ('default_fqdn', 'fqdn'), ('default_host', 'host')]
  for record in records_dict:
    if( record in ['name', 'block', 'addresses', 'edit'] ):
      continue
    for keys in valid_keys:
      if( keys[0] in records_dict[record] and
          keys[1] in records_dict[record] ):
        if( records_dict[record][keys[0]] !=
            records_dict[record][keys[1]] ):
          if( record not in add_dict ):
            add_dict[record] = {}
          if( record not in remove_dict ):
            remove_dict[record] = {}
          remove_dict[record][keys[1]] = records_dict[record][keys[0]]
          add_dict[record][keys[1]] = records_dict[record][keys[1]]
      elif( keys[0] in records_dict[record] and
          keys[1] not in records_dict[record] ):
        if( record not in remove_dict ):
          remove_dict[record] = {}
        remove_dict[record][keys[1]] = records_dict[record][keys[0]]
      elif( keys[0] not in records_dict[record] and
          keys[1] in records_dict[record] ):
        if( record not in add_dict ):
          add_dict[record] = {}
        add_dict[record][keys[1]] = records_dict[record][keys[1]]

  for ip_field in post_get_dict['ip_addresses']:
    ip_address = unicode(ip_field)
 
    chunks_available = 0
    if( 'default_fqdn_%s' % ip_address in post_get_dict ): 
      chunks_available += 1
    if( 'fqdn_%s' % ip_address in post_get_dict ): 
      chunks_available += 1
    if( 'default_host_%s' % ip_address in post_get_dict ): 
      chunks_available += 1
    if( 'host_%s' % ip_address in post_get_dict ): 
      chunks_available += 1

    if( chunks_available > 0 and chunks_available < 2):
      errors_to_show.append('Record %s not filled out completely.' %
                            ip_address)
  return (add_dict, remove_dict, errors_to_show)


def AddRow(html_page, record_html_data, color=None):
  """Adds row to html_page

  Inputs:
    html_page: html page object
    record_html_data: dictionary of data to add

  Outputs:
    list: html page strings
  """
  if( color is not None ):
    html_page.append('<tr bgcolor="%s">' % color)
  else:
    html_page.append('<tr>')
  html_page.append('<td>'
                   '<input type="hidden" '
                           'name="ip_addresses" '
                           'value="%(ip_address)s" />'
                   '%(real_ip_address)s'
                   '</td>'
                   '<td>'
                   '<input type="checkbox" '
                          'name="forward_reverse_%(ip_address)s" '
                          'value="forward" %(forward)s />'
                   '<input type="hidden" '
                           'name="default_forward_%(ip_address)s" '
                           'value="%(default_forward)s" />'
                   '</td>' 
                   '<td>'
                   '<input type="checkbox" '
                          'name="forward_reverse_%(ip_address)s" '
                          'value="reverse" %(reverse)s />'
                   '<input type="hidden" '
                           'name="default_reverse_%(ip_address)s" '
                           'value="%(default_reverse)s" />'
                   '</td>'
                   '<td>'
                   '<input type="hidden" '
                          'name="default_fqdn_%(ip_address)s" '
                          'value="%(default_fqdn)s" />'
                   '%(default_fqdn)s</td>'
                   '<td>'
                   '<input type="text" '
                          'name="host_%(ip_address)s" '
                          'value="%(host_name)s" />'
                   '<input type="hidden" '
                          'name="default_host_%(ip_address)s" '
                          'value="%(default_host_name)s" />'
                   '</td> '
                   '<td>'
                   '<input type="text" '
                           'name="fqdn_%(ip_address)s" '
                           'value="%(fqdn)s" />'
                   '</td>'
                   '</tr>' % record_html_data)
  return html_page


def AddError(ip_address, error, error_ips):
  """Adds error to error_ips

  Inputs:
    ip_address: string of ip address
    error: string of error message
    error_ips: dictionary of ips with errors

  Outputs:
    dict: dictionary of ips with errors
      ex: {'192.168.1.1-0': 'Host already exists.'}
  """
  if( ip_address not in error_ips ):
    error_ips[ip_address] = []
  error_ips[ip_address].append(error)
  error_ips[ip_address] = list(set(error_ips[ip_address]))
  return error_ips


def CheckChanges(records_dict, core_instance, view_name, error_ips,
                 action=None):
  """Does error cheking for changes

  Inputs:
    add_dict: dictionary of records to add
    remove_dict: dictionary of records to remove
    core_instance: core_instance from roster_core
    view_name: string of view name

  Outputs:
    dict: dictionary of error ips
      ex: {'192.168.1.1': 'Host already exists.'}
  """
  for ip_address in records_dict:
    # Check if fqdn has been changed
    if( 'fqdn' not in records_dict[ip_address] ):
      error_ips = AddError(
          ip_address, "FQDN of %s needs to be updated." % ip_address,
          error_ips)
      continue
    # Check if host has been changed
    if( 'host' not in records_dict[ip_address] ):
      error_ips = AddError(
          ip_address, "HOST of %s needs to be updated." % ip_address,
          error_ips)
      continue
    # Check for . in hostname
    if( '.' in records_dict[ip_address]['host'] ):
      error_ips = AddError(
          ip_address,
          'The use of "." in the hostname is not allowed.',
          error_ips)
      continue
    # Check if fqdn matches part of host
    if( not records_dict[ip_address]['fqdn'].startswith(records_dict[
        ip_address]['host']) ):
      error_ips = AddError(
          ip_address, "FQDN must start with HOST for %s" % ip_address,
          error_ips)
      continue
    # Try to get zone
    try:
      zone_origin = u'%s.' % records_dict[ip_address]['fqdn'].split(
          records_dict[ip_address]['host'])[1].lstrip('.')
    except:
      error_ips = AddError(ip_address,
               "No matching domain for %s" % records_dict[ip_address]['fqdn'],
               error_ips)
      continue
    zone = core_instance.ListZones(zone_origin=zone_origin)
    # Check if zone is found
    if( len(zone) < 1 ):
      error_ips = AddError(ip_address,
               "No matching domain for %s" % records_dict[ip_address]['fqdn'],
               error_ips)
      continue
    records  = core_instance.ListRecords(
        record_type=u'a', target=unicode(records_dict[ip_address]['host']),
        zone_name=zone.keys()[0],
        record_args_dict={u'assignment_ip': ip_address.split('-')[0]},
        view_name=unicode(view_name))
    # Check if multiple records exist for single ip
    if( len(records) > 1 ):
      error_ips = AddError(ip_address, "Multiple records found for %s" % (
          ip_address), error_ips)
    # Check if record already exists
    if( len(records) != 0 and action == 'add' ):
      error_ips = AddError(ip_address, "Record exists for %s" % ip_address,
                           error_ips)
    # Check if record does not exist
    if( len(records) == 0 and action == 'remove' ):
      error_ips = AddError(ip_address, "Record for %s not found" % ip_address,
                           error_ips)
    # Check if there are multiple zones found
    if( len(zone) > 1 ):
      error_ips = AddError(
          ip_address, "Multiple zones found with origin %s" % zone_origin,
          error_ips)
    # Check if view name matches with zone
    if( view_name not in zone[zone.keys()[0]] ):
      error_ips = AddError(ip_address, "View %s not found in zone %s" % (
          view_name, zone.keys()[0]), error_ips)

  return error_ips


def PushChanges(add_dict, remove_dict, error_ips, html_page, core_instance,
                helper_instance, view_name):
  """Does final error checking and writes changes to database

  Inputs:
    add_dict: dictionary of records to add
    remove_dict: dictionary of records to remove
    error_ips: dictionary of ips with errors
    html_page: list of html strings
    core_instance: instance of roster_core
    helper_instance: instance of roster_core helpers
    view_name: string of view name

  Outputs:
    dict: dictionary of error ips
      ex: {'192.168.1.1': 'Host already exists.'}
  """
  added_forward = 0
  added_reverse = 0
  removed_forward = 0
  removed_reverse = 0
  add_records = []
  delete_records = []
  if( len(error_ips) == 0 ):
    # Compile list of records to remove
    for ip_address in remove_dict:
      real_ip_address = ip_address.split('-')[0]
      zone_origin = u'%s.' % remove_dict[ip_address]['fqdn'][len(remove_dict[
        ip_address]['host']) + 1:]
      zone = core_instance.ListZones(zone_origin=zone_origin)
      delete_records.append(
          {'record_type': u'a',
           'record_target': unicode(remove_dict[ip_address]['host']),
           'view_name': unicode(view_name),
           'record_zone_name': unicode(zone.keys()[0]),
           'record_arguments': {u'assignment_ip': unicode(real_ip_address)}})
      removed_forward += 1
      ptr_target = helper_instance.GetPTRTarget(
          unicode(real_ip_address), unicode(view_name))
      delete_records.append(
          {'record_type': u'ptr',
           'record_target': unicode(ptr_target[0]),
           'view_name': unicode(view_name),
           'record_zone_name': unicode(ptr_target[1]),
           'record_arguments': {u'assignment_host': unicode(
               '%s.' % remove_dict[ip_address]['fqdn'])}})
      removed_reverse += 1

    # Compile list of records to add
    for ip_address in add_dict:
      real_ip_address = ip_address.split('-')[0]
      zone_origin = u'%s.' % add_dict[ip_address]['fqdn'][len(add_dict[
        ip_address]['host']) + 1:]
      zone = core_instance.ListZones(zone_origin=zone_origin);
      add_records.append(
          {'record_type': u'a',
           'record_target': unicode(add_dict[ip_address]['host']),
           'view_name': unicode(view_name),
           'record_zone_name': unicode(zone.keys()[0]),
           'record_arguments': {u'assignment_ip': unicode(real_ip_address)}})
      added_forward += 1
      ptr_target = helper_instance.GetPTRTarget(
          unicode(real_ip_address), unicode(view_name))
      add_records.append(
          {'record_type': u'ptr',
           'record_target': unicode(ptr_target[0]),
           'view_name': unicode(view_name),
           'record_zone_name': unicode(ptr_target[1]),
           'record_arguments': {u'assignment_host': unicode(
               '%s.' % add_dict[ip_address]['fqdn'])}})
      added_reverse += 1
    error_ips = {}
    try:
      helper_instance.ProcessRecordsBatch(delete_records=delete_records,
                                          add_records=add_records)
    except core_helpers.RecordsBatchError, e:
      added_forward = 0
      added_reverse = 0
      removed_forward = 0
      removed_forward = 0
      for ip_address in add_dict:
        if( add_dict[ip_address]['host'] == str(e).split(':')[0] ):
          # Grab error and add it to error_ips
          error_ips[ip_address] = str(e).split(':')[1]
      for ip_address in remove_dict:
        if( remove_dict[ip_address]['host'] == str(e).split(':')[0] ):
          # Grab error and add it to error_ips
          error_ips[ip_address] = str(e).split(':')[1]
      html_page.append("<b>An error has occurred!</b><br>")

  html_page.append("<b>ADDED: %s forward %s reverse,"
                   " REMOVED: %s forward %s reverse, ERRORS: %s</b>" % (
      added_forward, added_reverse, removed_forward, removed_reverse,
      len(error_ips)))

  return error_ips


def PrintAllRecordsPage(view_name, records, all_ips, cidr_block,
                        changed_records={}, error_ips={}):
  """Prints table with list of records

  Inputs:
    view_name: string of view name
    records: dictionary of records
    all_ips: list of all ip addresses in cidr
    cidr_block: string of cidr_block
    changed_records: dictionary of changed records
    error_ips: dictionary of error ips

  Outputs:
    list: list of strings of html page including table and rows of records
  """
  html_page = ['<form action="edit_records.py" method="post">']
  html_page.append('<input type="submit" value="Submit" />')
  html_page.append('<table><tr><td>Existing Record</td>'
                   '<td bgcolor="#FF6666">Error Record</td>'
                   '<td bgcolor="#66FF66">Add Record</td>'
                   '<td bgcolor="#6666FF">Remove Record</td>'
                   '<td bgcolor="#FFFF66">Change Record</td</tr></table>')
  html_page.append('<input type="hidden" name="cidr_block" value="%s" />' % 
                   cidr_block)
  html_page.append('<input type="hidden" name="view_name" value="%s" />' % 
                   view_name)
  html_page.append('<input type="hidden" name="edit" value="true" />')
  html_page.append('<table border="1">')
  html_page.append('<tr><td>IP Address</td><td>Forward Record</td>')
  html_page.append('<td>Reverse Record</td>')
  html_page.append('<td>Originial Full Qualifed Name</td>')
  html_page.append('<td>New Host Name</td><td>New Full Qualifed Name</td>')


  records = records[view_name]
  record_ips = records.keys()
  record_data = {}

  colored_row = False
  for ip in all_ips:
    record_html_data = {'default_forward': '',
                        'default_reverse': '',
                        'forward': '', 'reverse': '',
                        'default_host_name': '',
                        'default_fqdn': '',
                        'host_name': '', 'fqdn': '',
                        'ip_address': '%s-0' % ip,
                        'real_ip_address': ip}
    zone_origins = []
    duplicates = {}
    if( ip in records ):
      added_row = False
      for record in records[ip]:
        zone_origins.append(record['zone_origin'])
      zone_origins = set(zone_origins)
      for zone_origin in zone_origins:
        for record in records[ip]:
          if( record['host'].endswith(zone_origin.rstrip('.')) ):
            if( zone_origin not in duplicates ):
              duplicates[zone_origin] = []
            duplicates[zone_origin].append(record)
      for index, duplicate in enumerate(duplicates):
        if( duplicate in changed_records ):
          record_data = changed_records[duplicate]
        else:
          for record_data in duplicates[duplicate]:
            record_html_data['default_fqdn'] = record_data['host']
            
            if( record_data['forward'] ):
              record_html_data['default_forward'] = 1
              record_html_data['default_host_name'] = record_data['host'].split(
                  record_data['zone_origin'].rstrip('.'))[0].strip('.')
            else:
              record_html_data['default_reverse'] = 1

            record_html_data['fqdn'] = record_html_data['default_fqdn']

            if( not record_html_data['host_name'] ):
              record_html_data['host_name'] = record_html_data[
                  'default_host_name']
            if( not record_html_data['forward'] and
                record_html_data['default_forward' ]):
              record_html_data['forward'] = 'checked="checked"'
            if( not record_html_data['reverse'] and
                record_html_data['default_reverse'] ):
              record_html_data['reverse'] = 'checked="checked"'
        record_html_data['ip_address'] = '%s-%s' % (record_html_data[
            'ip_address'].split('-')[0], index)

        record_html_data = UpdateInputBoxes(
            changed_records, record_html_data, error_ips)

        if( record_html_data['ip_address'] in error_ips ):
          # Record with error
          html_page = AddRow(html_page, record_html_data, '#FF6666')
          html_page.append("<tr><td colspan=6 bgcolor=#FF6666>%s</td></tr>" % (
            ', '.join(error_ips[record_html_data['ip_address']])))
          added_row = True
        elif( changed_records ):
          if( record_html_data['ip_address'] in changed_records['add'] and
              record_html_data['ip_address'] in changed_records['remove'] ):
            # Changed record
            html_page = AddRow(html_page, record_html_data, '#FFFF66')
            added_row = True
          elif( record_html_data['ip_address'] in changed_records['add'] ):
            # Added record
            html_page = AddRow(html_page, record_html_data, '#66FF66')
            added_row = True
          elif( record_html_data['ip_address'] in changed_records['remove'] ):
            # Removed record
            html_page = AddRow(html_page, record_html_data, '#6666FF')
            added_row = True
          else:
            # existing or blank record
            html_page = AddRow(html_page, record_html_data,
                   "#EEEEEE" if colored_row else None )
            added_row = True
        else:
          # existing or blank record
          html_page = AddRow(html_page, record_html_data,
                 "#EEEEEE" if colored_row else None )
          added_row = True
        colored_row = not colored_row
      if( not added_row ):
        for record in records[ip]:
          if( record['forward'] ):
            record_html_data['default_forward'] = 1
            record_html_data['forward'] = 'checked="checked"'
            record_html_data['default_host_name'] = record_data['host'].split(
                record_data['zone_origin'].rstrip('.'))[0].strip('.')
            record_html_data['host_name'] = record_html_data[
                'default_host_name']
            record_html_data['default_fqdn'] = record_data['host']
            record_html_data['fqdn'] = record_data['host']
          else:
            record_html_data['default_reverse'] = 1
            record_html_data['reverse'] = 'checked="checked"'
            record_html_data['default_fqdn'] = record['host']
            record_html_data['fqdn'] = record['host']
          # Record with unknown error
          html_page = AddRow(html_page, record_html_data,
                 "#FF6666")
          colored_row = not colored_row
    else:
      record_html_data['default_forward'] = 1
      record_html_data['default_reverse'] = 1
      record_html_data['forward'] = 'checked="checked"'
      record_html_data['reverse'] = 'checked="checked"'

      UpdateInputBoxes(changed_records, record_html_data, error_ips)

      if( record_html_data['ip_address'] in error_ips ):
        html_page = AddRow(html_page, record_html_data, '#FF6666')
        html_page.append("<tr><td colspan=6 bgcolor=#FF6666>%s</td></tr>" % (
          ', '.join(error_ips[record_html_data['ip_address']])))
      elif( changed_records ):
        if( record_html_data['ip_address'] in changed_records['add'] and
            record_html_data['ip_address'] in changed_records['remove'] ):
          # Changed record
          html_page = AddRow(html_page, record_html_data, '#000000')
        elif( record_html_data['ip_address'] in changed_records['add'] ):
          # Added record
          html_page = AddRow(html_page, record_html_data, '#66FF66')
        elif( record_html_data['ip_address'] in changed_records['remove'] ):
          # Removed record
          html_page = AddRow(html_page, record_html_data, '#6666FF')
        else:
          # Existing or blank record
          html_page = AddRow(html_page, record_html_data,
                 "#EEEEEE" if colored_row else None )
      else:
        # Existing or blank record
        html_page = AddRow(html_page, record_html_data,
                           "#EEEEEE" if colored_row else None )
      colored_row = not colored_row

  html_page.append('</table>')
  html_page.append('<input type="submit" value="Submit" />')
  html_page.append('</form>')
  return html_page


def UpdateInputBoxes(changed_records, record_html_data, error_ips):
  """Restores user input after data has been submitted

  Inputs:
    changed_records: dictionary of changed records
    record_html_data: dictionary of record values
    error_ips: dictionary of error ips
    html_page: list of strings of html page

  Outputs:
    dict: updated record_html_dictionary
      ex: {'192.168.1.1-0': {
          'host_name': 'newhost1', 'default_host_name': 'oldhost1',
          'fqdn': 'newfqdn.', 'default_fqdn': 'oldfqdn.'}}
  """
  old_hostname = record_html_data['host_name']
  old_fqdn = record_html_data['fqdn']
  if( changed_records ):
    if( record_html_data['ip_address'] in changed_records['remove'] ):
      record_html_data['host_name'] = ''
      record_html_data['fqdn'] = ''
      if( not error_ips ):
        record_html_data['default_fqdn'] = ''
        record_html_data['default_host_name'] = ''
    if( record_html_data['ip_address'] in changed_records['add'] ):
      if( 'fqdn' not in changed_records['add'][record_html_data[
            'ip_address']] ):
        changed_records['add'][record_html_data['ip_address']][
            'fqdn'] = old_fqdn
        record_html_data['fqdn'] = record_html_data['default_fqdn']
      if( 'host' not in changed_records['add'][record_html_data[
            'ip_address']] ):
        changed_records['add'][record_html_data['ip_address']][
            'host'] = record_html_data['default_host_name']
        record_html_data['host_name'] = record_html_data['default_host_name']
      elif( old_hostname != changed_records['add'][record_html_data[
              'ip_address']]['host'] ):
        record_html_data['host_name'] = changed_records['add'][
            record_html_data['ip_address']]['host']
      if( old_fqdn != changed_records['add'][record_html_data[
              'ip_address']]['fqdn'] ):
        record_html_data['fqdn'] = changed_records['add'][
            record_html_data['ip_address']]['fqdn']
        if( len(error_ips) == 0 ):
          record_html_data['default_fqdn'] = changed_records['add'][
              record_html_data['ip_address']]['fqdn']
          record_html_data['default_host_name'] = changed_records['add'][
              record_html_data['ip_address']]['host']

  return record_html_data


def PrintGetCIDRPage():
  """Makes html page to get initial cidr

  Outputs:
    list: list of initial html strings to get cidr
  """
  html_page = ['<form action="edit_records.py" method="post">']
  html_page.append('Enter CIDR block to edit: ')
  html_page.append('<input type="text" name="cidr_block" /><br />')
  html_page.append('Enter view name: ')
  html_page.append( '<input type="text" name="view_name" value="any" />')
  html_page.append('<input type="submit" value="Submit" />')
  html_page.append('</form>')
  return html_page

def ProcessPostDict(post_get_dict):
  """Processes postdata from apache

  Inputs:
    post_get_dict: dictionary of postdata from apache

  Outputs:
    dict: dictionary of record values
      ex: {'192.168.1.1': {
        'forward': '1', 'reverse': '0', 'default_forward': '1',
        'default_reverse': '0', 'fqdn': 'newfqdn.',
        'default_fqdn': 'oldfqdn.', 'default_host': 'oldhost',
        'host': 'newhost'}}
  """
  keys = post_get_dict.keys()
  keys.sort()
  records_dict = {}
  temp_dict = {}
  for key in keys:
    key_array = key.split('_')
    ip_address = key_array[-1]
    sub_key = '_'.join(key_array[:len(key_array) - 1])
    if( ip_address not in temp_dict ):
      temp_dict[ip_address] = {}
    if( 'forward' not in temp_dict[ip_address] ):
      temp_dict[ip_address]['forward'] = '0'
    if( 'reverse' not in temp_dict[ip_address] ):
      temp_dict[ip_address]['reverse'] = '0'
    if( 'default_forward' not in temp_dict[ip_address] ):
      temp_dict[ip_address]['default_forward'] = '0'
    if( 'default_reverse' not in temp_dict[ip_address] ):
      temp_dict[ip_address]['default_reverse'] = '0'
    if( type(post_get_dict[key]) == list ):
      post_list = post_get_dict[key]
    else:
      post_list = [post_get_dict[key]]
    for post_item in post_list:
      duplicates = []
      duplicates.extend(post_item)
      if( key.startswith('cidr_block') ):
        pass
      elif( key.startswith('ip_addresses') ):
        pass
      elif( key.startswith('view_name') ):
        pass
      elif( key.startswith('addresses') ):
        pass
      elif( sub_key == 'forward_reverse' ):
        if( post_item.value == 'forward' ):
          temp_dict[ip_address]['forward'] = '1'
        if( post_item.value == 'reverse' ):
          temp_dict[ip_address]['reverse'] = '1'
      elif( sub_key == 'default_forward_reverse' ):
        if( post_item.value == 'forward' ):
          temp_dict[ip_address]['default_forward'] = '1'
        if( post_item.value == 'reverse' ):
          temp_dict[ip_address]['default_reverse'] = '1'
      else:
        temp_dict[ip_address][sub_key] = post_item.value
  for ip_address in temp_dict:
    records_dict[ip_address] = temp_dict[ip_address]

  return records_dict
