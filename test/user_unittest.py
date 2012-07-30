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

"""Unittest for user.py

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2009, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import unittest

import roster_core
from roster_core import audit_log
from roster_core import db_access
from roster_core import user
from roster_core import errors


CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
DATA_FILE = 'test_data/test_data.sql'


class TestUser(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    self.db_instance = self.config_instance.GetDb()

    schema = roster_core.embedded_files.SCHEMA_FILE
    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(schema)
    self.db_instance.EndTransaction()

    data = open(DATA_FILE, 'r').read()
    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(data)
    self.db_instance.EndTransaction()

    self.log_instance = audit_log.AuditLog(log_to_syslog=True)
    self.core_instance = roster_core.Core(u'sharrell', self.config_instance)

  def testInit(self):
    user.User(u'jcollins', self.db_instance, self.log_instance)
    self.assertRaises(errors.UserError, user.User, u'not_valid_user',
                      self.db_instance, self.log_instance)

  def testAuthorize(self):
    self.core_instance.MakeZone(u'192.168.0.rev', u'master',
                                u'0.168.192.IN-ADDR.ARPA.')
    self.core_instance.MakeZone(u'192.168.1.rev', u'master',
                                u'1.168.192.IN-ADDR.ARPA.')
    self.core_instance.MakeZone(u'10.10.rev', u'master',
                                u'10.10.IN-ADDR.ARPA.')
    self.core_instance.MakeReverseRangeZoneAssignment(u'10.10.rev', u'10.10/16')
    self.core_instance.MakeReverseRangePermission(u'10.10.5/24', u'cs', 
                                                  [u'ptr', u'cname'])
    self.core_instance.MakeUserGroupAssignment(u'jcollins', u'cs')

    # good forward zone data
    good_record_data = {'target': u'good',
                        'zone_name': u'cs.university.edu',
                        'view_name': u'any',
                        'record_type': u'a',
                        'record_args_dict' : { u'assignment_ip' : u'192.168.0.1' }
                        }

    txt_record_data = {'target': u'good',
                        'zone_name': u'cs.university.edu',
                        'view_name': u'any',
                        'record_type': u'txt',
                        'record_args_dict' : { u'quoted_text' : u'Hello World' }
                        }


    mx_record_data = {'target': u'good',
                      'zone_name': u'cs.university.edu',
                      'view_name': u'any',
                      'record_type': u'mx',
                      'record_args_dict' : { u'mail_server' : u'192.168.0.1' }
                      }

    # bad forward zone data
    bad_forward_record_data = {'target': u'good',
                          'zone_name': u'bio.university.edu',
                          'view_name': u'any',
                          'record_type': u'a',
                          'record_args_dict' : { 
                              u'assignment_ip' : u'173.194.75.99'}
                          }

    no_forward_record_data = {'target': u'noforward',
                              'zone_name': u'bio.university.edu',
                              'view_name': u'any',
                              'record_type': u'a',
                              'record_args_dict' : { 
                                  u'assignment_ip' : u'192.168.0.1'}
                              }

    # good reverse zone data
    good_reverse_record_data = {'target': u'5.5',
                                'zone_name': u'10.10.rev',
                                'view_name': u'any',
                                'record_type': u'ptr',
                                'record_args_dict' : { 
                                    u'assignment_host' : u'hello.cs.university.edu.'
                                    }
                                }

    no_record_args_dict_data = {'target': u'good',
                                'zone_name': u'cs.university.edu',
                                'view_name': u'any',
                                'record_type': u'a'}

    bad_reverse_record_data = {'target': u'1',
                               'zone_name': u'192.168.0.rev',
                               'view_name': u'any',
                               'record_type': u'ptr',
                               'record_args_dict' : { 
                                   u'assignment_host' : u'c1.google.com.'}
                               }
    # bad reverse zone data
    no_reverse_record_data = {'target': u'1',
                              'zone_name': u'192.168.1.rev',
                              'view_name': u'any',
                              'record_type': u'ptr',
                              'record_args_dict' : { 
                                  u'assignment_host' : u'john.cs.university.edu.'}
                              }

    # good reverse zone data (subset of ip range in bigger zone)
    good_10_reverse_record_data = {'target': u'10.5',
                                   'zone_name': u'10.10.rev',
                                   'view_name': u'any',
                                   'record_type': u'ptr',
                                   'record_args_dict' : { 
                                     u'assignment_host' : u'good.cs.university.edu.'
                                     }
                                   }

    # bad reverse zone data (subset of ip range in bigger zone)
    no_10_reverse_record_data = {'target': u'10.4',
                                 'zone_name': u'10.10.rev',
                                 'view_name': u'any',
                                 'record_type': u'ptr',
                                 'record_args_dict' : { 
                                     u'assignment_host' : u'bad.cs.university.edu.' }
                                 }

    # test success with admin user
    user_instance = user.User(u'sharrell', self.db_instance, self.log_instance)
    user_instance.Authorize(u'MakeView')
    user_instance.Authorize(u'MakeRecord', good_record_data)
    user_instance.Authorize(u'MakeRecord', txt_record_data)
    user_instance.Authorize(u'MakeRecord', mx_record_data)
    user_instance.Authorize(u'MakeRecord', bad_reverse_record_data)

    # test maintenance mode
    # maintainenance flag doesn't apply to admins
    user_instance.Authorize(u'MakeView')
    # it does apply to users tho
    user_instance = user.User(u'jcollins', self.db_instance, self.log_instance)
    user_instance.Authorize(u'MakeRecord', good_record_data)
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize,
                      u'MakeRecord', txt_record_data)
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize,
                      u'MakeRecord', mx_record_data)

    self.core_instance.SetMaintenanceFlag(True)
    self.assertRaises(errors.MaintenanceError, user_instance.Authorize,
                      u'MakeRecord', good_record_data)
    self.assertRaises(errors.MaintenanceError, user_instance.Authorize,
                      u'MakeRecord', mx_record_data)
    self.core_instance.SetMaintenanceFlag(False)

    # test missing record_data on certain methods, and make sure it passes
    # on the others
    user_instance.Authorize(u'MakeRecord', good_record_data)
    self.assertRaises(errors.MissingDataTypeError, user_instance.Authorize, u'MakeRecord')

    # test record_data dict to make sure all the keys and data are there
    user_instance.Authorize(u'MakeRecord', good_record_data)
    good_record_data['target'] = None
    self.assertRaises(errors.MissingDataTypeError, user_instance.Authorize, u'MakeRecord',
                      good_record_data)
    good_record_data['target'] = u'good'
    user_instance.Authorize(u'MakeRecord', good_record_data)
    del good_record_data['zone_name']
    self.assertRaises(errors.MissingDataTypeError, user_instance.Authorize, u'MakeRecord',
                      good_record_data)
    good_record_data['zone_name'] = u'cs.university.edu'

    # test no forward zone found
    user_instance.Authorize(u'MakeRecord', good_record_data)
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize, u'MakeRecord',
                      no_forward_record_data)

    # test no reverse range found
    user_instance.Authorize(u'MakeRecord', good_reverse_record_data)
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize, u'MakeRecord',
                      no_reverse_record_data)
    user_instance.Authorize(u'MakeRecord', good_10_reverse_record_data)
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize, u'MakeRecord',
                      no_10_reverse_record_data)

    # test no method found
    user_instance.Authorize(u'MakeRecord', good_reverse_record_data)
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize, u'FakeRecord',
                      good_reverse_record_data)

    # test bad record_args_dict, i.e. assignment_ip/hosts that are not in a roster zone
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize, u'MakeRecord',
                      bad_forward_record_data)
    self.assertRaises(errors.AuthorizationError, user_instance.Authorize, u'MakeRecord',
                      bad_reverse_record_data)

    # check to make sure Authorize only accepts record_data with a record_args_dict
    self.assertRaises(errors.MissingDataTypeError, user_instance.Authorize, u'MakeRecord',
                      no_record_args_dict_data)

  def testGetUserName(self):
    user_instance = user.User(u'jcollins', self.db_instance, self.log_instance)
    self.assertEquals(user_instance.GetUserName(), 'jcollins')

  def testGetPermissions(self):
    user_instance = user.User(u'jcollins', self.db_instance, self.log_instance)
    self.assertEquals(user_instance.GetPermissions(),
                      {'user_access_level': 32, 'user_name': u'jcollins',
                       'forward_zones': [], 'groups': [], 'reverse_ranges': []})


if( __name__ == '__main__' ):
    unittest.main()
