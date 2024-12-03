import os
import json
import gensim
from gensim import corpora
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import pyLDAvis.gensim_models

# Load JSON files
# path to the folder that has the json files
json_folder_path = "/Users/jaydencruz/PycharmProjects/MSRChallenge/Duaa'sFiles"

#hold summary and details from the json files
documents = []

#check to make sure that the folder path exist
if not os.path.exists(json_folder_path):
    raise FileNotFoundError(f"The folder path '{json_folder_path}' does not exist. Check the path and try again.")

#iterates through the json files in the folder
for file_name in os.listdir(json_folder_path):
    if file_name.endswith('.json'):
        try:
            with open(os.path.join(json_folder_path, file_name), 'r') as file:
                data = json.load(file)
                # Combine summary and details fields for each JSON entry
                summary = data.get('summary', '')
                details = data.get('details', '')
                documents.append(summary + " " + details)
        except json.JSONDecodeError as e:
            print(f"Error reading JSON file '{file_name}': {e}")
        except Exception as e:
            print(f"Unexpected error while processing '{file_name}': {e}")

# Preprocess text define the stopwords and lemmatize
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

#function to preprocess the text -> tokenize remove stop words and lemm
def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    # Remove stop words and lemmatize tokens
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word.isalnum() and word not in stop_words]
    return tokens

processed_docs = [preprocess_text(doc) for doc in documents]

if len(processed_docs) == 0:
    raise ValueError("No documents were processed. Check if the JSON files contain valid 'summary' or 'details' fields.")

# Create dictionary and corpus
dictionary = corpora.Dictionary(processed_docs)
#creat the BoW of each doc
corpus = [dictionary.doc2bow(doc) for doc in processed_docs]

# Train LDA model
num_topics = 10  # Number of topics to generate
lda_model = gensim.models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=10)

# Print topics
print("\nGenerated Topics:")
for idx, topic in lda_model.print_topics(-1):
    print(f"Topic {idx}: {topic}")

# Visualize topics
try:
    # Save the LDA visualization as an HTML file
    lda_vis = pyLDAvis.gensim_models.prepare(lda_model, corpus, dictionary)
    pyLDAvis.save_html(lda_vis, 'lda_visualization.html')
    print("\nLDA visualization has been saved as 'lda_visualization.html'. Open it in a browser to view.")
except Exception as e:
    print(f"Error during LDA visualization: {e}")
