
import click
import requests
import os
import shutil
from urllib.parse import urlparse
import re

from config import CONFIG
import appliance_cli.utils as utils
import appliance_cli.config_utils as config_utils
import appliance_cli.text as text


def add_commands(appliance):

    @appliance.group(help='Manage Alces Flight Support access')
    def support():
        pass

    @support.command(help='Enable Alces Flight Support access')
    @click.argument('url')
    def enable(url):
        if _support_access_enabled():
            raise click.ClickException(
                'Alces Flight Support access already enabled.'
            )
        else:
            _enable_support_access(url)

    @support.command(help='Disable Alces Flight Support access')
    def disable():
        if not _support_access_enabled():
            raise click.ClickException(
                'Alces Flight Support access already disabled.'
            )
        elif click.confirm(_disable_confirmation_message()):
            _disable_support_access()

    @support.command(help='Display Alces Flight Support status')
    def status():
        eject_info = 'Alces Flight Support: {}'.format(
            _support_coverage_status()
        )
        access_info = 'Alces Flight Support access: {}'.format(
            _support_access_status()
        )
        status = text.join_lines(eject_info, access_info)

        click.echo(status)

    eject_help = "Eject Flight {} support".format(
        config_utils.appliance_name()
    )

    @support.command(help=eject_help)
    @click.argument('eject_code')
    def eject(eject_code):
        if click.confirm(_eject_confirmation_message()):
            _eject_appliance(eject_code)


def _enable_support_access(url):
    _validate_support_key_url(url)
    url_content = _get_url_content(url)
    _error_if_not_ssh_key(url_content)
    _add_support_ssh_key(url_content)
    _record_support_access_enabled()
    _print_support_access_message(text.success('Enabled'))


def _validate_support_key_url(url):
    parsed_url = urlparse(url)
    support_key_url = urlparse(CONFIG.SUPPORT_KEY_URL)

    invalid_scheme = parsed_url.scheme != 'https'

    invalid_domain = parsed_url.netloc != support_key_url.netloc
    invalid_bucket_folder = not re.match(support_key_url.path, parsed_url.path)
    invalid_url = invalid_domain or invalid_bucket_folder

    error_message = None
    if invalid_scheme:
        error_message = "Support key URL must be accessed using 'https'."
    elif invalid_url:
        error_message = "Valid support key URLs must begin with '{}'.".format(
            CONFIG.SUPPORT_KEY_URL
        )

    if error_message:
        raise click.ClickException(error_message)


def _disable_confirmation_message():
    info = text.line_wrap(
        'This will disable Alces Flight Support from being able to access '
        'this appliance.'
    )
    continue_prompt = text.info('Continue?')
    return text.join_lines(info, continue_prompt)


def _disable_support_access():
    os.remove(CONFIG.SUPPORT_USER_AUTHORIZED_KEYS)
    _record_support_access_disabled()
    _print_support_access_message(text.failure('Disabled'))


def _error_if_not_ssh_key(url_content):
    error = 'This URL does not appear to contain a valid SSH public key.'
    if not utils.is_valid_ssh_public_key(url_content):
        raise click.ClickException(error)


def _get_url_content(url):
    try:
        return requests.get(url).text
    except requests.RequestException as ex:
        raise click.ClickException(ex)


def _add_support_ssh_key(ssh_key):
    # Ensure support user SSH dir is created, with correct permissions
    ssh_dir = os.path.dirname(CONFIG.SUPPORT_USER_AUTHORIZED_KEYS)
    os.makedirs(ssh_dir, mode=0o700, exist_ok=True)

    with open(CONFIG.SUPPORT_USER_AUTHORIZED_KEYS, 'w') as authorized_keys:
        authorized_keys.write(ssh_key)

    # Ensure support user owns needed SSH paths.
    for path in (ssh_dir, CONFIG.SUPPORT_USER_AUTHORIZED_KEYS):
        shutil.chown(path, CONFIG.SUPPORT_USER, CONFIG.SUPPORT_USER)


def _print_support_access_message(action):
    message = action + ' Alces Flight Support access to your appliance!'
    click.echo(message)


def _support_access_status():
    if _support_access_enabled():
        return text.success('Enabled')
    else:
        return text.failure('Disabled')


def _support_access_enabled():
    return utils.is_feature_enabled(CONFIG.SUPPORT_ACCESS_ENABLED_MARKER)


def _record_support_access_enabled():
    utils.record_feature_enabled(CONFIG.SUPPORT_ACCESS_ENABLED_MARKER)


def _record_support_access_disabled():
    utils.record_feature_disabled(CONFIG.SUPPORT_ACCESS_ENABLED_MARKER)


def _support_coverage_status():
    if _support_ejected():
        return text.failure('Unavailable')
    else:
        return text.success('Available')


def _support_ejected():
    return utils.is_feature_enabled(CONFIG.SUPPORT_EJECTED_MARKER)


def _record_support_ejected():
    utils.record_feature_enabled(CONFIG.SUPPORT_EJECTED_MARKER)


def _eject_confirmation_message():
    info = text.line_wrap(CONFIG.SUPPORT_EJECT_INFO_MESSAGE)
    support_warning = text.line_wrap(text.bold(
        'This will opt you out from any obligation for Alces Flight '
        "Ltd to provide you with support for your Flight {}.".format(
            config_utils.appliance_name()
        )
    ))
    continue_prompt = text.info('Continue?')

    return text.join_lines(info, support_warning, continue_prompt)


def _eject_appliance(eject_code):
    eject_command = [CONFIG.SUPPORT_EJECT_SCRIPT, eject_code]
    result = utils.run(eject_command)

    if result.returncode == 0:
        message = _eject_success_message()
        _record_support_ejected()
    elif result.returncode == 1:
        # Incorrect eject code.
        message = _eject_failure_message()
    else:
        # Anything else indicates an error.
        raise click.ClickException(result.stderr)

    click.echo(message)


def _eject_success_message():
    success = text.success('Success!')

    message_callback = CONFIG.SUPPORT_EJECT_SUCCESS_MESSAGE_CALLBACK
    appliance_success_message = \
        message_callback(appliance_url=config_utils.appliance_url())

    return text.join_lines(success, appliance_success_message)


def _eject_failure_message():
    incorrect_code = text.failure('Incorrect eject code given.')
    contact_support = text.line_wrap(
        'Please contact the Alces Flight Support team at '
        'support@alces-flight.com if you are encountering difficulty ejecting '
        "your Flight {}.".format(config_utils.appliance_name())
    )

    return text.join_lines(incorrect_code, contact_support)
