
from unittest import mock

from directory import directory
import ipa_utils
import appliance_cli.utils
from appliance_cli.testing_utils import click_run


def test_user_create_includes_random_by_default(
    mocker
):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney', '--last', 'Rubble'],
        ['user-add',
            ['barney', '--first', 'Barney', '--last', 'Rubble', '--random']],
    )


def test_user_create_does_not_pass_random_when_given_no_password(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney',
            '--last', 'Rubble', '--no-password'],
        ['user-add', ['barney', '--first', 'Barney', '--last', 'Rubble']],
    )


def test_user_create_passes_sshpubkey_when_given_key(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney', '--last', 'Rubble',
            '--key', 'ssh-rsa somekey key_name'],
        ['user-add',
            ['barney', '--first', 'Barney', '--last', 'Rubble', '--random',
                '--sshpubkey', 'ssh-rsa somekey key_name']],
    )


# TODO: add tests for generating extra name options for `user modify` when
# given single name. Will need to mock `ipa_find` for user.

def test_user_modify_includes_nothing_extra_by_default(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney'],
        ['user-mod', ['barney']],
    )


def test_user_modify_includes_extra_names_when_given_names(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--first', 'Barney', '--last', 'Rubble'],
        ['user-mod',
            ['barney', '--cn', 'Barney Rubble', '--displayname',
             'Barney Rubble', '--first', 'Barney', '--last', 'Rubble']
         ]
    )


def test_user_modify_passes_random_when_given_new_password(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--new-password'],
        ['user-mod', ['barney', '--random']],
    )


def test_user_modify_passes_sshpubkey_when_given_key(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--key', 'ssh-rsa somekey key_name'],
        ['user-mod', ['barney', '--sshpubkey', 'ssh-rsa somekey key_name']],
    )


def test_user_modify_passes_empty_sshpubkey_when_given_remove_key(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--remove-key'],
        ['user-mod', ['barney', '--sshpubkey', '']],
    )


def test_user_modify_passes_random_password_when_given_remove_password(
        mocker, monkeypatch
):
    mock_password = 'thiswillactuallyberandom'
    monkeypatch.setattr(
        appliance_cli.utils, 'secure_random_string', lambda: mock_password
    )

    _test_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--remove-password'],
        ['user-mod', ['barney', '--password', mock_password]],
    )


def _test_options_passed_to_ipa(mocker, directory_command, ipa_run_arguments):
    mocker.spy(ipa_utils, 'ipa_run')

    click_run(directory, directory_command)

    assert ipa_utils.ipa_run.call_args_list == [
        mock.call(*ipa_run_arguments),
    ]
