
import subprocess
import sys
import tempfile
import os
from pathlib import Path
import random
import string
from types import SimpleNamespace
import click


def run(command, **kwargs):
    return subprocess.run(
        command,

        # Capture these.
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,

        # Capture as strings not bytes.
        universal_newlines=True,

        # Pass these through.
        **kwargs
    )


def delegate_run(command):
    """Run a command letting it handle stdout/stderr as normal"""

    try:
        # Will just dump to stdout/stderr.
        process = subprocess.run(command)
    except KeyboardInterrupt:
        # Add newline otherwise prompt may be merged with process output.
        click.echo()

        # Gracefully exit; will not exit in sandbox as click-repl catches.
        sys.exit(1)

    if process.returncode != 0:
        # Exit with same return code; error should have been handled by process
        # and be in stderr/stdout.
        sys.exit(process.returncode)

    return process


# Load a Clusterware/Shell-style config file as a dict.
def read_config(config_file_path):
    config_lines = [
        line.strip().split('=')
        for line in open(config_file_path).readlines()
    ]
    config_parts = [
        tuple([part.strip('"') for part in parts])
        for parts in config_lines
    ]
    return dict(config_parts)


def in_sandbox():
    # We're in the sandbox if the program was started with the 'sandbox' arg.
    return len(sys.argv) > 1 and sys.argv[1] == 'sandbox'


def is_valid_ssh_public_key(string):
    with tempfile.NamedTemporaryFile('w') as scratch_file:
        # Need to write string to temporary file as `ssh-keygen` operates on
        # files not strings.
        scratch_file.write(string)
        scratch_file.flush()

        # Will give a non-zero exit code if the file does not contain a valid
        # SSH public key.
        valid_key_command = ['ssh-keygen', '-lf', scratch_file.name]

        try:
            result = run(valid_key_command)
            result.check_returncode()
        except subprocess.CalledProcessError:
            return False
        else:
            return True


def is_feature_enabled(marker_file):
    return os.path.exists(marker_file)


def record_feature_enabled(marker_file):
    Path(marker_file).touch(744)


def record_feature_disabled(marker_file):
    os.remove(marker_file)


def secure_random_string(length=100):
    # Cryptographically secure according to
    # http://stackoverflow.com/a/23728630/2620402.
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(length)
    )


def filter_none_values(dict_):
    return {
        param: value for param, value in dict_.items()
        if value is not None
    }


# Create a simple data object from a dict; in my opinion this is a better name
# and should also prevent me from forgetting to spread the SimpleNamespace
# arguments.
def struct(dict_):
    return SimpleNamespace(**dict_)


# TODO may be better way to do this, maybe use original Options object (which
# saves original params) if one available? But will still need to do this in
# some way when one not available.
def build_option_arguments(options_map):
    """Build list of arguments given a map from option names to values"""
    # Order options by name so in predictable order for testing.
    ordered_option_pairs = sorted(options_map.items())

    option_arguments = []
    for name, value in ordered_option_pairs:
        option = _option_name_to_argument(name)

        is_flag_option = isinstance(value, bool)
        if is_flag_option:
            if value:
                option_arguments.append(option)
        else:
            option_arguments += [option, str(value)]

    return option_arguments


def _option_name_to_argument(option_name):
    prefix = '-' if len(option_name) == 1 else '--'

    # Note: need to translate underscores back to hyphens as Click will
    # translate parameters the other way to form valid variable names.
    translation_table = str.maketrans('_', '-')
    return prefix + option_name.translate(translation_table)
