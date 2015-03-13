#summary Details Roster Core and Roster Server installation and usage.
#labels Phase-Deploy




# Introduction #

Installing Roster Core and Roster Server is an easy task as long as the dependencies are met. The procedure to install and use Roster is shown below. **It is recommended to have basic knowledge of DNS, BIND, and [Roster itself](About.md).**


# Prerequisites #
  * Python 2.5
  * MySQL
  * Python Setup Tools 0.6c9
  * BIND 9
### Packages and dependencies as they show up in CentOS 5.6 repo ###
  * bind97
    * openssl
  * python-setuptools
  * mysql-server
  * mysql-python
    * mysql-devel
    * openldap-devel
    * python-devel
  * pyopenssl
    * openssl
    * python-devel
  * python-ldap
    * openldap-clients
    * openldap-devel
    * python-devel
### Packages and dependencies as they show up in RedHat 6 repo ###
  * bind
    * openssl
  * python-setuptools
  * mysql-server
  * python-ldap
    * openldap-clients
    * openldap-devel
    * python-devel
### Packages and dependencies as they show up in Ubuntu 11.04 repo ###
  * mysql-server
    * libncurses5
    * libtool
  * bind9
    * penssl
  * python-setuptools
  * python-mysqldb
    * libmysqld-dev
    * libldap2-dev
    * python-dev
  * python-ldap
    * libldap2-dev
    * python-dev
  * python-openssl
    * openssl
    * python-dev


# Installation #

**All of the Roster's components need to be installed separately. Roster's components are not designed to run on a single server, but can if desired.**

For example, a normal setup would have one machine containing Roster Core, Roster Server, and Roster Config Manager, with clients connecting using Roster User Tools.
Another setup, similar to the aforementioned, may have Roster Config Manager on a different machine.
There are many possibilities, and your individual setup will depend on DNS size, among other variables.

To use an authentication module other than LDAP in Roster, a new authentication module must be written before setting up Roster Server. How to write an authentication module can be found on the [authentication page](Authentication.md).


## Installing Roster Components ##

All Roster components require Python Setup Tools for installation found [here](http://pypi.python.org/pypi/setuptools).


### Installing Components by Download ###

Each component of Roster can be installed by navigating to the component's respective root directory, (containing "setup.py") and running the following command:

```
# python setup.py install
```

The setup program will automatically resolve dependencies and install them.

Repeat for each component on its respective machine.


### Installing Components by Easy Install ###

An alternative install method is to use easy\_install to download, build, and install Roster from PyPI automatically.

Roster can be be downloaded directly from PyPI and installed by running the following commands (separately or together) from any directory:
```
# easy_install RosterConfigManager
# easy_install RosterCore
# easy_install RosterServer
# easy_install RosterUserTools
```


# Setting Up and Configuring Roster Components #


## Roster Core ##

[Core installation](CoreInstallation.md)


## Roster Server ##

[Server installation](ServerInstallation.md)


## Roster User Tools ##

[User Tools installation](UserToolsInstallation.md)


## Roster Config Manager ##

[Config Manager installation](ConfigManagerInstallation.md)