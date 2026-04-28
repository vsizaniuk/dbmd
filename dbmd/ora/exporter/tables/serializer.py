from typing import List, Optional
from ..serializers import ObjectTypes, MDBaseModel, ColumnType


class Column(MDBaseModel):
    name: str
    type: ColumnType
    nullable: bool
    default: Optional[str] = None
    description: Optional[str] = None


    def render_md(self, **kwargs):
        nullable = ' not null' if not self.nullable else ''
        default = f' {self.default}' if self.default else ''
        desc = ' --' + self.description if self.description else ''

        return f'- {self.name}: {self.type}{default}{nullable}{desc}'


class ForeignKeyReference(MDBaseModel):
    db_schema: str
    context_schema: str
    table: str
    columns: List[str]


    def render_md(self, **kwargs):
        external = self.db_schema != self.context_schema

        if external:
            res = f'{self.db_schema}.{self.table} ({','.join(self.columns)})'
        else:
            res = f'{self.table} ({','.join(self.columns)})'

        return res


class ForeignKey(MDBaseModel):
    name: str
    columns: List[str]
    references: ForeignKeyReference
    on_delete: Optional[str] = None


    def render_md(self, **kwargs):
        return f'- {self.name}: ({','.join(self.columns)}) -> {self.references} [{self.on_delete}]'


class UniqueConstraint(MDBaseModel):
    name: str
    columns: List[str]


    def render_md(self, **kwargs):
        return f'- {self.name}: ({','.join(self.columns)})'


class Index(MDBaseModel):
    name: str
    type: str
    columns: List[str]
    expression: Optional[str] = None


    def render_md(self, **kwargs):
        expression = f' [{self.expression}]' if self.expression else ''
        return f'- {self.name}: ({','.join(self.columns)}) {self.type}{expression}'


class TableTrigger(MDBaseModel):
    db_schema: str
    name: str
    type: str
    timing: str
    status: str


    def render_md(self, **kwargs):
        return f'- {self.db_schema}.{self.name}: {self.type} {self.timing} [{self.status}]'


class TableSchema(MDBaseModel):
    db_schema: str
    name: str
    type: ObjectTypes = ObjectTypes.TABLE
    description: Optional[str] = None
    columns: List[Column]
    primary_key: UniqueConstraint = None
    foreign_keys: List[ForeignKey] = []
    unique_constraints: List[UniqueConstraint] = []
    indexes: List[Index] = []
    triggers: List[TableTrigger] = []
    row_count: Optional[int] = None
    notes: Optional[str] = None


    def render_md(self, **kwargs):
        res = f'# Table: {self.name} \n[TYPE:TABLE]\n[SCHEMA:{self.db_schema}]\n\n'

        if self.row_count:
            res += '## Statistics\n'
            res += f'- Rows count: {self.row_count}\n'

        res += '## Columns\n'
        for col in self.columns:
            res += f'{col}\n'

        if self.primary_key:
            res += '## Primary key\n'
            res += f'{self.primary_key}\n'

        if self.unique_constraints:
            res += '## Unique keys\n'
            for uk in self.unique_constraints:
                res += f'{uk}\n'

        if self.foreign_keys:
            res += '## Foreign keys\n'
            for fk in self.foreign_keys:
                res += f'{fk}\n'

        if self.indexes:
            res += '## Indexes\n'
            for ind in self.indexes:
                res += f'{ind}\n'

        if self.triggers:
            res += '## Triggers\n'
            for trigger in self.triggers:
                res += f'{trigger}\n'

        res += self._render_definition_path(**kwargs)

        return res
