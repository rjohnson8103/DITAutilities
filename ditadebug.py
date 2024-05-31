
# PROLOG SECTION
# ditdebug.py
#
# A program that lists bad references in one or more ditamaps.
#
# Tested with Python 3.1.2 and the lxml module installed.
# July 19, 2010
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

# control whether running in repair mode
fixflag=False

if len(sys.argv)>2:
	fixflag=True

# get map(s) to be processed
source_spec = GetInputPath()

# startup message
print(" ")
print("ditadebug:",source_spec)
if fixflag:
    print("  operating in repair mode")
    
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

# scan the input files
if fixflag:
    # read all files if we want to fix problems
    GetFileInventory(mapfiles,source_spec,idlist)
else:
    # only read files included in a map
    GetMapInventory(mapfiles,idlist,source_spec)

if len(idlist)==0:
    print("No files found.")
    exit(0)

#
# First look for and report invalid key references
#
keymaster=[]
for item in idlist:
    # create the list of keys that have been defined
    if 'keys' in item and item['keys']!=[]:
        for key in item['keys']:
            keymaster=keymaster+key.split(" ")

# list all the defined key strings
if len(keymaster)>0:
    print("Defined keys:")
    for k in keymaster:
        print("  ",k)
    print(" ")
else:
    print("no keys are defined\n")

# display missing key definitions
nline=0
linelimit=50
for item in idlist:
    # check that keys references point to defined keys
    if 'keyrefs' in item and item['keyrefs']!=[]:
        for keyr in item['keyrefs']:
            key, kid = parseKeyref(keyr)
            # is the key reference in the list of defined keys?
            if key in keymaster:
                pass
            else:
                # error, key has not been defined
                if nline>linelimit:
                    break
                print("missing key definition:",ppath(fpath(item)))
                print("  -> ",keyr)
                nline=nline+1

if nline>=linelimit:
    print("\nonly first",nline,"displayed")
    
#
# Second look for and report bad href/conref references
#
print(" ")
nline=0
linelimit=100
setdebug(False)
# loop through the big list
for item in idlist:
    itempath=fpath(item)
    # only process DITA source files
    if isSource(item):
        if nline>linelimit:
            break
        # parse the XML file
        total_fixes=0
        tree=etree.parse(itempath)
        if 'hrefs' in item:
            if nline>linelimit:
                break
            # loop through all references in a file
            for href in item['hrefs']:
                if nline>linelimit:
                    break
                # ref must not be a URL
                if not isURL(href):
                    # parse the file reference
                    hdir, hfile, htopic, hcontent = parseHref(href)
                    # try to find this href in a source file
                    ret = findHref(item,hdir,hfile,htopic,hcontent,idlist)
                    # did we find it?
                    if ret==False:
                        # the reference is bad
                        if 'topicid' in item:
                            tid="#"+item['topicid']
                        else:
                            tid=""
                        print("Bad reference:",ppath(itempath)+tid)
                        badref=makeRef(hdir,hfile,htopic,hcontent)
                        print("  -> ",ppath(badref))
                        # try to fix the problem if requested
                        if fixflag:
                            fixes=FixHrefs(tree,item,href,idlist)
                            total_fixes=total_fixes+fixes
                        nline=nline+1

        if total_fixes>0:
            outfile=itempath
            print("writing file",outfile)
            tree.write(outfile)
                    
if nline>=linelimit:
    print("\nonly first",nline,"displayed")
                        
         
print(" ")


