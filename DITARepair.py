###################################
# PROLOG SECTION
# DITARepair.py
#
# A program that repairs references in a set of
# DITA source files.
#
# Tested with Python 3.12.2
# May 21, 2024
#
# Author: Dick Johnson
#
###################################

###################################
# ENVIRONMENT SETUP SECTION
###################################

# import needed modules
from xml.etree.ElementTree import *
from xml.parsers.expat import *
import sys
import os
import xml.dom.minidom

# setting this to True traces execution in great detail
dbgflag = False

# possible DITA filetype tuple
ditatypes = (".dita",".ditamap",".xml")

# types of list searches and href replacements
TYPE_DIR = 1
TYPE_FILE = 2
TYPE_TOPICID = 3
TYPE_CONTENTID = 4
TYPE_EXT = 5

###################################
# FUNCTION DEFINITION SECTION
###################################

def MakeTree(file):
    """
    Make an element tree for an XML file.
    """
    tmptree=ElementTree()
    # parse the file into a tree
    try:
        # file was parsed, return the tree
        tmptree.parse(file)
        return tmptree
    except ExpatError as e:
        # parsing failed, print out why
        print("MakeTree: error, file "+file+" not parsed.")
        print("  parser returned ExpatError",e)
        return False
    
    except:
        # error other than a parsing error
        print("MakeTree: error, file "+file+" not parsed.")
        print("parser returned",sys.exc_info()[0])
        return False
#
# Function to get the DOCTYPE for a file (if any)
#
def GetDOCTYPE(f):
    
    # create a Document object
    try:
    	doc = xml.dom.minidom.parse(f)
    except:
    	# parsing failed, return no doctype
    	return None
    
    # get the DocumentType for the doc
    dtype = doc.doctype
  
    # see if the doc has a DOCTYPE
    if dtype != None:
        # return what is in DOCTYPE
        doctype = dtype.toxml()
    else:
        doctype=None

    # free up resources 
    doc.unlink()
       
    return doctype

#
# Function to return a list of all source files
# in a directory.
#
def FindSourceFiles(filelist,dir):
    if dbgflag:
        print("Enter FindSourceFiles",dir)
    rc = True

    
    # validate we have a directory
    if os.path.isdir(dir) != True:
        print("Error",dir,"is not a directory")
        return False

    # temporary list of all files in the directory
    allfiles = os.walk(dir)

    # check the files one at a time to see if they
    # are DITA source files
    for f in allfiles:
        # get current directory
        fdir = f[0]
        # get list of files in this directory
        flist = f[2]
        for ff in flist:
            fpath = os.path.join(fdir,ff)
            # is it a source file?
            if isDITAext(ff):
                # file type is OK, check for DOCTYPE
                doctype = GetDOCTYPE(fpath)
                # remember file location and maybe DOCTYPE for it
                filelist.append([fpath,doctype])
            else:
                # non-source file, remember where we found it
                filelist.append([fpath,None])
                                    
    return rc

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
# Function to test if "file" is a URL
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
    
def setdebug(flag):
    """
    Set the debug flag:
    
    True = print details of execution
    False = print minimal progress messages
    
    """
    global dbgflag
    dbgflag = flag
    if dbgflag:
        print("**setdebug - debug flag set to",dbgflag)
    return

#
# Function to collect ID information for a DITA source file
#
def ScanSouceFile(fl,ilist):
    if dbgflag:
        print("Enter ScanSouceFile",fl)

    # either scan an XML file or just enter the
    # file in the list
    f = fl[0]
    dt = fl[1]

    if dt==None:
        # don't try to scan a non-source file (it has no DOCTYPE)
        ilist.append([os.path.dirname(f),os.path.basename(f),"",[]])
    else:
        # create a tree for the DITA source file
        tree = MakeTree(f)

        # quick exit on error
        if not tree:
            return

        # get root element for file
        root = tree.getroot()
        roottag = root.tag
    
        if dbgflag:
            print(" root tag is", roottag)
        
        if roottag == 'dita':
            # there may be topics inside this topic
            topics = root.getchildren()
        else:
            topics = [root]

        # get ID info for this topic(s)
        for t in topics:
            ScanTopic(t,f,ilist)
        
    
    return

#
# Function to scan a file topic for IDs
#
def ScanTopic(t,f,ilist):
    if dbgflag:
        print("Enter ScanTopic",f,t.tag)

    # try to fetch the topic ID
    topicid = t.get("id", default="")
    # file path split
    topicdir=os.path.dirname(f)
    topicfile=os.path.basename(f)
    
    elementids=[]
    kids = list(t)
    # loop through all the child elements
    for kid in kids:
        if kid.tag == 'topic':
            if dbgflag:
                print("Recursive ScanTopic")
            # scan sub-topics of this topic
            ScanTopic(kid,f,ilist)
        else:
            # collect all the content IDs
            ScanContentIDs(kid,elementids)

    # add the ID info collected to the big ID list
    ilist.append([topicdir,topicfile,topicid,elementids])
        
    return [f]

#
# Function to  scan for content ids in a topic
#
def ScanContentIDs(t,elist):
    if dbgflag:
        print("Enter ScanContentIDs", t.tag)

    kids = t.iter()
    for kid in kids:
        id = kid.get('id')
        if id != None:
            elist.append(id)

    
#
# Function to check all hrefs in a file.
# If fixflag is True and there is a broken href,
# try to fix it.
#
def CheckHrefs(fl,flag):
    if dbgflag:
        print("Enter CheckHrefs",fl,flag)

    # types of reference attributes to check
    refs=('href','conref')

    # count of references fixed
    fixed = 0

    # set the file and doctype
    f = fl[0]
    dt = fl[1]

    # skip files that are not DITA source files (i.e. no DOCTYPE)
    if dt==None:
        return
    
    # parse the file
    tree = MakeTree(f)

    # bail on strange parse error
    if tree == False:
        print("CheckHrefs error parsing",f)
        return

    # get the root element in the file
    root = tree.getroot()
    # prepare to iterate over elements
    iter = root.iter()
    
    # loop on all elements
    for e in iter:
        # inner loop on type of reference
        for r in refs:
            # get the reference string
            hr = e.get(r)
            # save current reference value
            oldref = hr
            if hr != None:
                # we have a reference!
                if dbgflag:
                    print("  ",r,hr)
                # parse the reference
                hdir, hfile, htopic, hcontent = parseHref(hr)
                # try to find this href in a source file
                ret = findHref(f,hdir,hfile,htopic,hcontent)
                # did we find it?
                if ret==False:
                    # reference is bad
                    newref = ""
                    print("Bad reference:",f)
                    print("  -> ",hr)

                    if hr[0]!="#":  # search if file was given                              
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
                            # try to find file with new extension
                            ret2=findHref(f,hdir,hfile2,htopic,hcontent)
                            if ret2:
                                # we found the ref in a file with a
                                # different file extension
                                newref = makeRef(hdir,hfile2,htopic,hcontent)
                            
                    if hr[0]!="#" and newref=="":
                        # Fix #2: try looking for file in another directory
                        file_list = returnList(TYPE_FILE,hfile,idlist)
                        ll = len(file_list)
                        if ll==1:
                            # we found the file in another directory
                            l0 = file_list[0]
                            filedir = os.path.dirname(f)
                            newdir = l0[0]
                            reldir = os.path.relpath(newdir,filedir)
                            # will this file satisfy the reference?
                            ret2 = findHref(f,reldir,hfile,htopic,hcontent)
                            if ret2:
                                # this file is OK, use it instead
                                newref = makeRef(reldir,hfile,htopic,hcontent)
                        else:
                            print(" file",hfile,"found in",ll,"places")
                            for ffl in file_list:
                                print(ffl[0]+os.sep+ffl[1])

                    if newref=="":
                        # Fix #3: try looking for new topicid in same file
                        file_list = returnList(TYPE_FILE,hfile,idlist)
                        ll = len(file_list)
                        if ll==1:
                            # we found the file, get its topicid
                            l0 = file_list[0]
                            htopic2 = l0[2]
                            filedir = os.path.dirname(f)
                            newdir = l0[0]
                            reldir = os.path.relpath(newdir,filedir)
                            # will this topicid satisfy the reference?
                            ret2 = findHref(f,reldir,hfile,htopic2,hcontent)
                            if ret2:
                                # this topicid is OK, use it instead
                                newref = makeRef(reldir,hfile,htopic2,hcontent)
                                                            
                        else:
                            if ll>0:
                                print(" file",hfile,"found in",ll,"places, cannot fix")
                                for ffl in file_list:
                                    print(ffl[0]+os.sep+ffl[1])
                            else:
                                if hr[0]!="#":
                                  print(" file",hfile,"not found")
                                
                    if newref!="":
                        # we have a changed reference, fix it in the source file
                        print("  change from:",r,oldref)
                        print("           to:",r,newref)
                        # are we running in fix mode?
                        if flag==True:
                            if fixed==0:
                                # read the file into a string
                                outfile=f
                                fout = open(outfile,"r")
                                fstr = fout.read()
                                fout.close()
                            
                            fixed = fixed + 1
                            olds = r+"="+'"'+oldref+'"'
                            news = r+"="+'"'+newref+'"'
                            # update the reference
                            fstr=fstr.replace(olds,news)

    # check to see if we changed the input. If so, rewrite it.
    #
    # note: we have to use string operations to replace references,
    #  because the elementTree routines don't preserve several
    #  things in the original source file, including:
    #    the <xml> top line
    #    the DOCTYPE
    #    any <!-- ... -> comment lines
    #
    if fixed>0:
        fout = open(outfile,"w")
        fout.write(fstr)
        fout.close()
        print("writing",fixed,"changes to",outfile)
        
                        
                        
#
# Function to create a reference string from its parts
#
def makeRef(d,f,t,c):
    if dbgflag:
        print("Enter makeRef",d,f,t,c)

    ref=d+"/"+f
    if t!="":
        ref=ref+"#"+t
        if c!="":
            ref=ref+os.sep+c

    return ref

#
# Function that searches for a match to an href in the big list
#
def findHref(f,hdir,hfile,htopic,hcontent):
    if dbgflag:
        print("Enter findHref",f,hdir,hfile,htopic,hcontent)
       
    rc = True

    # don't check URL references
    if isURL(hdir)==True or isURL(hfile)==True:
        return True
    
    fdir = os.path.dirname(f)
    fbase = os.path.basename(f)

    # get a normalized path to look for
    if len(hdir)>0:
        fpath=os.path.normpath(fdir+os.sep+hdir)
    else:
        fpath=fdir
    
    # look for directory path first
    path_list = returnList(TYPE_DIR, fpath, idlist)
    # we have files in the specified directory
    if len(path_list)>0:
        # next check files in the directory
        file_list = returnList(TYPE_FILE,hfile,path_list)
        #print("file_list",file_list)
        if len(file_list)>0:
            # we found file(s) that match as well
            if htopic!="":
                # check topicid
                top_list = returnList(TYPE_TOPICID,htopic,file_list)
                if hcontent!="":
                    # check contentid
                    con_list = returnList(TYPE_CONTENTID,hcontent,top_list)
                    if len(con_list)>0:
                        rc = True
                    else:
                        rc = False
                else:
                    # no contentid is present
                    rc = True
            else:
                # no topicid is present
                rc = True
        else:
            # file was not found
            rc = False
    else:
        # directory was not found
        rc = False
    
           
    return rc

#
# Function to return list of matches in a larger list
#
def returnList(mtype, s, inlist):
    if dbgflag:
        print("Enter returnList",mtype,s,len(inlist))

    retlist = []

    for idx in inlist:
        if mtype==TYPE_DIR:
            if s==idx[0]:
                retlist.append(idx)

        elif mtype==TYPE_FILE:
            if idx[1]==s:
                retlist.append(idx)

        elif mtype==TYPE_TOPICID:
            if idx[2]==s:
                retlist.append(idx)

        elif mtype==TYPE_CONTENTID:
            if s in idx[3]:
                retlist.append(idx)

        else:
            print("Error, mtype=",mtype)
            
    return retlist
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
            pp=rest.find('/')
            if pp>-1:
                htopic=rest[0:pp]
                hcontent=rest[pp+1:]
            else:
                htopic=rest
    
    return hdir, hfile, htopic,hcontent

###################################
# PROCESSING INITIALIZATION SECTION
###################################

setdebug(False)

# set the directory to search and the flag that
# controls whether we make any changes
fixflag = False
source_dir = os.getcwd()

for i in range(len(sys.argv)):
   if i==1:
        fixstr=sys.argv[i]
        fixstr=fixstr.upper()
        if fixstr[0]=="Y":
            fixflag = True
       
print("DITARepair:", source_dir)
if fixflag:
    print(" bad references will be fixed")
else:
    print(" scan only")

###################################
#
# MAIN PROCESSING SECTION
#
###################################

filelist = []
# get the list of files to scan
FindSourceFiles(filelist,source_dir)

lfl = len(filelist)
if lfl>0:
    print("Processing", len(filelist), "files.")
else:
    print("no files found")
    

if dbgflag:
    print("Files found:")
    for fl in filelist:
        print(fl[0], fl[1])
    
# build up ID information for all the files
idlist=[]
for f in filelist:
    ScanSouceFile(f,idlist)

# if debugging, dump out ids we found
if dbgflag:
    for idx in idlist:
        print(idx[0])
        print("  ",idx[1],idx[2],idx[3])

# scan all files checking hrefs and (optionally) fix problems
for f in filelist:
    CheckHrefs(f,fixflag)
    
print("DITARepair: exit")
