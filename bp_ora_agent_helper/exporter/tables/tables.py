import asyncio
import aiofiles
import json
import os
from typing import AsyncGenerator

from bp_ora_agent_helper.exporter.exporter import Exporter
from ..sql import connect, get_env_or_raise

import bp_ora_agent_helper.exporter.tables.sql as sql
from .serializer import (TableSchema, UniqueConstraint, ForeignKeyReference,
                         ForeignKey, TableTrigger, Index, Column, ColumnType)



class TablesExporter(Exporter):


    def __init__(self, schema: str = None):
        self.schema = schema or get_env_or_raise('ORA_SCHEMA')
        self.pool = connect()
        self.connections = []

    async def get_tables(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_tables(conn)

        return await asyncio.to_thread(query_f)

    async def get_constraints(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_table_constraints(conn)

        return await asyncio.to_thread(query_f)

    async def get_triggers(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_table_triggers(conn, self.schema)

        return await asyncio.to_thread(query_f)

    async def get_indexes(self):

        def query_f():
            conn = self.pool.acquire()
            self.connections.append(conn)

            return sql.get_table_indexes(conn, self.schema)

        return await asyncio.to_thread(query_f)

    @staticmethod
    def convert_columns(columns):
        if columns:
            if not isinstance(columns, str):
                columns = columns.read()

            columns = json.loads(columns)
        else:
            columns = []

        for col in columns:

            col_type = ColumnType(**col['type'])

            yield Column(
                name=col['name'],
                type=col_type,
                nullable=col['nullable'].upper() == 'Y',
                default=col['default'],
                description=col['description'])

    def convert_constraints(self, constraints):

        if constraints:
            if not isinstance(constraints, str):
                constraints = constraints.read()
            constraints = json.loads(constraints)
        else:
            constraints = []

        for cons in constraints:
            c_type = cons['constraint_type']
            c_name = cons['constraint_name']
            c_columns = cons['constrained_columns']

            if c_type in ('U', 'P'):
                uk = UniqueConstraint(name=c_name,columns=c_columns)
                yield c_type, uk
            elif c_type == 'R':
                reference = cons['ref_constraint']
                reference = ForeignKeyReference(db_schema=reference['schema'],
                                                context_schema=self.schema,
                                                table=reference['table'],
                                                columns=reference['columns'])
                fk = ForeignKey(name=c_name, columns=c_columns, references=reference, on_delete=cons['delete_rule'])
                yield c_type, fk

    @staticmethod
    def convert_triggers(triggers):

        if triggers:
            if not isinstance(triggers, str):
                triggers = triggers.read()
            triggers = json.loads(triggers)
        else:
            triggers = []

        for trigger in triggers:

            yield TableTrigger(name=trigger['name'],
                               type=trigger['type'],
                               timing=trigger['event'],
                               status=trigger['status'])

    @staticmethod
    def convert_indexes(indexes):

        if indexes:
            if not isinstance(indexes, str):
                indexes = indexes.read()
            indexes = json.loads(indexes)
        else:
            indexes = []

        for index in indexes:

            yield Index(name=index['name'],
                        type=index['type'],
                        columns=index['columns'],
                        expression=index['expression'])

    async def gather_data(self) -> AsyncGenerator[TableSchema]:
        try:
            tables = await self.get_tables()
            constraints = {tab: constraints for tab, constraints in await self.get_constraints()}
            triggers = {tab: triggers for tab, triggers in await self.get_triggers()}
            indexes = {tab: indexes for tab, indexes in await self.get_indexes()}

            for table_name, table_desc, table_columns, row_count in tables:

                table_columns = [c for c in self.convert_columns(table_columns)]
                table_constraints = constraints.get(table_name)
                table_triggers = triggers.get(table_name)
                table_indexes = indexes.get(table_name)

                table = TableSchema(db_schema=self.schema,
                                    name=table_name,
                                    columns=table_columns,
                                    row_count=row_count)

                table.triggers = [t for t in self.convert_triggers(table_triggers)]
                table.indexes = [i for i in self.convert_indexes(table_indexes)]

                for c_type, cons in self.convert_constraints(table_constraints):
                    if c_type == 'P':
                        table.primary_key = cons
                    elif c_type == 'U':
                        table.unique_constraints.append(cons)
                    elif c_type == 'R':
                        table.foreign_keys.append(cons)

                yield table
        finally:
            for conn in self.connections:
                conn.close()
            self.connections.clear()



    async def export_md(self):
        path = os.path.join('.', 'bp_llm_help', self.schema, 'tables')
        os.makedirs(path, exist_ok=True)

        async for tab in self.gather_data():
            file_path = os.path.join(path, f'{tab.name}.md')
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(tab.render_md())
