import click
from collections import OrderedDict

from config import CONFIG
import list_command
from list_command import \
	field_with_same_name, \
	field_with_name, \
	hostgroup_with_host_group_name, \
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

# TODO add host blacklist
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
			generate_additional_data=_additional_data_for_list,
			blacklist_key='Host name',
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
				generate_additional_data=_additional_data_for_list,
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
			help='Modify existing host'
		),
		ipa_wrapper_command.create(
			'delete',
			ipa_command='host-del',
			argument_name='hostname',
			help='Delete existing host'
        )]
	
	for command in wrapper_commands:
		host.add_command(command)

def _additional_data_for_list():
	return{
		'ip-address': _get_ip(),
		'hostgroups': _hostgroups_by_name()
	}

def _get_ip():
	host_ips_by_name = {}
	for host_data in _all_hosts():
		try:	
			command = 'dnsrecord-find'
			host_name = host_data['Host name'][0]
			host_name_text = re.sub(r'\..*$',"",host_name)
			domain_name = re.sub(r'^.*?\.',"",host_name)
			host_name_instruct = '--name='+host_name_text
			args = [domain_name, host_name_instruct]

			ip_result = ipa_utils.ipa_run(command, args, record=False)
			ip_result_parsed = ipa_utils.parse_find_output(ip_result)
			ip_address_dict = ip_result_parsed[0]
			ip_address_list = ip_address_dict["A record"]
			host_ips_by_name[host_name] = ip_address_list
		except KeyError:
			continue	
	return host_ips_by_name
	
def _hostgroups_by_name():
	hostgroups_by_name = {}
	for hostgroup_data in _all_hostgroups():
		try:
			host_group_name = hostgroup_data['Host-group'][0]
			hostgroups_by_name[host_group_name] = hostgroup_data
		except KeyError:
			continue
	return hostgroups_by_name	

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

def _transform_create_options(argument, options):
	_validate_blacklist_hosts(argument)
	return options

def _validate_blacklist_hosts(argument, options={}):
	if argument in HOST_BLACKLIST:
		error = "The host " + argument + " is a restricted host"
		raise click.ClickException(error)

