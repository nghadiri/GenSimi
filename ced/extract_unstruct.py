import pandas as pd
import spacy
import medspacy
from scispacy.linking import EntityLinker
from negspacy.negation import Negex
from negspacy.termsets import termset
import re

def load_ehr_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def preprocess(text):
    text = re.sub('\[(.*?)\]', '', text)  # remove de-identified brackets
    text = re.sub('[0-9]+\.', '', text)  # remove 1.2. since the segmenter segments based on this
    text = re.sub('dr\.', 'doctor', text)
    text = re.sub('m\.d\.', 'md', text)
    text = re.sub('admission date:', '', text)
    text = re.sub('Admission Date:', '', text)
    text = re.sub('discharge date:', '', text)
    text = re.sub('Discharge Date:', '', text)
    text = re.sub('Date of Birth:', '', text)
    text = re.sub('date of birth:', '', text)
    text = re.sub('--|__|==', '', text)
    return text.strip()

# Load spaCy model and add necessary pipes
nlp = spacy.load("en_ner_bc5cdr_md")
nlp.add_pipe("medspacy_sectionizer")
ts = termset("en_clinical")
nlp.add_pipe("negex", config={"neg_termset": ts.get_patterns()})
nlp.add_pipe("scispacy_linker", config={"linker_name": "umls", "max_entities_per_mention": 1})

linker = nlp.get_pipe("scispacy_linker")

def extract_sections_and_concepts(text):
    doc = nlp(text)
    sections = []
    concepts = []

    for section in doc._.sections:
        section_text = preprocess(str(section.span))
        sections.append({
            'category': section.category,
            'text': section_text
        })

        section_doc = nlp(section_text)
        for entity in section_doc.ents:
            if len(entity._.kb_ents) > 0:
                first_cuid = entity._.kb_ents[0][0]
                kb_entry = linker.kb.cui_to_entity[first_cuid]
                concepts.append({
                    'category': section.category,
                    'negex': entity._.negex,
                    'entity_text': entity.text,
                    'first_cuid': first_cuid,
                    'canonical_name': kb_entry.canonical_name,
                    'label': entity.label_
                })

    return sections, concepts

def main():
    file_path = 'F:\C\Data\Hm2\\new1.txt'  # Replace with your file path
    ehr_content = load_ehr_file(file_path)

    # Extract patient info (you might need to adjust these regex patterns)
    subject_id = re.search(r'Age:\s*(\d+)', ehr_content).group(1)
    hadm_id = '1'  # Assuming one admission per file, you might need to extract this differently
    chartdate = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', ehr_content).group(1)

    sections, concepts = extract_sections_and_concepts(ehr_content)

    # Create DataFrames
    df_sections = pd.DataFrame(sections)
    df_sections['SUBJECT_ID'] = subject_id
    df_sections['HADM_ID'] = hadm_id
    df_sections['CHARTDATE'] = chartdate

    df_concepts = pd.DataFrame(concepts)
    df_concepts['SUBJECT_ID'] = subject_id
    df_concepts['HADM_ID'] = hadm_id
    df_concepts['CHARTDATE'] = chartdate

    # Save results
    df_sections.to_csv('F:\C\Data\Hm2\Output\ehr_sections.csv', index=False)
    df_concepts.to_csv('F:\C\Data\Hm2\Output\ehr_concepts.csv', index=False)

    print(f"Processed EHR for Subject ID: {subject_id}")
    print(f"Number of sections extracted: {len(sections)}")
    print(f"Number of concepts extracted: {len(concepts)}")

if __name__ == "__main__":
    main()