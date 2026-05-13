from enum import Enum

from dbmd.serializers import MDBaseModel, Dependency


class ObjectTypes(Enum):
    TABLE          = 'table'
    VIEW           = 'view'
    FUNCTION       = 'function'
    PROCEDURE      = 'procedure'
    TRIGGER        = 'trigger'
    COMPOSITE_TYPE = 'composite type'
    ENUM_TYPE      = 'enum type'
    DOMAIN_TYPE    = 'domain type'


class ParameterMode(Enum):
    IN       = 'IN'
    OUT      = 'OUT'
    INOUT    = 'INOUT'
    VARIADIC = 'VARIADIC'


class Parameter(MDBaseModel):
    name: str
    mode: ParameterMode
    type: str

    def render_md(self, **kwargs):
        return f'{self.name} {self.mode.value} {self.type}'
