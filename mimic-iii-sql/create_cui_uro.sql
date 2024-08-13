CREATE TABLE IF NOT EXISTS mimiciii.sel_cui_uro (
    R INTEGER,
	HADM_ID INTEGER,
    SUBJECT_ID INTEGER,
    CHARTDATE DATE,
    category_Inner VARCHAR(255),
    negex BOOLEAN,
    entity_text TEXT,
    first_cuid VARCHAR(50),
    canonical_name TEXT,
    "label" VARCHAR(50)
);

COPY mimiciii.sel_cui_uro (R,HADM_ID, SUBJECT_ID, CHARTDATE, category_Inner, negex, entity_text, first_cuid, canonical_name, "label")
FROM 'C:\C\MEGA\Data.my\Input\Selected-ms\cui.csv' 
WITH CSV HEADER;

select distinct category_inner
from mimiciii.sel_cui_uro


select distinct entity_text
from mimiciii.sel_cui_uro
WHERE category_inner='chief_complaint'
order by entity_text

select first_cuid, entity_text 
from mimiciii.sel_cui_uro
WHERE category_inner='chief_complaint' AND entity_text like '%ne%' 
order by first_cuid

-- "C0013404"
-- "C0020295"

