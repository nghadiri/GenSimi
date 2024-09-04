select hadm_id,chartdate,charttime,text
from mimiciii.noteevents mn
--where hadm_id in (192314,156372,127789)
--	where hadm_id in (129767,196486,103541)
	where hadm_id in (139289,169684,186273)
order by text,hadm_id,chartdate,charttime
