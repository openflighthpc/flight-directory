import click
from collections import OrderedDict

from config import CONFIG
import list_command
from list_command import \
    field_with_same_name, \
    field_with_name, \
    host_with_ip
import ipa_wrapper_command
import ipa_utils
import appliance_cli.text as text
import appliance_cli.utils
import utils
import re
from exceptions import IpaRunError
from option_transformer import OptionTransformer

HOST_LIST_FIELD_CONFIGS = OrderedDict([
    ('Host name', field_with_same_name),
    ('ip-address', host_with_ip),
    ('Member of host-groups', field_with_same_name),
])

HOST_SHOW_FIELD_CONFIGS = HOST_LIST_FIELD_CONFIGS.copy()
HOST_SHOW_FIELD_CONFIGS.update([
])

HOST_BLACKLIST = ['controller', 'infra01', 'infra02', 'infra03']


def add_commands(directory):
	
    @directory.group(help='Perform host management tasks')
    def host():
        pass

    @host.command(help='List all hosts')
    def list():
        list_command.do(
            ipa_find_command='host-find',
	    field_configs=HOST_LIST_FIELD_CONFIGS,
	    sort_key='Host name',
	    blacklist_key='serverhostname',
	    blacklist_val_array=HOST_BLACKLIST,
	)

    @host.command(help='Show detailed information on a host')
    @click.argument('hostname')
    def show(hostname):
        _validate_blacklist_hosts(hostname)
        host_find_args = ['--hostname={}'.format(hostname)]
        try:
            list_command.do(
                ipa_find_command='host-find',
                ipa_find_args=host_find_args,
                field_configs=HOST_SHOW_FIELD_CONFIGS,
                display=list_command.list_displayer
            )
        except IpaRunError:
            # No matching host found; for consistency raise error with similar
            # format to IPA errors.
            error = '{}: host not found'.format(hostname)
            raise click.ClickException(error)

    wrapper_commands = [
        ipa_wrapper_command.create(
	    'create',
	    ipa_command='host-add',
	    argument_name='hostname',
	    options=_host_options(),
	    transform_options_callback=_transform_create_options,
	    help='Create new host'
	),
	ipa_wrapper_command.create(
	    'modify',
	    ipa_command='host-mod',
	    argument_name='hostname',
	    options=_host_options(),
            transform_options_callback=_transform_modify_options,
	    help='Modify existing host'
	),
	ipa_wrapper_command.create(
	    'delete',
	    ipa_command='host-del',
	    argument_name='hostname',
            transform_options_callback=_transform_delete_options,
            help='Delete existing host and its dns records'
        )]
	
    for command in wrapper_commands:
        host.add_command(command)


def _all_dns_zones():
    dns_zones = ipa_utils.ipa_find('dnszone-find', all_fields=False)
    return dns_zones

def _host_options():
    return {
        '--password': {'help': 'Host password'},
	'--ip-address': {'help': 'IP address of host'},
    }

def _transform_create_options(argument, options):
	_validate_blacklist_hosts(argument)
	return options

def _transform_modify_options(argument,options):
    _validate_blacklist_hosts(argument)
    # ipa handles host ip addresses differently from other data so a conditional is
    #   neccessary for if a user's trying to modify a host's ip
    if not options['ip-address'] == None:
        # need to determine if it's only address to be changed, and print success message if so
        ip_only = True
        for option, value in options.items():
            if (option != 'ip-address' and value != None):
                ip_only = False
                break
        _modify_ip(argument, new_ip=options['ip-address'], ip_only=ip_only)
        del options['ip-address']
    return options


def _modify_ip(argument, new_ip, ip_only):
    all_dns_zones = _all_dns_zones()

    # to prevent possible ambiguity here I've elected to reject any host that isn't fully qualified
    arg_zone = None
    for zone in all_dns_zones:
        zone_without_trailing_dot = re.sub(r'\.$','', zone['Zone name'][0])
        # create regex string with end of line char at the end
        zone_at_end = re.escape(zone_without_trailing_dot) + r'$'
        if re.search(zone_at_end, argument, re.IGNORECASE):
            arg_zone = zone_without_trailing_dot
            zone_with_leading_dot = r'.' + re.escape(arg_zone)
            arg_host_name = re.sub(zone_with_leading_dot,'',argument)

    if arg_zone == None:
        error = "Host " + argument + " not fully qualified"
        raise click.ClickException(error)
    else:
        args = [arg_zone, arg_host_name, '--a-rec='+new_ip]
        ipa_utils.ipa_run('dnsrecord-mod', args, record=True)
        if ip_only:
            utils.display_success()

def _transform_delete_options(argument, options):
    _validate_blacklist_hosts(argument)
    return OptionTransformer(argument, options).\
        set_option('updatedns').\
        options

def _validate_blacklist_hosts(argument, options={}):
    # need to check the argument against both qualified and unqualified host names
    argument = re.sub(r'\..*$',"",argument)
    if argument in HOST_BLACKLIST:
        error = "The host " + argument + " is a restricted host"
        raise click.ClickException(error)
