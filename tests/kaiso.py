from __future__ import absolute_import

from kaiso.attributes import Uuid, String
from kaiso.types import Entity


class Animal(Entity):
    id = Uuid(unique=True)
    name = String()


class Fish(Animal):
    pass
