# Python Modules
import sys
import os
import argparse
from pkg_resources import parse_version
from time import sleep
import json

# Workaround for Jenkins:
# Set the path to include the outsystems module
# Jenkins exposes the workspace directory through env.
if "WORKSPACE" in os.environ:
    sys.path.append(os.environ['WORKSPACE'])
else:  # Else just add the project dir
    sys.path.append(os.getcwd())

# Custom Modules
# Variables
from outsystems.vars.file_vars import ARTIFACT_FOLDER, APPLICATION_OAP_FOLDER, APPLICATION_OAP_FILE
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO, LIFETIME_API_ENDPOINT, LIFETIME_API_VERSION
from outsystems.vars.manifest_vars import MANIFEST_APPLICATION_VERSIONS, MANIFEST_FLAG_IS_TEST_APPLICATION
from outsystems.vars.pipeline_vars import QUEUE_TIMEOUT_IN_SECS, SLEEP_PERIOD_IN_SECS, CONFLICTS_FILE, \
    REDEPLOY_OUTDATED_APPS, DEPLOYMENT_TIMEOUT_IN_SECS, DEPLOYMENT_RUNNING_STATUS, DEPLOYMENT_WAITING_STATUS, \
    DEPLOYMENT_ERROR_STATUS_LIST, DEPLOY_ERROR_FILE, ALLOW_CONTINUE_WITH_ERRORS
# Functions
from outsystems.lifetime.lifetime_environments import get_environment_app_version, get_environment_deployment_zones
from outsystems.lifetime.lifetime_applications import get_application_version
from outsystems.lifetime.lifetime_deployments import get_deployment_status, get_deployment_info, \
    send_binary_deployment, delete_deployment, start_deployment, continue_deployment, get_running_deployment, \
    check_deployment_two_step_deploy_status
from outsystems.file_helpers.file import store_data, load_data, check_file
from outsystems.lifetime.lifetime_base import build_lt_endpoint
from outsystems.manifest.manifest_base import get_environment_details, get_deployment_notes
from outsystems.pipeline.deploy_tags_to_target_env_with_manifest import generate_deployment_based_on_manifest, check_if_can_deploy

# Exceptions
from outsystems.exceptions.app_does_not_exist import AppDoesNotExistError
from outsystems.exceptions.manifest_does_not_exist import ManifestDoesNotExistError


# ############################################################# SCRIPT ##############################################################
def get_oap_filename(app_data: dict, friendly_package_names: bool):
    filename = ""
    if friendly_package_names:
        filename = "{}_v{}{}".format(app_data["ApplicationName"].replace(" ", "_"), app_data["VersionNumber"].replace(".", "_"), APPLICATION_OAP_FILE)
    else:
        filename = "{}{}".format(app_data["VersionKey"], APPLICATION_OAP_FILE)

    return filename

def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_api_endpoint: str, lt_api_version: int, lt_token: str, dest_env_label: str, trigger_manifest: dict, include_test_apps: bool, friendly_package_names: bool):

    app_data_list = []  # will contain the applications to deploy details from LT
    to_deploy_app_keys = []  # will contain the app keys for the apps tagged

    # Builds the LifeTime endpoint
    lt_endpoint = build_lt_endpoint(lt_http_proto, lt_url, lt_api_endpoint, lt_api_version)

    # Tuple with (EnvName, EnvKey): dest_env_tuple[0] = EnvName; dest_env_tuple[1] = EnvKey
    dest_env_tuple = get_environment_details(trigger_manifest, dest_env_label)


    for app in trigger_manifest[MANIFEST_APPLICATION_VERSIONS]:
        if not include_test_apps and app[MANIFEST_FLAG_IS_TEST_APPLICATION]:
            continue

        wait_counter = 0
        deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_tuple[1])
        while len(deployments) > 0:
            if wait_counter >= QUEUE_TIMEOUT_IN_SECS:
                print("Timeout occurred while waiting for LifeTime to be free, to create the new deployment plan.", flush=True)
                sys.exit(1)
            sleep(SLEEP_PERIOD_IN_SECS)
            wait_counter += SLEEP_PERIOD_IN_SECS
            print("Waiting for LifeTime to be free. Elapsed time: {} seconds...".format(wait_counter), flush=True)
            deployments = get_running_deployment(artifact_dir, lt_endpoint, lt_token, dest_env_tuple[1])

        # LT is free to deploy
        # Get binary file name
        oap_file = get_oap_filename(app, friendly_package_names)
        # Set binary file path
        file_path = os.path.join(artifact_dir, APPLICATION_OAP_FOLDER, oap_file)

        if check_file("", file_path):
            print("'{}' application binary path: '{}'".format(app["ApplicationName"], file_path), flush=True)
        else:
            print("Could not find binary file for '{}' application: '{}'".format(app["ApplicationName"], file_path), flush=True)
            continue

        # Send the deployment plan and grab the key
        dep_plan_key = send_binary_deployment(artifact_dir, lt_endpoint, lt_token, lt_api_version, dest_env_tuple[1], file_path)

        print("Deployment plan {} created successfully.'".format(dep_plan_key, oap_file), flush=True)


        # Check if created deployment plan has conflicts
        dep_details = get_deployment_info(artifact_dir, lt_endpoint, lt_token, dep_plan_key)
        has_conflicts = len(dep_details["ApplicationConflicts"]) > 0
        if has_conflicts:
            store_data(artifact_dir, CONFLICTS_FILE, dep_details["ApplicationConflicts"])
            if not ALLOW_CONTINUE_WITH_ERRORS or lt_api_version == 1:
                print("Deployment plan {} has conflicts and will be aborted. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE), flush=True)
                # Abort previously created deployment plan to target environment
                delete_deployment(lt_endpoint, lt_token, dep_plan_key)
                print("Deployment plan {} was deleted successfully.".format(dep_plan_key), flush=True)
                sys.exit(1)
            else:
                print("Deployment plan {} has conflicts but will continue with errors. Check {} artifact for more details.".format(dep_plan_key, CONFLICTS_FILE), flush=True)

        # Check if outdated consumer applications (outside of deployment plan) should be redeployed and start the deployment plan execution
        if lt_api_version == 1:  # LT for OS version < 11
            start_deployment(lt_endpoint, lt_token, dep_plan_key)
        elif lt_api_version == 2:  # LT for OS v11
            if has_conflicts:
                start_deployment(lt_endpoint, lt_token, dep_plan_key, redeploy_outdated=False, continue_with_errors=True)
            else:
                start_deployment(lt_endpoint, lt_token, dep_plan_key, redeploy_outdated=REDEPLOY_OUTDATED_APPS)
        else:
            raise NotImplementedError("Please make sure the API version is compatible with the module.")
        print("Deployment plan {} started being executed.".format(dep_plan_key), flush=True)

        continue
        # Flag to only alert the user once
        alert_user = False
        # Sleep thread until deployment has finished
        wait_counter = 0
        while wait_counter < DEPLOYMENT_TIMEOUT_IN_SECS:
            # Check Deployment Plan status.
            dep_status = get_deployment_status(
                artifact_dir, lt_endpoint, lt_token, dep_plan_key)
            if dep_status["DeploymentStatus"] != DEPLOYMENT_RUNNING_STATUS:
                # Check deployment status is pending approval.
                if dep_status["DeploymentStatus"] == DEPLOYMENT_WAITING_STATUS:
                    # Check if deployment waiting status is due to 2-Step
                    if check_deployment_two_step_deploy_status(dep_status):
                        # Force it to continue in case of force_two_step_deployment parameter
                        if force_two_step_deployment:
                            continue_deployment(lt_endpoint, lt_token, dep_plan_key)
                            print("Deployment plan {} resumed execution.".format(dep_plan_key), flush=True)
                        else:
                            # Exit the script to continue with the pipeline execution
                            print("Deployment plan {} first step finished successfully.".format(dep_plan_key), flush=True)
                            sys.exit(0)
                    # Send notification to alert deployment manual intervention.
                    elif not alert_user:
                        alert_user = True
                        print("A manual intervention is required to continue the execution of the deployment plan {}.".format(dep_plan_key), flush=True)
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
                        help="(Optional) Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Token for LifeTime API calls.")
    parser.add_argument("-v", "--lt_api_version", type=int, default=LIFETIME_API_VERSION,
                        help="(Optional) LifeTime API version number. If version <= 10, use 1, if version >= 11, use 2. Default: 2")
    parser.add_argument("-e", "--lt_endpoint", type=str, default=LIFETIME_API_ENDPOINT,
                        help="(Optional) Used to set the API endpoint for LifeTime, without the version. Default: \"lifetimeapi/rest\"")
    parser.add_argument("-d", "--destination_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the destination environment where you want to deploy the apps.")
    parser.add_argument("-f", "--manifest_file", type=str,
                        help="Manifest file path (either deployment or trigger), used to promote the same application versions throughout the pipeline execution.")
    parser.add_argument("-i", "--include_test_apps", action='store_true',
                        help="(Optional) Flag that indicates if applications marked as \"Test Application\" in the trigger manifest are included in the Air Gap deployment.")
    parser.add_argument("-n", "--friendly_package_names", action='store_true',
                        help="Flag that indicates if downloaded application packages should have a user-friendly name. Example: \"AppName_v1_2_1\"")

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
    dest_env_label = args.destination_env_label
    # Parse Include Test Apps flag
    include_test_apps = args.include_test_apps

    # Validate Manifest is being passed either as JSON or as file
    if not args.manifest_file:
        raise ManifestDoesNotExistError("The manifest was not provided as JSON or as a file. Aborting!")

    # Parse Trigger Manifest artifact
    trigger_manifest = load_data("", args.manifest_file)

    friendly_package_names = args.friendly_package_names

    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_api_endpoint, lt_version, lt_token, dest_env_label, trigger_manifest, include_test_apps, friendly_package_names)
