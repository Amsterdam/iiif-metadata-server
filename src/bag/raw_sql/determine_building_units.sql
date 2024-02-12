-- This logic was written by Nico de Graaff and taken from the repository:
-- https://git.data.amsterdam.nl/team_stadsbeheer/afleiding_rijtjeswoningen
-- Code refactored by Jeroen Beekman

drop table if exists bag_pand_afleiding_objecten;
create table bag_pand_afleiding_objecten
as
with verblijfsobject_selection as (
	select 	pnd.identificatie as pand_id
	,		vot.identificatie  as vot_id
	,		vot.feitelijkgebruikomschrijving
	,		vot.gebruiksdoelwoonfunctieomschrijving as woonfunctie
	,		vot.gebruiksdoelgezondheidszorgfunctieomschrijving as gezondheidsfunctie
    from 	bag_pand pnd
    join	bag_verblijfsobjectpandrelatie vpr
    		on pnd.identificatie  = vpr.pand_id
    join	bag_verblijfsobject vot
     		on vpr.verblijfsobject_id = vot.identificatie
    where 	vot.statusomschrijving  like '%in gebruik%'
      and 	pnd.statusomschrijving  like '%in gebruik%'
)
-- aantal verblijfsobjecten, woningen en ontzelfst. eenheden per pand
, aantallen as (
    select	pand_id
    ,       count(*) as aantal_vot
    ,		count(*) filter (where feitelijkgebruikomschrijving = 'woning') as aantal_woningen
    ,		count(*) filter (
    			where feitelijkgebruikomschrijving = 'woning'
    			and (woonfunctie like '%onzelfst%' or gezondheidsfunctie like '%onzelfst%')
    		) as aantal_onzelfst_eenheden
    from 	verblijfsobject_selection
    group by 1
)
-- afleiden straatzijde van het pand
, pand_straatzijde as (
         select distinct on (pand_id)
         		pand_id
         , 		openbare_ruimte_id
         from (
              select vs.pand_id,
                    nag.ligtaanopenbareruimteid  as openbare_ruimte_id,
                    count(*) as aantal_opr_item
              from 	verblijfsobject_selection vs
              join 	bag_nummeraanduiding nag
                   	on vs.vot_id = nag.adresseertverblijfsobjectid
              where nag.typeadres = 'Hoofdadres'
              group by 1,2
         ) straatzijde
         order by pand_id, aantal_opr_item desc, openbare_ruimte_id
)
select pnd.identificatie  as id,
       pnd.identificatie  as pand_id,
       pnd.geometrie,
       atl.aantal_vot,
       atl.aantal_woningen,
       atl.aantal_onzelfst_eenheden,
       pse.openbare_ruimte_id,
       pnd.ligtinbouwblokid as bouwblok_id,
       pnd.liggingomschrijving  as ligging,
       pnd.typewoonobject  as type_woonobject,
       pnd.statusomschrijving  as status,
       pnd.begingeldigheid  as begin_geldigheid,
       pnd.eindgeldigheid  as einde_geldigheid
from bag_pand pnd
left join aantallen atl
     on pnd.identificatie  = atl.pand_id
left join pand_straatzijde pse
     on pnd.identificatie  = pse.pand_id
order by 1
;
drop index if exists bag_pand_afleiding_objecten_gidx;
create index bag_pand_afleiding_objecten_gidx on bag_pand_afleiding_objecten using GIST (geometrie);