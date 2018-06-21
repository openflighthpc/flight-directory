
from os.path import join

from appliance_cli.utils import struct

# Functions to create config object for an appliance CLI.


def create_config_dict(appliance_type):
    appliance_dir = join('/opt/', appliance_type)
    clusterware_root = '/opt/clusterware'
    support_user = 'alces'

    return {
        'APPLIANCE_TYPE': appliance_type,
        'APPLIANCE_DIR': appliance_dir,
        'APPLIANCE_CONFIG': join(appliance_dir, 'etc/config'),

        'SANDBOX_HISTORY': join(appliance_dir, 'history'),

        'CLUSTERWARE_ROOT': clusterware_root,
        'CLUSTERWARE_ACCESS_CONFIG': join(clusterware_root, 'etc/access.rc'),

        'SUPPORT_USER': support_user,
        'SUPPORT_USER_AUTHORIZED_KEYS': join(
            '/home', support_user, '.ssh/authorized_keys'
        ),
        'SUPPORT_KEY_URL': 'https://s3-eu-west-1.amazonaws.com/alces-flight/Support/',

        'SUPPORT_ACCESS_ENABLED_MARKER': join(
            appliance_dir, 'etc/.support-access-enabled'
        ),
        'SUPPORT_EJECTED_MARKER': join(appliance_dir, 'etc/.support-ejected'),
        'SUPPORT_EJECT_SCRIPT': join(appliance_dir, 'bin/eject.rb'),

        'ACCESS_FQDN_KEY': 'cw_ACCESS_fqdn',
    }


REQUIRED_CONFIG_VALUE_NAMES = [
    'SUPPORT_EJECT_INFO_MESSAGE',
    'SUPPORT_EJECT_SUCCESS_MESSAGE_CALLBACK',
]


def finalize_config(config_dict, custom_config=None):
    if custom_config:
        config_dict = {**config_dict, **custom_config}

    # All required config values must be provided by the client when creating
    # the config object.
    for key_name in REQUIRED_CONFIG_VALUE_NAMES:
        if key_name not in custom_config.keys():
            raise Exception(
                "Required config value '{}' not provided.".format(key_name)
            )

    return struct(config_dict)
