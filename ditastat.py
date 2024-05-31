# PROLOG SECTION
# ditastat.py
#
# A program that displays tag statistics for
# a set of DITA files.
#
# Tested with Python 3.12.2 and the lxml module installed.
# May 23, 2024
#
# Author: Dick Johnson
#
###################################

###################################
# ENVIRONMENT SETUP SECTION
###################################

# import needed modules
from DITAmod import *

###################################
# FUNCTION DEFINITION SECTION
###################################


###################################
# PROCESSING INITIALIZATION SECTION
###################################

idlist=[]
# control debugging level
setdebug(False)

# get map(s) to be processed
source_spec = GetInputPath()

# startup message
print(" ")
print("ditastat:",source_spec)
print(" ")

mapfiles = []
dstats = {}

# scan for files
GetMapInventory(mapfiles,idlist,source_spec)

# print the number of files found
print(str(len(mapfiles))+" files in the list\n")

#
# loop through the files counting the tags in
# all of them.
#
for f in mapfiles:
    # try to parse the (XML) file
    if not isDITAext(f):
        continue
    
    tree=etree.parse(f)
    if tree!=False:
        # start at the root element
        root=tree.getroot()
        # loop through all the elements
        items=root.getiterator()
        for i in items:
            if etree.iselement(i):
                # count this tag
                thistag = str(i.tag)
                if thistag in dstats:
                    dstats[thistag] = dstats[thistag]+1
                else:
                    dstats[thistag] = 1

# print out how many tags of each type were found
print(len(dstats),"tags found in files:")
for tag in sorted(dstats):
    print(tag.ljust(40),str(dstats[tag]).rjust(10))

print(" ")
print("end ditastat:")
print(" ")
