'''
select t.NAME as package_name,
       t.TYPE,
       json_arrayagg(t.TEXT order by t.LINE returning clob) as definition

  from user_source t
 where t.TYPE in ('PACKAGE BODY', 'PACKAGE')
 GROUP by t.NAME, t.TYPE;

with dependencies as
 (select t.name,
         json_objectagg(t.OBJECT_TYPE value t.dependencies returning clob) as dependencies
    from (select ud.name,
                 p.OBJECT_TYPE,
                 json_arrayagg(json_object('type' value
                                           lower(ud.REFERENCED_TYPE),
                                           'schema' value ud.REFERENCED_OWNER,
                                           'name' value ud.REFERENCED_NAME)
                               returning clob) as dependencies
            from user_dependencies ud
            join user_objects p
              on ud.name = p.OBJECT_NAME
             and ud.type = p.object_type
             and p.OBJECT_TYPE in ('PACKAGE BODY', 'PACKAGE')

           where ud.REFERENCED_OWNER != 'SYS'
           group by ud.name, p.OBJECT_TYPE) t

   group by t.name),
public_routines as
 (SELECT t.package_name,
         json_objectagg(T.OBJECT_NAME || '~' || T.OVERLOAD value
                        json_object('type' value case
                                      when t.return_type is not null then
                                       'function'
                                      else
                                       'procedure'
                                    end,
                                    'parameters' value t.PARAMS,
                                    'return_type' value t.return_type
                                    returning clob) returning clob) AS ROUTINES
    FROM (select A.PACKAGE_NAME,
                 a.OBJECT_NAME,
                 A.OVERLOAD,
                 json_arrayagg(case
                                 when a.POSITION > 0 then
                                  json_object('name' value a.ARGUMENT_NAME,
                                              'mode' value a.IN_OUT,
                                              'type' value a.DATA_TYPE)
                               end order by a.POSITION returning clob) as PARAMS,
                 max(case
                       when a.POSITION = 0 then
                        a.DATA_TYPE
                     end) as return_type

            from user_arguments a

           where A.PACKAGE_NAME IS NOT NULL
           group by A.PACKAGE_NAME, a.OBJECT_NAME, A.OVERLOAD

          ) T
   GROUP BY T.PACKAGE_NAME)

select t.OBJECT_NAME as package_name,
       case
         when pb.OBJECT_NAME is not null then
          1
         else
          0
       end as has_body,
       d.dependencies,
       pr.ROUTINES as public_routines

  from user_objects t
  left join user_objects pb
    on t.OBJECT_NAME = pb.OBJECT_NAME
   and pb.OBJECT_TYPE = 'PACKAGE BODY'
  left join dependencies d
    on t.OBJECT_NAME = d.name
  left join public_routines pr
    on t.OBJECT_NAME = pr.package_name

 where t.object_type = 'PACKAGE';
'''