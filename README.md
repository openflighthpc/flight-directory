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

- Add IPA server address to configuration (replace `infra01.testnet.alces.network` with the IPA server FQDN)

```
echo 'cw_ACCESS_fqdn=infra01.testnet.alces.network' > /opt/directory/etc/access.rc
```

- [OPTIONAL] Create user defaults

```
cat << EOF > /opt/directory/etc/user_config
DO_NOT_GENERATE_PASSWORD=TRUE
DEFAULT_GID=987654321
POST_CREATE_SCRIPT=/path/to/myscript.sh
```

- Create output directory for export

```
mkdir -p /var/www/html/secure
```

- Create a user for managing IPA

```
useradd -s /opt/directory/cli/bin/sandbox-starter useradmin
passwd useradmin
```

- Grant sudo permissions to the user

```
sudoedit /etc/sudoers
    useradmin ALL=(ALL) NOPASSWD:ALL
```
