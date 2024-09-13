CREATE OR REPLACE VIEW mimiciii.sep_pw_patients AS (
WITH sepsis_patients AS (
  SELECT DISTINCT subject_id, hadm_id
  FROM mimiciii.DIAGNOSES_ICD
  WHERE icd9_code IN (
    '99591', -- Sepsis
    '99592', -- Severe sepsis
    '78552'  -- Septic shock
  )
)
SELECT 
  sp.subject_id,
  sp.hadm_id,
  p.gender,
  p.dob,
  a.admittime AS sepsis_admission_time,
  a.dischtime AS discharge_time
FROM sepsis_patients sp
JOIN mimiciii.PATIENTS p ON sp.subject_id = p.subject_id
JOIN mimiciii.ADMISSIONS a ON sp.hadm_id = a.hadm_id
)

SELECT * 
INTO mimiciii.list_subject_id_sepsis_pw
from mimiciii.sep_pw_patients



CREATE OR REPLACE VIEW mimiciii.sepsis_care_events AS (
WITH lab_events AS (
  SELECT 
    le.subject_id,
    le.hadm_id,
    le.charttime,
    CASE
      WHEN le.itemid IN (51006, 50983) THEN 'Lactate'
      WHEN le.itemid IN (51256, 51265) THEN 'CBC'
      WHEN le.itemid IN (51288, 51289, 51290) THEN 'BloodCulture'
    END AS event_type
  FROM mimiciii.LABEVENTS le
  JOIN mimiciii.list_subject_id_sepsis_pw sp ON le.subject_id = sp.subject_id AND le.hadm_id = sp.hadm_id
  WHERE le.itemid IN (
    51006, 50983, -- Lactate
    51256, 51265, -- CBC
    51288, 51289, 51290 -- Blood Culture
  )
),
medication_events AS (
  SELECT 
    subject_id,
    hadm_id,
    startdate AS charttime,
    CASE
      WHEN LOWER(drug) LIKE '%saline%' OR LOWER(drug) LIKE '%lactated ringer%' THEN 'IVFluids'
      WHEN LOWER(drug) IN ('norepinephrine', 'epinephrine', 'vasopressin', 'dopamine') THEN 'Vasopressors'
      WHEN LOWER(drug) LIKE '%antibiotic%' THEN 'BroadSpectrumAntibiotics'
    END AS event_type
  FROM mimiciii.PRESCRIPTIONS
  WHERE subject_id IN (SELECT subject_id FROM mimiciii.list_subject_id_sepsis_pw)
)
SELECT 
  subject_id,
  hadm_id,
  charttime,
  event_type
FROM lab_events
UNION ALL
SELECT 
  subject_id,
  hadm_id,
  charttime,
  event_type
FROM medication_events
ORDER BY subject_id, hadm_id, charttime
)

SELECT * 
INTO mimiciii.list_sepsis_care_events
from mimiciii.sepsis_care_events



CREATE OR REPLACE VIEW mimiciii.sepsis_onset_time AS (
WITH sepsis_criteria AS (
  SELECT 
    ce.subject_id,
    ce.hadm_id,
    ce.charttime,
    CASE
      WHEN ce.itemid IN (220045, 220050, 220179, 220180) AND ce.valuenum > 100 THEN 1 -- Heart rate > 100
      WHEN ce.itemid IN (220179, 220180) AND ce.valuenum < 90 THEN 1 -- Systolic BP < 90
      WHEN ce.itemid IN (223762, 220235) AND ce.valuenum > 20 THEN 1 -- Respiratory rate > 20
      WHEN ce.itemid IN (223761, 220210) AND ce.valuenum > 38.3 THEN 1 -- Temperature > 38.3°C
      ELSE 0
    END AS criteria_met
  FROM mimiciii.CHARTEVENTS ce
  JOIN mimiciii.list_subject_id_sepsis_pw sp ON ce.subject_id = sp.subject_id AND ce.hadm_id = sp.hadm_id
  WHERE ce.itemid IN (
    220045, 220050, 220179, 220180, -- Heart rate and BP
    223762, 220235, -- Respiratory rate
    223761, 220210  -- Temperature
  )
)
SELECT 
  subject_id,
  hadm_id,
  MIN(charttime) AS sepsis_onset_time
FROM (
  SELECT subject_id, hadm_id, charttime
  FROM sepsis_criteria
  WHERE criteria_met = 1
  GROUP BY subject_id, hadm_id, charttime
  HAVING SUM(criteria_met) >= 2
  UNION ALL
  SELECT sp.subject_id, sp.hadm_id, admittime AS charttime
  FROM mimiciii.list_subject_id_sepsis_pw sp
  JOIN mimiciii.ADMISSIONS a ON sp.subject_id = a.subject_id AND sp.hadm_id = a.hadm_id
)
GROUP BY subject_id, hadm_id
)

SELECT * 
INTO mimiciii.list_sepsis_onset_time
from mimiciii.sepsis_onset_time
