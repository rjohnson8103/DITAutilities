
# PROLOG SECTION
# ditaauthors.py
#
# A program that lists authors in DITA source
# files.
#
# Tested with Python 3.12.2 and the lxml module installed.
# May 22, 2024
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

# initialization of variables
mapfiles=[]
idlist=[]

# control debugging level
setdebug(False)

# get map(s) to be processed
source_spec = GetInputPath()

# startup message
print(" ")
print("ditaauthors")
print(" ")
      
###################################
#
# MAIN PROCESSING SECTION
#
###################################

# scan for files
GetMapInventory(mapfiles,idlist,source_spec)

if len(idlist)==0:
    print("No files found.")
else:
    # create the report
    copyrights = {}
    authorlist = {}
    contribs = {}
    nsource=0
    for l in idlist:
        # only look in doctype files
        if isSource(l):
            flpath=fpath(l)
            atree = etree.parse(flpath)
            aroot = atree.getroot()
            prolog = aroot.xpath("prolog")
            if len(prolog)>0:
                authors = prolog[0].xpath("author")
                for author in authors:
                    tp = author.get('type')
                    if tp=="creator":
                        creator = author.text
                        if creator in authorlist:
                            authorlist[creator]=authorlist[creator]+1
                        else:
                            authorlist[creator]=1
                    if tp=="contributor":
                        contributor = author.text
                        if contributor in contribs:
                            contribs[contributor]=contribs[contributor]+1
                        else:
                            contribs[contributor]=1
                       
            nsource=nsource+1
            atree=None

print("Authors")
print("=======")
for a in authorlist:
    print("count: %5d, author: %s" % (authorlist[a],a))

print(" ")

print("Contributors")
print("============")
for a in contribs:
    print("count: %5d, contributor: %s" % (contribs[a],a))

print(" ")
print(nsource,"source files in",source_spec)
print(" ")
print("end ditaauthors")
print(" ")
