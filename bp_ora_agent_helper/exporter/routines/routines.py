'''
with routine_data as (
select t.NAME,
       json_arrayagg(t.signature order by t.LINE returning clob) as signature,
       json_arrayagg(t.TEXT order by t.LINE returning clob) as definition
from (
select t.NAME,
       t.LINE,
       t.TEXT,
       case
         when t.LINE < min(case
                             when REGEXP_LIKE(t.TEXT, '\s(IS|AS)\s', 'i') then
                              t.LINE
                           end) over(partition by t.NAME) then
          t.TEXT
       end as signature

  from user_source t
  join user_procedures up
    on t.NAME = up.OBJECT_NAME
 where up.OBJECT_TYPE in ('PROCEDURE', 'FUNCTION')) t
 group by t.NAME
), params_data as (
select a.OBJECT_NAME,
       json_arrayagg(case when a.POSITION > 0 then
                          json_object('name' value a.ARGUMENT_NAME,
                                      'mode' value a.IN_OUT,
                                      'type' value a.DATA_TYPE) end
                     order by a.POSITION
                                      returning clob) as "parameters",
       max(case when a.POSITION = 0 then a.DATA_TYPE end) as return_type
  from user_arguments a
  join user_procedures up
    on a.OBJECT_NAME = up.OBJECT_NAME
 where up.OBJECT_TYPE in ('PROCEDURE', 'FUNCTION')
 group by a.OBJECT_NAME
), dependencies as (
select ud.name,
       json_arrayagg(json_object('type' value lower(ud.REFERENCED_TYPE),
                                 'schema' value ud.REFERENCED_OWNER,
                                 'name' value ud.REFERENCED_NAME) returning clob) as dependencies
  from user_dependencies ud
  join user_procedures up
    on up.OBJECT_NAME = ud.name
 where up.OBJECT_TYPE in ('PROCEDURE', 'FUNCTION')
   and ud.REFERENCED_OWNER != 'SYS'
 group by ud.name
)

select t.OBJECT_NAME,
       t.OBJECT_TYPE,
       ud.dependencies,
       a."parameters",
       a.return_type,
       rd.signature,
       rd.definition

  from user_procedures t
  left join dependencies ud
    on t.OBJECT_NAME = ud.name
  left join params_data a
    on t.OBJECT_NAME = a.OBJECT_NAME
  left join routine_data rd
    on t.OBJECT_NAME = rd.NAME

 where t.OBJECT_TYPE in ('PROCEDURE', 'FUNCTION');
'''