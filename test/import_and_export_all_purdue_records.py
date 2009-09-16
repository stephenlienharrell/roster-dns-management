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

"""Regression test for zone_exporter_lib.py

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import dns.zone
import dns.rdatatype
from dns.exception import DNSException
import os
import time
import threading
import unittest

from roster_config_manager import zone_exporter_lib
from roster_config_manager import zone_importer_lib

import roster_core
from roster_core import db_access


ZONE_DIRECTORY = 'test_data/university.edu' # This directory will not be checked in
                                        # for security considerations.
CONFIG_FILE = os.path.expanduser('~/.rosterrc') # Example in test_data
SCHEMA_FILE = '../db/database_schema.sql'
DATA_FILE = '../db/test_data.sql'
TEMP_DIRECTORY = 'temp_data'
MAIN_USER = u'sharrell'


class ImportRecords(threading.Thread):
  def __init__(self, zone_file):
    threading.Thread.__init__(self)
    self.zone_file = zone_file
    self.record_count = 0
    self.done = False

  def run(self):
    importer_instance = zone_importer_lib.ZoneImport(self.zone_file,
                                                            CONFIG_FILE,
                                                            MAIN_USER,
                                                            u'external')

    self.record_count += importer_instance.MakeRecordsFromZone()
    self.zone = importer_instance.zone
    self.done = True


class TestZoneExport(unittest.TestCase):

  def setUp(self):
    config_instance = roster_core.Config(file_name=CONFIG_FILE)
    db_instance = config_instance.GetDb()

    schema = open(SCHEMA_FILE, 'r').read()
    db_instance.StartTransaction()
    db_instance.cursor.execute(schema)
    db_instance.CommitTransaction()

    db_instance.StartTransaction()
    db_instance.cursor.execute("INSERT INTO users (user_name, access_level) "
                               "VALUES ('%s', 128)" % MAIN_USER)
    db_instance.CommitTransaction()

    self.core_instance = roster_core.Core(MAIN_USER, config_instance)
    os.mkdir(TEMP_DIRECTORY)

  def tearDown(self):
    for zone_file in os.listdir(TEMP_DIRECTORY):
      zone_file = os.path.join(TEMP_DIRECTORY, zone_file)
      os.remove(zone_file)
    os.rmdir(TEMP_DIRECTORY)

  def testGetRecordsForZone(self):
    import_start_time = time.time()
    zone_file_list = os.listdir(ZONE_DIRECTORY)
    thread_list = []
    zone_list = []
    record_count = 0

    for zone_file in zone_file_list:
      zone_file = os.path.join(ZONE_DIRECTORY, zone_file)
      if( not os.path.isdir(zone_file) ):
        current_import_thread = ImportRecords(zone_file)
        thread_list.append(current_import_thread)
        current_import_thread.start()
        time.sleep(1)

    while True:
      time.sleep(2)
      for thread in thread_list:
        thread.join(1)
        if( not thread.isAlive() ):
          thread_list.remove(thread)
        if( thread.done ):
          zone_list.append(thread.zone)
          record_count += thread.record_count
      if( not len(thread_list) ):
        break

    print "import of all %s records took %s seconds" % (record_count, 
                                                        time.time() -
                                                        import_start_time)

    all_records = self.core_instance.ListRecords()
    unique = []
    for record in all_records:
      if record not in unique:
        unique.append(record)
      else:
        print "dupe found: record"


    export_start_time = time.time()
    zones = self.core_instance.ListZones(view_name=u'external')
    for zone in zones.keys():
      exporter_instance = zone_exporter_lib.ZoneExport(
          zone, MAIN_USER, CONFIG_FILE, u'external')
      zone_export_file = os.path.join(TEMP_DIRECTORY, zone)
      open(zone_export_file, 'w').write(exporter_instance.MakeZoneString())

    print "export of all zones took %s seconds" % (time.time() - 
                                                   export_start_time)

    print "checking output files against originals"
    for zone_file in os.listdir(TEMP_DIRECTORY):
      zone_file = os.path.join(TEMP_DIRECTORY, zone_file)
      if( not os.path.isdir(zone_file) ):
        current_zone = dns.zone.from_file(zone_file)
        if( os.system('/usr/sbin/named-checkzone %s %s' % (current_zone.origin,
                                                           zone_file))):
          raise AssertionError('Zone file %s failed named-checkzone' %
                               zone_file)
        for compare_zone in zone_list:
          if( current_zone.origin == compare_zone.origin ):
            self.assertEqual(current_zone.origin, compare_zone.origin)
            break
        else:
          raise AssertionError('Cannot find zone with origin %s' %
                               current_zone.origin)


if( __name__ == '__main__' ):
  unittest.main()
