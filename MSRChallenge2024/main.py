import json
import glob
import os
import shutil

#  path to the folder containing the JSON files
json_folder_path = '/Users/jaydencruz/PycharmProjects/MSRChallenge'

# path to the new folder where files will be moved
processed_folder_path = os.path.join(json_folder_path, 'processed_files')
os.makedirs(processed_folder_path, exist_ok=True)  # Create the folder if it doesn't exist

# Get all JSON files in the specified folder
json_files = glob.glob(os.path.join(json_folder_path, '*.json'))

# List to hold data from all JSON files
data_list = []

# Loop through each JSON file
for file_path in json_files:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)  # Load the JSON data

            # Check the severity level in the 'database_specific' section
            severity = data.get('database_specific', {}).get('severity', '').upper()

            # If the severity is "HIGH" or "CRITICAL", process it
            if severity in ['HIGH', 'CRITICAL']:
                data_list.append(data)  # Add the data to the list if it's of high or critical severity
                print(
                    f"Processed file: {file_path} with severity {severity}")  # Log the processed file path and severity

                # Move the file to the new folder
                new_file_path = os.path.join(processed_folder_path, os.path.basename(file_path))
                shutil.move(file_path, new_file_path)  # Move the file
                print(f"Moved file {file_path} to {new_file_path}")

            else:
                print(f"Skipping file: {file_path} with severity {severity}")  # Log the skipped file
                os.remove(file_path)

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")  # Handle any errors that occur

# Example of accessing the aggregated data (optional)
print(f"Processed {len(data_list)} files with HIGH or CRITICAL severity.")

