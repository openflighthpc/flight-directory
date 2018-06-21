
import click
from click_repl import repl
from prompt_toolkit.history import FileHistory

from config import CONFIG
import appliance_cli.config_utils as config_utils


def add_commands(appliance):
    sandbox_help = "Start {} CLI REPL".format(config_utils.appliance_name())
    exit_sandbox_help = "Exit the {} CLI".format(config_utils.appliance_name())

    @appliance.command(help=sandbox_help)
    def sandbox():

        # `exit` is defined only when in the `sandbox` REPL.
        @appliance.command(help=exit_sandbox_help)
        def exit():
            raise ExitSandboxException()

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
    prompt = CONFIG.APPLIANCE_TYPE + '> '
    title = 'Alces Flight ' + CONFIG.APPLIANCE_TYPE
    return {
        'message': prompt,
        'history': FileHistory(CONFIG.SANDBOX_HISTORY),
        'enable_history_search': True,
        'get_title': lambda: title
    }


class ExitSandboxException(Exception):
    pass
