import os
import pandas as pd
import time
import nltk
import sys
import psycopg2


from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
from string import digits

nltk.download('punkt')
nltk.download('punkt_tab')
# first the two, then get hadm-subject-sel-glc.csv from pg, then third
_train=False
_insert_db=True
_write_csv=False


# Load app settings (make sure this function and its dependencies are working)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.config import load_app_settings
settings = load_app_settings()

inputdir = settings['directories']['input_dir']
targetdir = settings['directories']['target_dir']

# Initialize an empty DataFrame to store the documents
sen = pd.DataFrame({'ID': [], 'doc': []})

# Directory containing the files
directory = os.path.join(inputdir, "proc", "merged")

# Read all xxxxxx-merged.txt files from the directory
dataframes = []
for filename in os.listdir(directory):
    if filename.endswith("-merged.txt"):
        admission_id = filename.split("-merged.txt")[0]
        with open(os.path.join(directory, filename), 'r') as file:
            document = file.read()
            df = pd.DataFrame({'ID': [admission_id], 'doc': [document]})
            dataframes.append(df)

# Concatenate all DataFrames into one
sen = pd.concat(dataframes, ignore_index=True)

# Clean the documents
def remove_digits_from_list(text_list):
    remove_digits = str.maketrans('', '', digits)
    return [text.translate(remove_digits) for text in text_list]

sen['cleanDoc'] = sen['doc'].apply(lambda x: remove_digits_from_list([x])[0])

# Prepare data for Doc2Vec
data = list(sen.cleanDoc)
tagged_data = [TaggedDocument(words=word_tokenize(_d.lower()), tags=[str(i)]) for i, _d in enumerate(data)]
model_save_path = os.path.join(targetdir, "d2v.model")

if _train:
    # Doc2Vec model parameters
    start = time.time()
    max_epochs = 20  # Increased epochs for better training
    vector_size = 200
    alpha = 0.025

    model = Doc2Vec(vector_size=vector_size,
                    alpha=alpha,
                    min_alpha=0.0001,
                    min_count=5,
                    dm=0,  # PV-DBOW
                    negative=5,
                    workers=4)  # Reduced workers for better compatibility

    model.build_vocab(tagged_data)

    # Train the Doc2Vec model
    for epoch in range(max_epochs):
        print(f'iteration {epoch}')
        model.train(tagged_data,
                    total_examples=model.corpus_count,
                    epochs=model.epochs)
        model.alpha -= 0.0002
        model.min_alpha = model.alpha

    
    model.save(model_save_path)
    end = time.time()
    print(f"Model Saved in {end - start} seconds")
else:
    model = Doc2Vec.load(model_save_path)

if _insert_db:
    conn = psycopg2.connect(
        dbname=settings['database']['dbname'],
        user=settings['database']['user'],
        password=settings['database']['password'],
        host=settings['database']['host'],
        port= settings['database']['port']
    )
    cur = conn.cursor()

    # Prepare the insert statement for PostgreSQL
    insert_query = """
        INSERT INTO mimiciii.vectors_glc (hadm_id, embedding)
        VALUES (%s, %s)
        ON CONFLICT (hadm_id) DO NOTHING;
    """

    # Generate vectors and insert them into the PostgreSQL table
    list_Subject_id = sen.ID.tolist()  # Get a list of all IDs
    for i in range(len(list_Subject_id)):
        admission_id = int(list_Subject_id[i])  # Convert to integer
        print(f"Inserting {admission_id} ...")
        vector = model.dv[i].tolist()  # Convert the vector to a list
        vector_str = f"[{', '.join(map(str, vector))}]"  # Convert to the string format required by pgvector

        # Insert the admission ID and vector into the table
        cur.execute(insert_query, (admission_id, vector_str))

    # Commit the transaction and close the connection
    conn.commit()
    cur.close()
    conn.close()

    print("Vectors successfully stored in PostgreSQL.")

if _write_csv:
    hadm_subject_df = pd.read_csv(os.path.join(inputdir, "hadm-subject-sel-ms.csv"))

    combined_data = []

    # Generate vectors and insert them into the PostgreSQL table
    list_Subject_id = sen.ID.tolist()  # Get a list of all IDs
    for i in range(len(list_Subject_id)):
        admission_id = int(list_Subject_id[i])  # Convert to integer
        vector = model.dv[i].tolist()  # Convert the vector to a list
        vector_str = f"[{', '.join(map(str, vector))}]"  # Convert to the string format required by pgvector
    
        # Find the corresponding subject_id from hadm_subject_df
        subject_id = hadm_subject_df.loc[hadm_subject_df['hadm_id'] == admission_id, 'subject_id'].values[0]
        
        # Append the data for CSV
        combined_data.append([subject_id, admission_id] + vector)
    
    # Step 3: Create a DataFrame with the combined data
    columns = ['subject_id', 'hadm_id'] + [f'vector_{i}' for i in range(len(vector))]
    combined_df = pd.DataFrame(combined_data, columns=columns)

    # Step 4: Write the DataFrame to a CSV file
    output_file_path = os.path.join(targetdir, "subj_hadm_vectors.csv")
    combined_df.to_csv(output_file_path, index=False)

    print(f"Vectors successfully written to {output_file_path}.")