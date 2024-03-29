#!/usr/bin/python3
"""Run these tasks from the project directory"""

# point to the appropriate project yml files

from invoke import task
import os

import os
stream = os.popen('pwd')
output = stream.read()
inv_path = output.strip()

os.environ["INV_PATH"]=inv_path

redis_depl = "$INV_PATH/k8s/redis-deployment.yml"
redis_svc = "$INV_PATH/k8s/redis-service.yml"
web_depl = "$INV_PATH/k8s/web-flask-deployment.yml"
web_svc = "$INV_PATH/k8s/web-flask-service.yml"
tasks_log = "$INV_PATH/k8s/log.txt"

# @task
# def genredisyml(c):
#     "try out better use of yaml lables"
    # kubectl run db --image=redis --replicas=1 --port=6379 \
    #                         --labels='app=redis,tier=backend' \
    #                         --dry-run --output=yaml > new-redis-deployment-xx2.yaml
@task
def usage(c):
    "Example:  inv undeploy rmi build deploy"
    c.run("echo Make changes, then run the following to try them out")
    c.run("echo Example:  inv undeploy rmi build deploy")

@task
def gh(c):
    "Open the current github branch on GitHub"
    c.run("open $(git remote -v | cut -f 1 -d ' ' |cut -f 2 | sed 1d | cut -d '.' -f1-2)/tree/$(git rev-parse --abbrev-ref HEAD)")
   
@task
def rmi(c):
    "Remove the web image from local (minikube) docker registry"
    c.run("eval $(minikube docker-env)")
    c.run("docker rmi johnshiner/frontend:v1")

@task
def push(c):
    "Run the bin/push-to-dockehub script -- requires env vars"
    c.run("eval $(minikube docker-env)")
    c.run("./bin/push_flask-redis-frontend")

@task
def build(c):
    "Build the web docker image"
    c.run("eval $(minikube docker-env)")
    c.run("docker build -t johnshiner/frontend:v1 .")

@task
def deploy_all(c):
    "Run this to deploy the application stack to minikube"

    # kubectl expose deployment db --selector='app=redis,tier=backend' \
    #                             --dry-run --output=yaml > new-redis-service.yaml

    # redis_depl - uncomment next two lines to install a new version 
    c.run("eval $(minikube docker-env)")

    c.run("kubectl create -f {}".format(redis_depl))
    c.run("kubectl create -f {}".format(redis_svc))

    c.run("kubectl create -f {}".format(web_depl))
    c.run("kubectl create -f {}".format(web_svc))

    c.run("minikube service list")

    c.run("date >> {}".format(tasks_log))
    c.run("minikube service list >> {}".format(tasks_log))
    c.run("minikube service web")

@task
def clean_deploy(c):
    "Undeploy, remove the web docker image from local registry, build a web docker image, and deploy"
    c.run("eval $(minikube docker-env)")
    c.run("kubectl delete all --all")

    c.run("inv rmi")
    c.run("inv build")
    # c.run("inv push")
    c.run("inv deploy-all")

@task
def st(c):
    "Open the current repository in Sublime Text"
    c.run("subl $INV_PATH")
    
@task
def deploy(c):
    "Run this to deploy the application stack to minikube"

    # kubectl expose deployment db --selector='app=redis,tier=backend' \
    #                             --dry-run --output=yaml > new-redis-service.yaml

    # redis_depl - uncomment next two lines to install a new version 
    c.run("eval $(minikube docker-env)")

    # c.run("kubectl create -f {}".format(redis_depl))
    # c.run("kubectl create -f {}".format(redis_svc))

    c.run("kubectl create -f {}".format(web_depl))
    c.run("kubectl create -f {}".format(web_svc))

    c.run("minikube service list")

    c.run("date >> {}".format(tasks_log))
    c.run("minikube service list >> {}".format(tasks_log))
    c.run("minikube service web")


@task 
def undeploy(c):
    "Run this to remove (all) the application stack(s) from minikube"

    # use delete all to change redis versions
    c.run("kubectl delete service web")
    c.run("kubectl delete deployment web")

    # c.run("kubectl delete all --all")

    c.run("date >> {}".format(tasks_log))
    c.run("echo 'removed app' >> {}".format(tasks_log))
    c.run("date >> {}".format(tasks_log))
    c.run("echo 'removed web' >> {}".format(tasks_log))
    c.run("echo to remove all, use 'kubectl delete all --all'")
    c.run("kubectl get pods >> {}".format(tasks_log))

@task
def scale(c, num=3):
    "Run this to scale the web pods to <num> replicas"
    str = "kubectl scale --replicas={} deployment web".format(num)
    c.run(str)
    c.run("date >> {}".format(tasks_log))
    str = "echo scaled web nodes to {} >> {}".format(num, tasks_log)
    c.run(str)
    c.run("kubectl get pods >> {}".format(tasks_log))

@task
def db(c):
    "Run the output of this command for a parameterized Redis-cli command string"
    str = "        redis-cli -h $(minikube ip) -p $(kubectl get service redis --output='jsonpath={.spec.ports[0].nodePort}')"
    c.run("echo {}".format(str))

    # c.run(str)

@task
def dbport(c):
    "Run this to return the exposed port for the redis service"
    str = "kubectl get service redis --output='jsonpath={.spec.ports[0].nodePort}'"
    print("----")
    c.run(str)
    print("    ")
    print("    ")

@task
def webport(c):
    "Run this to return the exposed port for the web service"
    str = "kubectl get service web --output='jsonpath={.spec.ports[0].nodePort}'"
    print("----")
    c.run(str)
    print("    ")
    print("    ")

@task
def dash(c):
    "Run this to launch the minikube dashboard"
    str = "minikube dashboard"
    c.run(str)
    
@task
def web(c):
    "Launch the minikube hosted 'web' service to run the deployed application"
    c.run("minikube service web")
