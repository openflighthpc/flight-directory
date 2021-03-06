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

import re
import subprocess
from click import ClickException

from config import CONFIG
import utils
import appliance_cli
from exceptions import IpaRunError


# Field names whose value should not be split into a list of values when
# encountered in `parse_find_output`, e.g. because the value may contain commas
# used for a purpose other than separating list items.
RAW_FIELD_WHITELIST = ['Random password']

# Separates key from value in `ipa *-find` output.
FIND_OUTPUT_DELIMITER = ': '


def parse_find_output(output):
    lines = [line.strip() for line in output.splitlines()]

    results = [{}]
    in_info_section = False  # Whether we're in header/footer.

    for line in lines:
        if _info_section_boundary(line):
            in_info_section = not in_info_section
        elif in_info_section:
            continue
        elif line == '':
            # We're entering the start of a new section, add a new dict to
            # build up the info for this section in.
            results.append({})
        else:
            current_section = results[-1]
            if FIND_OUTPUT_DELIMITER in line:
                key, value = _process_delimited_find_output_line(line)
                current_section[key] = value
            else:
                # This line is a continuation of the preceding line; append it
                # to the previous line's value.
                existing_value = current_section[key][0]
                current_section[key][0] = existing_value + ' ' + line

    return results


def _info_section_boundary(line):
    return re.match('^----', line)


def _process_delimited_find_output_line(line):
    key, raw_value = _strip_all(line.split(FIND_OUTPUT_DELIMITER, 1))

    if key in RAW_FIELD_WHITELIST:
        # Wrap in list for consistency with other values.
        value = [raw_value]
    else:
        # Values can contain multiple, comma-separated values; get a list of
        # all of these.
        value = _strip_all(raw_value.split(','))

    return key, value


def _strip_all(strings):
    return [string.strip() for string in strings]


def ipa_run(ipa_command, args=[], error_allowed=None, error_in_stdout=False, record=True):
    command = [CONFIG.IPA_WRAPPER_SCRIPT_PATH] + [ipa_command] + args

    try:
        result = appliance_cli.utils.run(command)
        if (error_allowed == None or not error_allowed in result.stdout):
            result.check_returncode()
    except subprocess.CalledProcessError as ex:
        error = result.stdout if error_in_stdout else result.stderr
        raise IpaRunError(error) from ex

    if record:
        _record_command()

    return result.stdout


def _record_command():
    with open(CONFIG.DIRECTORY_RECORD, 'a') as record:
        record_string = utils.original_command() + '\n'
        record.write(record_string)


# Wrapper around `ipa_run` for find commands, to always get all fields and
# records, not record when we run the find command, and return the parsed
# result.
def ipa_find(ipa_find_command, additional_args=[], error_allowed=None, all_fields=True):
    standard_args = [
        # Effectively make find command show all data.
        '--sizelimit', '0'
    ]

    if all_fields:
        standard_args = ['--all'] + standard_args

    args = additional_args + standard_args

    ipa_result = ipa_run(ipa_find_command, args, error_allowed, record=False)
    return parse_find_output(ipa_result)
