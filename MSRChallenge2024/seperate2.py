import os
import shutil

# Function to distribute files evenly into the three folders
def distribute_files_evenly(source_folder, target_folders):
    files = os.listdir(source_folder)
    num_files = len(files)
    num_folders = len(target_folders)

    # Ensure the target folders exist
    for folder in target_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Distribute files evenly
    for i, file_name in enumerate(files):
        target_folder = target_folders[i % num_folders]
        source_path = os.path.join(source_folder, file_name)
        target_path = os.path.join(target_folder, file_name)

        print(f"Moving {file_name} to {target_folder}")
        shutil.move(source_path, target_path)

    # After moving, print the number of files in each folder
    for folder in target_folders:
        num_files_in_folder = len(os.listdir(folder))
        print(f"{folder} contains {num_files_in_folder} files.")

# Example usage
if __name__ == "__main__":
    source_folder = "processed_files"  # Folder where matched files are located
    target_folders = ["Jayden's'Files2", "Duaa'sFiles2", "Kimberly'sFiles2"]  # Target folders

    distribute_files_evenly(source_folder, target_folders)
