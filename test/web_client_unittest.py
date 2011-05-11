#!/usr/bin/python

# Copyright (c) 2009, university University
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
# Neither the name of the university University nor the names of its contributors
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

"""Unittest for web client

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, university University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import cPickle
import datetime
import os
import time
import unicodedata
import unittest

from roster_core import audit_log

import roster_core
from roster_core import core_helpers
from roster_web import web_lib # main web file



CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
TEMP_LOG = 'temp_log'


class Field(object):
  def __init__(self, name, value):
    self.name = name
    self.value = value
    self.data = [name, value]
  def __iter__(self):
    return self.data.__iter__()

  def __len__(self):
    return len(self.data)

  def __contains__(self, v):
    return v in self.data

  def __getitem__(self, v):
    return self.data[v]

class TestAuditLog(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.db_instance = db_instance

    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)
    self.helper_instance = roster_core.CoreHelpers(self.core_instance)

  def testMakeHtmlHeader(self):
    self.assertEqual(web_lib.MakeHtmlHeader(),
                     ['<html><head><title>Roster Web</title></head>',
                      '<body>', '<style>\ntable {\n  border-collapse: '
                                'collapse;\n}\ntd {\n  border: 1px solid '
                                '#000000;\n}\nbody {\n  font-family: Arial;\n'
                                '}\n</style>', '<b><u>Roster Web</b></u><br />'
                                '<br />'])
    self.assertEqual(web_lib.PrintGetCIDRPage(),
                     ['<form action="edit_records.py" method="post">',
                      'Enter CIDR block to edit: ',
                      '<input type="text" name="cidr_block" /><br />',
                      'Enter view name: ',
                      '<input type="text" name="view_name" value="any" />',
                      '<input type="submit" value="Submit" />', '</form>'])

  def testMakeChangelist(self):
    records_dict = {'192.168.1.1': {
        'forward': '1', 'reverse': '0', 'default_forward': '1',
        'default_reverse': '0', 'fqdn': 'newhost.oldfqdn.',
        'default_fqdn': 'oldhost.oldfqdn.', 'default_host': 'oldhost',
        'host': 'newhost'}}
    post_get_dict = {'ip_addresses': ['192.168.1.1'],
        'default_fqdn_192.168.1.1': 'oldhost.oldfqdn.',
        'fqdn_192.168.1.1': 'newhost.newfqdn.',
        'default_host_192.168.1.1': 'oldhost',
        'host_192.168.1.1': 'newhost'}
    add_dict, remove_dict, errors_to_show = web_lib.MakeChangelist(
        records_dict, post_get_dict)
    self.assertEqual(add_dict,
        {'192.168.1.1': {'host': 'newhost', 'fqdn': 'newhost.oldfqdn.'}})
    self.assertEqual(remove_dict,
        {'192.168.1.1': {'host': 'oldhost', 'fqdn': 'oldhost.oldfqdn.'}})
    self.assertEqual(errors_to_show, [])
    records_dict = {'192.168.1.1': {
        'forward': '1', 'reverse': '0', 'default_forward': '1',
        'default_reverse': '0', 'fqdn': 'newhost.oldfqdn.',
        'default_fqdn': 'oldhost.oldfqdn.', 'default_host': 'oldhost',
        'host': 'newhost'}}
    post_get_dict = {'ip_addresses': ['192.168.1.1'],
        'host_192.168.1.1': 'newhost'}
    add_dict, remove_dict, errors_to_show = web_lib.MakeChangelist(
        records_dict, post_get_dict)
    self.assertEqual(add_dict,
        {'192.168.1.1': {'host': 'newhost', 'fqdn': 'newhost.oldfqdn.'}})
    self.assertEqual(remove_dict,
        {'192.168.1.1': {'host': 'oldhost', 'fqdn': 'oldhost.oldfqdn.'}})
    self.assertEqual(errors_to_show,
        [u'Record 192.168.1.1 not filled out completely.'])

  def testAddRow(self):
    html_page = []
    record_html_data = {'host_name': 'newhost1', 'fqdn': 'newhost1.com.',
        'real_ip_address': '192.168.1.1', 'default_host_name': 'newhost1',
        'default_fqdn': 'newhost1.com.', 'ip_address': '192.168.1.1-0',
        'forward': '1', 'default_forward': '1', 'reverse': '1',
        'default_reverse': '1'}
    html_page = web_lib.AddRow(html_page, record_html_data)
    self.assertEqual(html_page,
        ['<tr>', '<td><input type="hidden" name="ip_addresses" '
                 'value="192.168.1.1-0" />192.168.1.1</td><td><input '
                 'type="checkbox" name="forward_reverse_192.168.1.1-0" '
                 'value="forward" 1 /><input type="hidden" '
                 'name="default_forward_192.168.1.1-0" value="1" /></td><td>'
                 '<input type="checkbox" name="forward_reverse_192.168.1.1-0" '
                 'value="reverse" 1 /><input type="hidden" '
                 'name="default_reverse_192.168.1.1-0" value="1" /></td><td>'
                 '<input type="hidden" name="default_fqdn_192.168.1.1-0" '
                 'value="newhost1.com." />newhost1.com.</td><td>'
                 '<input type="text" name="host_192.168.1.1-0" '
                 'value="newhost1" /><input type="hidden" '
                 'name="default_host_192.168.1.1-0" value="newhost1" /></td> '
                 '<td><input type="text" name="fqdn_192.168.1.1-0" '
                 'value="newhost1.com." /></td></tr>'])

  def testAddError(self):
    ip_address = '192.168.1.1-0'
    error = 'Error string.'
    error_ips = {}

    error_ips = web_lib.AddError(ip_address, error, error_ips)
    self.assertEqual(error_ips, {'192.168.1.1-0': ['Error string.']})

  def testCheckChanges(self):
    add_dict = {'192.168.1.1': {'host': 'newhost', 'fqdn': 'newhost.oldfqdn'}}
    remove_dict = {'192.168.1.1': {'host': 'oldhost',
                                   'fqdn': 'oldhost.oldfqdn'}}
    view_name = u'any'
    error_ips = {}
    error_ips = web_lib.CheckChanges(remove_dict,
                                       self.core_instance, view_name, error_ips,
                                       action='remove')
    error_ips = web_lib.CheckChanges(add_dict, self.core_instance, view_name,
                                       error_ips=error_ips, action='add')
    self.assertEqual(error_ips,
        {'192.168.1.1': ['No matching domain for oldhost.oldfqdn',
                         'No matching domain for newhost.oldfqdn']})

    add_dict = {'192.168.1.1': {'host': 'newhost'}}
    error_ips = {}
    error_ips = web_lib.CheckChanges(remove_dict,
                                       self.core_instance, view_name, error_ips,
                                       action='remove')
    error_ips = web_lib.CheckChanges(add_dict, self.core_instance, view_name,
                                       error_ips=error_ips, action='add')
    self.assertEqual(error_ips,
        {'192.168.1.1': ['No matching domain for oldhost.oldfqdn',
                         'FQDN of 192.168.1.1 needs to be updated.']})

    error_ips = {}
    add_dict = {'192.168.1.1': {'fqdn': 'newhost.oldfqdn.'}}
    error_ips = web_lib.CheckChanges(remove_dict,
                                       self.core_instance, view_name,
                                       action='remove', error_ips=error_ips)
    error_ips = web_lib.CheckChanges(add_dict, self.core_instance, view_name,
                                       error_ips=error_ips, action='add')
    self.assertEqual(error_ips,
        {'192.168.1.1': ['No matching domain for oldhost.oldfqdn',
                         'HOST of 192.168.1.1 needs to be updated.']})

    error_ips = {}
    add_dict = {'192.168.1.1': {'host': 'newhost.', 'fqdn': 'newhost.oldfqdn.'}}
    error_ips = web_lib.CheckChanges(remove_dict,
                                       self.core_instance, view_name,
                                       action='remove', error_ips=error_ips)
    error_ips = web_lib.CheckChanges(add_dict, self.core_instance, view_name,
                                       error_ips=error_ips, action='add')
    self.assertEqual(error_ips,
        {'192.168.1.1': ['No matching domain for oldhost.oldfqdn',
                         'The use of "." in the hostname is not allowed.']})

    error_ips = {}
    add_dict = {'192.168.1.1': {'host': 'newhost', 'fqdn': 'diff.oldfqdn.'}}
    error_ips = web_lib.CheckChanges(remove_dict,
                                       self.core_instance, view_name,
                                       action='remove', error_ips=error_ips)
    error_ips = web_lib.CheckChanges(add_dict, self.core_instance, view_name,
                                       error_ips=error_ips, action='add')
    self.assertEqual(error_ips,
        {'192.168.1.1': ['No matching domain for oldhost.oldfqdn',
                        'FQDN must start with HOST for 192.168.1.1']})

    error_ips = {}
    view_name = u'test_view'
    add_dict = {'192.168.1.1': {'host': 'host1',
                                'fqdn': 'host1.university.edu'}}
    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeZone(u'test_zone', u'master', u'university.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'test_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')

    self.core_instance.MakeRecord(u'a', u'host1', u'test_zone',
                                  {u'assignment_ip': u'192.168.1.1'},
                                  view_name=u'test_view')
    error_ips = web_lib.CheckChanges(add_dict, self.core_instance, view_name,
                                       error_ips=error_ips, action='add')
    self.assertEqual(error_ips,
                     {'192.168.1.1': ['Record exists for 192.168.1.1']})
    add_dict = {}
    
    error_ips = {}
    remove_dict = {'192.168.1.1': {'host': 'host2',
                                   'fqdn': 'host2.university.edu'}}
    error_ips = web_lib.CheckChanges(remove_dict, self.core_instance,
                                       view_name, error_ips=error_ips,
                                       action='remove')
    self.assertEqual(error_ips,
                     {'192.168.1.1': ['Record for 192.168.1.1 not found']})

    error_ips = {}
    view_name = u'dne'
    add_dict = {'192.168.1.1': {'host': 'host2',
                                'fqdn': 'host2.university.edu'}}
    error_ips = web_lib.CheckChanges(add_dict, self.core_instance,
                                       view_name, error_ips=error_ips,
                                       action='add')
    self.assertEqual(error_ips,
                     {'192.168.1.1': ['View dne not found in zone test_zone']})

  def testPushChanges(self):
    add_dict = {'192.168.1.1': {'host': 'newhost', 'fqdn': 'newhost.oldfqdn'}}
    remove_dict = {'192.168.1.1': {'host': 'oldhost',
                                   'fqdn': 'oldhost.oldfqdn'}}
    error_ips = {}
    html_page = []
    view_name = u'any'
    self.assertEqual(self.core_instance.ListRecords(), [])
    self.core_instance.MakeZone(u'test_zone', u'master', u'oldfqdn.')
    self.core_instance.MakeZone(u'test_reverse_zone', u'master', u'1.168.192.in-addr.arpa.')
    self.core_instance.MakeReverseRangeZoneAssignment(u'test_reverse_zone',
                                                      u'192.168.1/24')
    web_lib.PushChanges(add_dict, remove_dict, error_ips, html_page,
                          self.core_instance, self.helper_instance, view_name)
    self.assertEqual(self.core_instance.ListRecords(),
        [{'target': u'newhost', 'ttl': 3600, 'record_type': u'a',
          'view_name': u'any', 'last_user': u'sharrell',
          'zone_name': u'test_zone', u'assignment_ip': u'192.168.1.1'},
         {'target': u'1', 'ttl': 3600, 'record_type': u'ptr',
          'view_name': u'any', 'last_user': u'sharrell',
          'zone_name': u'test_reverse_zone', u'assignment_host': u'newhost.oldfqdn.'}])

  def testPrintAllRecordsPage(self):
    view_name = u'any'
    records = {u'any':
        {u'123.210.23.1':
        [{u'forward': False,
          u'host': u'math-b44-c6506-01-23.dept.university.edu',
          'zone_origin': u'210.123.in-addr.arpa.',
          u'zone': u'210.123.in-addr.arpa'},
         {u'forward': True,
          u'host': u'math-b44-c6506-01-23.dept.university.edu',
          u'zone_origin': u'dept.university.edu.',
          u'zone': u'dept.university.edu'}],
         u'123.210.23.2':\
         [{u'forward': False,
           u'host': u'test_server23.dept.university.edu',
           'zone_origin': u'210.123.in-addr.arpa.',
           u'zone': u'210.123.in-addr.arpa'},
          {u'forward': True, u'host': u'test_server23.dept.university.edu',
           u'zone_origin': u'dept.university.edu.',
           u'zone': u'dept.university.edu'}]}}
    all_ips = [u'123.210.23.0', u'123.210.23.1', u'123.210.23.2',
               u'123.210.23.3']
    cidr_block = '123.210.23/30'
    changed_records = {'add': {}, 'remove': {}}
    html_page = web_lib.PrintAllRecordsPage(
        view_name, records, all_ips, cidr_block,
        changed_records=changed_records)
    self.assertEqual(html_page,
        ['<form action="edit_records.py" method="post">',
         '<input type="submit" value="Submit" />',
         '<table><tr><td>Existing Record</td><td bgcolor="#FF6666">Error '
         'Record</td><td bgcolor="#66FF66">Add Record</td>'
         '<td bgcolor="#6666FF">Remove Record</td><td bgcolor="#FFFF66">Change '
         'Record</td</tr></table>',
         '<input type="hidden" name="cidr_block" value="123.210.23/30" />',
         '<input type="hidden" name="view_name" value="any" />',
         '<input type="hidden" name="edit" value="true" />',
         '<table border="1">',
         '<tr><td>IP Address</td><td>Forward Record</td>',
         '<td>Reverse Record</td>',
         '<td>Originial Full Qualifed Name</td>',
         '<td>New Host Name</td><td>New Full Qualifed Name</td>',
         '<tr>',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.0-0" '
         '/>123.210.23.0</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.0-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.0-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.0-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.0-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.0-0" value="" /></td>'
         '<td><input type="text" name="host_123.210.23.0-0" value="" />'
         '<input type="hidden" name="default_host_123.210.23.0-0" value="" />'
         '</td> <td><input type="text" name="fqdn_123.210.23.0-0" value="" />'
         '</td></tr>',
         '<tr bgcolor="#EEEEEE">',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.1-0" '
         '/>123.210.23.1</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.1-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.1-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.1-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.1-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.1-0" '
         'value="math-b44-c6506-01-23.dept.university.edu" '
         '/>math-b44-c6506-01-23.dept.university.edu</td><td><input '
         'type="text" name="host_123.210.23.1-0" value="math-b44-c6506-01-23" '
         '/><input type="hidden" name="default_host_123.210.23.1-0" '
         'value="math-b44-c6506-01-23" /></td> <td><input type="text" '
         'name="fqdn_123.210.23.1-0" '
         'value="math-b44-c6506-01-23.dept.university.edu" /></td></tr>',
         '<tr>',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.2-0" '
         '/>123.210.23.2</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.2-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.2-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.2-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.2-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.2-0" '
         'value="test_server23.dept.university.edu" />test_server23.dept.university.edu'
         '</td><td><input type="text" name="host_123.210.23.2-0" '
         'value="test_server23" /><input type="hidden" '
         'name="default_host_123.210.23.2-0" value="test_server23" /></td> <td>'
         '<input type="text" name="fqdn_123.210.23.2-0" '
         'value="test_server23.dept.university.edu" /></td></tr>',
         '<tr bgcolor="#EEEEEE">',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.3-0" '
         '/>123.210.23.3</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.3-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.3-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.3-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.3-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.3-0" value="" /></td>'
         '<td><input type="text" name="host_123.210.23.3-0" value="" /><input '
         'type="hidden" name="default_host_123.210.23.3-0" value="" /></td> '
         '<td><input type="text" name="fqdn_123.210.23.3-0" value="" /></td>'
         '</tr>',
         '</table>',
         '<input type="submit" value="Submit" />',
         '</form>'])

    changed_records = {
        'add': {'123.210.23.2-0': {'host': 'test_server23wrong'},
                '123.210.23.3-0': {'host': 'new',
                                    'fqdn': 'new.org.university.edu'}},
        'remove': {'123.210.23.1-0': {
            'host': 'math-b44-c6506-01-23',
            'fqdn': 'math-b44-c6506-01-23.dept.university.edu'},
                   '123.210.23.2-0': {'host': 'test_server23'}}}
    error_ips = {'123.210.23.2-0':
        ['FQDN of 123.210.23.2-0 needs to be updated.']}
    html_page = web_lib.PrintAllRecordsPage(
        view_name, records, all_ips, cidr_block,
        changed_records=changed_records, error_ips=error_ips)
    self.assertEqual(html_page,
      ['<form action="edit_records.py" method="post">',
       '<input type="submit" value="Submit" />',
       '<table><tr><td>Existing Record</td><td bgcolor="#FF6666">Error '
       'Record</td><td bgcolor="#66FF66">Add Record</td><td bgcolor="#6666FF">'
       'Remove Record</td><td bgcolor="#FFFF66">Change Record</td</tr></table>',
       '<input type="hidden" name="cidr_block" value="123.210.23/30" />',
       '<input type="hidden" name="view_name" value="any" />',
       '<input type="hidden" name="edit" value="true" />',
       '<table border="1">',
       '<tr><td>IP Address</td><td>Forward Record</td>',
       '<td>Reverse Record</td>',
       '<td>Originial Full Qualifed Name</td>',
       '<td>New Host Name</td><td>New Full Qualifed Name</td>',
       '<tr>',
       '<td><input type="hidden" name="ip_addresses" value="123.210.23.0-0" '
       '/>123.210.23.0</td><td><input type="checkbox" '
       'name="forward_reverse_123.210.23.0-0" value="forward" '
       'checked="checked" /><input type="hidden" '
       'name="default_forward_123.210.23.0-0" value="1" /></td><td><input '
       'type="checkbox" name="forward_reverse_123.210.23.0-0" value="reverse" '
       'checked="checked" /><input type="hidden" '
       'name="default_reverse_123.210.23.0-0" value="1" /></td><td><input '
       'type="hidden" name="default_fqdn_123.210.23.0-0" value="" /></td><td>'
       '<input type="text" name="host_123.210.23.0-0" value="" /><input '
       'type="hidden" name="default_host_123.210.23.0-0" value="" /></td> <td>'
       '<input type="text" name="fqdn_123.210.23.0-0" value="" /></td></tr>',
       '<tr bgcolor="#6666FF">',
       '<td><input type="hidden" name="ip_addresses" value="123.210.23.1-0" '
       '/>123.210.23.1</td><td><input type="checkbox" '
       'name="forward_reverse_123.210.23.1-0" value="forward" '
       'checked="checked" /><input type="hidden" '
       'name="default_forward_123.210.23.1-0" value="1" /></td><td><input '
       'type="checkbox" name="forward_reverse_123.210.23.1-0" value="reverse" '
       'checked="checked" /><input type="hidden" '
       'name="default_reverse_123.210.23.1-0" value="1" /></td><td><input '
       'type="hidden" name="default_fqdn_123.210.23.1-0" '
       'value="math-b44-c6506-01-23.dept.university.edu" '
       '/>math-b44-c6506-01-23.dept.university.edu</td><td><input type="text" '
       'name="host_123.210.23.1-0" value="" /><input type="hidden" '
       'name="default_host_123.210.23.1-0" value="math-b44-c6506-01-23" '
       '/></td> <td><input type="text" name="fqdn_123.210.23.1-0" value="" '
       '/></td></tr>',
       '<tr bgcolor="#FF6666">',
       '<td><input type="hidden" name="ip_addresses" value="123.210.23.2-0" '
       '/>123.210.23.2</td><td><input type="checkbox" '
       'name="forward_reverse_123.210.23.2-0" value="forward" '
       'checked="checked" /><input type="hidden" '
       'name="default_forward_123.210.23.2-0" value="1" /></td><td><input '
       'type="checkbox" name="forward_reverse_123.210.23.2-0" value="reverse" '
       'checked="checked" /><input type="hidden" '
       'name="default_reverse_123.210.23.2-0" value="1" /></td><td><input '
       'type="hidden" name="default_fqdn_123.210.23.2-0" '
       'value="test_server23.dept.university.edu" />test_server23.dept.university.edu'
       '</td><td><input type="text" name="host_123.210.23.2-0" '
       'value="test_server23wrong" /><input type="hidden" '
       'name="default_host_123.210.23.2-0" value="test_server23" /></td> '
       '<td><input type="text" name="fqdn_123.210.23.2-0" '
       'value="test_server23.dept.university.edu" /></td></tr>',
       '<tr><td colspan=6 bgcolor=#FF6666>FQDN of 123.210.23.2-0 needs to be '
       'updated.</td></tr>',
       '<tr bgcolor="#66FF66">',
       '<td><input type="hidden" name="ip_addresses" value="123.210.23.3-0" '
       '/>123.210.23.3</td><td><input type="checkbox" '
       'name="forward_reverse_123.210.23.3-0" value="forward" '
       'checked="checked" /><input type="hidden" '
       'name="default_forward_123.210.23.3-0" value="1" /></td><td><input '
       'type="checkbox" name="forward_reverse_123.210.23.3-0" value="reverse" '
       'checked="checked" /><input type="hidden" '
       'name="default_reverse_123.210.23.3-0" value="1" /></td><td><input '
       'type="hidden" name="default_fqdn_123.210.23.3-0" value="" /></td><td>'
       '<input type="text" name="host_123.210.23.3-0" value="new" /><input '
       'type="hidden" name="default_host_123.210.23.3-0" value="" /></td> '
       '<td><input type="text" name="fqdn_123.210.23.3-0" '
       'value="new.org.university.edu" /></td></tr>',
       '</table>',
       '<input type="submit" value="Submit" />',
       '</form>'])
    changed_records = {'add': {
      '123.210.23.1-0': {'host': 'changed', 'fqdn': 'changed.dept.university.edu'},
      '123.210.23.2-0': {'fqdn': 'test_server23s.dept.university.edu'},
      '123.210.23.0-0': {'fqdn': 'forgot.host.'},
      '123.210.23.3-0': {'host': 'tr.', 'fqdn': 'tr.org.university.edu'}},
      'remove': {
      '123.210.23.1-0': {'host': 'math-b44-c6506-01-23',
                          'fqdn': 'math-b44-c6506-01-23.dept.university.edu'},
      '123.210.23.2-0': {'fqdn': 'test_server23.dept.university.edu'}}}
    error_ips = {
        '123.210.23.2-0': ['HOST of 123.210.23.2-0 needs to be updated.'],
        '123.210.23.0-0': ['HOST of 123.210.23.0-0 needs to be updated.'],
        '123.210.23.3-0':
            ['The use of "." in the hostname is not allowed.']}
    html_page = web_lib.PrintAllRecordsPage(
        view_name, records, all_ips, cidr_block,
        changed_records=changed_records, error_ips=error_ips)
    self.assertEqual(html_page,
        ['<form action="edit_records.py" method="post">',
         '<input type="submit" value="Submit" />',
         '<table><tr><td>Existing Record</td><td bgcolor="#FF6666">Error '
         'Record</td><td bgcolor="#66FF66">Add Record</td>'
         '<td bgcolor="#6666FF">Remove Record</td><td bgcolor="#FFFF66">'
         'Change Record</td</tr></table>',
         '<input type="hidden" name="cidr_block" value="123.210.23/30" />',
         '<input type="hidden" name="view_name" value="any" />',
         '<input type="hidden" name="edit" value="true" />',
         '<table border="1">',
         '<tr><td>IP Address</td><td>Forward Record</td>',
         '<td>Reverse Record</td>',
         '<td>Originial Full Qualifed Name</td>',
         '<td>New Host Name</td><td>New Full Qualifed Name</td>',
         '<tr bgcolor="#FF6666">',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.0-0" '
         '/>123.210.23.0</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.0-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.0-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.0-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.0-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.0-0" value="" /></td>'
         '<td><input type="text" name="host_123.210.23.0-0" value="" /><input '
         'type="hidden" name="default_host_123.210.23.0-0" value="" /></td> '
         '<td><input type="text" name="fqdn_123.210.23.0-0" '
         'value="forgot.host." /></td>'
         '</tr>',
         '<tr><td colspan=6 bgcolor=#FF6666>HOST of 123.210.23.0-0 needs to be '
         'updated.</td></tr>',
         '<tr bgcolor="#FFFF66">',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.1-0" '
         '/>123.210.23.1</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.1-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.1-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.1-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.1-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.1-0" '
         'value="math-b44-c6506-01-23.dept.university.edu" />'
         'math-b44-c6506-01-23.dept.university.edu</td><td><input type="text" '
         'name="host_123.210.23.1-0" value="changed" /><input '
         'type="hidden" name="default_host_123.210.23.1-0" '
         'value="math-b44-c6506-01-23" /></td> <td><input type="text" '
         'name="fqdn_123.210.23.1-0" '
         'value="changed.dept.university.edu" /></td></tr>',
         '<tr bgcolor="#FF6666">',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.2-0" '
         '/>123.210.23.2</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.2-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.2-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.2-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.2-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.2-0" '
         'value="test_server23.dept.university.edu" />'
         'test_server23.dept.university.edu</td><td><input type="text" '
         'name="host_123.210.23.2-0" value="test_server23" /><input type="hidden" '
         'name="default_host_123.210.23.2-0" value="test_server23" /></td> <td>'
         '<input type="text" name="fqdn_123.210.23.2-0" '
         'value="test_server23s.dept.university.edu" /></td></tr>',
         '<tr><td colspan=6 bgcolor=#FF6666>HOST of 123.210.23.2-0 needs to be '
         'updated.</td></tr>',
         '<tr bgcolor="#FF6666">',
         '<td><input type="hidden" name="ip_addresses" value="123.210.23.3-0" '
         '/>123.210.23.3</td><td><input type="checkbox" '
         'name="forward_reverse_123.210.23.3-0" value="forward" '
         'checked="checked" /><input type="hidden" '
         'name="default_forward_123.210.23.3-0" value="1" /></td><td><input '
         'type="checkbox" name="forward_reverse_123.210.23.3-0" '
         'value="reverse" checked="checked" /><input type="hidden" '
         'name="default_reverse_123.210.23.3-0" value="1" /></td><td><input '
         'type="hidden" name="default_fqdn_123.210.23.3-0" value="" /></td>'
         '<td><input type="text" name="host_123.210.23.3-0" value="tr." />'
         '<input '
         'type="hidden" name="default_host_123.210.23.3-0" value="" /></td> '
         '<td><input type="text" name="fqdn_123.210.23.3-0" '
         'value="tr.org.university.edu" /></td>'
         '</tr>',
         '<tr><td colspan=6 bgcolor=#FF6666>The use '
         'of "." in the hostname is not allowed.</td></tr>',
         '</table>',
         '<input type="submit" value="Submit" />',
         '</form>'])

  def testUpdateInputBoxes(self):
    changed_records = {'add': {
      '123.210.23.1-0': {'host': 'changed',
                         'fqdn': 'changed.dept.university.edu'},
      '123.210.23.2-0': {'fqdn': 'test_server189s.dept.university.edu'},
      '123.210.23.0-0': {'fqdn': 'forgot.host.'},
      '123.210.23.3-0': {'host': 'tr.', 'fqdn': 'tr.rcac.university.edu'}},
                       'remove': {
      '123.210.23.1-0': {'host': 'math-b44-c6506-01-189',
                          'fqdn': 'math-b44-c6506-01-189.dept.university.edu'},
      '123.210.23.2-0': {'fqdn': 'test_server189.dept.university.edu'}}}
    record_html_data = {
        'reverse': 'checked="checked"',
        'real_ip_address': u'123.210.23.0', 'default_reverse': 1,
        'default_host_name': '', 'fqdn': '', 'host_name': '',
        'default_forward': 1, 'default_fqdn': '',
        'forward': 'checked="checked"', 'ip_address': u'123.210.23.0-0'}
    error_ips = {
        '123.210.23.2-0': ['HOST of 123.210.23.2-0 needs to be updated.'],
        '123.210.23.0-0': ['HOST of 123.210.23.0-0 needs to be updated.'],
        '123.210.23.3-0':
            ['The use of "." in the hostname is not allowed.']}

    record_html_data = web_lib.UpdateInputBoxes(
        changed_records, record_html_data, error_ips)
    self.assertEqual(record_html_data,
        {'reverse': 'checked="checked"', 'real_ip_address': u'123.210.23.0',
         'default_reverse': 1, 'default_host_name': '', 'fqdn': 'forgot.host.',
         'host_name': '', 'default_forward': 1, 'default_fqdn': '',
         'forward': 'checked="checked"', 'ip_address': u'123.210.23.0-0'})

    changed_records = {'add': {
      '123.210.23.1-0': {'host': 'changed',
                         'fqdn': 'changed.dept.university.edu'},
      '123.210.23.2-0': {'fqdn': 'test_server189s.dept.university.edu'},
      '123.210.23.0-0': {'host': '', 'fqdn': 'forgot.host.'},
      '123.210.23.3-0': {'host': 'tr.', 'fqdn': 'tr.rcac.university.edu'}},
                       'remove': {
      '123.210.23.1-0': {'host': 'math-b44-c6506-01-189',
                          'fqdn': 'math-b44-c6506-01-189.dept.university.edu'},
      '123.210.23.2-0': {'fqdn': 'test_server189.dept.university.edu'}}}
    record_html_data = {
        'reverse': 'checked="checked"', 'real_ip_address': u'123.210.23.1',
        'default_reverse': 1, 'default_host_name': u'math-b44-c6506-01-189',
        'fqdn': u'math-b44-c6506-01-189.dept.university.edu',
        'host_name': u'math-b44-c6506-01-189', 'default_forward': 1,
        'default_fqdn': u'math-b44-c6506-01-189.dept.university.edu',
        'forward': 'checked="checked"', 'ip_address': u'123.210.23.1-0'}
    self.assertEqual(record_html_data,
        {'reverse': 'checked="checked"', 'real_ip_address': u'123.210.23.1',
         'default_reverse': 1, 'default_host_name': u'math-b44-c6506-01-189',
         'fqdn': u'math-b44-c6506-01-189.dept.university.edu',
         'host_name': u'math-b44-c6506-01-189', 'default_forward': 1,
         'default_fqdn': u'math-b44-c6506-01-189.dept.university.edu',
         'forward': 'checked="checked"', 'ip_address': u'123.210.23.1-0'})

  def testPrintGetCIDRPage(self):
    self.assertEqual(web_lib.PrintGetCIDRPage(),
        ['<form action="edit_records.py" method="post">',
         'Enter CIDR block to edit: ',
         '<input type="text" name="cidr_block" /><br />',
         'Enter view name: ',
         '<input type="text" name="view_name" value="any" />',
         '<input type="submit" value="Submit" />', '</form>'])

  def testProcessPostDict(self):
    post_get_dict = {
        'default_forward_123.210.23.1-0':
            [Field('default_forward_123.210.23.1-0', '1')],
        'default_forward_123.210.23.0-0':
            [Field('default_forward_123.210.23.0-0', '1')],
        'ip_addresses':
            [Field('ip_addresses', '123.210.23.0-0'),
             Field('ip_addresses', '123.210.23.1-0'),
             Field('ip_addresses', '123.210.23.2-0'),
             Field('ip_addresses', '123.210.23.3-0')],
        'default_forward_123.210.23.2-0':
            [Field('default_forward_123.210.23.2-0', '1')],
        'default_reverse_123.210.23.3-0':
            [Field('default_reverse_123.210.23.3-0', '1')],
        'forward_reverse_123.210.23.2-0':
            [Field('forward_reverse_123.210.23.2-0', 'forward'),
             Field('forward_reverse_123.210.23.2-0', 'reverse')],
        'default_forward_123.210.23.3-0':
            [Field('default_forward_123.210.23.3-0', '1')],
        'default_host_123.210.23.2-0':
            [Field('default_host_123.210.23.2-0', 'test_server189')],
        'fqdn_123.210.23.1-0':
            [Field('fqdn_123.210.23.1-0', 'changed.dept.university.edu')],
        'default_fqdn_123.210.23.2-0':
            [Field('default_fqdn_123.210.23.2-0',
                   'test_server189.dept.university.edu')],
        'default_reverse_123.210.23.2-0':
            [Field('default_reverse_123.210.23.2-0', '1')],
        'default_fqdn_123.210.23.1-0':
            [Field('default_fqdn_123.210.23.1-0',
                   'math-b44-c6506-01-189.dept.university.edu')],
        'default_reverse_123.210.23.0-0':
            [Field('default_reverse_123.210.23.0-0', '1')],
        'fqdn_123.210.23.0-0':
            [Field('fqdn_123.210.23.0-0', 'forgot.host.')],
        'default_reverse_123.210.23.1-0':
            [Field('default_reverse_123.210.23.1-0', '1')],
        'fqdn_123.210.23.2-0':
            [Field('fqdn_123.210.23.2-0', 'test_server189s.dept.university.edu')],
        'cidr_block': [Field('cidr_block', '123.210.23/30')],
        'host_123.210.23.2-0': [Field('host_123.210.23.2-0', 'test_server189')],
        'forward_reverse_123.210.23.0-0':
            [Field('forward_reverse_123.210.23.0-0', 'forward'),
             Field('forward_reverse_123.210.23.0-0', 'reverse')],
        'forward_reverse_123.210.23.1-0':
            [Field('forward_reverse_123.210.23.1-0', 'forward'),
             Field('forward_reverse_123.210.23.1-0', 'reverse')],
        'edit': [Field('edit', 'true')],
        'forward_reverse_123.210.23.3-0':
            [Field('forward_reverse_123.210.23.3-0', 'forward'),
             Field('forward_reverse_123.210.23.3-0', 'reverse')],
        'default_host_123.210.23.1-0':
            [Field('default_host_123.210.23.1-0', 'math-b44-c6506-01-189')],
        'view_name': [Field('view_name', 'any')],
        'host_123.210.23.3-0': [Field('host_123.210.23.3-0', 'tr.')],
        'fqdn_123.210.23.3-0': [Field('fqdn_123.210.23.3-0',
                                       'tr.rcac.university.edu')],
        'host_123.210.23.1-0': [Field('host_123.210.23.1-0', 'changed')]}

    records_dict = web_lib.ProcessPostDict(post_get_dict)
    self.assertEqual(records_dict,
        {'addresses': {'forward': '0', 'reverse': '0', 'default_forward': '0',
                       'default_reverse': '0'},
         'edit': {'forward': '0', '': 'true', 'reverse': '0',
                  'default_forward': '0', 'default_reverse': '0'},
         '123.210.23.3-0': {'reverse': '1', 'default_reverse': '1',
                             'fqdn': 'tr.rcac.university.edu', 'host': 'tr.',
                             'default_forward': '1', 'forward': '1'},
         '123.210.23.1-0': {'reverse': '1', 'default_reverse': '1',
                             'fqdn': 'changed.dept.university.edu',
                             'host': 'changed', 'default_forward': '1',
                             'default_fqdn':
                                 'math-b44-c6506-01-189.dept.university.edu',
                             'forward': '1',
                             'default_host': 'math-b44-c6506-01-189'},
         '123.210.23.0-0': {'forward': '1', 'fqdn': 'forgot.host.',
                             'reverse': '1', 'default_forward': '1',
                             'default_reverse': '1'},
         '123.210.23.2-0': {'reverse': '1', 'default_reverse': '1',
                             'fqdn': 'test_server189s.dept.university.edu',
                             'host': 'test_server189', 'default_forward': '1',
                             'default_fqdn': 'test_server189.dept.university.edu',
                             'forward': '1', 'default_host': 'test_server189'},
         'block': {'forward': '0', 'reverse': '0', 'default_forward': '0',
                   'default_reverse': '0'},
         'name': {'forward': '0', 'reverse': '0', 'default_forward': '0',
                  'default_reverse': '0'}})

if( __name__ == '__main__' ):
  unittest.main()
