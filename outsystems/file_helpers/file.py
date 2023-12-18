# Python Modules
import json
import os
import requests


def download_package(file_path: str, auth_token: str, package_url: str):
    response = requests.get(package_url, headers={"Authorization": auth_token})
    # Remove the spaces in the filename
    file_path = file_path.replace(" ", "_")
    # Makes sure that, if a directory is in the filename, that directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(response.content)


def store_data(artifact_dir: str, filename: str, data: str):
    filename = os.path.join(artifact_dir, filename)
    # Remove the spaces in the filename
    filename = filename.replace(" ", "_")
    # Makes sure that, if a directory is in the filename, that directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as outfile:
        json.dump(data, outfile, indent=4)


def load_data(artifact_dir: str, filename: str):
    # Remove the spaces in the filename
    filename = filename.replace(" ", "_")
    if check_file(artifact_dir, filename):
        filename = os.path.join(artifact_dir, filename)
        with open(filename, "r") as infile:
            return json.load(infile)
    raise FileNotFoundError(
        "The file with filename {} does not exist.".format(filename))


def check_file(artifact_dir: str, filename: str):
    filename = os.path.join(artifact_dir, filename)
    return os.path.isfile(filename)


def clear_cache(artifact_dir: str, filename: str):
    if not check_file(artifact_dir, filename):
        return
    filename = os.path.join(artifact_dir, filename)
    os.remove(filename)


# Returns a human readable string representation of bytes
def bytes_human_readable_size(bytes, units=[' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']):
    return str(bytes) + units[0] if bytes < 1024 else bytes_human_readable_size(bytes >> 10, units[1:])
