# Minimal app with docker-compose, k8s, python3, flask, redis

app.py == minimal python flask/redis web app

To check code quality locally, you can run flake in a container:
* alias flake="docker run -ti --rm -v $(pwd):/apps alpine/flake8:3.5.0"
* flake --help
* flake app.py

Dockerfile ==  builds that app as a container (based on python 3.8 image)

docker-compose.yml == assembles the flask and redis containers into an application

Usage:

* docker-compose build  # build the containers in the docker-compose file

* docker-compose up  # add -d to run detached (in background)

* docker-compose stop  # stop the app, leave the containers

* docker-compose down  # stop the app, remove the containers (not the images)

Open/refresh http://localhost:8000 to see the app

## Kubernetes (minikube)

### Minikube deployment commands (run from k8s directory)

Invoke (inv) commands

*  dash       - Run this to launch the minikube dashboard
*  db         - Output of this command is a parameterized Redis-cli command string
*  dbport     - Run this to return the exposed port for the redis service
*  deploy     - Run this to deploy the application stack to minikube
*  gh         - Open the current github branch on GitHub
*  scale -n <#web replicas> - Scale the web pods to the desired number of replicas
*  st         - Open the current repository in Sublime Text
*  undeploy   - Run this to remove (all) the application stack(s) from minikube
*  webport    - Run this to return the exposed port for the web service

After running the deploy command, run 'minikube services' to get exposed ports

