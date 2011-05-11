INIT_FILE = """#!/bin/sh
#
# /etc/rc.d/init.d/roster
#
# Starts Roster server
#
# chkconfig: 345 99 1
#
# description: Starts Roster Server
#
### BEGIN INIT INFO
# Provides:     rosterd
# Required-Start:   $local_fs $network $syslog
# Required-Stop:   $local_fs $network $syslog
# Default-Start:    3 4 5
# Default-Stop: 0 1 6
# Short-Description: Start/stop rosterd server
### END INIT INFO
#
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

lockfile=/var/lock/roster

start_roster()
{
  echo "Starting Roster Server..."
  rosterd &
}
stop_roster()
{
  if [ -e $lockfile ]
  then
    if [ -w $lockfile ]
    then
      echo "Stopping Roster Server..."
      rm $lockfile
    else
      echo "Could not stop Roster Server. Do you have correct permissions?"
      exit 1
    fi
  else
    echo "Could not find lock file. Is Roster Server running?"
    exit 1
  fi
}

case "$1" in
  start)
    start_roster
    ;;
  stop)
    stop_roster
    ;;
  restart)
    stop_roster
    sleep 2
    start_roster
    ;;
  *)
   echo "Usage $1 {start|stop|restart}"
   exit 1
   ;;
esac
"""

SCHEMA_FILE = """# Copyright (c) 2009, Purdue University
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


#####
# This file represents the current working schema. Any updates to the code need
# to be represented here.

########### These are commands prepare the database for our tables ###########

DROP TABLE IF EXISTS `ipv6_index`;
DROP TABLE IF EXISTS `ipv4_index`;
DROP TABLE IF EXISTS `audit_log`;
DROP TABLE IF EXISTS `reserved_words`;
DROP TABLE IF EXISTS `named_conf_global_options`;
DROP TABLE IF EXISTS `reverse_range_zone_assignments`;
DROP TABLE IF EXISTS `reverse_range_permissions`;
DROP TABLE IF EXISTS `forward_zone_permissions`;
DROP TABLE IF EXISTS `user_group_assignments`;
DROP TABLE IF EXISTS `groups`;
DROP TABLE IF EXISTS `dns_server_set_view_assignments`;
DROP TABLE IF EXISTS `dns_server_set_assignments`;
DROP TABLE IF EXISTS `dns_server_sets`;
DROP TABLE IF EXISTS `dns_servers`;
DROP TABLE IF EXISTS `view_dependency_assignments`;
DROP TABLE IF EXISTS `view_acl_assignments`;
DROP TABLE IF EXISTS `views`;
DROP TABLE IF EXISTS `acl_ranges`;
DROP TABLE IF EXISTS `acls`;
DROP TABLE IF EXISTS `record_arguments_records_assignments`;
DROP TABLE IF EXISTS `records`;
DROP TABLE IF EXISTS `zone_view_assignments`;
DROP TABLE IF EXISTS `zone_types`;
DROP TABLE IF EXISTS `view_dependencies`;
DROP TABLE IF EXISTS `zones`;
DROP TABLE IF EXISTS `credentials`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `record_arguments`;
DROP TABLE IF EXISTS `data_types`;
DROP TABLE IF EXISTS `record_types`;
DROP TABLE IF EXISTS `locks`;

########## Below is the database schema ##########

CREATE TABLE `locks` (

  `lock_id` smallint unsigned NOT NULL auto_increment,
  `lock_name` varchar(31) UNIQUE NOT NULL,
  `locked` tinyint(1) default '0',
  `lock_last_updated` timestamp default CURRENT_TIMESTAMP
      on update CURRENT_TIMESTAMP,

  PRIMARY KEY (`lock_id`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `record_types` (

  `record_types_id` smallint unsigned NOT NULL auto_increment,
  `record_type` varchar(8) UNIQUE NOT NULL,

  PRIMARY KEY (`record_types_id`),
  INDEX `record_type_1` (`record_type`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `data_types` (
    
  `data_types_id` smallint unsigned NOT NULL auto_increment,
  `data_type` varchar(255) UNIQUE NOT NULL,

  PRIMARY KEY (`data_types_id`),
  INDEX `data_types_1` (`data_type`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `record_arguments` (

  `record_arguments_id` smallint unsigned NOT NULL auto_increment,
  `record_arguments_type` varchar(8) NOT NULL,
  `argument_name` varchar(255) NOT NULL,
  `argument_order` smallint unsigned NOT NULL,
  `argument_data_type` varchar(255) NOT NULL,

  PRIMARY KEY (`record_arguments_id`),
  INDEX `record_arguments_type_1` (`record_arguments_type`),
  INDEX `record_arguments_data_type_1` (`argument_data_type`),
  INDEX `record_arguments_type_argument_1` (`record_arguments_type`,
      `argument_name`),
  INDEX `record_arguments_type_argument_order_1` (`record_arguments_type`,
      `argument_name`, `argument_order`),

  CONSTRAINT `unique_type_argument_order_1` UNIQUE (`record_arguments_type`,
    `argument_name`, `argument_order`),
  CONSTRAINT `argument_data_type_1` FOREIGN KEY (`argument_data_type`)
    REFERENCES `data_types` (`data_type`),
  CONSTRAINT `record_type_1` FOREIGN KEY (`record_arguments_type`) REFERENCES
    `record_types` (`record_type`) ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `users` (

  `users_id` mediumint unsigned NOT NULL auto_increment,
  `user_name` varchar(255) UNIQUE NOT NULL,
  `access_level` smallint unsigned NOT NULL,

  PRIMARY KEY (`users_id`),
  INDEX `user_name_1` (`user_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `credentials` (

  `credential_id` int unsigned NOT NULL auto_increment,
  `credential_user_name` varchar(255) UNIQUE NOT NULL,
  `credential` varchar(36) UNIQUE NOT NULL,
  `last_used_timestamp` timestamp default CURRENT_TIMESTAMP
    on update CURRENT_TIMESTAMP,
  `infinite_cred` bool default 0,

  PRIMARY KEY (`credential_id`),
  CONSTRAINT `user_name_4` FOREIGN KEY (`credential_user_name`)
    REFERENCES `users` (`user_name`) ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `zones` (

  `zones_id` mediumint unsigned NOT NULL auto_increment,
  `zone_name` varchar(255) UNIQUE NOT NULL,

  PRIMARY KEY (`zones_id`),
  INDEX `zone_name_1` (`zone_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `view_dependencies` (

  `view_dependencies_id` mediumint unsigned NOT NULL auto_increment,
  `view_dependency` varchar(255) UNIQUE NOT NULL,

  PRIMARY KEY (`view_dependencies_id`),
  INDEX `view_dependency_1` (`view_dependency`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `zone_types` (

  `zone_type_id` tinyint unsigned NOT NULL auto_increment,
  `zone_type` varchar(31) UNIQUE NOT NULL,

  PRIMARY KEY (`zone_type_id`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `zone_view_assignments` (

  `zone_view_assignments_id` mediumint unsigned NOT NULL auto_increment,
  `zone_view_assignments_zone_name` varchar(255) NOT NULL,
  `zone_view_assignments_view_dependency` varchar(255) NOT NULL,
  `zone_view_assignments_zone_type` varchar(31) NOT NULL,
  `zone_origin` varchar(255) NOT NULL,
  `zone_options` longtext,

  PRIMARY KEY (`zone_view_assignments_id`),
  INDEX `zone_name` (`zone_view_assignments_zone_name`,
                   `zone_view_assignments_view_dependency`),
  INDEX `view_dependency_3` (`zone_view_assignments_view_dependency`),

  CONSTRAINT `zone_type_1` FOREIGN KEY (`zone_view_assignments_zone_type`)
     REFERENCES `zone_types` (`zone_type`),
  CONSTRAINT `zone_name_3` FOREIGN KEY (`zone_view_assignments_zone_name`)
    REFERENCES `zones` (`zone_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `view_dependency_3` FOREIGN KEY
    (`zone_view_assignments_view_dependency`) REFERENCES `view_dependencies`
    (`view_dependency`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `unique_zone_name_zone_dependency` UNIQUE
    (`zone_view_assignments_zone_name`,`zone_view_assignments_view_dependency`),
  CONSTRAINT `unique_zone_origin_view_dependency` UNIQUE
    (`zone_view_assignments_view_dependency`,`zone_origin`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `records` (

  `records_id` mediumint unsigned NOT NULL auto_increment,
  `record_type` varchar(8) NOT NULL,
  `record_target` varchar(255) NOT NULL,
  `record_ttl` mediumint unsigned default NULL,
  `record_zone_name` varchar(255) NOT NULL,
  `record_view_dependency` varchar(255) NOT NULL,
  `record_last_updated` timestamp NOT NULL default CURRENT_TIMESTAMP on update
    CURRENT_TIMESTAMP,
  `record_last_user` varchar(255) NOT NULL,

  PRIMARY KEY (`records_id`),
  INDEX `record_type_id_1` (`records_id`, `record_type`),
  INDEX `record_type_1` (`record_type`),
  INDEX `user_name_1` (`record_last_user`),
  INDEX `record_target_1` (`record_target`),

  CONSTRAINT `record_type_2` FOREIGN KEY (`record_type`) REFERENCES
    `record_types` (`record_type`),
  CONSTRAINT `user_name_1` FOREIGN KEY (`record_last_user`) REFERENCES `users`
    (`user_name`),
  CONSTRAINT `zone_name_view_dependency_1` FOREIGN KEY (`record_zone_name`,
    `record_view_dependency`) REFERENCES `zone_view_assignments`
    (`zone_view_assignments_zone_name`, `zone_view_assignments_view_dependency`)
    ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `record_arguments_records_assignments` (

  `record_arguments_records_assignments_id` mediumint unsigned NOT NULL
    auto_increment,
  `record_arguments_records_assignments_record_id` mediumint unsigned 
    NOT NULL,
  `record_arguments_records_assignments_type` varchar(8) NOT NULL,
  `record_arguments_records_assignments_argument_name` varchar(255) NOT NULL,
  `argument_value` varchar(1022) NOT NULL,

  PRIMARY KEY (`record_arguments_records_assignments_id`),
  INDEX `argument_value_1` (`argument_value`(15)),
  INDEX `record_arguments_records_assignments_record_id_1`
    (`record_arguments_records_assignments_record_id`),
  INDEX `record_arguments_records_assignments_type_1`
    (`record_arguments_records_assignments_type`),
  INDEX `record_arguments_record_assignments_id_argument_1`
    (`record_arguments_records_assignments_record_id`,
      `record_arguments_records_assignments_argument_name`),

  CONSTRAINT `record_id_record_type_1` FOREIGN KEY
    (`record_arguments_records_assignments_record_id`,
      `record_arguments_records_assignments_type`) REFERENCES `records`
    (`records_id`, `record_type`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `argument_record_type_1` FOREIGN KEY
    (`record_arguments_records_assignments_type`,
      `record_arguments_records_assignments_argument_name`) REFERENCES
    `record_arguments` (`record_arguments_type`, `argument_name`),
  CONSTRAINT `unique_record_arguments_records_assignments` UNIQUE
    (`record_arguments_records_assignments_record_id`,
      `record_arguments_records_assignments_argument_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `acls` (

  `acl_id` smallint unsigned NOT NULL auto_increment,
  `acl_name` varchar(255) NOT NULL,

  PRIMARY KEY (`acl_id`),
  INDEX `acl_name_1` (`acl_name`),
  CONSTRAINT `acl_name_3` UNIQUE (`acl_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `acl_ranges` (
  `acl_range_id` mediumint unsigned NOT NULL auto_increment,
  `acl_ranges_acl_name` varchar(255) NOT NULL,
  `acl_range_allowed` boolean,
  `acl_range_cidr_block` varchar(43),

  PRIMARY KEY (`acl_range_id`),

  CONSTRAINT `acl_name_cidr_block_1` UNIQUE 
      (`acl_ranges_acl_name`, `acl_range_cidr_block`),
  CONSTRAINT `acl_name_1` FOREIGN KEY (`acl_ranges_acl_name`)
    REFERENCES `acls` (`acl_name`) ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `views` (

  `view_id` mediumint unsigned NOT NULL auto_increment,
  `view_name` varchar(255) UNIQUE NOT NULL,
  `view_options` longtext,

  PRIMARY KEY (`view_id`),
  INDEX `view_name_1` (`view_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `view_acl_assignments` (

  `view_acl_assignments_id` mediumint unsigned NOT NULL auto_increment,
  `view_acl_assignments_view_name` varchar(255) NOT NULL,
  `view_acl_assignments_acl_name` varchar(255) NOT NULL,

  PRIMARY KEY (`view_acl_assignments_id`),

  CONSTRAINT `acl_name_2` FOREIGN KEY (`view_acl_assignments_acl_name`)
    REFERENCES `acls` (`acl_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `view_name_2` FOREIGN KEY (`view_acl_assignments_view_name`)
    REFERENCES `views` (`view_name`) ON DELETE CASCADE ON UPDATE CASCADE,

  CONSTRAINT `acl_name_view_name_1` UNIQUE (`view_acl_assignments_acl_name`,
    `view_acl_assignments_view_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `view_dependency_assignments` (

  `view_dependency_assignments_id` mediumint unsigned NOT NULL auto_increment,
  `view_dependency_assignments_view_name` varchar(255) NOT NULL,
  `view_dependency_assignments_view_dependency` varchar(255) NOT NULL,

  PRIMARY KEY (`view_dependency_assignments_id`),
  INDEX `view_name_1` (`view_dependency_assignments_view_name`),
  INDEX `view_dependency_4` (`view_dependency_assignments_view_dependency`),

  CONSTRAINT `view_name_1` FOREIGN KEY (`view_dependency_assignments_view_name`)
    REFERENCES `views` (`view_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `view_dependency_assignments_unique_1` UNIQUE
    (`view_dependency_assignments_view_name`,
      `view_dependency_assignments_view_dependency`),
  CONSTRAINT `view_dependency_4` FOREIGN KEY 
    (`view_dependency_assignments_view_dependency`) REFERENCES
      `view_dependencies` (`view_dependency`) ON DELETE CASCADE
    ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `dns_servers` (
    
  `dns_server_id` smallint unsigned NOT NULL auto_increment,
  `dns_server_name` varchar(255) UNIQUE NOT NULL,

  PRIMARY KEY (`dns_server_id`),
  INDEX `dns_server_1` (`dns_server_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `dns_server_sets` (
    
  `dns_server_set_id` smallint unsigned NOT NULL auto_increment,
  `dns_server_set_name` varchar(255) UNIQUE NOT NULL,

  PRIMARY KEY (`dns_server_set_id`),
  INDEX `dns_server_set_1` (`dns_server_set_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `dns_server_set_assignments` (
  `dns_server_set_assignments_id` smallint unsigned NOT NULL auto_increment,
  `dns_server_set_assignments_dns_server_name` varchar(255) NOT NULL,
  `dns_server_set_assignments_dns_server_set_name` varchar(255) NOT NULL,

  PRIMARY KEY (`dns_server_set_assignments_id`),

  CONSTRAINT `dns_server_1` FOREIGN KEY 
    (`dns_server_set_assignments_dns_server_name`) REFERENCES `dns_servers` 
    (`dns_server_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `dns_server_set_1` FOREIGN KEY 
    (`dns_server_set_assignments_dns_server_set_name`) REFERENCES
    `dns_server_sets` (`dns_server_set_name`) ON DELETE CASCADE 
    ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `dns_server_set_view_assignments` (
  `dns_server_set_view_assignments_id` smallint unsigned NOT NULL
      auto_increment,
  `dns_server_set_view_assignments_dns_server_set_name` varchar(255) 
      NOT NULL,
  `dns_server_set_view_assignments_view_name` varchar(255) NOT NULL,

  PRIMARY KEY (`dns_server_set_view_assignments_id`),

  CONSTRAINT `view_name_3` FOREIGN KEY 
    (`dns_server_set_view_assignments_view_name`) REFERENCES `views` 
    (`view_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `dns_server_set_2` FOREIGN KEY 
    (`dns_server_set_view_assignments_dns_server_set_name`) REFERENCES 
    `dns_server_sets` (`dns_server_set_name`) ON DELETE CASCADE 
    ON UPDATE CASCADE,
  CONSTRAINT `dns_server_set_view_assignments_unique_1` UNIQUE
    (`dns_server_set_view_assignments_dns_server_set_name`,
     `dns_server_set_view_assignments_view_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `groups` (

  `group_id` mediumint unsigned NOT NULL auto_increment,
  `group_name` varchar(255) UNIQUE NOT NULL,

  PRIMARY KEY (`group_id`),
  INDEX `group_name_1` (`group_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `user_group_assignments` (

  `user_group_assignments_id` mediumint unsigned NOT NULL auto_increment,
  `user_group_assignments_group_name` varchar(255) NOT NULL,
  `user_group_assignments_user_name` varchar(255) NOT NULL,

  PRIMARY KEY (`user_group_assignments_id`),
  INDEX `group_name_1` (`user_group_assignments_group_name`),
  INDEX `user_name_2` (`user_group_assignments_user_name`),

  CONSTRAINT `group_name_1` FOREIGN KEY (`user_group_assignments_group_name`)
    REFERENCES `groups` (`group_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `user_group_assignments_unique_1` UNIQUE
    (`user_group_assignments_group_name`, `user_group_assignments_user_name`),
  CONSTRAINT `user_name_2` FOREIGN KEY (`user_group_assignments_user_name`)
    REFERENCES `users` (`user_name`) ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `forward_zone_permissions` (

  `forward_zone_permissions_id` mediumint unsigned NOT NULL auto_increment,
  `forward_zone_permissions_group_name` varchar(255) NOT NULL,
  `forward_zone_permissions_zone_name` varchar(255) NOT NULL,
  `forward_zone_permissions_access_right` varchar(4) NOT NULL,

  PRIMARY KEY (`forward_zone_permissions_id`),
  INDEX `group_name_2` (`forward_zone_permissions_group_name`),
  INDEX `zone_name_4` (`forward_zone_permissions_zone_name`),
  INDEX `access_right_1` (`forward_zone_permissions_access_right`),

  CONSTRAINT `group_name_2` FOREIGN KEY (`forward_zone_permissions_group_name`)
    REFERENCES `groups` (`group_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `zone_name_4` FOREIGN KEY (`forward_zone_permissions_zone_name`)
    REFERENCES `zones` (`zone_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `forward_zone_permissions_unique_1` UNIQUE
    (`forward_zone_permissions_group_name`,
      `forward_zone_permissions_zone_name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE `reverse_range_permissions` (

  `reverse_range_permissions_id` mediumint unsigned NOT NULL auto_increment,
  `reverse_range_permissions_group_name` varchar(255) NOT NULL,
  `reverse_range_permissions_cidr_block` varchar(43) NOT NULL,
  `reverse_range_permissions_access_right` varchar(4) NOT NULL,

  PRIMARY KEY (`reverse_range_permissions_id`),
  INDEX `group_name_3` (`reverse_range_permissions_group_name`),
  INDEX `access_right_2` (`reverse_range_permissions_access_right`),

  CONSTRAINT `group_name_3` FOREIGN KEY (`reverse_range_permissions_group_name`)
    REFERENCES `groups` (`group_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `reverse_range_permissions_unique_1` UNIQUE
    (`reverse_range_permissions_group_name`,
     `reverse_range_permissions_cidr_block`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `reverse_range_zone_assignments` (

  `reverse_range_zone_assignments_id` mediumint unsigned NOT NULL 
      auto_increment,
  `reverse_range_zone_assignments_zone_name` varchar(255) NOT NULL,
  `reverse_range_zone_assignments_cidr_block` varchar(43) NOT NULL,

  PRIMARY KEY (`reverse_range_zone_assignments_id`),
  INDEX `zone_name_5` (`reverse_range_zone_assignments_zone_name`),

  CONSTRAINT `reverse_range_zone_assignments_unique_1` UNIQUE
    (`reverse_range_zone_assignments_zone_name`,
     `reverse_range_zone_assignments_cidr_block`),
  CONSTRAINT `zone_name_5` FOREIGN KEY 
    (`reverse_range_zone_assignments_zone_name`) REFERENCES `zones` 
    (`zone_name`) ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `named_conf_global_options` (

  `named_conf_global_options_id` mediumint unsigned NOT NULL auto_increment,
  `global_options` longtext NOT NULL,
  `named_conf_global_options_dns_server_set_name` varchar(255) NOT NULL,
  `options_created` timestamp NOT NULL default CURRENT_TIMESTAMP,

  PRIMARY KEY (`named_conf_global_options_id`),

  CONSTRAINT `dns_server_set_3` FOREIGN KEY 
    (`named_conf_global_options_dns_server_set_name`) REFERENCES
    `dns_server_sets` (`dns_server_set_name`) ON DELETE CASCADE 
    ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `reserved_words` (

  `reserved_word_id` mediumint unsigned NOT NULL auto_increment,
  `reserved_word` varchar(255) UNIQUE NOT NULL,

  PRIMARY KEY (`reserved_word_id`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `audit_log` (

  `audit_log_id` bigint unsigned NOT NULL auto_increment,
  `audit_log_user_name` varchar(255) NOT NULL,
  `action` varchar(255) NOT NULL,
  `data` text NOT NULL,
  `success` boolean NOT NULL,
  `audit_log_timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP,

  PRIMARY KEY (`audit_log_id`),

  CONSTRAINT `user_name_3` FOREIGN KEY (`audit_log_user_name`)
    REFERENCES `users` (`user_name`) ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ipv4_index` (
  `ipv4_index_id` mediumint unsigned NOT NULL auto_increment,
  `ipv4_dec_address` int unsigned NOT NULL,
  `ipv4_index_record_id` mediumint unsigned NOT NULL UNIQUE,

  PRIMARY KEY (`ipv4_index_id`),
  INDEX `ipv4_address` (`ipv4_dec_address`),

  CONSTRAINT `ipv4_index_record_id_1` FOREIGN KEY (`ipv4_index_record_id`)
    REFERENCES `records` (`records_id`) ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ipv6_index` (
  `ipv6_index_id` mediumint unsigned NOT NULL auto_increment,
  `ipv6_dec_upper` bigint unsigned NOT NULL,
  `ipv6_dec_lower` bigint unsigned NOT NULL,
  `ipv6_index_record_id` mediumint unsigned NOT NULL UNIQUE,

  PRIMARY KEY (`ipv6_index_id`),
  INDEX `ipv6_address` (`ipv6_dec_upper`, `ipv6_dec_lower`),

  CONSTRAINT `ipv6_index_record_id_1` FOREIGN KEY (`ipv6_index_record_id`)
    REFERENCES `records` (`records_id`) ON DELETE CASCADE ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

##########
# Things that are expected in the db that are not schema.
##########

INSERT INTO locks (lock_name) VALUES ('db_lock_lock');
INSERT INTO locks (lock_name) VALUES ('maintenance');

INSERT INTO view_dependencies (view_dependency) VALUES ('any');
INSERT INTO zone_types (zone_type) VALUES ('master'),('slave'),('forward'),
                                          ('hint');
INSERT INTO data_types (data_type) VALUES ('UnicodeString'),('AccessRight'),
                                          ('AccessLevel'),('CIDRBlock'),
                                          ('IntBool'),('UnsignedInt'),
                                          ('Hostname'),('DateTime'),
                                          ('IPv4IPAddress'),('IPv6IPAddress');
INSERT INTO record_types (record_type) VALUES ('a'),('hinfo'),('cname'),
                                              ('soa'),('mx'),('ns'),('aaaa'),
                                              ('txt'),('srv'),('ptr');
INSERT INTO record_arguments (record_arguments_type, argument_name,
                              argument_order, argument_data_type) VALUES
    ('a', 'assignment_ip', '0', 'IPv4IPAddress'),
    ('aaaa', 'assignment_ip', '0', 'IPv6IPAddress'),
    ('hinfo', 'hardware', '0', 'UnicodeString'),
    ('hinfo', 'os', '1', 'UnicodeString'),
    ('txt', 'quoted_text', '0', 'UnicodeString'),
    ('cname', 'assignment_host', '0', 'Hostname'),
    ('soa', 'name_server', '0', 'Hostname'),
    # An email address in this context looks exactly like a valid hostname
    ('soa', 'admin_email', '1', 'Hostname'),
    ('soa', 'serial_number', '2', 'UnsignedInt'),
    ('soa', 'refresh_seconds', '3', 'UnsignedInt'),
    ('soa', 'retry_seconds', '4', 'UnsignedInt'),
    ('soa', 'expiry_seconds', '5', 'UnsignedInt'),
    ('soa', 'minimum_seconds', '6', 'UnsignedInt'),
    ('srv', 'priority', '0', 'UnsignedInt'),
    ('srv', 'weight', '1', 'UnsignedInt'),
    ('srv', 'port', '2', 'UnsignedInt'),
    ('srv', 'assignment_host', '3', 'Hostname'),
    ('ns', 'name_server', '0', 'Hostname'),
    ('mx', 'priority', '0', 'UnsignedInt'),
    ('mx', 'mail_server', '1', 'Hostname'),
    ('ptr', 'assignment_host', '0', 'Hostname');

# make acl any keyword for named.conf
INSERT INTO acls (acl_name) VALUES ('any');
INSERT INTO acl_ranges (acl_ranges_acl_name, acl_range_allowed) VALUES 
    ('any', 1);

# Tree exporter needs to audit log with no active user. Here is a user for the
# exporter.
INSERT INTO users (user_name, access_level) VALUES ('tree_export_user', 0);
"""
