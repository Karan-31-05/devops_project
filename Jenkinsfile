pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    triggers {
        // Polling works for local VM demos when webhook is not reachable from GitHub.
        pollSCM('H/1 * * * *')
    }

    environment {
        DATABASE_URL = 'sqlite:///db.sqlite3'
        APP_PORT = '8000'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Start Server (Simple Deploy)') {
            steps {
                sh '''
                    set -e
                    mkdir -p .logs

                    if ss -ltn | grep -q ":${APP_PORT}"; then
                        echo "Server already running on port ${APP_PORT}; leaving it as-is."
                    else
                        echo "Starting Django server on port ${APP_PORT}."
                        nohup env DATABASE_URL="$DATABASE_URL" python3 manage.py runserver 0.0.0.0:${APP_PORT} > .logs/runserver.log 2>&1 &
                        sleep 3
                    fi

                    ss -ltn | grep ":${APP_PORT}"
                    tail -n 20 .logs/runserver.log || true
                '''
            }
        }
    }

    post {
        success {
            echo 'Push detected and server step completed.'
        }
        failure {
            echo 'Build failed. Check stage logs for details.'
        }
    }
}
