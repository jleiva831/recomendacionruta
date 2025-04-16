pipeline {
    agent any

    stages {
        stage('Preparar Entorno') {
            steps {
                echo 'Preparando el entorno...'
                sh 'python -m venv venv'
                sh './venv/Scripts/pip install -r requirements.txt'
            }
        }

        stage('Ejecutar Pruebas') {
            steps {
                echo 'Ejecutando pruebas...'
                sh './venv/Scripts/pytest'
            }
        }

        stage('Construir Imagen Docker') {
            steps {
                echo 'Construyendo la imagen Docker...'
                sh 'docker build -t gps-app:latest .'
            }
        }

        stage('Desplegar Contenedor') {
            steps {
                echo 'Desplegando la aplicación en un contenedor...'
                sh 'docker run -d -p 5000:5000 --name gps-app gps-app:latest'
            }
        }
    }

    post {
        always {
            echo 'Limpieza del entorno...'
            sh 'docker stop gps-app || true'
            sh 'docker rm gps-app || true'
            sh 'docker rmi gps-app:latest || true'
        }
    }
}