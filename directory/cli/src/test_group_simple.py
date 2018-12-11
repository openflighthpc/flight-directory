
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
