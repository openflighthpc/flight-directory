import click
from collections import OrderedDict

import list_command
from list_command import \
	field_with_same_name, \
	field_with_name, \
	hostgroup_with_host_hgid
import ipa_wrapper_command
import ipa_utils
import appliance_cli.text as text
import appliance_cli.utils
import utils
from exceptions import IpaRunError
from option_transformer import OptionTransformer

HOST_LIST_FIELD_CONFIGS = OrderedDict([
	('Host name', field_with_same_name),
	('Password', field_with_same_name),
	('HID', field_with_same_name),
	('Host IP', field_with_same_name),
])

HOST_SHOW_FIELD_CONFIGS = HOST_LIST_FIELD_CONFIGS.copy()
HOST_SHOW_FIELD_CONFIGS.update([
])

# TODO add host blacklist
HOST_BLACKLIST = []


def add_commands(directory):
	
	@directory.group(help='Perform host management tasks')
	def host():
		pass

	@host.command(help='List all hosts')
	def list():
		list_command.do(
			ipa_find_command='host-find',
			field_configs=HOST_LIST_FIELD_CONFIGS,
			#TODO sort the sorting of the list results
			#sort_key='HID',
			generate_additional_data=_additional_data_for_list,
			blacklist_key='Host name',
			blacklist_val_array=HOST_BLACKLIST,
		)

	@host.command(help='Show detailed information on a host')		
	#need to decide on identifier
	@click.argument('hostname')
	def show(hostname):
		_validate_blacklist_hosts(hostname)
		host_find_args = ['--hostname={}'.format(hostname)]
		try:
			list_command.do(
				#or should this be 'host-show'(though it isn't in stu's code)?
				ipa_find_command='host-find',
				ipa_find_args=host_find_args,
				field_configs=HOST_SHOW_FIELD_CONFIGS,
				generate_additional_data=_additional_data_for_list,
				display=list_command.list_displayer
			)
		except IpaRunError:
			# No matching host found; for consistency raise error with similar
			# format to IPA errors.
			error = '{}: host not found'.format(identifier)
			raise click.ClickException(error)
	
	wrapper_commands = [
		ipa_wrapper_command.create(
			'create',
			ipa_command='host-add',
			argument_name='hostname',
			options=_host_options(),
			transform_options_callback=_transform_create_options,
			handle_result_callback=_handle_create_result,
			help='Create new host'
		),
		ipa_wrapper_command.create(
			'modify',
			ipa_command='host-mod',
			argument_name='hostname',
			options=_host_options(),
			transform_options_callback=_transform_modify_options,
			handle_result_callback=_handle_modify_result,
			help='Modify existing host'
		),
		ipa_wrapper_command.create(
			'delete',
			ipa_command='host-disable',
			argument_name='hostname',
			handle_result_callback=_handle_delete_result,
			help='Delete existing host'
        )]
	
	for command in wrapper_commands:
		host.add_command(command)

def _additional_data_for_list():
	return{
		'hostgroups': _hostgroups_by_hgid()
	}

def _hostgroups_by_hgid():
	hostgroups_by_hgid = {}
	for hostgroup_data in _all_hostgroups():
		try:
			hgid = hostgroup_data['HGID'][0]
			hostgroups_by_hgid[hgid] = hostgroup_data
		except KeyError:
			#some hostgroups don't have ID's, they can skipped over
			continue
		return hostgroups_by_hgid	

def _all_hostgroups():
	public_hostgroups = ipa_utils.ipa_find('hostgroup-find')
	#private_hostgroups = ipa_utils.ipa_find('hostgroup-find', ['--private'])
	return public_hostgroups# + private_hostgroups

def _host_options():
	return {
		'--password': {'help': 'Host password'},
		'--ip-address': {'help': 'IP address of host'},
		'--hid':{'help': 'The ID of the host'}
	}

def _transform_create_options(argument, options):
	_validate_blacklist_hosts(argument)
	_validate_create_hid(options['hid'])
	return OptionTransformer(argument, options).\
		options

def _validate_create_hid(hid):
	try:
		host_find_args = ['--hid={}'.format(hid)]
		matching_host_hid = ipa_utils.ipa_find('host-find', host_find_args)
	except IpaRunError:
		#if no user with the hid exists capture the runtime error
		matching_host_hid = []
	if matching_host_hid: 
		error = "Host with hid " + hid + " already exists"
		raise click.ClickException(error)

def _validate_blacklist_hosts(argument, options={}):
	if argument in HOST_BLACKLIST:
		error = "The host " + argument + " is a restricted host"
		raise click.ClickException(error)

def _transform_modify_options(argument, options):
	return OptionTransformer(argument, options).\
		options

def _handle_create_result(hostname, options, result):
	pass	

def _handle_modify_result(hostname, options, result):
	pass

def _handle_delete_result(hostname, options, result):
	pass

def _handle_new_temporary_password():
	pass

def _handle_removed_password():
	pass


