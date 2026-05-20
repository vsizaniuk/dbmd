from collections.abc import AsyncGenerator

from dbmd.serializers import MDBaseModel
from dbmd.pg.exporter.exporter import Exporter
from dbmd.pg.exporter.sql import connect
from dbmd.pg.exporter.tables import sql
from .serializer import (Column, ForeignKeyReference, ForeignKey,
                          UniqueConstraint, Index, TableTrigger, TableSchema)


_DELETE_RULES = {
    'a': 'NO ACTION',
    'r': 'RESTRICT',
    'c': 'CASCADE',
    'n': 'SET NULL',
    'd': 'SET DEFAULT',
}


class TablesExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'tables'):
        super().__init__(schema, subdir)

    @staticmethod
    def convert_columns(columns: list | None) -> list[Column]:
        if not columns:
            return []
        return [Column(
            name=col['name'],
            type=col['type'],
            nullable=col['nullable'],
            default=col['default'],
            description=col['description']
        ) for col in columns]

    def convert_constraints(self, constraints: list | None):
        if not constraints:
            return
        for con in constraints:
            c_type   = con['constraint_type']
            c_name   = con['constraint_name']
            c_cols   = con['constrained_columns']

            if c_type in ('p', 'u'):
                yield c_type, UniqueConstraint(name=c_name, columns=c_cols)
            elif c_type == 'f':
                ref = ForeignKeyReference(
                    ref_schema=con['ref_schema'],
                    context_schema=self.schema,
                    ref_table=con['ref_table'],
                    ref_columns=con['ref_columns']
                )
                yield c_type, ForeignKey(
                    name=c_name,
                    columns=c_cols,
                    references=ref,
                    on_delete=_DELETE_RULES.get(con['delete_rule'])
                )

    @staticmethod
    def convert_indexes(indexes: list | None) -> list[Index]:
        if not indexes:
            return []
        return [Index(
            name=idx['name'],
            type=idx['type'],
            unique=idx['unique'],
            columns=idx['columns'],
            definition=idx['definition']
        ) for idx in indexes]

    @staticmethod
    def convert_triggers(triggers: list | None) -> list[TableTrigger]:
        if not triggers:
            return []
        return [TableTrigger(
            name=tr['name'],
            type=tr['type'],
            timing=tr['timing'],
            enabled=tr['enabled'],
            function_schema=tr['function_schema'],
            function=tr['function']
        ) for tr in triggers]

    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        pool = await connect()
        async with pool.acquire() as conn:
            tables          = await sql.get_tables(conn, self.schema)
            constraints_rows = await sql.get_table_constraints(conn, self.schema)
            indexes_rows    = await sql.get_table_indexes(conn, self.schema)
            triggers_rows   = await sql.get_table_triggers(conn, self.schema)

        constraints = {row['table_name']: row['constraints'] for row in constraints_rows}
        indexes     = {row['table_name']: row['indexes']     for row in indexes_rows}
        triggers    = {row['table_name']: row['triggers']    for row in triggers_rows}

        for row in tables:
            table = TableSchema(
                db_schema=self.schema,
                name=row['table_name'],
                description=row['description'],
                columns=self.convert_columns(row['columns']),
                row_count=row['row_count']
            )

            for c_type, con in self.convert_constraints(constraints.get(row['table_name'])):
                if c_type == 'p':
                    table.primary_key = con
                elif c_type == 'u':
                    table.unique_constraints.append(con)
                elif c_type == 'f':
                    table.foreign_keys.append(con)

            table.indexes  = self.convert_indexes(indexes.get(row['table_name']))
            table.triggers = self.convert_triggers(triggers.get(row['table_name']))

            yield table, None
