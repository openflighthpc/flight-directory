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

import click
from click import ClickException
from pathlib import Path
import shlex

from config import CONFIG
import appliance_cli

from os import getenv
from exceptions import IpaRunError

import subprocess

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

def run_post_command_script(command, args):
    script_location = get_user_config(command)

    if script_location:
        try:
            script_result = subprocess.run([script_location, args], check=True)
        except PermissionError:
            raise click.ClickException(
                "Cannot execute post command script - you need permissions to execute '{}'."
                .format(script_location)
            )
        except OSError:
            raise click.ClickException(
                "Userware is unable to execute the script at '{}' ".format(script_location) + \
                "- please check the script exists and that it has a shebang line at its start"
            )
        except subprocess.CalledProcessError as ex:
            error = script_result.stdout if error_in_stdout else script_result.stderr
            raise IpaRunError(error) from ex

