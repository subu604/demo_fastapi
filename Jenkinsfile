// pipeline {
//     agent any

//     stages {
//         stage('Clone Repo') {
//             steps {
//                 ws('/var/lib/jenkins/projects-hello') {
//                     sh '''
//                         echo "Cloning repository..."
//                         rm -rf demo_fastapi
//                         git clone https://github.com/subu604/demo_fastapi.git
//                         ls -la
//                     '''
//                 }
//             }
//         }

//         stage('Build Docker Image') {
//             steps {
//                 ws('/var/lib/jenkins/projects-hello/demo_fastapi') {
//                     sh '''
//                         echo "Building Docker image..."
//                         docker build -t demo-fastapi:latest .
//                     '''
//                 }
//             }
//         }

//         stage('List Docker Images') {
//             steps {
//                 sh '''
//                     echo "Available Docker Images:"
//                     docker images
//                 '''
//             }
//         }
//     }
// }

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

        stage('Run Docker Container') {
            steps {
                sh '''
                    echo "Stopping old container if exists..."
                    docker rm -f demo-fastapi-container || true

                    echo "Running container on port 8000..."
                    docker run -d -p 8000:8000 --name demo-fastapi-container demo-fastapi:latest
                '''
            }
        }

        stage('List Docker Containers & Images') {
            steps {
                sh '''
                    echo "Running containers:"
                    docker ps

                    echo "Available images:"
                    docker images
                '''
            }
        }
    }
}
