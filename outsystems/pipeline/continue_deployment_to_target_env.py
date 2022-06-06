# Python Modules
import sys
import os
import argparse
from time import sleep

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
from outsystems.vars.pipeline_vars import SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
    DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
    DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_key
from outsystems.lifetime.lifetime_deployments import get_deployment_status, get_deployment_info, \
    continue_deployment, get_running_deployment
from outsystems.file_helpers.file import store_data
from outsystems.lifetime.lifetime_base import build_lt_endpoint
# Exceptions
from outsystems.exceptions.deployment_not_found import DeploymentNotFoundError

# ############################################################# SCRIPT ##############################################################


def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, dest_env: str):

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Gets the environment key for the destination environment
    dest_env_key = get_environment_key(artifact_dir, lt_endpoint, lt_token, dest_env)

    # Find deployment plan with 'saved' status in destination environment
    deployment = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_key)
    if deployment is None:
        raise DeploymentNotFoundError("Unable to find a running deployment plan on {} environment.".format(dest_env))

    # Grab the key from the deployment plan found
    dep_plan_key = deployment["Key"]
    print("Deployment plan {} was found.".format(dep_plan_key), flush=True)

    # Check if created deployment plan has conflicts
    dep_details = get_deployment_info(artifact_dir, lt_endpoint, lt_token, dep_plan_key)
    if len(dep_details["ApplicationConflicts"]) > 0:
        store_data(artifact_dir, CONFLICTS_FILE, dep_details["ApplicationConflicts"])
        print("Deployment plan {} has conflicts and will be aborted. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE), flush=True)
        # Previously created deployment plan to target environment will NOT be deleted
        sys.exit(1)

    # Check Deployment Plan status.
    dep_status = get_deployment_status(
        artifact_dir, lt_endpoint, lt_token, dep_plan_key)

    if dep_status["DeploymentStatus"] == DEPLOYMENT_WAITING_STATUS and dep_status["Info"] == "deployment_prepared":
        continue_deployment(lt_endpoint, lt_token, dep_plan_key)
        print("Deployment plan {} resumed execution.".format(dep_plan_key), flush=True)
    else:
        print("Deployment plan {} is not in 'Prepared' status".format(dep_plan_key), flush=True)
        # Previously created deployment plan to target environment will NOT be deleted
        sys.exit(1)

    # Sleep thread until deployment has finished
    wait_counter = 0
    while wait_counter < DEPLOYMENT_TIMEOUT_IN_SECS:
        # Check Deployment Plan status.
        dep_status = get_deployment_status(
            artifact_dir, lt_endpoint, lt_token, dep_plan_key)
        if dep_status["DeploymentStatus"] != DEPLOYMENT_RUNNING_STATUS:
            # Check deployment status is pending approval. Force it to continue (if 2-Step deployment is enabled)
            if dep_status["DeploymentStatus"] == DEPLOYMENT_WAITING_STATUS:
                continue_deployment(lt_endpoint, lt_token, dep_plan_key)
                print("Deployment plan {} resumed execution.".format(dep_plan_key), flush=True)
            elif dep_status["DeploymentStatus"] in DEPLOYMENT_ERROR_STATUS_LIST:
                print("Deployment plan finished with status {}.".format(dep_status["DeploymentStatus"]), flush=True)
                store_data(artifact_dir, DEPLOY_ERROR_FILE, dep_status)
                sys.exit(1)
            else:
                # If it reaches here, it means the deployment was successful
                print("Deployment plan finished with status {}.".format(dep_status["DeploymentStatus"]), flush=True)
                # Exit the script to continue with the pipeline
                sys.exit(0)
        # Deployment status is still running. Go back to sleep.
        sleep(SLEEP_PERIOD_IN_SECS)
        wait_counter += SLEEP_PERIOD_IN_SECS
        print("{} secs have passed since the deployment started...".format(wait_counter), flush=True)

    # Deployment timeout reached. Exit script with error
    print("Timeout occurred while deployment plan is still in {} status.".format(DEPLOYMENT_RUNNING_STATUS), flush=True)
    sys.exit(1)

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
                        help="LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-d", "--destination_env", type=str, required=True,
                        help="Name, as displayed in LifeTime, of the destination environment where you want to continue the deployment plan.")

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
    # Parse Destination Environment
    dest_env = args.destination_env

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, dest_env)
