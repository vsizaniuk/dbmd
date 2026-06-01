import asyncpg

from dbmd.pg.exporter.sql import ExporterSQL


class TablesSQL(ExporterSQL):

    select_tables = '''
    with columns as (
        select a.attrelid,
               jsonb_agg(
                 jsonb_build_object(
                     'name',        a.attname,
                     'type',        format_type(a.atttypid, a.atttypmod),
                     'nullable',    not a.attnotnull,
                     'default',     pg_get_expr(d.adbin, d.adrelid),
                     'description', col_description(a.attrelid, a.attnum)
                 ) order by a.attnum
             ) as columns
          from pg_attribute a
          join pg_class c
            on c.oid = a.attrelid
          join pg_namespace n
            on n.oid = c.relnamespace
          left join pg_attrdef d
            on d.adrelid = a.attrelid
           and d.adnum   = a.attnum
         where n.nspname  = $1
           and a.attnum   > 0
           and not a.attisdropped
           and c.relkind  in ('r', 'p')
           and not c.relispartition
           and ($2::text is null or c.relname = $2)
         group by a.attrelid
    )

    select c.relname               as table_name,
           obj_description(c.oid)  as description,
           s.n_live_tup            as row_count,
           cols.columns
      from pg_class c
      join pg_namespace n
        on n.oid     = c.relnamespace
       and n.nspname = $1
      left join pg_stat_user_tables s
        on s.relname    = c.relname
       and s.schemaname = n.nspname
      left join columns cols
        on cols.attrelid = c.oid
     where c.relkind in ('r', 'p')
       and not c.relispartition
       and ($2::text is null or c.relname = $2)
     order by c.relname
    '''

    select_table_constraints = '''
    with constraint_cols as (
        select con.oid                                                             as constraint_oid,
               jsonb_agg(a.attname order by array_position(con.conkey, a.attnum))  as columns
          from pg_constraint con
          join pg_class t
            on t.oid = con.conrelid
          join pg_namespace n
            on n.oid = t.relnamespace
          join pg_attribute a
            on a.attrelid = con.conrelid
           and a.attnum   = any(con.conkey)
         where n.nspname      = $1
           and con.contype in ('p', 'u', 'f')
           and ($2::text is null or t.relname = $2)
         group by con.oid
    ),
    ref_cols as (
        select con.oid                                                              as constraint_oid,
               jsonb_agg(a.attname order by array_position(con.confkey, a.attnum))  as columns
          from pg_constraint con
          join pg_class t
            on t.oid = con.conrelid
          join pg_namespace n
            on n.oid = t.relnamespace
          join pg_attribute a
            on a.attrelid = con.confrelid
           and a.attnum   = any(con.confkey)
         where n.nspname    = $1
           and con.contype  = 'f'
           and ($2::text is null or t.relname = $2)
         group by con.oid
    )
    select t.relname as table_name,
           jsonb_agg(
               jsonb_build_object(
                   'constraint_type',     con.contype,
                   'constraint_name',     con.conname,
                   'delete_rule',         con.confdeltype,
                   'constrained_columns', cc.columns,
                   'ref_schema',          rn.nspname,
                   'ref_table',           rf.relname,
                   'ref_columns',         rc.columns
               )
           ) as constraints
      from pg_constraint con
      join pg_class t
        on t.oid = con.conrelid
      join pg_namespace n
        on n.oid = t.relnamespace
      left join pg_class rf
        on rf.oid = con.confrelid
      left join pg_namespace rn
        on rn.oid = rf.relnamespace
      left join constraint_cols cc
        on cc.constraint_oid = con.oid
      left join ref_cols rc
        on rc.constraint_oid = con.oid
     where n.nspname      = $1
       and con.contype in ('p', 'u', 'f')
       and ($2::text is null or t.relname = $2)
     group by t.relname
    '''

    select_table_indexes = '''
    with index_cols as (
        select ix.indexrelid,
               jsonb_agg(
                   pg_get_indexdef(ix.indexrelid, t_rn.rn, true)
                   order by t_rn.rn
               ) as columns
          from pg_index ix
          join pg_class t
            on t.oid = ix.indrelid
          join pg_namespace n
            on n.oid = t.relnamespace,
               generate_series(1, array_length(ix.indkey::smallint[], 1)) as t_rn(rn)
         where n.nspname = $1
           and ($2::text is null or t.relname = $2)
         group by ix.indexrelid
    )
    select t.relname as table_name,
           jsonb_agg(
               jsonb_build_object(
                   'name',       i.relname,
                   'type',       am.amname,
                   'unique',     ix.indisunique,
                   'columns',    ic.columns,
                   'definition', pg_get_indexdef(ix.indexrelid)
               )
           ) as indexes
      from pg_index ix
      join pg_class t
        on t.oid = ix.indrelid
      join pg_class i
        on i.oid = ix.indexrelid
      join pg_namespace n
        on n.oid = t.relnamespace
      join pg_am am
        on am.oid = i.relam
      left join index_cols ic
        on ic.indexrelid = ix.indexrelid
     where n.nspname = $1
       and not ix.indisprimary
       and ($2::text is null or t.relname = $2)
       and not exists (
               select 1
                 from pg_constraint c
                where c.conindid = ix.indexrelid
           )
     group by t.relname
    '''

    select_table_triggers = '''
    select t.relname as table_name,
           jsonb_agg(
               jsonb_build_object(
                   'name',            tr.tgname,
                   'type',            case when tr.tgtype & 1 = 1 then 'ROW' else 'STATEMENT' end,
                   'timing',          case
                                          when tr.tgtype & 2  = 2  then 'BEFORE'
                                          when tr.tgtype & 64 = 64 then 'INSTEAD OF'
                                          else 'AFTER'
                                      end,
                   'enabled',         tr.tgenabled != 'D',
                   'function_schema', pn.nspname,
                   'function',        p.proname
               )
           ) as triggers
      from pg_trigger tr
      join pg_class t
        on t.oid = tr.tgrelid
      join pg_namespace n
        on n.oid = t.relnamespace
      join pg_proc p
        on p.oid = tr.tgfoid
      join pg_namespace pn
        on pn.oid = p.pronamespace
     where n.nspname      = $1
       and not tr.tgisinternal
       and ($2::text is null or t.relname = $2)
     group by t.relname
    '''


    select_table_partitions = '''
    select c.relname as table_name,
           case pt.partstrat
               when 'r' then 'RANGE'
               when 'l' then 'LIST'
               when 'h' then 'HASH'
           end as partitioning_type,
           (select count(*)
              from pg_inherits pi
             where pi.inhparent = c.oid)::int as partition_count,
           regexp_replace(pg_get_partkeydef(c.oid), '^(RANGE|LIST|HASH) ', '') as partition_key,
           (select case spt.partstrat
                       when 'r' then 'RANGE'
                       when 'l' then 'LIST'
                       when 'h' then 'HASH'
                   end
              from pg_inherits pi
              join pg_partitioned_table spt on spt.partrelid = pi.inhrelid
             where pi.inhparent = c.oid
             limit 1) as subpartitioning_type,
           (select regexp_replace(pg_get_partkeydef(pi.inhrelid), '^(RANGE|LIST|HASH) ', '')
              from pg_inherits pi
              join pg_partitioned_table spt on spt.partrelid = pi.inhrelid
             where pi.inhparent = c.oid
             limit 1) as subpartition_key
      from pg_class c
      join pg_namespace n on n.oid = c.relnamespace
      join pg_partitioned_table pt on pt.partrelid = c.oid
     where n.nspname = $1
       and ($2::text is null or c.relname = $2)
    '''


async def get_tables(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TablesSQL.select_tables.execute(conn, schema, name)


async def get_table_constraints(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TablesSQL.select_table_constraints.execute(conn, schema, name)


async def get_table_indexes(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TablesSQL.select_table_indexes.execute(conn, schema, name)


async def get_table_triggers(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TablesSQL.select_table_triggers.execute(conn, schema, name)


async def get_table_partitions(conn: asyncpg.Connection, schema: str, name: str | None = None):
    return await TablesSQL.select_table_partitions.execute(conn, schema, name)
