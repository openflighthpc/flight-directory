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

from unittest import mock

import directory
import ipa_utils
import test_utils
import appliance_cli.utils

# This setup runs before every test ensuring that they are run in advanced mode
def setUpModule():
    test_utils.reload_in_advanced_mode()

def test_user_create_includes_random_by_default(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney', '--last', 'Rubble'],
        [
            (
                'user-add',
                [
                    [
                        'barney',
                        '--first',  'Barney',
                        '--gidnumber', 'clusterusers_gid',
                        '--last', 'Rubble',
                        '--random'
                    ]
                ]
            )
        ],
    )


def test_user_create_does_not_pass_random_when_given_no_password(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney',
            '--last', 'Rubble', '--no-password'],
        [
            (
                'user-add',
                [
                    [
                        'barney',
                        '--first', 'Barney',
                        '--gidnumber', 'clusterusers_gid',
                        '--last', 'Rubble'
                    ]
                ]
            )
        ]
    )


def test_user_create_passes_sshpubkey_when_given_key(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create', 'barney', '--first', 'Barney', '--last', 'Rubble',
            '--key', 'ssh-rsa somekey key_name'],
        [
            (
                'user-add',
                [
                    [
                        'barney',
                        '--first', 'Barney',
                        '--gidnumber', 'clusterusers_gid',
                        '--last', 'Rubble',
                        '--random',
                        '--sshpubkey', 'ssh-rsa somekey key_name'
                    ]
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

