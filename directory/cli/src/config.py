
from os.path import join

import appliance_cli.config
import appliance_cli.text as text


# Create Directory CLI config object.


_APPLIANCE_TYPE = 'directory'

_STANDARD_CONFIG = appliance_cli.config.create_config_dict(_APPLIANCE_TYPE)


_WEB_SERVER_ROOT = '/var/www/html'
_EXPORT_PREFIX = 'secure'


def _support_eject_success_message(appliance_url=None):
    cli_info = text.line_wrap(
        'You may now log out and in again to gain full command-line access to '
        'the appliance.'
    )

    freeipa_url = appliance_url + '/ipa/ui'
    freeipa_info = text.line_wrap(
        (
            'You may also visit {} to access your full FreeIPA interface.'
        ).format(freeipa_url)
    )

    return text.join_lines(cli_info, freeipa_info)

_DIRECTORY_CONFIG = {
    'DIRECTORY_RECORD': join(_STANDARD_CONFIG['APPLIANCE_DIR'], 'record'),

    'PASSWORD_KEY': 'IPAPASSWORD',

    'WEB_SERVER_ROOT': _WEB_SERVER_ROOT,
    'EXPORT_PREFIX': _EXPORT_PREFIX,
    'EXPORT_DIR': join(_WEB_SERVER_ROOT, _EXPORT_PREFIX),

    # Best practise to include module name in meta keys (ref
    # http://click.pocoo.org/6/api/#click.Context.meta).
    'ORIGINAL_COMMAND_META_KEY': __name__ + '.command',
    'IMPORT_STATUS_META_KEY': __name__ + '.importing',
    'IMPORTED_USER_PASSWORDS_META_KEY': __name__ + '.imported-user-passwords',

    'SUPPORT_EJECT_INFO_MESSAGE': (
        'This will eject your Flight Directory support, allowing you full '
        'command-line access via SSH and full access to FreeIPA.'
    ),
    'SUPPORT_EJECT_SUCCESS_MESSAGE_CALLBACK': _support_eject_success_message,
}

CONFIG = appliance_cli.config.finalize_config(
    _STANDARD_CONFIG, custom_config=_DIRECTORY_CONFIG
)
