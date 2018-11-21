
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
