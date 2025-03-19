import argparse
import requests

# Constants
JIRA_URL = "https://noesis-devops.atlassian.net"
JIRA_USER = "rodrigo.r.alcaide@noesis.pt"

def get_arguments():
    """
    Parse command-line arguments for Epic ID and Jira API Token.
    Returns:
        args (Namespace): Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch child issues from a Jira Epic.')
    parser.add_argument('--epic', required=True, help='ID of the Jira Epic')
    parser.add_argument('--jira_token', required=True, help='Jira API Token')
    parser.add_argument('--lifetime_token', required=True, help='Lifetime API Token')
    return parser.parse_args()

def fetch_child_issues(epic_id, token):
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
    auth = (JIRA_USER, token)

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
            "App": issue['fields'].get('description', "No description available for this issue."),
            "Version": issue['fields'].get('customfield_10055', "No version available for this issue.")
        }
        processed_issues.append(issue_data)
    return processed_issues

def display_issues(processed_issues):
    """
    Display processed issues data in a readable format.

    Args:
        processed_issues (list): List of processed issues.
    """
    if not processed_issues:
        print("No child issues found for this Epic.")
        return

    print("Processed Child Issues:")
    for issue in processed_issues:
        print(f"- App: {issue['App']}, Version: {issue['Version']}")

def main():
    """
    Main function to handle the workflow:
    1. Parse arguments.
    2. Fetch child issues from Jira.
    3. Process and display issues.
    """
    args = get_arguments()
    print(f"Fetching child issues for Epic ID: {args.epic}")

    issues = fetch_child_issues(args.epic, args.jira_token)
    if issues:
        processed_issues = process_issues(issues)
        display_issues(processed_issues)
    else:
        print("No issues retrieved from Jira.")

if __name__ == "__main__":
    main()
