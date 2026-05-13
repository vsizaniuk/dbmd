from ..serializers import ObjectTypes, MDBaseModel


class TriggerDetails(MDBaseModel):
    type:            ObjectTypes = ObjectTypes.TRIGGER
    db_schema:       str
    name:            str
    table_name:      str
    trigger_type:    str
    timing:          str
    events:          list[str]
    enabled:         bool
    function_schema: str
    function_name:   str
    definition:      str | None = None

    def render_md(self, **kwargs):
        res = f'# Trigger: {self.name} \n[TYPE:TRIGGER]\n[SCHEMA:{self.db_schema}]\n\n'

        res += '## General\n'
        res += f'- Status: {"enabled" if self.enabled else "disabled"}\n'
        res += f'- Table: {self.table_name}\n'
        res += f'[TABLE:{self.table_name}]\n'
        res += f'- Type: {self.trigger_type}\n'
        res += f'- Timing: {self.timing}\n'
        res += f'- Events: {", ".join(self.events)}\n'
        res += f'- Function: {self.function_schema}.{self.function_name}\n'
        res += f'[FUNCTION:{self.function_schema}.{self.function_name}]\n'

        if self.definition:
            res += '\n## Definition\n'
            res += '```sql\n'
            res += f'{self.definition.strip()}\n'
            res += '```\n'

        res += self._render_definition_path(**kwargs)
        return res
