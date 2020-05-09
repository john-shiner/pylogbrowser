# lb_commmand

def showLogEntry(self, logEntryKey="1"):
    print()
    print("**********************")
    print("logEntry:"+logEntryKey)
    # print(redis.hgetall("logEntry:"+logEntryKey))
    fieldValues = redis.hgetall("logEntry:"+logEntryKey)
    for i in fieldValues.keys():
        print("     {} : {}".format(i, fieldValues[i]))
    print("**********************")
    print()

def printIndexValueMap(self, indexName):
    print()
    print("**********************")
    print()
    
    print("{} index with {} values".format(indexName, len(indexValueMaps[indexName].valueSet)))

    for vm in indexValueMaps[indexName].valueMap:
        print("        --> value '{}' is referenced by {} logEntries".format(vm, len(vm)))
    print()
    print("**********************")
    print()

def printIndexValueLogEntries(self, indexName):
    print()
    print("**********************")
    print()
    
    print("{} index with {} values".format(indexName, len(indexValueMaps[indexName].valueSet)))

    for vm in indexValueMaps[indexName].valueMap:
        print("        --> value '{}' is referenced by {} logEntries".format(vm, len(vm)))

    # breakpoint()

    for k in indexValueMaps[indexName].valueMap.keys():
        print("Value:   {}".format(k))
        print(indexValueMaps[indexName].valueMap[k])
    print()
    print("**********************")
    print()


def printAllIndexValueMaps(self): 
    for indexName in supportedIndices:
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

def _experiment_printAllIndexValueMaps(self): 
    content = ""
    for indexName in self.supportedIndices:
        content += "<br/>"
        content += "{} index with {} values".format(indexName, len(self.indexValueMaps[indexName].valueSet))
        content += "<br/>"
        for vm in self.indexValueMaps[indexName].valueMap:
            content += "<p>        --> value '{}' is referenced by {} logEntries</p>".format(vm, len(vm))
        content += "<br/>"


def menu(self):
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

# menu()
# printIndexValueMap("target_basepath")
# printIndexValueLogEntries("target_basepath")
# printIndexValueMap("target_basepath")
# printAllIndexValueMaps()

# loadLogFile()