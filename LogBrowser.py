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
        self.page_content = ""
        self.table_content = ""
        # self.valueSet = set()

        IndexMgr.indexValueManagers[fieldName] = self

    def maple(self, fieldValue, logEntryKey):
        ivm = IndexMgr.indexValueManagers
        mgr = ivm[self.fieldName]
        vm = mgr.valueMap

        if fieldValue in vm.keys():
            vm[fieldValue].append(str(logEntryKey))
        else:
            vm[fieldValue] = []
            vm[fieldValue].append(str(logEntryKey))

    def content(self):
        if len(self.page_content) > 0:
            return self.page_content
        vm = self.valueMap
        self.page_content +="<h4>{}</h4>".format(self.fieldName)
        self.page_content +="<ul>"
        # breakpoint()
        for j in vm.keys():
            self.page_content += "<li>Value '{}' mapped to {} logEntries</li>".format(j, len(vm[j]))
            self.page_content += "<p>---> mapped logEntries -----    "
            self.page_content += "map:{}:{}</p>".format(self.fieldName, j)
        self.page_content +="</ul>"
        return self.page_content
       
    def tab_content(self):
        if len(self.table_content) > 0:
            return self.table_content
        vm = self.valueMap
        self.table_content += "<div class=\"container\">"
        self.table_content += "<h4>Field Name: {}</h4>".format(self.fieldName)
        self.table_content += "<table class=\"table\">"
        self.table_content += "<thead class=\"thead-dark\">"
        self.table_content += "<tr>"
        self.table_content += "<th scope=\"col\">Field Value</th>"
        self.table_content += "<th scope=\"col\">Mapped LogEntry Count</th>"
        self.table_content += "<th scope=\"col\">Percent of analyzed</th>"
        self.table_content += "<th scope=\"col\">Redis Key to Mapped LogEntries</th>"
        self.table_content += "</tr>"
        self.table_content += "</thead>"

        self.table_content += "<tbody>"
        le_count = LogBrowser.logEntryCount()
        # breakpoint()
        for j in vm.keys():
            self.table_content += "<tr>"
            self.table_content += "<td>{}</td>".format(j) 
            le_idx_count = len(vm[j])
            percent = int(le_idx_count/le_count * 100)
            self.table_content += "<td>{}</td>".format(le_idx_count)
            self.table_content += "<td>{}</td>".format(percent)
            self.table_content += "<td>map:{}:{}</td>".format(self.fieldName, j)
            self.table_content += "</tr>"

        self.table_content += "</tbody>"
        self.table_content += "</table>"
        self.table_content += "</div>"

        return self.table_content

# class LogBrowser(redisInstance):
#     redis = redisInstance

class LogBrowser:
    _instance = None

    # import lb_command

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            # cls._instance.set_vm_dirtyFlag()
            cls._instance.page_content = None
            cls._instance.table_content = None
            cls._instance.csv = None
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

    def vm_dirtyFlag(self):
        return bool(redis.get("vm_dirtyFlag"))

    def clear_vm_dirtyFlag(self):
        redis.set("vm_dirtyFlag", "False")

    def set_vm_dirtyFlag(self):
        redis.set("vm_dirtyFlag", "True")
        LogBrowser._instance.page_content = None
        LogBrowser._instance.table_content = None

    # Store for index-value-logEntry maps as they are created
    def indexValueMaps():
        return IndexMgr.indexValueManagers

    def logEntryCount():
        return len(LogBrowser.logEntries())

    def logEntries():
        LogBrowser._logEntries = {}
        for d in redis.scan_iter(match="logEntry:*", count='100'):
            LogBrowser._logEntries[d] = redis.hgetall(d)
        return LogBrowser._logEntries

    def logEntryKeys(self):
        LogBrowser._logEntries = LogBrowser.logEntries()
        return LogBrowser._logEntries.keys()

    def analysis_table_content(self):
        if LogBrowser._instance.table_content:
            return LogBrowser._instance.table_content
        else:
            ivm = IndexMgr.indexValueManagers

            tab_content = ""
            for i in self.supportedIndices:
                mgr = ivm[i]
                vm = mgr.valueMap

                tab_content += mgr.tab_content()

            LogBrowser._instance.table_content = tab_content
            return tab_content

    def createAllIndexValueMaps(self):
        """ Creates a value-to-LogEntry map for the specified indexName"""
        IndexMgr.indexValueManagers = {}
        for indexName in self.supportedIndices:
            indexMgr = IndexMgr(indexName)
            self.loadIndexValueMap(indexName)
            self.clear_vm_dirtyFlag()

    def loadIndexValueMap(self, indexName):
        """ Creates a value-to-LogEntry map for the specified indexName"""

        indexMgr = IndexMgr.indexValueManagers[indexName]
        vm = indexMgr.valueMap

        if not self.vm_dirtyFlag():
            for i in redis.scan_iter(match="map:{}:*".format(indexName), count=100):
                valueName = i.split(":")[2]
                vm[valueName] = redis.get("map:{}:{}".format(indexName, valueName)).strip('][').split(', ')
        else:

            # scan the logEntries that have been loaded 

            for le in redis.scan_iter(match="logEntry:*", count='100'):
                v = redis.hget(le, indexName)

                fieldVal = v
                if len(fieldVal) == 0:
                    fieldVal="None"

                indexMgr.maple(fieldVal, le)

            for i in vm.keys():
                storable = [ int(x.split(":")[1]) for x in vm[i]]
                pipe.set("idx:{}:{}".format(indexName, i), "map:{}:{}".format(indexName, i) )
                # print("idx:{}:{}".format(indexName, i))
                pipe.set("map:{}:{}".format(indexName, i), str(sorted(storable)))
                # print("map:{}:{}".format(indexName, i))
            pipe.execute()

    def getLoadedFiles():
        return sorted(redis.smembers("loadedLogFiles"))

    def loadLogFile(self, filePath):
        ###################### filePath = directory + filename
        # Import Log files
        self.set_vm_dirtyFlag()

        print("Importing ...")
        if filePath in LogBrowswer.getLoadedFiles():
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
                    k, v = j.split("|")

                    indexName = k.strip()

                    fields[k] = v.strip()

                    # Populate the logEntryKey hash for each logEntry key-value pair
                    pipe.hset(logEntryKey, k, v )

                    pipe.hset(logEntryKey, "request_content", "PLACEHOLDER")
                    pipe.hset(logEntryKey, "response_payload", "PLACEHOLDER")
                    pipe.hset(logEntryKey, "logFileName", sourceFileName)
                    pipe.sadd("loadedLogFiles", sourceFileName)
                pipe.execute()

           ## If desired, uncomment to persist the valueMap for indexName

        print("Import of {} records completed.".format(le_count))

    def analysis_page_content(self):
        if LogBrowser._instance.page_content:
            return LogBrowser._instance.page_content
        else:
            ivm = IndexMgr.indexValueManagers

            page_content = ""
            for i in self.supportedIndices:
                mgr = ivm[i]
                vm = mgr.valueMap

                page_content += mgr.content()

            LogBrowser._instance.page_content = page_content
            return page_content

    def analysis_csv(self):
        if LogBrowser._instance.csv:
            return LogBrowser._instance.csv
        else:
            ivm = IndexMgr.indexValueManagers
            row_header = "{}|{}|{}\n".format("Index", "Value", "Count")
            row_content = row_header

            for i in self.supportedIndices:
                mgr = ivm[i]
                vm = mgr.valueMap
                # vs = mgr.valueSet
                first_field = "{}|".format(i)

                # breakpoint()
                for j in vm.keys():
                    row_content += first_field
                    row_content += "{}|".format(j)
                    row_content += "{}\n".format(len(vm[j]))
            LogBrowser._instance.csv = row_content
            return row_content

# indexName="client_host"
# lb = LogBrowser()
# for i in redis.scan_iter(match="map:{}:*".format(indexName), count=100):
#     valueName = i.split(":")[2]
#     print(valueName)
#     breakpoint()
#     ivm = IndexMgr.indexValueManagers
#     vm = ivm[indexName].valueMap
#     vm[valueName] = redis.get("map:{}:{}".format(indexName, valueName)).strip('][').split(', ')
#     vm[valueName]

# os.system("redis-cli smembers loadedLogFiles")

# output = lb.analysis_csv()

# f = open('analysis.csv', 'w')
# f.write(output)
# f.close()


# ivm = IndexMgr.indexValueManagers
# ivm['request_path'].valueMap
# ivm['request_path'].valueSet
# # vm = ivm['request_path'].valueMap
# # for i in vm.keys()
# #     print(i)
# breakpoint()
# len(vm[j].valueMap)