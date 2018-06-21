# Userware
A sandbox CLI for simplifying management of IPA

## Features of Userware

- Interactive login shell (replacing `/bin/bash` for the designated admin users)

  - Tab completion menu
  - Intuitive fade of cancelled commands

- IPA command wrappers (reducing complexity of adding users, etc)

## Source

Currently this repository is just a collection of the code from [Imageware](https://github.com/alces-software/imageware), specifically:

- `directory/{cli,bin}`
- `share/appliance_cli`

## Configuring Userware on IPA Server

Note: This does not setup an IPA server, that must be done separately. For more information on setting up an IPA server see the [Cluster Platform Knowledgebase instructions](http://cluster-platform-knowledgebase.readthedocs.io/en/latest/user-management/user-management-guidelines.html#ipa-server-setup)

- Clone the repository

```
git clone https://github.com/alces-software/userware /tmp/userware
```

- Copy userware into `/opt/`

```
rsync -auv /tmp/userware/{directory,share} /opt/
```

- Setup the Python environment

```
cd /opt/directory/cli
make setup
```

- Add IPA password to configuration

```
mkdir /opt/directory/etc
echo "IPAPASSWORD=MyIPApassHere" > /opt/directory/etc/config
```

- Create a user for managing IPA

```
useradd -s /opt/directory/cli/bin/sandbox-starter ipaadmin
passwd ipaadmin
```

- Grant sudo permissions to the user

```
sudoedit /etc/sudoers
    ipaadmin ALL=(ALL) NOPASSWD:ALL
```
