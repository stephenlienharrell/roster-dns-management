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

"""Regression test for tree exporter

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import os
import shutil
import sys
import tarfile
import unittest
import datetime
import glob
import roster_core
import ConfigParser
from roster_config_manager import tree_exporter


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
SCHEMA_FILE = '../roster-core/data/database_schema.sql'
DATA_FILE = 'test_data/test_data.sql'
KSKFILE = 'test_data/Ksub.university.edu.+005+27931.key'
ZSKFILE = 'test_data/Ksub.university.edu.+005+43557.key'
ZONE_FILE = 'test_data/test_zone.db'
DNSSEC_SIGNZONE_EXEC = '/usr/sbin/dnssec-signzone'
DNSSEC_KEYGEN_EXEC = '/usr/sbin/dnssec-keygen'
RANDOM = '/dev/urandom'


class TestTreeExporter(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.bind_config_dir = self.config_instance.config_file['exporter'][
        'root_config_dir']
    self.named_dir = self.config_instance.config_file['exporter'][
        'named_dir']
    self.tree_exporter_instance = tree_exporter.BindTreeExport(
        CONFIG_FILE)

    db_instance = self.config_instance.GetDb()

    schema = roster_core.embedded_files.SCHEMA_FILE
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(data)
    db_instance.EndTransaction()
    db_instance.close()
    self.db_instance = db_instance

    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

    db_instance.StartTransaction()

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

    zones_dict['zone_name'] = u'168.192.in-addr.arpa'
    db_instance.MakeRow('zones', zones_dict)

    zones_dict['zone_name'] = u'4.3.2.1.in-addr.arpa'
    db_instance.MakeRow('zones', zones_dict)

    # Make Zone/View assignments
    zone_view_assignments_dict = {}

    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'university.edu')
    zone_view_assignments_dict['zone_view_assignments_zone_type'] = u'master'
    zone_view_assignments_dict['zone_origin'] = u'university.edu.'
    zone_view_assignments_dict['zone_options'] = (
        u'#Allow update\nallow-update { none; };\n')

    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = u'any'
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
        u'168.192.in-addr.arpa')
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
        u'4.3.2.1.in-addr.arpa')
    zone_view_assignments_dict['zone_origin'] = u'4.3.2.1.in-addr.arpa.'
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    zone_view_assignments_dict['zone_view_assignments_zone_type'] = u'slave'
    zone_view_assignments_dict['zone_view_assignments_zone_name'] = (
        u'bio.university.edu')
    zone_view_assignments_dict['zone_origin'] = u'university.edu.'
    zone_view_assignments_dict['zone_options'] = (
        u'#Allow update\nallow-transfer { any; };\n')

    zone_view_assignments_dict['zone_origin'] = u'university4.edu.'
    zone_view_assignments_dict['zone_view_assignments_view_dependency'] = (
        u'external_dep')
    db_instance.MakeRow('zone_view_assignments', zone_view_assignments_dict)

    # Make DNS Servers
    dns_servers_dict = {}
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
    records_dict['record_zone_name'] = u'168.192.in-addr.arpa'
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
        'record_arguments_records_assignments_argument_name'] = u'serial_number'
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
        'record_arguments_records_assignments_argument_name'] = u'assignment_ip'
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
        'record_arguments_records_assignments_argument_name'] = u'assignment_ip'
    record_arguments_record_assignments_dict['argument_value'] = (
        u'192.168.1.2')
    db_instance.MakeRow('record_arguments_records_assignments',
                        record_arguments_record_assignments_dict)

    # Make 'soa' record for 'external' view
    records_dict['records_id'] = None
    records_dict['record_type'] = u'soa'
    records_dict['record_target'] = u'4.3.2.1.in-addr.arpa.'
    records_dict['record_ttl'] = 3600
    records_dict['record_zone_name'] = u'4.3.2.1.in-addr.arpa'
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
        'record_arguments_records_assignments_argument_name'] = u'serial_number'
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
        'record_arguments_records_assignments_argument_name'] = u'assignment_ip'
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
        'record_arguments_records_assignments_argument_name'] = u'assignment_ip'
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
        'record_arguments_records_assignments_argument_name'] = u'assignment_ip'
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
        'record_arguments_records_assignments_argument_name'] = u'serial_number'
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
        'record_arguments_records_assignments_argument_name'] = u'serial_number'
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
        'record_arguments_records_assignments_argument_name'] = u'serial_number'
    record_arguments_record_assignments_dict['argument_value'] = u'20091225'
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
    records_dict['record_zone_name'] = u'4.3.2.1.in-addr.arpa'
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
    records_dict['record_zone_name'] = u'168.192.in-addr.arpa'
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
    acl_ranges_dict['acl_range_allowed'] = 1
    acl_ranges_dict['acl_range_cidr_block'] = u'192.168.1.4/30'
    db_instance.MakeRow('acl_ranges', acl_ranges_dict)
    acl_ranges_dict['acl_range_allowed'] = 1
    acl_ranges_dict['acl_range_cidr_block'] = u'10.10/32'
    db_instance.MakeRow('acl_ranges', acl_ranges_dict)
    acl_ranges_dict['acl_ranges_acl_name'] = u'secret'
    acl_ranges_dict['acl_range_allowed'] = 0
    acl_ranges_dict['acl_range_cidr_block'] = u'10.10/32'
    db_instance.MakeRow('acl_ranges', acl_ranges_dict)

    ## Make view ACL assignments
    view_acl_assignments_dict = {}
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'internal'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'secret'
    db_instance.MakeRow('view_acl_assignments', view_acl_assignments_dict)
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'internal'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'public'
    db_instance.MakeRow('view_acl_assignments', view_acl_assignments_dict)
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'external'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'public'
    db_instance.MakeRow('view_acl_assignments', view_acl_assignments_dict)
    view_acl_assignments_dict['view_acl_assignments_view_name'] = u'private'
    view_acl_assignments_dict['view_acl_assignments_acl_name'] = u'secret'
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

    named_conf_global_options_dict['global_options'] = (
        u'options {\n\tdirectory "/var/domain";\n\trecursion no;\n'
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

    named_conf_global_options_dict['global_options'] = (
        u'options {\n\tdirectory "/var/domain";\n\trecursion no;\n'
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

    named_conf_global_options_dict['global_options'] = (
        u'options {\n\tdirectory "/var/domain";\n\trecursion no;\n'
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

    # get data
    self.tree_exporter_instance.db_instance.StartTransaction()
    self.data = self.tree_exporter_instance.GetRawData()
    self.tree_exporter_instance.db_instance.EndTransaction()
    self.cooked_data = self.tree_exporter_instance.CookData(self.data[0])

  def tearDown(self):
    if( os.path.exists(self.bind_config_dir) ):
        shutil.rmtree(self.bind_config_dir)
    for file in glob.glob('*.key'):
      os.remove(file)
    for file in glob.glob('*.private'):
      os.remove(file)

  def testTreeExporterListRecordArgumentDefinitions(self):
    search_record_arguments_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments')

    self.db_instance.StartTransaction()
    try:
      record_arguments = self.db_instance.ListRow('record_arguments',
                                                  search_record_arguments_dict)
    finally:
      self.db_instance.EndTransaction()

    self.assertEqual(self.tree_exporter_instance.ListRecordArgumentDefinitions(
        record_arguments),
        {u'a': [{'argument_name': u'assignment_ip', 'argument_order': 0}],
         u'soa': [{'argument_name': u'name_server', 'argument_order': 0},
                  {'argument_name': u'admin_email', 'argument_order': 1},
                  {'argument_name': u'serial_number', 'argument_order': 2},
                  {'argument_name': u'refresh_seconds', 'argument_order': 3},
                  {'argument_name': u'retry_seconds', 'argument_order': 4},
                  {'argument_name': u'expiry_seconds', 'argument_order': 5},
                  {'argument_name': u'minimum_seconds', 'argument_order': 6}],
         u'ns': [{'argument_name': u'name_server', 'argument_order': 0}],
         u'ptr': [{'argument_name': u'assignment_host', 'argument_order': 0}],
         u'aaaa': [{'argument_name': u'assignment_ip', 'argument_order': 0}],
         u'cname': [{'argument_name': u'assignment_host',
                     'argument_order': 0}],
         u'srv': [{'argument_name': u'priority', 'argument_order': 0},
                  {'argument_name': u'weight', 'argument_order': 1},
                  {'argument_name': u'port', 'argument_order': 2},
                  {'argument_name': u'assignment_host', 'argument_order': 3}],
         u'hinfo': [{'argument_name': u'hardware', 'argument_order': 0},
                    {'argument_name': u'os', 'argument_order': 1}],
         u'txt': [{'argument_name': u'quoted_text', 'argument_order': 0}],
         u'mx': [{'argument_name': u'priority', 'argument_order': 0},
                 {'argument_name': u'mail_server', 'argument_order': 1}]})

  def testTreeExporterSortRecords(self):

    records_dict = self.db_instance.GetEmptyRowDict('records')
    record_args_assignment_dict = self.db_instance.GetEmptyRowDict(
        'record_arguments_records_assignments')
    self.db_instance.StartTransaction()
    try:
      records = self.db_instance.ListRow(
          'records', records_dict, 'record_arguments_records_assignments',
          record_args_assignment_dict)
    finally:
      self.db_instance.EndTransaction()

    self.assertEqual(self.tree_exporter_instance.SortRecords(records),
                     {(u'university.edu', u'external_dep'):
                          {13: {u'serial_number': 20091227,
                                u'refresh_seconds': 5,
                                'target': u'university.edu.',
                                u'name_server': u'ns1.university.edu.',
                                u'retry_seconds': 5, 'ttl': 3600,
                                u'minimum_seconds': 5, 'record_type': u'soa',
                                'view_name': u'external',
                                'last_user': u'sharrell',
                                'zone_name': u'university.edu',
                                u'admin_email': u'admin@university.edu.',
                                u'expiry_seconds': 5},
                           6: {'target': u'computer1', 'ttl': 3600,
                               'record_type': u'a', 'view_name': u'external',
                               'last_user': u'sharrell',
                               'zone_name': u'university.edu',
                               u'assignment_ip': u'1.2.3.5'},
                           7: {'target': u'computer3', 'ttl': 3600,
                               'record_type': u'a', 'view_name': u'external',
                               'last_user': u'sharrell',
                               'zone_name': u'university.edu',
                               u'assignment_ip': u'1.2.3.6'}},
                      (u'4.3.2.1.in-addr.arpa', u'external_dep'):
                          {5: {u'serial_number': 20091224,
                               u'refresh_seconds': 5,
                               'target': u'4.3.2.1.in-addr.arpa.',
                               u'name_server': u'ns1.university.edu.',
                               u'retry_seconds': 5, 'ttl': 3600,
                               u'minimum_seconds': 5, 'record_type': u'soa',
                               'view_name': u'external',
                               'last_user': u'sharrell',
                               'zone_name': u'4.3.2.1.in-addr.arpa',
                               u'admin_email': u'admin@university.edu.',
                               u'expiry_seconds': 5},
                           15: {'target': u'1', 'ttl': 3600,
                                'record_type': u'ptr',
                                'view_name': u'external',
                                'last_user': u'sharrell',
                                'zone_name': u'4.3.2.1.in-addr.arpa',
                                u'assignment_host': u'computer1'}},
                      (u'168.192.in-addr.arpa', u'internal_dep'):
                          {16: {'target': u'4', 'ttl': 3600,
                                'record_type': u'ptr',
                                'view_name': u'internal',
                                'last_user': u'sharrell',
                                'zone_name': u'168.192.in-addr.arpa',
                                u'assignment_host': u'computer4'},
                           2: {u'serial_number': 20091223,
                               u'refresh_seconds': 5,
                               'target': u'168.192.in-addr.arpa.',
                               u'name_server': u'ns1.university.edu.',
                               u'retry_seconds': 5, 'ttl': 3600,
                               u'minimum_seconds': 5,
                               'record_type': u'soa',
                               'view_name': u'internal',
                               'last_user': u'sharrell',
                               'zone_name': u'168.192.in-addr.arpa',
                               u'admin_email': u'admin@university.edu.',
                               u'expiry_seconds': 5}},
                      (u'university.edu', u'private_dep'):
                          {14: {u'serial_number': 20091225,
                                u'refresh_seconds': 5,
                                'target': u'university.edu.',
                                u'name_server': u'ns1.university.edu.',
                                u'retry_seconds': 5, 'ttl': 3600,
                                u'minimum_seconds': 5, 'record_type': u'soa',
                                'view_name': u'private',
                                'last_user': u'sharrell',
                                'zone_name': u'university.edu',
                                u'admin_email': u'admin@university.edu.',
                                u'expiry_seconds': 5}},
                      (u'university.edu', u'internal_dep'):
                          {11: {'target': u'computer4', 'ttl': 3600,
                                'record_type': u'a', 'view_name': u'internal',
                                'last_user': u'sharrell',
                                'zone_name': u'university.edu',
                                u'assignment_ip': u'192.168.1.4'},
                           12: {u'serial_number': 20091225,
                                u'refresh_seconds': 5,
                                'target': u'university.edu.',
                                u'name_server': u'ns1.university.edu.',
                                u'retry_seconds': 5, 'ttl': 3600,
                                u'minimum_seconds': 5, 'record_type': u'soa',
                                'view_name': u'internal',
                                'last_user': u'sharrell',
                                'zone_name': u'university.edu',
                                u'admin_email': u'admin@university.edu.',
                                u'expiry_seconds': 5},
                           3: {'target': u'computer1', 'ttl': 3600,
                               'record_type': u'a',
                               'view_name': u'internal',
                               'last_user': u'sharrell',
                               'zone_name': u'university.edu',
                               u'assignment_ip': u'192.168.1.1'},
                           4: {'target': u'computer2', 'ttl': 3600,
                               'record_type': u'a', 'view_name': u'internal',
                               'last_user': u'sharrell',
                               'zone_name': u'university.edu',
                               u'assignment_ip': u'192.168.1.2'}},
                      (u'university.edu', u'any'):
                          {8: {'target': u'@', 'ttl': 3600, u'priority': 1,
                               'record_type': u'mx', 'view_name': u'any',
                               'last_user': u'sharrell',
                               'zone_name': u'university.edu',
                               u'mail_server': u'mail2.university.edu.'},
                           1: {'target': u'@', 'ttl': 3600, u'priority': 1,
                               'record_type': u'mx', 'view_name': u'any',
                               'last_user': u'sharrell',
                               'zone_name': u'university.edu',
                               u'mail_server': u'mail1.university.edu.'},
                           10: {'target': u'@',
                                u'name_server': u'ns2.university.edu',
                                'ttl': 3600, 'record_type': u'ns',
                                'view_name': u'any',
                                'last_user': u'sharrell',
                                'zone_name': u'university.edu'},
                           9: {'target': u'@',
                               u'name_server': u'ns1.university.edu',
                               'ttl': 3600, 'record_type': u'ns',
                               'view_name': u'any',
                               'last_user': u'sharrell',
                               'zone_name': u'university.edu'}}})

  def testTreeExporterMakeNamedConf(self):
    self.core_instance.SetMaintenanceFlag(1)
    self.assertRaises(tree_exporter.MaintenanceError,
                      self.tree_exporter_instance.ExportAllBindTrees)
    self.core_instance.SetMaintenanceFlag(0)
    self.tree_exporter_instance.ExportAllBindTrees()
    tar = tarfile.open(self.tree_exporter_instance.tar_file_name)
    tar.extractall()
    tar.close()
    self.assertEqual(self.tree_exporter_instance.MakeNamedConf(
        self.data[0], self.cooked_data, u'internal_dns'),
        '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'options {\n'
        '\tdirectory "%s/named";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size '
        '10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n\n'
        'acl secret {\n'
        '\t!10.10/32;\n'
        '};\n\n'
        'acl public {\n'
        '\t10.10/32;\n'
        '\t192.168.1.4/30;\n'
        '};\n\n'
        'view "internal" {\n'
        '\tmatch-clients { public; secret; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "168.192.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/168.192.in-addr.arpa.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "external" {\n'
        '\tmatch-clients { public; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.1.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/4.3.2.1.in-addr.arpa.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n\t};'
        '\n};' % tuple([self.named_dir.rstrip('/') for x in range(5)]))
    for fname in ['audit_log_replay_dump-1.bz2', 'full_database_dump-1.bz2',
                  self.tree_exporter_instance.tar_file_name]:
      if( os.path.exists(fname) ):
        os.remove(fname)

    self.assertRaises(tree_exporter.ChangesNotFoundError,
                      self.tree_exporter_instance.ExportAllBindTrees)

  def testTreeExporterCookRawDump(self):
    self.db_instance.StartTransaction()
    raw_dump = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    dump_lines = ''.join(self.tree_exporter_instance.CookRawDump(raw_dump)[1])

    self.core_instance.SetMaintenanceFlag(1)
    self.core_instance.MakeZoneType(u'zonetype5')

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(dump_lines)
    self.db_instance.EndTransaction()

    self.db_instance.StartTransaction()
    raw_dump_2 = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()

    self.assertEquals(raw_dump, raw_dump_2)

    self.db_instance.StartTransaction()
    raw_dump = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    dump_lines = ''.join(self.tree_exporter_instance.CookRawDump(raw_dump)[0])

    self.core_instance.MakeZoneType(u'zonetype5')

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(dump_lines)
    self.db_instance.EndTransaction()

    self.db_instance.StartTransaction()
    raw_dump_2 = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    # audit log is constantly changing
    del raw_dump['audit_log']
    del raw_dump_2['audit_log']

    self.assertEquals(raw_dump, raw_dump_2)

    self.db_instance.StartTransaction()
    raw_dump = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    dump_lines = ''.join(self.tree_exporter_instance.CookRawDump(raw_dump)[0])

    self.core_instance.SetMaintenanceFlag(1)

    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(dump_lines)
    self.db_instance.EndTransaction()

    self.db_instance.StartTransaction()
    raw_dump_2 = self.db_instance.DumpDatabase()
    self.db_instance.EndTransaction()
    del raw_dump['audit_log']
    del raw_dump_2['audit_log']

    self.assertNotEquals(raw_dump, raw_dump_2)

  def testTreeExporterGetRawData(self):
    self.tree_exporter_instance.db_instance.StartTransaction()
    raw_data = self.tree_exporter_instance.GetRawData()
    self.tree_exporter_instance.db_instance.EndTransaction()

    ## Testing the RawData raw_data[0]
    self.assertEqual(raw_data[0]['dns_server_sets'],
        ({'dns_server_set_name':u'external_dns'},
         {'dns_server_set_name':u'internal_dns'},
         {'dns_server_set_name':u'private_dns'}))

    self.assertEqual(raw_data[0]['view_acl_assignments'],
        ({'view_acl_assignments_view_name':u'external',
          'view_acl_assignments_acl_name':u'public'},
         {'view_acl_assignments_view_name':u'internal',
          'view_acl_assignments_acl_name':u'public'},
         {'view_acl_assignments_view_name':u'internal',
          'view_acl_assignments_acl_name':u'secret'},
         {'view_acl_assignments_view_name':u'private',
          'view_acl_assignments_acl_name':u'secret'}))

    self.assertEqual(raw_data[0]['view_dependency_assignments'],
        ({'view_dependency_assignments_view_dependency':u'any',
          'view_dependency_assignments_view_name':u'external'},
         {'view_dependency_assignments_view_dependency':u'external_dep',
          'view_dependency_assignments_view_name':u'external'},
         {'view_dependency_assignments_view_dependency':u'any',
          'view_dependency_assignments_view_name':u'internal'},
         {'view_dependency_assignments_view_dependency':u'internal_dep',
          'view_dependency_assignments_view_name':u'internal'},
         {'view_dependency_assignments_view_dependency':u'any',
          'view_dependency_assignments_view_name':u'private'},
         {'view_dependency_assignments_view_dependency':u'private_dep',
          'view_dependency_assignments_view_name':u'private'}))

    self.assertEqual(raw_data[0]['zone_view_assignments'],
        ({'zone_origin':u'university.edu.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'university.edu',
          'zone_view_assignments_view_dependency':u'any',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'university.edu.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'university.edu',
           'zone_view_assignments_view_dependency':u'internal_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'university.edu.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'university.edu',
          'zone_view_assignments_view_dependency':u'external_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'university.edu.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'university.edu',
          'zone_view_assignments_view_dependency':u'private_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'university2.edu.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'int.university.edu',
          'zone_view_assignments_view_dependency':u'internal_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'university2.edu.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'int.university.edu',
          'zone_view_assignments_view_dependency':u'private_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'university3.edu.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'priv.university.edu',
          'zone_view_assignments_view_dependency':u'private_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'168.192.in-addr.arpa.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'168.192.in-addr.arpa',
          'zone_view_assignments_view_dependency':u'internal_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'168.192.in-addr.arpa.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'168.192.in-addr.arpa',
          'zone_view_assignments_view_dependency':u'external_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'168.192.in-addr.arpa.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'168.192.in-addr.arpa',
          'zone_view_assignments_view_dependency':u'private_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'4.3.2.1.in-addr.arpa.',
          'zone_view_assignments_zone_type':u'master',
          'zone_view_assignments_zone_name':u'4.3.2.1.in-addr.arpa',
          'zone_view_assignments_view_dependency':u'external_dep',
          'zone_options':u'#Allow update\nallow-update { none; };\n'},
         {'zone_origin':u'university4.edu.',
          'zone_view_assignments_zone_type':u'slave',
          'zone_view_assignments_zone_name':u'bio.university.edu',
          'zone_view_assignments_view_dependency':u'external_dep',
          'zone_options':u'#Allow update\nallow-transfer { any; };\n'}))

    ## Testing the RawDump raw_data[1]
    self.assertEqual(raw_data[1]['zones']['rows'],
        [{'zone_name': "'168.192.in-addr.arpa'", 'zones_id': '7'},
         {'zone_name': "'4.3.2.1.in-addr.arpa'", 'zones_id': '8'},
         {'zone_name': "'bio.university.edu'", 'zones_id': '2'},
         {'zone_name': "'cs.university.edu'", 'zones_id': '1'},
         {'zone_name': "'eas.university.edu'", 'zones_id': '3'},
         {'zone_name': "'int.university.edu'", 'zones_id': '5'},
         {'zone_name': "'priv.university.edu'", 'zones_id': '6'},
         {'zone_name': "'university.edu'", 'zones_id': '4'}])

    self.assertEqual(raw_data[1]['reserved_words']['columns'],
        [u'reserved_word_id', u'reserved_word'])

    self.assertEqual(raw_data[1]['reserved_words']['rows'],
        [])

    self.assertEqual(raw_data[1]['zone_types']['rows'],
        [{'zone_type': "'forward'", 'zone_type_id': '3'},
         {'zone_type': "'hint'", 'zone_type_id': '4'},
         {'zone_type': "'master'", 'zone_type_id': '1'},
         {'zone_type': "'slave'", 'zone_type_id': '2'}])

    self.assertEqual(raw_data[1]['users']['rows'],
        [{'access_level': '0',
          'user_name': "'tree_export_user'",
          'users_id': '1'},
         {'access_level': '32',
          'user_name': "'jcollins'",
          'users_id': '2'},
         {'access_level': '128',
          'user_name': "'sharrell'",
          'users_id': '3'},
         {'access_level': '64',
          'user_name': "'shuey'",
          'users_id': '4'}])

    self.assertEqual(raw_data[1]['view_dependency_assignments']['rows'],
        [{'view_dependency_assignments_id': '2',
          'view_dependency_assignments_view_dependency': "'any'",
          'view_dependency_assignments_view_name': "'external'"},
         {'view_dependency_assignments_id': '5',
          'view_dependency_assignments_view_dependency': "'external_dep'",
          'view_dependency_assignments_view_name': "'external'"},
         {'view_dependency_assignments_id': '1',
          'view_dependency_assignments_view_dependency': "'any'",
          'view_dependency_assignments_view_name': "'internal'"},
         {'view_dependency_assignments_id': '4',
          'view_dependency_assignments_view_dependency': "'internal_dep'",
          'view_dependency_assignments_view_name': "'internal'"},
         {'view_dependency_assignments_id': '3',
          'view_dependency_assignments_view_dependency': "'any'",
          'view_dependency_assignments_view_name': "'private'"},
         {'view_dependency_assignments_id': '6',
          'view_dependency_assignments_view_dependency': "'private_dep'",
          'view_dependency_assignments_view_name': "'private'"}])

  def testTreeExporterCookData(self):
    self.tree_exporter_instance.db_instance.StartTransaction()
    raw_data = self.tree_exporter_instance.GetRawData()
    self.tree_exporter_instance.db_instance.EndTransaction()
    cooked_data = self.tree_exporter_instance.CookData(raw_data[0])

    self.assertEqual(cooked_data['external_dns'], {
        'dns_servers': [u'ns1.university.edu', u'dns2.university.edu',u'dns3.university.edu'],
            'views':{
                u'external':{
                    'zones':{
                        u'university.edu':{
                            'zone_type': u'master',
                            'records':[{
                                'target': u'@',
                                'ttl': 3600,
                                u'priority': 1,
                                'record_type': u'mx',
                                'view_name': u'any',
                                'last_user': u'sharrell',
                                'zone_name': u'university.edu',
                                u'mail_server': u'mail2.university.edu.'},
                            {'target': u'@',
                             'ttl': 3600,
                             u'priority': 1,
                             'record_type': u'mx',
                             'view_name': u'any',
                             'last_user': u'sharrell',
                             'zone_name': u'university.edu',
                             u'mail_server': u'mail1.university.edu.'},
                            {'target': u'@',
                             u'name_server': u'ns2.university.edu',
                             'ttl': 3600,
                             'record_type': u'ns',
                             'view_name': u'any',
                             'last_user': u'sharrell',
                             'zone_name': u'university.edu'},
                            {'target': u'@',
                             u'name_server': u'ns1.university.edu',
                             'ttl': 3600,
                             'record_type': u'ns',
                             'view_name': u'any',
                             'last_user': u'sharrell',
                             'zone_name': u'university.edu'},
                            {'serial_number': 20091227,
                             u'refresh_seconds': 5,
                             'target': u'university.edu.',
                             u'name_server': u'ns1.university.edu.',
                             u'retry_seconds': 5,
                             'ttl': 3600,
                             u'minimum_seconds': 5,
                             'record_type': u'soa',
                             'view_name': u'external',
                             'last_user': u'sharrell',
                             'zone_name': u'university.edu',
                             u'admin_email': u'admin@university.edu.',
                             u'expiry_seconds': 5},
                            {'target':u'computer1',
                             'ttl':3600,
                             'record_type':u'a',
                             'view_name':u'external',
                             'last_user':u'sharrell',
                             'zone_name':u'university.edu',
                             u'assignment_ip':u'1.2.3.5'},
                            {'target':u'computer3',
                             'ttl':3600,
                             'record_type':u'a',
                             'view_name':u'external',
                             'last_user':u'sharrell',
                             'zone_name':u'university.edu',
                             u'assignment_ip':u'1.2.3.6'}],
                            'zone_origin': u'university.edu.',
                            'zone_options': u'#Allow update\nallow-update { none; };\n'},
                            u'4.3.2.1.in-addr.arpa':{
                                'zone_type':u'master',
                                'records':[{
                                    u'serial_number':20091224,
                                    u'refresh_seconds':5,
                                    'target':u'4.3.2.1.in-addr.arpa.',
                                    u'name_server':u'ns1.university.edu.',
                                    u'retry_seconds':5,
                                    'ttl':3600,
                                    'minimum_seconds':5,
                                    'record_type':u'soa',
                                    'view_name':u'external',
                                    'last_user':u'sharrell',
                                    'zone_name':u'4.3.2.1.in-addr.arpa',
                                    u'admin_email':u'admin@university.edu.',
                                    u'expiry_seconds':5},
                                {'target':u'1',
                                 'ttl':3600,
                                 'record_type':u'ptr',
                                 'view_name':u'external',
                                 'last_user':u'sharrell',
                                 'zone_name':u'4.3.2.1.in-addr.arpa',
                                 u'assignment_host':u'computer1'}],
                                'zone_origin':u'4.3.2.1.in-addr.arpa.',
                                'zone_options':u'#Allow update\nallow-update { none; };\n'}},
                'acls': [u'public']}}})

    self.assertEqual(cooked_data['private_dns'], {
        'dns_servers': [u'ns1.int.university.edu', u'dns4.university.edu'],
        'views':{
            u'private':{
                'zones':{
                    u'university.edu':{
                        'zone_type': u'master',
                        'records':[{
                            'target': u'@',
                            'ttl': 3600,
                            u'priority': 1,
                            'record_type': u'mx',
                            'view_name': u'any',
                            'last_user': u'sharrell',
                            'zone_name': u'university.edu',
                            u'mail_server': u'mail2.university.edu.'},
                        {'target': u'@',
                         'ttl': 3600,
                         u'priority': 1,
                         'record_type': u'mx',
                         'view_name': u'any',
                         'last_user': u'sharrell',
                         'zone_name': u'university.edu',
                         u'mail_server': u'mail1.university.edu.'},
                        {'target': u'@',
                         u'name_server': u'ns2.university.edu',
                         'ttl': 3600,
                         'record_type': u'ns',
                         'view_name': u'any',
                         'last_user': u'sharrell',
                         'zone_name': u'university.edu'},
                        {'target': u'@',
                         u'name_server': u'ns1.university.edu',
                         'ttl': 3600,
                         'record_type': u'ns',
                         'view_name': u'any',
                         'last_user': u'sharrell',
                         'zone_name': u'university.edu'},
                        {'serial_number': 20091225,
                         u'refresh_seconds': 5,
                         'target': u'university.edu.',
                         u'name_server': u'ns1.university.edu.',
                         u'retry_seconds': 5,
                         'ttl': 3600,
                         u'minimum_seconds': 5,
                         'record_type': u'soa',
                         'view_name': u'private',
                         'last_user': u'sharrell',
                         'zone_name': u'university.edu',
                          u'admin_email': u'admin@university.edu.',
                          u'expiry_seconds': 5}],
                        'zone_origin': u'university.edu.',
                        'zone_options': u'#Allow update\nallow-update { none; };\n'}},
            'acls': [u'secret']}}})

    self.assertEqual(cooked_data['internal_dns'], {
        'dns_servers': [u'ns1.int.university.edu', u'dns1.university.edu'],
        'views':{
            u'external':{
                'acls':[u'public'],
                'zones':{
                    u'4.3.2.1.in-addr.arpa':{
                        'records':[{
                            u'admin_email': u'admin@university.edu.',
                            u'expiry_seconds': 5,
                            'last_user': u'sharrell',
                            u'minimum_seconds': 5,
                            u'name_server': u'ns1.university.edu.',
                            'record_type': u'soa',
                            u'refresh_seconds': 5,
                            u'retry_seconds': 5,
                            u'serial_number': 20091224,
                            'target': u'4.3.2.1.in-addr.arpa.',
                            'ttl': 3600,
                            'view_name': u'external',
                            'zone_name': u'4.3.2.1.in-addr.arpa'},
                        {u'assignment_host': u'computer1',
                         'last_user': u'sharrell',
                         'record_type': u'ptr',
                         'target': u'1',
                         'ttl': 3600,
                         'view_name': u'external',
                         'zone_name': u'4.3.2.1.in-addr.arpa'}],
                        'zone_options': u'#Allow update\nallow-update { none; };\n',
                        'zone_origin': u'4.3.2.1.in-addr.arpa.',
                        'zone_type': u'master'},
                    u'university.edu':{
                        'records':[{
                            'last_user': u'sharrell',
                            u'mail_server': u'mail2.university.edu.',
                            u'priority': 1,
                            'record_type': u'mx',
                            'target': u'@',
                            'ttl': 3600,
                            'view_name': u'any',
                            'zone_name': u'university.edu'},
                        { 'last_user': u'sharrell',
                            u'mail_server': u'mail1.university.edu.',
                            u'priority': 1,
                            'record_type': u'mx',
                            'target': u'@',
                            'ttl': 3600,
                            'view_name': u'any',
                            'zone_name': u'university.edu'},
                        { 'last_user': u'sharrell',
                            u'name_server': u'ns2.university.edu',
                            'record_type': u'ns',
                            'target': u'@',
                            'ttl': 3600,
                            'view_name': u'any',
                            'zone_name': u'university.edu'},
                        { 'last_user': u'sharrell',
                            u'name_server': u'ns1.university.edu',
                            'record_type': u'ns',
                            'target': u'@',
                            'ttl': 3600,
                            'view_name': u'any',
                            'zone_name': u'university.edu'},
                        { u'admin_email': u'admin@university.edu.',
                            u'expiry_seconds': 5,
                            'last_user': u'sharrell',
                            u'minimum_seconds': 5,
                            u'name_server': u'ns1.university.edu.',
                            'record_type': u'soa',
                            u'refresh_seconds': 5,
                            u'retry_seconds': 5,
                            u'serial_number': 20091227,
                            'target': u'university.edu.',
                            'ttl': 3600,
                            'view_name': u'external',
                            'zone_name': u'university.edu'},
                        { u'assignment_ip': u'1.2.3.5',
                            'last_user': u'sharrell',
                            'record_type': u'a',
                            'target': u'computer1',
                            'ttl': 3600,
                            'view_name': u'external',
                            'zone_name': u'university.edu'},
                        { u'assignment_ip': u'1.2.3.6',
                            'last_user': u'sharrell',
                            'record_type': u'a',
                            'target': u'computer3',
                            'ttl': 3600,
                            'view_name': u'external',
                            'zone_name': u'university.edu'}],
                    'zone_options': u'#Allow update\nallow-update { none; };\n',
                    'zone_origin': u'university.edu.',
                    'zone_type': u'master'}}},
            u'internal': { 'acls': [u'public', u'secret'],
            'zones':{
                u'168.192.in-addr.arpa':{
                    'records':[{
                        u'assignment_host': u'computer4',
                        'last_user': u'sharrell',
                        'record_type': u'ptr',
                        'target': u'4',
                        'ttl': 3600,
                        'view_name': u'internal',
                        'zone_name': u'168.192.in-addr.arpa'},
                        {u'admin_email': u'admin@university.edu.',
                         u'expiry_seconds': 5,
                         'last_user': u'sharrell',
                         u'minimum_seconds': 5,
                         u'name_server': u'ns1.university.edu.',
                         'record_type': u'soa',
                         u'refresh_seconds': 5,
                         u'retry_seconds': 5,
                         u'serial_number': 20091223,
                         'target': u'168.192.in-addr.arpa.',
                         'ttl': 3600,
                         'view_name': u'internal',
                         'zone_name': u'168.192.in-addr.arpa'}],
                    'zone_options': u'#Allow update\nallow-update { none; };\n',
                    'zone_origin': u'168.192.in-addr.arpa.',
                    'zone_type': u'master'},
                u'university.edu':{
                    'records':[{
                        'last_user': u'sharrell',
                        u'mail_server': u'mail2.university.edu.',
                        u'priority': 1,
                        'record_type': u'mx',
                        'target': u'@',
                        'ttl': 3600,
                        'view_name': u'any',
                        'zone_name': u'university.edu'},
                        {'last_user': u'sharrell',
                         u'mail_server': u'mail1.university.edu.',
                         u'priority': 1,
                         'record_type': u'mx',
                         'target': u'@',
                         'ttl': 3600,
                         'view_name': u'any',
                         'zone_name': u'university.edu'},
                        {'last_user': u'sharrell',
                         u'name_server': u'ns2.university.edu',
                         'record_type': u'ns',
                         'target': u'@',
                         'ttl': 3600,
                         'view_name': u'any',
                         'zone_name': u'university.edu'},
                        {'last_user': u'sharrell',
                         u'name_server': u'ns1.university.edu',
                         'record_type': u'ns',
                         'target': u'@',
                         'ttl': 3600,
                         'view_name': u'any',
                         'zone_name': u'university.edu'},
                        {u'assignment_ip': u'192.168.1.4',
                         'last_user': u'sharrell',
                         'record_type': u'a',
                         'target': u'computer4',
                         'ttl': 3600,
                         'view_name': u'internal',
                         'zone_name': u'university.edu'},
                        {u'admin_email': u'admin@university.edu.',
                         u'expiry_seconds': 5,
                         'last_user': u'sharrell',
                         u'minimum_seconds': 5,
                         u'name_server': u'ns1.university.edu.',
                         'record_type': u'soa',
                         u'refresh_seconds': 5,
                         u'retry_seconds': 5,
                         u'serial_number': 20091225,
                         'target': u'university.edu.',
                         'ttl': 3600,
                         'view_name': u'internal',
                         'zone_name': u'university.edu'},
                        {u'assignment_ip': u'192.168.1.1',
                         'last_user': u'sharrell',
                         'record_type': u'a',
                         'target': u'computer1',
                         'ttl': 3600,
                         'view_name': u'internal',
                         'zone_name': u'university.edu'},
                        {u'assignment_ip': u'192.168.1.2',
                         'last_user': u'sharrell',
                         'record_type': u'a',
                         'target': u'computer2',
                         'ttl': 3600,
                         'view_name': u'internal',
                         'zone_name': u'university.edu'}],
                    'zone_options': u'#Allow update\nallow-update { none; };\n',
                    'zone_origin': u'university.edu.',
                    'zone_type': u'master'}}}}})

  def testTreeExporterListACLNamesByView(self):
    acl_names_private = self.tree_exporter_instance.ListACLNamesByView(
        self.data[0], u'private')
    self.assertEqual(
        acl_names_private, [u'secret'])
    acl_names_internal = self.tree_exporter_instance.ListACLNamesByView(
        self.data[0], u'internal')
    self.assertEqual(
        acl_names_internal, [u'public', u'secret'])
    acl_names_external = self.tree_exporter_instance.ListACLNamesByView(
        self.data[0], u'external')
    self.assertEqual(
        acl_names_external, [u'public'])

  def testSignZone(self):
    self.dnssec_tree_exporter_instance = tree_exporter.BindTreeExport(
        CONFIG_FILE, dnssec=True, kskfile=KSKFILE, zskfile=ZSKFILE,
        dnssec_signzone_exec=DNSSEC_SIGNZONE_EXEC)
    signed_zone_file_lines = []
    zone_file_string = open(ZONE_FILE).read()
    self.assertEqual(len(zone_file_string.split('\n')), 28)
    signed_zone_file_string = self.dnssec_tree_exporter_instance.SignZone(
        zone_file_string, 'sub.university.edu')
    self.assertEqual(len(signed_zone_file_string.split('\n')), 260)

  def testTreeExporterExpportAllBindTreesDnssec(self):
    self.dnssec_tree_exporter_instance = tree_exporter.BindTreeExport(
        CONFIG_FILE, dnssec=True, dnssec_keygen_exec=DNSSEC_KEYGEN_EXEC,
        dnssec_signzone_exec=DNSSEC_SIGNZONE_EXEC, random=RANDOM)
    self.tree_exporter_instance = self.dnssec_tree_exporter_instance
    self.core_instance.SetMaintenanceFlag(1)
    self.assertRaises(tree_exporter.MaintenanceError,
        self.tree_exporter_instance.ExportAllBindTrees)
    self.core_instance.SetMaintenanceFlag(0)
    self.tree_exporter_instance.ExportAllBindTrees()
      
    tar_file = tarfile.open(self.tree_exporter_instance.tar_file_name)
    tar_file.extractall()
    tar_file.close()

    handle = open(
        '%s/external_dns_servers/named/external_dns_config' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                     'dns_servers = ns1.university.edu,dns2.university.edu,'
                     'dns3.university.edu\n'
                     'dns_server_set_name = external_dns\n\n')
    handle.close()
    handle = open('%s/external_dns_servers/named.conf' % self.bind_config_dir,
                  'r')
    self.assertEqual(handle.read(),
                     '#This named.conf file is autogenerated. DO NOT EDIT\n'
                     'options {\n'
                     '\tdirectory "%s/named";\n'
                     '\trecursion no;\n'
                     '\tmax-cache-size 512M;\n'
                     '};\n\n'
                     'logging {\n'
                     '\tchannel "security" {\n'
                     '\t\tfile "/var/log/named-security.log" versions 10 size '
                     '10m;\n'
                     '\t\tprint-time yes;\n'
                     '\t};\n'
                     '\tchannel "query_logging" {\n'
                     '\t\tsyslog local5;\n'
                     '\t\tseverity info;\n'
                     '\t};\n'
                     '\tcategory "client" { "null"; };\n'
                     '\tcategory "update-security" { "security"; };\n'
                     '\tcategory "queries" { "query_logging"; };\n'
                     '};\n\n'
                     'controls {\n'
                     '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
                     '};\n\n'
                     'include "/etc/rndc.key";\n\n'
                     'acl secret {\n'
                     '\t!10.10/32;\n'
                     '};\n\n'
                     'acl public {\n'
                     '\t10.10/32;\n'
                     '\t192.168.1.4/30;\n'
                     '};\n\n'
                     'view "external" {\n'
                     '\tmatch-clients { public; };\n'
                     '\tzone "university.edu" {\n'
                     '\t\ttype master;\n'
                     '\t\tfile "%s/named/external/university.edu.db";\n'
                     '\t\t#Allow update\n'
                     '\t\tallow-update { none; };\n'
                     '\t};\n'
                     '\tzone "4.3.2.1.in-addr.arpa" {\n'
                     '\t\ttype master;\n'
                     '\t\tfile "%s/named/external/4.3.2.1.in-addr.arpa.db";\n'
                     '\t\t#Allow update\n'
                     '\t\tallow-update { none; };\n'
                     '\t};\n'
                     '};' % tuple(
                          [self.named_dir.rstrip('/') for x in range(3)]))
    handle.close()
    handle = open(
        '%s/external_dns_servers/named/external/4.3.2.1.in-addr.arpa.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(len(handle.read().split()), 227)
    handle.close()
    handle = open(
        '%s/external_dns_servers/named/external/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(len(handle.read().split()), 322)
    handle.close()
    handle = open('%s/internal_dns_servers/named/internal_dns_config' %
                  self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                                    'dns_servers = ns1.int.university.edu,'
                                    'dns1.university.edu\n'
                                    'dns_server_set_name = internal_dns\n\n')
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named.conf' % self.bind_config_dir,
        'r')
    self.assertEqual(
        handle.read(), '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'options {\n'
        '\tdirectory "%s/named";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n\n'
        'acl secret {\n'
        '\t!10.10/32;\n'
        '};\n\n'
        'acl public {\n'
        '\t10.10/32;\n'
        '\t192.168.1.4/30;\n'
        '};\n\n'
        'view "internal" {\n'
        '\tmatch-clients { public; secret; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "168.192.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/168.192.in-addr.arpa.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "external" {\n'
        '\tmatch-clients { public; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.1.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/4.3.2.1.in-addr.arpa.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tuple([self.named_dir.rstrip('/') for x in range(5)]))
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named/external/4.3.2.1.in-addr.arpa.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(len(handle.read().split()), 227)
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named/external/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(len(handle.read().split()), 322)
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named/internal/168.192.in-addr.arpa.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(len(handle.read().split()), 227)
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named/internal/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(len(handle.read().split()), 367)
    handle.close()
    handle = open(
        '%s/private_dns_servers/named/private_dns_config' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                                    'dns_servers = ns1.int.university.edu,'
                                    'dns4.university.edu\n'
                                    'dns_server_set_name = private_dns\n\n')
    handle.close()
    handle = open('%s/private_dns_servers/named.conf' % self.bind_config_dir,
                  'r')
    self.assertEqual(
        handle.read(), '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'options {\n'
        '\tdirectory "%s/named";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n\n'
        'acl secret {\n'
        '\t!10.10/32;\n'
        '};\n\n'
        'acl public {\n'
        '\t10.10/32;\n'
        '\t192.168.1.4/30;\n'
        '};\n\n'
        'view "private" {\n'
        '\tmatch-clients { secret; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/private/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tuple([self.named_dir.rstrip('/') for x in range(2)]))
    handle.close()
    handle = open(
        '%s/private_dns_servers/named/private/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(len(handle.read().split()), 232)
    handle.close()

  def testTreeExporterListLatestNamedConfGlobalOptions(self):
    global_options_internal = (
        self.tree_exporter_instance.ListLatestNamedConfGlobalOptions(
            self.data[0], u'internal_dns'))
    self.assertEqual(
        global_options_internal, (
            u'options {\n'
            '\tdirectory "/var/domain";\n'
            '\trecursion no;\n'
            '\tmax-cache-size 512M;\n'
            '};\n'
            '\nlogging {\n'
            '\tchannel "security" {\n'
            '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
            '\t\tprint-time yes;\n'
            '\t};\n'
            '\tchannel "query_logging" {\n'
            '\t\tsyslog local5;\n'
            '\t\tseverity info;\n'
            '\t};\n'
            '\tcategory "client" { "null"; };\n'
            '\tcategory "update-security" { "security"; };\n'
            '\tcategory "queries" { "query_logging"; };\n'
            '};\n\n'
            'controls {\n'
            '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
            '};\n\n'
            'include "/etc/rndc.key";\n'))
    global_options_external = (
        self.tree_exporter_instance.ListLatestNamedConfGlobalOptions(
            self.data[0], u'external_dns'))
    self.assertEqual(
        global_options_external, (
            u'options {\n'
            '\tdirectory "/var/domain";\n'
            '\trecursion no;\n'
            '\tmax-cache-size 512M;\n'
            '};\n\n'
            'logging {\n'
            '\tchannel "security" {\n'
            '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
            '\t\tprint-time yes;\n'
            '\t};\n'
            '\tchannel "query_logging" {\n'
            '\t\tsyslog local5;\n'
            '\t\tseverity info;\n'
            '\t};\n'
            '\tcategory "client" { "null"; };\n'
            '\tcategory "update-security" { "security"; };\n'
            '\tcategory "queries" { "query_logging"; };\n'
            '};\n\n'
            'controls {\n'
            '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
            '};\n\n'
            'include "/etc/rndc.key";\n'))
    global_options_private = (
        self.tree_exporter_instance.ListLatestNamedConfGlobalOptions(
            self.data[0], u'private_dns'))
    self.assertEqual(
        global_options_private, (
            u'options {\n'
            '\tdirectory "/var/domain";\n'
            '\trecursion no;\n'
            '\tmax-cache-size 512M;\n'
            '};\n\n'
            'logging {\n'
            '\tchannel "security" {\n'
            '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
            '\t\tprint-time yes;\n'
            '\t};\n'
            '\tchannel "query_logging" {\n'
            '\t\tsyslog local5;\n'
            '\t\tseverity info;\n'
            '\t};\n'
            '\tcategory "client" { "null"; };\n'
            '\tcategory "update-security" { "security"; };\n'
            '\tcategory "queries" { "query_logging"; };\n'
            '};\n\n'
            'controls {\n'
            '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
            '};\n\n'
            'include "/etc/rndc.key";\n'))

  def testTreeExporterExpportAllBindTrees(self):
    self.core_instance.SetMaintenanceFlag(1)
    self.assertRaises(tree_exporter.MaintenanceError,
        self.tree_exporter_instance.ExportAllBindTrees)
    self.core_instance.SetMaintenanceFlag(0)
    self.tree_exporter_instance.ExportAllBindTrees()
      
    tar_file = tarfile.open(self.tree_exporter_instance.tar_file_name)
    tar_file.extractall()
    tar_file.close()

    handle = open(
        '%s/external_dns_servers/named/external_dns_config' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                     'dns_servers = ns1.university.edu,dns2.university.edu,'
                     'dns3.university.edu\n'
                     'dns_server_set_name = external_dns\n\n')
    handle.close()
    handle = open('%s/external_dns_servers/named.conf' % self.bind_config_dir,
                  'r')
    self.assertEqual(handle.read(),
                     '#This named.conf file is autogenerated. DO NOT EDIT\n'
                     'options {\n'
                     '\tdirectory "%s/named";\n'
                     '\trecursion no;\n'
                     '\tmax-cache-size 512M;\n'
                     '};\n\n'
                     'logging {\n'
                     '\tchannel "security" {\n'
                     '\t\tfile "/var/log/named-security.log" versions 10 size '
                     '10m;\n'
                     '\t\tprint-time yes;\n'
                     '\t};\n'
                     '\tchannel "query_logging" {\n'
                     '\t\tsyslog local5;\n'
                     '\t\tseverity info;\n'
                     '\t};\n'
                     '\tcategory "client" { "null"; };\n'
                     '\tcategory "update-security" { "security"; };\n'
                     '\tcategory "queries" { "query_logging"; };\n'
                     '};\n\n'
                     'controls {\n'
                     '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
                     '};\n\n'
                     'include "/etc/rndc.key";\n\n'
                     'acl secret {\n'
                     '\t!10.10/32;\n'
                     '};\n\n'
                     'acl public {\n'
                     '\t10.10/32;\n'
                     '\t192.168.1.4/30;\n'
                     '};\n\n'
                     'view "external" {\n'
                     '\tmatch-clients { public; };\n'
                     '\tzone "university.edu" {\n'
                     '\t\ttype master;\n'
                     '\t\tfile "%s/named/external/university.edu.db";\n'
                     '\t\t#Allow update\n'
                     '\t\tallow-update { none; };\n'
                     '\t};\n'
                     '\tzone "4.3.2.1.in-addr.arpa" {\n'
                     '\t\ttype master;\n'
                     '\t\tfile "%s/named/external/4.3.2.1.in-addr.arpa.db";\n'
                     '\t\t#Allow update\n'
                     '\t\tallow-update { none; };\n'
                     '\t};\n'
                     '};' % tuple(
                          [self.named_dir.rstrip('/') for x in range(3)]))
    handle.close()
    handle = open(
        '%s/external_dns_servers/named/external/4.3.2.1.in-addr.arpa.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(),
                     '; This zone file is autogenerated. DO NOT EDIT.\n'
                     '$ORIGIN 4.3.2.1.in-addr.arpa.\n'
                     '4.3.2.1.in-addr.arpa. 3600 in soa ns1.university.edu. '
                     'admin@university.edu. 20091224 5 5 5 5\n'
                     '1 3600 in ptr computer1\n')
    handle.close()
    handle = open(
        '%s/external_dns_servers/named/external/university.edu.db' %
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
    handle = open('%s/internal_dns_servers/named/internal_dns_config' %
                  self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                                    'dns_servers = ns1.int.university.edu,'
                                    'dns1.university.edu\n'
                                    'dns_server_set_name = internal_dns\n\n')
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named.conf' % self.bind_config_dir,
        'r')
    self.assertEqual(
        handle.read(), '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'options {\n'
        '\tdirectory "%s/named";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n\n'
        'acl secret {\n'
        '\t!10.10/32;\n'
        '};\n\n'
        'acl public {\n'
        '\t10.10/32;\n'
        '\t192.168.1.4/30;\n'
        '};\n\n'
        'view "internal" {\n'
        '\tmatch-clients { public; secret; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "168.192.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/internal/168.192.in-addr.arpa.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};\n'
        'view "external" {\n'
        '\tmatch-clients { public; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '\tzone "4.3.2.1.in-addr.arpa" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/external/4.3.2.1.in-addr.arpa.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tuple([self.named_dir.rstrip('/') for x in range(5)]))
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named/external/4.3.2.1.in-addr.arpa.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN 4.3.2.1.in-addr.arpa.\n'
        '4.3.2.1.in-addr.arpa. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091224 5 5 5 5\n'
        '1 3600 in ptr computer1\n')
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named/external/university.edu.db' %
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
        '%s/internal_dns_servers/named/internal/168.192.in-addr.arpa.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN 168.192.in-addr.arpa.\n'
        '168.192.in-addr.arpa. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091223 5 5 5 5\n'
        '4 3600 in ptr computer4\n')
    handle.close()
    handle = open(
        '%s/internal_dns_servers/named/internal/university.edu.db' %
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
        '%s/private_dns_servers/named/private_dns_config' %
        self.bind_config_dir, 'r')
    self.assertEqual(handle.read(), '[dns_server_set_parameters]\n'
                                    'dns_servers = ns1.int.university.edu,'
                                    'dns4.university.edu\n'
                                    'dns_server_set_name = private_dns\n\n')
    handle.close()
    handle = open('%s/private_dns_servers/named.conf' % self.bind_config_dir,
                  'r')
    self.assertEqual(
        handle.read(), '#This named.conf file is autogenerated. DO NOT EDIT\n'
        'options {\n'
        '\tdirectory "%s/named";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n\n'
        'acl secret {\n'
        '\t!10.10/32;\n'
        '};\n\n'
        'acl public {\n'
        '\t10.10/32;\n'
        '\t192.168.1.4/30;\n'
        '};\n\n'
        'view "private" {\n'
        '\tmatch-clients { secret; };\n'
        '\tzone "university.edu" {\n'
        '\t\ttype master;\n'
        '\t\tfile "%s/named/private/university.edu.db";\n'
        '\t\t#Allow update\n'
        '\t\tallow-update { none; };\n'
        '\t};\n'
        '};' % tuple([self.named_dir.rstrip('/') for x in range(2)]))
    handle.close()
    handle = open(
        '%s/private_dns_servers/named/private/university.edu.db' %
        self.bind_config_dir, 'r')
    self.assertEqual(
        handle.read(), '; This zone file is autogenerated. DO NOT EDIT.\n'
        '$ORIGIN university.edu.\n'
        'university.edu. 3600 in soa ns1.university.edu. '
        'admin@university.edu. 20091225 5 5 5 5\n'
        '@ 3600 in ns ns1.university.edu\n'
        '@ 3600 in ns ns2.university.edu\n'
        '@ 3600 in mx 1 mail2.university.edu.\n'
        '@ 3600 in mx 1 mail1.university.edu.\n')
    handle.close()

  def testTreeExporterAddToTarFile(self):
    tar_string = (  ## The string was arbitrarily chosen.
        u'options {\n'
        '\tdirectory "/var/domain";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n')

    if not (os.path.exists(self.bind_config_dir)):
        os.mkdir(self.bind_config_dir)
    temp_tar_filename = '%s/temp_file.tar.bz2' % self.bind_config_dir
    tar_file = tarfile.open(temp_tar_filename, 'w:bz2')
    self.tree_exporter_instance.AddToTarFile(tar_file, 'tar_string', tar_string)
    tar_file.close()

    tar_file = tarfile.open(temp_tar_filename, 'r:bz2')
    tar_file.extractall(self.bind_config_dir)
    tar_file.close()

    handle = open('%s/tar_string' % self.bind_config_dir , 'r')
    extracted_tar_string = handle.read()
    handle.close()

    self.assertEqual(extracted_tar_string, tar_string)

  def testNamedHeaderChangeDirectory(self):
    header_string = (  ## The string was arbitrarily chosen.
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff\n'
        '}\n'
        'options {\n'
        '\tdirectory "/var/domain";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n')
    self.assertEqual(self.tree_exporter_instance.NamedHeaderChangeDirectory(
        header_string, '/tmp/newdir'),
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff\n'
        '}\n'
        'options {\n'
        '\tdirectory "/tmp/newdir";\n'
        '\trecursion no;\n'
        '\tmax-cache-size 512M;\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n')
    header_string = (  ## The string was arbitrarily chosen.
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff\n'
        '}\n' # No options stanza
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n')
    self.assertEqual(self.tree_exporter_instance.NamedHeaderChangeDirectory(
        header_string, '/tmp/newdir'),
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff\n'
        '}\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n'
        'options\n{\n'
        '\tdirectory "/tmp/newdir";\n'
        '};\n\n') # Added at end
    header_string = (  ## The string was arbitrarily chosen.
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff\n'
        '}\n'
        'options {\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n')
    self.assertEqual(self.tree_exporter_instance.NamedHeaderChangeDirectory(
        header_string, '/tmp/newdir'),
        '#Comment1\n'
        '//options\n'
        '//{\n'
        '//directory "test";\n'
        '//};\n'
        '/*\n'
        'options\n'
        '{\n'
        '  directory "test";\n'
        '}\n'
        '*/\n'
        'otherstanza{\n'
        '\tstuff\n'
        '}\n'
        'options {\n'
        '\tdirectory "/tmp/newdir";\n'
        '};\n\n'
        'logging {\n'
        '\tchannel "security" {\n'
        '\t\tfile "/var/log/named-security.log" versions 10 size 10m;\n'
        '\t\tprint-time yes;\n'
        '\t};\n'
        '\tchannel "query_logging" {\n'
        '\t\tsyslog local5;\n'
        '\t\tseverity info;\n'
        '\t};\n'
        '\tcategory "client" { "null"; };\n'
        '\tcategory "update-security" { "security"; };\n'
        '\tcategory "queries" { "query_logging"; };\n'
        '};\n\n'
        'controls {\n'
        '\tinet * allow { control-hosts; } keys {rndc-key; };\n'
        '};\n\n'
        'include "/etc/rndc.key";\n')


if( __name__ == '__main__' ):
  unittest.main()
