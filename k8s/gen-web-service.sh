kubectl expose deployment web --selector='app=web,tier=frontend' --type=LoadBalancer \
                                     --dry-run --output=yaml > web-flask-service-x.yml