#!/usr/bin/python

# Copyright (c) 2010, Purdue University
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

"""Regression test for roster_database_bootstrap

Make sure you are running this against a database that can be destroyed.

DO NOT EVER RUN THIS TEST AGAINST A PRODUCTION DATABASE.
"""

__copyright__ = 'Copyright (C) 2010, Purdue University'
__license__ = 'BSD'
__version__ = '#TRUNK#'


import sys
import os
import subprocess
import shutil
import MySQLdb
import MySQLdb.cursors
from optparse import OptionParser
import ConfigParser
import getpass
import unittest
import roster_core
import roster_server

CONFIG_FILE = 'test_data/roster.conf' ## Example in test_data
EXEC = '../roster-core/scripts/roster_database_bootstrap'


class TestRosterDatabaseBootstrap(unittest.TestCase):

  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)
    self.cfg_server = self.config_instance.config_file['server']
    self.cfg_database = self.config_instance.config_file['database']
    self.cfg_exporter = self.config_instance.config_file['exporter']
    self.cfg_fakeldap = self.config_instance.config_file['fakeldap']
    self.db_instance = self.config_instance.GetDb()
    self.base_command = (
        'python %s -c %s/config.conf -u %s -U %s '
        '-d %s -n %s '
        '--ssl-cert %s --ssl-key %s '
        '--root-config-dir %s --backup-dir %s -i %s/init '
        '-p %s --run-as %s --force' % (
            EXEC,
            self.cfg_exporter['backup_dir'],
            self.cfg_database['login'],u'new_user',
            self.cfg_database['database'],
            self.cfg_database['server'],
            self.cfg_server['ssl_cert_file'], self.cfg_server['ssl_key_file'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_database['passwd'],os.getuid()))
    ## The first number represents the auth_module chosen. This can change if
    ## more modules are added later and appear before general_ldap.
    self.base_communicate = ('1\nuid=%%s,ou=People,dc=dc,dc=university,dc=edu\n'
        '/etc/roster_certs/host.cert\n3\nldaps://ldap.university.edu:636\n')

  def tearDown(self):
    if( os.path.exists(self.cfg_exporter['backup_dir']) ):
      shutil.rmtree(self.cfg_exporter['backup_dir'])

  def testDBBootstrapExtraParamSSL(self):
    command = subprocess.Popen(
        '%s --infinite-renew-time %s --core-die-time %s '
        '--get-credentials-wait-increment %s --credential-expiry-time %s '
        '--big-lock-timeout %s --db-ssl --db-ssl-ca ca' % (
            self.base_command,
            90210, 22221, 13, 26, 9001),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    ## Check base_communicate in setUp if module selected is wrong
    command.communicate(self.base_communicate)

    config = roster_core.Config(file_name='%s/config.conf' %
        self.cfg_exporter['backup_dir'])
    config_server = config.config_file['server']
    config_credentials = config.config_file['credentials']
    config_database = config.config_file['database']
    self.assertEquals(config_server['inf_renew_time'], 90210)
    self.assertEquals(config_server['core_die_time'], 22221)
    self.assertEquals(config_server['get_credentials_wait_increment'], 13)
    self.assertEquals(config_credentials['exp_time'], 26)
    self.assertEquals(config_database['ssl'], True)
    self.assertEquals(config_database['ssl_ca'], 'ca')

  def testDBBootstrapExtraParam(self):
    command = subprocess.Popen(
        '%s --infinite-renew-time %s --core-die-time %s '
        '--get-credentials-wait-increment %s --credential-expiry-time %s '
        '--big-lock-timeout %s' % (
            self.base_command,
            90210, 22221, 13, 26, 9001),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    ## Check base_communicate in setUp if module selected is wrong
    command.communicate(self.base_communicate)

    config = roster_core.Config(file_name='%s/config.conf' %
        self.cfg_exporter['backup_dir'])
    config_server = config.config_file['server']
    config_credentials = config.config_file['credentials']
    config_database = config.config_file['database']
    self.assertEquals(config_server['inf_renew_time'], 90210)
    self.assertEquals(config_server['core_die_time'], 22221)
    self.assertEquals(config_server['get_credentials_wait_increment'], 13)
    self.assertEquals(config_credentials['exp_time'], 26)
    self.assertEquals(config_database['ssl'], False)
    self.assertEquals(config_database['ssl_ca'], '')

  def testDBBootstrapUsername(self):
    command = subprocess.Popen('python %s -c %s/config.conf -u %s -U %s '
        '-d %s -n %s '
        '--ssl-cert %s --ssl-key %s '
        '--root-config-dir %s --backup-dir %s -i %s/init '
        '-p %s --run-as %s --force' % (
            EXEC,
            self.cfg_exporter['backup_dir'],
            self.cfg_database['login'],u'new_user',
            self.cfg_database['database'],
            self.cfg_database['server'],
            self.cfg_server['ssl_cert_file'], self.cfg_server['ssl_key_file'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_database['passwd'],os.getuid()),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    ## Check base_communicate in setUp if module selected is wrong
    command.communicate(self.base_communicate)

    self.db_instance.StartTransaction()
    user_arguments = self.db_instance.ListRow('users',
        self.db_instance.GetEmptyRowDict('users'))
    self.assertEqual(user_arguments[1]['user_name'],u'new_user')
    self.db_instance.EndTransaction()

    command = subprocess.Popen('python %s -c %s/config.conf -u %s -U %s '
        '-d %s -n %s '
        '--ssl-cert %s --ssl-key %s '
        '--root-config-dir %s --backup-dir %s -i %s/init '
        '-p %s --run-as %s --force' % (
            EXEC,
            self.cfg_exporter['backup_dir'],
            self.cfg_database['login'],u'another_new_user',
            self.cfg_database['database'],
            self.cfg_database['server'],
            self.cfg_server['ssl_cert_file'], self.cfg_server['ssl_key_file'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_database['passwd'],os.getuid()),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    ## Check base_communicate in setUp if module selected is wrong
    self.base_communicate = (
        'n\n1\nuid=%%s,ou=People,dc=dc,dc=university,dc=edu\n'
        '/etc/roster_certs/host.cert\n3\nldaps://ldap.university.edu:636\n')
    command.communicate(self.base_communicate)

    self.db_instance.StartTransaction()
    user_arguments = self.db_instance.ListRow('users',
        self.db_instance.GetEmptyRowDict('users'))
    self.assertEqual(user_arguments[1]['user_name'],u'another_new_user')
    self.db_instance.EndTransaction()

  def testDBBootstrapNoCert(self):
    command = subprocess.Popen('python %s -c %s/config.conf -u %s -U %s '
        '-d %s -n %s '
        '--root-config-dir %s --backup-dir %s -i %s/init '
        '-p %s --run-as %s --force' % (
            EXEC,
            self.cfg_exporter['backup_dir'],
            self.cfg_database['login'],u'new_user',
            self.cfg_database['database'],
            self.cfg_database['server'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_exporter['backup_dir'],
            self.cfg_database['passwd'],os.getuid()),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    ## Check base_communicate in setUp if module selected is wrong
    stdout_value = command.communicate(self.base_communicate)[0]
    self.assertNotEqual(repr(stdout_value).find('ERROR: An ssl cert file MUST '
        'be specified with --ssl-cert.'), -1)

  def testDBBootstrapUseConfigFile(self):
    pre_test_config_file_string = open(CONFIG_FILE, 'r').read()
    command = subprocess.Popen('python %s -c %s/roster.conf -U %s -i %s '
        '--backup-dir %s --root-config-dir %s --run-as %d --force' % (EXEC,
            u'test_data', u'new_user', u'./test_data/rosterd', u'./test_data',
            u'./test_data', os.getuid()), shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    stdout_value = command.communicate('Y')
    self.assertEqual(stdout_value, ('Config file test_data/roster.conf exists, '
                                    'use it? (Y/n): ', None))
    post_test_config_file_string = open(CONFIG_FILE, 'r').read()
    self.assertEqual(pre_test_config_file_string, post_test_config_file_string)

  def testDBBootstrapMissingConfigFileInfo(self):
    missing_info_config = './test_data/missing_info_test.conf'
    pre_test_config_file_string = open(CONFIG_FILE, 'r').read()
    config_lines = pre_test_config_file_string.split('\n')
    rewrite_config_file = open(missing_info_config, 'w')
    for line in config_lines:
      if( not 'host = ' in line ):
        rewrite_config_file.write('%s\n' % line)
    rewrite_config_file.close()
    command = subprocess.Popen('python %s -c %s -U %s '
        '-i %s --backup-dir %s --root-config-dir %s --run-as %d --force' % (
            EXEC, missing_info_config, u'new_user', u'./test_data/rosterd',
            u'./test_data', u'./test_data', os.getuid()), shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout_value = command.communicate('Y')
    self.assertEqual(stdout_value, ('Config file '
        './test_data/missing_info_test.conf exists, use it? (Y/n): Variable '
        '\"host\" is missing in config file: '
        '\"./test_data/missing_info_test.conf\", in the \"server\" section.\n',
        None))
    os.remove(missing_info_config)

    rewrite_config_file = open(missing_info_config, 'w')
    for line in config_lines:
      if( not 'database = ' in line ):
        rewrite_config_file.write('%s\n' % line)
    rewrite_config_file.close()
    command = subprocess.Popen('python %s -c %s -U %s '
        '-i %s --backup-dir %s --root-config-dir %s --run-as %d --force' % (
            EXEC, missing_info_config, u'new_user', u'./test_data/rosterd',
            u'./test_data', u'./test_data', os.getuid()), shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout_value = command.communicate('Y')
    self.assertEqual(stdout_value, ('Config file '
        './test_data/missing_info_test.conf exists, use it? (Y/n): Variable '
        '\"database\" is missing in config file: '
        '\"./test_data/missing_info_test.conf\", in the \"database\" section.\n',
        None))
    os.remove(missing_info_config)

  def testDBBootstrapInvalidUseConfigFileResponse(self):
    pre_test_config_file_string = open(CONFIG_FILE, 'r').read()

    command = subprocess.Popen('python %s -c %s/roster.conf -U %s -i %s '
        '--backup-dir %s --root-config-dir %s --run-as %d --force' % (EXEC,
            u'test_data', u'new_user', u'./test_data/rosterd', u'./test_data',
            u'./test_data', os.getuid()), shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    stdout_value = command.communicate('si\nyes')
    self.assertEqual(stdout_value, ('Config file test_data/roster.conf exists, '
        'use it? (Y/n): Please enter response as either \"yes\" or \"no\"\n'
        'Config file test_data/roster.conf exists, use it? (Y/n): ', None))

    post_test_config_file_string = open(CONFIG_FILE, 'r').read()
    self.assertEqual(pre_test_config_file_string, post_test_config_file_string)

  def testDBBootstrapDefault(self):
    command = subprocess.Popen(
        self.base_command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    command.communicate(self.base_communicate)

    if( not os.path.exists('%s/config.conf' % self.cfg_exporter['backup_dir']) ):
      self.fail('Conf file was not created.')
    if( not os.path.exists('%s/init' % self.cfg_exporter['backup_dir']) ):
      self.fail('Init File was not created.')

    config = roster_core.Config(file_name='%s/config.conf' %
        self.cfg_exporter['backup_dir'])
    config_database = config.config_file['database']
    config_credentials = config.config_file['credentials']
    config_server = config.config_file['server']
    self.assertEqual(config_database['server'], self.cfg_database['server'])
    self.assertEqual(config_database['ssl'], self.cfg_database['ssl'])
    self.assertEqual(config_database['ssl_ca'], self.cfg_database['ssl_ca'])

if( __name__ == '__main__' ):
      unittest.main()
