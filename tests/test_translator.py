import pytest

from taal import Translator


def test_bind_unknown():
    translator = Translator(None, None, None)

    with pytest.raises(RuntimeError):
        translator.bind(None)
