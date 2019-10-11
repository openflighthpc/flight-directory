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

def setUpModule():
    test_utils.reload_in_simple_mode()

def test_group_create_with_gid_calls_ipa_correctly(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['group', 'create'],
        [
            (
                'group-add',
                [
                    [
                        'clustertonkers',
                        '--desc', 'very useful description',
                        '--gid', '9002'
                    ]
                ]
            )
        ],
        'clustertonkers\nvery useful description\nYes\n9002\n'
    )

def test_group_create_without_gid_calls_ipa_correctly(mocker):
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['group', 'create'],
        [
            (
                'group-add',
                [
                    [
                        'clustertonkers',
                        '--desc', 'very useful description'
                    ]
                ]
            )
        ],
        'clustertonkers\nvery useful description\nNo\n'
    )

def test_group_modify_with_modifications_calls_ipa_correctly(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['group', 'modify'],
        [
            (
                'group-mod',
                [
                    [
                       'clustertonkers',
                       '--desc', 'this is a more relevant description'
                    ]
                ]
            )
        ],
        'clustertonkers\nthis is a more relevant description\n'
    )

def test_group_modify_without_modifications_calls_ipa_correctly(mocker):
    test_utils.mock_ipa_find_output(mocker)
    test_utils.mock_options_passed_to_ipa(
        mocker,
        ['group', 'modify'],
        [
            (
                'group-mod',
                [
                    [
                       'clustertonkers',
                       '--desc', 'clustertonkers_desc'
                    ]
                ]
            )
        ],
        'clustertonkers\n\n'
    )
