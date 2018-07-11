import click
from collections import OrderedDict

import list_command
from list_command import field_with_same_name    	
import ipa_wrapper_command
import ipa_utils
from exceptions import IpaRunError

HOSTGROUP_LIST_FIELD_CONFIGS = OrderedDict([
	('Host group name', field_with_same_name),
	('Description', field_with_same_name),
	('HGID', field_with_same_name),
])

HOSTGROUP_SHOW_FIELD_CONFIGS = HOSTGROUP_LIST_FIELD_CONFIGS.copy()
HOSTGROUP_SHOW_FIELD_CONFIGS.update([
	('Member hosts', field_with_same_name),
])

HOSTGROUP_OPTIONS = {
	'--desc':{'help': 'Host group description'}
}
# TODO enter blacklist hostgroups
HOSTGROUP_BLACKLIST = []

def add_commands(directory):

	@directory.group(help='Manage host groups')
	def hostgroup():
		pass

	@hostgroup.command(help='List all host groups')
	def list():
		list_command.do(
			ipa_find_command='hostgroup-find',
			field_configs=HOSTGROUP_LIST_FIELD_CONFIGS,
			# TODO sort out the sort of the list results &
			#sort_key='HGID',
			#blacklist_key='Host group name',
			blacklist_val_array=HOSTGROUP_BLACKLIST,
		)
	
	@hostgroup.command(help='Show detailed information on one host group')
	#this line gives the host group's name as an argument to the command call above
	@click.argument('hostgroup_name')
	def show(hostgroup_name):
		_validate_blacklist_hostgroups(hostgroup_name)
		## i don't understand this line
		hostgroup_find_args = ['--hostgroup-name={}'.format(hostgroup_name)]
		try:
			list_command.do(
				#should this be -show?
				ipa_find_command='hostgroup-find',
				ip_find_args=hostgroup_find_args,
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
		ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)

	@hostgroup.command(name='remove-member', help='Remove host(s) from a host group') 
	@click.argument('hostgroup_name')
	@click.argument('hosts', nargs=-1)
	def remove_member(hostgroup_name, hosts):
		_validate_blacklist_hostgroups(hostgroup_name, hosts)
		host_options = ['--hosts={}'.format(host) for host in host]
		ipa_command = 'hostgroup-remove-member'
		args = [hostgroup_name] + host_options
		ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)


	wrapper_commands = [
		ipa_wrapper_command.create(
			'create',
			ipa_command='hostgroup-add',
			argument_name='name',
			options=HOSTGROUP_OPTIONS,
			transform_options_callback=_validate_blacklist_hostgroups,
			handle_result_callback=_handle_create_result,
			help='Create a new host group',
		),
		ipa_wrapper_command.create(
			'modify',
			ipa_command='hostgroup-mod',
			argument_name='name',
			options=HOSTGROUP_OPTIONS,
			transform_options_callback=_validate_blacklist_hostgroups,
			handle_result_callback=_handle_modify_result,
			help='Modify an existing host group',
		),
		ipa_wrapper_command.create(
			'delete',
			ipa_command='hostgroup-del',
			argument_name='name',
			options=HOSTGROUP_OPTIONS,
			transform_options_callback=_validate_blacklist_hostgroups,
			handle_result_callback=_handle_delete_result,
			help='Delete a host group',
		)
	]

	for command in wrapper_commands:
		hostgroup.add_command(command)

def _validate_blacklist_hostgroups(argument, options={}):
	if argument in HOSTGROUP_BLACKLIST:
		error = "The host group " + argument + " is a resricted hostgroup"
		raise click.ClickException(error)

def _handle_create_result(hostname, options, result):
	pass	

def _handle_modify_result(hostname, options, result):
	pass

def _handle_delete_result(hostname, options, result):
	pass

