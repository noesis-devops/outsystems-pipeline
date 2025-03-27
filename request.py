import argparse
import requests
import json
import subprocess

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
    parser.add_argument('--outsystems_url', required=True, help='outsystems url')
    parser.add_argument('--jira_user', required=True, help='Jira user')
    parser.add_argument('--jira_url', required=True, help='Jira url')
    return parser.parse_args()

def fetch_child_issues(epic_id, jira_token, jira_url, jira_user):
    """
    Fetch child issues of a given Jira Epic using the Jira API.

    Args:
        epic_id (str): ID of the Jira Epic.
        token (str): Jira API Token.

    Returns:
        list: List of issues retrieved from Jira.
    """
    jql_query = f"parent={epic_id}"
    search_url = f"{jira_url}/rest/api/2/search?jql={jql_query}"
    headers = {"Accept": "application/json"}
    auth = (jira_user, jira_token)

    try:
        response = requests.get(search_url, headers=headers, auth=auth)
        response.raise_for_status()
        data = response.json()
        return data.get("issues", [])
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Jira: {e}")
        return []
        
def create_tag_for_applications(outsystems_url, lifetime_token, source_env, target_env, app_list=None, manifest_file=None, log_msg="Version created automatically using outsystems-pipeline package."):
    """
    Calls the script to create tags for the applications using the provided parameters.

    Args:
        outsystems_url (str): URL for the OutSystems environment.
        lifetime_token (str): API token for the LifeTime API.
        source_env (str): Source environment (e.g., Development).
        target_env (str): Target environment (e.g., Production).
        app_list (list, optional): List of applications to tag.
        manifest_file (str, optional): Path to the manifest file.
        log_msg (str, optional): Log message for the tags.
    """
    if not app_list and not manifest_file:
        print("Either app_list or manifest_file must be provided.")
        return

    # Prepare the command to execute the script for tags
    command = [
        'python', 'outsystems/pipeline/tag_modified_apps.py',
        '-u', outsystems_url,
        '-t', lifetime_token,
        '-s', source_env,
        '-d', target_env,
        '-l', log_msg
    ]

    if app_list:
        command.extend(['-a', ','.join(app_list)])
    elif manifest_file:
        command.extend(['-f', manifest_file])

    try:
        subprocess.run(command, check=True)
        print(f"Tags for applications in environment '{target_env}' have been created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating tags: {e}")

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

    issues = fetch_child_issues(args.epic, args.jira_token, args.jira_url, args.jira_user)
    if issues:
        processed_issues = process_issues(issues)
        create_tag_for_applications(
            outsystems_url=args.outsystems_url,
            lifetime_token=args.lifetime_token,
            source_env=args.source_env,
            target_env=args.target_env,
            app_list=[issue['app_name'] for issue in processed_issues],  # Usando os nomes dos aplicativos processados
            log_msg="Version created automatically before deployment."
        )
        create_deployment_plan(processed_issues, args.outsystems_url, args.lifetime_token, args.source_env, args.target_env)
    else:
        print("No issues retrieved from Jira.")

if __name__ == "__main__":
    main()
