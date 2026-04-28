from typing import List, Optional

from ..serializers import ObjectTypes, Dependency, MDBaseModel


class TriggerDetails(MDBaseModel):
    type: ObjectTypes = ObjectTypes.TRIGGER
    db_schema: str
    name: str
    status: str
    trigger_type: str
    event: Optional[str] = None
    table_name: Optional[str] = None
    dependencies: List[Dependency] = []
    signature: Optional[str] = None

    def render_md(self, **kwargs):
        res = f'# Trigger: {self.name} \n[TYPE:TRIGGER]\n[SCHEMA:{self.db_schema}]\n\n'

        # --- General info ---
        res += '## General\n'
        res += f'- Status: {self.status}\n'
        res += f'- Trigger type: {self.trigger_type}\n'

        if self.event:
            res += f'- Event: {self.event}\n'

        if self.table_name:
            res += f'- Table: {self.table_name}\n'
            res += f'[TABLE:{self.table_name}]\n'

        # --- Dependencies ---
        if self.dependencies:
            res += '\n## Dependencies\n'
            for dep in self.dependencies:
                res += f'{dep}\n'

        # --- Signature ---
        if self.signature:
            res += '\n## Signature\n'
            res += '```sql\n'
            res += f'{self.signature.strip()}\n'
            res += '```\n'

        res += self._render_definition_path(**kwargs)

        return res
