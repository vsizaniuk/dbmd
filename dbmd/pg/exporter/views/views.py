from typing import AsyncGenerator

from dbmd.serializers import MDBaseModel
from dbmd.pg.exporter.exporter import Exporter
from dbmd.pg.exporter.sql import connect
from dbmd.pg.exporter.views import sql
from .serializer import ViewColumn, ViewSchema


class ViewsExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'views'):
        super().__init__(schema, subdir)

    @staticmethod
    def convert_columns(columns: list | None) -> list[ViewColumn]:
        if not columns:
            return []
        return [ViewColumn(
            name=col['name'],
            type=col['type'],
            description=col['description']
        ) for col in columns]

    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        pool = await connect()
        async with pool.acquire() as conn:
            views = await sql.get_views(conn, self.schema)

        for row in views:
            view = ViewSchema(
                db_schema=self.schema,
                name=row['view_name'],
                description=row['description'],
                columns=self.convert_columns(row['columns']),
                definition=row['view_definition'],
                dependencies=self.convert_dependencies(row['dependencies'])
            )
            yield view, None
