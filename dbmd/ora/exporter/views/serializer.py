from typing import List, Optional

from ..serializers import ObjectTypes, Dependency, MDBaseModel, ColumnType


class ViewColumn(MDBaseModel):
    name: str
    type: ColumnType
    description: Optional[str] = None

    def render_md(self, **kwargs):
        desc = ' ' + self.description if self.description else ''
        return f'- {self.name}: {self.type}{desc}'


class ViewSchema(MDBaseModel):
    type: ObjectTypes = ObjectTypes.VIEW
    db_schema: str
    name: str
    description: Optional[str] = None
    columns: List[ViewColumn]
    definition: str
    dependencies: List[Dependency] = []

    def render_md(self, **kwargs):
        res = f'# View: {self.name} \n[TYPE:VIEW]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        res += '## Columns\n'
        for col in self.columns:
            res += f'{col}\n'

        if self.description:
            res += '## Description\n'
            res += f'{self.description}\n'

        res += '## Dependencies\n'
        for d in self.dependencies:
            res += f'{d}\n'

        res += '## Definition\n'
        res += '```sql\n'
        res += f'{self.definition.strip()}\n'
        res += '```\n'

        res += self._render_definition_path(**kwargs)

        return res
