import click
from click import ClickException, Group
import shlex
import re

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
            args = ["Failure"]
            # some click exceptions (e.g. MissingParameter) don't have human readable standard
            #   output so this is neccessary to log them fully
            if hasattr(error, 'format_message'):
                error_str = error.format_message()
            else:
                error_str = str(error)
            if error.__class__.__name__:
                args[0] = args[0] + ": " + error.__class__.__name__
            if (error_str and not error_str=="None"):
                # some errors came packaged with newlines & strip wasn't working for some reason
                error_str = re.sub(r'\n','',error_str)
                # Error strings have many uneccessary quotes. All those that are valid are duplicated
                #   deleting non consecutive quotes
                error_str = re.sub(r'(?<!\")\"(?!\")','',error_str)
                #   replacing consecutive quotes with single quotes
                error_str = re.sub(r'""','"',error_str)
                args[0] = args[0] + ": " + error_str
            logger.log_cmd(args)
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

command_modules = standard_command_modules + [user, group, import_export, host, hostgroup]

for module in command_modules:
    module.add_commands(directory)

logger.write_to_log(["access", "Success"])
