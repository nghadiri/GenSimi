prompt = """You are an intelligent clinical languge model.
Below is a snippet of patient's discharge summary and a following instruction from healthcare professional.
Write a response that appropriately completes the instruction.
The response should provide the accurate answer to the instruction, while being concise.

[Discharge Summary Begin]
{note}
[Discharge Summary End]

[Instruction Begin]
{question}
[Instruction End] 
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
tokenizer = AutoTokenizer.from_pretrained("starmpcc/Asclepius-Llama3-8B", use_fast=False)
model = AutoModelForCausalLM.from_pretrained("starmpcc/Asclepius-Llama3-8B")

note = "History of Present Illness: \
___ HCV cirrhosis c/b ascites, hiv on ART, h/o IVDU, COPD,  \
bioplar, PTSD, presented from OSH ED with worsening abd  \
distension over past week.  \
Pt reports self-discontinuing lasix and spirnolactone ___ weeks  \
ago, because she feels like they don't do anything and that  \
she doesn't want to put more chemicals in her. She does not \
follow Na-restricted diets. In the past week, she notes that she  \
has been having worsening abd distension and discomfort. She  \
denies ___ edema, or SOB, or orthopnea. She denies f/c/n/v, d/c,  \
dysuria. She had food poisoning a week ago from eating stale \
cake (n/v 20 min after food ingestion), which resolved the same  \
day. She denies other recent illness or sick contacts. She notes \
that she has been noticing gum bleeding while brushing her teeth \
in recent weeks. she denies easy bruising, melena, BRBPR, \
hemetesis, hemoptysis, or hematuria.  \
Because of her abd pain, she went to OSH ED and was transferred \
to ___ for further care. Per ED report, pt has brief period of \
confusion - she did not recall the ultrasound or bloodwork at \
osh. She denies recent drug use or alcohol use. She denies \
feeling confused, but reports that she is forgetful at times.  \
In the ED, initial vitals were 98.4 70 106/63 16 97%RA  \
Labs notable for ALT/AST/AP ___ ___: ___, \
Tbili1.6, WBC 5K, platelet 77, INR 1.6  \
Past Medical History: \
1. HCV Cirrhosis   \
2. No history of abnormal Pap smears.   \
3. She had calcification in her breast, which was removed  \
previously and per patient not, it was benign.  \
4. For HIV disease, she is being followed by Dr. ___ Dr.  \
___.  \
5. COPD   \
6. Past history of smoking.  \
7. She also had a skin lesion, which was biopsied and showed  \
skin cancer per patient report and is scheduled for a complete removal of the skin lesion in ___ of this year.  \
8. She also had another lesion in her forehead with purple  \
discoloration. It was biopsied to exclude the possibility of 's sarcoma, the results is pending.  \
9. A 15 mm hypoechoic lesion on her ultrasound on ___  \
and is being monitored by an MRI.  \
10. History of dysplasia of anus in ___.  \
11. Bipolar affective disorder, currently manic, mild, and PTSD. "
 

question = "What is the diagnosis?"

model_input = prompt.format(note=note, question=question)
input_ids = tokenizer(model_input, return_tensors="pt").input_ids
output = model.generate(input_ids)
print(tokenizer.decode(output[0]))
