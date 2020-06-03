kubectl run web --image=$DOCKER_LOGIN/frontend:v1 --replicas=1 --port=5000 \
                      --labels='app=web,tier=frontend' \
                      --env="GET_HOSTS_FROM=dns" \
                      --dry-run --output=yaml > web-flask-deployment2.yml
