import os
import glob
import json
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


# Directory path where JSON files are located
json_directory_path = "/Users/jaydencruz/PycharmProjects/MSRChallenge/Kimberly'sFiles"

# Use glob to get all JSON files in the directory
json_files = glob.glob(os.path.join(json_directory_path, "*.json"))

# Check if we have any JSON files
if not json_files:
    print("No JSON files found in the directory.")
else:
    # Initialize lists to hold the extracted text and labels
    texts = []
    labels = []

    # Process each JSON file in the directory
    for json_file_path in json_files:
        try:
            print(f"Processing {json_file_path}...")

            with open(json_file_path, 'r') as f:
                data = json.load(f)

            # Extract the relevant fields (e.g., summary and severity)
            summary = data.get("summary", "")
            severity = data.get("database_specific", {}).get("severity", "UNKNOWN")

            # Convert severity to a numerical label (example: HIGH = 2, MEDIUM = 1, LOW = 0)
            if isinstance(severity, str):
                if severity.upper() == "HIGH":
                    label = 2
                elif severity.upper() == "MEDIUM":
                    label = 1
                elif severity.upper() == "LOW":
                    label = 0
                else:
                    label = -1  # Unknown severity
            else:
                label = -1  # Unknown severity if it's not a string

            # Add the extracted summary and severity label to the lists
            texts.append(summary)
            labels.append(label)

        except Exception as e:
            print(f"Error processing {json_file_path}: {e}")

    # If we have enough data, proceed with the machine learning steps
    if len(texts) > 0:
        # Convert the text data into numerical features using TF-IDF
        vectorizer = TfidfVectorizer(stop_words=nltk.corpus.stopwords.words('english'))
        X = vectorizer.fit_transform(texts)
        y = labels

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Initialize the Logistic Regression model
        model = LogisticRegression(max_iter=1000)

        # Train the model
        model.fit(X_train, y_train)

        # Predict on the test set
        y_pred = model.predict(X_test)

        # Evaluate the model
        print("\nModel Evaluation:")
        print(classification_report(y_test, y_pred))

        # Predict the severity of a new vulnerability (example)
        new_summary = "Keycloak's admin API allows low privilege users to use administrative functions"
        new_summary_tfidf = vectorizer.transform([new_summary])
        predicted_severity = model.predict(new_summary_tfidf)

        severity_labels = ["LOW", "MEDIUM", "HIGH"]
        print(f"\nPredicted Severity for new vulnerability: {severity_labels[predicted_severity[0]]}")

    else:
        print("No valid data found for processing.")
