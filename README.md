# roster-dns-management
Automatically exported from code.google.com/p/roster-dns-management

This is a DNS management system originally hosted at code.google.com. It is no longer active but saved here for posterity.

From the original webpage:
Roster is DNS management software for use with BIND 9. It is licensed under the BSD license. Roster is currently being developed at Purdue University.

Roster is written in Python and uses a MySQL database with an XML-RPC front-end. It contains a set of command line user tools that connect to the XML-RPC front-end.

The config files for BIND are generated from the MySQL database so if a failure occurs in the database, the BIND servers will run as normal while recovery efforts can take place.

The software has four basic components. * The core which includes the database interface and core API. This layer contains the authorization layer. * The server which is an SSL enabled multi-threaded XML-RPC server. It also contains a plug-able authentication layer. (LDAP is the default) * The config manger which creates bind config files using the core API and handles pushing the files to their appropriate servers. * The user tools which contain over 30 tools to create, list and remove records, zones, views, dns servers, dns server sets, groups, users and the assignments between them all.

There is currently support for views, many dns servers in many configurations, IPv6, user/group authorization, zone/reverse CIDR block delegation, LDAP authentication, unicode hosts, and a rollback/disaster recovery framework.

If you have any questions, email us at roster-discussion at googlegroups.com
