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

from appliance_cli.utils import read_config

from config import CONFIG


"""Module for shared util functions that depend on the appliance's config

This keeps these functions separate from those that are generic and don't
depend on the appliance's config. It also avoids recursive importing errors if
need to import generic util functions when creating config (as those utils
don't need to depend on the config module).
"""


def appliance_url():
    access_config = \
        read_config(CONFIG.CLUSTERWARE_ACCESS_CONFIG)
    fqdn = access_config[CONFIG.ACCESS_FQDN_KEY]
    return 'https://' + fqdn


def appliance_name():
    return CONFIG.APPLIANCE_TYPE.capitalize()
