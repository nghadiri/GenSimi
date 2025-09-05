# -*- coding: utf-8 -*-
"""
Patient Sampling Module - UTTree Data Preprocessing

This module implements patient sampling and filtering for the UTTree methodology.
It performs statistical analysis and creates filtered datasets based on clinical notes
and admission frequency criteria.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Key Functions:
1. Analyzes patient admission and clinical note distributions
2. Filters patients with minimum clinical note requirements (≥10 notes)
3. Creates random samples for model development and testing
4. Generates visualizations of data distributions

This sampling step ensures that selected patients have sufficient clinical documentation
for meaningful temporal tree construction and patient similarity assessment.

The module processes:
- ADMISSIONS.csv: Hospital admission records
- NOTEEVENTS.csv: Clinical notes and documentation
- LABEVENTS.csv: Laboratory test results
- PRESCRIPTIONS.csv: Medication data
- PATIENTS.csv: Patient demographics

Output: Filtered datasets containing patients with adequate clinical documentation
for downstream UTTree processing.
"""

import pandas as pd

#from google.colab import drive
#drive.mount('/content/gdrive')
#basedir = '/content/gdrive/My Drive/data/MIMIC3/'

basedir="C:\\Proj\\simi\\"
readdir = basedir+'Input\\MIMIC3\\samp1000\\'
mimicdir = basedir+'Input\\MIMIC3\\'
targetdir = basedir+"Output\\samp1000\\"

# Load admissions data
admissions_df = pd.read_csv(readdir+'ADMISSIONS.csv')

# Load notes data
notes_df = pd.read_csv(readdir+'NOTEEVENTS.csv')

# Number of admissions per patient
admissions_per_patient = admissions_df.groupby('SUBJECT_ID')['HADM_ID'].nunique()
min_admissions = admissions_per_patient.min()
max_admissions = admissions_per_patient.max()
mean_admissions = admissions_per_patient.mean()

print("Minimum admissions per patient:", min_admissions)
print("Maximum admissions per patient:", max_admissions)
print("Mean admissions per patient:", mean_admissions)

# Number of notes per patient
notes_per_patient = notes_df.groupby('SUBJECT_ID')['ROW_ID'].count()
min_notes = notes_per_patient.min()
max_notes = notes_per_patient.max()
mean_notes = notes_per_patient.mean()

print("Minimum notes per patient:", min_notes)
print("Maximum notes per patient:", max_notes)
print("Mean notes per patient:", mean_notes)

import seaborn as sns
import matplotlib.pyplot as plt
# Create boxplots
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
sns.boxplot(y=admissions_per_patient)
plt.title('Admissions per Patient')

plt.subplot(1, 2, 2)
sns.boxplot(y=notes_per_patient)
plt.title('Notes per Patient')

plt.tight_layout()
plt.show()

# Skip
# Count number of notes per patient
notes_count_per_patient = notes_df.groupby('SUBJECT_ID')['ROW_ID'].count()

# Filter patients with at least 10 clinical notes
patients_with_10_notes_or_more = notes_count_per_patient[notes_count_per_patient >= 10].index.tolist()

# Filter admissions data to include only patients with at least 10 clinical notes
filtered_admissions = admissions_df[admissions_df['SUBJECT_ID'].isin(patients_with_10_notes_or_more)]

# Write filtered admissions to CSV
filtered_admissions.to_csv(targetdir + 'filtered_admissions.csv', index=False)

# Filter notes data for the selected patients
filtered_notes = notes_df[notes_df['SUBJECT_ID'].isin(patients_with_10_notes_or_more)]

# Write filtered notes to CSV
filtered_notes.to_csv(targetdir + 'filtered_notes.csv', index=False)

# Count number of unique patients, admissions, and notes in original data
original_num_patients = admissions_df['SUBJECT_ID'].nunique()
original_num_admissions = admissions_df['HADM_ID'].nunique()
original_num_notes = notes_df['ROW_ID'].nunique()

print("Original Data:")
print("Number of patients:", original_num_patients)
print("Number of admissions:", original_num_admissions)
print("Number of notes:", original_num_notes)

filtered_num_patients = filtered_admissions['SUBJECT_ID'].nunique()
filtered_num_admissions = filtered_admissions['HADM_ID'].nunique()
filtered_num_notes = filtered_notes['ROW_ID'].nunique()

print("\nFiltered Data:")
print("Number of patients:", filtered_num_patients)
print("Number of admissions:", filtered_num_admissions)
print("Number of notes:", filtered_num_notes)

# Read filtered admissions data
r_admissions = pd.read_csv(readdir + 'ADMISSIONS.csv')

# Read filtered notes data
r_notes = pd.read_csv(readdir + 'NOTEEVENTS.csv')

# Select 1000 random patients from filtered dataset
random_sample_patients = r_admissions['SUBJECT_ID'].sample(n=10, random_state=42)

# Filter admissions data for the random sample of patients
sampled_admissions = r_admissions[r_admissions['SUBJECT_ID'].isin(random_sample_patients)]

# Filter notes data for the random sample of patients
sampled_notes = r_notes[r_notes['SUBJECT_ID'].isin(random_sample_patients)]

# Write sampled admissions to CSV
sampled_admissions.to_csv(targetdir + 'ADMISSIONS.csv', index=False)

# Write sampled notes to CSV
sampled_notes.to_csv(targetdir + 'NOTEEVENTS.csv', index=False)

# Count number of unique patients, admissions, and notes in sampled data
sampled_num_patients = sampled_admissions['SUBJECT_ID'].nunique()
sampled_num_admissions = sampled_admissions['HADM_ID'].nunique()
sampled_num_notes = sampled_notes['ROW_ID'].nunique()

# Print the counts
print("Sampled Data:")
print("Number of patients:", sampled_num_patients)
print("Number of admissions:", sampled_num_admissions)
print("Number of notes:", sampled_num_notes)

#readdir=basedir
r_labs = pd.read_csv(readdir + 'LABEVENTS.csv')
sampled_labs = r_labs[r_labs['SUBJECT_ID'].isin(random_sample_patients)]
sampled_labs.to_csv(targetdir + 'LABEVENTS.csv', index=False)

r_pre = pd.read_csv(readdir + 'PRESCRIPTIONS.csv')
sampled_pre = r_pre[r_pre['SUBJECT_ID'].isin(random_sample_patients)]
sampled_pre.to_csv(targetdir + 'PRESCRIPTIONS.csv', index=False)

r_pat = pd.read_csv(mimicdir + 'PATIENTS.csv')
sampled_pat = r_pat[r_pat['SUBJECT_ID'].isin(random_sample_patients)]
sampled_pat.to_csv(targetdir + 'PATIENTS.csv', index=False)