
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
