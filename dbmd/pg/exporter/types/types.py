from typing import AsyncGenerator

from dbmd.serializers import MDBaseModel
from dbmd.pg.exporter.exporter import Exporter
from dbmd.pg.exporter.sql import connect
from dbmd.pg.exporter.types import sql
from .serializer import (CompositeAttribute, CompositeTypeDetails,
                          EnumTypeDetails, DomainConstraint, DomainTypeDetails)


class TypesExporter(Exporter):

    def __init__(self, schema: str = None, subdir: str = 'types'):
        super().__init__(schema, subdir)

    @staticmethod
    def convert_attributes(attrs: list | None) -> list[CompositeAttribute]:
        if not attrs:
            return []
        return [CompositeAttribute(
            name=a['name'],
            type=a['type'],
            nullable=a['nullable']
        ) for a in attrs]

    @staticmethod
    def convert_domain_constraints(cons: list | None) -> list[DomainConstraint]:
        if not cons:
            return []
        return [DomainConstraint(name=c['name'], check=c['check']) for c in cons]

    async def gather_data(self) -> AsyncGenerator[tuple[MDBaseModel, str | None]]:
        pool = await connect()
        async with pool.acquire() as conn:
            composite_types = await sql.get_composite_types(conn, self.schema)
            enum_types      = await sql.get_enum_types(conn, self.schema)
            domain_types    = await sql.get_domain_types(conn, self.schema)

        for row in composite_types:
            yield CompositeTypeDetails(
                db_schema=self.schema,
                name=row['name'],
                description=row['description'],
                attributes=self.convert_attributes(row['attributes'])
            ), None

        for row in enum_types:
            yield EnumTypeDetails(
                db_schema=self.schema,
                name=row['name'],
                description=row['description'],
                values=list(row['values'])
            ), None

        for row in domain_types:
            yield DomainTypeDetails(
                db_schema=self.schema,
                name=row['name'],
                description=row['description'],
                base_type=row['base_type'],
                not_null=row['not_null'],
                default_value=row['default_value'],
                constraints=self.convert_domain_constraints(row['constraints'])
            ), None
