import os
import sys
import subprocess

def run_mediaconch_on_mkv_files(folder_path, policy_file):
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    files = os.listdir(folder_path)

    for file in files:
        if file.endswith(".mkv"):
            input_file = os.path.join(folder_path, file)
            output_csv = os.path.splitext(input_file)[0] + ".csv"
            
            command = f'mediaconch -p "{policy_file}" "{input_file}" -oc "{output_csv}"'
            subprocess.run(command, shell=True)
            print(f"Processed: {file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mediaconch_batch.py /path/to/directory")
    else:
        folder_path = sys.argv[1]
        policy_file = "policy.xml"  # Replace with the actual policy file path if it's different

        run_mediaconch_on_mkv_files(folder_path, policy_file)
