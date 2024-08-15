CREATE OR REPLACE VIEW mimiciii.glc_patients AS (
 WITH glaucoma_patients AS (
    -- Patients with glaucoma diagnoses
    SELECT DISTINCT d.subject_id
    FROM mimiciii.diagnoses_icd d
    WHERE d.icd9_code LIKE '365%' -- Glaucoma codes

    INTERSECT

	 -- Patients with glaucoma-related terms in their notes
	-- Takes about 6 minutes, 1539 patients
    SELECT DISTINCT subject_id
    FROM mimiciii.noteevents
    WHERE LOWER(text) LIKE '%glaucoma%'
       OR LOWER(text) LIKE '%intraocular pressure%'
       OR LOWER(text) LIKE '%optic nerve damage%'
       OR LOWER(text) LIKE '%visual field loss%'
       OR LOWER(text) LIKE '%angle closure%'
       OR LOWER(text) LIKE '%open-angle%'
       -- Add more relevant terms
     )	   

	SELECT DISTINCT p.subject_id, p.gender, p.dob, p.dod
	FROM mimiciii.patients p
	INNER JOIN glaucoma_patients gp ON p.subject_id = gp.subject_id
)


/*
    -- Patients with glaucoma-related procedures
	-- Zero
    SELECT DISTINCT p.subject_id
    FROM mimiciii.procedures_icd p
    WHERE p.icd9_code IN (
        '12.64', -- Trabeculectomy ab externo
        '12.65', -- Other fistulizing procedure
        '12.66', -- Revision of fistulization procedure
        '12.67', -- Insertion of aqueous drainage device
        '12.71', -- Cyclocryotherapy
        '12.72', -- Cyclophotocoagulation
        '12.73'  -- Cyclodialysis
        -- Add more glaucoma-related procedure codes as needed
    )

	UNION
	
	-- Zero
	SELECT DISTINCT p.subject_id
		FROM mimiciii.procedures_icd p
		WHERE p.icd9_code IN (
		    '12.64', '12.65', '12.66', '12.67', '12.71', '12.72', '12.73',
		    '012.64', '012.65', '012.66', '012.67', '012.71', '012.72', '012.73'
		)
		OR p.icd9_code LIKE '12.6%'
		OR p.icd9_code LIKE '12.7%'
		OR p.icd9_code LIKE '012.6%'
		OR p.icd9_code LIKE '012.7%'

    UNION

    -- Patients with relevant lab tests or measurements
    SELECT DISTINCT l.subject_id
    FROM mimiciii.labevents l
    WHERE l.itemid IN (
        -- Add relevant item IDs here
        -- Note: MIMIC-III might not have specific glaucoma tests,
        -- but you could include related eye exams if available
    )

    UNION

  */ 






SELECT * 
INTO mimiciii.list_subject_id_glc_diag_icd_notes
from mimiciii.glc_patients
  
select subject_id from mimiciii.list_subject_id_glc_diag_icd_notes

-- Selected GLC patients by gender
SELECT p.gender,count(p.subject_id)
FROM mimiciii.patients p
INNER JOIN mimiciii.list_subject_id_glc_diag_icd_notes glp ON p.subject_id = glp.subject_id
GROUP BY p.gender;


-- Total number of note events for select GLC patients
select count(mn.row_id)
from mimiciii.noteevents mn
where subject_id in (
	SELECT p.subject_id
	FROM mimiciii.patients p
	INNER JOIN mimiciii.list_subject_id_glc_diag_icd_notes glc ON p.subject_id = glc.subject_id
)

-- Number of note events for each selected GLC patient
select subject_id, count(mn.row_id)
from mimiciii.noteevents mn
where subject_id in (
	SELECT p.subject_id
	FROM mimiciii.patients p
	INNER JOIN mimiciii.list_subject_id_glc_diag_icd_notes glc ON p.subject_id = glc.subject_id
)
group by subject_id
order by count(mn.row_id) desc