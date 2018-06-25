
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
    ('Login shell', field_with_same_name),
    ('Email address', field_with_same_name),
    ('Account disabled', field_with_same_name),
    ('SSH public key', field_with_same_name),
])


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
            generate_additional_data=_additional_data_for_list
        )

    @user.command(help='Show detailed information on a user')
    @click.argument('login')
    def show(login):
        user_find_args = ['--login={}'.format(login)]
        try:
            list_command.do(
                ipa_find_command='user-find',
                ipa_find_args=user_find_args,
                field_configs=USER_SHOW_FIELD_CONFIGS,
                generate_additional_data=_additional_data_for_list,
                display=list_command.list_displayer
            )
        except IpaRunError:
            # No matching user found; for consistency raise error with similar
            # format to IPA errors.
            error = '{}: user not found'.format(login)
            raise click.ClickException(error)

    wrapper_commands = [
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
            handle_result_callback=_handle_delete_result,
            help='Delete a user',
        )
    ]

    for command in wrapper_commands:
        user.add_command(command)


def _additional_data_for_list():
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
    public_groups = ipa_utils.ipa_find('group-find')
    private_groups = ipa_utils.ipa_find('group-find', ['--private'])
    return public_groups + private_groups


def _user_options(require_names=True):
    return {
        '--first': {'help': 'First name', 'required': require_names},
        '--last': {'help': 'Last name', 'required': require_names},
        '--shell': {'help': 'Login shell'},
        '--email': {'help': 'Email address'},
        '--uid': {'help': 'User ID Number'},
        '--gidnumber': {'help': 'Group ID Number'},
        '--key': {'help': 'SSH public key'},
    }


def _create_options():
    return {
        **_user_options(),
        '--no-password': {
            'help': 'Do not generate temporary password',
            'is_flag': True,
        }
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


def _transform_create_options(argument, options):
    _validate_create_uid(options['uid'])
    return OptionTransformer(argument, options).\
        rename_and_invert_flag_option('no_password', 'random').\
        rename_option('key', 'sshpubkey').\
        options


def _validate_create_uid(uid):
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


def _transform_modify_options(argument, options):
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
    _handle_new_temporary_password(login, options, result)


def _handle_modify_result(login, options, result):
    _handle_new_temporary_password(login, options, result)
    if options['remove_password']:
        _handle_removed_password(login, options, result)


def _handle_delete_result(login, options, result):
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
