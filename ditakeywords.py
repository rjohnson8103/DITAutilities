#
# PROLOG SECTION
# ditunused.py
#
# A program that lists keywords used in one or more ditamaps.
#
# Tested with Python 3.12.2 and the lxml module installed.
# May 23, 2024
#
# Author: Dick Johnson
#         VR Communications, Inc.
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
allfiles=[]
idlist=[]

# control debugging level
setdebug(False)

# get map(s) to be processed
source_spec = GetInputPath()
# debug
#source_spec="C:/DITAdemo/DITAinformationcenter_DOCUMENTATION/demo.ditamap"
# startup message
print(" ")
print("ditakeywords:",source_spec)
# pull directory out of source spec
if os.path.isdir(source_spec):
    spec_dir = source_spec
else:
    spec_dir = os.path.dirname(source_spec)
    
print(" ")
     
###################################
#
# MAIN PROCESSING SECTION
#
###################################

# scan map files
GetMapInventory(mapfiles,idlist,source_spec)

print(" ")
print("ditakeywords:",source_spec)
print(" ")

if len(idlist)==0:
    print("No files found.")
else:
    keydict={}
    for item in idlist:
        if 'keywords' in item:
            keywords=item['keywords']
            fpath=item['directory']+os.sep+item['basename']
            if len(keywords)>0:
                for keyword in keywords:
                    if keyword in keydict:
                        keydict[keyword].append(fpath)
                    else:
                        keydict[keyword]=[fpath]

# print out the results sorted by keyword
pad=35*" "
for k in sorted(keydict.keys()):
    nl=0
    for keyw in keydict[k]:
        if nl>0:
            keyp=pad
            
        else:
            keyp=(k+pad)[0:35]

        fmt="%35s %s"
        print(fmt % (keyp,ppath(keyw)))
        nl=nl+1
    

print(" ")
print("end ditakeywords:",source_spec)
print(" ")

