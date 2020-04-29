import csv
import config

from redis import Redis

# Database Connection
host = config.REDIS_CFG["host"]
port = config.REDIS_CFG["port"]
pwd = config.REDIS_CFG["password"]
db = config.REDIS_CFG["db"]
redis = Redis(db=db, host=host, port=port, password=pwd, charset="utf-8", decode_responses=True)
pipe = redis.pipeline(transaction=False)

# Import Log files
print("Importing ...")

count = 0

with open('data/workfile') as f:


    for read_data in f:
        count = count+1
        logEntryKey = "logEntry:{}".format(count)
        print(logEntryKey)       
        lst = read_data.split("|")
        # print(lst)
        lst.pop(35)
        lst.pop(0)
        lst.pop(30)
        for i in lst:

           j = i.replace(":", "|", 1)

           k, v = j.split("|")
           # print("k = {}, v = {}".format(k, v))
           pipe.hset(logEntryKey, k, v )
        pipe.execute()


print("Import of {} records completed.".format(count))
