
import appliance_cli.text as text
from click.testing import CliRunner


# Wrapper around `CliRunner.invoke()`, to enable behaviour we normally want.
def click_run(cli, args, **kwargs):
    runner = CliRunner()
    result = runner.invoke(cli, args, catch_exceptions=False, **kwargs)
    print(text.bold('Command output:'), result.output)
    return result
