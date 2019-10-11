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
from click import ClickException, Group
import shlex
import re
from os import getenv

from config import CONFIG
import utils
import user
import group
import host
import hostgroup
import import_export
import logger
from appliance_cli.commands import command_modules as standard_command_modules
from appliance_cli.sandbox import ExitSandboxException
from exceptions import IpaRunError


# Customized Group class to use for the Directory CLI top-level command.
class DirectoryGroup(Group):

    # Record the exact args before parsing in the `context` `meta` dictionary,
    # so that when needed the exact original command may be recorded in the
    # Directory record.
    def parse_args(self, ctx, args):
        quoted_args = [shlex.quote(arg.strip()) for arg in args]
        original_command = ' '.join(quoted_args)
        ctx.meta[CONFIG.ORIGINAL_COMMAND_META_KEY] = original_command
        return Group.parse_args(self, ctx, args)

    def _log_and_run_cmd(self, ctx):
        try:
            super().invoke(ctx)
            logger.log_cmd(args=["Success"])
        # Ignores the actual 'exit' command from the log (as it throws an ExitSandboxException)
        # Instead we write to the log immediately after, as the sandbox exits, with the original command retrieved from the Click context
        # TODO also filter out logs produced through EOF commands like Ctrl+D
        #   may take an overhaul of logging method + use of atexit module
        except ExitSandboxException:
            raise
        except Exception as error:
            logger.log_cmd(args=["Failure"], error=error)
            raise error

    def invoke(self, ctx):
        try:
            DirectoryGroup._log_and_run_cmd(self, ctx)
        except IpaRunError as ex:
            # Convert any unhandled `IpaRunError` to a `ClickException`, for
            # nice error display.
            raise ClickException(ex.message)

@click.command(
    cls=DirectoryGroup,
    help='Perform Flight Directory management tasks.'
)

def directory():
    # TODO: This might not be needed for all directory subcommands; should
    # maybe move calling so only done if needed.
    utils.obtain_kerberos_ticket()

command_modules = standard_command_modules + [
            user,
            group,
            import_export,
        ]
if utils.advanced_mode_enabled():
    command_modules += [host, hostgroup]

for module in command_modules:
    module.add_commands(directory)

logger.write_to_log(["access", "Success"])
