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
    
def tag_versions(processed_issues, outsystems_url, lifetime_token):
    """
    Tag the versions of applications before deployment.

    Args:
        processed_issues (list): List of processed issues with app names and versions.
        outsystems_url (str): OutSystems environment URL.
        lifetime_token (str): OutSystems API Token.
    """
    for issue in processed_issues:
        app_name = issue["app_name"]
        app_version = issue["app_version"]

        if not app_name or not app_version:
            print(f"Skipping tagging for {app_name} due to missing information.")
            continue

        tag_payload = {
            "ApplicationName": app_name,
            "Version": app_version
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {lifetime_token}"
        }

        tag_url = f"{outsystems_url}/lifetimeapi/v2/Applications/Tag"

        try:
            response = requests.post(tag_url, json=tag_payload, headers=headers)
            response.raise_for_status()
            print(f"Successfully tagged {app_name} with version {app_version}.")
        except requests.exceptions.RequestException as e:
            print(f"Error tagging {app_name}: {e}")

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
        tag_versions(processed_issues, outsystems_url, args.lifetime_token)
        create_deployment_plan(processed_issues, outsystems_url, args.lifetime_token, args.source_env, args.target_env)
    else:
        print("No issues retrieved from Jira.")

if __name__ == "__main__":
    main()
