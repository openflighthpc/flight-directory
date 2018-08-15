
import click
import ipa_utils


# TODO: consider using new wrapper_command stuff for this has been written; is
# more flexible.


def create(
        command_name,
        ipa_command=None,
        argument_name=None,
        help='',
        options={},
        transform_options_callback=lambda argument, options: options,
        handle_result_callback=lambda argument, options, result: None,
):
    
    if not all([ipa_command, argument_name]):
        raise TypeError

    argument = click.Argument([argument_name])
    options = [
        click.Option([option_name], **option_config)
        for option_name, option_config in options.items()
    ]
    params = [argument] + options

    ipa_wrapper = _create_ipa_wrapper(
        ipa_command,
        argument_name=argument_name,
        transform_options_callback=transform_options_callback,
        handle_result_callback=handle_result_callback
    )
	
    return click.Command(
        command_name,
        callback=ipa_wrapper,
        params=params,
        help=help
    )


def _create_ipa_wrapper(
        ipa_command,
        argument_name=None,
        transform_options_callback=None,
        handle_result_callback=None,
):
    def ipa_wrapper(**validated_params):
	
        # Get argument if present; the other params are options.
        argument = validated_params.pop(argument_name)

        #At somepoint during processing of the options, seemingly in click.Option, the '-' in ip-address
	    #	is being replaced with an underscore
	    #I couldn't work out why so this is a messy fix for the time being
        if 'ip_address' in validated_params:
            validated_params['ip-address'] = validated_params['ip_address'] 
            del validated_params['ip_address']

        options = validated_params

        args = _build_ipa_args(
            argument,
            options=options,
            transform_options_callback=transform_options_callback
        )
        
        # if the command is modify host & there's only one item in the args list it's neccesary not to call
        #   the ipa command as a) the option to modify it wouldn't do anything anyway and b) it woudl result
        #   in a spurious error message if the --ip-address option has been removed in transform_options_callback
        if not (ipa_command == "host-mod" and len(args) == 1): 
            result = ipa_utils.ipa_run(ipa_command, args)
            handle_result_callback(argument, options, result)

    return ipa_wrapper


# TODO similar behaviour to `controller/cli/src/fly_wrapper`, but this is
# a bit less clean.
def _build_ipa_args(
        argument=None,
        options={},
        transform_options_callback=None
):
    args = []
    transformed_options = transform_options_callback(argument, options)

    # Click will give us `None` as the value for possible options which
    # have not been passed; we want only those which have been passed.
    filtered_options = {name: value for
                        name, value in transformed_options.items()
                        if value is not None}

    # Order options by name, so in predictable order for testing.
    ordered_option_pairs = sorted(filtered_options.items())

    if argument:
        args.append(argument)

    for name, value in ordered_option_pairs:
        args.append('--{}'.format(name))

        # Explicitly check whether value is False to allow passing empty string
        # values; if value is False then the option is treated as a flag.
        if value is not False:
            args.append(value)

    return args
