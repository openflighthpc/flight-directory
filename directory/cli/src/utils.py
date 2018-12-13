
import click
from click import ClickException
from pathlib import Path
import shlex

from config import CONFIG
import appliance_cli

from os import getenv

def obtain_kerberos_ticket():
    # TODO: apparently this is a bad idea, consider using keytab - refer to:
    # http://stackoverflow.com/questions/8144596/kerberos-kinit-enter-password-without-prompt.
    password = directory_config()[CONFIG.PASSWORD_KEY]
    kinit_command = 'echo {} | kinit admin'.format(password),
    appliance_cli.utils.run(kinit_command, shell=True)


# Note: Could be made generic, but not needed by another appliance CLI yet.
def directory_config():
    try:
        return appliance_cli.utils.read_config(CONFIG.APPLIANCE_CONFIG)
    except PermissionError:
        raise ClickException(
            "Cannot read Directory config - you need permissions to read '{}'."
            .format(CONFIG.APPLIANCE_CONFIG)
        )

def get_user_config(conf_variable):
    # only even try read it if file exists, to allow backwards compatability
    if detect_user_config():
        try:
            return appliance_cli.utils.read_config(CONFIG.DIRECTORY_USER_CONFIG)[conf_variable]
        except KeyError:
            # if the specified config field hasn't been set/doesn't exist
            #   we want to error silently & return None
            return None
        except PermissionError:
            raise ClickException(
                "Cannot read user config - you need permissions to read '{}'."
                .format(CONFIG.DIRECTORY_USER_CONFIG)
            )

def detect_user_config():
    user_config_file = Path(CONFIG.DIRECTORY_USER_CONFIG)
    return user_config_file.is_file()

# return true if a password is not to be generated
def get_password_policy():
    return get_user_config('DO_NOT_GENERATE_PASSWORD') == 'TRUE'

def original_command():
    return _meta()[CONFIG.ORIGINAL_COMMAND_META_KEY]


def mark_import_started():
    _set_import_status_meta_key(True)

    # Initialize new dict to track newly generated user passwords.
    _meta()[CONFIG.IMPORTED_USER_PASSWORDS_META_KEY] = {}


def mark_import_finished():
    _set_import_status_meta_key(False)


def _set_import_status_meta_key(in_import):
    _meta()[CONFIG.IMPORT_STATUS_META_KEY] = in_import


def currently_importing():
    return _meta().get(CONFIG.IMPORT_STATUS_META_KEY)


def set_imported_user_password(login, password):
    imported_user_passwords()[login] = password


def remove_imported_user_entry(login):
    imported_user_passwords().pop(login)


def imported_user_passwords():
    return _meta()[CONFIG.IMPORTED_USER_PASSWORDS_META_KEY]


def _meta():
    return click.get_current_context().meta

# Re-invoke `directory` command with given arguments string.


def directory_run(directory, command_string):
    arguments = shlex.split(command_string)

    # Invoke command in new child context so can access and modify shared
    # `meta` dict from child commands.
    with directory.make_context(
            None,
            arguments,
            parent=click.get_current_context()
    ) as context:
        directory.invoke(context)

def display_success():
    command_string = " ".join(original_command().split(" ")[:2])
#    command_string = " ".join([word.capitalize() for word in command_string])
    click.echo("------------- " + command_string + " successful -------------")

def advanced_mode_enabled():
    return getenv('ADVANCED', default='false').lower() == 'true'
