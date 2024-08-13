-- ALTER TABLE public.procedures_icd SET SCHEMA mimiciii;


CREATE OR REPLACE VIEW mimiciii.urological_patients AS (
    -- Patients with urological diagnoses
 
	SELECT DISTINCT d.subject_id
    FROM mimiciii.diagnoses_icd d
    WHERE d.icd9_code BETWEEN '600' AND '608'


	intersect

	
    -- Patients with urological procedures
    SELECT DISTINCT p.subject_id
    FROM mimiciii.procedures_icd p
    WHERE p.icd9_code BETWEEN '55' AND '59'
)

SELECT * 
INTO mimiciii.list_subject_id_uro_diag_icd_proc_icd
from mimiciii.urological_patients

/*
    UNION

    -- Patients with relevant lab tests
    SELECT DISTINCT l.subject_id
    FROM mimiciii.labevents l
    WHERE l.itemid IN (
        -- Add relevant lab test item IDs here
        -- For example: PSA, urine analysis, etc.
        51081, -- PSA
        51094, -- PSA, Free
        50971  -- URINE APPEARANCE
        -- Add more relevant lab test IDs
    )
*/	
)

SELECT p.gender,count(p.subject_id)
FROM mimiciii.patients p
INNER JOIN mimiciii.urological_patients up ON p.subject_id = up.subject_id
GROUP BY p.gender;

select subject_id, count(mn.row_id)
from mimiciii.noteevents mn
where subject_id in (
	SELECT p.subject_id
	FROM mimiciii.patients p
	INNER JOIN mimiciii.urological_patients up ON p.subject_id = up.subject_id
)
group by subject_id
order by count(mn.row_id)

select subject_id, count(mn.row_id)
from mimiciii.labevents mn
where subject_id = 13852
group by subject_id