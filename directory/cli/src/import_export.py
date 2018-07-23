
import click
import requests
from requests_file import FileAdapter
import shutil
import os
import operator
import time
import math
import csv

import utils
import appliance_cli
import appliance_cli.text as text
from config import CONFIG


# Add adapter so we can accept `file://` as well as `http://` URLs.
SESSION = requests.Session()
SESSION.mount('file://', FileAdapter())


def add_commands(directory):

    if appliance_cli.utils.in_sandbox():
        return

    @directory.command(
        name='import',
        help='Import a Directory record from a URL'
    )
    @click.argument('url')
    def import_(url):
        utils.mark_import_started()
        try:
            content = SESSION.get(url).text

            content_lines = [
                (line_number, line)
                for (line_number, line) in enumerate(content.splitlines())
                if line.strip() != ''
            ]

            with click.progressbar(content_lines) as lines_bar:
                for line_number, command in lines_bar:
                    utils.directory_run(directory, command)

        except click.ClickException as ex:
            error_string = "processing line {} ('{}'):{}"
            new_ex = error_string.format(line_number, command, ex)
            raise click.ClickException(new_ex)

        except requests.RequestException as ex:
            raise click.ClickException(ex)

        finally:
            utils.mark_import_finished()
            _output_imported_user_passwords()

    @directory.command(help='Export Directory record')
    def export():
        try:
            export_filepath = shutil.copy2(
                CONFIG.DIRECTORY_RECORD, CONFIG.EXPORT_DIR
            )
        except FileNotFoundError:
            raise click.ClickException(
                "No Directory record found; nothing to export."
            )

        success_message = _record_export_success_message(export_filepath)
        click.echo(success_message)


def _output_imported_user_passwords():
    passwords_data = [
        [username, password] for username,
        password in utils.imported_user_passwords().items()
    ]

    # If no generated temporary passwords then no handling necessary (this
    # occurs either because no commands in imported record which would produce
    # new passwords, or an error occurred prior to reaching such a command).
    if not passwords_data:
        return

    sorted_passwords_data = sorted(passwords_data, key=operator.itemgetter(0))

    _display_imported_user_passwords(sorted_passwords_data)
    _export_imported_user_passwords(sorted_passwords_data)


def _display_imported_user_passwords(passwords_data):
    click.echo(
        'The following new temporary passwords have been generated:'
    )
    headers = ['User', 'Password']

    text.display_table(headers, passwords_data)


# Make the generated imported user temporary passwords available at a
# password-protected URL.
def _export_imported_user_passwords(passwords_data):
    unix_timestamp = math.floor(time.time())
    export_filename = 'passwords-{}.tsv'.format(unix_timestamp)
    export_filepath = os.path.join(CONFIG.EXPORT_DIR, export_filename)

    with open(export_filepath, 'w', newline='') as export_file:
        writer = csv.writer(export_file, delimiter='\t')
        for entry in passwords_data:
            writer.writerow(entry)

    download_info = text.line_wrap(
        'The temporary passwords are also available to download in TSV format '
        'at {}.'.format(_export_url(export_filename))
    ) + '\n'

    message = text.join_lines(download_info, _auth_details())
    click.echo(message)


def _record_export_success_message(export_filepath):
    success = text.success('Success!')

    export_filename = os.path.basename(export_filepath)
    download_info = \
        'Your Directory record is available to download at {}.\n'.format(
            _export_url(export_filename)
        )

    parts = [success, download_info, _auth_details()]

    # If we're in the directory sandbox we may not have access to files on
    # the appliance, so we don't want to show local access info.
        local_file_info = '\nIt can also be viewed locally at {}.'.format(
            export_filepath
        )
        parts.append(local_file_info)

    return text.join_lines(*parts)


def _export_url(export_filename):
    appliance_url = appliance_cli.config_utils.appliance_url()
    return '{}/{}/{}'.format(
        appliance_url, CONFIG.EXPORT_PREFIX, export_filename
    )


def _auth_details():
    username = 'flight'
    password = utils.directory_config()[CONFIG.PASSWORD_KEY]

    return 'You will need the following authentication details to access it:\n' + \
        "username: '{}'; password: '{}'.".format(username, password)
