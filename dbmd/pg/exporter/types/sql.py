import asyncpg

from dbmd.pg.exporter.sql import ExporterSQL


class TypesSQL(ExporterSQL):

    select_composite_types = '''
    with type_attrs as (
        select a.attrelid,
               jsonb_agg(
                   jsonb_build_object(
                       'name',     a.attname,
                       'type',     format_type(a.atttypid, a.atttypmod),
                       'nullable', not a.attnotnull
                   ) order by a.attnum
               ) as attributes
          from pg_attribute a
          join pg_class c
            on c.oid = a.attrelid
          join pg_type t
            on t.typrelid = c.oid
          join pg_namespace n
            on n.oid = t.typnamespace
         where a.attnum        > 0
           and not a.attisdropped
           and n.nspname        = $1
         group by a.attrelid
    )
    select t.typname                         as name,
           obj_description(t.oid, 'pg_type') as description,
           ta.attributes
      from pg_type t
      join pg_class c
        on c.oid     = t.typrelid
       and c.relkind = 'c'
      join pg_namespace n
        on n.oid = t.typnamespace
      left join type_attrs ta
        on ta.attrelid = c.oid
     where n.nspname = $1
       and ($2::text is null or t.typname = $2)
    '''

    select_enum_types = '''
    select t.typname                         as name,
           obj_description(t.oid, 'pg_type') as description,
           jsonb_agg(e.enumlabel order by e.enumsortorder) as values
      from pg_type t
      join pg_namespace n
        on n.oid = t.typnamespace
      join pg_enum e
        on e.enumtypid = t.oid
     where n.nspname  = $1
       and t.typtype  = 'e'
       and ($2::text is null or t.typname = $2)
     group by t.typname, t.oid
    '''

    select_domain_types = '''
    with domain_constraints as (
        select con.contypid,
               jsonb_agg(
                   jsonb_build_object(
                       'name',  con.conname,
                       'check', pg_get_constraintdef(con.oid)
                   )
               ) as constraints
          from pg_constraint con
          join pg_type t
            on t.oid = con.contypid
          join pg_namespace n
            on n.oid = t.typnamespace
         where n.nspname = $1
         group by con.contypid
    )
    select t.typname                              as name,
           obj_description(t.oid, 'pg_type')      as description,
           format_type(t.typbasetype, t.typtypmod) as base_type,
           t.typnotnull                            as not_null,
           t.typdefault                            as default_value,
           dc.constraints
      from pg_type t
      join pg_namespace n
        on n.oid = t.typnamespace
      left join domain_constraints dc
        on dc.contypid = t.oid
     where n.nspname = $1
       and t.typtype = 'd'
       and ($2::text is null or t.typname = $2)
    '''


async def get_composite_types(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TypesSQL.select_composite_types.execute(conn, schema, name)


async def get_enum_types(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TypesSQL.select_enum_types.execute(conn, schema, name)


async def get_domain_types(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TypesSQL.select_domain_types.execute(conn, schema, name)
