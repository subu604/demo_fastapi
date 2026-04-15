pipeline {
    agent any

    stages {
        stage('Clone Repo') {
            steps {
                ws('/var/lib/jenkins/projects-hello') {
                    sh '''
                        echo "Cloning repository..."
                        rm -rf demo_fastapi
                        git clone https://github.com/subu604/demo_fastapi.git
                        ls -la
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                ws('/var/lib/jenkins/projects-hello/demo_fastapi') {
                    sh '''
                        echo "Building Docker image..."
                        docker build -t demo-fastapi:latest .
                    '''
                }
            }
        }

        stage('List Docker Images') {
            steps {
                sh '''
                    echo "Available Docker Images:"
                    docker images
                '''
            }
        }
    }
}
