import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description='Ler o parâmetro Epic e buscar Child Issues no Jira.')
    parser.add_argument('--epic', required=True, help='ID do Epic do Jira')
    parser.add_argument('--token', required=True, help='Jira API Token')
    args = parser.parse_args()
    
    JIRA_URL = "https://noesis-devops.atlassian.net"
    JIRA_USER = "rodrigo.r.alcaide@noesis.pt"

    # Child issues request
    jql_query = f"parent={args.epic}"
    search_url = f"{JIRA_URL}/rest/api/2/search?jql={jql_query}"
    
    headers = {"Accept": "application/json"}
    auth = (JIRA_USER, args.token)
    
    response = requests.get(search_url, headers=headers, auth=auth)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Child Issues do Epic {args.epic}:")
        for issue in data.get("issues", []):
            print(f"- {issue['key']}: {issue['fields']['summary']}")
    else:
        print(f"Erro ao procurar child issues: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
