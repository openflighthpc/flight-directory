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

# This file contains utils for testing rather than tests designed for utils.py

import os
import importlib
import ipa_utils
import directory
import appliance_cli.utils

from unittest import mock
from appliance_cli.testing_utils import click_run

def reload_in_advanced_mode():
    _reload_with_advanced_set_to('true')

def reload_in_simple_mode():
    _reload_with_advanced_set_to('false')

def mock_options_passed_to_ipa(mocker, directory_command, ipa_run_arguments, input_stream=None):
    mocker.spy(ipa_utils, 'ipa_run')

    click_run(directory.directory, directory_command, input=input_stream)

    expected_ipa_calls = [
        _mock_call(command_with_args) for command_with_args in ipa_run_arguments
    ]
    assert ipa_utils.ipa_run.call_args_list == expected_ipa_calls

def mock_ipa_find_output(mocker):
    # Mocks ipa_utils.ipa_find for the command given
    def mock_ipa_find(ipa_command, ipa_args, *args, **kwargs):
        # Tests that expect to call group-find grab the mocked GID here
        if ipa_command == 'group-find':
            group_name = ipa_args[0].replace('--group-name=', '')
            return  [
                        {
                            'GID': ['{}_gid'.format(group_name)],
                            'Description': ['{}_desc'.format(group_name)]
                        }
                    ]

        # Tests that need user data found via calling user-find go here
        elif ipa_command == 'user-find':
            # If the test searches via UID for an existing user we return
            # none to mock that the user is new
            if '--uid' in ipa_args[0]:
                return None

            # Mock data is returned to tests that call user-find and require
            # values that aren't empty
            username = ipa_args[0].replace('--login=', '')
            return  [
                        {
                            'First name': ['{}_first'.format(username)],
                            'Last name': ['{}_last'.format(username)],
                            'Email address': ['{}_email'.format(username)]
                        }
                    ]

    mocker.patch('ipa_utils.ipa_find', mock_ipa_find)

def _reload_with_advanced_set_to(val):
    os.environ['ADVANCED'] = val
    importlib.reload(directory)

def _mock_call(command_with_args):
    command, args, *rest = command_with_args

    try:
        kwargs = rest[0]
    except IndexError:
        kwargs = {}

    return mock.call(command, *args, **kwargs)
