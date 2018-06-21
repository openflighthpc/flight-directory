
from unittest import mock
import re

from directory import directory
import utils
import ipa_utils
from appliance_cli.testing_utils import click_run


def test_import_runs_directory_cli_with_each_line(
        tmpdir,
        mocker
):
    mocker.spy(utils, 'directory_run')

    test_record = tmpdir.mkdir('somedir').join('record').strpath
    with open(test_record, 'w') as record_file:
        record_file.writelines([
            'group create mygroup\n',
            'user create someuser --first some --last user\n',
        ])

    test_record_url = 'file://' + test_record

    click_run(directory, ['import', test_record_url])

    assert utils.directory_run.call_count == 2
    assert utils.directory_run.call_args_list == [
        mock.call(directory, 'group create mygroup'),
        mock.call(directory, 'user create someuser --first some --last user')
    ]


def test_import_outputs_last_password_generated_for_each_user(
        tmpdir,
        mocker,
        monkeypatch
):
    mocker.spy(utils, 'directory_run')

    _mock_ipa_run_output(monkeypatch)

    # TODO this tests a lot of related things; could be worth breaking up into
    # more discrete tests.
    test_record = tmpdir.mkdir('somedir').join('record').strpath
    with open(test_record, 'w') as record_file:
        record_file.writelines([
            'user create newuser --first new --last user\n',

            'user create anotheruser --first someone --last else\n',
            'user modify anotheruser --new-password\n',

            'user create willbedeleteduser --first soon --last deleted\n',
            'user delete willbedeleteduser\n'

            'user create nopassworduser --first no --last password --no-password\n',

            'user create removedpassworduser --first removed --last password\n'
            'user modify removedpassworduser --remove-password\n',
        ])

    test_record_url = 'file://' + test_record

    result = click_run(directory, ['import', test_record_url])

    assert re.search('newuser.*newuser_user-add_password', result.output)

    # Only the last generated password for a user should be displayed.
    assert re.search(
        'anotheruser.*anotheruser_user-mod_password',
        result.output
    )
    assert 'anotheruser_user-add_password' not in result.output

    # Users which have been deleted, were created with no password, or have had
    # their password removed should not appear.
    assert 'willbedeleteduser' not in result.output
    assert 'nopassworduser' not in result.output
    assert 'removedpassworduser' not in result.output

    # The standard interactive output should not be displayed.
    assert 'Generated temporary password for user' not in result.output


def _mock_ipa_run_output(monkeypatch):
    def mock_ipa_run(ipa_command, args, **kwargs):
        user_login = args[0]
        mock_password = '{}_{}_password'.format(user_login, ipa_command)

        mock_output_lines = [
            'Junk: junk entry',
            'User login: {}'.format(user_login),
        ]
        if '--random' in args:
            # Assume that if `--random` arg is passed, the IPA command will
            # successfully output a random password.
            mock_output_lines.append(
                'Random password: {}'.format(mock_password)
            )

        return '\n'.join(mock_output_lines)

    monkeypatch.setattr(ipa_utils, 'ipa_run', mock_ipa_run)


def test_import_stops_on_error_and_reports_it(
        tmpdir,
        mocker,
        subprocess_run_failure
):
    mocker.spy(utils, 'directory_run')

    test_record = tmpdir.mkdir('somedir').join('record').strpath
    with open(test_record, 'w') as record_file:
        record_file.writelines([
            'group create mygroup\n',
            'user create someuser --first some --last user\n',
        ])

    test_record_url = 'file://' + test_record

    result = click_run(directory, ['import', test_record_url])

    # Assert only called once as first fails.
    assert utils.directory_run.call_count == 1

    assert \
        "Error: processing line 0 ('group create mygroup'):" in result.output


def test_import_reports_requests_error_if_occurs(
        tmpdir,
        mocker
):
    mocker.spy(utils, 'directory_run')

    test_bad_record_url = 'some/path/which/isnt/a/url'

    result = click_run(directory, ['import', test_bad_record_url])

    assert "Invalid URL 'some/path/which/isnt/a/url':" in result.output
