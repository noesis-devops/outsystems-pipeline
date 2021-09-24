# Python Modules
import sys
import os
import argparse
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
from outsystems.vars.manifest_vars import MANIFEST_CONFIG_ITEM_TYPE, MANIFEST_MODULE_KEY, MANIFEST_CONFIG_ITEM_KEY, \
    MANIFEST_CONFIG_ITEM_TARGET_VALUE, MANIFEST_CONFIG_ITEM_NAME, MANIFEST_CONFIG_ITEM_TYPE
from outsystems.vars.properties_vars import PROPERTY_TYPE_SITE_PROPERTY
from outsystems.vars.lifetime_vars import LIFETIME_HTTP_PROTO
from outsystems.vars.file_vars import ARTIFACT_FOLDER
# Functions
from outsystems.manifest.manifest_base import get_configuration_items_for_environment
from outsystems.manifest.manifest_base import get_environment_details
from outsystems.properties.properties_set_value import set_site_property_value


# Function to apply configuration values to a target environment
def main(artifact_dir: str, lt_http_proto: str, lt_url: str, lt_token: str, target_env_label: str, trigger_manifest: dict):
    
    # Tuple with (EnvName, EnvKey): target_env_tuple[0] = EnvName; target_env_tuple[1] = EnvKey
    target_env_tuple = get_environment_details(trigger_manifest, target_env_label)
    
    # Get configuration items defined in the manifest for target environment
    config_items = get_configuration_items_for_environment(trigger_manifest, target_env_tuple[1])

    # Check if there are any configuration item values to apply for target environment 
    if len(config_items) == 0:
        print("No configuration item values were found in the manifest for {} (Label: {}).".format(target_env_tuple[0], target_env_label), flush=True)
    else:
        print("Applying new values to configuration items in {} (Label: {})...".format(target_env_tuple[0], target_env_label), flush=True)

    # Apply target value for each configuration item according to its type
    for cfg_item in config_items:
        if cfg_item[MANIFEST_CONFIG_ITEM_TYPE] == PROPERTY_TYPE_SITE_PROPERTY:
            result = set_site_property_value(
                lt_url, lt_token, cfg_item[MANIFEST_MODULE_KEY], target_env_tuple[1], cfg_item[MANIFEST_CONFIG_ITEM_KEY], cfg_item[MANIFEST_CONFIG_ITEM_TARGET_VALUE])
            if result["Success"]:
                print("New value successfully applied to configuration item '{}' ({}).".format(cfg_item[MANIFEST_CONFIG_ITEM_NAME], cfg_item[MANIFEST_CONFIG_ITEM_TYPE]), flush=True)
            else:
                print("Unable to apply new value to configuration item '{}' ({}).\nReason: {}".format(cfg_item[MANIFEST_CONFIG_ITEM_NAME], cfg_item[MANIFEST_CONFIG_ITEM_TYPE], result["Message"]), flush=True)            
        else:
            raise NotImplementedError("Configuration item type '{}' not supported.".format(cfg_item[MANIFEST_CONFIG_ITEM_TYPE]))
    
    # Exit the script to continue with the pipeline
    sys.exit(0)


# End of main()


if __name__ == "__main__":
    # Argument menu / parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts", type=str, default=ARTIFACT_FOLDER,
                        help="(Optional) Name of the artifacts folder. Default: \"Artifacts\"")
    parser.add_argument("-u", "--lt_url", type=str, required=True,
                        help="URL for LifeTime environment, without the API endpoint. Example: \"https://<lifetime_host>\"")
    parser.add_argument("-t", "--lt_token", type=str, required=True,
                        help="Service account token for Properties API calls.")
    parser.add_argument("-e", "--target_env_label", type=str, required=True,
                        help="Label, as configured in the manifest, of the target environment where the configuration values will be applied.")
    parser.add_argument("-m", "--trigger_manifest", type=str, required=True,
                        help=" Manifest artifact (in JSON format) received when the pipeline is triggered. Contains required data used throughout the pipeline execution.")

    args = parser.parse_args()

    # Parse the artifact directory
    artifact_dir = args.artifacts
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
    # Parse the LT Token
    lt_token = args.lt_token
    # Parse Destination Environment
    target_env_label = args.target_env_label
    # Parse Manifest artifact
    # TODO: Isolate in separate funtion to store manifest as a file
    trigger_manifest = json.loads(args.trigger_manifest)
    
    # Calls the main script
    main(artifact_dir, lt_http_proto, lt_url, lt_token, target_env_label, trigger_manifest)