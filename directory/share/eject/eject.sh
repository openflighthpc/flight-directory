#!/bin/bash
#==============================================================================
# Copyright (C) 2019-present Alces Flight Ltd.
#
# This file is part of Flight Directory.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License 2.0 which is available at
# <https://www.eclipse.org/legal/epl-2.0>, or alternative license
# terms made available by Alces Flight Ltd - please direct inquiries
# about licensing to licensing@alces-flight.com.
#
# Flight Directory is distributed in the hope that it will be useful, but
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
# IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
# OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
# PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
# details.
#
# You should have received a copy of the Eclipse Public License 2.0
# along with Flight Directory. If not, see:
#
#  https://opensource.org/licenses/EPL-2.0
#
# For more information on Flight Directory, please visit:
# https://github.com/openflighthpc/flight-directory
#==============================================================================
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
