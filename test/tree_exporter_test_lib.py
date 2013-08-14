import unittest
import os
import getpass
import shutil

import roster_core

TESTDIR = u'%s/unittest_dir/' % os.getcwd()
BINDDIR = u'%s/test_data/bind_dir/' % os.getcwd()
NAMED_DIR = os.path.join(BINDDIR, 'named')
SSH_USER = unicode(getpass.getuser())
USER_CONFIG = 'test_data/roster_user_tools.conf'
CONFIG_FILE = 'test_data/roster.conf' # Example in test_data
DATA_FILE = 'test_data/test_data.sql'
EXEC = '../roster-config-manager/scripts/dnstreeexport'
USERNAME = u'sharrell'

class TreeExportTestCase(unittest.TestCase):
  def setUp(self):
    self.config_instance = roster_core.Config(file_name=CONFIG_FILE)

    self.root_config_dir = self.config_instance.config_file['exporter'][
        'root_config_dir']
    self.backup_dir = self.config_instance.config_file['exporter'][
        'backup_dir']

    self.db_instance = self.config_instance.GetDb()

    self.db_instance.CreateRosterDatabase()

    data = open(DATA_FILE, 'r').read()
    self.db_instance.StartTransaction()
    self.db_instance.cursor.execute(data)
    self.db_instance.EndTransaction()
    self.db_instance.close()

    self.core_instance = roster_core.Core(USERNAME, self.config_instance)

    for zone in self.core_instance.ListZones():
      self.core_instance.RemoveZone(zone)
    self.assertEqual(self.core_instance.ListZones(), {})

    self.tarfile = ''

    self.core_instance.MakeDnsServerSet(u'internal_dns')
    self.core_instance.MakeDnsServerSet(u'external_dns')
    self.core_instance.MakeDnsServerSet(u'private_dns')

    self.core_instance.MakeView(u'internal')
    self.core_instance.MakeView(u'external')
    self.core_instance.MakeView(u'private')

    self.core_instance.MakeZone(u'university.edu', u'master', 
        u'university.edu.', 
        zone_options=u'#Allow update\nallow-update { none; };\n',
        view_name=u'internal')
    self.core_instance.MakeZone(u'university.edu', u'master', 
        u'university.edu.', 
        zone_options=u'#Allow update\nallow-update { none; };\n',
        view_name=u'external')
    self.core_instance.MakeZone(u'university.edu', u'master', 
        u'university.edu.', 
        zone_options=u'#Allow update\nallow-update { none; };\n',
        view_name=u'private')
    self.core_instance.MakeZone(u'int.university.edu', u'master', 
        u'university2.edu.',
        zone_options=u'#Allow update\nallow-update { none; };\n',
        view_name=u'internal', make_any=False)
    self.core_instance.MakeZone(u'priv.university.edu', u'master',
        u'university3.edu.', 
        zone_options=u'#Allow update\nallow-update { none; };\n',
        view_name=u'private', make_any=False)
    self.core_instance.MakeZone(u'168.192.in-addr', u'master',
        u'168.192.in-addr.arpa.', 
        zone_options=u'#Allow update\nallow-update { none; };\n',
        view_name=u'internal', make_any=False)
    self.core_instance.MakeZone(u'4.3.2.in-addr', u'master',
        u'4.3.2.in-addr.arpa.',
        zone_options=u'#Allow update\nallow-update { none; };\n',
        view_name=u'external', make_any=False)
    self.core_instance.MakeZone(u'bio.university.edu', u'slave',
        u'university4.edu.',
        zone_options=u'Allow update\nallow-update { any; };\n',
        view_name=u'external', make_any=False)

    self.core_instance.MakeDnsServer(u'dns1.university.edu', SSH_USER,
        BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServer(u'dns2.university.edu', SSH_USER,
        BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServer(u'dns3.university.edu', SSH_USER,
        BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServer(u'dns4.university.edu', SSH_USER,
        BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServer(u'ns1.university.edu', SSH_USER,
        BINDDIR, TESTDIR)
    self.core_instance.MakeDnsServer(u'ns1.int.university.edu', SSH_USER,
        BINDDIR, TESTDIR)

    self.core_instance.MakeDnsServerSetAssignments(u'ns1.university.edu', 
        u'external_dns')
    self.core_instance.MakeDnsServerSetAssignments(u'ns1.int.university.edu', 
        u'internal_dns')
    self.core_instance.MakeDnsServerSetAssignments(u'dns1.university.edu', 
        u'internal_dns')
    self.core_instance.MakeDnsServerSetAssignments(u'dns2.university.edu', 
        u'external_dns')
    self.core_instance.MakeDnsServerSetAssignments(u'dns3.university.edu', 
        u'external_dns')
    self.core_instance.MakeDnsServerSetAssignments(u'dns4.university.edu', 
        u'private_dns')

    self.core_instance.MakeDnsServerSetViewAssignments(u'external', 1, 
        u'internal_dns', view_options=u'recursion no;')
    self.core_instance.MakeDnsServerSetViewAssignments(u'internal', 2, 
        u'internal_dns', view_options=u'recursion no;')

    self.core_instance.MakeDnsServerSetViewAssignments(u'external', 1,
        u'external_dns', view_options=u'recursion no;')

    self.core_instance.MakeDnsServerSetViewAssignments(u'private', 1,
        u'private_dns', view_options=u'recursion no;')

    self.core_instance.MakeRecord(u'soa', u'@', u'168.192.in-addr',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin@university.edu.',
         u'serial_number': 20091223,
         u'refresh_seconds': 5,
         u'retry_seconds': 5,
         u'expiry_seconds': 5,
         u'minimum_seconds': 5},
        view_name=u'internal', ttl=3600)
    self.core_instance.MakeRecord(u'soa', u'@', u'4.3.2.in-addr',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin@university.edu.',
         u'serial_number': 20091224,
         u'refresh_seconds': 5,
         u'retry_seconds': 5,
         u'expiry_seconds': 5,
         u'minimum_seconds': 5},
        view_name=u'external', ttl=3600)
    self.core_instance.MakeRecord(u'soa', u'@', u'university.edu',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin@university.edu.',
         u'serial_number': 20091225,
         u'refresh_seconds': 5,
         u'retry_seconds': 5,
         u'expiry_seconds': 5,
         u'minimum_seconds': 5},
        view_name=u'internal', ttl=3600)
    self.core_instance.MakeRecord(u'soa', u'@', u'university.edu',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin@university.edu.',
         u'serial_number': 20091226,
         u'refresh_seconds': 5,
         u'retry_seconds': 5,
         u'expiry_seconds': 5,
         u'minimum_seconds': 5},
        view_name=u'private', ttl=3600)
    self.core_instance.MakeRecord(u'soa', u'@', u'university.edu',
        {u'name_server': u'ns1.university.edu.',
         u'admin_email': u'admin@university.edu.',
         u'serial_number': 20091227,
         u'refresh_seconds': 5,
         u'retry_seconds': 5,
         u'expiry_seconds': 5,
         u'minimum_seconds': 5},
        view_name=u'external', ttl=3600)

    # Make Records
    self.core_instance.MakeRecord(u'mx', u'@', u'university.edu',
        {u'priority': 1, u'mail_server': u'mail1.university.edu.'},
        view_name=u'any', ttl=3600)
    self.core_instance.MakeRecord(u'mx', u'@', u'university.edu',
        {u'priority': 1, u'mail_server': u'mail2.university.edu.'},
        view_name=u'any', ttl=3600)
    self.core_instance.MakeRecord(u'a', u'computer1', u'university.edu',
        {u'assignment_ip': u'1.2.3.5'},
        view_name=u'external', ttl=3600)
    self.core_instance.MakeRecord(u'a', u'computer1', u'university.edu',
        {u'assignment_ip': u'192.168.1.1'},
        view_name=u'internal', ttl=3600)
    self.core_instance.MakeRecord(u'a', u'computer2', u'university.edu',
        {u'assignment_ip': u'192.168.1.2'},
        view_name=u'internal', ttl=3600)
    self.core_instance.MakeRecord(u'a', u'computer3', u'university.edu',
        {u'assignment_ip': u'1.2.3.6'},
        view_name=u'external', ttl=3600)
    self.core_instance.MakeRecord(u'a', u'computer4', u'university.edu',
        {u'assignment_ip': u'192.168.1.4'},
        view_name=u'internal', ttl=3600)
    self.core_instance.MakeRecord(u'ns', u'@', u'university.edu',
        {u'name_server': u'ns1.university.edu.'},
        view_name=u'any', ttl=3600)
    self.core_instance.MakeRecord(u'ns', u'@', u'university.edu',
        {u'name_server': u'ns2.university.edu.'},
        view_name=u'any', ttl=3600)
    self.core_instance.MakeRecord(u'ptr', u'1', u'4.3.2.in-addr',
        {u'assignment_host': u'computer1.university.edu.'},
        view_name=u'external', ttl=3600)
    self.core_instance.MakeRecord(u'ptr', u'4', u'168.192.in-addr',
        {u'assignment_host': u'computer4.university.edu.'},
        view_name=u'internal', ttl=3600)

    self.core_instance.MakeACL(u'public', u'192.168.1.4/30')
    self.core_instance.MakeACL(u'public', u'10.10/32')
    self.core_instance.MakeACL(u'secret', u'10.10/32')

    self.core_instance.MakeViewToACLAssignments(u'internal', u'internal_dns', 
        u'secret', 1)
    self.core_instance.MakeViewToACLAssignments(u'internal', u'internal_dns', 
        u'public', 0)
    self.core_instance.MakeViewToACLAssignments(u'external', u'internal_dns', 
        u'public', 1)
    self.core_instance.MakeViewToACLAssignments(u'private', u'private_dns', 
        u'secret', 0)

    #self.core_instance.MakeNamedConfGlobalOption(u'internal_dns', u'null')
    self.core_instance.MakeNamedConfGlobalOption(u'internal_dns', 
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
    self.core_instance.MakeNamedConfGlobalOption(u'external_dns',
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
    self.core_instance.MakeNamedConfGlobalOption(u'private_dns',
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

    self.core_instance.RemoveZone(u'cs.university.edu')
    self.core_instance.RemoveZone(u'eas.university.edu')
    self.core_instance.RemoveZone(u'bio.university.edu')

  def tearDown(self):
    if( os.path.exists(self.root_config_dir) ):
      shutil.rmtree(self.root_config_dir)
    if( os.path.exists('dns_tree-1.tar.bz2') ):
      os.remove('dns_tree-1.tar.bz2')
    if( os.path.exists('./test_data/backup_dir') ):
      for fname in os.listdir('./test_data/backup_dir'):
        if( fname.endswith('.bz2') ):
          os.remove('./test_data/backup_dir/%s' % fname)

