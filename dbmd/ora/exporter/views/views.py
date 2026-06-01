import asyncio
from collections.abc import AsyncGenerator

from dbmd.ora.exporter.exporter import Exporter
from dbmd.ora.exporter.serializers import ColumnType

from dbmd.ora.exporter.views import sql
from .serializer import ViewSchema, ViewColumn


class ViewsExporter(Exporter):


    def __init__(self, schema: str = None, subdir: str = 'views'):
        super().__init__(schema, subdir)


    async def get_views(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_views(conn, self.schema, self.name)

        return await asyncio.to_thread(query_f)

    def convert_columns(self, columns):
        columns = self.read_clob_json(columns) or []

        for col in columns:
            col_type = ColumnType(**col['type'])

            yield ViewColumn(
                name=col['name'],
                type=col_type,
                description=col['description'])


    async def gather_data(self) -> AsyncGenerator[tuple[ViewSchema, str | None]]:
        try:
            views = await self.get_views()

            for view_name, desc, view_sql, columns, dependencies in views:
                view_columns = [c for c in self.convert_columns(columns)]
                dependencies = self.convert_dependencies(dependencies)
                view_sql = self.read_clob_str(view_sql)

                view = ViewSchema(
                    db_schema=self.schema,
                    name=view_name,
                    description=desc,
                    columns=view_columns,
                    definition=view_sql,
                    dependencies=dependencies)

                yield view, None

        finally:
            self.cleanup()
