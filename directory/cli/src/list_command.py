
import click
from operator import itemgetter

import ipa_utils
import appliance_cli.text as text


# Data displayers - take some headers and some data (`ipa_find` output) and
# display in some way.

table_displayer = text.display_table


def list_displayer(headers, data):
    # There should only be exactly one item in the data, and we only want to
    # display that.
    single_item = data[0]

    longest_header_length = len(max(headers, key=len))

    def padding_for(header):
        minimum_gap = 1
        padding_amount = longest_header_length - len(header) + minimum_gap
        return padding_amount * ' '

    def pad_value(header, value):
        padding = padding_for(header)

        header_size = len(header) + 1
        header_offset = header_size * ' '

        value_lines = value.split('\n')

        # Values can be multi-line; the first part just needs to be padded
        # appropriately from the header, but any additional lines need
        # additional padding to line up below this.
        additional_value_lines = len(value_lines) - 1
        additional_line_paddings = \
            [header_offset + padding] * additional_value_lines
        value_line_paddings = [padding] + additional_line_paddings

        padded_value_lines = \
            [''.join(parts) for parts in zip(value_line_paddings, value_lines)]
        return text.join_lines(*padded_value_lines)

    lines = []
    for header, value in zip(headers, single_item):
        line = text.bold(header) + ':' + pad_value(header, value)
        lines.append(line)

    display = text.join_lines(*lines)
    click.echo(display)


# Note: `field_configs` takes an OrderedDict with a mapping from field names
# (to be used as the headers in the display function) to the function to
# generate that field for each row; these functions have a signature like those
# in the `Field generators` section below.
def do(
        ipa_find_command=None,
        ipa_find_args=[],
        field_configs=None,
        sort_key=None,
        generate_additional_data=lambda: {},
        display=table_displayer,
        blacklist_key=None,
        blacklist_val_array=[]
):
    if not all([ipa_find_command, field_configs]):
        raise TypeError

    item_dicts = ipa_utils.ipa_find(ipa_find_command, ipa_find_args)

    # Remove blacklisted items
    if blacklist_key:
        item_dicts = [item_dict for item_dict in item_dicts if item_dict[blacklist_key][0] not in blacklist_val_array]
        
    if sort_key:
        item_dicts.sort(key=itemgetter(sort_key))

    headers = field_configs.keys()
    results_data = _create_data(
        item_dicts,
        field_configs,
        generate_additional_data()
    )

    display(headers, results_data)


def _create_data(item_dicts, field_configs, additional_data):
    return [
        _create_row(item_dict, field_configs, additional_data)
        for item_dict in item_dicts
    ]


def _create_row(item_dict, field_configs, additional_data):
    return [
        _display_value_for(item_dict, field_config, additional_data)
        for field_config in field_configs.items()
    ]


def _display_value_for(item_dict, field_config, additional_data):
    name, generator = field_config
    value = generator(name, item_dict, additional_data)
    return '\n'.join(value)


# Field generators.

def field_with_same_name(field_name, item_dict, additional_data):
    return item_dict.get(field_name, '')


def field_with_name(name):
    def generator(field_name, item_dict, additional_data):
        return item_dict.get(name, '')
    return generator


def group_with_users_gid(field_name, item_dict, additional_data):
    user_gid = item_dict['GID'][0]
    groups_by_gid = additional_data['groups']
    user_group = groups_by_gid[user_gid]
    group_name = user_group['Group name']
    return group_name