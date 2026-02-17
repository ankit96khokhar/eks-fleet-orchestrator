pipeline {
  agent {
    kubernetes {
      defaultContainer 'terraform'
      idleMinutes 1
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: terraform
    image: terraform-python-venv:local
    imagePullPolicy: IfNotPresent
    command: ["cat"]
    tty: true
"""
    }
  }

  parameters {
    string(
      name: 'TENANT',
      defaultValue: 'tenant-a',
      description: 'Tenant / Business Unit name (example: tenant-a)'
    )

    choice(
      name: 'ENV',
      choices: ['dev', 'staging', 'prod'],
      description: 'Terraform environment'
    )

    choice(
      name: 'REGION',
      choices: ['ap-south-1', 'us-east-1', 'eu-west-1'],
      description: 'AWS region'
    )
    
    choice(
      name: 'ACTION',
      choices: ['plan', 'apply', 'destroy'],
      description: 'Terraform action to perform'
    )

    choice(
      name: 'CONFIRM_DESTROY',
      choices: ['NO', 'YES'],
      description: 'Required for DESTROY'
    )    
  }

  environment {
    TF_IN_AUTOMATION = "true"
    TF_INPUT = "false"
    BLUEPRINT_REPO = 'git@github.com:ankit96khokhar/blueprint-config.git'
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Checkout Blueprint Config Repo') {
      steps {
        dir('blueprints'){
          git(
            url: env.BLUEPRINT_REPO,
            branch: 'main',
            credentialsId: 'github-ssh'            
          )
        }
      }
    }

    stage('Check Tenant Blueprint Exists') {
      steps {
        sh """
          test -f blueprints/tenants/${params.TENANT}/${params.ENV}/${params.REGION}.yaml \
          || (echo "❌ Tenant blueprint not found" && exit 1)
        """
      }
    }

    stage('Run Fleet Orchestrator') {
      steps {
        sh """
          python3 -m app.main \
          blueprints/tenants/${params.TENANT}/${params.ENV}/${params.REGION}.yaml
        """
      }
    }
  }
}
