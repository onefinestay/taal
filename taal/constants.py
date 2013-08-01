
# placeholder string used to represent translated strings in the database
PLACEHOLDER = "taal:placeholder"


class PlaceholderValue(object):
    """ Represents a translated value that has not been transformed.

    Users will receive this if they directly access a model attribute rather
    than using the taal machinary.
    """
