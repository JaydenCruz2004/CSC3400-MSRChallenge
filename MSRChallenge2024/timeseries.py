import json
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd


def convert_to_datetime(timestamp):
    """Converts ISO timestamp to a datetime object."""
    try:
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            print(f"Invalid timestamp format: {timestamp}")
            return None


def map_version_to_date(version, dynamic_mapping):
    """Maps version numbers to release dates."""
    version_date_mapping = {
        "2.4.0": "2020-05-01T00:00:00Z",
        "4.3.1": "2021-08-01T00:00:00Z",
        "7.0.1": "2022-01-01T00:00:00Z",
        # Add additional static mappings
    }
    return version_date_mapping.get(version) or dynamic_mapping.get(version)


def process_entry(entry, dynamic_mapping):
    """Helper function to process each individual entry."""
    patch_time = None
    skipped_entries = []

    published = entry.get("published")
    if not published:
        skipped_entries.append((entry.get("id", "Unknown"), "Published date not found"))
        return None, skipped_entries

    fixed = None
    affected = entry.get("affected", [])
    for item in affected:
        ranges = item.get("ranges", [])
        for range_info in ranges:
            for event in range_info.get("events", []):
                if "fixed" in event:
                    fixed = event["fixed"]
                    break
            if fixed:
                break
        if fixed:
            break

    if not fixed:
        skipped_entries.append((entry.get("id", "Unknown"), "Fixed date not found"))
        return None, skipped_entries

    fixed_date = convert_to_datetime(fixed)

    if not fixed_date:
        fixed_date_str = map_version_to_date(fixed, dynamic_mapping)
        if not fixed_date_str:
            skipped_entries.append((entry.get("id", "Unknown"), f"No date mapping for version {fixed}"))
            return None, skipped_entries
        fixed_date = convert_to_datetime(fixed_date_str)

    published_date = convert_to_datetime(published)
    if not published_date:
        skipped_entries.append((entry.get("id", "Unknown"), "Invalid published date"))
        return None, skipped_entries

    # Debug: Print out the dates to check if they are correct
    print(f"Published: {published_date}, Fixed: {fixed_date}")

    if fixed_date < published_date:
        skipped_entries.append((entry.get("id", "Unknown"), "Fixed date is earlier than published date"))
        return None, skipped_entries

    # Calculate the patch time in minutes
    patch_time = (fixed_date - published_date).total_seconds() / 60

    # Filter out unusually large patch times (greater than 30 days)
    if patch_time > 60 * 24 * 30:  # 30 days
        skipped_entries.append((entry.get("id", "Unknown"), "Patch time too large"))
        return None, skipped_entries

    return patch_time, skipped_entries


# The rest of your code for building dynamic mapping, loading files, and generating the time series follows...


def build_dynamic_mapping(data_list):
    """Dynamically generates mappings for versions."""
    mapping = {}

    for entry in data_list:
        if isinstance(entry, list):
            for sub_entry in entry:
                if isinstance(sub_entry, dict):
                    published = sub_entry.get("published")
                    if published:
                        affected = sub_entry.get("affected", [])
                        for item in affected:
                            ranges = item.get("ranges", [])
                            for range_info in ranges:
                                for event in range_info.get("events", []):
                                    if "fixed" in event:
                                        mapping[event["fixed"]] = published
        elif isinstance(entry, dict):
            published = entry.get("published")
            if published:
                affected = entry.get("affected", [])
                for item in affected:
                    ranges = item.get("ranges", [])
                    for range_info in ranges:
                        for event in range_info.get("events", []):
                            if "fixed" in event:
                                mapping[event["fixed"]] = published
    return mapping


def load_json_files(file_pattern):
    """Loads JSON files into a list."""
    data_list = []
    files = glob.glob(file_pattern)
    print(f"Files found: {files}")

    for file in files:
        try:
            with open(file, "r") as f:
                data = json.load(f)
                data_list.append(data)
        except Exception as e:
            print(f"Error loading file {file}: {e}")
    return data_list


# Define file pattern and load files
file_pattern = "/Users/jaydencruz/PycharmProjects/MSRChallenge/processed_files/*.json"
data_list = load_json_files(file_pattern)

# Build dynamic mapping and calculate patch times
dynamic_mapping = build_dynamic_mapping(data_list)
patch_times, published_dates, skipped_entries = calculate_patch_times(data_list, dynamic_mapping)

# Log skipped entries
if skipped_entries:
    print("\nSkipped Entries:")
    for entry_id, reason in skipped_entries:
        print(f"Entry ID: {entry_id}, Reason: {reason}")

# Filter out zero patch times and entries with missing published dates
valid_dates = []
valid_patch_times = []

for i in range(len(published_dates)):
    if published_dates[i] and patch_times[i] > 0:
        valid_dates.append(convert_to_datetime(published_dates[i]))
        valid_patch_times.append(patch_times[i])

# Ensure that both lists (valid_dates and valid_patch_times) have the same length
if len(valid_dates) == len(valid_patch_times):
    # Create a DataFrame to calculate time series
    df = pd.DataFrame({"published_date": valid_dates, "patch_time": valid_patch_times})

    # Set the published date as the index
    df.set_index("published_date", inplace=True)

    # Resample by month and calculate the mean patch time for each month
    monthly_patch_times = df.resample('ME').mean()

    # Plot the time series of average patch times
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_patch_times.index, monthly_patch_times["patch_time"], marker='o', color='b')
    plt.title("Average Patch Time by Month")
    plt.xlabel("Month")
    plt.ylabel("Average Patch Time (minutes)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Print the average patch time
    if valid_patch_times:
        average_patch_time = sum(valid_patch_times) / len(valid_patch_times)
        print(f"\nAverage Patch Time: {average_patch_time:.2f} minutes")
    else:
        print("\nNo valid patch times available.")
else:
    print("\nError: Valid dates and patch times do not have the same length.")
