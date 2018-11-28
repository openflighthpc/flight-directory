
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
    def mock_ipa_find(ipa_command, ipa_args, *args, **kwargs):
        if ipa_command == 'group-find':
            group_name = ipa_args[0]
            return  [
                        {
                            'GID': ['{}_gid'.format(group_name)]
                        }
                    ]
        elif ipa_command == 'user-find':
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
