from __future__ import absolute_import

from contextlib import contextmanager

from kaiso.attributes import Uuid, String
from kaiso.types import Entity

from taal.kaiso import monkey_patch_kaiso, unpatch_kaiso


class Animal(Entity):
    id = Uuid(unique=True)
    name = String()


class Fish(Animal):
    pass


@contextmanager
def patch_kaiso():
    monkey_patch_kaiso()
    try:
        yield
    finally:
        unpatch_kaiso()


