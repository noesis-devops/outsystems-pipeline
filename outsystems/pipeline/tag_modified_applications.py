# Python Modules
import sys
import os
import argparse

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION

# Functions
from outsystems.lifetime.lifetime_applications import get_running_app_version
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.lifetime.lifetime_applications import set_application_version

# Exceptions


# ############################################################# SCRIPT ##############################################################
def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, source_env: str, tag_data: dict):
    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Get the environment key
    env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, source_env)

    # Get the application names list
    app_list = [x["ApplicationName"] for x in tag_data]

    for version_details in tag_data:

        # Get current running version details
        app_name = version_details["ApplicationName"]
        running_app_version = get_running_app_version(artifact_dir, lt_endpoint, lt_token, env_key, app_name=app_name, app_list=app_list)

        # Check if there are any changes to be tagged in the source environment
        if running_app_version["IsModified"]:
            set_application_version(lt_endpoint, lt_token, env_key, running_app_version["ApplicationKey"], version_details["ChangeLog"], version_details["VersionNumber"])
            print("Version {} successfully created for application {} in {} environment.".format(version_details["VersionNumber"], app_name, source_env), flush=True)
        else:
            print("Application {} is not modified in {} environment. New version creation was skipped.".format(app_name, source_env), flush=True)
# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="(Optional) LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(Optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-s", "--source_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the environment to use for creating new application tags.")
    parser.add_argument("-l", "--app_name", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the application to create the new tag using the currently published version.")
    parser.add_argument("-n", "--version_nbr", type=str, required=True,
                        help="Version number (using M.m.r schema) to assign to the new application tag.")
    parser.add_argument("-m", "--log_msg", type=str, default="Version created automatically using outsystems-pipeline package.",
                        help="(Optional) Change log message to add to the new application tag.")
    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
    # Parse the API endpoint
    lt_api_endpoint = args.lt_endpoint
    # Parse the LT Url and split the LT hostname from the HTTP protocol
    # Assumes the default HTTP protocol = https
    lt_http_proto = LIFETIME_HTTP_PROTO
    lt_url = args.lt_url
    if lt_url.startswith("http://"):
        lt_http_proto = "http"
        lt_url = lt_url.replace("http://", "")
    else:
        lt_url = lt_url.replace("https://", "")
    if lt_url.endswith("/"):
        lt_url = lt_url[:-1]
    # Parte LT API Version
    lt_version = args.lt_api_version
    # Parse the LT Token
    lt_token = args.lt_token
    # Parse Source Environment
    source_env = args.source_env
    # Parse Version Data
    tag_data = [
        {"ApplicationName": args.app_name, "VersionNumber": args.version_nbr, "ChangeLog": args.log_msg}
    ]
    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, source_env, tag_data)
