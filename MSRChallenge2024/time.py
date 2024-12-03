import json
import glob
from datetime import datetime

# Directory containing JSON files
json_folder_path = "/Users/jaydencruz/PycharmProjects/MSRChallenge/Kimberly'sFiles"

# List to store patch times (in days)
patch_times = []

# Iterate through all JSON files
json_files = glob.glob(f"{json_folder_path}/*.json")

for file_path in json_files:
    try:
        # Load the JSON data
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract the published date
        published_date = data.get("published")
        if not published_date:
            print(f"Skipping {file_path}: 'published' date not found.")
            continue

        # Extract fixed version information
        fixed_version_date = None
        for range_info in data.get("affected", [{}])[0].get("ranges", []):
            fixed = range_info.get("fixed")
            if fixed:
                fixed_version_date = range_info.get("introduced")  # Example placeholder for 'fixed_date'
                break

        # Validate the fixed date
        if not fixed_version_date:
            print(f"Skipping {file_path}: 'fixed version date' not found.")
            continue

        # Normalize the dates to datetime objects
        published_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
        fixed_date = datetime.fromisoformat(fixed_version_date.replace("Z", "+00:00"))

        # Calculate the patch time in days
        patch_time = (fixed_date - published_date).days
        patch_times.append(patch_time)

    except KeyError as e:
        print(f"Error in {file_path}: Missing key - {e}")
    except ValueError as e:
        print(f"Error in {file_path}: Invalid date format - {e}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Calculate and display the average patch time
if patch_times:
    average_patch_time = sum(patch_times) / len(patch_times)
    print(f"\nAverage time to patch vulnerabilities: {average_patch_time:.2f} days")
else:
    print("\nNo valid patch times found.")
