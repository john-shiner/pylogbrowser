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

sourcePath = "./data/"
sourceFileName = "workfile"

rawFields = [] #  parsed array of contents within each logentry field (delimited by "|")
fields = {} #  name{}value pairs for each log entry -- no payloads or other fields with "{}" chars in value


with open(sourcePath+sourceFileName) as f:

    # Each row is a logEntry
    for rawString in f:
        count = count+1
        logEntryKey = "logEntry:{}".format(count)
        print(logEntryKey)
        # pipe.hset(logEntryKey, "rawString", rawString )

        # Split each logEntry into separate fields
        # Each field is a key-value pair

        rawFields = rawString.split("|")
        # pipe.hset(logEntryKey, "rawFields", str(rawFields) )


        # breakpoint()

        # Handle the first field specially
        i = rawFields[0]
        ii = re.sub(r"^", "timestamp|", i, count=1)
        k, v = ii.split("|")
        pipe.hset(logEntryKey, k, v )
        fields[k] =  v

        # Remove Messy fields
        rawFields.pop(35)
        # rawFields.pop(0)
        rawFields.pop(30)

        for i in range(1 , len(rawFields)):
           # Replace the first ':' character with a '|' to obtain proper k-v split
           j = rawFields[i].replace(":", "|", 1)

           k, v = j.split("|")

           fields[k] = v

           # Populate the logEntryKey hash for each logEntry key-value pair
           pipe.hset(logEntryKey, k, v )

        # More messy fields
        pipe.hset(logEntryKey, "request_content", "PLACEHOLDER")
        pipe.hset(logEntryKey, "response_payload", "PLACEHOLDER")

        pipe.execute()
        # print(fields)
        # c = input("Continue?   ")
        # if c != "y":
        #     exit()

print("Import of {} records completed.".format(count))
