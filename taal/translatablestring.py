class TranslatableString(object):
    """
    Placeholder for a string to be translated

    Holds metadata, ``context`` and ``message_id``, and optionally
    a string ``pending_value``
    """

    def __init__(self, context=None, message_id=None, pending_value=None):
        self.context = context
        self.message_id = message_id
        self.pending_value = pending_value

    def __repr__(self):
        return "<TranslatableString: ({}, {}, {})>".format(
            self.context, self.message_id, self.pending_value)

    def __eq__(self, other):
        if not isinstance(other, TranslatableString):
            return False

        self_data = (self.context, self.message_id, self.pending_value)
        other_data = (other.context, other.message_id, other.pending_value)
        return self_data == other_data
