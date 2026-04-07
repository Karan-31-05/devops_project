pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    triggers {
        // Polling works for local VM demos when webhook is not reachable from GitHub.
        pollSCM('H/2 * * * *')
    }

    environment {
        DATABASE_URL = 'sqlite:///db.sqlite3'
        VENV_DIR = '.venv_jenkins'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    set -e
                    python3 -m venv "$VENV_DIR"
                    "$VENV_DIR/bin/python" -m pip install --upgrade pip
                    "$VENV_DIR/bin/python" -m pip install -r requirements.txt
                '''
            }
        }

        stage('Build / Validate') {
            steps {
                sh '''
                    set -e
                    "$VENV_DIR/bin/python" manage.py migrate --noinput
                    "$VENV_DIR/bin/python" manage.py check
                '''
            }
        }

        stage('Package Artifact') {
            steps {
                sh '''
                    set -e
                    mkdir -p build
                    tar -czf build/erp-${BUILD_NUMBER}.tar.gz \
                        --exclude='.git' \
                        --exclude="$VENV_DIR" \
                        .
                '''
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'build/*.tar.gz', fingerprint: true
            echo 'Build succeeded and artifact archived.'
        }
        failure {
            echo 'Build failed. Check stage logs for details.'
        }
        always {
            cleanWs()
        }
    }
}
