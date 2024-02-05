-- This code was written by Nico de Graaff
-- and taken from the repository:
-- https://git.data.amsterdam.nl/team_stadsbeheer/afleiding_rijtjeswoningen

--
drop table if exists bag_pand_woningcluster;
create table bag_pand_woningcluster

as
select
    -- de panden liggen maximaal 10 cm uit elkaar en het cluster bevat minimaal twee panden
    ST_ClusterDBScan(geometrie, 0.1, 2) over () as woningcluster_id,
    *
from (
         select id AS pand_id,
                concat(bouwblok_id::varchar, openbare_ruimte_id) as bouwblokzijde,
                geometrie,
                aantal_vot,
                aantal_woningen,
                aantal_onzelfst_eenheden,
                openbare_ruimte_id,
                bouwblok_id,
                ligging,
                type_woonobject,
                status,
                begin_geldigheid,
                einde_geldigheid
         from bag_pand_afleiding_objecten
         where aantal_woningen = 1
         and   aantal_vot = 1) panden
;
--
drop index if exists bag_pand_woningcluster_gidx;
create index bag_pand_woningcluster_gidx on bag_pand_woningcluster using GIST (geometrie);
--


--
--
-- aggregatie naar zuivere clusters:
drop table if exists bag_agg_pand_woningcluster CASCADE;
create table bag_agg_pand_woningcluster
as
select *
from (
         select st_collect(geometrie)                        geometrie,
                concat(bouwblokzijde, woningcluster_id)      id,
                array_agg(pand_id)                           bevat_panden,
                sum(aantal_vot)                              aantal_vot,
                sum(aantal_woningen)                         aantal_woningen,
                sum(aantal_onzelfst_eenheden)                aantal_onzelfst_eenheden,
                bouwblok_id
         from public.bag_pand_woningcluster
         where woningcluster_id is not null
         group by bouwblokzijde, woningcluster_id, bouwblok_id) clusters
where
-- alleen funtionele cluster met meer dan 1 pand
cardinality(bevat_panden) > 1
;
--
drop index if exists bag_agg_pand_woningcluster_gidx;
create index bag_agg_pand_woningcluster_gidx on bag_agg_pand_woningcluster using GIST (geometrie);


--
--
-- rijtjeshuizen
drop table if exists bag_rijtjeshuis CASCADE;
create table bag_rijtjeshuis
as
SELECT
    unnest(bevat_panden) AS pand_id,
    id AS rij_id
FROM public.bag_agg_pand_woningcluster

