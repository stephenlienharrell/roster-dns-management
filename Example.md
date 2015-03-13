#summary Instructions for setting up common DNS setups.

<a href='Hidden comment: 
Google Drawings:
https://docs.google.com/leaf?id=0BxZBXx33-8suNDcyNWU2ZDctYjVjNi00OWQ5LWExMGItMmNkMTg5OWJhZWNj&hl=en_US
'></a>

# Introduction #
Descriptions of some common DNS setups and the step-by-step instructions on how to do it with the [roster-user-tools](UserToolsUsage.md).

# Common Setups #


## Basic Setup ##
### Description ###
A single DNS server serving records.


![http://roster-dns-management.googlecode.com/svn/wiki/img/MasterNameServers.png](http://roster-dns-management.googlecode.com/svn/wiki/img/MasterNameServers.png)
### Commands ###
  1. Create a DNS server set:
```
$ dnsmkdnsserver dns_server_set -e server_set
```
  1. Create a DNS server:
```
$ dnsmkdnsserver dns_server -d server
```
  1. Assign the DNS server to the DNS server set:
```
$ dnsmkdnsserver assignment -d server -e server_set
```
  1. Make a view
```
$ dnsmkview view -v public
```
  1. Assign the view to the DNS server set:
```
$ dnsmkview dns_server_set -v public -e server_set -r 1
```
  1. Assign the view to the any ACL/DNS server set combo:
```
$ dnsmkview acl -v public -a any -e server_set
```
  1. Create a zone with the public view:
```
$ dnsmkzone forward -z example.com. --origin example.com. -v public -t master 
```
  1. Create an SOA record for the public zone:
```
$ dnsmkrecord soa --admin-email admin.example.com. --expiry-seconds 60 --name-server ns.example.com. --retry-seconds 120 --refresh-seconds 80  --minimum-seconds 40 --serial-number 1337 -t example.com -v public -z example.com.
```
  1. Create an A record:
```
$ dnsmkrecord a -t www -z example.com. -v any --assignment-ip 192.168.1.24
```


## Slave Name Server ##
### Description ###
This consists of two DNS servers serving records with one as the primary (master) and one as the secondary (slave). The slave serves as a backup of the master.


![http://roster-dns-management.googlecode.com/svn/wiki/img/SlaveNameServers.png](http://roster-dns-management.googlecode.com/svn/wiki/img/SlaveNameServers.png)
### Commands ###
  1. Create a DNS server set:
```
$ dnsmkdnsserver dns_server_set -e server_set
```
  1. Create a DNS server:
```
$ dnsmkdnsserver dns_server -d server
```
  1. Assign the DNS server to the DNS server set:
```
$ dnsmkdnsserver assignment -d server -e server_set
```
  1. Make a view
```
$ dnsmkview view -v public
```
  1. Assign the view to the DNS server set:
```
$ dnsmkview dns_server_set -v public -e server_set -r 1
```
  1. Assign the view to the any ACL/DNS server set combo:
```
$ dnsmkview acl -v public -a any -e server_set
```
  1. Create a master zone:
```
$ dnsmkzone forward -z example.com. --origin example.com. -v public -t master 
```
  1. Create a slave zone:
```
$ dnsmkzone forward -z example.com. --origin example.com. -v public -t slave 
```
  1. Create an SOA record for the public zone:
```
$ dnsmkrecord soa --admin-email admin.example.com. --expiry-seconds 60 --name-server ns.example.com. --retry-seconds 120 --refresh-seconds 80  --minimum-seconds 40 --serial-number 1337 -t example.com -v public -z example.com.
```
  1. Create an A record:
```
$ dnsmkrecord a -t www -z example.com. -v any --assignment-ip 192.168.1.24
```


## Stealth DNS ##
### Description ###
The purpose of a stealth DNS setup or split zone is to control who can see what. For example, you want users with internal IP's to be able to view private hosts, but still have hosts the public can see.

Creating records in Roster's any view will create records that will automatically show up in both private and public views while only being defined once.


![http://roster-dns-management.googlecode.com/svn/wiki/img/StealthDNS.png](http://roster-dns-management.googlecode.com/svn/wiki/img/StealthDNS.png)
### Commands ###
  1. Create a DNS server set:
```
$ dnsmkdnsserver dns_server_set -e server_set
```
  1. Create a DNS server:
```
$ dnsmkdnsserver dns_server -d server
```
  1. Assign the DNS server to the DNS server set:
```
$ dnsmkdnsserver assignment -d server -e server_set -r 1
```
  1. Define an ACL that only allows local IP's:
```
$ dnsmkacl -a private --cidr-block 192.168.1.0/24 --allow
```
  1. Make both the public and stealth views
```
$ dnsmkview view -v public
$ dnsmkview view -v stealth
```
  1. Assign the views to the DNS server set:
```
$ dnsmkview dns_server_set -v public -e server_set -r 1
$ dnsmkview dns_server_set -v stealth -e server_set -r 2
```
  1. Assign the views to their respective ACL/DNS server set combos:
```
$ dnsmkview acl -v public -a any -e server_set
$ dnsmkview acl -v stealth -a private -e server_set
```
  1. Create a zone with the public view:
```
$ dnsmkzone forward -z example.com. --origin example.com. -v public -t master 
```
  1. create a zone with the stealth view:
```
$ dnsmkzone forward -z example.com. --origin example.com. -v stealth -t master
```
  1. Create a reverse zone for local IP's:
```
$ dnsmkzone reverse -z example.com._rev --dont-make-any -v stealth -t master --origin 2.0.192.in-addr.arpa.
```
  1. Create an SOA record for the public zone:
```
$ dnsmkrecord soa --admin-email admin.example.com. --expiry-seconds 60 --name-server ns.example.com. --retry-seconds 120 --refresh-seconds 80  --minimum-seconds 40 --serial-number 1337 -t example.com -v public -z example.com.
```
  1. Create an SOA record for the stealth zone:
```
$ dnsmkrecord soa --admin-email admin.example.com. --expiry-seconds 60 --name-server ns.example.com. --retry-seconds 120 --refresh-seconds 80 --minimum-seconds 40 --serial-number 1337 -t example.com -v stealth -z example.com.
```
  1. Create an SOA record for the reverse stealth zone:
```
$ dnsmkrecord soa --admin-email admin.example.com. --expiry-seconds 60 --name-server ns.example.com. --retry-seconds 120 --refresh-seconds 80  --minimum-seconds 40 --serial-number 1337 -t example.com -v stealth -z example.com._rev
```
  1. Create an A record for everyone:
```
$ dnsmkrecord a -t www -z example.com. -v any --assignment-ip 192.168.1.24
```
  1. Create an A record for everyone:
```
$ dnsmkrecord a -t ftp -z example.com. -v any --assignment-ip 192.168.1.26
```
  1. Create an A record for local IP's:
```
$ dnsmkrecord a -t secret -z example.com. -v stealth --assignment-ip 192.168.1.32
```