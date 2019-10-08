
import click
from collections import OrderedDict

import list_command
from list_command import field_with_same_name
import ipa_wrapper_command
import ipa_utils
import utils
import logger
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
    '--desc': {'help': 'Group description'},
    '--gid': {'help': 'Group ID Number'},
}

GROUP_BLACKLIST = [
        'ipausers',
        'trust admins',
        'adminusers',
        'admins',
        'editors',
        'clusterusers',
        'alces-cluster'
    ]

def add_commands(directory):

    @directory.group(help='Perform group management tasks')
    def group():
        pass

    @group.command(help='List all groups')
    def list():
        list_command.do(
            ipa_find_command='group-find',
            all_fields=False,
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


    @group.group(name='member', help='Handle group membership')
    def member():
        pass

    # TODO duplication
    if utils.advanced_mode_enabled():
        @member.command(name='add', help='Add user(s) to a group')
        @click.argument('group_name')
        @click.argument('users', nargs=-1, required=True)
        def add_member(group_name, users):
            _validate_blacklist_groups(group_name, users)
            user_options = ['--users={}'.format(user) for user in users]
            ipa_command = 'group-add-member'
            args = [group_name] + user_options
            try:
                ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)
                utils.display_success()
                _run_post_command_script('POST_MEMBER_ADD_SCRIPT', users)
            except IpaRunError:
                _diagnose_member_command_error(group_name, users, add_command=True)

    @member.command(name='remove', help='Remove user(s) from a group')
    @click.argument('group_name')
    @click.argument('users', nargs=-1, required=True)
    def remove_member(group_name, users):
        _validate_blacklist_groups(group_name, users)
        user_options = ['--users={}'.format(user) for user in users]
        ipa_command = 'group-remove-member'
        args = [group_name] + user_options
        try:
            ipa_utils.ipa_run(ipa_command, args, error_in_stdout=True)
            utils.display_success()
            _run_post_command_script('POST_MEMBER_REMOVE_SCRIPT', users)
        except IpaRunError:
            _diagnose_member_command_error(group_name, users, add_command=False)

    if not utils.advanced_mode_enabled():
        @click.argument('GID', required=False)
        @click.argument('desc', required=False)
        @click.argument('Name', required=False)
        @group.command(name='create', help="""
Create a new group.

Optionally, ignore all arguments to be prompted for values.
        """.strip())
        def create(name, desc, gid):
            wrapper = ipa_wrapper_command.create_ipa_wrapper(
                'group-add',
                argument_name='name',
                transform_options_callback=_validate_blacklist_groups
            )

            if all(a is not None for a in [name, desc]):
                params = OrderedDict([
                    ('name', name),
                    ('desc', desc)
                ])
                if gid: params = { **params, 'gid': gid }
            elif name is not None:
                error = """
Please provide a name and a description.
Optionally a GID can also be provided, otherwise one will be auto-generated.
Leave all fields blank to be prompted for values.""".strip()
                raise click.ClickException(error)
            else:
                click.echo('Please enter details for the following:')

                params = OrderedDict([
                    ('name', click.prompt('  Group name')),
                    ('desc', click.prompt('  Description'))
                ])
                if click.confirm("""
Would you like to set a specific GID for this group? (Default: Autogenerated GID)
                """.strip()):
                    params = { **params, 'gid': click.prompt('  GID') }

            wrapper(**params)

            logger.log_simple_cmd(params)

        @click.argument('desc', required=False)
        @click.argument('name', required=False)
        @group.command(name='modify', help="""
Modify an existing group.

Optionally, ignore all arguments to be prompted for values.
        """)
        def modify(name, desc):
            args = locals()
            wrapper = ipa_wrapper_command.create_ipa_wrapper(
                'group-mod',
                argument_name='name',
            )

            if all(a is not None for a in args.values()):
                _validate_blacklist_groups(args['name'])
                params = OrderedDict([])
                for arg, value in args.items():
                    if value != "":
                        params.update({arg:value})
            elif name is not None:
                error = """
Please provide a login, a first name, a last name and an email.
To leave a field unchanged, enter "".
Leave all fields blank to be prompted for values.""".strip()
                raise click.ClickException(error)
            else:
                click.echo('Please enter the name of the group you want to modify:')
                group = click.prompt('  Group name')
                group_find_args = ['--group-name={}'.format(group)]
                try:
                    group_data = ipa_utils.ipa_find(
                            'group-find',
                            group_find_args,
                            all_fields=True
                    )[0]
                except IpaRunError:
                    error = '{}: group not found'.format(group)
                    raise click.ClickException(error)

                _validate_blacklist_groups(group)

                click.echo(
                    'Adjust the following fields as necessary:\n'
                    'Leave blank to keep current value shown within brackets'
                )

                params = OrderedDict([
                    ('name', group),
                    ('desc', click.prompt(
                        '  Description',
                        default=group_data['Description'][0]
                    ))
                ])

            wrapper(**params)

            logger.log_simple_cmd(params)

        @member.command(name='add', help='Add user(s) to a group')
        def add_member():
            click.echo('Please enter the name of the group you wish to add to:')
            group = click.prompt('  Group name')
            _validate_blacklist_groups(group)

            click.echo(
                'Please enter the user(s) you wish to add to %s, separated by spaces:' % group
            )
            users = click.prompt('  User(s)').split()
            user_options = ['--users={}'.format(user) for user in users]

            args = [group] + user_options
            try:
                ipa_utils.ipa_run('group-add-member', args, error_in_stdout=True)
                utils.display_success()
                _run_post_command_script('POST_MEMBER_ADD_SCRIPT', users)
            except IpaRunError:
                _diagnose_member_command_error(group, users, add_command=True)

            logger.log_cmd(args)

    advanced_ipa_wrapper_commands = [
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

    if utils.advanced_mode_enabled():
        for command in advanced_ipa_wrapper_commands:
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
        groups_found = ipa_utils.ipa_find('group-find', group_find_args, all_fields=False)
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
            users_found = ipa_utils.ipa_find('user-find', user_find_args, all_fields=False)
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
            groups_found = ipa_utils.ipa_find('group-find', group_find_args, all_fields=False)
            #if the user's in the group the cmd's trying to add them to, that's an error
            if add_command:
                error = error + "User " + user + " already in the group"
                raise click.ClickException(error)
        except IpaRunError:
            # if the user's not in the group & the cmd's is trying to remove them, that's an error
            if not add_command:
                error = error + "User " + user + " not in the group"
                raise click.ClickException(error)

    error = "Unknown error"
    raise click.ClickException(error)

def _run_post_command_script(command, args):
    script_location = utils.get_user_config(command)

    if script_location:
        try:
            script_result = subprocess.run([script_location, args], check=True)
        except PermissionError:
            raise click.ClickException(
                "Cannot execute post command script - you need permissions to execute '{}'."
                .format(script_location)
            )
        except OSError:
            raise click.ClickException(
                "Userware is unable to execute the script at '{}' ".format(script_location) + \
                "- please check the script exists and that it has a shebang line at its start"
            )
        except subprocess.CalledProcessError as ex:
            error = script_result.stdout if error_in_stdout else script_result.stderr
            raise IpaRunError(error) from ex

