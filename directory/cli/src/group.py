
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

GROUP_BLACKLIST = ['ipausers', 'trust admins', 'adminusers', 'admins', 'editors']

def add_commands(directory):

    @directory.group(help='Perform group management tasks')
    def group():
        pass

    @group.command(help='List all groups')
    def list():
        list_command.do(
            ipa_find_command='group-find',
            field_configs=GROUP_LIST_FIELD_CONFIGS,
            sort_key='Group name',
            blacklist_key='Group name',
            blacklist_val_array=GROUP_BLACKLIST
        )

    @group.command(help='Show detailed information on a group')
    @click.argument('group_name')
    def show(group_name):
        _validate_blacklist_groups(group_name)
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
    @click.argument('users', nargs=-1, required=True)
    def add_member(group_name, users):
        _validate_blacklist_groups(group_name, users)
        user_options = ['--users={}'.format(user) for user in users]
        ipa_command = 'group-add-member'
        args = [group_name] + user_options
        try:
            ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)
        except IpaRunError:
            _diagnose_member_command_error(group_name, users, add_command=True)

    @group.command(name='remove-member', help='Remove user(s) from a group')
    @click.argument('group_name')
    @click.argument('users', nargs=-1, required=True)
    def remove_member(group_name, users):
        _validate_blacklist_groups(group_name, users)
        user_options = ['--users={}'.format(user) for user in users]
        ipa_command = 'group-remove-member'
        args = [group_name] + user_options
        try:
            ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)
        except IpaRunError:
            _diagnose_member_command_error(group_name, users, add_command=False)

    wrapper_commands = [
        ipa_wrapper_command.create(
            'create',
            ipa_command='group-add',
            argument_name='name',
            options=GROUP_OPTIONS,
            transform_options_callback=_validate_blacklist_groups,
            help='Create a new group',
        ),
        ipa_wrapper_command.create(
            'modify',
            ipa_command='group-mod',
            argument_name='name',
            options=GROUP_OPTIONS,
            transform_options_callback=_validate_blacklist_groups,
            help='Modify an existing group',
        ),
        ipa_wrapper_command.create(
            'delete',
            ipa_command='group-del',
            argument_name='name',
            transform_options_callback=_validate_blacklist_groups,
            help='Delete a group',
        )
    ]

    for command in wrapper_commands:
        group.add_command(command)


def _validate_blacklist_groups(argument, options={}):
    if argument in GROUP_BLACKLIST:
        error = "The group " + argument + " is a restricted group"
        raise click.ClickException(error)
    return options


#add-member & remove-member commands were erroring silently so this method was needed
def _diagnose_member_command_error(group_name, users, add_command=False):
    if add_command:
        error = "Group-add error: "
    else:
        error = "Group-remove error: "

    # first checking if group exists
    try:
        group_find_args = ['--group-name={}'.format(group_name)]
        groups_found = ipa_utils.ipa_find('group-find', group_find_args)
    except IpaRunError:
        error = error + '{} - group not found'.format(group_name)
        raise click.ClickException(error)

    # the other errors are non-castrophic, the command still goes through
    error = "Non-fatal " + error.lower()
    # next checking if each user in users exists
    user_not_found = None
    for user in users:
        try:
            user_find_args = ['--login={}'.format(user)]
            users_found = ipa_utils.ipa_find('user-find', user_find_args)
        except IpaRunError:
            user_not_found = user
            break
    if user_not_found:
        error = error + '{} - user not found'.format(user_not_found)
        raise click.ClickException(error)

    #check if the any of the users already are/aren't in the group
    for user in users:
        try:
            group_find_args = ['--group-name={}'.format(group_name), '--users={}'.format(user)]
            groups_found = ipa_utils.ipa_find('group-find', group_find_args)
            #if the user's in the group the cmd's trying to add them to, that's an error
            if add_command:
                error = error + "User " + user + " already in the group"
                raise click.ClickException(error)
        except IpaRunError:
            # if the user's not in the group & the cmd's is trying to remove them, that's an error
            if not add_command:
                error = error + "User " + user + " not in the group"
                raise click.ClickException(error)

    error = error + "Unknown error"
    raise click.ClickException(error)
