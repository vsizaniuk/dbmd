import asyncpg

from dbmd.pg.exporter.sql import ExporterSQL


class RoutinesSQL(ExporterSQL):

    select_routines = '''
    with params as (
        select p.oid,
               jsonb_agg(
                   jsonb_build_object(
                       'name', coalesce(t.argname, '$' || t.rn::text),
                       'mode', case t.argmode
                                   when 'i' then 'IN'
                                   when 'o' then 'OUT'
                                   when 'b' then 'INOUT'
                                   when 'v' then 'VARIADIC'
                                   else          'IN'
                               end,
                       'type', format_type(t.argtype, null)
                   ) order by t.rn
               ) as parameters
          from pg_proc p
          join pg_namespace n on n.oid = p.pronamespace,
               unnest(
                   coalesce(p.proallargtypes, p.proargtypes::oid[]),
                   coalesce(p.proargmodes::char[],
                            array_fill('i'::char,
                                       array[cardinality(p.proargtypes::oid[])])),
                   coalesce(p.proargnames,
                            array_fill(null::text,
                                       array[cardinality(coalesce(p.proallargtypes,
                                                                  p.proargtypes::oid[]))]))
               ) with ordinality as t(argtype, argmode, argname, rn)
         where n.nspname  = $1
           and p.prokind in ('f', 'p')
           and t.argmode in ('i', 'b', 'v')
           and ($2::text is null or p.proname = $2)
         group by p.oid
    ),
    routine_deps as (
        select d.objid as routine_oid,
               jsonb_agg(
                   jsonb_build_object(
                       'type',   case c.relkind
                                     when 'r' then 'table'
                                     when 'v' then 'view'
                                     when 'S' then 'sequence'
                                     else          'other'
                                 end,
                       'db_schema', rn.nspname,
                       'name',   c.relname
                   )
               ) as dependencies
          from pg_depend d
          join pg_class c
            on c.oid        = d.refobjid
           and d.refclassid = 'pg_class'::regclass
          join pg_namespace rn
            on rn.oid = c.relnamespace
         where d.classid  = 'pg_proc'::regclass
           and d.deptype in ('n', 'a')
           and c.relkind  in ('r', 'v', 'S')
         group by d.objid
    )
    select p.proname                                                   as name,
           case p.prokind when 'f' then 'FUNCTION'
                          when 'p' then 'PROCEDURE' end                as routine_type,
           pg_get_function_result(p.oid)                               as return_type,
           'CREATE OR REPLACE '
               || case p.prokind when 'f' then 'FUNCTION '
                                 when 'p' then 'PROCEDURE ' end
               || p.proname || '(' || pg_get_function_arguments(p.oid) || ')'
               || case when p.prokind = 'f'
                       then ' returns ' || pg_get_function_result(p.oid)
                       else '' end                                      as signature,
           pg_get_functiondef(p.oid)                                   as definition,
           obj_description(p.oid, 'pg_proc')                           as description,
           pa.parameters,
           rd.dependencies
      from pg_proc p
      join pg_namespace n  on n.oid  = p.pronamespace
      left join params pa  on pa.oid = p.oid
      left join routine_deps rd on rd.routine_oid = p.oid
     where n.nspname    = $1
       and p.prokind in ('f', 'p')
       and ($2::text is null or p.proname = $2)
    '''


async def get_routines(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await RoutinesSQL.select_routines.execute(conn, schema, name)
