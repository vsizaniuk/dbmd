from typing import List, Optional
from ..serializers import ObjectTypes, Parameter, Dependency, MDBaseModel


class PackagePublicRoutine(MDBaseModel):
    name: str
    overload: int
    type: ObjectTypes
    parameters: List[Parameter] = []
    return_type: Optional[str] = None

    def render_md(self, **kwargs):
        res = f'### {self.type.name.title()}: {self.name}\n'
        res += f'[ROUTINE:{self.name}]\n'

        if self.overload:
            res += f' (overload {self.overload})'
        res += '\n'

        # --- Signature (lightweight) ---
        if self.parameters:
            res += '- Parameters:\n'
            for param in self.parameters:
                res += f'  - {param}\n'

        if self.type == ObjectTypes.FUNCTION and self.return_type:
            res += f'- Returns: {self.return_type}\n'

        return res


class Package(MDBaseModel):
    type: ObjectTypes = ObjectTypes.PACKAGE
    db_schema: str
    name: str
    spec_dependencies: List[Dependency] = []
    body_dependencies: List[Dependency] = []
    has_body: bool = True
    public_routines: List[PackagePublicRoutine] = []

    def render_md(self, **kwargs):
        res = f'# Package: {self.name} \n[TYPE:PACKAGE]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[PACKAGE:{self.name}]\n'

        # --- Body flag ---
        res += '## General\n'
        res += f'- Has body: {"YES" if self.has_body else "NO"}\n'

        # --- Public routines ---
        if self.public_routines:
            res += '\n## Public routines\n'
            for routine in self.public_routines:
                res += f'{routine.render_md()}\n'

        # --- Spec dependencies ---
        if self.spec_dependencies:
            res += '\n## Spec dependencies\n'
            for dep in self.spec_dependencies:
                res += f'{dep}\n'

        # --- Body dependencies ---
        if self.body_dependencies:
            res += '\n## Body dependencies\n'
            for dep in self.body_dependencies:
                res += f'{dep}\n'

        res += self._render_definition_path(**kwargs)

        return res
