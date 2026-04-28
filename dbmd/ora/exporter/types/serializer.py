from enum import Enum
from typing import List, Optional

from ..serializers import ObjectTypes, Dependency, MDBaseModel, ColumnType


class OTAttribute(MDBaseModel):
    name: str
    datatype: ColumnType
    inherited: bool

    def render_md(self, **kwargs):
        res = f'- {self.name}: {self.datatype}\n'
        res += f'[NAME:{self.name}]\n'

        if self.inherited:
            res += '[INHERITED]\n'

        return res


class OTMethod(MDBaseModel):
    name: str
    type: str
    parameters_cnt: int
    is_function: bool
    final: bool
    instantiable: bool
    is_overriding: bool
    is_inherited: bool

    def render_md(self, **kwargs):
        res = f'- {self.name} ({self.parameters_cnt} params)\n'
        res += f'[NAME:{self.name}]\n'

        if self.is_function:
            res += '[FUNCTION]\n'
        else:
            res += '[PROCEDURE]\n'

        flags = []
        if self.final:
            flags.append('FINAL')
        if self.instantiable:
            flags.append('INSTANTIABLE')
        if self.is_overriding:
            flags.append('OVERRIDING')
        if self.is_inherited:
            flags.append('INHERITED')

        if flags:
            res += f'[{" | ".join(flags)}]\n'

        return res


class ObjectTypeDetails(MDBaseModel):
    type: ObjectTypes = ObjectTypes.OBJECT_TYPE
    db_schema: str
    name: str
    has_methods: bool = False
    attributes: List[OTAttribute] = []
    methods: List[OTMethod] = []
    dependencies: List[Dependency] = []

    def render_md(self, **kwargs):
        res = f'# Object Type: {self.name} \n[TYPE:OBJECT_TYPE]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        # --- General ---
        res += '## General\n'
        res += f'- Has methods: {"YES" if self.has_methods else "NO"}\n'

        # --- Attributes ---
        if self.attributes:
            res += '\n## Attributes\n'
            for attr in self.attributes:
                res += f'{attr}\n'

        # --- Methods ---
        if self.methods:
            res += '\n## Methods\n'
            for method in self.methods:
                res += f'{method}\n'

        # --- Dependencies ---
        if self.dependencies:
            res += '\n## Dependencies\n'
            for dep in self.dependencies:
                res += f'{dep}\n'

        res += self._render_definition_path(**kwargs)

        return res


class CollectionTypes(Enum):
    TABLE = 'table'
    VARRAY = 'varray'


class CollectionTypeDetails(MDBaseModel):
    type: ObjectTypes = ObjectTypes.COLLECTION_TYPE
    db_schema: str
    name: str
    collection_type: CollectionTypes
    definition: str
    dependencies: List[Dependency] = []

    def render_md(self, **kwargs):
        res = f'# Collection Type: {self.name} \n[TYPE:COLLECTION_TYPE]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        # --- General ---
        res += '## General\n'
        res += f'- Collection type: {self.collection_type.value.upper()}\n'
        res += f'[COLLECTION:{self.collection_type.value}]\n'

        # --- Definition ---
        if self.definition:
            res += '\n## Definition\n'
            res += '```sql\n'
            res += f'{self.definition.strip()}\n'
            res += '```\n'

        # --- Dependencies ---
        if self.dependencies:
            res += '\n## Dependencies\n'
            for dep in self.dependencies:
                res += f'{dep}\n'

        res += self._render_definition_path(**kwargs)

        return res


class ScalarType(MDBaseModel):
    type: ObjectTypes = ObjectTypes.SCALAR_TYPE
    db_schema: str
    name: str
    definition: str

    def render_md(self, **kwargs):
        res = f'# Scalar Type: {self.name} \n[TYPE:SCALAR_TYPE]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        # --- Definition ---
        if self.definition:
            res += '## Definition\n'
            res += '```sql\n'
            res += f'{self.definition.strip()}\n'
            res += '```\n'

        res += self._render_definition_path(**kwargs)

        return res
