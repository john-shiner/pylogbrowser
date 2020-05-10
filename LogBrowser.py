import re
import config
from redis import Redis
import os


# Desktop
host = config.REDIS_DESKTOP["host"]
port = config.REDIS_DESKTOP["port"]
pwd = config.REDIS_DESKTOP["password"]
db = config.REDIS_DESKTOP["db"]
redis = Redis(db=db, host=host, port=port, password=pwd,
              charset="utf-8", decode_responses=True)

# # Kubernetes Deployment
# redis = Redis(host="redis", charset="utf-8", decode_responses=True)

pipe = redis.pipeline()

# logEntryKeys = redis.keys("logEntry:*")

class IndexMgr:
    indexValueManagers = {}

    def __init__(self, fieldName):
        self.fieldName = fieldName
        self.valueMap = {}
        self.valueSet = set()

        IndexMgr.indexValueManagers[fieldName] = self
    def setadd(self, fieldValue):
        ivm = IndexMgr.indexValueManagers
        mgr = ivm[self.fieldName]
        vs = mgr.valueSet
        vs.add(str(fieldValue).strip())
    def maple(self, fieldValue, logEntryKey):
        ivm = IndexMgr.indexValueManagers
        mgr = ivm[self.fieldName]
        vm = mgr.valueMap

        if fieldValue in vm.keys():
            vm[fieldValue].append(str(logEntryKey))
        else:
            vm[fieldValue] = []
            vm[fieldValue].append(str(logEntryKey))

# class LogBrowser(redisInstance):
#     redis = redisInstance

class LogBrowser:
    _instance = None
    # import lb_command

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.indexValueManagers = {}
            cls._instance.createAllIndexValueMaps()

        return cls._instance

    supportedIndices = ["client_host", "client_id", "client_ip", \
                        "environment", "organization", "proxy", \
                        "proxy_basepath", "proxy_name", \
                        "proxy_revision", "request_path", "request_uri", \
                        "request_verb", "response_reason_phrase", \
                        "response_status_code", "soap_operation", \
                        "soap_siteId", "target_basepath", "target_host", \
                        "target_ip", "virtual_host"]

    # Store for index-value-logEntry maps as they are created
    def indexValueMaps():
        return IndexMgr.indexValueManagers

    def logEntryCount(self):
        return len(self.logEntries())

    def logEntries(self):
        self._logEntries = {}
        for d in redis.scan_iter(match="logEntry:*", count='100'):
            self._logEntries[d] = redis.hgetall(d)
        return self._logEntries

    def logEntryKeys(self):
        self._logEntries = self.logEntries()
        return self._logEntries.keys()

    def analysis_page_content(self):

        ivm = IndexMgr.indexValueManagers

        page_content = ""
        for i in self.supportedIndices:
            mgr = ivm[i]
            vm = mgr.valueMap
            vs = mgr.valueSet
            page_content +="<h4>{}</h4>".format(i)
            page_content +="<ul>"
            # breakpoint()
            for j in vm.keys():
                page_content += "<li>Value '{}' mapped to {} logEntries</li>".format(j, len(vm[j]))
                page_content += "<p>---> mapped logEntries -----    "
                page_content += "map:{}:{}</p>".format(i, j)
            page_content +="</ul>"
        return page_content

    def createAllIndexValueMaps(self):
        """ Creates a value-to-LogEntry map for the specified indexName"""
        IndexMgr.indexValueManagers = {}
        for indexName in self.supportedIndices:
            indexMgr = IndexMgr(indexName)
            self.loadIndexValueMap(indexName)

    def loadIndexValueMap(self, indexName):
        """ Creates a value-to-LogEntry map for the specified indexName"""

        indexMgr = IndexMgr.indexValueManagers[indexName]

        # scan the logEntries that have been loaded 

        for le in redis.scan_iter(match="logEntry:*", count='100'):
            v = redis.hget(le, indexName)

            fieldVal = v
            if len(fieldVal) == 0:
                fieldVal="None"

            indexMgr.setadd(fieldVal)

            indexMgr.maple(fieldVal, le)

        vm = indexMgr.valueMap
        # breakpoint()
        # pipe.set("idx:{}".format(indexName), vm)
        # print("idx:{}".format(indexName))

        for i in vm.keys():
            storable = [ int(x.split(":")[1]) for x in vm[i]]
            pipe.set("idx:{}:{}".format(indexName, i), "map:{}:{}".format(indexName, i) )
            # print("idx:{}:{}".format(indexName, i))
            pipe.set("map:{}:{}".format(indexName, i), str(sorted(storable)))
            # print("map:{}:{}".format(indexName, i))
        pipe.execute()

    def getLoadedFiles(self):
        return sorted(redis.smembers("loadedLogFiles"))

    def loadLogFile(self, filePath):
        ###################### filePath = directory + filename
        # Import Log files
        print("Importing ...")
        if filePath in self.getLoadedFiles():
            print("File {} is already loaded".format(filePath))
            return

        le_count = self.logEntryCount()

        # Reference app: gitprojects/logbrowser

        # sourcePath = filePath
        sourceFileName = filePath

        #  parsed array of contents within each logentry field (delimited by "|")
        rawFields = [] 

        #  name{}value pairs for each log entry -- 
        #  no payloads or other fields with "{}" chars in value
        
        fields = {} 
        with open(sourceFileName) as f:

            # Each row is a logEntry
            for rawString in f:
                le_count = le_count+1
                logEntryKey = "logEntry:{}".format(le_count)

                # print(logEntryKey)

                # Split each logEntry into separate fields
                # Each field is a key-value pair

                rawFields = rawString.strip().split("|")
                # pipe.hset(logEntryKey, "rawFields", str(rawFields) )

                # Handle the first field specially
                i = rawFields[0]
                ii = re.sub(r"^", "timestamp|", i, count=1)
                k, v = ii.split("|")
                pipe.hset(logEntryKey, k, v )
                fields[k] =  v
                # print(k,v)

                # Remove Messy fields
                rawFields.pop(35)
                # rawFields.pop(0)
                rawFields.pop(31)

                for i in range(1 , len(rawFields)):
                    # Replace the first ':' character with a '|' to obtain proper k-v split
                    j = rawFields[i].replace(":", "|", 1)
                    jj = j.replace(":", "-")
                    k, v = j.split("|")

                    indexName = k.strip()

                    fields[k] = v.strip()

                    # Populate the logEntryKey hash for each logEntry key-value pair
                    pipe.hset(logEntryKey, k, v )

                    # # Populate the IndexMgr data
                    # fieldVal = v

                    # if len(fieldVal) == 0:
                    #     fieldVal="None"

                    # if indexName in self.supportedIndices:
                    #     indexMgr = IndexMgr.indexValueManagers[indexName]

                    #     indexMgr.setadd(fieldVal)

                    #     indexMgr.maple(fieldVal, logEntryKey)
                    # More messy fields
                    pipe.hset(logEntryKey, "request_content", "PLACEHOLDER")
                    pipe.hset(logEntryKey, "response_payload", "PLACEHOLDER")
                    pipe.hset(logEntryKey, "logFileName", sourceFileName)
                    pipe.sadd("loadedLogFiles", sourceFileName)
                pipe.execute()

           ## If desired, uncomment to persist the valueMap for indexName

        print("Import of {} records completed.".format(le_count))

# os.system("redis-cli smembers loadedLogFiles")

# lb = LogBrowser()
# lb.createAllIndexValueMaps()
# ivm = IndexMgr.indexValueManagers
# ivm['request_path'].valueMap
# ivm['request_path'].valueSet
# # vm = ivm['request_path'].valueMap
# # for i in vm.keys()
# #     print(i)
# breakpoint()
# len(vm[j].valueMap)