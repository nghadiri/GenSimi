import os
import pandas as pd
import time
import nltk

from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
from string import digits

nltk.download('punkt')

# Load app settings (make sure this function and its dependencies are working)
import sys
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
dataframes = []c
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

model_save_path = os.path.join(targetdir, "d2v.model")
model.save(model_save_path)
end = time.time()
print(f"Model Saved in {end - start} seconds")

# Create DataFrame for embedded vectors
list_Subject_id = sen.ID.tolist()  # Get a list of all IDs
list_total = [model.dv[i] for i in range(len(list_Subject_id))]

# Generate column names for the vectors
list_columns_name = [f'f{i}' for i in range(vector_size)]

# Create DataFrame with vectors and admission_Id
EmbeddedVector = pd.DataFrame(list_total, columns=list_columns_name)
EmbeddedVector['admission_Id'] = list_Subject_id

embedded_vectors_path = os.path.join(targetdir, "embedded_vectors.csv")
# Save the vectors DataFrame to a CSV file
from gensim.models import Doc2Vec
model = Doc2Vec.load(model_save_path)
vector_length = model.vector_size
print("Vector Length:", vector_length)

#EmbeddedVector.to_csv(embedded_vectors_path, index=False)

