#summary Usage of Roster Config Manager
# Roster Config Manager #
This is a collection of tools that check validity of BIND files, push BIND files to their appropriate servers, and recover the database to a previous state.




**Note about installation path:**
The scripts used on this page are default installed by setuptools to **_prefix_/bin**
prefix is default **_/usr_**. However, this might be different depending on the system.
If you'd like to find out what **_prefix_** is for your system, open up a python shell and type:
```
  Python 2.6.6 (r266:84292, Sep 12 2011, 14:03:14) 
  [GCC 4.4.5 20110214 (Red Hat 4.4.5-6)] on linux2
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import sys
  >>> sys.exec_prefix
  '/usr'
```
If you'd like to know more, please consult [Installing Python Modules](http://docs.python.org/install/index.html#inst-alt-install,).
From this point forward, it is expected that the scripts are installed in a directory in your $PATH.

## Basic Usage ##
1. The database needs to be exported to a staging area first. To dump the database into BIND files, use [dnstreeexport](ConfigManagerUsage#dnstreeexport.md):
```
# dnstreeexport
```

2. Before sending the BIND files to each respective server, check the configuration integrity each time. To check the zone and named.conf configuration files, use [dnscheckconfig](ConfigManagerUsage#dnscheckconfig.md):
```
# dnscheckconfig
```

3. Before sending the BIND files to each respective server, check that each DNS server is online, can be reached, and has proper directories and permissions present. To check DNS servers, user [dnsservercheck](ConfigManagerUseage#dnsservercheck.md):

```
# dnsservercheck
```

4. Now send the BIND files out to each server. To export the configuration to the appropriate servers, use [dnsconfigsync](ConfigManagerUsage#dnsconfigsync.md):
```
# dnsconfigsync
```

5. Now that dnsconfigsync finished successfully, check that the DNS servers are online and operating correctly. To check that zone files are correctly loaded, use [dnsquerycheck](ConfigManagerUsage#dnsquerycheck.md):
```
# dnsquerycheck
```

Or, to automate the process, run [dnsexportconfig](ConfigManagerUsage#dnsexportconfig.md):
```
# dnsexportconfig
```

# Commands #
Each command's usage can be viewed by adding the **`--help`** flag.

## dnstreeexport ##
Dump the Roster configuration tree to bz2 files.
> To export all bind trees:
```
dnstreeexport [-c <config-file>] [-f] [-q]
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-c <config-file>, --config-file=<config-file>
                      Config File Location
-f, --force           Export trees even if nothing has changed in the
                      database.
-q, --quiet           Suppress program output.
```

## dnscheckconfig ##
Uses BIND's named-checkconf and named-checkzone binaries to validate named configuration and zone files.
> To check config files:
```
dnscheckconfig [-i <audit-id>] [--config-file <config-file>]
[-z <checkzone-binary>] [-c <checkconf-binary>] [-v]
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-d <directory>, --directory=<directory>
                      Directory to scan.
-o OUTPUT_DIRECTORY, --output-directory=OUTPUT_DIRECTORY
                      Directory to temporarily output files to. Must be same
                      in named.conf.
-z NAMED_CHECKZONE, --named-checkzone=NAMED_CHECKZONE
                      Location of named_checkzone binary.
-c NAMED_CHECKCONF, --named-checkconf=NAMED_CHECKCONF
                      Location of named_checkconf binary.
-v, --verbose         Make command verbose.
--config-file=<config-file>
                      Config File Location
-i <id>, --id=<id>    ID of tarfile output from Roster tree export.
```

## dnsservercheck ##
Checks that each DNS server is online, can be reached, and has proper directories and permissions present.
> To check a DNS server:
```
dnsservercheck -d <dns-server> [-c <config-file>] [-i <audit-id>]
```

> ### Options ###
```
  --version             show programs version number and exit
  -h, --help            show this help message and exit
  --export-config       This flag is used when dnsservercheck is called from
                        dnsexportconfig. This should not be used by any user.
  -d <dns-server>, --dns-server=<dns-server>
                        DNS Server to check.
  -c <config-file>, --config-file=<config-file>
                        Roster Server Config File Location.
  -i <audit-id>, --id=<audit-id>
                        Audit Log ID for the tarfile output from Roster tree
                        export
```

## dnsconfigsync ##
SSH's BIND files to, and rndc reloads, appropriate servers.
> To sync bind trees:
```
dnsconfigsync -i <audit-id> [-c <config-file>] [-d <dest-directory>]
[-u <rsync-user>] [-p <rsync-port>]
```

> ### Options ###
```
  --version             show programs version number and exit
  -h, --help            show this help message and exit
  --export-config       This flag is used when dnsconfigsync is called from
                        dnsexportconfig. This should not be used by any user.
  -d <dns-server>, --dns-server=<dns-server>
                        DNS Server Name
  -c <config-file>, --config-file=<config-file>
                        Config File Location
  -i <id>, --id=<id>    ID of tarfile output from Roster tree export.
  --ssh-id=<ssh-id>     SSH id file.
  --rndc-exec=<rndc-exec>
                        RNDC executable location.
  --rndc-key=<rndc-key>
                        RNDC key file.
  --rndc-conf=<rndc-conf>
                        RNDC conf file.
  --rndc-port=<rndc-port>
                        RNDC communication port. If none provided, named.conf
                        will be parsed to find one. If one can not be found,
                        953 will be used.
  --ssh-failure-retries=TRIES
                        Number of times to retry config syncing should an SSH
                        error (e.g. timeout) occur. Defaults to 3.
```

## dnsquerycheck ##
Queries a DNS server to make sure it is online and serving the correct zone files.

> To test a DNS server:
```
	/usr/bin/dnsquerycheck -c <config-file> -i <audit-log-id> -s <dns-server> (-z <zone-name>) (-v <view-name>) or
	/usr/bin/dnsquerycheck -f <zone-file> -s <dns-server>
```

> ### Options ###
```
  --version             show programs version number and exit
  -h, --help            show this help message and exit
  --export-config       This flag is used when dnsquerycheck is called from
                        dnsexportconfig. This should not be used by any user.
  -c <config_file>, --config-file=<config_file>
                        Roster Server config file
  -i <id>, --id=<id>    Audit log ID
  -d <server>, --dns-server=<server>
                        DNS server to query.
  -p <port>, --port=<port>
                        Port to query DNS server on.
  -n <number>, --number=<number>
                        Number of random records to query for. Default=5 To
                        query all records, use -n 0
  -f <zone_file>, --file=<zone_file>
                        Zone file to use for queries, instead of audit log id.
  -v <view_name>, --view=<view_name>
                        Check only a specific view. (optional)
  -z <zone_name>, --zone=<zone_name>
                        Check only a specific zone. (optional)
```

## dnsexportconfig ##
Exports trees, checks named configurations and zones, and syncs the configuration with the appropriate servers. Essentially, this command will run [dnstreeexport](ConfigManagerUsage#dnstreeexport.md), [dnscheckconfig](ConfigManagerUsage#dnscheckconfig.md), [dnsservercheck](ConfigManageUsage#dnsservercheck.md), [dnsconfigsync](ConfigManagerUsage#dnsconfigsync.md), and [dnsquerycheck](ConfigManagerUsage#dnsquerycheck.md)
> To export database to config files:
```
dnsexportconfig [-d <output-directory>] [-f]
[--config-file <config-file>] [-t <tree-exporter-executable>]
[-c <check-config-executable>] [-s <config-sync-excutable>]
[--named-checkzone <named-checkzone-executable>
[--named-checkconf <named-checkconf-executable>
```

> ### Options ###
```
  --version             show programs version number and exit
  -h, --help            show this help message and exit
  -i <audit-id>, --id=<audit-id>
                        ID of tarfile output from Roster tree export.
  -c <config-file>, --config-file=<config-file>
                        Roster config file location.
  -q, --quiet           Suppress program output.
  --tree-exporter=TREE_EXPORT
                        Location of "dnstreeexport" binary.
  --check-config=CHECK_CONFIG
                        Location of "dnscheckconfig" binary.
  --server-check=SERVER_CHECK
                        Location of "dnsservercheck" binary.
  --config-sync=CONFIG_SYNC
                        Location of "dnsconfigsync" binary.
  --query-check=QUERY_CHECK
                        Location of "dnsquerycheck" binary.
  -f, --force           (dnstreeexport)Export trees even if nothing has
                        changed in the database.
  --named-checkzone=NAMED_CHECKZONE
                        (dnscheckconfig)Location of named_checkzone binary.
  --named-checkconf=NAMED_CHECKCONF
                        (dnscheckconfig)Location of named_checkconf binary.
  --ssh-id=<ssh-id>     (dnsconfigsync)SSH id file.
  --rndc-exec=<rndc-exec>
                        (dnsconfigsync)Rndc executable location.
  --rndc-key=<rndc-key>
                        (dnsconfigsync)Rndc key file.
  --rndc-conf=<rndc-conf>
                        (dnsconfigsync)Rndc conf file.
  --rndc-port=<rndc-port>
                        RNDC communication port.  If none provided, named.conf
                        will be parsed to find one.  If one can not be found,
                        953 will be used.
  -p <port>, --port=<port>
                        (dnsquerycheck)Port to query DNS server on.
  -n <number>, --number=<number>
                        (dnsquerycheck)Number of random records to query for
                        Default=5 To query all records, use '-n all'

```

## dnsrecover ##
Roll back and recover the Roster configuration to a certain audit-ID or remove a certain audit-ID from being performed.
> To recover up to a certain audit ID:
```
dnsrecover -i <id>
```

> To recover a single audit step:
```
dnsrecover -i <id> --single
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-i <id>, --id=<id>    Audit log ID to recover to.
--single              Run single audit rather than a full range.
-u <username>, --username=<username>
                      Run as a different username.
--config-file=<file>  Config file location.
```

## dnszonecompare ##
Compare two similar zones on two nameservers.
> To compare two zone files:
```
dnszonecompare <domain> <nameserver_1>[:port] <nameserver_2>[:port]
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
```

## dnszoneimporter ##
Import zones from a zone file into Roster.
> To import zone files:
```
dnszoneimporter [-c <config-file>] -z <zone-view> -v <records-view>
(-d <directory> | -f <file>) [-u <username>]
```

> ### Options ###
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-c <config-file>, --config-file=<config-file>
                      Database config file.
-d <directory>, --directory=<directory>
                      Directory of zone files to load in. Mutually exclusive
                      from -f/--file
-f <file>, --file=<file>
                      Zone file to load in. Mutually exclusive from
                      -d/--directory.
-v <view>, --view=<view>
                      View to assign zone to. (This cannot be the any view)
--use-specific-view   Records will be put in the any view unless this flag
                      is used. If the flag is set records will go to the
                      view specified with the -v flag.
-u <user_name>, --username=<user_name>
                      Override default username.
```