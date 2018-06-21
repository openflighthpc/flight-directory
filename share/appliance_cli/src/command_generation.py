
import click
from collections import namedtuple, OrderedDict
from autorepr import autorepr
from copy import deepcopy


def generate_commands(root_command, config, callback):
    """Generate commands using the given config.

    Recursively define a tree of commands using the config, where the leaf
    commands will execute the callback function with 3 arguments when run: a
    list of the ancestor commands, a list of the arguments, and a dict of
    passed option names to values. The generated commands will be added to the
    given root command.
    """
    for command_name, config in config.items():
        initial_ancestor_commands = [command_name]
        command = _parse_command(initial_ancestor_commands, config, callback)
        root_command.add_command(command)


def _parse_command(ancestor_commands, config, callback):
    if 'commands' in config:
        command_class = click.Group
        config_parser = _parse_group_command_config
    else:
        command_class = click.Command
        config_parser = _parse_simple_command_config

    command_args = config_parser(ancestor_commands, config, callback)

    command_name = ancestor_commands[-1]
    command = command_class(
        command_name,
        help=config.get('help'),
        short_help=(config.get('short_help') or config.get('help')),
        **command_args
    )

    return command


class Options():

    # An additional option to be passed to the callback function, not created
    # from a click.Option or passed a value (directly) by a user; can create
    # via `__setitem__`.
    AdditionalOption = namedtuple('AdditionalOption', ['value'])

    fields = ['options_map']
    __repr__ = autorepr(fields)

    def __init__(self, options_config):
        self.options_map = {}
        for name_or_names, config in options_config.items():
            names = _to_list(name_or_names)
            click_option = click.Option(names, **config)

            # Put Option entry in map for each option name, as options can have
            # multiple names but we want to be able to navigate to click Option
            # and option config from any of these.
            for name in names:
                option = Option(name, config, click_option)
                self.options_map[option.identifier()] = option

    def __getitem__(self, identifier):
        return self.options_map[identifier]

    def __setitem__(self, identifier, option_value):
        self.options_map[identifier] = Options.AdditionalOption(option_value)

    def __delitem__(self, identifier):
        del self.options_map[identifier]

    def __iter__(self):
        return iter(self.options_map.items())

    def click_options(self):
        """`click.Option`s for these Options"""
        # Note: get click.Options as set before converting to list to remove
        # duplicates; same option will appear in map multiple times for each
        # name for the option, but we want only one copy of each.
        return list({opt.click_option for opt in self.options_map.values()})

    def values_map(self):
        """A map from option identifiers to values, without unpassed options"""
        return {
            identifier: option.value
            for identifier, option in self
            # Don't include not passed options or flags.
            if option.value not in [None, False]
        }


class Option():

    fields = [
        'click_option',
        'config',
        'parameter',
        'value'
    ]
    __repr__ = autorepr(fields)

    def __init__(self, parameter, config, click_option):
        self.parameter = parameter
        self.config = config
        self.click_option = click_option

        self.value = None

    def identifier(self):
        return _parameter_identifier(self.parameter)


def _parse_simple_command_config(ancestor_commands, config, callback):
    arguments_config = config.get('arguments', [])
    options_config = config.get('options', {})

    # Create ordered map of argument identifiers to click.Arguments.
    # TODO Could create Argument and Arguments classes as with Options; don't
    # need complicated behaviour (yet) for arguments but might make things
    # clearer.
    arguments = _form_arguments(arguments_config)
    click_arguments = list(arguments.values())

    options = Options(options_config)

    click_params = click_arguments + options.click_options()

    # Define function to be passed as 'callback' parameter to click.Command,
    # transforming its arguments suitable to be passed to our own callback.
    def click_callback(**params):
        argument_values = [
            params[arg_name] for arg_name in arguments.keys()
        ]

        # Set values for passed options.
        passed_param_names = params.keys()
        for identifier, option in options:
            if identifier in passed_param_names:
                option.value = params[identifier]

        # Clone arguments for callback so callback can modify freely without
        # effecting future callback calls.
        new_commands = deepcopy(ancestor_commands)
        new_options = deepcopy(options)

        callback(new_commands, argument_values, new_options)

    return {
        'params': click_params,
        'callback': click_callback
    }


def _form_arguments(arguments_config):
    args_map = OrderedDict()
    for arg_name in arguments_config:
        identifier = _parameter_identifier(arg_name)
        args_map[identifier] = click.Argument([arg_name])
    return args_map


def _to_list(obj):
    if isinstance(obj, str):
        # Create 1-element list, otherwise would be converted to list of chars.
        return [obj]
    else:
        return list(obj)


def _parameter_identifier(param):
    # Click strips leading dashes and translates internal dashes to underscores
    # in passed parameter names to get valid variable names to pass to command
    # callbacks, so to get the parameter identifiers which will be used by
    # Click we need to perform this translation ourselves.
    translation_table = str.maketrans('-', '_')
    return param.lstrip('-').translate(translation_table)


def _parse_group_command_config(ancestor_commands, config, callback):
    commands = {
        command_name: _parse_command(
            ancestor_commands + [command_name],
            config,
            callback
        )
        for command_name, config
        in config['commands'].items()
    }

    return {
        'commands': commands
    }
