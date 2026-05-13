from ..serializers import ObjectTypes, Dependency, MDBaseModel


class ViewColumn(MDBaseModel):
    name:        str
    type:        str
    description: str | None = None

    def render_md(self, **kwargs):
        desc = ' -- ' + self.description if self.description else ''
        return f'- {self.name}: {self.type}{desc}'


class ViewSchema(MDBaseModel):
    type:         ObjectTypes = ObjectTypes.VIEW
    db_schema:    str
    name:         str
    description:  str | None = None
    columns:      list[ViewColumn]
    definition:   str
    dependencies: list[Dependency] = []

    def render_md(self, **kwargs):
        res = f'# View: {self.name} \n[TYPE:VIEW]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        if self.description:
            res += f'{self.description}\n\n'

        res += '## Columns\n'
        for col in self.columns:
            res += f'{col}\n'

        if self.dependencies:
            res += '## Dependencies\n'
            for dep in self.dependencies:
                res += f'{dep}\n'

        res += '## Definition\n'
        res += '```sql\n'
        res += f'{self.definition.strip()}\n'
        res += '```\n'

        res += self._render_definition_path(**kwargs)
        return res
