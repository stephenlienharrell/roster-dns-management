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

"""Regression test for dnstreeexport

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import iscpy
import os
import sys
import shutil
import tarfile
import datetime
import getpass

import unittest
sys.path.append('../')

import roster_core

TESTDIR = u'%s/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/named/' % os.getcwd()
SSH_USER = unicode(getpass.getuser())
USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
DATA_FILE = 'test_data/test_data.sql'
EXEC = '../roster-config-manager/scripts/dnstreeexport'
USERNAME = u'sharrell'

class TestDnsMkHost(unittest.TestCase):

  def setUp(self):

    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.bind_config_dir = self.config_instance.config_file['exporter'][
        'root_config_dir']
    self.backup_dir = self.config_instance.config_file['exporter'][
        'backup_dir']
    self.named_dir = self.config_instance.config_file['exporter'][
        'named_dir'].rstrip('/')

    db_instance = self.config_instance.GetDb()
    self.db_instance = db_instance

    db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()

    self.core_instance = roster_core.Core(USERNAME, self.config_instance)

    db_instance.StartTransaction()

    self.tarfile = ''

    # Make server sets
    dns_server_sets_dict = {}

    dns_server_sets_dict['dns_server_set_name'] = u'internal_dns'
    db_instance.MakeRow('dns_server_sets', dns_server_sets_dict)

    dns_server_sets_dict['dns_server_set_name'] = u'external_dns'
    db_instance.MakeRow('dns_server_sets', dns_server_sets_dict)

    dns_server_sets_dict['dns_server_set_name'] = u'private_dns'
    db_instance.MakeRow('dns_server_sets', dns_server_sets_dict)

    # Make Views
    views_dict = {}

    views_dict['view_options'] = u'recursion no;'

    views_dict['view_name'] = u'internal'
    db_instance.MakeRow('views', views_dict)

    views_dict['view_name'] = u'external'
    db_instance.MakeRow('views', views_dict)

    views_dict['view_name'] = u'private'
    db_instance.MakeRow('views', views_dict)

    # Make View Dependencies
    view_dependencies_dict = {}

    view_dependencies_dict['view_dependency'] = u'internal_dep'
    db_instance.MakeRow('view_dependencies', view_dependencies_dict)

    view_dependencies_dict['view_dependency'] = u'external_dep'
    db_instance.MakeRow('view_dependencies', view_dependencies_dict)

    view_dependencies_dict['view_dependency'] = u'private_dep'
    db_instance.MakeRow('view_dependencies', view_dependencies_dict)

    # Make View Dependency Assignments
    view_dependency_assignments_dict = {}

    view_dependency_assignments_dict[
        'view_dependency_assignments_view_name'] = u'internal'
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_dependency'] = u'any'
    db_instance.MakeRow('view_dependency_assignments',
                        view_dependency_assignments_dict)

    view_dependency_assignments_dict[
        'view_dependency_assignments_view_name'] = u'external'
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_dependency'] = u'any'
    db_instance.MakeRow('view_dependency_assignments',
                        view_dependency_assignments_dict)

    view_dependency_assignments_dict[
        'view_dependency_assignments_view_name'] = u'private'
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_dependency'] = u'any'
    db_instance.MakeRow('view_dependency_assignments',
                        view_dependency_assignments_dict)

    view_dependency_assignments_dict[
        'view_dependency_assignments_view_name'] = u'internal'
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_dependency'] = u'internal_dep'
    db_instance.MakeRow('view_dependency_assignments',
                        view_dependency_assignments_dict)

    view_dependency_assignments_dict[
        'view_dependency_assignments_view_name'] = u'external'
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_dependency'] = u'external_dep'
    db_instance.MakeRow('view_dependency_assignments',
                        view_dependency_assignments_dict)

    view_dependency_assignments_dict[
        'view_dependency_assignments_view_name'] = u'private'
    view_dependency_assignments_dict[
        'view_dependency_assignments_view_dependency'] = u'private_dep'
    db_instance.MakeRow('view_dependency_assignments',
                        view_dependency_assignments_dict)

    # Make Zones
    zones_dict = {}

    zones_dict['zone_name'] = u'university.edu'
    db_instance.MakeRow('zones', zones_dict)

    zones_dict['zone_name'] = u'int.university.edu'
    db_instance.MakeRow('zones', zones_dict)

    zones_dict['zone_name'] = u'priv.university.edu'
    db_instance.MakeRow('zones', zones_dict)

    zones_dict['zone_name'] = u'168.192.in-addr'
    db_instance.MakeRow('zones', zones_dict)

    zones_dict['zone_name'] = u'4.3.2.1.in-addr'
    db_instance.MakeRow('zones', zones_dict)

    # Make Zone/View assignments
    zone_view_assignments_dict = {}

    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'university.edu')
    zone_view_assignments_dict['zone_view_assignments_zone_type'] = u'master'
    zone_view_assignments_dict['zone_origin'] = u'university.edu.'
    zone_view_assignments_dict['zone_options'] = iscpy.Serialize(
        u'#Allow update\nallow-update { none; };\n')

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'any')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'internal_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'external_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'private_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_origin'] = u'university2.edu.'
    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'internal_dep')
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'int.university.edu')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'private_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_origin'] = u'university3.edu.'
    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'private_dep')
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'priv.university.edu')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'internal_dep')
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'168.192.in-addr')
    zone_view_assignments_dict['zone_origin'] = u'168.192.in-addr.arpa.'
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'external_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'private_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'external_dep')
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'4.3.2.1.in-addr')
    zone_view_assignments_dict['zone_origin'] = u'4.3.2.1.in-addr.arpa.'
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_zone_type'] = u'slave'
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'bio.university.edu')
    zone_view_assignments_dict['zone_origin'] = u'university4.edu.'
    zone_view_assignments_dict['zone_options'] = (
        u'#Allow update\nallow-transfer { any; };\n')

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'external_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    # Make DNS Servers
    dns_servers_dict = db_instance.GetEmptyRowDict('dns_servers')
    dns_servers_dict['dns_server_name'] = u'dns1.university.edu'
    dns_servers_dict['dns_server_remote_bind_directory'] = BINDDIR
    dns_servers_dict['dns_server_remote_test_directory'] = TESTDIR
    dns_servers_dict['dns_server_ssh_username'] = SSH_USER
    dns_servers_dict['dns_server_name'] = u'dns1.university.edu'
    db_instance.MakeRow('dns_servers', dns_servers_dict)

    dns_servers_dict['dns_server_name'] = u'dns2.university.edu'
    db_instance.MakeRow('dns_servers', dns_servers_dict)

    dns_servers_dict['dns_server_name'] = u'dns3.university.edu'
    db_instance.MakeRow('dns_servers', dns_servers_dict)

    dns_servers_dict['dns_server_name'] = u'dns4.university.edu'
    db_instance.MakeRow('dns_servers', dns_servers_dict)

    dns_servers_dict['dns_server_name'] = u'ns1.university.edu'
    db_instance.MakeRow('dns_servers', dns_servers_dict)

    dns_servers_dict['dns_server_name'] = u'ns1.int.university.edu'
    db_instance.MakeRow('dns_servers', dns_servers_dict)

    # Make Dns Server Set Assignments
    dns_server_set_assignments_dict = {}

    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_name'] = u'ns1.university.edu'
    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_set_name'] = (
            u'external_dns')
    db_instance.MakeRow('dns_server_set_assignments',
                        dns_server_set_assignments_dict)

    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_name'] = (
            u'ns1.int.university.edu')
    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_set_name'] = (
            u'internal_dns')
    db_instance.MakeRow('dns_server_set_assignments',
                        dns_server_set_assignments_dict)

    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_name'] = (
            u'ns1.int.university.edu')
    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_set_name'] = (
            u'private_dns')
    db_instance.MakeRow('dns_server_set_assignments',
                        dns_server_set_assignments_dict)

    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_name'] = u'dns1.university.edu'
    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_set_name'] = (
            u'internal_dns')
    db_instance.MakeRow('dns_server_set_assignments',
                        dns_server_set_assignments_dict)

    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_name'] = u'dns2.university.edu'
    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_set_name'] = (
            u'external_dns')
    db_instance.MakeRow('dns_server_set_assignments',
                        dns_server_set_assignments_dict)

    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_name'] = u'dns3.university.edu'
    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_set_name'] = (
            u'external_dns')
    db_instance.MakeRow('dns_server_set_assignments',
                        dns_server_set_assignments_dict)

    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_name'] = u'dns4.university.edu'
    dns_server_set_assignments_dict[
        'dns_server_set_assignments_dns_server_set_name'] = (
            u'private_dns')
    db_instance.MakeRow('dns_server_set_assignments',
                        dns_server_set_assignments_dict)

    # Make DNS Server Set View assignments
    dns_server_set_view_assignments_dict = {}

    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_dns_server_set_name'] = (
            u'internal_dns')
    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_view_name'] = u'internal'
    db_instance.MakeRow('dns_server_set_view_assignments',
                        dns_server_set_view_assignments_dict)

    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_dns_server_set_name'] = (
            u'internal_dns')
    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_view_name'] = u'external'
    db_instance.MakeRow('dns_server_set_view_assignments',
                        dns_server_set_view_assignments_dict)

    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_dns_server_set_name'] = (
            u'external_dns')
    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_view_name'] = u'external'
    db_instance.MakeRow('dns_server_set_view_assignments',
                        dns_server_set_view_assignments_dict)

    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_dns_server_set_name'] = (
            u'private_dns')
    dns_server_set_view_assignments_dict[
        'dns_server_set_view_assignments_view_name'] = u'private'
    db_instance.MakeRow('dns_server_set_view_assignments',
                        dns_server_set_view_assignments_dict)

    # Make Records

    # Make mail server 1 'mx' record for 'any' view
    records_dict = {}
    records_dict['records_id'] = None
    records_dict['record_type'] = u'mx'
    records_dict['record_target'] = u'@'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'any'
    records_dict['record_last_user'] = u'sharrell'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 1
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'mx'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'priority'
    record_arguments_record_assignments_dict['argument_value'] = u'1'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 1
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'mx'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'mail_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'mail1.university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make 'soa' record for 'internal' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'soa'
    records_dict['record_target'] = u'168.192.in-addr.arpa.'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'168.192.in-addr'
    records_dict['record_view_dependency'] = u'internal_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 2
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'name_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'ns1.university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 2
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'admin_email'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'admin@university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 2
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'serial_number')
    record_arguments_record_assignments_dict['argument_value'] = u'20091223'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 2
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'refresh_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 2
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'retry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 2
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'expiry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 2
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'minimum_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make computer 1 'a' record for 'internal' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'a'
    records_dict['record_target'] = u'computer1'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'internal_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 3
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'a'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'assignment_ip')
    record_arguments_record_assignments_dict['argument_value'] = (
        u'192.168.1.1')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make computer 2 'a' record for 'internal' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'a'
    records_dict['record_target'] = u'computer2'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'internal_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 4
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'a'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'assignment_ip')
    record_arguments_record_assignments_dict['argument_value'] = (
        u'192.168.1.2')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make 'soa' record for 'external' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'soa'
    records_dict['record_target'] = u'4.3.2.1.in-addr.arpa.'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'4.3.2.1.in-addr'
    records_dict['record_view_dependency'] = u'external_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 5
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'name_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'ns1.university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 5
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'admin_email'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'admin@university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 5
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'serial_number')
    record_arguments_record_assignments_dict['argument_value'] = u'20091224'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 5
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'refresh_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 5
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'retry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 5
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'expiry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 5
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'minimum_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make computer 1 'a' record for 'external' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'a'
    records_dict['record_target'] = u'computer1'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'external_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 6
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'a'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'assignment_ip')
    record_arguments_record_assignments_dict['argument_value'] = (
        u'1.2.3.5')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make computer 3 'a' record for 'external' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'a'
    records_dict['record_target'] = u'computer3'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'external_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 7
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'a'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'assignment_ip')
    record_arguments_record_assignments_dict['argument_value'] = (
        u'1.2.3.6')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make mail server 2 'mx' record for 'any' view
    records_dict = {}
    records_dict['records_id'] = None
    records_dict['record_type'] = u'mx'
    records_dict['record_target'] = u'@'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'any'
    records_dict['record_last_user'] = u'sharrell'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 8
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'mx'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'priority'
    record_arguments_record_assignments_dict['argument_value'] = u'1'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 8
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'mx'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'mail_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'mail2.university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make name server 1 'ns' record for 'any' view
    records_dict = {}
    records_dict['records_id'] = None
    records_dict['record_type'] = u'ns'
    records_dict['record_target'] = u'@'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'any'
    records_dict['record_last_user'] = u'sharrell'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 9
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'ns'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'name_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'ns1.university.edu')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make name server 2 'ns' record for 'any' view
    records_dict = {}
    records_dict['records_id'] = None
    records_dict['record_type'] = u'ns'
    records_dict['record_target'] = u'@'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'any'
    records_dict['record_last_user'] = u'sharrell'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 10
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'ns'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'name_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'ns2.university.edu')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make computer 4 'a' record for 'internal' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'a'
    records_dict['record_target'] = u'computer4'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'internal_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 11
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'a'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'assignment_ip')
    record_arguments_record_assignments_dict['argument_value'] = (
        u'192.168.1.4')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make 'soa' record for 'internal' view / 'university.edu' zone
    records_dict['records_id'] = None
    records_dict['record_type'] = u'soa'
    records_dict['record_target'] = u'university.edu.'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'internal_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 12
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'name_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'ns1.university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 12
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'admin_email'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'admin@university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 12
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'serial_number')
    record_arguments_record_assignments_dict['argument_value'] = u'20091225'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 12
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'refresh_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 12
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'retry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 12
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'expiry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 12
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'minimum_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make 'soa' record for 'private' view / 'university.edu' zone
    records_dict['records_id'] = None
    records_dict['record_type'] = u'soa'
    records_dict['record_target'] = u'university.edu.'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'private_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 13
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'name_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'ns1.university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 13
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'admin_email'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'admin@university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 13
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'serial_number')
    record_arguments_record_assignments_dict['argument_value'] = u'20091227'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 13
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'refresh_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 13
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'retry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 13
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'expiry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 13
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'minimum_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)


    # Make 'soa' record for 'external' view / 'university.edu' zone
    records_dict['records_id'] = None
    records_dict['record_type'] = u'soa'
    records_dict['record_target'] = u'university.edu.'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'university.edu'
    records_dict['record_view_dependency'] = u'external_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 14
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'name_server'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'ns1.university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 14
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = u'admin_email'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'admin@university.edu.')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 14
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'serial_number')
    record_arguments_record_assignments_dict['argument_value'] = u'20091227'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 14
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'refresh_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 14
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'retry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 14
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'expiry_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 14
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'soa'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'minimum_seconds')
    record_arguments_record_assignments_dict['argument_value'] = u'5'
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make computer 1 'ptr' record for 'external' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'ptr'
    records_dict['record_target'] = u'1'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'4.3.2.1.in-addr'
    records_dict['record_view_dependency'] = u'external_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 15
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'ptr'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'assignment_host')
    record_arguments_record_assignments_dict['argument_value'] = (
        u'computer1')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make computer 4 'ptr' record for 'internal' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'ptr'
    records_dict['record_target'] = u'4'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'168.192.in-addr'
    records_dict['record_view_dependency'] = u'internal_dep'
    db_instance.MakeRow('records', records_dict)
    record_arguments_record_assignments_dict = {}
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_record_id'] = 16
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_type'] = u'ptr'
    record_arguments_record_assignments_dict[
        'record_arguments_records_assignments_argument_name'] = (
            u'assignment_host')
    record_arguments_record_assignments_dict['argument_value'] = (
        u'computer4')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    ## Make ACLs
    acls_dict = {}
    acls_dict['acl_name'] = u'public'
    db_instance.MakeRow('acls', acls_dict)
    acls_dict['acl_name'] = u'secret'
    db_instance.MakeRow('acls', acls_dict)
    acl_ranges_dict = {}
    acl_ranges_dict['acl_ranges_acl_name'] = u'public'
    acl_ranges_dict['acl_range_cidr_block'] = u'192.168.1.4/30'
    db_instance.MakeRow('acl_ranges', acl_ranges_dict)
    acl_ranges_dict['acl_range_cidr_block'] = u'10.10/32'
    db_instance.MakeRow('acl_ranges', acl_ranges_dict)
    acl_ranges_dict['acl_ranges_acl_name'] = u'secret'
    acl_ranges_dict['acl_range_cidr_block'] = u'10.10/32'
    db_instance.MakeRow('acl_ranges', acl_ranges_dict)


    ## Make view ACL assignments
    view_acl_assignments_dict = {}
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'internal'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'secret'
    view_acl_assignments_dict['view_acl_assignments_range_allowed'] = 1
    db_instance.MakeRow('view_acl_assignments', view_acl_assignments_dict)
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'internal'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'public'    
    view_acl_assignments_dict['view_acl_assignments_range_allowed'] = 0
    db_instance.MakeRow('view_acl_assignments', view_acl_assignments_dict)
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'external'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'public'    
    view_acl_assignments_dict['view_acl_assignments_range_allowed'] = 1
    db_instance.MakeRow('view_acl_assignments', view_acl_assignments_dict)
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'private'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'secret'    
    view_acl_assignments_dict['view_acl_assignments_range_allowed'] = 0
    db_instance.MakeRow('view_acl_assignments', view_acl_assignments_dict)

    ## Make named conf global option
    named_conf_global_options_dict = {}
    named_conf_global_options_dict['global_options'] = u'null'
    named_conf_global_options_dict['options_created'] = datetime.datetime(
        2009, 7, 4, 13, 37, 0)
    named_conf_global_options_dict[
        'named_conf_global_options_dns_server_set_name'] = (
            u'internal_dns')
    named_conf_global_options_dict['named_conf_global_options_id'] = 1
    db_instance.MakeRow('named_conf_global_options',
                        named_conf_global_options_dict)

    named_conf_global_options_dict['global_options'] = iscpy.Serialize(
        u'options {\n\tdirectory "test_data/named/named";\n\trecursion no;\n'
        '\tmax-cache-size 512M;\n};\n\nlogging {\n\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n\t};\n\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n\t\tseverity info;\n\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n};\n\ncontrols {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n};\n\n'
        'include "/etc/rndc.key";\n')
    named_conf_global_options_dict['options_created'] = datetime.datetime(
        2010, 3, 11, 13, 37, 0)
    named_conf_global_options_dict[
        'named_conf_global_options_dns_server_set_name'] = (
            u'internal_dns')
    named_conf_global_options_dict['named_conf_global_options_id'] = 2
    db_instance.MakeRow('named_conf_global_options',
                        named_conf_global_options_dict)

    named_conf_global_options_dict['global_options'] = iscpy.Serialize(
        u'options {\n\tdirectory "test_data/named/named";\n\trecursion no;\n'
        '\tmax-cache-size 512M;\n};\n\nlogging {\n\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n\t};\n\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n\t\tseverity info;\n\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n};\n\ncontrols {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n};\n\n'
        'include "/etc/rndc.key";\n')
    named_conf_global_options_dict['options_created'] = datetime.datetime(
        2010, 3, 11, 13, 37, 0)
    named_conf_global_options_dict[
        'named_conf_global_options_dns_server_set_name'] = (
            u'external_dns')
    named_conf_global_options_dict['named_conf_global_options_id'] = 3
    db_instance.MakeRow('named_conf_global_options',
                        named_conf_global_options_dict)

    named_conf_global_options_dict['global_options'] = iscpy.Serialize(
        u'options {\n\tdirectory "test_data/named/named";\n\trecursion no;\n'
        '\tmax-cache-size 512M;\n};\n\nlogging {\n\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n\t};\n\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n\t\tseverity info;\n\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n};\n\ncontrols {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n};\n\n'
        'include "/etc/rndc.key";\n')
    named_conf_global_options_dict['options_created'] = datetime.datetime(
        2010, 3, 11, 13, 37, 0)
    named_conf_global_options_dict[
        'named_conf_global_options_dns_server_set_name'] = (
            u'private_dns')
    named_conf_global_options_dict['named_conf_global_options_id'] = 4
    db_instance.MakeRow('named_conf_global_options',
                        named_conf_global_options_dict)

    # COMMIT
    db_instance.EndTransaction()

    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')

  def tearDown(self):
    if( os.path.exists(self.bind_config_dir) ):
      shutil.rmtree(self.bind_config_dir)
    if( os.path.exists('dns_tree-1.tar.bz2') ):
      os.remove('dns_tree-1.tar.bz2')
    for fname in os.listdir('./test_data/backup_dir'):
      if( fname.endswith('.bz2') ):
        os.remove('./test_data/backup_dir/%s' % fname)

  def testMakeFilesFromDB(self):
    output = os.popen('python %s -c %s' % (
        EXEC, CONFIG_FILE))
    output.close()
    for fname in os.listdir(self.backup_dir):
      if( not fname.endswith('.tar.bz2') ):
        continue
      if( 'dns_tree' in fname ):
        tar = tarfile.open('%s/%s' % (self.backup_dir, fname))
        tar.extractall()
        tar.close()
        break
    else:
      raise Exception("File not found")
    ##Test Files
    handle = open(
        './%s/external_dns_servers/named/external_dns_config' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                                    'dns_servers = ns1.university.edu,'
                                    'dns2.university.edu,dns3.university.edu\n'
                                    'dns_server_set_name = external_dns\n\n')
    handle.close()
    handle = open('./%s/external_dns_servers/named.conf' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(),
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s/named";\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "external" {\n'
        '\tmatch-clients { public; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.1.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/4.3.2.1.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tuple(['%s/%s' % (os.getcwd(), self.named_dir) for x in range(3)]))
    handle.close()
    handle = open(
        './%s/external_dns_servers/named/external/4.3.2.1.in-addr.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(),
                     '; This zone file is autogenerated. DO NOT EDIT.\n'
                     '$ORIGIN 4.3.2.1.in-addr.arpa.\n'
                     '4.3.2.1.in-addr.arpa. 3600 in soa ns1.university.edu. '
                     'admin@university.edu. 20091224 5 5 5 5\n'
                     '1 3600 in ptr computer1\n')
    handle.close()
    handle = open(
        './%s/external_dns_servers/named/external/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        'university.edu. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091227 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu\n'
        '@ 3600 in ns ns2.university.edu\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n'
        'computer1 3600 in a 1.2.3.5\n'
        'computer3 3600 in a 1.2.3.6\n')
    handle.close()
    handle = open(
        './%s/internal_dns_servers/named/internal_dns_config' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                                    'dns_servers = ns1.int.university.edu,'
                                    'dns1.university.edu\n'
                                    'dns_server_set_name = internal_dns\n\n')
    handle.close()
    handle = open('./%s/internal_dns_servers/named.conf' %
                  self.bind_config_dir, 'r')    
    self.assertEqual(handle.read(),
		'#This named.conf file is autogenerated. DO NOT EDIT\n'
        'include "/etc/rndc.key";\n'
        'logging { category "update-security" { "security"; };\n'
        'category "queries" { "query_logging"; };\n'
        'channel "query_logging" { syslog local5;\n'
        'severity info; };\n'
        'category "client" { "null"; };\n'
        'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
        'print-time yes; }; };\n'
        'options { directory "%s/named";\n'
        'recursion no;\n'
        'max-cache-size 512M; };\n'
        'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
        'acl secret {\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'acl public {\n'
        '\t192.168.1.4/30;\n'
        '\t10.10/32;\n'
        '};\n'
        '\n'
        'view "internal" {\n'
        '\tmatch-clients { secret; !public; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "168.192.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/168.192.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "external" {\n'
        '\tmatch-clients { public; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/university.edu.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.1.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/4.3.2.1.in-addr.db";\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tuple(['%s/%s' % (os.getcwd(), self.named_dir) for x in range(5)]))
    handle.close()
    handle = open(
        './%s/internal_dns_servers/named/external/4.3.2.1.in-addr.db' % 
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN 4.3.2.1.in-addr.arpa.\n'
        '4.3.2.1.in-addr.arpa. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091224 5 5 5 5\n'
        '1 3600 in ptr computer1\n')
    handle.close()
    handle = open(
        './%s/internal_dns_servers/named/external/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        'university.edu. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091227 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu\n'
        '@ 3600 in ns ns2.university.edu\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n'
        'computer1 3600 in a 1.2.3.5\n'
        'computer3 3600 in a 1.2.3.6\n')
    handle.close()
    handle = open(
        './%s/internal_dns_servers/named/internal/168.192.in-addr.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN 168.192.in-addr.arpa.\n'
        '168.192.in-addr.arpa. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091223 5 5 5 5\n'
        '4 3600 in ptr computer4\n')
    handle.close()
    handle = open(
        './%s/internal_dns_servers/named/internal/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        'university.edu. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091225 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu\n'
        '@ 3600 in ns ns2.university.edu\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n'
        'computer1 3600 in a 192.168.1.1\n'
        'computer2 3600 in a 192.168.1.2\n'
        'computer4 3600 in a 192.168.1.4\n')
    handle.close()
    handle = open(
        './%s/private_dns_servers/named/private_dns_config' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                                    'dns_servers = ns1.int.university.edu,'
                                    'dns4.university.edu\n'
                                    'dns_server_set_name = private_dns\n\n')
    handle.close()
    handle = open('./%s/private_dns_servers/named.conf' % 
                  self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '#This named.conf file is autogenerated. DO NOT EDIT\n'
            'include "/etc/rndc.key";\n'
            'logging { category "update-security" { "security"; };\n'
            'category "queries" { "query_logging"; };\n'
            'channel "query_logging" { syslog local5;\n'
            'severity info; };\n'
            'category "client" { "null"; };\n'
            'channel "security" { file "/var/log/named-security.log" versions 10 size 10m;\n'
            'print-time yes; }; };\n'
            'options { directory "%s/named";\n'
            'recursion no;\n'
            'max-cache-size 512M; };\n'
            'controls { inet * allow { control-hosts; } keys { rndc-key; }; };\n'
            'acl secret {\n'
            '\t10.10/32;\n'
            '};\n'
            '\n'
            'acl public {\n'
            '\t192.168.1.4/30;\n'
            '\t10.10/32;\n'
            '};\n'
            '\n'
            'view "private" {\n'
            '\tmatch-clients { !secret; };\n'
            '\tzone "university.edu" {\n'
            '\t\ttype master;\n'
            '\t\tfile "%s/named/private/university.edu.db";\n'
            '\t\tallow-update { none; };\n'
            '\t};\n'
            '};' % tuple(['%s/%s' % (os.getcwd(), self.named_dir) for x in range(2)]))
    handle.close()
    handle = open(
        './%s/private_dns_servers/named/private/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        'university.edu. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091227 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu\n'
        '@ 3600 in ns ns2.university.edu\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n')
    handle.close()

    output = os.popen('python %s -c %s' % (
        EXEC, CONFIG_FILE))
    self.assertEquals(output.read(), 'No changes made to database. In order '
                                     'to export use the --force flag.\n')
    output.close()
    output = os.popen('python %s -c %s --force' % (
        EXEC, CONFIG_FILE))
    self.assertEquals(output.read(), '')
    output.close()

  for fname in os.listdir('.'):
    if( fname.endswith('.bz2') ):
      os.remove(fname)

  def testErrors(self):
    zones_dict = {}

    try:
      self.db_instance.StartTransaction()
      zones_dict['zone_name'] = u'university.edu'
      self.db_instance.RemoveRow('zones', zones_dict)
    finally:
      self.db_instance.EndTransaction()
    output = os.popen('python %s -c %s -f' % (
        EXEC, CONFIG_FILE))
    self.assertEquals(output.read(),
        'ERROR: Server set private_dns has no zones in private view.\n')
    output.close()

    views_dict = {}
    try:
      self.db_instance.StartTransaction()
      views_dict['view_options'] = u'recursion no;'

      views_dict['view_name'] = u'internal'
      self.db_instance.RemoveRow('views', views_dict)

      views_dict['view_name'] = u'external'
      self.db_instance.RemoveRow('views', views_dict)

      views_dict['view_name'] = u'private'
      self.db_instance.RemoveRow('views', views_dict)
    finally:
      self.db_instance.EndTransaction()

    output = os.popen('python %s -c %s' % (
        EXEC, CONFIG_FILE))
    self.assertEquals(output.read(),
        'ERROR: Server set external_dns has no views.\n')
    output.close()


    dns_server_sets_dict = {}
    try:
      self.db_instance.StartTransaction()
      dns_server_sets_dict['dns_server_set_name'] = u'internal_dns'
      self.db_instance.RemoveRow('dns_server_sets', dns_server_sets_dict)

      dns_server_sets_dict['dns_server_set_name'] = u'external_dns'
      self.db_instance.RemoveRow('dns_server_sets', dns_server_sets_dict)

      dns_server_sets_dict['dns_server_set_name'] = u'private_dns'
      self.db_instance.RemoveRow('dns_server_sets', dns_server_sets_dict)
    finally:
      self.db_instance.EndTransaction()

    output = os.popen('python %s -c %s' % (
        EXEC, CONFIG_FILE))
    self.assertEquals(output.read(), 'ERROR: No dns server sets found.\n')
    output.close()

  for fname in os.listdir('.'):
    if( fname.endswith('.bz2') ):
      os.remove(fname)

if( __name__ == '__main__' ):
      unittest.main()
