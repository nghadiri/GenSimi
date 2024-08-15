import pandas as pd
import spacy
import medspacy
import re
from negspacy.negation import Negex
from negspacy.termsets import termset
from scispacy.linking import EntityLinker
from tqdm import tqdm
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concurrent.futures import ProcessPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Load configuration settings."""
    # You can replace this with a proper config file reader if needed
    return {
        'input_dir': 'path/to/input/',
        'output_dir': 'path/to/output/',
        'batch_size': 1000,  # Process this many rows at a time
    }

def preprocess_text(text):
    """Preprocess the text."""
    replacements = {
        r'\[(.*?)\]': '',
        r'[0-9]+\.': '',
        r'dr\.': 'doctor',
        r'm\.d\.': 'md',
        r'admission date:': '',
        r'Admission Date:': '',
        r'discharge date:': '',
        r'Discharge Date:': '',
        r'Date of Birth:': '',
        r'date of birth:': '',
        r'--|__|==': '',
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    return text.strip()

def setup_nlp():
    """Set up the NLP pipeline."""
    nlp = medspacy.load()
    nlp.add_pipe("medspacy_sectionizer")
    
    nlp_ner = spacy.load("en_ner_bc5cdr_md")
    ts = termset("en_clinical")
    nlp_ner.add_pipe("negex", config={"neg_termset": ts.get_patterns()})
    nlp_ner.add_pipe("scispacy_linker", config={"linker_name": "umls", "max_entities_per_mention": 1})
    
    return nlp, nlp_ner

def process_note(note, nlp):
    """Process a single note."""
    doc = nlp(note['TEXT'])
    processed_sections = []
    for span, category in zip(doc._.section_spans, doc._.section_categories):
        processed_text = preprocess_text(str(span))
        processed_sections.append({
            'HADM_ID': note['HADM_ID'],
            'SUBJECT_ID': note['SUBJECT_ID'],
            'CHARTDATE': note['CHARTDATE'],
            'CATEGORY': note['CATEGORY'],
            'body_span_Without_line': processed_text,
            'category': category
        })
    return processed_sections

def extract_entities(section, nlp_ner):
    """Extract entities from a section."""
    doc = nlp_ner(section['body_span_Without_line'])
    entities = []
    for entity in doc.ents:
        if entity._.kb_ents:
            first_cuid = entity._.kb_ents[0][0]
            kb_entry = nlp_ner.get_pipe("scispacy_linker").kb.cui_to_entity[first_cuid]
            entities.append({
                'HADM_ID': section['HADM_ID'],
                'SUBJECT_ID': section['SUBJECT_ID'],
                'CHARTDATE': section['CHARTDATE'],
                'category_Inner': section['category'],
                'negex': entity._.negex,
                'entity_text': entity.text,
                'first_cuid': first_cuid,
                'canonical_name': kb_entry.canonical_name,
                'label': entity.label_
            })
    return entities

def process_batch(batch, nlp, nlp_ner):
    """Process a batch of notes."""
    sections = []
    for _, note in batch.iterrows():
        sections.extend(process_note(note, nlp))
    
    entities = []
    for section in sections:
        entities.extend(extract_entities(section, nlp_ner))
    
    return pd.DataFrame(entities)

def main():
    config = load_config()
    nlp, nlp_ner = setup_nlp()

    # Load data
    df_notes = pd.read_csv(os.path.join(config['input_dir'], 'NOTEEVENTS.csv'))
    logging.info(f"Loaded {len(df_notes)} notes.")

    # Process in batches
    all_entities = []
    with ProcessPoolExecutor() as executor:
        futures = []
        for i in range(0, len(df_notes), config['batch_size']):
            batch = df_notes.iloc[i:i+config['batch_size']]
            futures.append(executor.submit(process_batch, batch, nlp, nlp_ner))
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing batches"):
            all_entities.append(future.result())

    # Combine results
    df_cui = pd.concat(all_entities, ignore_index=True)
    
    # Save results
    output_path = os.path.join(config['output_dir'], 'cui.csv')
    df_cui.to_csv(output_path, index=False)
    logging.info(f"Results saved to {output_path}")

    # Print some statistics
    logging.info(f"Unique labels: {df_cui['label'].nunique()}")
    logging.info(f"Unique categories: {df_cui['category_Inner'].nunique()}")

if __name__ == "__main__":
    main()