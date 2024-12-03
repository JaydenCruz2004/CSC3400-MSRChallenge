import os
import json
from datetime import datetime

# Path to the directory containing JSON files
directory_path = "/Users/jaydencruz/PycharmProjects/MSRChallenge/Duaa'sFiles"


def calculate_average_patch_time(directory):
    patch_durations = []
    processed_files = 0  # To count successfully processed files

    # Iterate over all files in the directory
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)

        # Process only JSON files
        if file_name.endswith(".json"):
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)

                    # Handle root JSON structure: either list or dictionary
                    if isinstance(data, list):
                        # Process each item in the list
                        for item in data:
                            patch_durations.extend(process_vulnerability(item))
                    elif isinstance(data, dict):
                        # Process single dictionary
                        patch_durations.extend(process_vulnerability(data))
                    else:
                        print(f"Unknown JSON structure in {file_name}")

                    processed_files += 1
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    # Calculate the average patch time
    if patch_durations:
        average_time = sum(patch_durations) / len(patch_durations)
        print(f"Average time to patch vulnerabilities: {average_time:.2f} days")
    else:
        print("No valid data found to compute the average patch time.")
    print(f"Processed {processed_files} files with HIGH or CRITICAL severity.")

# check the vulnerabiltieries and return the patch times
def process_vulnerability(vuln_data):
    patch_durations = []
    try:
        published_date = vuln_data.get("nvd_published_at")
        reviewed_date = vuln_data.get("github_reviewed_at")

        if published_date and reviewed_date:
            # Convert dates to datetime objects
            published = datetime.fromisoformat(published_date.rstrip("Z"))
            reviewed = datetime.fromisoformat(reviewed_date.rstrip("Z"))

            # Calculate duration in days
            duration = (reviewed - published).days
            patch_durations.append(duration)
    except Exception as e:
        print(f"Error processing vulnerability data: {e}")

    return patch_durations


# Call the function
calculate_average_patch_time(directory_path)

