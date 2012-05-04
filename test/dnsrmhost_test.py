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

"""Regression test for dnsrmhost

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '0.16'


import os
import sys
import socket
import threading
import time
import getpass
import unittest

import roster_core
import roster_server
from roster_user_tools import roster_client_lib

USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
HOST = u'localhost'
USERNAME = u'sharrell'
PASSWORD = u'test'
KEYFILE=('test_data/dnsmgmt.key.pem')
CERTFILE=('test_data/dnsmgmt.cert.pem')
CREDFILE='%s/.dnscred' % os.getcwd()
EXEC = '../roster-user-tools/scripts/dnsrmhost'

class options(object):
  password = u'test'
  username = u'sharrell'
  server = None
  ldap = u'ldaps://ldap.cs.university.edu:636'
  credfile = CREDFILE
  view_name = None
  ip_address = None
  target = u'machine1'
  ttl = 64

class DaemonThread(threading.Thread):
  def __init__(self, config_instance, port):
    threading.Thread.__init__(self)
    self.config_instance = config_instance
    self.port = port
    self.daemon_instance = None

  def run(self):
    self.daemon_instance = roster_server.Server(self.config_instance, KEYFILE,
                                                CERTFILE)
    self.daemon_instance.Serve(port=self.port)

class Testdnsrmhost(unittest.TestCase):

  def setUp(self):

    def PickUnusedPort():
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind((HOST, 0))
      addr, port = s.getsockname()
      s.close()
      return port

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.port = PickUnusedPort()
    self.server_name = 'https://%s:%s' % (HOST, self.port)
    self.daemon_thread = DaemonThread(self.config_instance, self.port)
    self.daemon_thread.daemon = True
    self.daemon_thread.start()
    self.core_instance = roster_core.Core(USERNAME, self.config_instance)
    self.core_helper_instance = roster_core.CoreHelpers(self.core_instance)
    self.password = 'test'
    time.sleep(1)
    roster_client_lib.GetCredentials(USERNAME, u'test', credfile=CREDFILE,
                                     server_name=self.server_name)

    self.core_instance.MakeView(u'test_view')
    self.core_instance.MakeView(u'test_view2')
    self.core_instance.MakeView(u'test_view3')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'0.168.192.in-addr.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'university.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(u'forward_zone', u'master',
                                u'university.edu.',
                                view_name=u'test_view3')
    self.core_instance.MakeZone(u'reverse_zone', u'master',
                                u'0.168.192.in-addr.arpa.',
                                view_name=u'test_view2')
    self.core_instance.MakeZone(u'ipv6zone', u'master',
                                u'8.0.e.f.f.3.ip6.arpa.',
                                view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(u'reverse_zone',
                                                      u'192.168.0/24')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'forward_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'forward_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view3')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'reverse_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view2')
    self.core_instance.MakeRecord(
        u'soa', u'soa1', u'ipv6zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host2', u'forward_zone', {u'assignment_ip':
            u'4321:0000:0001:0002:0003:0004:0567:89ab'}, view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host1', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.1'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host2', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.11'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host3', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.5'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host4', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.10'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'host5', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.17'},
                                  view_name=u'test_view3')
    self.core_instance.MakeRecord(u'a', u'host6', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.8'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'a', u'@', u'forward_zone',
                                  {u'assignment_ip': u'192.168.0.9'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'8',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host6.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'9',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'4',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host2.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'5',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host3.university.edu.'},
                                  view_name=u'test_view')
    self.core_instance.MakeRecord(u'ptr', u'10',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host4.university.edu.'},
                                  view_name=u'test_view2')
    self.core_instance.MakeRecord(u'ptr', u'7',
                                  u'reverse_zone',
                                  {u'assignment_host':
                                      u'host5.university.edu.'},
                                  view_name=u'test_view2')

  def tearDown(self):
    if( os.path.exists(CREDFILE) ):
      os.remove(CREDFILE)

  def testRemoveHost(self):
    returned_dict = self.core_helper_instance.ListRecordsByCIDRBlock(
        u'192.168.0/24', view_name=u'test_view')
    self.assertEqual(len(returned_dict), 1)
    self.assertEqual(len(returned_dict[u'test_view']), 5)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.9']),2)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.8']),2)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.10']),1)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.5']),2)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.1']),1)
    self.assertTrue(
        { u'forward': False,
          u'host': u'host6.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.8'},
          'record_last_user': u'sharrell',
          'record_target': u'8',
          'record_ttl': 3600,
          'record_type': u'ptr',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'reverse_zone',
          'records_id': 14,
          u'view_name': u'test_view',
          u'zone_origin': u'0.168.192.in-addr.arpa.'} in
        returned_dict[u'test_view'][u'192.168.0.8'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host6.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.8'},
          'record_last_user': u'sharrell',
          'record_target': u'host6',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 12,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.8'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host1.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.1'},
          'record_last_user': u'sharrell',
          'record_target': u'host1',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 7,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.1'])
    self.assertTrue(
        { u'forward': False,
          u'host': u'university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.9'},
          'record_last_user': u'sharrell',
          'record_target': u'9',
          'record_ttl': 3600,
          'record_type': u'ptr',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'reverse_zone',
          'records_id': 15,
          u'view_name': u'test_view',
          u'zone_origin': u'0.168.192.in-addr.arpa.'} in
        returned_dict[u'test_view'][u'192.168.0.9'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'@.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.9'},
          'record_last_user': u'sharrell',
          'record_target': u'@',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 13,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.9'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host4.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.10'},
          'record_last_user': u'sharrell',
          'record_target': u'host4',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 10,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.10'])
    self.assertTrue(
        { u'forward': False,
          u'host': u'host3.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.5'},
          'record_last_user': u'sharrell',
          'record_target': u'5',
          'record_ttl': 3600,
          'record_type': u'ptr',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'reverse_zone',
          'records_id': 17,
          u'view_name': u'test_view',
          u'zone_origin': u'0.168.192.in-addr.arpa.'} in
        returned_dict[u'test_view'][u'192.168.0.5'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host3.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.5'},
          'record_last_user': u'sharrell',
          'record_target': u'host3',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 9,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.5'])
    output = os.popen('python %s -q -i 192.168.0.5 -t host3 '
                      '-z forward_zone -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    output.close()
    returned_dict = self.core_helper_instance.ListRecordsByCIDRBlock(
        u'192.168.0/24', view_name=u'test_view')
    self.assertEqual(len(returned_dict),1)
    self.assertEqual(len(returned_dict[u'test_view']),4)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.8']),2)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.1']),1)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.9']),2)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.10']),1)
    self.assertTrue(
        { u'forward': False,
          u'host': u'host6.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.8'},
          'record_last_user': u'sharrell',
          'record_target': u'8',
          'record_ttl': 3600,
          'record_type': u'ptr',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'reverse_zone',
          'records_id': 14,
          u'view_name': u'test_view',
          u'zone_origin': u'0.168.192.in-addr.arpa.'} in
        returned_dict[u'test_view'][u'192.168.0.8'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host6.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.8'},
          'record_last_user': u'sharrell',
          'record_target': u'host6',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 12,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.8'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host1.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.1'},
          'record_last_user': u'sharrell',
          'record_target': u'host1',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 7,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.1'])
    self.assertTrue(
        { u'forward': False,
          u'host': u'university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.9'},
          'record_last_user': u'sharrell',
          'record_target': u'9',
          'record_ttl': 3600,
          'record_type': u'ptr',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'reverse_zone',
          'records_id': 15,
          u'view_name': u'test_view',
          u'zone_origin': u'0.168.192.in-addr.arpa.'} in
        returned_dict[u'test_view'][u'192.168.0.9'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'@.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.9'},
          'record_last_user': u'sharrell',
          'record_target': u'@',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 13,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
    returned_dict[u'test_view'][u'192.168.0.9'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host4.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.10'},
          'record_last_user': u'sharrell',
          'record_target': u'host4',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 10,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.10'])
    output = os.popen('python %s -q -i 192.168.0.9 -t @ '
                      '-z forward_zone -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    output.close()

    returned_dict = self.core_helper_instance.ListRecordsByCIDRBlock(
        u'192.168.0/24', view_name=u'test_view')
    self.assertEqual(len(returned_dict),1)
    self.assertEqual(len(returned_dict[u'test_view']),3)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.8']),2)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.1']),1)
    self.assertEqual(len(returned_dict[u'test_view'][u'192.168.0.10']),1)
    self.assertTrue(
        { u'forward': False,
          u'host': u'host6.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.8'},
          'record_last_user': u'sharrell',
          'record_target': u'8',
          'record_ttl': 3600,
          'record_type': u'ptr',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'reverse_zone',
          'records_id': 14,
          u'view_name': u'test_view',
          u'zone_origin': u'0.168.192.in-addr.arpa.'} in
        returned_dict[u'test_view'][u'192.168.0.8'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host6.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.8'},
          'record_last_user': u'sharrell',
          'record_target': u'host6',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 12,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.8'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host1.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.1'},
          'record_last_user': u'sharrell',
          'record_target': u'host1',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 7,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.1'])
    self.assertTrue(
        { u'forward': True,
          u'host': u'host4.university.edu',
          u'record_args_dict': { 'assignment_ip': u'192.168.0.10'},
          'record_last_user': u'sharrell',
          'record_target': u'host4',
          'record_ttl': 3600,
          'record_type': u'a',
          'record_view_dependency': u'test_view_dep',
          'record_zone_name': u'forward_zone',
          'records_id': 10,
          u'view_name': u'test_view',
          u'zone_origin': u'university.edu.'} in
        returned_dict[u'test_view'][u'192.168.0.10'])

  def testRemoveIPV6(self):
    self.core_instance.MakeZone(u'ipv6_zone', u'master',
                                u'university2.edu.',
                                view_name=u'test_view')
    self.core_instance.MakeZone(
        u'ipv6_zone_rev', u'master',
        u'0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.'
        '0.0.0.1.0.0.2.ip6.arpa.', view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'soa', u'soa2', u'ipv6_zone_rev',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin.university.edu.',
         u'serial_number': 1, u'refresh_seconds': 5,
         u'retry_seconds': 5, u'expiry_seconds': 5,
         u'minimum_seconds': 5}, view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'ipv6host', u'ipv6_zone', {u'assignment_ip':
            u'2001:0000:0000:0000:0000:0000:0000:0001'}, 
        view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'aaaa', u'host_ipv6', u'ipv6_zone', {u'assignment_ip':
            u'2001:0000:0000:0000:0000:0000:0000:0002'}, 
        view_name=u'test_view')
    self.core_instance.MakeRecord(
        u'ptr', u'1', u'ipv6_zone_rev', {u'assignment_host':
          u'ipv6host.university2.edu.'}, view_name=u'test_view')
    self.core_instance.MakeReverseRangeZoneAssignment(u'ipv6_zone_rev',
                                                      u'2001::/124')
    self.assertEqual(self.core_instance.ListRecords(record_type=u'aaaa'),
        [{'target': u'ipv6host', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'ipv6_zone',
          u'assignment_ip': u'2001:0000:0000:0000:0000:0000:0000:0001'},
         {'target': u'host2', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone',
          u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
         {'target': u'host_ipv6', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'ipv6_zone',
          u'assignment_ip': u'2001:0000:0000:0000:0000:0000:0000:0002'}])
    output = os.popen('python %s -i 2001:0000:0000:0000:0000:0000:0000:0001 -t '
                      'ipv6host -z ipv6_zone -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (EXEC, self.server_name,
                                                  USERNAME, PASSWORD,
                                                  USER_CONFIG))
    self.assertEqual(output.read(),
        'REMOVED AAAA: ipv6host zone_name: ipv6_zone view_name: test_view '
        'ttl: 3600\n'
        '    assignment_ip: 2001:0000:0000:0000:0000:0000:0000:0001\n'
        'REMOVED PTR: 1 zone_name: ipv6_zone_rev view_name: test_view '
        'ttl: 3600\n    assignment_host: ipv6host.university2.edu.\n')
    output.close()
    self.assertEqual(self.core_instance.ListRecords(record_type=u'aaaa'),
        [{'target': u'host2', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'forward_zone',
          u'assignment_ip': u'4321:0000:0001:0002:0003:0004:0567:89ab'},
         {'target': u'host_ipv6', 'ttl': 3600, 'record_type': u'aaaa',
          'view_name': u'test_view', 'last_user': u'sharrell',
          'zone_name': u'ipv6_zone',
          u'assignment_ip': u'2001:0000:0000:0000:0000:0000:0000:0002'}])

  def testErrors(self):
    output = os.popen('python %s -i notipaddress -t '
                      'host3. -z forward_zone -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: Incorrectly formatted IP '
                                    'address.\n')
    output.close()
    output = os.popen('python %s -i 192.168.0.90 -t '
                      'host3. -z forward_zone -v test_view2 -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(), 'CLIENT ERROR: Record not found.\n')
    output.close()
    output = os.popen('python %s -t '
                      'host3 -z test_zone -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -i/--ip-address flag is required.\n')
    output.close()
    output = os.popen('python %s '
                      '-z test_zone -v test_view -s %s -u %s '
                      '-p %s --config-file %s' % (
                          EXEC, self.server_name,
                          USERNAME, PASSWORD, USER_CONFIG))
    self.assertEqual(output.read(),
        'CLIENT ERROR: The -t/--target flag is required.\n')
    output.close()



if( __name__ == '__main__' ):
      unittest.main()
