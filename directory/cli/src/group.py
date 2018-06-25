
import click
from collections import OrderedDict

import list_command
from list_command import field_with_same_name
import ipa_wrapper_command
import ipa_utils
from exceptions import IpaRunError


GROUP_LIST_FIELD_CONFIGS = OrderedDict([
    ('Group name', field_with_same_name),
    ('Description', field_with_same_name),
    ('GID', field_with_same_name),
])

GROUP_SHOW_FIELD_CONFIGS = GROUP_LIST_FIELD_CONFIGS.copy()
GROUP_SHOW_FIELD_CONFIGS.update([
    ('Member users', field_with_same_name),
])

GROUP_OPTIONS = {
    '--desc': {'help': 'Group description'}
}


def add_commands(directory):

    @directory.group(help='Perform group management tasks')
    def group():
        pass

    @group.command(help='List all groups')
    def list():
        list_command.do(
            ipa_find_command='group-find',
            field_configs=GROUP_LIST_FIELD_CONFIGS,
            sort_key='Group name'
        )

    @group.command(help='Show detailed information on a group')
    @click.argument('group_name')
    def show(group_name):
        group_find_args = ['--group-name={}'.format(group_name)]
        try:
            list_command.do(
                ipa_find_command='group-find',
                ipa_find_args=group_find_args,
                field_configs=GROUP_SHOW_FIELD_CONFIGS,
                display=list_command.list_displayer
            )
        except IpaRunError:
            # No matching group found
            error = '{}: group not found'.format(group_name)
            raise click.ClickException(error)


    # TODO duplication
    @group.command(name='add-member', help='Add user(s) to a group')
    @click.argument('group_name')
    @click.argument('users', nargs=-1)
    def add_member(group_name, users):
        user_options = ['--users={}'.format(user) for user in users]
        ipa_command = 'group-add-member'
        args = [group_name] + user_options
        ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)

    @group.command(name='remove-member', help='Remove user(s) from a group')
    @click.argument('group_name')
    @click.argument('users', nargs=-1)
    def remove_member(group_name, users):
        user_options = ['--users={}'.format(user) for user in users]
        ipa_command = 'group-remove-member'
        args = [group_name] + user_options
        ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)

    wrapper_commands = [
        ipa_wrapper_command.create(
            'create',
            ipa_command='group-add',
            argument_name='name',
            options=GROUP_OPTIONS,
            help='Create a new group',
        ),
        ipa_wrapper_command.create(
            'modify',
            ipa_command='group-mod',
            argument_name='name',
            options=GROUP_OPTIONS,
            help='Modify an existing group',
        ),
        ipa_wrapper_command.create(
            'delete',
            ipa_command='group-del',
            argument_name='name',
            help='Delete a group',
        )
    ]

    for command in wrapper_commands:
        group.add_command(command)
