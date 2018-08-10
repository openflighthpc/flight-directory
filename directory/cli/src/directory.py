import click
from click import ClickException, Group
import shlex

from config import CONFIG
import utils
import user
import group
import host
import hostgroup
import import_export
import logger
from appliance_cli.commands import command_modules as standard_command_modules
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
        except Exception as error:
            args = ["Failure"]
            # some click exceptions (e.g. MissingParameter) don't have human readable standard 
            #   output so this is neccessary to log them fully
            if hasattr(error, 'format_message'):
                error_str = error.format_message()
            else:
                error_str = str(error)
            error_str.strip()
            if type(error):
                args[0] = args[0] + ": " + error.__class__.__name__ 
            if (error_str and not error_str=="None"):
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

logger.write_to_log(["Access"])

for module in command_modules:
    module.add_commands(directory)
