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
from click_repl import repl
from prompt_toolkit.history import FileHistory

from config import CONFIG
import appliance_cli.config_utils as config_utils

from os import environ, execve
from sys import argv

from utils import advanced_mode_enabled

def add_commands(appliance):
    sandbox_help = "Start {} CLI REPL".format(config_utils.appliance_name())
    exit_sandbox_help = "Exit the {} CLI".format(config_utils.appliance_name())

    @appliance.command(help=sandbox_help)
    def sandbox():

        # `exit` is defined only when in the `sandbox` REPL.
        @appliance.command(help=exit_sandbox_help)
        def exit():
            raise ExitSandboxException()

        @appliance.group(help='Toggle advanced mode')
        def advanced():
            pass

        @advanced.command(help='Enable advanced mode')
        def enable():
            toggle_advanced_mode(True)

        @advanced.command(help='Disable advanced mode')
        def disable():
            toggle_advanced_mode(False)

        try:
            repl(
                click.get_current_context(),
                prompt_kwargs=_prompt_kwargs(),
                allow_system_commands=False,
                allow_internal_commands=False,
            )
        except ExitSandboxException:
            return

def _prompt_kwargs():
    prompt = CONFIG.APPLIANCE_TYPE + (' (advanced)>' if advanced_mode_enabled() else '>')
    title = 'Alces Flight ' + CONFIG.APPLIANCE_TYPE
    return {
        'message': prompt,
        'history': FileHistory(CONFIG.SANDBOX_HISTORY),
        'enable_history_search': True,
        'get_title': lambda: title
    }

def toggle_advanced_mode(switch):
    environ['ADVANCED'] = str(switch)
    print('Advanced mode %s' % ('enabled' if switch else 'disabled'))

    # execve allows us to create a fresh process of the CLI with advanced mode
    # toggled on/off. As there are distinct differences in available commands
    # we need to execute a new process. This takes the script being executed
    # as its first argument and the arguments required second in argv itself.
    execve(argv[0], argv, environ)

class ExitSandboxException(Exception):
    pass
