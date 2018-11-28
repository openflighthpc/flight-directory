
from unittest import mock

import directory
import ipa_utils
import test_utils

from click.testing import CliRunner

# This setup runs before every test ensuring that they are run in simple mode
def setUpModule():
    test_utils.reload_in_simple_mode()

def test_user_create_calls_ipa_correctly(mocker):
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

def test_user_modify_calls_ipa_correctly(mocker):
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

