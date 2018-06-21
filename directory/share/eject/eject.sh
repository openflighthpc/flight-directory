#!/bin/bash
#ALCES_META
# Refer to `clusterware/scripts/development/propagate`.
#path=/opt/directory/bin/eject.sh
#ALCES_META_END
set -euo pipefail
IFS=$'\n\t'


# Script to the actual shell commands to eject the appliance, without
# performing any checks of the eject code.


IPA_BLOCK_CONFIG=/etc/httpd/conf.d/00-ipa-block.conf

# Remove the httpd config file that blocks most FreeIPA access.
sudo rm -f "$IPA_BLOCK_CONFIG"
sudo systemctl reload httpd

# Modify `flight` SSH config to allow normal SSH access, rather than dropping
# user straight into Directory CLI sandbox.
sudo sed -i \
  -e 's#command="/opt/directory/cli/bin/sandbox-starter" ##g' \
  /home/flight/.ssh/authorized_keys
