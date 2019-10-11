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

import pytest
from click import ClickException

from appliance_cli.support import _validate_support_key_url

# TODO: Not ideal to test private function here, but I can't be bothered
# mocking everything else out at the moment to just test this one function.


def test_validation_does_nothing_for_valid_support_key_url():
    # Should not raise.
    _validate_support_key_url(
        'https://s3-eu-west-1.amazonaws.com/alces-flight/Support/mykey'
    )


def test_validation_raises_unless_support_key_url_uses_https():
    with pytest.raises(ClickException):
        _validate_support_key_url(
            'http://s3-eu-west-1.amazonaws.com/alces-flight/Support/mykey'
        )


def test_validation_raises_unless_support_key_url_uses_correct_domain():
    with pytest.raises(ClickException):
        _validate_support_key_url(
            'https://s3-eu-west-2.amazonaws.com/alces-flight/Support/mykey'
        )


def test_validation_raises_unless_support_key_url_uses_correct_bucket():
    with pytest.raises(ClickException):
        _validate_support_key_url(
            'https://s3-eu-west-1.amazonaws.com/alces-flight-NEW/Support/mykey'
        )


def test_validation_raises_unless_support_key_url_uses_correct_bucket_folder():
    with pytest.raises(ClickException):
        _validate_support_key_url(
            'https://s3-eu-west-1.amazonaws.com/alces-flight/Support-NEW/mykey'
        )
