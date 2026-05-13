from ..serializers import ObjectTypes, Parameter, Dependency, MDBaseModel


class Routine(MDBaseModel):
    db_schema:    str
    name:         str
    parameters:   list[Parameter] = []
    dependencies: list[Dependency] = []
    signature:    str | None = None
    definition:   str | None = None

    def _render_general(self) -> str:
        return ''

    def render_md(self, **kwargs):
        type_name = self.type.name.title()
        type_tag  = self.type.name
        res = f'# {type_name}: {self.name} \n[TYPE:{type_tag}]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        if self.signature:
            res += '## Signature\n'
            res += '```sql\n'
            res += f'{self.signature.strip()}\n'
            res += '```\n'

        res += self._render_general()

        if self.parameters:
            res += '\n## Parameters\n'
            for param in self.parameters:
                res += f'- {param}\n'

        if self.dependencies:
            res += '\n## Dependencies\n'
            for dep in self.dependencies:
                res += f'{dep}\n'

        res += self._render_definition_path(**kwargs)
        return res


class Function(Routine):
    type:        ObjectTypes = ObjectTypes.FUNCTION
    return_type: str | None = None

    def _render_general(self) -> str:
        res = '\n## General\n'
        if self.return_type:
            res += f'- Return type: {self.return_type}\n'
            res += f'[RETURNS:{self.return_type}]\n'
        return res


class Procedure(Routine):
    type: ObjectTypes = ObjectTypes.PROCEDURE
