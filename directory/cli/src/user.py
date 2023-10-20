#==============================================================================
# Copyright (C) 2019-present Alces Flight Ltd.
#
# This file is part of Flight Directory.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License 2.0 which is available at
# <https://www.eclipse.org/legal/epl-2.0>, or alternative license
# terms made available by Alces Flight Ltd - please direct inquiries
# about licensing to licensing@alces-flight.com.
#
# Flight Directory is distributed in the hope that it will be useful, but
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
# IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
# OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
# PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
# details.
#
# You should have received a copy of the Eclipse Public License 2.0
# along with Flight Directory. If not, see:
#
#  https://opensource.org/licenses/EPL-2.0
#
# For more information on Flight Directory, please visit:
# https://github.com/openflighthpc/flight-directory
#==============================================================================

import click
from collections import OrderedDict

import list_command
from list_command import \
    field_with_same_name, \
    field_with_name, \
    group_with_users_gid
import ipa_wrapper_command
import ipa_utils
import appliance_cli.text as text
import appliance_cli.utils
import utils
import subprocess
import logger
from exceptions import IpaRunError
from option_transformer import OptionTransformer


USER_LIST_FIELD_CONFIGS = OrderedDict([
    ('User login', field_with_same_name),
    ('Full name', field_with_same_name),
    ('UID', field_with_same_name),
    ('GID', field_with_same_name),
    ('Primary group', group_with_users_gid),
    ('Secondary groups', field_with_name('Member of groups')),
])

USER_SHOW_FIELD_CONFIGS = USER_LIST_FIELD_CONFIGS.copy()
USER_SHOW_FIELD_CONFIGS.update([
    ('Home directory', field_with_same_name),
    ('GECOS', field_with_same_name),
    ('Login shell', field_with_same_name),
    ('Email address', field_with_same_name),
    ('Account disabled', field_with_same_name),
    ('SSH public key', field_with_same_name),
])

USER_BLACKLIST = ['admin', 'alces-cluster']
USER_BLACKLIST.extend(utils.user_blacklist())

def add_commands(directory):

    @directory.group(help='Perform user management tasks')
    def user():
        pass

    @user.command(help='List all users')
    def list():
        list_command.do(
            ipa_find_command='user-find',
            field_configs=USER_LIST_FIELD_CONFIGS,
            sort_key='UID',
            generate_additional_data=_additional_data_for_list,
            blacklist_key='User login',
            blacklist_val_array=USER_BLACKLIST
        )

    @user.command(help='Show detailed information on a user')
    @click.argument('login')
    def show(login):
        _validate_blacklist_users(login)
        user_find_args = ['--login={}'.format(login)]
        try:
            list_command.do(
                ipa_find_command='user-find',
                ipa_find_args=user_find_args,
                field_configs=USER_SHOW_FIELD_CONFIGS,
                generate_additional_data=_additional_data_for_show,
                display=list_command.list_displayer
            )
        except IpaRunError:
            # No matching user found; for consistency raise error with similar
            # format to IPA errors.
            error = '{}: user not found'.format(login)
            raise click.ClickException(error)

    if not utils.advanced_mode_enabled():
        @click.argument('UID', required=False)
        @click.argument('email', required=False)
        @click.argument('last', required=False)
        @click.argument('first', required=False)
        @click.argument('login', required=False)
        @user.command(help="""
Create a new user.

Optionally, ignore all arguments to be prompted for values.
        """)
        def create(login, first, last, email, uid):
            wrapper = ipa_wrapper_command.create_ipa_wrapper(
                'user-add',
                argument_name='login',
                transform_options_callback=_transform_create_options,
                handle_result_callback=_handle_create_result,
            )

            if all(a is not None for a in [login, first, last, email]):
                params = OrderedDict([
                            ('login', login),
                            ('first', first),
                            ('last', last),
                            ('email', email),
                ])
                if uid: params = { **params, 'uid': uid }
            elif login is not None:
                error = """
Please provide a login, a first name, a last name and an email.
Optionally a UID can also be provided, otherwise one will be auto-generated.
Leave all fields blank to be prompted for values.""".strip()
                raise click.ClickException(error)
            else:
                click.echo('Please enter details for the following:')

                params = OrderedDict([
                            ('login', click.prompt('  Username')),
                            ('first', click.prompt('  First name')),
                            ('last', click.prompt('  Surname')),
                            ('email', click.prompt('  Email')),
                ])
                if click.confirm("""
Would you like to set an SSH public key? (Default: No)
                """.strip()):
                    params = { **params, 'key': click.prompt('  SSH key') }
                if click.confirm("""
Would you like to set a specific UID for this user? (Default: Autogenerated UID)
                """.strip()):
                    params = { **params, 'uid': click.prompt('  UID') }

            wrapper(**params)

            logger.log_simple_cmd(params)

        @click.argument('key', required=False)
        @click.argument('email', required=False)
        @click.argument('last', required=False)
        @click.argument('first', required=False)
        @click.argument('login', required=False)
        @user.command(help="""
Modify an existing user.

Optionally, ignore all arguments to be prompted for values.
        """)
        def modify(login, first, last, email, key):
            args = locals()
            wrapper = ipa_wrapper_command.create_ipa_wrapper(
                'user-mod',
                argument_name='login',
                transform_options_callback=_transform_modify_options,
                handle_result_callback=_handle_modify_result,
            )

            if all(a is not None for a in args.values()):
                _validate_blacklist_users(args['login'])
                params = OrderedDict([])
                for arg, value in args.items():
                    if value != "":
                        params.update({arg:value})
            elif login is not None:
                error = """
Please provide a login, a first name, a last name, an email and an SSH public key.
To leave a field unchanged, enter "".
Leave all fields blank to be prompted for values.""".strip()
                raise click.ClickException(error)
            else:
                click.echo("""
Please enter the name of the user you want to modify:
                """.strip())
                user = click.prompt('  Username')
                user_find_args = ['--login={}'.format(user)]
                try:
                    user_data = ipa_utils.ipa_find(
                            'user-find',
                            user_find_args,
                            all_fields=True
                    )[0]
                except IpaRunError:
                    # Matches error shown for user show, can extract logic to a method
                    # in the future
                    error = '{}: user not found'.format(user)
                    raise click.ClickException(error)

                _validate_blacklist_users(user)

                click.echo(
                    'Adjust the following fields as necessary:\n'
                    'Leave blank to keep current value shown within brackets'
                )

                params = OrderedDict([
                    ('login', user),
                    ('first', click.prompt(
                        '  First name',
                        default=user_data['First name'][0]
                    )),
                    ('last', click.prompt(
                        '  Surname',
                        default=user_data['Last name'][0]
                    )),
                    ('email', click.prompt(
                        '  Email',
                        default=user_data['Email address'][0]
                    )),
                ])
                ssh_key_list = user_data.get('SSH public key')
                ssh_key_default = ssh_key_list[0] if ssh_key_list else 'None'
                new_ssh = click.prompt('  SSH public key', default=ssh_key_default)
                if new_ssh != 'None':
                    params = { **params, 'key': new_ssh }

            wrapper(**params)

            logger.log_simple_cmd(params)

    base_ipa_wrapper_commands = [
        ipa_wrapper_command.create(
            'enable',
            ipa_command='user-enable',
            argument_name='login',
            transform_options_callback=_transform_options,
            help='Enable a user',
        ),
        ipa_wrapper_command.create(
            'disable',
            ipa_command='user-disable',
            argument_name='login',
            transform_options_callback=_transform_options,
            help='Disable a user',
        )
    ]

    advanced_ipa_wrapper_commands = [
        ipa_wrapper_command.create(
            'create',
            ipa_command='user-add',
            argument_name='login',
            options=_create_options(),
            transform_options_callback=_transform_create_options,
            handle_result_callback=_handle_create_result,
            help='Create a new user',
        ),
        ipa_wrapper_command.create(
            'modify',
            ipa_command='user-mod',
            argument_name='login',
            options=_modify_options(),
            transform_options_callback=_transform_modify_options,
            handle_result_callback=_handle_modify_result,
            help='Modify an existing user',
        ),
        ipa_wrapper_command.create(
            'delete',
            ipa_command='user-del',
            argument_name='login',
            transform_options_callback=_transform_options,
            handle_result_callback=_handle_delete_result,
            help='Delete a user',
        )
    ]

    wrapper_commands = base_ipa_wrapper_commands
    if utils.advanced_mode_enabled():
        wrapper_commands += advanced_ipa_wrapper_commands

    for command in wrapper_commands:
        user.add_command(command)

def _additional_data_for_list(item_dict=None):
    del item_dict
    return {
        'groups': _groups_by_gid()
    }


def _groups_by_gid():
    groups_by_gid = {}
    for group_data in _all_groups():
        try:
            gid = group_data['GID'][0]
            groups_by_gid[gid] = group_data
        except KeyError:
            # Sometimes groups don't have a GID (e.g. the `ipausers` group);
            # skip over these.
            continue
    return groups_by_gid

def _all_groups():
    # Want to get all groups, normal/public and private; I would have thought
    # there would be a single `ipa` command that would give these but AFAICT it
    # can only be done using both of these.
    public_groups = ipa_utils.ipa_find('group-find', all_fields=False)
    private_groups = ipa_utils.ipa_find('group-find', ['--private'], all_fields=False)
    return public_groups + private_groups

# split the additional data functions for list & show to save time
# only returns 1 private group, for the GID of the specified user
def _additional_data_for_show(item_dict):
    gid = item_dict['GID'][0]
    return {
        'groups': {
            gid : _users_primary_group(gid)[0]
        }
    }

def _users_primary_group(gid):
    group_find_args = ['--gid={}'.format(gid)]
    # will only find max one group between the two calls
    # if the first doesn't find the group it will error but continue due to `error_allowed`
    # if neither find it (i.e. if the GID is invalid) [{}] will be returned
    primary_group = ipa_utils.ipa_find('group-find', group_find_args + ['--private'], error_allowed='0 groups matched')
    if primary_group == [{}]:
        primary_group = ipa_utils.ipa_find('group-find', group_find_args, error_allowed='0 groups matched')
    return primary_group

def _user_options(require_names=True):
    return {
        '--first': {'help': 'First name', 'required': require_names},
        '--last': {'help': 'Last name', 'required': require_names},
        '--shell': {'help': 'Login shell'},
        '--email': {'help': 'Email address'},
        '--uid': {'help': 'User ID Number'},
        '--key': {'help': 'SSH public key'},
        '--homedir': {'help': 'Home directory'},
        '--gecos': {'help': 'GECOS field'},
    }


def _create_options():
    if utils.get_password_policy():
        return {
            **_user_options(),
            '--group': {
                'help': 'Specify a group to assign the user to on creation'
            },
            '--make-password': {
                'help': 'Generate a temporary password',
                'is_flag': True,
            },
        }
    else:
        return {
            **_user_options(),
            '--group': {
                'help': 'Specify a group to assign the user to on creation'
            },
            '--no-password': {
                'help': 'Do not generate temporary password',
                'is_flag': True,
            },
        }


def _modify_options():
    return {
        **_user_options(require_names=False),
        '--new-password': {
            'help': 'Generate new temporary password',
            'is_flag': True
        },
        '--remove-password': {
            'help': 'Remove password',
            'is_flag': True
        },
        '--remove-key': {
            'help': 'Remove SSH public key',
            'is_flag': True
        },
    }


def _transform_options(argument, options):
    _validate_blacklist_users(argument)
    return options

def _transform_create_options(argument, options):
    _validate_blacklist_users(argument)
    _validate_create_uid(options['uid'])

    options['gidnumber'] = _standard_default_user_gid()

    if utils.get_password_policy():
        return OptionTransformer(argument, options).\
            rename_flag_option('make_password', 'random').\
            rename_option('key', 'sshpubkey').\
            options
    else:
        return OptionTransformer(argument, options).\
            rename_and_invert_flag_option('no_password', 'random').\
            rename_option('key', 'sshpubkey').\
            options

def _validate_create_uid(uid):
    if not uid:
        return
    try:
        user_find_args = ['--uid={}'.format(uid)]
        matching_user_uid = ipa_utils.ipa_find('user-find', user_find_args)
    except IpaRunError:
        # If no user with UID exists capture the runtime error
        # and use empty array
        matching_user_uid = []
    if matching_user_uid:
        error = "User with uid '" + uid + "' already exists"
        raise click.ClickException(error)


def _validate_blacklist_users(argument, options={}):
    if argument in USER_BLACKLIST:
        error = "The user " + argument + " is a restricted user"
        raise click.ClickException(error)


def _transform_modify_options(argument, options):
    _validate_blacklist_users(argument)
    return OptionTransformer(argument, options).\
        rename_option('key', 'sshpubkey').\
        rename_flag_option('new_password', 'random').\
        delete_option('remove_key').\
        modify(_generate_remove_key_option).\
        delete_option('remove_password').\
        modify(_generate_remove_password_option).\
        modify(_generate_extra_name_options).\
        options


def _generate_remove_key_option(argument, options):
    if options['remove_key']:
        # No IPA option to explicitly remove a key, but can do this by passing
        # an empty string.
        return {'sshpubkey': ''}
    else:
        return {}


def _generate_remove_password_option(argument, options):
    if options['remove_password']:
        # No IPA option to remove a password, but can effectively achieve same
        # result by setting long, secure, random string, and keeping this
        # secret.
        return {'password': appliance_cli.utils.secure_random_string()}
    else:
        return {}


def _generate_extra_name_options(argument, options):
    new_first = options['first']
    new_last = options['last']

    if not (new_first or new_last):
        # We've not been given an option that requires us to pass any extra
        # name options.
        return {}

    if new_first and new_last:
        # We've been given both name parameters; we can just create the extra
        # name options without needing to find the current user.
        return _extra_name_options(new_first, new_last)

    user_find_args = ['--login={}'.format(argument)]
    try:
        matching_user_dicts = ipa_utils.ipa_find('user-find', user_find_args)
    except IpaRunError:
        # We can't find any matching user; the actual `ipa user-mod` command
        # should fail so return no extra options and just let this happen.
        return {}

    current_user = matching_user_dicts[0]
    current_first = current_user['First name'][0]
    current_last = current_user['Last name'][0]

    # Create the extra name options using the passed name parameter (if given)
    # and the current user name fields.
    first = new_first or current_first
    last = new_last or current_last
    return _extra_name_options(first, last)


def _extra_name_options(first_name, last_name):
    # `ipa user-mod` does not update the full name or display name when the
    # first or last name are changed, although these are initially created on
    # `ipa user-add` from these fields. To keep these in sync we need to create
    # the options to set these from the current first and last name and pass
    # them in.
    # TODO: we may want to create `initials`, `gecos` or other options here
    # too, as these are also created from the initial name options.

    full_name = '{} {}'.format(first_name, last_name)
    return {
        'cn': full_name,
        'displayname': full_name,
    }


def _handle_create_result(login, options, result):
    utils.run_post_command_script('POST_CREATE_SCRIPT', [login])
    _handle_new_temporary_password(login, options, result)


def _handle_modify_result(login, options, result):
    _handle_new_temporary_password(login, options, result)
    if options['remove_password']:
        _handle_removed_password(login, options, result)


def _handle_delete_result(login, options, result):
    utils.run_post_command_script('POST_DELETE_SCRIPT', [login])
    _handle_removed_password(login, options, result)


def _handle_new_temporary_password(login, options, result):
    # Details of user will be output in similar format to find output.
    item_dicts = ipa_utils.parse_find_output(result)
    user_dict = item_dicts[0]  # First and only item.

    if 'Random password' not in user_dict:
        # A new temporary password has not been generated; nothing to handle.
        return

    temporary_password = user_dict['Random password'][0]

    if utils.currently_importing():
        utils.set_imported_user_password(login, temporary_password)
    else:
        message = 'Generated temporary password for user {}: {}'.format(
            login, text.bold(temporary_password)
        )
        click.echo(message)


def _handle_removed_password(login, options, result):
    if utils.currently_importing():
        utils.remove_imported_user_entry(login)

def _standard_default_user_gid():
    # If a default GID is set within the config this takes precedence.
    # However if this value is absent or blank it will attempt to find the GID
    # of the clusterusers group
    return utils.get_user_config('DEFAULT_GID') or _get_group_id('clusterusers')

def _get_group_id(group):
    # If present the clusterusers group now takes precedence.
    # However as a last resort this will return None. This causes IPA to use
    # its default.
    try:
        return ipa_utils.ipa_find(
            'group-find',
            [group],
            all_fields=False
        )[0].get('GID')[0]
    except IpaRunError:
        # It might be worth adjusting this so that it only returns None when
        # the group can't be found. Currently this will catch all IPA run
        # errors which isn't ideal.
        return None
