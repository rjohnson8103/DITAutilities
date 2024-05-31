
# PROLOG SECTION
# ditunused.py
#
# A program that lists source files not refered to in one or
# more ditamaps.
#
# Tested with Python 3.12.2 and the lxml module installed.
# May 23,2024
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

# debugging functions
def showallfiles():
    for f in allfiles:
        print(f)
def showmapfiles():
    for f in mapfiles:
        print(f)

#
# Test to see if a file in in a map
#
def inMaps(f, mapf):
    if debugMode():
        print("inMaps",f)

    rc = False

    fnorm = os.path.abspath(f)

    for mf in mapf:
        mfn = os.path.abspath(mf)
        if mfn == fnorm:
            rc = True
            break
    
    return rc

###################################
# PROCESSING INITIALIZATION SECTION
###################################

# initialization of variables
mapfiles=[]
allfiles=[]
idlist=[]
ucount = 0

# control debugging level
setdebug(False)

# get map(s) to be processed
source_spec = GetInputPath()

# startup message
print(" ")
print("ditaunused:",source_spec)
print(" ")

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
# get all files in the directory
GetFileInventory(allfiles,spec_dir,None)

mapdirs = getMapDirs(mapfiles)

if debugMode():
    for md in sorted(mapdirs):
        print("source file directory",ppath(md))
    print(" ")

if len(allfiles)==0:
    print("No files found.")
else:
    # loop through all source and image files to see if they are a map
    ucount=0
    for afile in allfiles:
        if isDITAext(afile) or isImage(afile) and not isURL(afile):
            # is the file in the map?
            afabs = os.path.abspath(afile)
            afd = os.path.dirname(afabs)
            if afd in mapdirs:
                if not inMaps(afile,mapfiles):
                    # oh oh! file is not in the map
                    print("unused file:",ppath(afile))
                    missingf = afile
                    ucount=ucount+1
                
    
if ucount>0:
    print(" ")
    print(ucount,"unused files found")
else:
    print(" ")
    print("no unused files found")
 

print(" ")
print("end ditaunused:",source_spec)
print(" ")


