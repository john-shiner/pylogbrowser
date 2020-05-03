
import config
import re

from redis import Redis

# Database Connection
# Database Connection
host = config.REDIS_CFG["host"]
port = config.REDIS_CFG["port"]
pwd = config.REDIS_CFG["password"]
db = config.REDIS_CFG["db"]
redis = Redis(db=db, host=host, port=port, password=pwd, \
              charset="utf-8", decode_responses=True)

pipe = redis.pipeline(transaction=False)

# Store for index-value-logEntry maps as they are created
indexValueMaps = {}

logEntryKeys = redis.keys("logEntry:*")

supportedIndices = ["client_host", "client_id", "client_ip", \
                    "environment", "organization", "proxy", \
                    "proxy_basepath", "proxy_name", \
                    "proxy_revision", "request_path", "request_uri", \
                    "request_verb", "response_reason_phrase", \
                    "response_status_code", "soap_operation", \
                    "soap_siteId", "target_basepath", "target_host", \
                    "target_ip", "virtual_host"]

class IndexMgr:
    def __init__(self, fieldName):
        self.fieldName = fieldName
        self.valueMap = {}
        self.valueSet = set()
    def setadd(self, fieldValue):
        self.valueSet.add(str(fieldValue))
    def add(self, logEntryKey, fieldValue):
        self.valueMap[logEntryKey] = str(fieldValue)


def showLogEntry(logEntryKey="1"):
    print()
    print("**********************")
    print()

    print("logEntry:"+logEntryKey)
    print(redis.hgetall("logEntry:"+logEntryKey))

    print()
    print("**********************")
    print()

def createIndexValueMap(indexName):
    """ Creates a value-to-LogEntry map for the specified indexName"""
    if indexName not in indexValueMaps:
        indexValueMaps[indexName] = IndexMgr(indexName)

        for k in logEntryKeys:
           for rs in redis.hscan_iter(k, match=indexName, count='100'):
                # print("rs[0]=indexName={}".format(rs[0]))
                # print("rs[1]=indexValue={}".format(rs[1]))
                indexValueMaps[indexName].setadd(rs[1])
                le_index = k.split(":")[1]
                if rs[1] in indexValueMaps[indexName].valueMap:
                    indexValueMaps[indexName].valueMap[rs[1]].append(le_index)
                else:
                    indexValueMaps[indexName].valueMap[rs[1]]=[]
                    indexValueMaps[indexName].valueMap[rs[1]].append(le_index) 

    ## If desired, uncomment to persist the valueMap for indexName
    # pipe.sadd("{}_valueSet".format(i), str(indexValueMaps[i].valueSet))
        # for vm in indexValueMaps[i].valueMap:
        #     pipe.lpush("{}:val:{}".format(i,vm), str(indexValueMaps[i].valueMap[vm]))
        # pipe.execute()

def printIndexValueMap(indexName):
    print()
    print("**********************")
    print()
    
    print("{} index with {} values".format(indexName, len(indexValueMaps[indexName].valueSet)))

    for vm in indexValueMaps[indexName].valueMap:
        print("        --> value '{}' is referenced by {} logEntries".format(vm, len(vm)))
    print()
    print("**********************")
    print()

def createAllIndexValueMaps():
    """ Creates a value-to-LogEntry map for the specified indexName"""

    for indexName in supportedIndices:
        indexValueMaps[indexName] = IndexMgr(indexName)

        if indexName not in indexValueMaps:
            indexValueMaps[indexName] = IndexMgr(indexName)

            for k in logEntryKeys:
               for rs in redis.hscan_iter(k, match=indexName, count='100'):
                    # print("rs[0]=indexName={}".format(rs[0]))
                    # print("rs[1]=indexValue={}".format(rs[1]))
                    indexValueMaps[indexName].setadd(rs[1])
                    le_index = k.split(":")[1]
                    if rs[1] in indexValueMaps[indexName].valueMap:
                        indexValueMaps[indexName].valueMap[rs[1]].append(le_index)
                    else:
                        indexValueMaps[indexName].valueMap[rs[1]]=[]
                        indexValueMaps[indexName].valueMap[rs[1]].append(le_index) 

            ## If desired, uncomment to persist the valueMap for indexName
            # pipe.sadd("{}_valueSet".format(i), str(indexValueMaps[i].valueSet))
            # for vm in indexValueMaps[i].valueMap:
            #     pipe.lpush("{}:val:{}".format(i,vm), str(indexValueMaps[i].valueMap[vm]))
            # pipe.execute()

def printAllIndexValueMaps(): 
    print()
    print("**********************")
    print()                   
    print("{} index with {} values".format(indexName, len(indexValueMaps[indexName].valueSet)))

    for vm in indexValueMaps[indexName].valueMap:
        print("        --> value '{}' is referenced by {} logEntries".format(vm, len(vm)))

    print()
    print("**********************")
    print()
    # pipe.sadd("{}_valueSet".format(i), str(indexValueMaps[i].valueSet))
    # for vm in indexValueMaps[i].valueMap:
    #     pipe.lpush("{}:val:{}".format(i,vm), str(indexValueMaps[i].valueMap[vm]))
    # pipe.execute()


def loadLogFile():
    ######################
    # Import Log files
    print("Importing ...")

    count = 0

    # Reference app: gitprojects/logbrowser

    sourcePath = "./data/"
    sourceFileName = "logFile2.log"

    #  parsed array of contents within each logentry field (delimited by "|")
    rawFields = [] 

    #  name{}value pairs for each log entry -- 
    #  no payloads or other fields with "{}" chars in value
    
    fields = {} 
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

def menu():
    while (1):
        for num, indexName in enumerate(supportedIndices):
            print(num, indexName)
        le = num + 1
        print(le, "ShowLogEntry")
        q = le + 1
        print(q, "Quit")
        idx = input("Select indexName's number to view a value analysis:   ")
        if str(idx) == 'q':
            exit()
        elif idx == str(q):
            exit()
        else:
            if int(idx) == le:
                le_idx = input("Enter Log Entry ID:   ")
                showLogEntry(le_idx)
            else:
                createIndexValueMap(supportedIndices[int(idx)])
                printIndexValueMap((supportedIndices[int(idx)]))

        # createIndexValueMap("target_basepath")
        # showLogEntry()

menu()