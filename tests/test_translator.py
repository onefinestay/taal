import pytest

from taal import Translator
from taal.exceptions import BindError


def test_bind_unknown():
    translator = Translator(None, None, None)

    with pytest.raises(BindError):
        translator.bind(None)


def test_translate_dict():
    data = {object(): object()}

    translator = Translator(None, None, None)
    assert translator.translate(data) == data


def test_translate_list():
    data = [object(), object()]

    translator = Translator(None, None, None)
    assert translator.translate(data) == data


def test_translate_tuple():
    data = (object(), object())

    translator = Translator(None, None, None)
    assert translator.translate(data) == data


def test_static_language():
    translator = Translator(None, None, language='static')
    assert translator.language == 'static'


def test_dynamic_language():
    language = 'foo'

    def get_language():
        return language

    translator = Translator(None, None, language=get_language)
    assert translator.language == 'foo'

    language = 'bar'
    assert translator.language == 'bar'
