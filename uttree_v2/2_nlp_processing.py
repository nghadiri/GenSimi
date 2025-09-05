"""
UTTree V2 - Integrated NLP and Quadruple Processing Module

Streamlined NLP processing that combines clinical note sectioning, NER, UMLS mapping,
and direct quadruple generation without intermediate file storage.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Key Improvements in V2:
- Combined NLP processing pipeline
- In-memory quadruple generation
- Direct integration with structured data
- Optimized for modern embedding workflow

Processing Steps:
1. Clinical Note Sectioning (MedspaCy)
2. Named Entity Recognition (ScispaCy BC5CDR)
3. UMLS Concept Mapping
4. Temporal Event Classification
5. Quadruple Generation and Integration
"""

import pandas as pd
import numpy as np
import spacy
import medspacy
import scispacy
from negspacy.negation import Negex
from negspacy.termsets import termset
from scispacy.linking import EntityLinker
import re
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import os
import sys

# Add parent directory to path for config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.config import load_app_settings

class UTTreeNLPProcessor:
    def __init__(self):
        self.settings = load_app_settings()
        self.input_dir = self.settings['directories']['input_dir']
        
        # Initialize NLP models
        self._setup_nlp_pipeline()
        
    def _setup_nlp_pipeline(self):
        """Initialize the NLP processing pipeline."""
        print("Initializing NLP pipeline...")
        
        # MedspaCy for sectioning
        self.sectioning_nlp = medspacy.load()
        self.sectioning_nlp.add_pipe("medspacy_sectionizer")
        
        # ScispaCy for NER and UMLS linking
        self.ner_nlp = spacy.load("en_ner_bc5cdr_md")
        
        # Add negation detection
        ts = termset("en_clinical")
        self.ner_nlp.add_pipe("negex", config={"neg_termset": ts.get_patterns()})
        
        # Add UMLS entity linker
        self.ner_nlp.add_pipe("scispacy_linker", config={"linker_name": "umls", "max_entities_per_mention": 1})
        self.linker = self.ner_nlp.get_pipe("scispacy_linker")
        
        print("NLP pipeline initialized successfully!")
        
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess clinical text.
        
        Args:
            text: Raw clinical text
            
        Returns:
            Preprocessed text
        """
        # Remove de-identified brackets and clean text
        text = re.sub(r'\[(.*?)\]', '', text)  # Remove de-identified brackets
        text = re.sub(r'[0-9]+\.', '', text)  # Remove numbered lists
        text = re.sub(r'dr\.', 'doctor', text, flags=re.IGNORECASE)
        text = re.sub(r'm\.d\.', 'md', text, flags=re.IGNORECASE)
        text = re.sub(r'admission date:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'discharge date:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'date of birth:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'--|__|==', '', text)
        
        return text.strip()
    
    def process_clinical_notes(self, selected_patients: List[int]) -> pd.DataFrame:
        """
        Process clinical notes for selected patients with integrated NLP pipeline.
        
        Args:
            selected_patients: List of patient IDs to process
            
        Returns:
            DataFrame with processed clinical concepts
        """
        print("Processing clinical notes...")
        
        # Load notes for selected patients
        notes_df = pd.read_csv(os.path.join(self.input_dir, 'NOTEEVENTS.csv'))
        notes_df = notes_df[notes_df['SUBJECT_ID'].isin(selected_patients)]
        
        all_concepts = []
        
        for idx, row in notes_df.iterrows():
            if idx % 10 == 0:
                print(f"Processing note {idx+1}/{len(notes_df)}")
                
            try:
                # Extract basic info
                hadm_id = row['HADM_ID']
                subject_id = row['SUBJECT_ID']
                chart_date = row['CHARTDATE']
                text = str(row['TEXT'])
                
                # Handle missing HADM_ID
                if pd.isna(hadm_id):
                    hadm_id = -1
                else:
                    hadm_id = int(hadm_id)
                
                # Step 1: Section the text
                sections = self._section_text(text, hadm_id, subject_id, chart_date)
                
                # Step 2: Process each section for concepts
                for section in sections:
                    concepts = self._extract_concepts_from_section(section)
                    all_concepts.extend(concepts)
                    
            except Exception as e:
                print(f"Error processing note {idx}: {e}")
                continue
                
        print(f"Extracted {len(all_concepts)} clinical concepts")
        return pd.DataFrame(all_concepts)
    
    def _section_text(self, text: str, hadm_id: int, subject_id: int, chart_date: str) -> List[Dict]:
        """
        Section clinical text and return structured sections.
        
        Args:
            text: Clinical text to section
            hadm_id: Hospital admission ID
            subject_id: Patient subject ID
            chart_date: Chart date
            
        Returns:
            List of section dictionaries
        """
        # Preprocess text
        cleaned_text = self.preprocess_text(text)
        
        # Process with sectioning NLP
        doc = self.sectioning_nlp(cleaned_text)
        
        sections = []
        for i, section_span in enumerate(doc._.section_spans):
            section_text = self.preprocess_text(str(section_span))
            if section_text:  # Only include non-empty sections
                sections.append({
                    'hadm_id': hadm_id,
                    'subject_id': subject_id,
                    'chart_date': chart_date,
                    'section_text': section_text,
                    'section_category': doc._.section_categories[i] if i < len(doc._.section_categories) else 'other'
                })
                
        return sections
    
    def _extract_concepts_from_section(self, section: Dict) -> List[Dict]:
        """
        Extract medical concepts from a text section.
        
        Args:
            section: Section dictionary with text and metadata
            
        Returns:
            List of concept dictionaries
        """
        concepts = []
        
        # Process section text with NER pipeline
        doc = self.ner_nlp(section['section_text'])
        
        for entity in doc.ents:
            # Only process disease entities with UMLS mappings
            if entity.label_ == 'DISEASE' and len(entity._.kb_ents) > 0:
                try:
                    # Get UMLS concept
                    first_cuid = entity._.kb_ents[0][0]
                    kb_entry = self.linker.kb.cui_to_entity[first_cuid]
                    
                    concepts.append({
                        'hadm_id': section['hadm_id'],
                        'subject_id': section['subject_id'],
                        'chart_date': section['chart_date'],
                        'section_category': section['section_category'],
                        'negation': entity._.negex,
                        'entity_text': entity.text,
                        'cui': first_cuid,
                        'canonical_name': kb_entry.canonical_name,
                        'label': entity.label_
                    })
                except Exception:
                    continue
                    
        return concepts
    
    def generate_unstructured_quadruples(self, concepts_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert extracted concepts to temporal quadruple format.
        
        Args:
            concepts_df: DataFrame with extracted medical concepts
            
        Returns:
            DataFrame with unstructured data quadruples
        """
        print("Generating unstructured quadruples...")
        
        quadruples = []
        
        # Group by hospital admission
        for hadm_id, group in concepts_df.groupby('hadm_id'):
            # Sort by chart date
            group = group.sort_values('chart_date')
            
            # Create time sequence mapping
            unique_dates = group['chart_date'].unique()
            date_to_time = {date: idx + 1 for idx, date in enumerate(unique_dates)}
            
            # Process each concept
            for _, row in group.iterrows():
                # Determine temporal event type based on section
                if row['section_category'] == 'past_medical_history':
                    temporal_type = 'Retro'
                else:
                    temporal_type = 'NewFinding'
                
                quadruples.append({
                    'subject_id': row['subject_id'],
                    'hadm_id': hadm_id,
                    'timestamp': row['chart_date'],
                    'time_window': date_to_time[row['chart_date']],
                    'temporal_event_type': temporal_type,
                    'event': 'DiseaseDisorderMention',
                    'value': row['canonical_name']
                })
                
        return pd.DataFrame(quadruples)
    
    def integrate_structured_unstructured(self, structured_data: pd.DataFrame, 
                                        unstructured_data: pd.DataFrame) -> Dict[int, pd.DataFrame]:
        """
        Integrate structured and unstructured quadruples by admission.
        
        Args:
            structured_data: Structured data quadruples
            unstructured_data: Unstructured data quadruples
            
        Returns:
            Dictionary mapping hadm_id to integrated DataFrame
        """
        print("Integrating structured and unstructured data...")
        
        integrated_data = {}
        
        # Get all unique admission IDs
        all_hadm_ids = set(structured_data['hadm_id'].unique()) | set(unstructured_data['hadm_id'].unique())
        
        for hadm_id in all_hadm_ids:
            # Get data for this admission
            struct_subset = structured_data[structured_data['hadm_id'] == hadm_id].copy()
            unstruct_subset = unstructured_data[unstructured_data['hadm_id'] == hadm_id].copy()
            
            # Add time_window column to structured data if missing
            if 'time_window' not in struct_subset.columns and len(struct_subset) > 0:
                # Create time windows based on unique timestamps
                unique_dates = struct_subset['timestamp'].unique()
                date_to_time = {date: idx + 1 for idx, date in enumerate(sorted(unique_dates))}
                struct_subset['time_window'] = struct_subset['timestamp'].map(date_to_time)
            
            # Combine data
            if len(struct_subset) > 0 and len(unstruct_subset) > 0:
                combined = pd.concat([struct_subset, unstruct_subset], ignore_index=True)
            elif len(struct_subset) > 0:
                combined = struct_subset
            elif len(unstruct_subset) > 0:
                combined = unstruct_subset
            else:
                continue
                
            # Sort by time window and timestamp
            combined = combined.sort_values(['time_window', 'timestamp'])
            integrated_data[hadm_id] = combined
            
        print(f"Integrated data for {len(integrated_data)} admissions")
        return integrated_data
    
    def process_all(self, selected_patients: List[int], structured_data: pd.DataFrame) -> Dict[int, pd.DataFrame]:
        """
        Execute complete NLP processing pipeline.
        
        Args:
            selected_patients: List of patient IDs to process
            structured_data: Structured data from preprocessing
            
        Returns:
            Dictionary of integrated quadruple data by admission
        """
        print("Starting UTTree V2 NLP processing...")
        
        # Process clinical notes
        concepts_df = self.process_clinical_notes(selected_patients)
        
        # Generate unstructured quadruples
        unstructured_data = self.generate_unstructured_quadruples(concepts_df)
        
        # Integrate with structured data
        integrated_data = self.integrate_structured_unstructured(structured_data, unstructured_data)
        
        print("NLP processing completed successfully!")
        return integrated_data


def main():
    """Main execution function for testing."""
    # This would normally receive data from the preprocessing module
    from data_preprocessing import UTTreeDataPreprocessor
    
    # Initialize processors
    preprocessor = UTTreeDataPreprocessor()
    nlp_processor = UTTreeNLPProcessor()
    
    # Get preprocessed data
    selected_patients, structured_data = preprocessor.process_all(min_notes=10, sample_size=5)
    
    # Process with NLP
    integrated_data = nlp_processor.process_all(selected_patients, structured_data)
    
    print(f"\nProcessing Summary:")
    print(f"Processed admissions: {len(integrated_data)}")
    
    # Display sample integrated data
    if integrated_data:
        sample_hadm_id = list(integrated_data.keys())[0]
        print(f"\nSample integrated data for HADM_ID {sample_hadm_id}:")
        print(integrated_data[sample_hadm_id].head())


if __name__ == "__main__":
    main()