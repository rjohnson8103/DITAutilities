###################################
# PROLOG SECTION
# DITAmod.py
#
# Common functions used in DITA XML processing.
#
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
from   lxml import etree
import sys
import os
import os.path
import shutil
import glob
from   xml.parsers.expat import *

# debug flag - setting this to True traces execution in great detail
dbgflag = False

# saved project directory
project_dir=""

# possible DITA filetype tuple
ditatypes = (".dita",".ditamap",".xml",".XML")

# types of DITA reference attributes to check
refs=('href','conref','data')

# types of DITA key reference attributes
keytypes=('keyref','conkeyref')

# types of list searches and href replacements
TYPE_DIR = 1
TYPE_FILE = 2
TYPE_TOPICID = 3
TYPE_CONTENTID = 4
TYPE_EXT = 5

# key values
keyvalues = {}

###################################
# FUNCTION DEFINITION SECTION
###################################

#
# Function to return the list of directories
# containing map source files.
#
def getMapDirs(mapfiles):
    if debugMode():
        print("getMapDirs for",len(mapfiles),"files")

    mdir = []

    for f in mapfiles:
        if isURL(f):
            continue
        
        mfd = os.path.dirname(os.path.abspath(f))
        
        if not (mfd in mdir):
            mdir.append(mfd)
                        
    return mdir

#
# Function to return a list of all files
# used by a DITA map. We return:
#
#   mapfiles - file path
#   idlist - dictionary list of file information
#
def GetMapInventory(mapfiles,idlist,mappath):
        
    if dbgflag:
        print("EnterGetMapInventory",mappath)

    # intialize list of map filepaths
    maps=[]

    # save project directory
    setpdir(mappath)
    
    if os.path.exists(mappath):
        if os.path.isdir(mappath):
            # get a list of the ditamaps in the directory
            maps = glob.glob(mappath+"/*.ditamap")
        else:
            # input was not a directory
            maps=[mappath]
        if dbgflag:
            # display the maps to be used
            for m in maps:
                print("map file:",m)
            print(" ")
            
    else:
        print("GetMapInventory error",mappath,"does not exist")

    if dbgflag:
        print("map count =",len(maps))
            
    # remember files we have scanned
    filedict={}
    # first collect information in the maps
    for map in maps:
        filedict[map]=False
        
    # initialize not scanned count
    notscanned=len(filedict)
    
    # keep scanning until we don't find any new references to unscanned files
    while notscanned>0:
        if dbgflag:
            print(notscanned,"files to be scanned")
        ns=0
        olddict=filedict.copy()
        for ff in olddict:
            # Check for unscanned files 
            if filedict[ff]==False:
                # file has not yet been scanned
                mapfiles.append(ff)
                # scan this file
                filedict[ff]=True
                loclist=ScanSourceFile(ff,idlist)
                # look for hrefs to add to the scan list
                for lcl in loclist:
                    if 'hrefs' in lcl:
                       # there is an href
                       for href in lcl['hrefs']:
                           if isURL(href):
                               # URL href
                               filedict[href]=False
                               ns=ns+1
                               if dbgflag:
                                   print(href,"URL not yet scanned")
                           else:
                               # file href
                               xdir, xfile, xtopic, xcont = parseHref(href)
                               if len(xdir)>0:
                                   absdir=os.path.normpath(xdir)
                                   absdir=os.path.abspath(absdir)
                                   xfpath=absdir+os.sep+xfile
                               else:
                                   xfpath=xfile
                               if not xfpath in filedict:
                                   # href file not already scanned
                                   filedict[xfpath]=False
                                   ns=ns+1
                                   if dbgflag:
                                       print(href,"file not yet scanned")
                
        notscanned=ns

        
    return

#
#
# Function to return a list of all source files
# in a directory (dir).
#
# In each list output entry we have:
#    file-path file-doctype (or None)
#
def GetFileInventory(filelist,dir,idlist):
    global keyvalues

    keyvalues={}
        
    if dbgflag:
        print ("Enter GetFileInventory",dir)
    rc = True

    # save project directory
    setpdir(dir)
    
    # validate we have a directory
    if os.path.isdir(dir) != True:
        print ("Error",dir,"is not a directory") 
        return False

    # temporary list of all files in the directory
    allfiles = os.walk(dir)

    # build up the filelist
    for f in allfiles:
        # get current directory
        fdir = f[0]
        # get list of files in this directory
        flist = f[2]
        for ff in flist:
            fpath = os.path.join(fdir,ff)
            # remember file path
            filelist.append(fpath)
            
    if dbgflag:
        print(len(filelist),"files found")

    # scan the files (if required)
    if idlist!=None:
        # scan the files in the list
        for fle in filelist:
            ScanSourceFile(fle,idlist)
                    
    return rc

#
# Functions to set/return project directory
#
def getpdir():
    return project_dir

def setpdir(p):
    global project_dir

    if dbgflag:
        print("setpdir",p)
        
    if os.path.isdir(p):
        project_dir=p
    else:
        ps=os.path.split(p)
        project_dir=ps[0]

    if dbgflag:
        print("setpdir to",project_dir)
    
       
#
# Function to display a file path relative to
# the project directory.
#
def ppath(f):
    pd=getpdir()
    if isURL(f):
        return f
    else:
        if len(f)>0:
        	return os.path.relpath(f,pd)
        else:
        	return f

#
# Function to extract file path from big list
#
def fpath(item):
    fp = item['directory']+os.sep+item['basename']
    return fp

#
# Function to return the input path to be processed
#
def GetInputPath():
    # default to cwd
    source_spec = os.getcwd()

    # use first argument (if provided)
    for i in range(len(sys.argv)):
       if i==1:
            source_spec=sys.argv[i]
            
    return source_spec

#
# Function to test for possible DITA source file extension
#
def isDITAext(f):
    
    fdata = os.path.splitext(f)
    
    if fdata[1] in ditatypes:
        return True
    else:
        return False

#
# Function to test if list item is a source file
#
def isSource(item):
    
    if isDITAext(item['basename']) and 'doctype' in item and item['doctype']!=None:
        return True
    else:
        return False
    
#
# Function to test if file could be a map
#
def isDITAMap(f):
    fdata = os.path.splitext(f)
    
    if fdata[1] == ".ditamap":
        return True
    else:
        return False

#
# Function to test if file is an image
#
def isImage(f):
    iexts = (".PNG",".JPG",".GIF",".BMP",".JPEG")
    fdata = os.path.splitext(f)
    fext = fdata[1]
    fext = fext.upper()
    if fext in iexts:
        return True
    else:
        return False
    
#
# Function to test if "file" is actually a URL
#
def isURL(f):
    
    if f.find("http:")>=0:
        return True
    elif f.find("https:")>=0:
        return True
    elif f.find("news:")>=0:
        return True
    elif f.find("mailto:")>=0:
        return True
    else:
        return False
  

#
# Function to get keys defined
def getKeys():
    return keyvalues

def setdebug(flag):
    """
    Set the debug flag:
    
    True = print details of execution
    False = print minimal progress messages
    
    """
    global dbgflag
    dbgflag = flag
    if dbgflag:
        print ("**setdebug - debug flag set to",dbgflag) 
    return

#
# Function to return the dbgflag value
#
def debugMode():
    return dbgflag

#
# Function to collect information from a DITA source file
#
# Each entry in the output list is a dictionary containing
# these keys:
#
# directory
# basename
# topicid
# elementids
# hrefs
# keyrefs
# doctype
#
def ScanSourceFile(fl,ilist):
    if dbgflag:
        print("Enter ScanSourceFile",fl)

    # file path
    f = fl
    absf=os.path.abspath(fl)
    # initialize the dictionary
    dict={}
    locallist=[]

    # bail if a URL
    if isURL(fl):
        dict['directory']=""
        dict["basename"]=fl
        ilist.append(dict)
        return locallist

    # bail if it is not the right filetype
    if not isDITAext(absf):
        dict['directory']=os.path.dirname(absf)
        dict['basename']=os.path.basename(absf)
        dict['doctype']=None
        ilist.append(dict)
        return locallist
        
    # try to parse the file as XML
    try:
        # create a tree for the source file
        tree = etree.parse(f)

        # quick exit on error
        if not tree:
            print("ScanSourceFile error",f,"not parsed")
            dict['directory']=os.path.dirname(absf)
            dict['basename']=os.path.basename(absf)
            dict['doctype']=None
            ilist.append(dict)
            return locallist

        # get the root element for file
        root = tree.getroot()
        roottag = root.tag

        # set the doctype
        docinfo = tree.docinfo
        tdoctype = docinfo.doctype
        # make sure it is really DOCTYPE (other things can occur)
        if len(tdoctype)>9 and tdoctype.find('<!DOCTYPE')>-1:
            doctype=tdoctype
        else:
            doctype=None
        dt=doctype
            
        if dbgflag:
            print(" root tag is", roottag)
        
        if roottag == 'dita':
            # there may be other topics inside this topic
            topics = root.getchildren()
            if dbgflag:
                for t in topics:
                    print("topic: ",t.tag,t.get('id'))
        else:
            # there is only a single topic in the file
            topics = [root]

        # get ID info for this topic(s)
        for t in topics:
            ScanTopic(t,f,dt,locallist)

        # add to big list
        for ll in locallist:
            ilist.append(ll)

    except:
        if dbgflag:
            print("ScanSourceFile EXCEPTION!",f)
        # file cannot be parsed
        # or also file may not exist.
        if isURL(f):
            # record data for a URL
            dict['directory']=""
            dict['basename']=f
            dict['doctype']=None
            ilist.append(dict)
        else:
            if os.path.exists(f):
                if dbgflag:
                    print("  file could not be parsed")
                # record data for non-parseable file
                dict['directory']=os.path.dirname(absf)
                dict['basename']=os.path.basename(absf)
                dict['doctype']=None
                ilist.append(dict)
            else:
                # do nothing if file does not exist
                if dbgflag:
                    print("  file does not exist")


    # free up resources
    tree=None
    
    return locallist

#
# Function to scan a file topic for information
#
# where: t = starting element
#        f = file path
#        doctype = DOCTYPE string
#        ilist = id list
#
def ScanTopic(t,f,doctype,ilist):
    if dbgflag:
        print("Enter ScanTopic",f,doctype,t.tag)
        
    # initialize what we return
    dict={}
    
    # try to fetch the topic ID attribute
    topicid = t.get("id", default="")
    # file path split
    topicdir=os.path.dirname(f)
    topicdir=os.path.abspath(topicdir)
    topicfile=os.path.basename(f)
    
    elementids=[]
    
    kids = t.getchildren()
    # loop through all the child elements of the starting element
    for kid in kids:
        if dbgflag:
            print("child element",kid.tag,kid.get('id'))
        if kid.tag == 'topic':
            if dbgflag:
                print("Recursive ScanTopic in",f)
            # scan the sub-topics of this topic
            ScanTopic(kid,f,doctype,ilist)
        elif "<!-- " in str(etree.tostring(kid)):
            # ignore comments
            pass
        else:
            # collect all the content IDs in this topic
            ScanContentIDs(kid,elementids)
        # fill in key/value pairs
        xpstr="@keys"
        keysa = kid.xpath(xpstr)
        if keysa!=[]:
            hrefa = kid.get("href")
            if debugMode():
                print("key/value",keysa,hrefa)
            if hrefa!=None:
                ksplit = keysa[0].split(" ")
                for kkk in ksplit:
                    keyvalues[kkk]=hrefa
                                        

    # find all the external and internal references in the file
    eref=[]
    for r in refs:
        xpstr=".//@"+r
        xrefs = t.xpath(xpstr)
        if dbgflag and len(xrefs)>0:
            print("  found",r,len(xrefs),"times")
        for xx in xrefs:
            if dbgflag:
                print("   href is",xx)
            if isURL(xx):
                eref.append(xx)
            else:
                if xx[0]=="#":
                    # internal reference
                    if dbgflag:
                        print("    internal reference",xx)
                    ipath=f+xx
                    eref.append(normHref(ipath))
                else:
                    # external reference
                    relpat=topicdir+os.sep+xx
                    relpat=normHref(relpat)
                    if dbgflag:
                        print("    external reference",relpat)
                    eref.append(relpat)

    # find all the key references in the file
    kref=[]
    for kr in keytypes:
        xpstr=".//@"+kr
        xrefs = t.xpath(xpstr)
        if dbgflag and len(xrefs)>0:
            print("  found",kr,len(xrefs),"times")
        for xx in xrefs:
            kref.append(xx)

    # find all the key definitions in the file
    keylist=[]
    xpstr=".//@keys"
    xrefs = t.xpath(xpstr)
    if dbgflag and len(xrefs)>0:
        print("  found",len(xrefs),"keys")
    for xx in xrefs:
        for kxx in xx[0].split(" "):
            keylist.append(kxx)
                
    # find all keywords defined in the file
    keywords=[]
    xpstr=".//*/keyword"
    keys=t.xpath(xpstr)
    if len(keys)>0:
        if dbgflag:
            print("  found",len(keys),"keywords")
        for xx in keys:
            if xx.text==None:
                keywords.append("")
            else:
                keywords.append(xx.text)
            
    # store information to return
    xdir, xfile, xtopic, xcont = parseHref(f)
    dict['directory']=topicdir
    dict['basename']=xfile
    dict['topicid']=topicid
    dict['elementids']=elementids
    dict['hrefs']=eref
    dict['keyrefs']=kref
    dict['keys']=keylist
    dict['doctype']=doctype
    dict['keywords']=keywords
    
    # add the information collected to the big list
    ilist.append(dict)
        
    return [f]

#
# Function to  scan for content ids in a single topic
#
def ScanContentIDs(t,elist):
    if dbgflag:
        print("Enter ScanContentIDs", t.tag)

    allid=t.xpath("//*/@id")
    for aid in allid:
        if aid in elist:
            pass
        else:
            elist.append(aid)
 

    
#
# Function to return list of matches in a larger list
#
def returnList(mtype, s, inlist):
    if dbgflag:
        print("Enter returnList",mtype,s,len(inlist))

    retlist = []

    for idx in inlist:
        if mtype==TYPE_DIR:
            if s==idx['directory']:
                # file in specified directory
                retlist.append(idx)

        elif mtype==TYPE_FILE:
            if idx['basename']==s:
                # file with specified file path
                retlist.append(idx)

        elif mtype==TYPE_TOPICID:
            if 'topicid' in idx and idx['topicid']==s:
                # file with specified topicid
                retlist.append(idx)

        elif mtype==TYPE_CONTENTID:
            if ('elementids' in idx) and (s in idx['elementids']):
                # file contains specified content id
                retlist.append(idx)

        else:
            print("Error, mtype=",mtype)
            
    return retlist

#
# Function to parse a keyref into parts:
# key id
#
def parseKeyref(h):
    kkey=""
    kid=""
    if len(h)>0:
        p=h.find('/')
        if p>-1:
            kid=h[p+1:]
            kkey=h[0:p]
        else:
            kkey=h
            kid=""

    if dbgflag:
        print("parseKeyref returns",kkey,kid)
        
    return kkey, kid

    
#
# Function to parse an href into parts:
#  directory, filename, topicid, contentid
#
# General format to parse is: path/filename#topicid/contentid
#
def parseHref(h):
            
    hdir=""
    hfile=""
    htopic=""
    hcontent=""

    if len(h)>0:
        # is there a topicid?
        p = h.find('#')
        if p > -1:
            rest = h[p+1:]
            first = h[0:p]
        else:
            rest=""
            first=h

        # is there something preceeding the topicid?
        if len(first)>0:
            hdir=os.path.dirname(first)
            hfile=os.path.basename(first)
            
        # is there also a contentid?
        if len(rest)>0:
            pp1=rest.find('/')
            pp2=rest.find("\\")
            pp=max(pp1,pp2)  
            if pp>-1:
                htopic=rest[0:pp]
                hcontent=rest[pp+1:]
            else:
                htopic=rest

    # returned the parts of the supplied href
        
    return hdir, hfile, htopic,hcontent

#
# Function to create a reference string from its parts
#
def makeRef(d,f,t,c):
    
    ref=d+os.sep+f
    if t!="":
        ref=ref+"#"+t
        if c!="":
            ref=ref+os.sep+c

    return ref

#
# Function to create a normalized href
#
def normHref(h):
    d,f,t,c=parseHref(h)
    p=os.path.normpath(d+os.sep+f)
    p=os.path.abspath(p)
    dd=os.path.dirname(p)
    ff=os.path.basename(p)
    newh=makeRef(dd,ff,t,c)
        
    return newh

#
# Function used for debugging to dump out internal
# information.
#
def dumpAll(idlist):
    
    print("dumpAll\n")
    for id in idlist:
        print(id['basename'],id,"\n")
        
#
# Function that searches for a match to an href in the big list
#
def findHref(item,hdir,hfile,htopic,hcontent,idlist):
    
    fdir=item['directory']
    fbase=item['basename']
    
    if dbgflag:
        print("Enter findHref","fdir:",fdir,"fbase:",fbase)
        print("              ","hdir:",hdir,"hfile:",hfile)
        print("              ","htopic:",htopic,"hcontent:",hcontent)
       
    rc = True

    # don't check URL references
    if isURL(hdir)==True:
        return True
      
        
    # look for files in directory first
    path_list = returnList(TYPE_DIR, hdir, idlist)
    # we have files in the specified directory
    if len(path_list)>0:
        # next check files in the directory
        file_list = returnList(TYPE_FILE,hfile,path_list)
        if len(file_list)>0:
            # we found file(s) that match as well
            if htopic!="":
                # check topicid (or contentid)
                top_list = returnList(TYPE_TOPICID,htopic,file_list)
                if len(top_list)>0:
                    if hcontent!="":
                        # check contentid
                        con_list = returnList(TYPE_CONTENTID,hcontent,top_list)
                        if len(con_list)>0:
                            rc = True
                        else:
                            if dbgflag:
                                print(hcontent,"*contentid* not found in list")
                            rc = False
                    else:
                        # there is no contentid
                        rc=True
                else:
                    # topicid not found
                    if dbgflag:
                        print(htopic,"*topicid* not found in list")
                    # check if reference was to a contentid instead
                    if hcontent=="":
                        # check contentid
                        con_list = returnList(TYPE_CONTENTID,htopic,file_list)
                        if len(con_list)>0:
                            rc = True
                        else:
                            if dbgflag:
                                print(htopic,"*contentid(topicid)* not found in list")
                            rc = False
                    else:
                        # there is both a topic and content id
                        rc = False
            else:
                # no topicid is present
                rc = True
        else:
            # file was not found
            if dbgflag:
                print(hfile,"*file* not found in list")
            rc = False
    else:
        # directory was not found
        if dbgflag:
            print(hdir,"*dir* not found in list")
        rc = False
    
           
    return rc

#
# Function to try to repair all hrefs in a file.
#  Input must be an XML file with a DOCTYPE.
#
def FixHrefs(tree,item,href,idlist):
    filepath=fpath(item)
    topicdir=os.path.dirname(filepath)
    topicdir=os.path.abspath(topicdir)
    if dbgflag:
        print("Enter FixHrefs",filepath)
        print("   ==>",href)
        

    # count of references fixed
    fixed = 0
    oldref=None

    # set the file and doctype
    f = filepath
    
    # skip files that are not DITA source files (i.e. no DOCTYPE)
    if isSource(item)==False:
        print("FixHrefs error",f,"is not XML source")
        return
        
    # get the root element in the file
    root = tree.getroot()
    # prepare to iterate over elements in the file
    iter = root.getiterator()
    
    # loop on all elements to find the reference to be fixed
    
    for e in iter:
        # stop if we have made a fix already
        if fixed>0:
            break
        # inner loop on type of reference
        for r in refs:
            # get the reference string
            hr = e.get(r)
            # put href in normalized form
            if hr==None:
                relpat=""
            elif hr[0]=="#":
                    # internal reference
                    relpat=filepath+hr
                    if dbgflag:
                        print("    internal reference",relpat)
                    
            else:
                    # external reference
                    relpat=topicdir+os.sep+hr
                    relpat=normHref(relpat)
                    if dbgflag:
                        print("    external reference",relpat)
                    
            if relpat==href:
                # save the reference value
                oldref = hr
                newref=""
                # parse the reference
                hdir, hfile, htopic, hcontent = parseHref(relpat)

                # Fix #1: try using another file extension
                fdata = os.path.splitext(hfile)
                ext = fdata[1]
                newext=""
                if ext==".dita" or ext==".ditamap":
                    newext=".xml"
                elif ext==".xml":
                    newext=".dita"
                if newext!="":
                    hfile2=fdata[0]+newext
                    if dbgflag:
                        print("FixHrefs try #1",hfile2)
                    # try to find file with new extension
                    ret2=findHref(item,hdir,hfile2,htopic,hcontent,idlist)
                    if ret2:
                        # we found the ref in a file with a
                        # different file extension
                        newref = makeRef(hdir,hfile2,htopic,hcontent)
                        newref=os.path.relpath(newref,topicdir)
                        if dbgflag:
                            print("fix #1 succeeds",newref)

                if newref=="":
                        # Fix #2: try looking for file in another directory
                        if dbgflag:
                            print("FixHrefs try #2")
                        file_list = returnList(TYPE_FILE,hfile,idlist)
                        ll = len(file_list)
                        if ll==1:
                            # we found the file in another directory
                            l0 = file_list[0]
                            filedir = os.path.dirname(f)
                            newdir = l0['directory']
                            reldir = os.path.relpath(newdir,filedir)
                            # will this file satisfy the reference?
                            ret2 = findHref(item,newdir,hfile,htopic,hcontent,idlist)
                            if ret2:
                                # this file is OK, use it instead
                                newref = makeRef(reldir,hfile,htopic,hcontent)
                                if dbgflag:
                                    print("FixHrefs #2 succeeds",newref)
                        else:
                            if dbgflag:
                                print(" file",hfile,"found in",ll,"places")
                                for ffl in file_list:
                                    print(ppath(fpath(ffl)))

                if newref=="":
                        # Fix #3: try looking for new topicid in same file
                        if dbgflag:
                            print("FixHrefs try #3")
                        file_list = returnList(TYPE_FILE,hfile,idlist)
                        ll = len(file_list)
                        if ll==1:
                            # we found the file, get its topicid
                            l0 = file_list[0]
                            htopic2 = l0['topicid']
                            filedir = os.path.dirname(f)
                            newdir = l0['directory']
                            reldir = os.path.relpath(newdir,filedir)
                            # will this topicid satisfy the reference?
                            ret2 = findHref(item,newdir,hfile,htopic2,hcontent,idlist)
                            if ret2:
                                # this topicid is OK, use it instead
                                newref = makeRef(reldir,hfile,htopic2,hcontent)
                                if dbgflag:
                                    print("FixHrefs #3 succeeds",newref)
                                                            
                        else:
                            if ll>0:
                                print(" file",hfile,"found in",ll,"places, cannot fix")
                                if dbgflag:
                                    for ffl in file_list:
                                        print(ppath(fpath(ffl)))
                            else:
                                if dbgflag:
                                    print(" file",hfile,"not found")
                                
                if newref!="":
                    # we have a changed reference, fix it in the source file
                    print("  change from:",r,oldref)
                    print("           to:",r,newref)
                    e.set(r,newref)
                    fixed=fixed+1
                    
                else:
                    if dbgflag:
                        print("FixHrefs, all fixes failed, giving up")

    # check for logic error
    if oldref==None:
        print("FixHrefs ERROR",href,"not found")
        
    return fixed
                        
        
                        


                
            
