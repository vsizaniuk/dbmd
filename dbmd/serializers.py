from abc import ABC, abstractmethod

from pydantic import BaseModel


class MDBaseModel(BaseModel, ABC):

    name: str | None = None

    @abstractmethod
    def render_md(self, **kwargs):
        ...

    @staticmethod
    def _render_definition_path(**kwargs):
        res = ''
        definition_path = kwargs.get('definition_path')
        if definition_path:
            res += '\n## Definition\n'
            res += '[DEFINITION]\n'
            res += f'{definition_path}\n'
        return res

    def __str__(self):
        return self.render_md()


class Dependency(MDBaseModel):
    type:      str
    db_schema: str
    name:      str

    def render_md(self, **kwargs):
        return f'- {self.type} {self.db_schema}.{self.name}'
