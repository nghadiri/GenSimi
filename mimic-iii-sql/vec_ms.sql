CREATE TABLE mimiciii.vectors_ms 
(
hadm_id INTEGER PRIMARY KEY,
embedding vector(200)
)

SELECT * FROM mimiciii.vectors_ms
ORDER BY hadm_id ASC LIMIT 100


select v.hadm_id, subject_id
from mimiciii.admissions a
inner join mimiciii.vectors_ms v
on (a.hadm_id=v.hadm_id)
order by hadm_id

select subject_id, max(v.hadm_id)
from mimiciii.admissions a
inner join mimiciii.vectors_ms v
on (a.hadm_id=v.hadm_id)
group by subject_id
order by subject_id