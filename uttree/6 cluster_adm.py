import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

import os
import sys

_kmeans=False
_hier=True
_last_adm_only=False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.config import load_app_settings
settings = load_app_settings()

inputdir = settings['directories']['input_dir']
targetdir = settings['directories']['target_dir']

# Step 1: Read the vectors from the CSV file
csv_file_path = os.path.join(inputdir, "subj_hadm_vectors.csv")
dfr = pd.read_csv(csv_file_path)

if _last_adm_only:
    df = dfr.loc[dfr.groupby('subject_id')['hadm_id'].idxmax()]
else:
    df = dfr


if _kmeans:
    # Step 2: Extract the vector columns
    vector_columns = [col for col in df.columns if col.startswith('vector_')]
    vectors = df[vector_columns].values

    # Step 3: Optional - Standardize the vectors (helps with clustering)
    scaler = StandardScaler()
    vectors_scaled = scaler.fit_transform(vectors)

    # Step 4: Choose the number of clusters
    n_clusters = 15 # You can change this number

    # Step 5: Perform KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df['cluster'] = kmeans.fit_predict(vectors_scaled)

    # Step 6: Analyze and visualize the clustering results
    # Example: Count the number of items in each cluster
    cluster_counts = df['cluster'].value_counts().sort_index()
    print(cluster_counts)

    # Example: Add cluster centers to the DataFrame

    #cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    #for i, center in enumerate(cluster_centers):
    #    df[f'cluster_center_{i}'] = center

    # Step 7: Save the clustered data to a new CSV file
    output_csv_path = os.path.join(targetdir, "clustered_vectors.csv")
    df.to_csv(output_csv_path, index=False)

    # Step 8: Visualize clusters (optional)
    # Using a pairplot to visualize (only works for lower-dimensional data, e.g., first 4 vector dimensions)
    sns.pairplot(df, vars=vector_columns[:200], hue='cluster', palette='tab10')
    plt.savefig(os.path.join(targetdir, "clusters_pairplot.png"))  # Save the plot to a file

    plt.show()

if _hier:
    from scipy.cluster.hierarchy import dendrogram, linkage

    # Step 2: Extract the vector columns and hadm_id
    vector_columns = [col for col in df.columns if col.startswith('vector_')]
    vectors = df[vector_columns].values
    hadm_ids = df['hadm_id'].tolist()  # List of hadm_ids for labeling
    subject_ids = df['subject_id'].tolist()  # List of subject_ids for labeling

    labels = [f'P{subject_id}-A{hadm_id}' for subject_id, hadm_id in zip(subject_ids, hadm_ids)]

    # Step 3: Standardize the vectors (helps with clustering)
    scaler = StandardScaler()
    vectors_scaled = scaler.fit_transform(vectors)

    # Step 4: Perform Hierarchical Clustering using the 'ward' method
    linked = linkage(vectors_scaled, method='ward')

    # Step 5: Plot the Dendrogram with hadm_id labels
    plt.figure(figsize=(20, 7))  # Adjust the figure size if necessary
    plt.rcParams['font.size'] = 4

    dendrogram(
        linked,
        labels=labels,  # Use hadm_id as labels on the dendrogram
        orientation='top',
        distance_sort='descending',
        show_leaf_counts=True,
        leaf_font_size=4  # Directly set font size for leaf labels

    )

    # Step 6: Save the Dendrogram to a PNG file
    if _last_adm_only:
        typex = 'last_adm_only'
    else:
        typex = 'all_adm'
    output_png_path = os.path.join(targetdir, f"hierarchical_clustering_dendrogram_{typex}.png")
    plt.title('Hierarchical Clustering Dendrogram')
    plt.xlabel('PatientID - AdmissionID ')
    plt.ylabel('Distance')
    plt.tight_layout()  # Adjust layout to fit labels and title
    plt.savefig(output_png_path, dpi=300)  # Save with high resolution
    plt.close()  # Close the plot to free up resources

    print(f"Dendrogram saved to {output_png_path}")