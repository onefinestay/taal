class NoTranslatorRegistered(Exception):
    """ Trying to translate without first binding to a translator """


class BindError(Exception):
    """ Binding to an unrecognized target """
