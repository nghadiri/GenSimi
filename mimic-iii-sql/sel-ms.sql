CREATE OR REPLACE VIEW mimiciii.ms_patients AS (
  
	-- Patients with MS diagnoses
    SELECT DISTINCT d.subject_id
    FROM mimiciii.diagnoses_icd d
    WHERE d.icd9_code IN ('340', '341.0', '341.1', '341.8', '341.9')

	intersect

    -- Patients with MS-related terms in their notes
    SELECT DISTINCT subject_id
	FROM mimiciii.noteevents
    WHERE LOWER(text) LIKE '%multiple sclerosis%'
       OR LOWER(text) LIKE '%ms diagnosis%'
       OR LOWER(text) LIKE '%demyelinating disease%'
       OR LOWER(text) LIKE '%optic neuritis%'
       -- Add more relevant terms
	
/*
    UNION

    -- Patients with MS-related procedures
    SELECT DISTINCT p.subject_id
    FROM mimiciii.procedures_icd p
    WHERE p.icd9_code IN ('92.01', '92.02', '92.03') -- MRI procedures

	  
    UNION

    -- Patients with relevant lab tests
    SELECT DISTINCT l.subject_id
    FROM mimiciii.labevents l
    WHERE l.itemid IN (
        -- Add relevant lab test item IDs here
        -- For example: CSF analysis, oligoclonal bands, etc.
        51516, -- Oligoclonal Bands
        50995, -- Glucose, CSF
        50912  -- WBC, CSF
        -- Add more relevant lab test IDs
    )

*/    
	/*
	intersect 
	
	 SELECT DISTINCT subject_id
     FROM mimiciii.prescriptions
     WHERE LOWER(drug) IN (
        'interferon beta-1a', 'interferon beta-1b', 'glatiramer acetate',
        'fingolimod', 'dimethyl fumarate', 'teriflunomide', 'natalizumab',
        'ocrelizumab', 'alemtuzumab', 'mitoxantrone'
        -- Add more MS medications as needed
    )
	*/
)

SELECT * 
INTO mimiciii.list_subject_id_ms_diag_icd_notes
from mimiciii.ms_patients
  
select * from mimiciii.list_subject_id_ms_diag_icd_notes

SELECT p.gender,count(p.subject_id)
FROM mimiciii.patients p
INNER JOIN mimiciii.list_subject_id_ms_diag_icd_notes msp ON p.subject_id = msp.subject_id
GROUP BY p.gender;

select count(mn.row_id)
from mimiciii.noteevents mn
where subject_id in (
	SELECT p.subject_id
	FROM mimiciii.patients p
	INNER JOIN mimiciii.list_subject_id_ms_diag_icd_notes mp ON p.subject_id = mp.subject_id
)

select subject_id, count(mn.row_id)
from mimiciii.noteevents mn
where subject_id in (
	SELECT p.subject_id
	FROM mimiciii.patients p
	INNER JOIN mimiciii.list_subject_id_ms_diag_icd_notes mp ON p.subject_id = mp.subject_id
)
group by subject_id
order by count(mn.row_id)