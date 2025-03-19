import requests

LIFETIME_URL = "https://noesisdemos.outsystemscloud.com/lifetimeapi/rest/v2"
LIFETIME_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjY0NjI3ZTNmLWEyYzItNGM0My1iNGU0LTdhMDJjZWU2NDc5NyIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzQyMzk0NTE5Iiwic3ViIjoiWkRnMFl6VTJORE10TXpCbFpTMDBNREF3TFRoaFpqa3RNbVJqWTJFMU5qTm1ObU5qIiwianRpIjoiTUFONjNqTkJ6UyIsImV4cCI6MTgwNTQ2NjUxOSwiaXNzIjoibGlmZXRpbWUiLCJhdWQiOiJsaWZldGltZSJ9.ijITQkGjJO5kfzOVs-mgExVTw577MU1V8jctDHWXlgKPzEyH8jduRs3TtDq_pLGhpQ6DT6bXcpHJBu1BrYhxGpxtJKcCvcV22jGHpNghIRfeeXsAu6PNGfU0kWZn2fVcNVX1MxBxDZd5a8uDSyFVERIHNLgW97lHpMjKjWg-8ApionVpwZ0NrCIC913DIlfT1Yjh1QOeTOnidStx67sCQ5xiBqCbImtu-fgVbqaBNoA-TMxIHUs-kyy7akbUZKHCkLnNei8gsoWf-FtkxRsy5ty749j7SsXuz99ItnaQJjcNkOLJ2h_ZFKj04aMydfgVh5IW8OZhEvUE9gRLDBUerw"
SOURCE_ENV_KEY = "f8de1190-a088-4451-9c2d-8931f71e6998"
TARGET_ENV_KEY = "036f5145-6782-4e8b-92bf-f2cc9694306a"
APPLICATION_KEY = "d353f2c5-de0e-429d-836f-b3859303f5f9"
APPLICATION_VERSION_KEY = "251e8353-1c67-45e3-a389-74590e7d4187"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LIFETIME_TOKEN}"
}

# Criar Deployment Plan
payload = {
    "SourceEnvironmentKey": SOURCE_ENV_KEY,
    "TargetEnvironmentKey": TARGET_ENV_KEY,
    "Applications": [{
        "Key": APPLICATION_KEY,
        "VersionKey": APPLICATION_VERSION_KEY
    }]
}

print("Creating deployment plan")
response = requests.post(f"{LIFETIME_URL}/deployments", json=payload, headers=headers)

if response.status_code == 200:
    deployment_plan_key = response.json().get("DeploymentPlanKey")
    print(f"Deployment Plan criado! Key: {deployment_plan_key}")
else:
    print(f"Erro ao criar Deployment Plan: {response.text}")
    exit(1)

# Iniciar Deployment ignorando conflitos
start_payload = {"IgnoreWarnings": True}
print("Iniciando Deployment...")
start_response = requests.post(f"{LIFETIME_URL}/deployments/{deployment_plan_key}/start", json=start_payload, headers=headers)

if start_response.status_code == 200:
    print("Deployment iniciado com sucesso!")
else:
    print(start_response.text)
    exit(1)

# Status do Deployment
print("status do Deployment...")
while True:
    status_response = requests.get(f"{LIFETIME_URL}/deployments/{deployment_plan_key}/status", headers=headers)
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        status = status_data.get("Status")
        print(f"Status atual: {status}")
        
        if status in ["Completed", "Failed"]:
            break
    else:
        print(f"Erro ao obter status: {status_response.text}")
        break

print("Processo finalizado!")
