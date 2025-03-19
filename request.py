import argparse

def main():
    parser = argparse.ArgumentParser(description='Ler e imprimir o parâmetro Epic.')
    parser.add_argument('--epic', required=True, help='ID do Epic do Jira')
    args = parser.parse_args()
    
    print(f"Recebido Epic: {args.epic}")

if __name__ == "__main__":
    main()
