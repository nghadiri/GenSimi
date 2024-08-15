import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Tuple

def load_ehr_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()

def extract_medications(content: str) -> List[Dict]:
    medications = []
    med_section = re.search(r'MEDICATIONS(.*?)INTERVENTION & RESULTS', content, re.DOTALL)
    if med_section:
        med_lines = med_section.group(1).strip().split('\n')
        for line in med_lines:
            if '(' in line and ')' in line:
                parts = line.split(')')
                if len(parts) > 1:
                    name = parts[0].strip() + ')'
                    dosage = parts[1].strip()
                    medications.append({
                        'drug_name': name,
                        'dosage': dosage
                    })
    return medications

def extract_lab_results(content: str) -> List[Dict]:
    lab_results = []
    results_section = re.search(r'Results(.*?)Medical Imaging', content, re.DOTALL)
    if results_section:
        result_lines = results_section.group(1).strip().split('\n')
        current_date = None
        for line in result_lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    if len(parts[0]) == 10 and parts[0][2] == parts[0][5] == '/':  # Date check
                        current_date = datetime.strptime(parts[0], '%d/%m/%Y').date()
                    else:
                        lab_results.append({
                            'date': current_date,
                            'test': parts[0].strip(),
                            'value': parts[1].strip(),
                            'unit': parts[2].strip() if len(parts) > 2 else ''
                        })
    return lab_results

def create_dataframes(medications: List[Dict], lab_results: List[Dict]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    med_df = pd.DataFrame(medications)
    lab_df = pd.DataFrame(lab_results)
    
    # Add necessary columns to match the original format
    med_df['Subject_id'] = 1  # Assuming one subject per file
    med_df['HADM_ID'] = 1  # Assuming one hospital admission per file
    med_df['Timestame_id'] = datetime.now().date()  # Using current date as we don't have specific dates for medications
    med_df['TemporalEventType'] = 'RealTime'
    med_df['entity'] = 'Drug'
    med_df['value'] = med_df['drug_name'] + ' ' + med_df['dosage']
    
    lab_df['Subject_id'] = 1
    lab_df['HADM_ID'] = 1
    lab_df['TemporalEventType'] = 'RealTime'
    lab_df['entity'] = lab_df['test']
    lab_df['value'] = lab_df['value'] + ' ' + lab_df['unit']
    lab_df = lab_df.rename(columns={'date': 'Timestame_id'})
    
    return med_df[['Subject_id', 'HADM_ID', 'Timestame_id', 'TemporalEventType', 'entity', 'value']], \
           lab_df[['Subject_id', 'HADM_ID', 'Timestame_id', 'TemporalEventType', 'entity', 'value']]

def main():
    file_path = 'F:\C\Data\Hm2\\new1.txt'  # Replace with your file path
    ehr_content = load_ehr_file(file_path)
    
    medications = extract_medications(ehr_content)
    lab_results = extract_lab_results(ehr_content)
    
    med_df, lab_df = create_dataframes(medications, lab_results)
    
    # Merge results
    result = pd.concat([med_df, lab_df])
    
    # Save results
    result.to_csv('F:\C\Data\Hm2\Output\merged_drug_lab_ehr.csv', index=False)
    
    # Print statistics
    num_unique_subjects = result['Subject_id'].nunique()
    print(f"Number of unique subject ids: {num_unique_subjects}")

if __name__ == "__main__":
    main()