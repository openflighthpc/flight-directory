
import pytest

import ipa_utils
from config import CONFIG
import utils
from exceptions import IpaRunError

# Simplified `ipa user-find --all` output. Note: currently parsing output
# without `--raw` as easier to read groups; this may make this more likely to
# break in future though.
ipa_output = """---------------
4 users matched
---------------
  dn: uid=admin,cn=users,cn=accounts,dc=bobdomain,dc=alces,dc=network
  User login: admin
  Full name: Administrator
  Home directory: /home/admin
  Login shell: /bin/bash
  UID: 172600000
  SSH public key: ssh-rsa
                  yourkeygoeshere
                  aws_ireland
  SSH public key fingerprint: 83:96:F0:C6:30:65:03:07:D6:50:0E:9C:35:7F:9D:24 aws_ireland (ssh-rsa)
  Account disabled: False
  Password: True
  Random password: jeZ3Liu,wySy
  Member of groups: admins, trust admins

  dn: uid=flightuser,cn=users,cn=accounts,dc=bobdomain,dc=alces,dc=network
  User login: flightuser
  First name: Alces
  Full name: Alces Flight
  Display name: Alces Flight
  Initials: AF
  Home directory: /home/flightuser
  Login shell: /bin/bash
  Email address: flightuser@bobdomain.alces.network
  UID: 172600004
  Account disabled: False
  Password: True
  Member of groups: clusterusers, adminusers
----------------------------
Number of entries returned 4
----------------------------
"""


def test_parse_find_output_parses_dict_for_each_item():
    result = ipa_utils.parse_find_output(ipa_output)

    assert len(result) == 2

    first = result[0]
    assert first['Full name'] == ['Administrator']
    assert first['Login shell'] == ['/bin/bash']

    second = result[1]
    assert second['Full name'] == ['Alces Flight']


def test_parse_find_output_parses_lines_with_multiple_values():
    result = ipa_utils.parse_find_output(ipa_output)

    first = result[0]
    assert first['Member of groups'] == ['admins', 'trust admins']


def test_parse_find_output_parses_multiline_values():
    result = ipa_utils.parse_find_output(ipa_output)

    first = result[0]
    assert first['SSH public key'] == ['ssh-rsa yourkeygoeshere aws_ireland']


def test_parse_find_output_handles_values_containing_colons():
    result = ipa_utils.parse_find_output(ipa_output)

    first = result[0]
    assert first['SSH public key fingerprint'] == [
        '83:96:F0:C6:30:65:03:07:D6:50:0E:9C:35:7F:9D:24 aws_ireland (ssh-rsa)'
    ]


def test_parse_find_output_reads_random_password_as_single_value():
    result = ipa_utils.parse_find_output(ipa_output)

    first = result[0]
    assert first['Random password'] == [
        'jeZ3Liu,wySy'
    ]


def test_ipa_run_logs_commands_by_default(monkeypatch):
    mock_original_command(monkeypatch, 'command 1')
    ipa_utils.ipa_run('group-add', ['flintstones'])

    mock_original_command(monkeypatch, 'command 2')
    ipa_utils.ipa_run(
        'user-add', ['fred', '--first', 'Fred', '--last', 'Flintstone']
    )

    mock_original_command(monkeypatch, 'command 3')
    ipa_utils.ipa_run(
        'user-add', ['barney', '--first', 'Barney', '--last', 'Rubble']
    )

    with open(CONFIG.DIRECTORY_RECORD) as record:
        lines = record.readlines()
        assert lines[0].strip() == 'command 1'
        assert lines[1].strip() == 'command 2'
        assert lines[2].strip() == 'command 3'


def test_ipa_run_can_not_record_commands(monkeypatch):
    mock_original_command(monkeypatch, 'command 1')

    ipa_utils.ipa_run('group-add', ['flintstones'])
    ipa_utils.ipa_run(
        'user-add',
        ['fred', '--first', 'Fred', '--last', 'Flintstone'],
        record=False  # Don't record in this case.
    )

    with open(CONFIG.DIRECTORY_RECORD) as record:
        lines = record.read()
        assert lines.strip() == 'command 1'


def test_ipa_run_does_not_record_erroring_commands(
        monkeypatch, subprocess_run_failure):
    mock_original_command(monkeypatch, 'command 1')

    with pytest.raises(IpaRunError):
        ipa_utils.ipa_run('group-add', ['flintstones'])

        with open(CONFIG.DIRECTORY_RECORD) as record:
            lines = record.read()
            assert lines.strip() == ''


def mock_original_command(monkeypatch, original_command):
    def mock_result():
        return original_command
    monkeypatch.setattr(utils, 'original_command', mock_result)
