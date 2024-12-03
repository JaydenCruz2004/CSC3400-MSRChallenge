import os

def count_json_files(folder_path):
    try:
        # Get a list of all files in the specified folder
        files = os.listdir(folder_path)
        # Filter the list for files with the '.json' extension
        json_files = [file for file in files if file.endswith('.json')]
        # Return the count of JSON files
        return len(json_files)
    except FileNotFoundError:
        return "The folder 'processed_files' does not exist."
    except Exception as e:
        return f"An error occurred: {e}"

# Path to the folder
folder_path = '/Users/jaydencruz/PycharmProjects/MSRChallenge/processed_files'

# Count JSON files
json_count = count_json_files(folder_path)
print(f"Number of JSON files in '{folder_path}': {json_count}")
