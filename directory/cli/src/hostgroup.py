import click
from collections import OrderedDict

import list_command
from list_command import field_with_same_name    	
import ipa_wrapper_command
import ipa_utils
from exceptions import IpaRunError
from option_transformer import OptionTransformer

HOSTGROUP_LIST_FIELD_CONFIGS = OrderedDict([
    ('Host-group', field_with_same_name),
    ('Description', field_with_same_name),
])

HOSTGROUP_SHOW_FIELD_CONFIGS = HOSTGROUP_LIST_FIELD_CONFIGS.copy()
HOSTGROUP_SHOW_FIELD_CONFIGS.update([
    ('Member hosts', field_with_same_name),
])

HOSTGROUP_OPTIONS = {
    '--desc':{'help': 'Host group description'}
}

HOSTGROUP_BLACKLIST = ['adminnode', 'ipaservers']

def add_commands(directory):

    @directory.group(help='Manage host groups')
    def hostgroup():
        pass

    @hostgroup.command(help='List all host groups')
    def list():
        list_command.do(
            ipa_find_command='hostgroup-find',
            field_configs=HOSTGROUP_LIST_FIELD_CONFIGS,
            sort_key='Host-group',
            blacklist_key='Host-group',
            blacklist_val_array=HOSTGROUP_BLACKLIST,
        )
	
    @hostgroup.command(help='Show detailed information on one host group')
    @click.argument('hostgroup_name')
    def show(hostgroup_name):
        _validate_blacklist_hostgroups(hostgroup_name)
        hostgroup_find_args = ['--hostgroup-name={}'.format(hostgroup_name)]
        try:
            list_command.do(
                ipa_find_command='hostgroup-find',
                ipa_find_args=hostgroup_find_args,
                field_configs=HOSTGROUP_SHOW_FIELD_CONFIGS,
                display=list_command.list_displayer
            )
        except IpaRunError:
            #no hostgroup by that name found
            error = '{}: group not found'.format(hostgroup_name)
            raise click.ClickException(error)

    @hostgroup.command(name='add-member', help='Add host(s) to a host group')
    @click.argument('hostgroup_name')
    @click.argument('hosts', nargs=-1)
    def add_member(hostgroup_name, hosts):
        _validate_blacklist_hostgroups(hostgroup_name, hosts)
        host_options = ['--hosts={}'.format(host) for host in hosts]
        ipa_command = 'hostgroup-add-member'
        args = [hostgroup_name] + host_options
        try:
            ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)
        except IpaRunError:
            error = "Host group add member failed"
            raise click.ClickException(error)

    @hostgroup.command(name='remove-member', help='Remove host(s) from a host group')
    @click.argument('hostgroup_name')
    @click.argument('hosts', nargs=-1)
    def remove_member(hostgroup_name, hosts):
        _validate_blacklist_hostgroups(hostgroup_name, hosts)
        host_options = ['--hosts={}'.format(host) for host in hosts]
        ipa_command = 'hostgroup-remove-member'
        args = [hostgroup_name] + host_options
        try:
            ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)
        except IpaRunError:
            error = "Host group remove member failed"
            raise click.ClickException(error)


    wrapper_commands = [
        ipa_wrapper_command.create(
            'create',
            ipa_command='hostgroup-add',
            argument_name='name',
            options=HOSTGROUP_OPTIONS,
            transform_options_callback=_transform_options,
            help='Create a new host group',
        ),
        ipa_wrapper_command.create(
            'modify',
            ipa_command='hostgroup-mod',
            argument_name='name',
            options=HOSTGROUP_OPTIONS,
            transform_options_callback=_transform_options,
            help='Modify an existing host group',
        ),
        ipa_wrapper_command.create(
            'delete',
            ipa_command='hostgroup-del',
            argument_name='name',
            options=HOSTGROUP_OPTIONS,
            transform_options_callback=_transform_options,
            help='Delete a host group',
        )
    ]

    for command in wrapper_commands:
        hostgroup.add_command(command)

def _transform_options(argument, options):
    _validate_blacklist_hostgroups(argument)
    return options

def _validate_blacklist_hostgroups(argument, options={}):
    if argument in HOSTGROUP_BLACKLIST:
        error = "The host group " + argument + " is a resricted hostgroup"
        raise click.ClickException(error)
