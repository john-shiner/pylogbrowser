import csv
import config
import re

from redis import Redis

# Database Connection
host = config.REDIS_CFG["host"]
port = config.REDIS_CFG["port"]
pwd = config.REDIS_CFG["password"]
db = config.REDIS_CFG["db"]
redis = Redis(db=db, host=host, port=port, password=pwd, charset="utf-8", decode_responses=True)

# Populate the logEntry hash structures in a server-side batch pipeline
pipe = redis.pipeline(transaction=False)

# Import Log files
print("Importing ...")

count = 0

# Reference app: gitprojects/logbrowser

with open('data/workfile') as f:

    # Each row is a logEntry
    for read_data in f:
        count = count+1
        logEntryKey = "logEntry:{}".format(count)
        print(logEntryKey)

        # Split each logEntry into separate fields
        # Each field is a key-value pair

        lst = read_data.split("|")

        # breakpoint()

        # Handle the first field specially
        i = lst[0]
        ii = re.sub(r"^", "timestamp|", i, count=1)
        k, v = ii.split("|")
        pipe.hset(logEntryKey, k, v )

        # Messy fields
        # lst.pop(35)
        # lst.pop(0)
        # lst.pop(30)

        for i in range(1 , len(lst)):
           # Replace the first ':' character with a '|' to obtain proper k-v split
           j = lst[i].replace(":", "|", 1)

           k, v = j.split("|")

           # Populate the logEntryKey hash for each logEntry key-value pair
           pipe.hset(logEntryKey, k, v )
        pipe.execute()

print("Import of {} records completed.".format(count))
