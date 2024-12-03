import os
import json
import shutil

# Function to load CVEs from the Filtered Data.json
def load_filtered_data(filtered_file):
    with open(filtered_file, 'r') as f:
        data = json.load(f)
    # Extract CVEs from the filtered data
    cve_list = {entry["CVE"] for entry in data}  # Use set for fast lookup
    return cve_list

# Function to load processed data .json files and find matches
def find_matching_files(processed_folder, cve_list, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over all json files in the processed data folder
    for file_name in os.listdir(processed_folder):
        if file_name.endswith(".json"):
            file_path = os.path.join(processed_folder, file_name)

            with open(file_path, 'r') as f:
                data = json.load(f)

            # Checks if any aliases (CVE) match the filtered data
            aliases = {alias for alias in data.get("aliases", [])}

            # Find intersection of CVEs between filtered data and aliases in processed file
            matching_cves = cve_list.intersection(aliases)

            if matching_cves:
                print(f"Match found in {file_name}: {matching_cves}")
                # If there's a match, copy the file to the output folder
                shutil.copy(file_path, os.path.join(output_folder, file_name))

# Main function to orchestrate the process
def main(filtered_file, processed_folder, output_folder):
    # Load filtered CVEs
    cve_list = load_filtered_data(filtered_file)

    # Find and copy matching files
    find_matching_files(processed_folder, cve_list, output_folder)

# Example usage
if __name__ == "__main__":
    filtered_file = "Filtered Data.json"  # Path to the Filtered Data.json

    processed_folder = "processed_files"  # Folder containing the processed .json files
    output_folder = "matched_files"     # Folder where matched files will be saved

    main(filtered_file, processed_folder, output_folder)



