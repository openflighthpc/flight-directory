
import click
from terminaltables import DoubleTable
import textwrap


def line_wrap(text):
    return textwrap.fill(
        text,
        width=80,
        replace_whitespace=False,
        break_long_words=False,
        break_on_hyphens=False,
    )


def join_lines(*parts):
    return '\n'.join(parts)


def info(text):
    return _colour_text(text, 'yellow')


def success(text):
    return _colour_text(text, 'green')


def failure(text):
    return _colour_text(text, 'red')


def _colour_text(text, colour):
    return click.style(text, fg=colour)


def bold(text):
    return click.style(text, bold=True)


def display_table(headers, data):
    bolded_headers = [bold(header) for header in headers]
    table_data = [bolded_headers] + data

    table = DoubleTable(table_data)
    table.inner_row_border = True
    click.echo_via_pager(table.table)


def help_text_literal_paragraph(*parts):
    """Get text as a paragraph which will have indentation preserved in help"""
    # See http://click.pocoo.org/6/api/#click.wrap_text for explanation.
    return '\n\n\b\n' + ''.join(parts) + '\n\n'


def indented_list(*lines):
    """Get argument lines as an indented list"""
    return '\n\t' + '\n\t'.join(lines)
