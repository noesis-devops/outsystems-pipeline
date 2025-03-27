pipeline {
    agent {
        kubernetes {
            idleMinutes 1
            defaultContainer 'node'
            yaml """
            apiVersion: v1
            kind: Pod
            spec:
              containers:
                - name: node
                  image: python:3.9
                  command:
                    - cat
                  tty: true
            """
        }
    }
    environment {
        JIRA_URL = 'https://noesis-devops.atlassian.net'
        JIRA_USER = 'rodrigo.r.alcaide@noesis.pt'
        outsystems_url = "https://noesisdemos.outsystemscloud.com"
    }
    stages {
        
        stage('Get Jira Issues') {
            steps {
                script {
                    echo "Jira Epic: ${params.epic}"
                }
            }
        }
        
        stage('Clone Repository') {
            steps {
                git branch: 'master', credentialsId: 'github-credentials', url: 'https://github.com/noesis-devops/outsystems-pipeline.git'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Create Deployment Plan') {
            steps {
                withCredentials([string(credentialsId: 'jira', variable: 'JIRA_TOKEN'), 
                                 string(credentialsId: 'lifetime', variable: 'LIFETIME_TOKEN')]) {
                    sh """ 
                        python3 request.py \
                        --epic "${params.epic}" \
                        --jira_token "${JIRA_TOKEN}" \
                        --lifetime_token "${LIFETIME_TOKEN}" \
                        --source_env "${params.source_environment}" \
                        --target_env "${params.target_environment}" \
                        --outsystems_url "${outsystems_url}" \
                        --jira_user "${JIRA_USER}" \
                        --jira_url "${JIRA_URL}"
                        
                    """
                }
            }
        }
    }
}
