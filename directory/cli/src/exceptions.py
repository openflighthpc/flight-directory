
class IpaRunError(Exception):

    def __init__(self, message):
        # Make errors easier to read as can be multiline.
        self.message = '\n' + str(message)

    def __str__(self):
        return self.message
