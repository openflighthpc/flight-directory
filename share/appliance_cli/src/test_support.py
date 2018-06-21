
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
