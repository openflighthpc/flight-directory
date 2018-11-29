
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
