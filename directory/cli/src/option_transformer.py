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

import copy


# Given an argument and a dict of options, as passed to a Click command, an
# instance of this class can chain a series of transformations together to be
# applied to these options to produce a new dict of options suitable to be
# passed through to `ipa`.
class OptionTransformer:

    def __init__(self, argument, options):
        self.argument = argument
        self.original_options = options
        self.options = copy.copy(options)

    # Note: `False` indicates option takes no argument.
    def set_option(self, option_name, option_value=False):
        self.options[option_name] = option_value
        return self

    def rename_option(self, directory_name, ipa_name):
        value = self.original_options[directory_name]
        self.set_option(ipa_name, value)
        self.delete_option(directory_name)
        return self

    def rename_flag_option(self, directory_name, ipa_name):
        flag_given = self.original_options[directory_name]
        self.delete_option(directory_name)
        if flag_given:
            self.set_option(ipa_name)
        return self

    # Rename a flag option, and set it if and only if the Directory CLI flag is
    # not passed.
    def rename_and_invert_flag_option(self, directory_name, ipa_name):
        flag_given = self.original_options[directory_name]
        self.delete_option(directory_name)
        if not flag_given:
            self.set_option(ipa_name)
        return self

    def delete_option(self, option_name):
        if option_name in self.options:
            del self.options[option_name]

        return self

    # Modify options using arbitrary `(argument, original_options) -> options`
    # callback.
    def modify(self, modify_callback):
        option_changes = modify_callback(self.argument, self.original_options)
        self.options.update(option_changes)
        return self
