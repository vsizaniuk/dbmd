import asyncpg

from dbmd.pg.exporter.sql import ExporterSQL


class IndexSQL(ExporterSQL):

    select_tables = '''
    select c.relname as name
      from pg_class c
      join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = $1
       and c.relkind in ('r', 'p')
       and not c.relispartition
     order by c.relname
    '''

    select_views = '''
    select c.relname as name
      from pg_class c
      join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = $1
       and c.relkind = 'v'
     order by c.relname
    '''

    select_routines = '''
    select p.proname as name,
           case p.prokind when 'f' then 'FUNCTION' when 'p' then 'PROCEDURE' end as routine_type
      from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = $1
       and p.prokind in ('f', 'p')
     order by p.prokind, p.proname
    '''

    select_triggers = '''
    select distinct tr.tgname as name
      from pg_trigger tr
      join pg_class t  on t.oid  = tr.tgrelid
      join pg_namespace n on n.oid = t.relnamespace
     where n.nspname = $1
       and not tr.tgisinternal
     order by tr.tgname
    '''

    select_types = '''
    select t.typname as name
      from pg_type t
      join pg_namespace n on n.oid = t.typnamespace
     where n.nspname = $1
       and t.typtype in ('c', 'e', 'd')
       and not exists (select 1 from pg_class c where c.reltype = t.oid)
     order by t.typname
    '''


async def get_index(conn: asyncpg.Connection, schema: str) -> dict:
    tables   = await IndexSQL.select_tables.execute(conn, schema)
    views    = await IndexSQL.select_views.execute(conn, schema)
    routines = await IndexSQL.select_routines.execute(conn, schema)
    triggers = await IndexSQL.select_triggers.execute(conn, schema)
    types    = await IndexSQL.select_types.execute(conn, schema)

    return {
        'tables':     [r['name'] for r in tables],
        'views':      [r['name'] for r in views],
        'functions':  [r['name'] for r in routines if r['routine_type'] == 'FUNCTION'],
        'procedures': [r['name'] for r in routines if r['routine_type'] == 'PROCEDURE'],
        'triggers':   [r['name'] for r in triggers],
        'types':      [r['name'] for r in types],
    }
