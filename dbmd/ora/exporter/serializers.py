from enum import Enum
from typing import Optional

from dbmd.serializers import MDBaseModel, Dependency


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


class ParameterMode(Enum):
    IN = 'IN'
    OUT = 'OUT'
    IN_OUT= 'IN/OUT'


class Parameter(MDBaseModel):
    name: str
    mode: ParameterMode
    type: str
    default: Optional[str] = None

    def render_md(self, **kwargs):
        res = f'{self.name} {self.mode.name} {self.type}'

        if self.default is not None:
            res += f' DEFAULT {self.default}'

        return res


class ColumnType(MDBaseModel):
    name: str
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.convert_str()

    def convert_str(self):
        self.length=int(self.length) if self.length else None
        self.precision = int(self.precision) if self.precision else None
        self.scale = int(self.scale) if self.scale else None

    def render_md(self, **kwargs):
        if self.name == 'VARCHAR2':
            res = f'{self.name}({self.length})'
        elif self.name == 'NUMBER' and self.precision and self.precision > 0:
            if self.scale and self.scale > 0:
                res = f'{self.name}({self.precision}, {self.scale})'
            else:
                res = f'{self.name}({self.precision})'
        else:
            res = self.name

        return res
