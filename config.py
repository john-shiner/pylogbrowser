REDIS_DESKTOP= {
    "env" : "dev",
    "host" : "127.0.0.1",
    "port" : 6379,
    "password" : "",
    "db" : "0",
} 

# use k8s dns
REDIS_K8S = {
    "env" : "integration",
    "host" : "redis",
} 
