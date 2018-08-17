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
	    blacklist_key='Host name',
	    blacklist_val_array=_expand_host_blacklist(),
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
            options=_delete_options(),
            transform_options_callback=_transform_delete_options,
            help='Delete existing host'
        )]
	
    for command in wrapper_commands:
        host.add_command(command)

def _all_hosts():
    public_hosts = ipa_utils.ipa_find('host-find')
    return public_hosts


def _all_hostgroups():
    public_hostgroups = ipa_utils.ipa_find('hostgroup-find')
    return public_hostgroups

def _host_options():
    return {
        '--password': {'help': 'Host password'},
	'--ip-address': {'help': 'IP address of host'},
    }

def _delete_options():
    return {
        '--remove-dns': {
            'help': 'Remove A, AAAA, SSHFP and PTR records of the host',
            'is_flag': True
        }
    }

def _transform_create_options(argument, options):
	_validate_blacklist_hosts(argument)
	return options

def _transform_modify_options(argument,options):
    _validate_blacklist_hosts(argument)
    # ipa handles host ip addresses differently from other data so a conditional is
    #   neccessary for if a user's trying to modify a host's ip
    if not options['ip-address'] == None:
        _modify_ip(argument, new_ip=options['ip-address'])
        del options['ip-address']
    return options

def _modify_ip(argument, new_ip):
    # it is required to find the host's domain name
    host = {}
    all_hosts = _all_hosts()
    for host_data in all_hosts:
        #TODO check this can't cause conflicts, can two hosts have the same server name?
        # this or stmt is neccessary as modify can be called with either qualified or unqualified host name as its argument
        if host_data['serverhostname'][0] == argument or host_data['Host name'][0] == argument:
            host = host_data
            break
    if not host == {}:
        host_name = host['Host name'][0]
        domain_name = re.sub(r'^.*?\.',"",host_name)
        host_label = re.sub(r'\..*$',"",host_name)
        args = [domain_name, host_label , '--a-rec='+new_ip]
        ipa_utils.ipa_run('dnsrecord-mod', args, record=True)
    else:
        error = "Host " + argument + " not found"
        raise click.ClickException(error)

def _transform_delete_options(argument, options):
    _validate_blacklist_hosts(argument)
    return OptionTransformer(argument, options).\
        rename_flag_option('remove_dns', 'updatedns').\
        options

def _validate_blacklist_hosts(argument, options={}):
    # need to check the argument against both qualified and unqualified host names
    argument = re.sub(r'\..*$',"",argument)
    if argument in HOST_BLACKLIST:
        error = "The host " + argument + " is a restricted host"
        raise click.ClickException(error)

def _expand_host_blacklist():
    _modified_host_blacklist = HOST_BLACKLIST
    all_hosts =  _all_hosts()
    for host_data in all_hosts:
        if host_data['serverhostname'][0] in _modified_host_blacklist:
            _modified_host_blacklist= _modified_host_blacklist + [host_data['Host name'][0]]
    return _modified_host_blacklist
