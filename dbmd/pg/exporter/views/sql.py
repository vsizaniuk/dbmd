import asyncpg

from dbmd.pg.exporter.sql import ExporterSQL


class ViewsSQL(ExporterSQL):

    select_views = '''
    with view_cols as (
        select a.attrelid,
               jsonb_agg(
                   jsonb_build_object(
                       'name',        a.attname,
                       'type',        format_type(a.atttypid, a.atttypmod),
                       'description', col_description(a.attrelid, a.attnum)
                   ) order by a.attnum
               ) as columns
          from pg_attribute a
          join pg_class c
            on c.oid = a.attrelid
          join pg_namespace n
            on n.oid = c.relnamespace
         where n.nspname    = $1
           and a.attnum     > 0
           and not a.attisdropped
           and c.relkind    = 'v'
         group by a.attrelid
    ),
    view_deps as (
        select vtu.view_name,
               jsonb_agg(
                   jsonb_build_object(
                       'type',      case c2.relkind
                                        when 'r' then 'table'
                                        when 'v' then 'view'
                                        else          'other'
                                    end,
                       'db_schema', vtu.table_schema,
                       'name',      vtu.table_name
                   )
               ) as dependencies
          from information_schema.view_table_usage vtu
          join pg_class c2
            on c2.relname = vtu.table_name
          join pg_namespace n2
            on n2.nspname = vtu.table_schema
           and n2.oid     = c2.relnamespace
         where vtu.view_schema = $1
         group by vtu.view_name
    )
    select c.relname                  as view_name,
           obj_description(c.oid)     as description,
           pg_get_viewdef(c.oid, true) as view_definition,
           vc.columns,
           vd.dependencies
      from pg_class c
      join pg_namespace n
        on n.oid     = c.relnamespace
       and n.nspname = $1
      left join view_cols vc
        on vc.attrelid = c.oid
      left join view_deps vd
        on vd.view_name  = c.relname
     where c.relkind = 'v'
       and ($2::text is null or c.relname = $2)
    '''


async def get_views(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await ViewsSQL.select_views.execute(conn, schema, name)
