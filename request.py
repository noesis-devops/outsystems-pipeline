import argparse
import requests
import json
import subprocess

# Constants
JIRA_URL = "https://noesis-devops.atlassian.net"
JIRA_USER = "rodrigo.r.alcaide@noesis.pt"
outsystems_url = "https://noesisdemos.outsystemscloud.com"

def get_arguments():
    """
    Parse command-line arguments for Epic ID and Jira API Token.
    Returns:
        args (Namespace): Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch child issues from a Jira Epic and deploy applications.')
    parser.add_argument('--epic', required=True, help='ID of the Jira Epic')
    parser.add_argument('--jira_token', required=True, help='Jira API Token')
    parser.add_argument('--lifetime_token', required=True, help='OutSystems API Token')
    parser.add_argument('--source_env', required=True, help='Source environment (e.g. Development)')
    parser.add_argument('--target_env', required=True, help='Target environment (e.g. Production)')
    return parser.parse_args()

def fetch_child_issues(epic_id, jira_token):
    """
    Fetch child issues of a given Jira Epic using the Jira API.

    Args:
        epic_id (str): ID of the Jira Epic.
        token (str): Jira API Token.

    Returns:
        list: List of issues retrieved from Jira.
    """
    jql_query = f"parent={epic_id}"
    search_url = f"{JIRA_URL}/rest/api/2/search?jql={jql_query}"
    headers = {"Accept": "application/json"}
    auth = (JIRA_USER, jira_token)

    try:
        response = requests.get(search_url, headers=headers, auth=auth)
        response.raise_for_status()
        data = response.json()
        return data.get("issues", [])
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Jira: {e}")
        return []

def process_issues(issues):
    """
    Process issues data to extract relevant fields like description and version.

    Args:
        issues (list): List of issues from Jira.

    Returns:
        list: List of dictionaries containing processed issue data.
    """
    processed_issues = []
    for issue in issues:
        issue_data = {
            "app_name": issue['fields'].get('description', "No description available for this issue."),
            "app_version": issue['fields'].get('customfield_10055', "No version available for this issue.")
        }
        processed_issues.append(issue_data)
    return processed_issues

def get_latest_version(app_name, outsystems_url, lifetime_token):
    """
    Get the latest version of an application from OutSystems.

    Args:
        app_name (str): Name of the application.
        outsystems_url (str): OutSystems environment URL.
        lifetime_token (str): OutSystems API Token.

    Returns:
        str: Latest version or None if not found.
    """
    headers = {
        "Authorization": f"Bearer {lifetime_token}",
        "Accept": "application/json"
    }

    # Endpoint correto para buscar versões pode precisar de ajustes
    url = f"{outsystems_url}/lifetimeapi/v2/Applications?filter={app_name}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data or "Applications" not in data:
            print(f"No versions found for {app_name}")
            return None

        versions = [app["Version"] for app in data["Applications"] if app["Name"] == app_name]
        latest_version = sorted(versions, reverse=True)[0] if versions else None

        return latest_version
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest version for {app_name}: {e}")
        return None

def tag_new_version(app_name, outsystems_url, lifetime_token):
    """
    Create and tag a new version of an application in OutSystems.

    Args:
        app_name (str): Name of the application.
        outsystems_url (str): OutSystems environment URL.
        lifetime_token (str): OutSystems API Token.

    Returns:
        str: New version tagged or None if failed.
    """
    latest_version = get_latest_version(app_name, outsystems_url, lifetime_token)

    if not latest_version:
        print(f"Cannot find latest version for {app_name}. Aborting tag creation.")
        return None

    # Incrementar a versão (de 2.0 para 3.0, por exemplo)
    new_version = str(int(latest_version.split(".")[0]) + 1) + ".0"

    tag_payload = {
        "ApplicationName": app_name,
        "Version": new_version
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {lifetime_token}"
    }

    tag_url = f"{outsystems_url}/lifetimeapi/v2/Applications/Tag"

    try:
        response = requests.post(tag_url, json=tag_payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully tagged {app_name} with version {new_version}.")
        return new_version
    except requests.exceptions.RequestException as e:
        print(f"Error tagging {app_name}: {e}")
        return None

def create_deployment_plan(processed_issues, outsystems_url, lifetime_token, source_env, target_env):
    """
    Generate a deployment plan using the applications extracted from Jira.

    Args:
        processed_issues (list): List of processed issues.
        outsystems_url (str): OutSystems environment URL.
        lifetime_token (str): OutSystems API Token.
        source_env (str): Source environment.
        target_env (str): Target environment.
    """
    if not processed_issues:
        print("No applications to deploy.")
        return
    
    # Convert the processed issues into a JSON string
    applications_json = json.dumps(processed_issues)

    # Build the command to execute
    command = [
        'python', 'outsystems/pipeline/deploy_specific_tags_to_target_env.py',
        '-u', outsystems_url,
        '-t', lifetime_token,
        '-s', source_env,
        '-d', target_env,
        '-l', applications_json
    ]
    
    # Execute the deployment command
    try:
        subprocess.run(command, check=True)
        print(f"Deployment plan created successfully for {len(processed_issues)} applications.")
    except subprocess.CalledProcessError as e:
        print(f"Error during deployment: {e}")

def main():
    """
    Main function to handle the workflow:
    1. Parse arguments.
    2. Fetch child issues from Jira.
    3. Process issues and create deployment plan.
    """
    args = get_arguments()
    print(f"Fetching child issues for Epic ID: {args.epic}")

    issues = fetch_child_issues(args.epic, args.jira_token)
    if issues:
        processed_issues = process_issues(issues)
        for issue in processed_issues:
            new_version = tag_new_version(issue["app_name"], outsystems_url, args.lifetime_token)
            if new_version:
                issue["app_version"] = new_version
        create_deployment_plan(processed_issues, outsystems_url, args.lifetime_token, args.source_env, args.target_env)
    else:
        print("No issues retrieved from Jira.")

if __name__ == "__main__":
    main()
