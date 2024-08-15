#pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.0/en_ner_bc5cdr_md-0.5.0.tar.gz
#https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_ner_bc5cdr_md-0.5.1.tar.gz
#up to 0.5.4

# instead of:
#!python -m spacy download en_ner_bc5cdr_md   #12MB mem


import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
settings = load_app_settings()

inputdir=settings['directories']['input_dir']
targetdir=settings['directories']['input_dir']
ddir=settings['directories']['def_dir']

df_notes=pd.read_csv(inputdir+'NOTEEVENTS.csv')

import spacy;
import medspacy
# Option 1: Load default
nlp = medspacy.load()

sectionizer = nlp.add_pipe("medspacy_sectionizer")

nlp.pipe_names

import re
def preprocess(x):
    y=re.sub('\[(.*?)\]','',x) #remove de-identified brackets
    y=re.sub('[0-9]+\.','',y) #remove 1.2. since the segmenter segments based on this
    y=re.sub('dr\.','doctor',y)
    y=re.sub('m\.d\.','md',y)
    y=re.sub('admission date:','',y)
    y=re.sub('Admission Date:','',y)
    y=re.sub('discharge date:','',y)
    y=re.sub('Discharge Date:','',y)
    y=re.sub('Date of Birth:','',y)
    y=re.sub('date of birth:','',y)
    y=re.sub('--|__|==','',y)
    y = y.strip()
    return y

# Start of loop

df_notes.shape[0]



for i in range(df_notes.shape[0]):
  CATEGORY='Discharge summary'
  #HADM_ID=159647
  HADM_ID=df_notes.iloc[i]['HADM_ID']
  SUBJECT_ID=df_notes.iloc[i]['SUBJECT_ID']

  #CHARTDATE='2146/07/28'
  CHARTDATE=df_notes.iloc[i]['CHARTDATE']
  text=df_notes.iloc[i]['TEXT']
  print("Processing note %f" %i)
  doc = nlp(text)
  ls_notes=[]
  for j in range(len(doc._.sections)):
            mystr=str(doc._.section_spans[j])
            mystr_Without_line=preprocess(mystr)
            ls_notes.append([HADM_ID,SUBJECT_ID,CHARTDATE,CATEGORY,mystr_Without_line,doc._.section_categories[j]])

  df2=pd.DataFrame(ls_notes,columns=["HADM_ID",'SUBJECT_ID','CHARTDATE','CATEGORY',"body_span_Without_line",'category'])
  if i==0:
    df_main=df2
  else:
    df_main = pd.concat([df_main, df2], ignore_index=True)

df_main.tail()

df_main['HADM_ID'] = df_main['HADM_ID'].fillna(-1).astype(int)  # Replace NaN with -1

#df_main[df_main['HADM_ID']==-1]

#len(doc._.sections)
#doc._.section_bodies[3]
#doc._.section_titles[3]
#doc._.section_categories[3]
#doc._.section_spans[3]

"""Step 2 : Finding CUI from each section text"""

#!python -m spacy download en_core_web_sm
#!python -m spacy download en_ner_bc5cdr_md   #12MB mem

CATEGORY='Discharge summary'
#HADM_ID=159647
#CHARTDATE='2146/07/28'

import re

import scispacy
import spacy

from negspacy.negation import Negex
from negspacy.termsets import termset
from scispacy.linking import EntityLinker
import pandas as pd

#nlp = spacy.load("en_core_web_sm")
nlp = spacy.load("en_ner_bc5cdr_md")

#
ts = termset("en_clinical")
nlp.add_pipe("negex", config={"neg_termset": ts.get_patterns()})
nlp.add_pipe("scispacy_linker", config={"linker_name": "umls", "max_entities_per_mention": 1})

linker = nlp.get_pipe("scispacy_linker")
nlp.pipe_names

#nlp.pipe_names

d = {'HADM_ID':HADM_ID, 'CHARTDATE': CHARTDATE,'body_span_Without_line':text, 'category':'history_of_present_illness'}

df = pd.DataFrame(data=d,index=[0])

df_main['HADM_ID'] = df_main['HADM_ID'].astype(int)

df=df_main

df.tail()

list_Cui=[]
list_Exception=[]

for i in range(len(df)):
            print('Processing note %f' %i)
            #CATEGORY='Discharge summary
            text= str(df.iloc[i]['body_span_Without_line'])
            HADM_ID	=df.iloc[i]['HADM_ID']
            SUBJECT_ID=df.iloc[i]['SUBJECT_ID']

            CHARTDATE	=df.iloc[i]['CHARTDATE']

            category_Inner=	df.iloc[i]['category']

            doc = nlp(text)

            for entity in doc.ents:

                if(len(entity._.kb_ents)>0):
                    first_cuid = entity._.kb_ents[0][0]
                    kb_entry = linker.kb.cui_to_entity[first_cuid]
                    list_Cui.append([HADM_ID,SUBJECT_ID,CHARTDATE,category_Inner,entity._.negex,entity.text,
                                     first_cuid, kb_entry.canonical_name,entity.label_  ])
                else:
                    list_Exception.append([HADM_ID,SUBJECT_ID,CHARTDATE,category_Inner,entity.text])
                    continue



df_cui=pd.DataFrame(list_Cui,columns=['HADM_ID','SUBJECT_ID','CHARTDATE','category_Inner','negex','entity_text',
                                      'first_cuid', 'canonical_name','label'
                                          ])
#df_cui

df_cui.to_csv(targetdir+'cui.csv')

df_cui['label'].unique()

df_cui['category_Inner'].unique()

