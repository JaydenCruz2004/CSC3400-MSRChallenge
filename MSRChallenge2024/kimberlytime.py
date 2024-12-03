import json
import glob
from datetime import datetime


def convert_to_datetime(timestamp):
    """Converts ISO timestamp to a datetime object."""
    try:
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return None


def map_version_to_date(version, dynamic_mapping):
    """Maps version numbers to release dates."""
    version_date_mapping = {
        "2.4.0": "2020-05-01T00:00:00Z",
        "4.3.1": "2021-08-01T00:00:00Z",
        "7.0.1": "2022-01-01T00:00:00Z",
    }
    return version_date_mapping.get(version) or dynamic_mapping.get(version)


def calculate_average_patch_time(data_list, dynamic_mapping):
    """Calculates average patch time."""
    patch_times = []
    skipped_entries = []

    for entry in data_list:
        published = entry.get("published")
        if not published:
            skipped_entries.append((entry.get("id"), "Published date not found"))
            continue

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
            skipped_entries.append((entry.get("id"), "Fixed date not found"))
            continue

        fixed_date = convert_to_datetime(fixed)


        if not fixed_date:
            fixed_date_str = map_version_to_date(fixed, dynamic_mapping)
            if not fixed_date_str:
                skipped_entries.append((entry.get("id"), f"No date mapping for version {fixed}"))
                continue
            fixed_date = convert_to_datetime(fixed_date_str)

        published_date = convert_to_datetime(published)
        if not published_date:
            skipped_entries.append((entry.get("id"), "Invalid published date"))
            continue

        if fixed_date < published_date:
            skipped_entries.append((entry.get("id"), "Fixed date is earlier than published date"))
            continue

        patch_time = (fixed_date - published_date).total_seconds()/60
        print(fixed_date, published_date)
        patch_times.append(patch_time)
        print(patch_time)

    if patch_times:
        average_patch_time = sum(patch_times) / len(patch_times)
        return average_patch_time, skipped_entries
    else:
        return 0, skipped_entries


def build_dynamic_mapping(data_list):
    """Dynamically generates mappings for versions."""
    mapping = {}
    for entry in data_list:
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
file_pattern = "/Users/jaydencruz/PycharmProjects/MSRChallenge/Kimberly'sFiles/*.json"
data_list = load_json_files(file_pattern)

# Build dynamic mapping and calculate average patch time
dynamic_mapping = build_dynamic_mapping(data_list)
average_patch_time, skipped_entries = calculate_average_patch_time(data_list, dynamic_mapping)

# Log skipped entries
if skipped_entries:
    print("\nSkipped Entries:")
    for entry_id, reason in skipped_entries:
        print(f"Entry ID: {entry_id}, Reason: {reason}")

# Print average patch time
print(f"\nAverage Patch Time: {average_patch_time:.2f} minutes")
