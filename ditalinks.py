
# PROLOG SECTION
# ditalinks.py
#
# A program that tests URLs referenced in DITA source
# files and flags those that cannot be reached.
#
# Tested with Python 3.2 and the lxml module installed.
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
import urllib.request
import urllib.error

###################################
# FUNCTION DEFINITION SECTION
###################################


###################################
# PROCESSING INITIALIZATION SECTION
###################################

# initialization of variables
mapfiles=[]
idlist=[]
timeout=10

# control debugging level
setdebug(False)

# get map(s) to be processed
source_spec = GetInputPath()
#source_spec = "C:/DITADemo/DITAinformationcenter_DOCUMENTATION/DITA_Elementary_pdf.ditamap"

# startup message
print(" ")
print("ditalinks:",source_spec)
print(" ")
      
###################################
#
# MAIN PROCESSING SECTION
#
###################################

# scan for files
GetMapInventory(mapfiles,idlist,source_spec)
print(" ")

if len(idlist)==0:
    print("No files found.")
else:
    nurl=0
    nfail=0
    allurl = []
    print("Begin testing URLs\n")
    for l in idlist:
        fpath=l['basename']
                            
        if isURL(fpath):
            nurl=nurl+1
            allurl.append(fpath)
            try:
                u=urllib.request.urlopen(fpath,None,timeout)
                if debugMode():
                    print("Success: ",fpath)
                u.close()
            except urllib.error.URLError as e:
                print(" URL error",e)
                print("  URL:",fpath)
                nfail=nfail+1
            except:
                print("ohoh!")
   
print("\nURLs tested",nurl)
print("   failures  ",nfail)
print(" ")
print("end ditalinks:",source_spec)
print(" ")
