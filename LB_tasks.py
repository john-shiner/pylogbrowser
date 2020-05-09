#!/usr/bin/python3
"""Run these tasks from the project directory"""

# point to the appropriate project yml files

from invoke import task
import os
import LogBrowser as LB

import os
stream = os.popen('pwd')
output = stream.read()
inv_path = output.strip()

os.environ["INV_PATH"]=inv_path

supportedIndices = LB.supportedIndices

@task
def browseIndex(c):
    "Interactive menu to show numeric analysis for the values in each Log Entry field"
    q = 0
    while (q == 0):
        for num, indexName in enumerate(supportedIndices):
            print(num, indexName)
        qq = num + 1
        print(qq, "Quit")
        idx = input("Select indexName's number to view a value analysis:   ")
        if str(idx) == 'q':
            q = 1
        elif idx == str(qq):
            q = 1
        else:
            LB.createIndexValueMap(supportedIndices[int(idx)])
            # LB.printIndexValueMap((supportedIndices[int(idx)]))
            LB.printIndexValueLogEntries(supportedIndices[int(idx)])

@task
def showLogEntry(c, logEntryId = "1"):
    "Show the Log Entry field values for a specified logEntryId"
    logEntryId = input("Enter Log Entry ID:   ")
    LB.showLogEntry(logEntryId)

@task
def gh(c):
    "Open the current github branch on GitHub"
    c.run("open $(/usr/bin/git remote -v | cut -f 1 -d ' ' |cut -f 2 | sed 1d | cut -d '.' -f1-2)/tree/$(git rev-parse --abbrev-ref HEAD)")
    
@task
def st(c):
    "Open the current repository in Sublime Text"
    c.run("subl $INV_PATH")
    