from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class MDBaseModel(BaseModel, ABC):


    @abstractmethod
    def render_md(self):
        ...


    def __str__(self):
        return self.render_md()


class ObjectTypes(Enum):
    TABLE = 'table'
    VIEW = 'view'
    FUNCTION = 'function'
    PROCEDURE = 'procedure'
    PACKAGE = 'package'
    TRIGGER = 'trigger'
    OBJECT_TYPE = 'object type'
    SCALAR_TYPE = 'scalar type'
    COLLECTION_TYPE = 'collection type'


class Dependency(MDBaseModel):
    type: ObjectTypes
    db_schema: str
    name: str

    def render_md(self):
        ...


class ParameterMode(Enum):
    IN = 'IN'
    OUT = 'OUT'
    IN_OUT= 'IN/OUT'


class Parameter(MDBaseModel):
    name: str
    mode: ParameterMode
    type: str
    default: Optional[str] = None

    def render_md(self):
        ...
