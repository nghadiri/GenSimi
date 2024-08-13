import pandas as pd
import os

# Define paths
main_folder = "F:\C\Data\MIMIC-III\csv"
selected_folder = "F:\C\Data\MIMIC-III\Selected"
subject_file = os.path.join(selected_folder, "subject-sel.csv")

# Read selected subject IDs
selected_subjects = pd.read_csv(subject_file)['SUBJECT_ID'].tolist()

# List of files to process
files_to_process = [
    "PATIENTS.csv",
    "ADMISSIONS.csv",
    "LABEVENTS.csv",
    "NOTEEVENTS.csv",
    "PRESCRIPTIONS.csv",
    "PROCEDURES_ICD.csv",
    "DIAGNOSES_ICD.csv"
]

# Process each file
for file in files_to_process:
    input_path = os.path.join(main_folder, file)
    output_path = os.path.join(selected_folder, f"{file}")
    
    print(f"Processing {file}...")
    
    # Read the CSV file in chunks to handle large files
    chunk_size = 1000000  # Adjust this based on your system's memory
    chunks = []
    
    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        # Filter rows based on SUBJECT_ID
        filtered_chunk = chunk[chunk['SUBJECT_ID'].isin(selected_subjects)]
        chunks.append(filtered_chunk)
    
    # Combine all filtered chunks
    filtered_df = pd.concat(chunks, ignore_index=True)
    
    # Save the filtered data to a new CSV file
    filtered_df.to_csv(output_path, index=False)
    print(f"Saved selected records to {output_path}")

print("Processing complete!")