import click
import sys, os

SCRIPT_PATH = os.path.realpath(sys.argv[0])
CURRENT_SCRIPT = '{0}.py'.format(SCRIPT_PATH)

def add_commands(directory):

    @directory.group(help='Toggle advanced mode')
    def advanced():
        pass

    @advanced.command(help='Enable advanced mode')
    def enable():
        os.environ['ADVANCED'] = 'true'
        os.execve(sys.argv[0], sys.argv, os.environ)

    @advanced.command(help='Disable advanced mode')
    def disable():
        os.environ['ADVANCED'] = 'false'
        os.execve(sys.argv[0], sys.argv, os.environ)
