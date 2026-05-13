from ..serializers import ObjectTypes, MDBaseModel


class Column(MDBaseModel):
    name:        str
    type:        str
    nullable:    bool
    default:     str | None = None
    description: str | None = None

    def render_md(self, **kwargs):
        nullable = ' not null' if not self.nullable else ''
        default  = f' default {self.default}' if self.default else ''
        desc     = ' -- ' + self.description if self.description else ''
        return f'- {self.name}: {self.type}{default}{nullable}{desc}'


class ForeignKeyReference(MDBaseModel):
    ref_schema:     str
    context_schema: str
    ref_table:      str
    ref_columns:    list[str]

    def render_md(self, **kwargs):
        if self.ref_schema != self.context_schema:
            return f'{self.ref_schema}.{self.ref_table} ({", ".join(self.ref_columns)})'
        return f'{self.ref_table} ({", ".join(self.ref_columns)})'


class ForeignKey(MDBaseModel):
    name:       str
    columns:    list[str]
    references: ForeignKeyReference
    on_delete:  str | None = None

    def render_md(self, **kwargs):
        return f'- {self.name}: ({", ".join(self.columns)}) -> {self.references} [{self.on_delete}]'


class UniqueConstraint(MDBaseModel):
    name:    str
    columns: list[str]

    def render_md(self, **kwargs):
        return f'- {self.name}: ({", ".join(self.columns)})'

class Index(MDBaseModel):
    name:       str
    type:       str
    unique:     bool
    columns:    list[str]
    definition: str

    def render_md(self, **kwargs):
        unique = ' unique' if self.unique else ''
        return f'- {self.name}: ({", ".join(self.columns)}) {self.type}{unique}\n  `{self.definition}`'


class TableTrigger(MDBaseModel):
    name:            str
    type:            str
    timing:          str
    enabled:         bool
    function_schema: str
    function:        str

    def render_md(self, **kwargs):
        status = 'enabled' if self.enabled else 'disabled'
        return f'- {self.function_schema}.{self.function}: {self.type} {self.timing} [{status}]'


class TableSchema(MDBaseModel):
    db_schema:          str
    name:               str
    type:               ObjectTypes = ObjectTypes.TABLE
    description:        str | None = None
    columns:            list[Column]
    primary_key:        UniqueConstraint | None = None
    foreign_keys:       list[ForeignKey] = []
    unique_constraints: list[UniqueConstraint] = []
    indexes:            list[Index] = []
    triggers:           list[TableTrigger] = []
    row_count:          int | None = None

    def render_md(self, **kwargs):
        res = f'# Table: {self.name} \n[TYPE:TABLE]\n[SCHEMA:{self.db_schema}]\n\n'

        if self.description:
            res += f'{self.description}\n\n'

        if self.row_count is not None:
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
