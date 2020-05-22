# Fun with docker-compose, k8s, python3, flask, redis

Application:  Flask app to process log files into redis data structures for web log analysis.
Development:  Uses the 'Invoke' library to create convenience commands for service deployment, etc.
Platform:  Kubernetes (yaml files under k8s/ folder)

## Files/Usage

* app.py == flask web app using LogBrowser module for services

* Dockerfile ==  builds that app as a container (based on python 3.8 image)

* docker-compose.yml == assembles the flask and redis containers into an application

* LogBrowser.py == the processor loading, parsing, and storing LogFiles into Redis data structures

* tasks.py == Command-line tools exposed with the 'invoke' library.  Commands are summarized below.

## Docker-Compose Dev Deployment (not prod) Usage:

* docker-compose build  # build the containers in the docker-compose file

* docker-compose up  # add -d to run detached (in background)

* docker-compose stop  # stop the app, leave the containers

* docker-compose down  # stop the app, remove the containers (not the images)

Open/refresh http://localhost:8000 to see the app

## Minikube (kubernetes) Dev Deployment

##### Assumes a running minikube platform

Basic command support to deploy and undeploy a flask app (web) running against a redis db.  The web application can be scaled up or down to a desired number of instance pods.  

After running the deploy command, run 'minikube services' to get exposed ports

#### Primary k8s convenience commands

Run these from the project root directory (in the tasks.py folder:

*  deploy     - Run this to deploy the application stack to minikube
*  undeploy   - Run this to remove (all) the application stack(s) from minikube
*  scale -n <#web replicas> - Scale the web pods to the desired number of replicas
*  webport    - Run this to return the exposed port for the web service
*  db         - Output of this command is a parameterized Redis-cli command string
*  build      - Task chain Build docker image, store in dockerhub, deploy to k8s

## Invoke (inv) commands (reference)

Example usage:  inv undeploy rmi build deploy

* <b>build </b> Build the web docker image
* <b> clean-deploy	</b> Undeploy, remove the web docker image from local registry, build a web docker image, and deploy
* <b>   dash  </b>         Run this to launch the minikube dashboard
* <b>   db  </b>           Run the output of this command for a parameterized Redis-cli command string
* <b>   dbport  </b>       Run this to return the exposed port for the redis service
* <b>   deploy </b>        Run this to deploy the application stack to minikube
* <b>   gh  </b>           Open the current github branch on GitHub
* <b>   push   </b>        Run the bin/push-to-dockehub script -- requires env vars
* <b>   rmi  </b>          Remove the web image from local (minikube) docker registry
* <b>   scale </b>         Run this to scale the web pods to <num> replicas
* <b>   st    </b>         Open the current repository in Sublime Text
* <b>   undeploy  </b>     Run this to remove (all) the application stack(s) from minikube
* <b>   usage  </b>        Example:  inv undeploy rmi build deploy
* <b>   web   </b>         Launch the minikube hosted 'web' service to run the deployed application
* <b>   webport  </b>      Run this to return the exposed port for the web service