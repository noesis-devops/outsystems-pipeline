pipeline {
    agent any
    
    stages {
        stage('Request Jira') {
            steps {
                script {
                    def responseData = jiraJqlSearch(
                        site: 'https://noesis-devops.atlassian.net',
                        jql: 'parent = LFTJIRA-52 and status = "Ready for Prd"'
                    )
                    
                    if (responseData) {
                        def issuesData = []
                        
                        if (responseData.data.issues) {
                            responseData.data.issues.each { issue ->
                                def issueData = [:]
                                
                                //issueData['Key'] = issue.key
                                
                                if (issue.fields.description) {
                                    issueData['App'] = issue.fields.description
                                } else {
                                    issueData['App'] = "Nenhuma descrição disponível para este problema."
                                }
                                
                                if (issue.fields.customfield_10055) { 
                                    issueData['Version'] = issue.fields.customfield_10055
                                } else {
                                    issueData['Version'] = "Nenhuma versão disponível para este problema."
                                }
                                
                                issuesData.add(issueData)
                            }
                        } else {
                            echo "Nenhum problema encontrado."
                        }
                        
                        issuesData.each { issue ->
                            //echo "Key: ${issue['Key']}"
                            echo "App: ${issue['App']}"
                            echo "Version: ${issue['Version']}"
                        }
                    } else {
                        echo "Nenhum dado retornado pela consulta JQL."
                    }
                }
            }
        }
        stage('Check if Python3 is installed'){
            steps {
                script {
                    def python3Installed = powershell(returnStatus: true, script: 'python --version')
                    if (python3Installed == 0) {
                        echo 'Python 3 está instalado.'
                    } else {
                        echo 'Python 3 não está instalado. A instalar'
                        powershell 'choco install python'
                    }
                }
            }
        }
        stage('Upgrade Pip') {
            steps {
                bat 'python.exe -m pip install --upgrade pip'
            }
        }
        stage('Verificar instalação do setuptools') {
            steps {
                script {
                    def setuptoolsInstalled = sh(script: 'pip show setuptools', returnStatus: true)
                    if (setuptoolsInstalled == 0) {
                        echo 'Setuptools está instalado.'
                    } else {
                        echo 'Setuptools não está instalado. A istalar...'
                        sh 'pip install setuptools'
                        setuptoolsInstalled = sh(script: 'pip show setuptools', returnStatus: true)
                        if (setuptoolsInstalled == 0) {
                            echo 'Setuptools foi instalado com sucesso.'
                        } else {
                            echo 'Erro ao instalar o setuptools.'
                        }
                    }
                }
            }
        }
        stage('Install requests module') {
            steps {
                script {
                    def installed = bat(script: 'pip show requests > nul 2>&1', returnStatus: true)
                    if (installed != 0) {
                        bat 'pip install requests'
                    } else {
                        echo 'O modulo requests ja esta instalado.'
                    }
                }
            }
        }
        stage('Install dotenv module') {
            steps {
                script {
                    def installedDotenv = bat(script: 'pip show python-dotenv > nul 2>&1', returnStatus: true)
                    if (installedDotenv != 0) {
                        bat 'pip install python-dotenv'
                    } else {
                        echo 'O modulo dotenv ja esta instalado.'
                    }
                }
            }
        }
        stage('Criar Deployment Plan da App OutSystems') {
            steps {
                script {
                    def changeDirCommand = 'cd outsystems-pipeline-master'
        
                    bat(script: changeDirCommand, returnStatus: true)
        
                    def pythonCommand = 'python outsystems/pipeline/deploy_specific_tags_to_target_env.py -u https://noesisdemos.outsystemscloud.com -t eyJhbGciOiJSUzI1NiIsImtpZCI6IjY0NjI3ZTNmLWEyYzItNGM0My1iNGU0LTdhMDJjZWU2NDc5NyIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzExNjI3MjM4Iiwic3ViIjoiWkRnMFl6VTJORE10TXpCbFpTMDBNREF3TFRoaFpqa3RNbVJqWTJFMU5qTm1ObU5qIiwianRpIjoiaHM4dzhhWmpjVCIsImV4cCI6MTc0MzE2MzIzOCwiaXNzIjoibGlmZXRpbWUiLCJhdWQiOiJsaWZldGltZSJ9.Q_TYTicDsEvMRzcVNFbg2YsK7lGIjJuAk33BnvUG9SYwzddA-n1WRwxk2rdFK6huJcmadQvemkZtdab9dYMk-VYv2rcBqYRC9fflnSVU0AKMHZGMrY1goNT5X1t30otr02Aalg4zOLCRn7y-11_muGaEHcphi78BNrSoFgKkLSOCO8YBuxRb40UK-y_iHlravJ7Av3TuVYxgglJZ1k-pHkalo8BRwaO4d0BkLGaSDvS5ZoF_sRWspLW7TWaHc8qPt3AX7NX_mpELxihhsz0KfEE_jnH2wm4nla-o199acYPVhNGCTwkVjetQYM0jbcn5j7_G9SyTjR4OG6aw5DOcqw -s Development -d Production -l \'[{"app_name": "Lifetime - jira App1", "app_version": "2.0"}]\''
        
                    def result = bat(script: pythonCommand, returnStatus: true)
        
                    if (result == 0) {
                        echo 'Deployment Plan criado com sucesso.'
                    } else {
                        echo 'Erro ao criar Deployment Plan.'
                    }
                }
            }
        }
    }
}
