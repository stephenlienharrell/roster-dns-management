#summary Usage of Roster User Tools

# Roster User Tools #

Roster User Tools is a collection of tools to create, list, and remove various records, zones, views, DNS servers, DNS server sets, groups, users, reserved words, ACL's,  and assignments between them. They can also set the database maintenance flag, create credential files, and list the audit log.

Each command's usage can be viewed by adding the **`--help`** flag. It is also worth noting that all **--config-file** flags on user tools are expecting a usertools config file created by [roster\_user\_tools\_bootstrap](UserToolsInstallation#Roster_User_Tools_Installation.md), not a roster config file.




**Note about installation path:**
The scripts used on this page are default installed by setuptools to **_prefix_/bin**
prefix is default **/usr**, but might be different depending on the system.
If you'd like to find out what **_prefix_** is for your system, open up a python shell and type:
```
  Python 2.6.6 (r266:84292, Sep 12 2011, 14:03:14) 
  [GCC 4.4.5 20110214 (Red Hat 4.4.5-6)] on linux2
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import sys
  >>> sys.exec_prefix
  '/usr'
```
If you'd like to know more, please consult: [Installing Python Modules](http://docs.python.org/install/index.html#inst-alt-install,).
From this point forward, it is expected that the scripts are installed in a directory in your $PATH.

**Note about standard flags:**
The examples on this page, for space and readability concerns, all exclude the standard user-tool flags.
```
They are: 
-u <username>
-p <password>
--config-file=<file> 
-s <server>

-u is the roster username
-p is the password
--config-file is the roster user tools config file location
-s is the URL for the Roster XML-RPC server. ex https://roster.example.edu:8000
```

## Basic Usage ##
After setting up and running Roster Core and Roster Server, Roster will now accept commands from the client machine.


1. You may start by adding some users with [dnsmkusergroup](UserToolsUsage#dnsmkusergroup.md) as shown:
```
# dnsmkusergroup user -n new_user -a 128
# dnsmkusergroup group -g group
# dnsmkusergroup assignment -n new_user -g group
```

  * **_new\_user_** is the username created
  * **_128_** is the access level
  * **_group_** is the desired group

2. DNS servers are physical machines running their own instance of BIND. They can be added with [dnsmkdnsserver](UserToolsUsage#dnsmkdnsserver.md) as shown:
```
# dnsmkdnsserver dns_server -d dns1 --dns-server-ssh-username user --dns-server-bind-dir /etc/bind/ --dns-server-test-dir /etc/bind/test/
# dnsmkdnsserver dns_server_set -e master
```

  * **_dns1_** is the hostname of the machine

3. This DNS server will be assigned to a DNS server set with [dnsmkdnsserver](UserToolsUsage#dnsmkdnsserver.md) as shown:
```
# dnsmkdnsserver assignment -d dns1 -e master
```

  * **_dns1_** is the hostname of the machine
  * **_master_** is the DNS server set name

4. Before any records are made, global options should be set with [dnsupnamedglobals](UserToolsUsage#dnsupnamedglobals.md). This command will upload the common information on all **named.conf** files. If you need examples, search the web for **named.conf** examples. A file must contain the global  header in order to use this command. For example, the file could be named **_globals.txt_**. Use of the command would be as follows:
```
# dnsupnamedglobals update -f named_globals.txt -d internal
```

  * **_named\_globals.txt_** is the text file uploaded
  * **_internal_** is the name of DNS server set that it will apply to
  * **_--update_** tells the version control system to update the named.conf header for that DNS server set.

5. ACLs can now be added with [dnsmkacl](UserToolsUsage#dnsmkacl.md) as shown below:
```
# dnsmkacl -a internal --cidr-block 192.168.1.0/24
```

  * **_internal_** is the ACL name
  * **_192.168.1.0/24_** is the CIDR block of the ACL

6. Next, a view will be created and by default there will be a view named "any". Create views with [dnsmkview](UserToolsUsage#dnsmkview.md) as shown:
```
# dnsmkview view -v internal --acl internal --allow
```

  * **_internal_** is the name of the view
  * the second **_internal_** is the corresponding ACL name
  * **_--allow_** toggles the view to allow machines in the ACL

7. The view can be added to a DNS server set with [dnsmkview](UserToolsUsage#dnsmkview.md)  as shown:
```
# dnsmkview dns_server_set -v internal -e master
```
  * **_internal_** is the name of the view
  * **_master_** is the DNS server set name

8. Zones can be added with [dnsmkzone](UserToolsUsage#dnsmkzone.md) as shown below:
```
# dnsmkzone reverse -z private_rev -v internal --type master --origin 1.168.192.in-addr.arpa.
# dnsmkzone forward -z private -v internal --type master --origin example.com.
```

  * **_private_** is the zone name
  * **_internal_** is the view name
  * **_master_** is the zone type
  * **_example.com._** is the zone origin
**(Don't forget the last dot on the origin.)**

9a. Create a SOA record with [dnsmkrecord](UserToolsUsage#dnsmkrecord.md) for the forward and reverse zones. The SOA record stores information about the DNS zone, such as the admin e-mail address, the source host, the serial number, and the several timers to refresh the zone. Use of the command would be as follows:
```
# dnsmkrecord soa --admin-email user.example.com. --name-server example.com. --serial-number 1 --refresh-seconds 3600 --retry-seconds 600 --expiry-seconds 86400 --minimum-seconds 3600 -z private -t example.com --view-name internal
# dnsmkrecord soa --admin-email user.example.com. --name-server example.com. --serial-number 1 --refresh-seconds 3600 --retry-seconds 600 --expiry-seconds 86400 --minimum-seconds 3600 -z private_rev -t example.com --view-name internal
```
  * **_user.example.com._** is the e-mail address of the admin. Note that a "." is used instead of an "@" in the e-mail address.
  * **_1_** is the default serial number of the zone. It is also known as the revision number of the zone file and increases each time the zone file is changed.
  * **_3600_** is the default seconds a slave DNS server will refresh from the master.
  * **_600_** is the default retry seconds for the slave to retry connecting to master after a failed attempt.
  * **_86400_** is the default time for the slave server to consider the zone file to be valid.
  * the second **_3600_** is the default minimum time-to-live seconds for the slave server to cache the zone file.

9b. Alternatively, an SOA record, and optionally, an NS record, can be auto-created with the zone using dnsmkzone.
```
# dnsmkzone reverse -z private_rev -v internal --type master --origin 1.168.192.in-addr.arpa. --bootstrap-zone --bootstrap-admin-email user.example.com. --bootstrap-nameserver example.com.
# dnsmkzone forward -z private -v internal --type master --origin example.com. --bootstrap-zone --bootstrap-admin-email user.example.com. --bootstrap-nameserver example.com.
```

10. Group permissions will need to be assigned prior to users being able to create records on delegated zones/reverse-ranges:
```
# dnsmkusergroup forward -g group -z private --group-permission a,aaaa
# dnsmkusergroup reverse -g group -z private_rev -b 192.168.1.0/24 --group-permission ptr
```

11. Records will be added next. For a simple way to make a host, the command [dnsmkhost](UserToolsUsage#dnsmkhost.md) can be used as follows:
```
# dnsmkhost add -i 192.168.1.101 -t machine1 -z private -v internal
```

  * **_192.168.1.101_** is the IP address of the target machine
  * **_machine1_** is the hostname of the target machine
  * **_private_** is the zone name
  * **_internal_** is the target view name This command will create an 'A' or 'AAAA' record along with a corresponding 'PTR' record.

12. Specific records can be added by more advanced users with the [dnsmkrecord](UserToolsUsage#dnsmkrecord.md) command. An example of creating an 'A' record is shown below:
```
# dnsmkrecord a --a-assignment-ip=192.168.1.101 -t machine1 -z private
```

  * **_a_** tells dnsmkrecord to make an 'A' record
  * **_192.168.1.101_** is the target IP address
  * **_machine1_** is the target hostname
  * **_private_** is the target zone name


# Commands #

## Credential ##
A credfile is a file used to verify that you have recently logged in and that the current session is still engaged to prevent excessive password re-entering. The credfile itself contains a unique UUID string for the current user.


> ### dnscredential ###
> To make an infinite credential:
```
dnscredential make_infinite -U <user-name>
```

> To remove a credential:
```
dnscredential remove -U <user-name>
```

> To list credentials:
```
dnscredential list [-U <user-name>]
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-U <user-credential>, --user-credential=<user-credential>
                      Username to apply credential to.
--no-header           Do not display a header.
```


## ACL (Access Control List) ##
An ACL is a specific set of IP addresses that can be assigned to views to control access.


> ### dnsmkacl ###
> To make ACLs:
```
dnsmkacl -a <acl-name> --cidr-block <cidr_block>
```
All arguments are required.


> ### dnslsacl ###
> To list ACLs:
```
dnslsacl -a <acl-name> --cidr-block <cidr_block>
```
You may use any or none of the arguments above to search ACLs.


> ### dnsrmacl ###
> To remove ACLs:
```
dnsrmacl -a <acl-name> --cidr-block <cidr-block>
```
All arguments are required.


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
-a ACL, --acl=ACL     String of access control list name.
--cidr-block=CIDR_BLOCK
                      String of CIDR block or single IP address.
```


## Audit Log ##
The audit log is a list of every change made to the configuration files. Audit ID is the identification number of a certain change. Every addition to the audit log increments the ID by 1.


> ### dnslsauditlog ###
> To list audit log:
```
dnslsauditlog [-a <action>] [-b <begin-time> -e <end-time>]
[--success <success>] [--no-header]
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-U <roster-user>, --roster-user=<roster-user>
                      Roster username.
-a <action>, --action=<action>
                      Specify action run on Roster.
--success=<success>   Integer 1 or 0 of action success.
-b <begin-time>, --begin-time=<begin-time>
                      Beginning time stamp in format YYYY-MM-DDThh:mm:ss.
-e <end-time>, --end-time=<end-time>
                      Ending time stamp in format YYYY-MM-DDThh:mm:ss.
--no-header           Do not display a header.
```


## DNS Servers ##
A host running BIND.


> ### dnsmkdnsserver ###
> To make a DNS server:
```
dnsmkdnsserver dns_server -d <dns-server>
```

> To make a DNS server set:
```
dnsmkdnsserver dns_server_set -e <dns-server-set>
```

> To make a DNS server set assignment:
```
dnsmkdnsserver assignment -d <dns-server> -e <dns-server-set>
```


> ### dnslsdnsserver ###
> To list a DNS server:
```
dnslsdnsserver dns_server [-d <dns-server>]
```

> To list a DNS server set:
```
dnslsdnsserver dns_server_set [-e <dns-server-set>]
```

> To list a DNS server set assignment:
```
dnslsdnsserver assignment [-d <dns-server>] [-e <dns-server-set>]
```


> ### dnsrmdnsserver ###
> To remove a DNS server:
```
dnsrmdnsserver dns_server -d <dns-server>
```

> To remove a DNS server set:
```
dnsrmdnsserver dns_server_set -e <dns-server-set>
```

> To remove a DNS server set assignment:
```
dnsrmdnsserver assignment -d <dns-server> -e <dns-server-set>
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--force               Force actions to complete.
-d DNS_SERVER, --dns-server=DNS_SERVER
                      DNS server.
-e DNS_SERVER_SET, --dns-server-set=DNS_SERVER_SET
                      DNS server set.
```


## Host ##
A host is a tool to shortcut creating an A/AAAA record coupled with a PTR record.


> ### dnsmkhost ###
> To make a host:
```
dnsmkhost add --ip-address <ip-address> -t <target>
-z <zone-name> [--ttl <ttl>] [-v <view-name>]
```

> To make a host with an automatically assigned IP address:
```
dnsmkhost findfirst --cidr-block <cidr-block> -t <target>
-z <zone-name> [--ttl <ttl>] [-v <view-name>]
```


> ### dnslshost ###
> To list hosts by CIDR:
```
dnslshost cidr --cidr-block <cidr-block> [-v <view-name>]
[-z <zone-name>]
```

> To list hosts by zone:
```
dnslshost zone -z <zone-name> [-v <view-name>]
```


> ### dnsrmhost ###
> To remove a host:
```
dnsrmhost --ip-address <ip-address> -t <target>
-z <zone-name> [--ttl <ttl>] [-v <view-name>]
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--force               Force actions to complete.
-i <ip-address>, --ip-address=<ip-address>
                      Full IP address of machine.
-t <target>, --target=<target>
                      String of machine host name. (Not FQDN)
--ttl=<ttl>           Time for host to live before being refreshed.
-z <zone-name>, --zone-name=<zone-name>
                      String of the zone name.
-v <view-name>, --view-name=<view-name>
                      String of the view name <view-name>. Example:
                      "internal"
```


## CNAMEs ##
A CNAME is an alias for a host name.


> ### dnslscnames ###
> To list all CNAMEs for a specified hostname:
```
dnslscnames cname --hostname <hostname> -v <view-name> -z <zone-name> [-r]
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
--no-header           Do not display a header.
--hostname <hostname> String of hostname
-z <zone-name>, --zone-name=<zone-name>
                      String of the zone name.
-v <view-name>, --view-name=<view-name>
                      String of the view name <view-name>. Example:
                      "internal"
-r, --recursive       Use recursion during lookup
```


## Record ##
Records are used to define zones. They can be of the following types:
  * IPv4 (**A**)
  * IPv6 (**AAAA**)
  * Pointer (**PTR**)
  * Canonical Name (**CNAME**)
  * Host Information (**HINFO**)
  * Text (**TXT**)
  * Start of Authority (**SOA**)
  * Service (**SRV**)
  * Name Server (**NS**)
  * Mail Exchanger (**MX**).


> ### dnsmkrecord ###
> To make an "A" record (IPv4 forward):
```
dnsmkrecord a --assignment-ip <ipv4-address> -z <zone-name>
-t <hostname>
```

> To make an "AAAA" record (IPv6 forward):
```
dnsmkrecord aaaa --assignment-ip <ipv6-address> -z <zone-name>
-t <hostname>
```

> To make a "PTR" record (reverse):
```
dnsmkrecord ptr --assignment-host <full-hostname> -z <zone-name>
-t <ipv4/6-address>
```

> To make a "CNAME" record (alias):
```
dnsmkrecord cname --assignment-host <alias-hostname> -z <zone-name>
-t <hostname>
```

> To make an "HINFO" record (hardware info):
```
dnsmkrecord hinfo --hardware <hardware-info> --os <operating-system>
-z <zone-name> -t <hostname>
```

> To make a "TXT" record (text):
```
dnsmkrecord txt --quoted-text <text> -z <zone-name> -t <hostname>
```

> To make an "SOA" record (start of authority):
```
dnsmkrecord soa --admin-email <admin-email> --name-server <name-server>
--serial-number <serial-number> --refresh-seconds <refresh-seconds>
--retry-seconds <retry-seconds> --expiry-seconds <expiry-seconds>
--minimum-seconds <minimum-seconds> -z <zone-name> -t <hostname>
--view-name <view-name>
```

> To make an "SRV" record (service):
```
dnsmkrecord srv --priority <priority> --weight <weight> --port <port>
--assignment-host <full-hostname> -z <zone-name> -t <hostname>
```

> To make an "NS" record (nameserver):
```
dnsmkrecord ns --name-server <full-hostname> -z <zone-name> -t <hostname>
```

> To make an "MX" record (mail):
```
dnsmkrecord mx --mail-server <full-hostname> --priority <priority>
-z <zone-name> -t <hostname>
```


> ### dnslsrecord ###
> To list an "A" record (IPv4 forward):
```
	dnslsrecord a --assignment-ip <ipv4-address> -z <zone-name>
-t <hostname>
```

> To list a "AAAA" record (IPv6 forward):
```
dnslsrecord aaaa --assignment-ip <ipv6-address> -z <zone-name>
-t <hostname>
```

> To list a "PTR" record (reverse):
```
dnslsrecord ptr --assignment-host <full-hostname> -z <zone-name>
-t <ipv4/6-address>
```

> To list a "CNAME" record (alias):
```
dnslsrecord cname --assignment_host <alias_hostname> -z <zone-name>
-t <hostname>
```

> To list an "HINFO" record (hardware info):
```
dnslsrecord hinfo --hardware <hardware-info> --os <operating-system>
-z <zone-name> -t <hostname>
```

> To list a "TXT" record (text):
```
dnslsrecord txt --quoted-text <text> -z <zone-name> -t <hostname>
```

> To list an "SOA" record (start of authority):
```
dnslsrecord soa --admin-email <admin-email> --name-server <name-server>
--serial-number <serial-number> --refresh-seconds <refresh-seconds>
--retry_seconds <retry-seconds> --expiry-seconds <expiry-seconds>
--minimum-seconds <minimum-seconds> -z <zone-name> -t <hostname>
```

> To list an "SRV" record (service):
```
dnslsrecord srv --priority <priority> --weight <weight> --port <port>
--assignment-host <full-hostname> -z <zone-name> -t <hostname>
```

> To list an "NS" record (nameserver):
```
dnslsrecord ns --name-server <full-hostname> -z <zone-name>
 -t <hostname>
```

> To list an "MX" record (mail):
```
dnslsrecord mx --mail-server <full-hostname> --priority <priority>
-z <zone-name> -t <hostname>
```

> To list all record types:
```
dnslsrecord all -z <zone-name> -t <hostname>
```


> ### dnsrmrecord ###
> To remove an "A" record (IPv4 forward):
```
dnsrmrecord a --assignment-ip <ipv4-address> -z <zone-name>
-t <hostname>
```

> To remove a "AAAA" record (IPv6 forward):
```
dnsrmrecord aaaa --assignment-ip <ipv6-address> -z <zone-name>
-t <hostname>
```

> To remove a "PTR" record (reverse):
```
dnsrmrecord ptr --assignment-host <full-hostname> -z <zone-name>
-t <ipv4/6-address>
```

> To remove a "CNAME" record (alias):
```
dnsrmrecord cname --assignment_host <alias_hostname> -z <zone-name>
-t <hostname>
```

> To remove an "HINFO" record (hardware info):
```
dnsrmrecord hinfo --hardware <hardware-info> --os <operating-system>
-z <zone-name> -t <hostname>
```

> To remove a "TXT" record (text):
```
dnsrmrecord txt --quoted-text <text> -z <zone-name> -t <hostname>
```

> To remove an "SOA" record (start of authority):
```
dnsrmrecord soa --admin-email <admin-email> --name-server <name-server>
--serial-number <serial-number> --refresh-seconds <refresh-seconds>
--retry_seconds <retry-seconds> --expiry-seconds <expiry-seconds>
--minimum-seconds <minimum-seconds> -z <zone-name> -t <hostname>
```

> To remove an "SRV" record (service):
```
dnsrmrecord srv --priority <priority> --weight <weight> --port <port>
--assignment-host <full-hostname> -z <zone-name> -t <hostname>
```

> To remove an "NS" record (nameserver):
```
dnsrmrecord ns --name-server <full-hostname> -z <zone-name> -t <hostname>
```

> To remove an "MX" record (mail):
```
dnsrmrecord mx --mail-server <full-hostname> --priority <priority>
-z <zone-name> -t <hostname>
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--assignment-ip=<assignment-ip>
                      (A, AAAA) String of the IP address
--hardware=<hardware>
                      (HINFO) String of the hardware type.
--os=<os>             (HINFO) String of the OS type.
--quoted-text=<quoted-text>
                      (TXT) String of quoted text.
--assignment-host=<hostname>
                      (CNAME, PTR, SRV) String of the hostname.
--name-server=<name-server>
                      (SOA,NS) String of the hostname of the name server.
--admin-email=<admin-email>
                      (SOA) String of the admin email address.
--serial-number=<serial-number>
                      (SOA) Integer of the serial number.
--refresh-seconds=<refresh-seconds>
                      (SOA) Integer of number of seconds to refresh.
--retry-seconds=<retry-seconds>
                      (SOA) Integer of number of seconds to retry.
--expiry-seconds=<expiry-seconds>
                      (SOA) Integer of number of seconds to expire.
--minimum-seconds=<minumum-seconds>
                      (SOA) Integer of minium number of seconds to refresh.
--priority=<priority>
                      (SRV, MX) Integer of priority between 0-65535.
--weight=<weight>     (SRV) Integer of weight between 0-65535.
--port=<port>         (SRV) Integer of port number.
--mail-server=<hostname>
                      (MX) String of mail server hostname.
-z <zone-name>, --zone-name=<zone-name>
                      String of the <zone-name>. Example:
                      "sub.university.edu"
-t <target>, --target=<target>
                      String of the target. "A" record example:
                      "machine-01", "PTR" record example: 192.168.1.1
--ttl=<ttl>           Time for host to be cached before being refreshed.
-v <view-name>, --view-name=<view-name>
                      String of view name.
```


## Reserved Word ##
Reserved words are keywords that cannot be used in the names of various types. **In order for reserved words to be enforced, Roster Core's cache must be refreshed or Roster Core must be restarted.**


> ### dnsmkreservedword ###
> To make a reserved word:
```
dnsmkreservedword -w <reserved-word>
```


> ### dnslsreservedword ###
> To list reserved words:
```
dnslsreservedword
```


> ### dnsrmreservedword ###
> To remove a reserved word:
```
dnsrmreservedword -w <reserved-word>
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--force               Force actions to complete.
-w <word>, --word=<word>
                      The reserved word.
```

## User and Group ##
This helps manage users and groups of users and control permissions for Roster's users.


> ### dnsmkusergroup ###
> To make a user:
```
dnsmkusergroup user -n <user-name> -a <access-level>
```

> To make a group:
```
dnsmkusergroup group -g <group>
```

> To make a user group assignment:
```
dnsmkusergroup assignment -n <user-name> -g <group>
```

> To make a forward zone permission:
```
dnsmkusergroup forward -z <zone-name> -g <group>
--group-permission <group-permission>
```

> To make a reverse range permission:
```
dnsmkusergroup reverse -z <zone-name> -b <cidr-block> -g <group>
--group-permission <group-permission>
```


> ### dnslsusergroup ###
> To list a user:
```
dnslsusergroup user -n <user-name> -a <access-level>
```

> To list a group:
```
dnslsusergroup group -g <group>
```

> To list a user group assignment:
```
dnslsusergroup assignment -n <user-name> -g <group>
```

> To list a forward zone permission:
```
dnslsusergroup forward -z <zone-name> -g <group>
--group-permission <group-permission>
```

> To list a reverse range permission:
```
dnslsusergroup reverse -z <zone-name> -b <cidr-block> -g <group>
--group-permission <group-permission>
```


> ### dnsrmusergroup ###
> To remove a user:
```
dnsrmusergroup user -n <user-name>
```

> To remove a group:
```
dnsrmusergroup group -g <group>
```

> To remove a user group assignment:
```
dnsrmusergroup assignment -n <user-name> -g <group>
```

> To remove a forward zone permission:
```
dnsrmusergroup forward -z <zone-name> -g <group>
--group-permission <group-permission>
```

> To remove a reverse range permission:
```
dnsrmusergroup reverse -z <zone-name> -b <cidr-block> -g <group>
--group-permission <group-permission>
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--force               Force actions to complete.
-n <new-user>, --new-user=<new-user>
                      String of the new user to create.
-a <access-level>, --access-level=<access-level>
                      Access level of new user.
-g <group>, --group=<group>
                      String of the group name to create or assign.
-z <zone>, --zone-name=<zone>
                      String of the zone name (optional)
--group-permission=<group-permission>    Comma-separated group permissions, i.e., a,aaaa,cname,ns,soa,srv
-b <cidr-block>, --cidr-block=<cidr-block>
                      String of CIDR block.
```

### Access Levels and Permissions ###

The above example use access levels for users and permissions for groups outlined in the [Access Levels and Permissions](AccessLevelsAndPermissions.md) page. Please refer to it for some specific examples and usage.

## View ##
Views control what permissions hosts have based on their location. Use these tools to: make, list, and remove views, server sets, acl assignments, and view assignments.


> ### dnsmkview ###
> To make views:
```
dnsmkview view -v <view-name> -a <acl>
[--allow/--deny] [-o <options>]
```

> To make DNS server set view assignments:
```
dnsmkview dns_server_set -v <view-name> 
-e <dns-server-set> -r <view-name>
```

> To make ACL view assignments:
```
dnsmkview acl -v <view-name> -a <acl-name> [--allow/--deny]
```

> To make view assignments:
```
dnsmkview view_subset -v <view-superset-name>
-V <view-subset-name> [--allow/--deny]
```
> Note: Both the view and the view-dependency must exist within Roster to use this tool.


> ### dnslsview ###
> To list views:
```
dnslsview view [-v <view-name>]
```

> To list DNS server set view assignments:
```
dnslsview dns_server_set [-v <view-name>] [-e <dns-server-set>]
```

> To list ACL view assignments:
```
dnslsview acl [-v <view-name>] [-a <acl-name>]
```

> To list view assignments:
```
dnslsview view_subset [-v <view-superset-name>]
[-V <view-subset-name>]
```


> ### dnsrmview ###
> To remove views:
```
dnsrmview view -v <view-name> [-o <options>]
```

> To remove DNS server set view assignments:
```
dnsrmview dns_server_set -v <view-name> -e <dns-server-set>
```

> To remove ACL view assignments:
```
dnsrmview acl -v <view-name> -a <acl-name> [--allow/--deny]
```

> To remove view assignments:
```
dnsrmview view_subset -v <view-superset-name>
-V <view-subset-name>
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--force               Force actions to complete.
-v VIEW_NAME, --view-name=VIEW_NAME
                      String of view.
-V VIEW_SUBSET, --view-dep=VIEW_SUBSET
                      String of view dependency.
-o <options>, --options=<options>
                      View options.
-e DNS_SERVER_SET, --dns-server-set=DNS_SERVER_SET
                      String of dns server set name.
-r VIEW_ORDER, --view-order=VIEW_ORDER
                      View order in named.conf
-a ACL, --acl=ACL     String of access control list name.
--allow               Allow ACL in view.
--deny                Deny ACL in view.
```


## Zone ##
Zones define mappings between domain names and IP addresses. Use these tools to make, list, and remove forward and reverse zones.


> ### dnsmkzone ###
> To make forward zones:
```
dnsmkzone forward -z <zone-name> -v <view-name> --origin <origin>
-t <type> [-o <options>]
```

> To make reverse zones:
```
dnsmkzone reverse -z <zone-name> -v <view-name> -t <type>
(--origin <origin> | --cidr-block <cidr-block>)
[-o <options>]
```


> ### dnslszone ###
> To list all zones:
```
dnslszone all
```

> To list forward zones:
```
dnslszone forward [-z <zone-name>] [-v <view-name>] [-0 <options>]
[--origin <origin>] [-t <type>]
```

> To list reverse zones:
```
dnslszone reverse [-z <zone-name>] [-v <view-name>] [-0 <options>]
[--origin <origin>] [-t <type>] [--cidr-block <cidr-block>]
```


> ### dnsrmzone ###
> To remove zones:
```
dnsrmzone -z <zone-name> -v <view-name>|--force
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--force               Force actions to complete.
-v VIEW_NAME, --view-name=VIEW_NAME
                      String of view name.
-z ZONE_NAME, --zone-name=ZONE_NAME
                      String of zone name.
```


## Set Maintenance ##
Use this tool to control the maintenance mode of the database. When on, the database **cannot** be dumped to BIND files.


> ### dnssetmaintenance ###
> To turn maintenance mode on:
```
dnssetmaintenance set --on
```

> To turn maintenance mode off:
```
dnssetmaintenance set --off
```

> To list current maintenance status:
```
dnssetmaintenance list
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
--on                  Turn Roster maintenance mode on.
--off                 Turn Roster maintenance mode off.
```


## Mass Record Handling ##
Mass record handling is for easily working with large, already generated zone files.

> ## dnsmassadd ##
> To add a list of hosts from a file:
```
dnsmassadd -f <file-name> -v <view-name> -z <zone-name>
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
--commit              Commits changes of hosts file without confirmation.
--no-commit           Suppresses changes of hosts file.
-z <zone-name>, --zone-name=<zone-name>
                      String of the zone name.
-v <view-name>, --view-name=<view-name>
                      String of the view name <view-name>. Example:
                      "internal"
-f <file-name>, --file=<file-name>
                      File name of hosts file to write to database.
```

> ## dnsaddformattedrecords ##
> To add records:
```
dnsaddformattedrecords -f <records-file> -z <zone-name> [-v <view-name>]
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
-q, --quiet           Suppress program output.
-v VIEW_NAME, --view-name=VIEW_NAME
                      String of view name.
-f RECORDS_FILE, --records-file=RECORDS_FILE
                      Records file location.
-z ZONE_NAME, --zone-name=ZONE_NAME
                      String of zone name.
```

> ### dnsuphosts ###
> To dump a text hosts file of a CIDR-block:
```
dnsuphosts dump -r <cidr-block> [-f <file-name>] [-v <view-name>]
[-z <zone-name>]
```

> To update a CIDR block at once:
```
dnsuphosts update [-f <file-name>] [-v <view-name]
[-z <zone-name>] [--commit|--no-commit]
```

> To dump and update a CIDR block:
```
dnsuphosts edit -r <cidr_block> [-f <file-name>] [-v <view-name>]
[-z <zone-name>] [--commit|--no-commit]
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
--keep-output         Keep output file.
--commit              Commits changes of hosts file without confirmation.
--no-commit           Suppresses changes of hosts file.
-r <range>, --range=<range>
                      CIDR block range of IP addresses. Assumes -l, will
                      only print a list of ip addresses. Example:
                      10.10.0.0/24
--ttl=<ttl>           Time to live.
-z <zone-name>, --zone-name=<zone-name>
                      String of the zone name.
-v <view-name>, --view-name=<view-name>
                      String of the view name <view-name>. Example:
                      "internal"
-f <file-name>, --file=<file-name>
                      File name of hosts file to write to database.
```


## Named Globals ##
Use dnsupnamedglobals to view, modify, and edit named global confs.


> ### dnsupnamedglobals ###
> To list avalible named global configurations:
```
dnsupnamedglobals list -d <dns-server-set>
```

> To dump a configuration:
```
dnsupnamedglobals dump [-i <option-id> | (-d <dns-server-set> -t <timestamp>)]
```
> > Note: If option-ID is not specified, use latest configuration.


> To edit a configuration:
```
dnsupnamedglobals edit [-i <option-id> | (-d <dns-server-set> -t <timestamp>)]
```
> > Note: If option-ID is not specified, use latest configuration.


> To update to an existing file:
```
dnsupnamedglobals update -d <dns-server-set> [-f <file-name>]
```

> To revert a change:
```
dnsupnamedglobals revert -d <dns-server-set> -i <option-id>
```


> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-u <username>, --username=<username>
                      Run as different username.
-p <password>, --password=<password>
                      Password string, NOTE: It is insecure to use this flag
                      on the command line.
--cred-string=<cred-string>
                      String of credential.
-s <server>, --server=<server>
                      XML RPC Server URL.
-c <cred-file>, --cred-file=<cred-file>
                      Location of credential file.
--config-file=<file>  Config file location.
--keep-output         Keep output file.
-d <dns-server-set>, --dns-server-set=<dns-server-set>
                      String of the dns server set name.
-i <option-id>, --option-id=<option-id>
                      Integer of option id.
-t <timestamp>, --timestamp=<timestamp>
                      String of timestamp in YYYY/MM/DD/HH/MM/SS format.
-q, --quiet           Suppress program output.
-f <file-name>, --file=<file-name>
                      File name of named header dump.
--no-header           Do not display a header.
```