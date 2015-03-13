#summary Installation of Roster User Tools

See the Roster User Tools [usage page](UserToolsUsage.md) for more information on the usage of these commands.

## Roster User Tools Setup ##
Installation of Roster User Tools is as follows:

> From pypi:
```
# easy_install RosterUserTools
```

> From source package:
```
# python setup.py install
```

## Bootstrapping UserTools Config ##

After Roster User Tools is installed, it MUST be bootstrapped to create a usertools config file by running: `*# roster-user-tools-bootstrap*`
```
# roster_user_tools_bootstrap -s <server> --config-file <config_file>
```

## More on roster\_user\_tools\_bootstrap ##
Additional options can be configured using special flags visible with: `# *roster_user_tools_bootstrap --help*`
```
--version             show programs version number and exit
-h, --help            show this help message and exit
-s <server>, --server=<server>
                      XML RPC Server URL.
--config-file=<file>  Config file location.
```
The config file can be specified to 2 locations:
  * **_/etc/roster/roster\_user\_tools.conf_**
  * **_~/.rosterrc_**
You can also put it anywhere as long as an environment variable is set like so: `*# export ROSTER_USER_CONFIG=/some/path/to.conf*`

this is an example usertools config file from **`/test/test_data/roster_user_tools.conf`**:
```
[user_tools]

# credential file placement
cred_file = test_data/dnscred

# xml-rpc server host
# be sure to include a full URL such as https://localhost:8000
server = https://localhost:8000
```
For more information on the dnscred file, see the [Credentials](UserToolsUsage#Credential.md) documentation.