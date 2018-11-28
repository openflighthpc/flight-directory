
from unittest import mock

import directory
import ipa_utils
import test_utils
import appliance_cli.utils

# This setup runs before every test ensuring that they are run in advanced mode
def setUpModule():
    test_utils.reload_in_advanced_mode()

def test_user_create_includes_random_by_default(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney', '--last', 'Rubble'],
        [
            (
                'group-find',
                [
                    [
                        'clusterusers',
                        '--sizelimit', '0'
                    ],
                    None
                ],
              { 'record': False }
            ),
            (
                'user-add',
                [
                    ['barney', '--first', 'Barney', '--last', 'Rubble', '--random']
                ]
            )
        ],
    )


def test_user_create_does_not_pass_random_when_given_no_password(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney',
            '--last', 'Rubble', '--no-password'],
        [
            (
                'group-find',
                [
                    [
                        'clusterusers',
                        '--sizelimit', '0'
                    ],
                    None
                ],
              { 'record': False }
            ),
            (
                'user-add',
                [
                    ['barney', '--first', 'Barney', '--last', 'Rubble']
                ]
            )
        ]
    )


def test_user_create_passes_sshpubkey_when_given_key(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney', '--last', 'Rubble',
            '--key', 'ssh-rsa somekey key_name'],
        [
            (
                'group-find',
                [
                    [
                        'clusterusers',
                        '--sizelimit', '0'
                    ],
                    None
                ],
              { 'record': False }
            ),
            (
                'user-add',
                [
                    ['barney', '--first', 'Barney', '--last', 'Rubble', '--random',
                '--sshpubkey', 'ssh-rsa somekey key_name']
                ]
            )
        ]
    )


# TODO: add tests for generating extra name options for `user modify` when
# given single name. Will need to mock `ipa_find` for user.

def test_user_modify_includes_nothing_extra_by_default(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney'],
        [
            (
                'user-mod',
                [
                    ['barney']
                ]
            )
        ]
    )


def test_user_modify_includes_extra_names_when_given_names(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--first', 'Barney', '--last', 'Rubble'],
        [
            (
                'user-mod',
                [
                    ['barney', '--cn', 'Barney Rubble', '--displayname',
                        'Barney Rubble', '--first', 'Barney', '--last', 'Rubble']
                ]
            )
         ]
    )


def test_user_modify_passes_random_when_given_new_password(mocker):
   test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--new-password'],
        [
            (
                'user-mod',
                [
                    ['barney', '--random']
                ]
            )
        ]
    )


def test_user_modify_passes_sshpubkey_when_given_key(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--key', 'ssh-rsa somekey key_name'],
        [
            (
                'user-mod',
                [
                    ['barney', '--sshpubkey', 'ssh-rsa somekey key_name']
                ]
            )
        ]
    )


def test_user_modify_passes_empty_sshpubkey_when_given_remove_key(mocker):
   test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--remove-key'],
        [
            (
                'user-mod',
                [
                    ['barney', '--sshpubkey', '']
                ]
            )
        ]
    )


def test_user_modify_passes_random_password_when_given_remove_password(
        mocker, monkeypatch
):
    mock_password = 'thiswillactuallyberandom'
    monkeypatch.setattr(
        appliance_cli.utils, 'secure_random_string', lambda: mock_password
    )

    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify', 'barney', '--remove-password'],
        [
            (
                'user-mod',
                [
                    ['barney', '--password', mock_password]
                ]
            )
        ]
    )

