
import click


def add_commands(appliance):
    @appliance.command(help='Show overall or individual command help')
    @click.argument('command', nargs=-1, required=False)
    def help(command):
        appliance(list(command) + ['--help'])
