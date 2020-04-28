#! /bin/sh

# alias redis-cli="redis-cli -h $(minikube ip) -p $(kubectl get service redis --output='jsonpath={.spec.ports[0].nodePort}')"

redis-cli -h $(minikube ip) -p $(kubectl get service redis --output='jsonpath={.spec.ports[0].nodePort}')

