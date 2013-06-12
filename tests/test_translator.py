import pytest

from taal import Translator
from taal.exceptions import BindError


def test_bind_unknown():
    translator = Translator(None, None, None)

    with pytest.raises(BindError):
        translator.bind(None)
