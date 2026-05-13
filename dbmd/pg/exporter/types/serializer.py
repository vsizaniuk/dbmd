from ..serializers import ObjectTypes, MDBaseModel


class CompositeAttribute(MDBaseModel):
    name:     str
    type:     str
    nullable: bool

    def render_md(self, **kwargs):
        nullable = '' if self.nullable else ' not null'
        return f'- {self.name}: {self.type}{nullable}'


class CompositeTypeDetails(MDBaseModel):
    type:        ObjectTypes = ObjectTypes.COMPOSITE_TYPE
    db_schema:   str
    name:        str
    description: str | None = None
    attributes:  list[CompositeAttribute] = []

    def render_md(self, **kwargs):
        res = f'# Composite Type: {self.name} \n[TYPE:COMPOSITE_TYPE]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        if self.description:
            res += f'{self.description}\n\n'

        if self.attributes:
            res += '## Attributes\n'
            for attr in self.attributes:
                res += f'{attr}\n'

        res += self._render_definition_path(**kwargs)
        return res


class EnumTypeDetails(MDBaseModel):
    type:        ObjectTypes = ObjectTypes.ENUM_TYPE
    db_schema:   str
    name:        str
    description: str | None = None
    values:      list[str]

    def render_md(self, **kwargs):
        res = f'# Enum Type: {self.name} \n[TYPE:ENUM_TYPE]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        if self.description:
            res += f'{self.description}\n\n'

        res += '## Values\n'
        for val in self.values:
            res += f'- {val}\n'

        res += self._render_definition_path(**kwargs)
        return res


class DomainConstraint(MDBaseModel):
    name:  str
    check: str

    def render_md(self, **kwargs):
        return f'- {self.name}: {self.check}'


class DomainTypeDetails(MDBaseModel):
    type:          ObjectTypes = ObjectTypes.DOMAIN_TYPE
    db_schema:     str
    name:          str
    description:   str | None = None
    base_type:     str
    not_null:      bool
    default_value: str | None = None
    constraints:   list[DomainConstraint] = []

    def render_md(self, **kwargs):
        res = f'# Domain Type: {self.name} \n[TYPE:DOMAIN_TYPE]\n[SCHEMA:{self.db_schema}]\n\n'
        res += f'[NAME:{self.name}]\n'

        if self.description:
            res += f'{self.description}\n\n'

        res += '## General\n'
        res += f'- Base type: {self.base_type}\n'
        if self.not_null:
            res += '- Not null: YES\n'
        if self.default_value:
            res += f'- Default: {self.default_value}\n'

        if self.constraints:
            res += '\n## Constraints\n'
            for con in self.constraints:
                res += f'{con}\n'

        res += self._render_definition_path(**kwargs)
        return res
