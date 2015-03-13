#summary Installation of Roster Config Mananger

See the Roster Config Manager [usage page](ConfigManagerUsage.md) for more on the usage of these commands.

## Roster Config Manager Setup ##
Installation of Roster User Tools is as follows:

> From pypi:
```
# easy_install RosterConfigManager
```

> From source package:
```
# python setup.py install
```

## Importing zones ##
Rather than adding records manually with the user tools, they can also be imported using [dnszoneimporter](ConfigManagerUsage#dnszoneimporter.md) as shown below:
```
# dnszoneimporter -f private.db -z private
```

> Where **`private.db`** is an existing zone file for the private zone.