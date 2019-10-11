# Flight Directory

A sandbox CLI for simplifying management of user directory services with IPA.

## Overview

- Interactive login shell (replacing `/bin/bash` for the designated admin users)

  - Tab completion menu
  - Intuitive fade of cancelled commands

- IPA command wrappers (reducing complexity of adding users, etc)

## Installation

### Configuring Flight Directory on IPA Server

Note: This does not setup an IPA server, that must be done
separately. For more information on setting up an IPA server see the
[FreeIPA project](https://www.freeipa.org/).

 * Install dependencies

   ```
   yum install apg
   ```

   (Optional requirement for the `password-generator` script)

 * Clone the repository

   ```
   git clone https://github.com/openflighthpc/flight-directory /tmp/flight-directory
   ```

 * Copy the code into `/opt/`

   ```
   rsync -auv /tmp/flight-directory/{directory,share} /opt/
   ```

 * Setup the Python environment

   ```
   cd /opt/directory/cli
   make setup
   ```

## Configuration

 * Add IPA password to configuration

   ```
   mkdir /opt/directory/etc
   echo "IPAPASSWORD=MyIPApassHere" > /opt/directory/etc/config
   ```

 * Add IPA server address to configuration (replace `infra01.testnet.alces.network` with the IPA server FQDN)

   ```
   echo 'cw_ACCESS_fqdn=infra01.testnet.alces.network' > /opt/directory/etc/access.rc
   ```

 * [OPTIONAL] Create user defaults

   ```
   cat << EOF > /opt/directory/etc/user_config
   DO_NOT_GENERATE_PASSWORD=TRUE
   DEFAULT_GID=987654321

   POST_CREATE_SCRIPT=/path/to/post-create-script.sh
   POST_DELETE_SCRIPT=/path/to/post-delete-script.sh
   POST_MEMBER_ADD_SCRIPT=/path/to/post-member-add-script.sh
   POST_MEMBER_REMOVE_SCRIPT=/path/to/post-member-remove-script.sh
   ```

 * Create output directory for export

   ```
   mkdir -p /var/www/html/secure
   ```

 * Create a user for managing IPA

   ```
   useradd -s /opt/directory/cli/bin/sandbox-starter useradmin
   passwd useradmin
   ```

 * Grant sudo permissions to the user

   ```
   sudoedit /etc/sudoers
       useradmin ALL=(ALL) NOPASSWD:ALL
   ```

# Contributing

Fork the project. Make your feature addition or bug fix. Send a pull
request. Bonus points for topic branches.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

# Copyright and License

Eclipse Public License 2.0, see [LICENSE.txt](LICENSE.txt) for details.

Copyright (C) 2019-present Alces Flight Ltd.

This program and the accompanying materials are made available under
the terms of the Eclipse Public License 2.0 which is available at
[https://www.eclipse.org/legal/epl-2.0](https://www.eclipse.org/legal/epl-2.0),
or alternative license terms made available by Alces Flight Ltd -
please direct inquiries about licensing to
[licensing@alces-flight.com](mailto:licensing@alces-flight.com).

Flight Directory is distributed in the hope that it will be
useful, but WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER
EXPRESS OR IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR
CONDITIONS OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR
A PARTICULAR PURPOSE. See the [Eclipse Public License 2.0](https://opensource.org/licenses/EPL-2.0) for more
details.
