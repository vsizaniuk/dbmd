import asyncpg

from dbmd.pg.exporter.sql import ExporterSQL


class TriggersSQL(ExporterSQL):

    select_triggers = '''
    select tr.tgname                                                          as trigger_name,
           t.relname                                                           as table_name,
           n.nspname                                                           as db_schema,
           case when tr.tgtype & 1  = 1  then 'ROW' else 'STATEMENT' end     as trigger_type,
           case when tr.tgtype & 2  = 2  then 'BEFORE'
                when tr.tgtype & 64 = 64 then 'INSTEAD OF'
                else 'AFTER' end                                               as timing,
           array_remove(array[
               case when tr.tgtype & 4  = 4  then 'INSERT'   end,
               case when tr.tgtype & 8  = 8  then 'DELETE'   end,
               case when tr.tgtype & 16 = 16 then 'UPDATE'   end,
               case when tr.tgtype & 32 = 32 then 'TRUNCATE' end
           ], null)::text[]                                                    as events,
           tr.tgenabled != 'D'                                                 as enabled,
           pn.nspname                                                          as function_schema,
           p.proname                                                           as function_name,
           case when pn.nspname != $1
                then pg_get_functiondef(p.oid)
           end                                                                 as definition
      from pg_trigger tr
      join pg_class t
        on t.oid = tr.tgrelid
      join pg_namespace n
        on n.oid = t.relnamespace
      join pg_proc p
        on p.oid = tr.tgfoid
      join pg_namespace pn
        on pn.oid = p.pronamespace
     where n.nspname       = $1
       and not tr.tgisinternal
       and ($2::text is null or tr.tgname = $2)
     order by t.relname, tr.tgname
    '''


async def get_triggers(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TriggersSQL.select_triggers.execute(conn, schema, name)
