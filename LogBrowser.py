import re
import config
from redis import Redis
import os

# # Desktop
# host = config.REDIS_DESKTOP["host"]
# port = config.REDIS_DESKTOP["port"]
# pwd = config.REDIS_DESKTOP["password"]
# db = config.REDIS_DESKTOP["db"]
# redis = Redis(db=db, host=host, port=port, password=pwd, \
#     charset="utf-8", decode_responses=True)

# # Redis Labs Enterprise Account
# host = config.REDIS_LABS["host"]
# port = config.REDIS_LABS["port"]
# pwd = config.REDIS_LABS["password"]
# db = config.REDIS_LABS["db"]
# redis = Redis(db=db, host=host, port=port, password=pwd, \
#     charset="utf-8", decode_responses=True)

# Kubernetes Deployment
redis = Redis(host="redis", charset="utf-8", decode_responses=True)

pipe = redis.pipeline()

# logEntryKeys = redis.keys("logEntry:*")

class IndexMgr:

    indexValueManagers = {}

    cls_indices = []

    def __init__(self, fieldName):
        self.fieldName = fieldName
        self.valueMap = {}
        self.page_content = ""
        self.table_content = ""
        self.loadIndexValueMap()

        IndexMgr.indexValueManagers[self.fieldName] = self


    def createAllIndexValueMaps():
        """ Creates a value-to-LogEntry map for the specified indexName"""
        print("createAllIndexValueMaps")
        indexValueManagers = {}
        for indexName in LogBrowser.supportedIndices():
            IndexMgr(indexName).loadIndexValueMap()
        LogBrowser.clear_vm_dirtyFlag()

    def loadIndexValueMap(self):
        """ Creates a value-to-LogEntry map for the specified indexName"""

        vm = self.valueMap

        for i in redis.scan_iter(match="idx:{}:*".format(self.fieldName), count=100):
            valueName = i.split(":")[2]
            # vm[valueName] = redis.zrange("map:{}:{}".format(indexName, valueName)).strip('][').split(', '), 0, -1)
            # vm[valueName] = redis.zrange("map:{}:{}".format(self.fieldName, valueName), 0, -1)
            vm[valueName] = redis.zcard("map:{}:{}".format(self.fieldName, valueName))

    def tab_content(self):
        if  LogBrowser.content_dirtyFlag():

            self.table_content = ""
            vm = self.valueMap
            self.table_content += "<div class=\"container\">"
            self.table_content += "<h4>Field Name: {}</h4>".format(self.fieldName)
            self.table_content += "<table class=\"table\">"
            self.table_content += "<thead class=\"thead-dark\">"
            self.table_content += "<tr>"
            self.table_content += "<th scope=\"col\">Field Value</th>"
            self.table_content += "<th scope=\"col\">Mapped LogEntry Count</th>"
            self.table_content += "<th scope=\"col\">Percent of analyzed</th>"
            self.table_content += "<th scope=\"col\">Mapped LogEntries</th>"
            self.table_content += "</tr>"
            self.table_content += "</thead>"

            self.table_content += "<tbody>"
            le_count = LogBrowser.logEntryCount()
            # breakpoint()
            # ivm = IndexMgr.indexValueManagers[self.fieldName]
            vm = self.valueMap

            # for vm_key in redis.scan_iter(match="idx:{}:*".format(self.fieldName), count='100'):
            #     # breakpoint()
            #     zkey = "map:{}:{}".format(self.fieldName, vm_key.split(":")[2])
            #     vm[zkey] = redis.zcard(zkey)


            for j in vm.keys():
                index_value = j.replace("/","^")
                self.table_content += "<tr>"
                self.table_content += "<td>{}</td>".format(j) 
                le_idx_count = vm[j]
                # le_idx_count = redis.zcard("map:{}:{}".format(self.fieldName, j))

                percent = int(le_idx_count/le_count * 100)
                self.table_content += "<td>{}</td>".format(le_idx_count)
                self.table_content += "<td>{}</td>".format(percent)
                # /mapfieldval/?mapkey=ABC
                self.table_content += "<td><a href=\"/mapfieldval/mapkey=map:{}:{}\">map:{}:{}</a></td>".format(self.fieldName, index_value, self.fieldName, j)
                self.table_content += "</tr>"

            self.table_content += "</tbody>"
            self.table_content += "</table>"
            self.table_content += "</div>"
        else:
            print("cached tab_content")

        return self.table_content

# class LogBrowser(redisInstance):
#     redis = redisInstance

class LogBrowser:
    _instance = None

    # import lb_command

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)


            cls._instance.table_content = None
            cls._instance.logEntries = {}

            IndexMgr.createAllIndexValueMaps()
            cls.set_content_dirtyFlag()
            cls.set_vm_dirtyFlag()

        return cls._instance

    indexNames = ["client_host", "client_id", "client_ip", \
                        "environment", "organization", "proxy", \
                        "proxy_basepath", "proxy_name", \
                        "proxy_revision", "request_path", "request_uri", \
                        "request_verb", "response_reason_phrase", \
                        "response_status_code", "soap_operation", \
                        "soap_siteId", "target_basepath", "target_host", \
                        "target_ip", "virtual_host"]

    # indexNames = [ "proxy", "proxy_basepath", "request_path", "request_uri", \
    #                     "soap_operation", "soap_siteId", "target_basepath" ]

    def supportedIndices():
        return sorted(LogBrowser.indexNames)

    def vm_dirtyFlag():
        return "True" == redis.get("vm_dirtyFlag")

    def clear_vm_dirtyFlag():
        redis.set("vm_dirtyFlag", "False")

    def set_vm_dirtyFlag():
        redis.set("vm_dirtyFlag", "True")
        LogBrowser._instance.page_content = None
        LogBrowser._instance.table_content = None

    def content_dirtyFlag():
        return "True" == redis.get("content_dirtyFlag")

    def clear_content_dirtyFlag():
        redis.set("content_dirtyFlag", "False")

    def set_content_dirtyFlag():
        redis.set("content_dirtyFlag", "True")
        # LogBrowser._instance.page_content = None
        LogBrowser._instance.table_content = None

    # Store for index-value-logEntry maps as they are created
    def indexValueMaps():
        return IndexMgr.indexValueManagers

    def logEntryCount():
        # return len(LogBrowser.logEntryKeys())
        rtn = []
        rtn += redis.scan_iter(match="logEntry:*", count='100')
        return len(rtn)

    def logEntries():
        if LogBrowser.vm_dirtyFlag():
            LogBrowser._logEntries = {}
            for d in redis.scan_iter(match="logEntry:*", count='100'):
                LogBrowser._instance.logEntries[d] = redis.hgetall(d)
            IndexMgr.createAllIndexValueMaps()
        return LogBrowser._instance.logEntries

    def logEntryKeys():
        LogBrowser._instance.logEntries = LogBrowser.logEntries()
        return LogBrowser._instance.logEntries.keys()

    def analysis_table_content(self):
        # breakpoint()
        if LogBrowser.content_dirtyFlag():
            ivm = IndexMgr.indexValueManagers

            tab_content = ""
            for i in LogBrowser.supportedIndices():
                mgr = ivm[i]
                vm = mgr.valueMap

                tab_content += mgr.tab_content()

            LogBrowser._instance.table_content = tab_content
            LogBrowser.clear_content_dirtyFlag()
        else:
            print("using cached analysis_table_content")
            tab_content = LogBrowser._instance.table_content
        return tab_content

    def getLoadedFiles():
        return sorted(redis.smembers("loadedLogFiles"))

    def loadLogFile(self, filePath):
        ###################### filePath = directory + filename
        # Import Log files
        LogBrowser.set_vm_dirtyFlag()
        LogBrowser.set_content_dirtyFlag()

        print("Importing ...")
        if filePath in LogBrowser.getLoadedFiles():
            print("File {} is already loaded".format(filePath))
            return

        le_count = LogBrowser.logEntryCount()

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
                    # jjj = jj.replace("/", "\\")
                    # k, v = j.split("|")
                    k, v = jj.split("|")

                    indexName = k.strip()

                    if v.strip() == "":
                        v = "None"
                    fields[k] = v.strip()

                    # Populate the logEntryKey hash for each logEntry key-value pair
                    pipe.hset(logEntryKey, k, v )

                    pipe.hset(logEntryKey, "request_content", "PLACEHOLDER")
                    pipe.hset(logEntryKey, "response_payload", "PLACEHOLDER")
                    pipe.hset(logEntryKey, "_logFileName", sourceFileName)
                    pipe.sadd("loadedLogFiles", sourceFileName)
                    storable = int(logEntryKey.split(":")[1]) 
                    # print("v = {}".format(v))
                    if k in LogBrowser.supportedIndices():
                        pipe.set("idx:{}:{}".format(indexName, v), "map:{}:{}".format(indexName, v))
                        mapkey = "map:{}:{}".format(indexName, v)
                        mapping = { str(storable) : storable }
                        # print("{} = {} = {}".format(indexName, mapkey, mapping))
                        pipe.zadd(mapkey, mapping )
                pipe.execute()

           ## If desired, uncomment to persist the valueMap for indexName

        print("Import of {} records completed.".format(le_count))
       
# fieldChoices = []

# choices = []
# searchKey = redis.get("logmap")
# # print("get logmap:  {}".format(searchKey))

# if len(searchKey) > 0:
#     for i in redis.zrange(searchKey, "0", "-1"):
#         choices.append((i, i))

# fieldChoices = choices

# print("searchKey {}".format(searchKey))
# print("choices {}".format(choices))
# print("fieldChoices {}".format(fieldChoices))
