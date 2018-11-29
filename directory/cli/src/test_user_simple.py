
from unittest import mock

import directory
import ipa_utils
import test_utils
import appliance_cli.utils
from appliance_cli.testing_utils import click_run

from click.testing import CliRunner

# This setup runs before every test ensuring that they are run in simple mode
def setUpModule():
    test_utils.reload_in_simple_mode()

def test_user_create_calls_ipa_correctly(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'create'],
        'walterwhite\nWalter\nWhite\nheisenberg@example.com\nNo\n',
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
                    [
                        'walterwhite',
                        '--email', 'heisenberg@example.com',
                        '--first', 'Walter',
                        '--last', 'White',
                        '--random'
                    ]
                ]
            )
        ]
    )

def test_user_modify_calls_ipa_correctly(mocker):
    _test_options_passed_to_ipa(
        mocker,
        ['user', 'modify'],
        'walterwhite\nWalt\nJackson\nnotheisenberg@example.com\nNo\n',
        [
            (
                'user-find',
                [
                    [
                        '--login=walterwhite',
                        '--all',
                        '--sizelimit', '0'
                    ],
                    None
                ],
                { 'record': False }
            ),
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
        ]
    )

def _test_options_passed_to_ipa(mocker, directory_command, input_stream, ipa_run_arguments):
    mocker.spy(ipa_utils, 'ipa_run')

    click_run(directory.directory, directory_command, input=input_stream)

    expected_ipa_calls = [mock_call(command_with_args) for command_with_args in ipa_run_arguments]
    assert ipa_utils.ipa_run.call_args_list == expected_ipa_calls

def mock_call(command_with_args):
    command, args, *rest = command_with_args

    try:
        kwargs = rest[0]
    except IndexError:
        kwargs = {}

    return mock.call(command, *args, **kwargs)
