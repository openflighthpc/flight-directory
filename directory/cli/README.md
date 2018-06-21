
# Directory CLI

This directory contains the Directory CLI tool, designed to be installed within
a Flight Directory appliance to perform user and group management tasks.

## Development

Tasks to help in development are defined in the [Makefile](./Makefile).  For
example:

  - To setup an existing Directory appliance in order to develop locally, while
    testing remotely on the appliance:

    ```bash
    make rsync IP=$DIRECTORY_IP
    make remote-run IP=$DIRECTORY_IP COMMAND='make development-setup'
    ```

  - To run tests: `make unit-test`, `make functional-test`, or run all with
    `make test`. These can all be run on the appliance by locally running `make
    remote-run` (as above); this also syncs across local changes first.

  - To keep local changes synced to the appliance as you make them (requires
    [rerun](https://github.com/alexch/rerun)):

  ```bash
  make watch-rsync IP=$DIRECTORY_IP
  ```
