from oracledb import Connection

from dbmd.ora.exporter.sql import ExporterSQL


class IndexSQL(ExporterSQL):

    select_tables = '''
    select table_name
      from all_tables
     where owner = :schema
     order by table_name
    '''

    select_views = '''
    select view_name
      from all_views
     where owner = :schema
     order by view_name
    '''

    select_routines = '''
    select object_name, object_type
      from all_objects
     where owner = :schema
       and object_type in ('FUNCTION', 'PROCEDURE')
     order by object_type, object_name
    '''

    select_packages = '''
    select object_name
      from all_objects
     where owner = :schema
       and object_type = 'PACKAGE'
     order by object_name
    '''

    select_triggers = '''
    select trigger_name
      from all_triggers
     where :schema = any(owner, table_owner)
     order by trigger_name
    '''

    select_types = '''
    select type_name
      from all_types
     where owner = :schema
     order by type_name
    '''


def get_index(conn: Connection, schema: str) -> dict:
    results = {}

    with conn.cursor() as cur:
        IndexSQL.select_tables.execute(cur, {'schema': schema})
        results['tables'] = [row[0] for row in cur.fetchall()]

    with conn.cursor() as cur:
        IndexSQL.select_views.execute(cur, {'schema': schema})
        results['views'] = [row[0] for row in cur.fetchall()]

    with conn.cursor() as cur:
        IndexSQL.select_routines.execute(cur, {'schema': schema})
        routines = cur.fetchall()
        results['functions']  = [r[0] for r in routines if r[1] == 'FUNCTION']
        results['procedures'] = [r[0] for r in routines if r[1] == 'PROCEDURE']

    with conn.cursor() as cur:
        IndexSQL.select_packages.execute(cur, {'schema': schema})
        results['packages'] = [row[0] for row in cur.fetchall()]

    with conn.cursor() as cur:
        IndexSQL.select_triggers.execute(cur, {'schema': schema})
        results['triggers'] = [row[0] for row in cur.fetchall()]

    with conn.cursor() as cur:
        IndexSQL.select_types.execute(cur, {'schema': schema})
        results['types'] = [row[0] for row in cur.fetchall()]

    return results
