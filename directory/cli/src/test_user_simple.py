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

from click.testing import CliRunner

# This setup runs before every test ensuring that they are run in simple mode
def setUpModule():
    test_utils.reload_in_simple_mode()

def test_user_create_with_uid_calls_ipa_correctly(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create'],
        [
            (
                'user-add',
                [
                    [
                        'walterwhite',
                        '--email', 'heisenberg@example.com',
                        '--first', 'Walter',
                        '--gidnumber', 'clusterusers_gid',
                        '--last', 'White',
                        '--random',
                        '--uid', '9001'
                    ]
                ]
            )
        ],
        'walterwhite\nWalter\nWhite\nheisenberg@example.com\nYes\n9001\n',
    )

def test_user_create_without_uid_calls_ipa_correctly(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'create'],
        [
            (
                'user-add',
                [
                    [
                        'walterwhite',
                        '--email', 'heisenberg@example.com',
                        '--first', 'Walter',
                        '--gidnumber', 'clusterusers_gid',
                        '--last', 'White',
                        '--random'
                    ]
                ]
            )
        ],
        'walterwhite\nWalter\nWhite\nheisenberg@example.com\nNo\n',
    )

def test_user_modify_with_modifications_calls_ipa_correctly(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify'],
        [
            (
                'user-mod',
                [
                    [
                        'walterwhite',
                        '--cn', 'Walt Jackson',
                        '--displayname', 'Walt Jackson',
                        '--email', 'notheisenberg@example.com',
                        '--first', 'Walt',
                        '--last', 'Jackson',
                    ]
                ]
            )
        ],
        'walterwhite\nWalt\nJackson\nnotheisenberg@example.com\nNo\n',
    )

# We would expect this test to match the defaults mocked within
# mock_ipa_find_output
def test_user_modify_without_modifications_calls_ipa_correctly(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['user', 'modify'],
        [
            (
                'user-mod',
                [
                    [
                        'walterwhite',
                        '--cn', 'walterwhite_first walterwhite_last',
                        '--displayname', 'walterwhite_first walterwhite_last',
                        '--email', 'walterwhite_email',
                        '--first', 'walterwhite_first',
                        '--last', 'walterwhite_last'
                    ]
                ]
            )
        ],
        'walterwhite\n\n\n\n\n'
    )
