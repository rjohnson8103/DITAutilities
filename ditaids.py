
# PROLOG SECTION
# ditaids.py
#
# A program that lists topic ids in DITA source
# files and flags duplicates.
#
# Tested with Python 3.2 and the lxml module installed.
# May 1, 2011
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
idlist=[]

# control debugging level
setdebug(False)

# get map(s) to be processed
source_spec = GetInputPath()

# startup message
print(" ")
print("ditaids:",source_spec)
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
    topiclist=[]
    for l in idlist:
        # only look in source files
        if isSource(l):
            flpath=fpath(l)
            if 'topicid' in l:
                topicid=l['topicid']
                
            else:
                topicid=""
            topiclist.append([topicid,flpath])
    
    
    pad=35*" "
    tsave=""
    fsave=""
    dupind=False
    ndup=0
    # print out the results
    for ll in sorted(topiclist):
        tid=ll[0]
        tfile=ll[1]
        ptid=(tid+pad)[0:35]
        pfile=ppath(tfile)
        
        # check for duplicate topic ids
        if tid==tsave:
            dupind=True
            ndup=ndup+1
            ptid=(tsave+pad)[0:35]
            pfile=ppath(fsave)
            print("%35s   %s" % (ptid,pfile))
        else:
            if dupind:
                dupind=False
                ptid=(tsave+pad)[0:35]
                pfile=ppath(fsave)
                print("%35s   %s" % (ptid,pfile))
                
        tsave=tid
        fsave=tfile
        
        
            
print(" ")
print("Total topics",len(topiclist))
print(" ")
print(ndup,"duplicate IDs")
print(" ")
print("end ditaids:",source_spec)
print(" ")
