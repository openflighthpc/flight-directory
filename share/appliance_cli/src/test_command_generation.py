
import click
import re
import copy

from appliance_cli.testing_utils import click_run
from appliance_cli.command_generation import generate_commands


DEFAULT_TEST_CONFIG = {
    'first-level-command': {
        'arguments': ['arg1', 'arg2'],
        'options': {
            '--opt1': {},
            '--opt2': {'help': 'Add extra magic'},
            # Note: use a tuple for multiple options; lists cannot be used as
            # not hashable.
            ('--opt3', '-o'): {},
        },
        'help': 'first-level-command help'
    },
    'command-group': {
        'commands': {
            'group-command': {
                'arguments': ['group-command-arg1', 'group-command-arg2'],
                'options': {
                    '--group-command-opt1': {}
                },
            },
        },
        'help': 'command-group help',
    }
}


def test_valid_first_level_command():
    args = ['first-level-command', 'arg1_value',
            'arg2_value', '--opt2', 'opt2_value', '-o', 'opt3_value']

    def callback(commands, arguments, options):
        assert commands == ['first-level-command']
        assert arguments == ['arg1_value', 'arg2_value']
        assert options.values_map() == {
            # Note: only options with a value given are included.
            'opt2': 'opt2_value',

            # Note: short option is included using long option name.
            'opt3': 'opt3_value'
        }

        click.echo('Callback was called')

    result = valid_command_test(args, callback)
    assert 'Callback was called' in result.output


def test_first_level_command_help():
    args = ['first-level-command', '--help']
    result = valid_command_test(args)

    assert 'first-level-command help' in result.output
    assert re.search("--opt2.+Add extra magic", result.output)


def test_valid_grouped_command():
    args = ['command-group', 'group-command', 'group-command-arg-1_value',
            'group-command-arg-2_value', '--group-command-opt1', 'opt1_value']

    def callback(commands, arguments, options):
        assert commands == ['command-group', 'group-command']
        assert arguments == ['group-command-arg-1_value',
                             'group-command-arg-2_value']
        # Note: Click translates hyphens to underscores in parameter names to
        # get valid variable names.
        assert options.values_map() == {
            'group_command_opt1': 'opt1_value'
        }

        click.echo('Callback was called')

    result = valid_command_test(args, callback)
    assert 'Callback was called' in result.output


def test_command_group_help():
    args = ['command-group', '--help']
    result = valid_command_test(args)

    assert 'command-group help' in result.output


def test_command_without_arguments():
    config = {
        'test-command': {
            'options': {'--some-opt': {}}
        }
    }

    def callback(commands, arguments, options):
        assert arguments == []
        click.echo('Callback was called')

    args = ['test-command']
    result = valid_command_test(args, callback, config)
    assert 'Callback was called' in result.output


def test_command_without_options():
    config = {
        'test-command': {
            'arguments': ['test-arg']
        }
    }

    def callback(commands, arguments, options):
        assert options.values_map() == {}
        click.echo('Callback was called')

    args = ['test-command', 'test-arg_value']
    result = valid_command_test(args, callback, config)
    assert 'Callback was called' in result.output


def test_command_with_flag_option():
    config = {
        'test-command': {
            'options': {
                '--flag-opt': {'is_flag': True}
            }
        }
    }

    def when_passed_callback(commands, arguments, options):
        assert options.values_map() == {'flag_opt': True}
        click.echo('Callback was called')

    args = ['test-command', '--flag-opt']
    result = valid_command_test(args, when_passed_callback, config)
    # TODO refactor callback testing?
    assert 'Callback was called' in result.output

    def when_not_passed_callback(commands, arguments, options):
        assert options.values_map() == {}
        click.echo('Callback was called')

    args = ['test-command']
    result = valid_command_test(args, when_not_passed_callback, config)
    assert 'Callback was called' in result.output


def test_callbacks_are_passed_fresh_arguments():
    """Test generated command callbacks are new cloned arguments on each call

    The same generated commands will be reused if the root command is reused,
    which happens for instance in the sandbox, and in other tests when running
    multiple commands in a test. In these situations we do not want to pass the
    same objects as the callback arguments, so that we are free to modify the
    callback arguments within the callback without effecting future callback
    calls.
    """
    last_callback_call_args = {}

    def save_args_callback(commands, arguments, options):
        last_callback_call_args['commands'] = commands
        last_callback_call_args['arguments'] = arguments
        last_callback_call_args['options'] = options

    # Generate commands once and then reuse for this test, rather than using
    # `valid_command_test`, as want to test that for the same generated
    # commands the callback is passed fresh arguments.
    root_command = click.Group('root')
    generate_commands(root_command, DEFAULT_TEST_CONFIG, save_args_callback)

    args = ['first-level-command', 'arg1_value', 'arg2_value', '--opt1',
            'opt1_value']

    click_run(root_command, args)

    # Shallow copy the last callback args to retain references to the original
    # objects.
    first_callback_call_args = copy.copy(last_callback_call_args)

    click_run(root_command, args)

    # Callback should be called with fresh arguments.
    for arg_name in ['commands', 'arguments', 'options']:
        assert last_callback_call_args[arg_name] \
            is not first_callback_call_args[arg_name]


def identity_callback(*arguments, **options):
    pass


def valid_command_test(
        args, callback=identity_callback, config=DEFAULT_TEST_CONFIG
):
    root_command = click.Group('root')
    generate_commands(root_command, config, callback)

    result = click_run(root_command, args)
    assert result.exit_code is 0
    return result
