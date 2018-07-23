
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

    def invoke(self, ctx):
        try:
            super().invoke(ctx)
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
