#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import copy
import gzip
from dateutil import tz
import jinja2
import logging
import argparse
import magic
import os
import re
import datetime
import locale
import cPickle
import bokeh.charts
import bokeh.io
from itertools import islice
import pdfkit
import pytz
import Util
import webcolors
import threading
import signal

__author__ = 'Andreas Bader'
__version__ = "0.03"

# Helpscript if you need a quick diagram!

plotColorDict={"DEFAULT" : "blue",
               "INSERT0" : "red",
               "INSERT1" : "darkred",
               "READ0" : "orange",
               "READ1" : "darkorange",
               "CLEAN0" : "green",
               "CLEAN1" : "darkgreen",
               "UPDATE0" : "purple",
               "UPDATE1" : "darkpurple"
               }

defaultPlotColor=plotColorDict["DEFAULT"]
convertFromUsToMs = ["AverageLatency(us)", "MinLatency(us)", "MaxLatency(us)", "99thPercentileLatency(us)", "95thPercentileLatency(us)" ]

def openCompressedFile(ycsbfile, dict, key, logger):
    try:
        file = gzip.open(ycsbfile,"r")
        dict[key]=cPickle.load(file)
        file.close()
    except Exception, e:
        logger.error("Can't open '%s'. Is it really a compressed .ydc file?" %(ycsbfile), exc_info=True)
        os._exit(-1)

def decompressFile(fileDict, newFileName,logger):
    neededKeys = ["timeseries","granularity","description","bucket","startTime","startLoadTime","runtimeLoad",
                  "throughputLoad","description","endLoadTime","startRunTime","runtimeRun","throughputRun",
                  "description","endRunTime", "endTime", "spaceBegin", "blocks", "errors", "warnings", "exceptions"]
    neededBlockKeys = ["Operations","LatencyList","MaxLatency(us)","MinLatency(us)","99thPercentileLatency(us)",
                       "95thPercentileLatency(us)", "AverageLatency(us)"]
                       # return not in this list, as CLEANUP blocks have no return
    for key in neededKeys:
        if key not in fileDict.keys():
            logger.error("'%s' is missing in ydc file, abort." %(key))
            return False
    file = open("%s" % (newFileName), "w")
    if "timeseries" in fileDict.keys():
        if fileDict["timeseries"]:
            file.write("TIMESERIES: 1\n")
        else:
            file.write("TIMESERIES: 0\n")
    if "granularity" in fileDict.keys():
        file.write("GRANULARITY: %s\n" %(fileDict["granularity"]))
    if "dbDesc" in fileDict.keys():
        des=fileDict["dbDesc"]
        if des[-1] == "\n":
            des = des[:-1]
        file.write("DESCRIPTION: %s\n" %(des))
    if "bucket" in fileDict.keys():
        file.write("BUCKET: %s\n" %(fileDict["bucket"]))
    if "startTime" in fileDict.keys():
        file.write("START: %s: Start Test\n" %(fileDict["startTime"].strftime('%a %b %d %H:%M:%S %Z %Y')))
    if "startLoadTime" in fileDict.keys():
        file.write("START: %s: Start Load\n" %(fileDict["startLoadTime"].strftime('%a %b %d %H:%M:%S %Z %Y')))
    if "runtimeLoad" in fileDict.keys():
        file.write("[OVERALL], RunTime(ms), %s\n" %(fileDict["runtimeLoad"]))
    if "throughputLoad" in fileDict.keys():
        file.write("[OVERALL], Throughput(ops/sec), %s\n" %(fileDict["throughputLoad"]))
    ## load blocks
    for key in ["CLEANUP", "INSERT" ]:
        if key in fileDict["blocks"] and len(fileDict["blocks"][key]) > 0:
            for key2 in neededBlockKeys:
                if key2 not in fileDict["blocks"][key][0].keys():
                    logger.error("'%s' is missing in ydc file block '%s'0, abort." %(key2, key))
                    return False
            if "Operations" in fileDict["blocks"][key][0].keys():
                file.write("[%s], Operations, %s\n" %(key,fileDict["blocks"][key][0]["Operations"]))
            if "AverageLatency(us)" in fileDict["blocks"][key][0].keys():
                file.write("[%s], AverageLatency(us), %s\n" %(key,fileDict["blocks"][key][0]["AverageLatency(us)"]))
            if "MinLatency(us)" in fileDict["blocks"][key][0].keys():
                file.write("[%s], MinLatency(us), %s\n" %(key,fileDict["blocks"][key][0]["MinLatency(us)"]))
            if "MaxLatency(us)" in fileDict["blocks"][key][0].keys():
                file.write("[%s], MaxLatency(us), %s\n" %(key,fileDict["blocks"][key][0]["MaxLatency(us)"]))
            if "95thPercentileLatency(ms)" in fileDict["blocks"][key][0].keys():
                file.write("[%s], 95thPercentileLatency(ms), %s\n" %(key,fileDict["blocks"][key][0]["95thPercentileLatency(ms)"]))
            if "99thPercentileLatency(ms)" in fileDict["blocks"][key][0].keys():
                file.write("[%s], 99thPercentileLatency(ms), %s\n" %(key,fileDict["blocks"][key][0]["99thPercentileLatency(ms)"]))
            if "Return" in fileDict["blocks"][key][0].keys():
                for returnVal in fileDict["blocks"][key][0]["Return"]:
                    file.write("[%s], Return=%s, %s\n" %(key,returnVal[0],returnVal[1]))
            if "LatencyList" in fileDict["blocks"][key][0].keys():
                for counter in range(0,len(fileDict["blocks"][key][0]["LatencyList"])-1):
                    file.write("[%s], %s, %s\n" %(key, counter, fileDict["blocks"][key][0]["LatencyList"][counter]))
                file.write("[%s], >%s, %s\n" %(key, len(fileDict["blocks"][key][0]["LatencyList"])-1, fileDict["blocks"][key][0]["LatencyList"][-1]))
            # block latency data
    if "description" in fileDict.keys():
        des=fileDict["description"]
        if des[-1] == "\n":
            des = des[:-1]
        file.write("[DESCRIPTION], %s\n" %(des))
    if "endLoadTime" in fileDict.keys():
        file.write("END: %s: End Load\n" %(fileDict["endLoadTime"].strftime('%a %b %d %H:%M:%S %Z %Y')))
    if "startRunTime" in fileDict.keys():
        file.write("START: %s: Start Run\n" %(fileDict["startRunTime"].strftime('%a %b %d %H:%M:%S %Z %Y')))
    if "runtimeRun" in fileDict.keys():
        file.write("[OVERALL], RunTime(ms), %s\n" %(fileDict["runtimeRun"]))
    if "throughputRun" in fileDict.keys():
        file.write("[OVERALL], Throughput(ops/sec), %s\n" %(fileDict["throughputRun"]))
    ## run blöcke
    for key in ["CLEANUP", "INSERT", "READ", "UPDATE", "SCAN", "AVG", "SUM", "COUNT"]:
        if key in fileDict["blocks"] and len(fileDict["blocks"][key]) > 0:
            for index in range(0,len(fileDict["blocks"][key])):
                if index == 0 and key in ["CLEANUP", "INSERT" ]:
                    # First Cleanup/Insert block is from load phase -> ignore it
                    continue
                for key2 in neededBlockKeys:
                    if key2 not in fileDict["blocks"][key][index].keys():
                        logger.error("'%s' is missing in ydc file block '%s'0, abort." %(key2, key))
                        return False
                if "Operations" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], Operations, %s\n" %(key,fileDict["blocks"][key][index]["Operations"]))
                if "AverageLatency(us)" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], AverageLatency(us), %s\n" %(key,fileDict["blocks"][key][index]["AverageLatency(us)"]))
                if "MinLatency(us)" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], MinLatency(us), %s\n" %(key,fileDict["blocks"][key][index]["MinLatency(us)"]))
                if "MaxLatency(us)" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], MaxLatency(us), %s\n" %(key,fileDict["blocks"][key][index]["MaxLatency(us)"]))
                if "95thPercentileLatency(ms)" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], 95thPercentileLatency(ms), %s\n" %(key,fileDict["blocks"][key][index]["95thPercentileLatency(ms)"]))
                if "99thPercentileLatency(ms)" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], 99thPercentileLatency(ms), %s\n" %(key,fileDict["blocks"][key][index]["99thPercentileLatency(ms)"]))
                if "Return" in fileDict["blocks"][key][index].keys():
                    for returnVal in fileDict["blocks"][key][index]["Return"]:
                        file.write("[%s], Return=%s, %s\n" %(key,returnVal[index],returnVal[1]))
                if "LatencyList" in fileDict["blocks"][key][index].keys():
                    for counter in range(0,len(fileDict["blocks"][key][index]["LatencyList"])-1):
                        file.write("[%s], %s, %s\n" %(key, counter, fileDict["blocks"][key][index]["LatencyList"][counter]))
                    file.write("[%s], >%s, %s\n" %(key, len(fileDict["blocks"][key][index]["LatencyList"])-1, fileDict["blocks"][key][index]["LatencyList"][-1]))
    if "description" in fileDict.keys():
        des=fileDict["description"]
        if des[-1] == "\n":
            des = des[:-1]
        file.write("[DESCRIPTION], %s\n" %(des))
    if "endRunTime" in fileDict.keys():
        file.write("END: %s: End Run\n" %(fileDict["endRunTime"].strftime('%a %b %d %H:%M:%S %Z %Y')))
    if "endTime" in fileDict.keys():
        file.write("END: %s: End Test\n" %(fileDict["endTime"].strftime('%a %b %d %H:%M:%S %Z %Y')))
    if "errors" in fileDict.keys():
        for line in fileDict["errors"]:
            line2 = line
            if line2[-1] == "\n":
                line2=line2[:-1]
            file.write("%s\n" %(line2))
    if "exceptions" in fileDict.keys():
        for line in fileDict["exceptions"]:
            line2 = line
            if line2[-1] == "\n":
                line2=line2[:-1]
            file.write("%s\n" %(line2))
    if "warnings" in fileDict.keys():
        for line in fileDict["warnings"]:
            line2 = line
            if line2[-1] == "\n":
                line2=line2[:-1]
            file.write("%s\n" %(line2))
    if "spaceBegin" in fileDict.keys() and "spaceBetween" in fileDict.keys() and "spaceEnd" in fileDict.keys():
        file.write("SPACE: %s %s %s\n" %(fileDict["spaceBegin"],fileDict["spaceBetween"],fileDict["spaceEnd"]))
    file.flush()
    file.close()

# replaces bokeh.charts.Bar because it can't do logarithmic scale
def generate_bar_plot(dataDict, cat, legendPos, title, ylabel, xlabel, width, height, logger):
    maxValue=0
    for dataKey in dataDict.keys():
        for dataPoint in dataDict[dataKey]:
            if dataPoint >= maxValue:
                try:
                    dataPointStr = str(dataPoint)
                    if "." in dataPointStr:
                        dataPointStr = dataPointStr.split(".")[0]
                    maxValue = 10**len(dataPointStr)
                except:
                    logger.error("Can't convert '%s' to string. Can't generate bar plot." %(dataPoint))
                    return None
    if maxValue == 0:
        logger.error("Maximum value is 0. Can't generate bar plot.")
        return None
    p = bokeh.plotting.figure(title=title, y_axis_type="log", x_range=cat, y_range=[0,maxValue], width=width, height=height)
    dataLen = -1
    for dataKey in dataDict.keys():
        if dataLen == -1:
            dataLen = len(dataDict[dataKey])
        else:
            if dataLen != len(dataDict[dataKey]):
                logger.error("Some dataLists in dataDict have different lengths. Can't generate bar plot.")
                return None
    if dataLen == -1:
        logger.error("Can't find list length. Can't generate bar plot.")
        return None
    keyLen = float(len(dataDict.keys()))

    groupSep = min(max(0.0015,1.0/dataLen),0.1)
    barSep = min(max(0.00015,1.0/keyLen),0.025)
    barStart = (groupSep - (barSep*(keyLen/2.0)) + barSep)/2.0
    barWidth = max((1.0-groupSep-(barSep*keyLen))/keyLen,0.005)
    #groupSep = 0.2
    defaultColors=[66,88,104,32,131,143,40,92,41,45]
    # colors that are hard to see against white (see http://www.w3schools.com/cssref/css_colornames.asp)
    chosenColors=[122,48,144,142,109,24,107,55,126,90,91,36,112,76,133,103,130,128,132,94,46,6,58,14,146,70,23,28,96,10,20,99,80,113,31,137]
    for dataKey in sorted(dataDict.keys()):
        left=[]
        right=[]
        top=[]
        bottom=[]
        color = Util.get_random_int_with_chosen_default(0, len(webcolors.css3_names_to_hex),chosenColors,defaultColors)
        if color == None:
            logger.error("Not enough colors. Can't generate bar plot.")
            return None
        chosenColors.append(color)
        for dataPoint in dataDict[dataKey]:
            if len(right) != len(left) != len(top):
                logger.error("Some error occured. Can't generate bar plot.")
                return None
            counter=len(left)+1-((barWidth*keyLen)+groupSep+(barSep*(keyLen/2.0)))/2.0
            left.append(counter+barStart)
            right.append(counter+barStart+barWidth)
            top.append(dataPoint)
            bottom.append(0)
            logger.info("%s %s %s %s %s %s %s %s %s" %(dataKey, barStart, barWidth, dataLen, counter, groupSep, barSep, left,right))
        #p.quad(bottom=bottom, top=top, left=left, right=right, color=webcolors.css3_names_to_hex[webcolors.css3_names_to_hex.keys()[color]], legend="%s_%s"%(dataKey,counter2))
        # There is an error on Bokeh in the line above: If any of the top values is zero, alle bars/quads will be drawn as zero. Drawing them non-grouped fixes this.
        # This is independent from the set y-range (-1 or 0 does not effect this)
        # See https://github.com/bokeh/bokeh/issues/3022
        for i in range(0,len(top)):
            p.quad(bottom=bottom[i], top=top[i], left=left[i], right=right[i], color=webcolors.css3_names_to_hex[webcolors.css3_names_to_hex.keys()[color]], legend=dataKey)
        barStart+= barWidth + barSep
    p.xaxis.axis_label_text_font_size = "10pt"
    p.yaxis.axis_label_text_font_size = "10pt"
    p.yaxis.axis_label = ylabel
    p.xaxis.axis_label = xlabel
    #p.y_range = (0, 10000)
    p.legend.orientation = legendPos
    return p

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="ProcessYcsbLog.py",version=__version__,description="Generates some special diagrams (not needed for pyTsdbBench). Only supportd .ydc files.", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-l", "--log", action='store_true', help="Be more verbose")
parser.add_argument("-f", "--ycsbfiles", metavar="YCSBFILE", nargs='+', required=True, help="Path to YCSB YDC file(s).")
parser.add_argument("-o", "--overwrite", action='store_true', help="Overwrite existing files")
parser.add_argument("-k", "--keys", metavar="KEYS",nargs='+', required=True, choices=['COUNT', 'INSERT', 'SCAN', 'SUM', 'CLEANUP', 'AVG', 'READ'],  help="Which key do you want to use? (only takes first one!)")
parser.add_argument("-t", "--type", metavar="TYPE", required=True, choices=['MaxLatency(us)', 'MinLatency(us)', '99thPercentileLatency(ms)', '95thPercentileLatency(ms)', 'AverageLatency(us)'],  help="Which type do you want to use?")

args = parser.parse_args()

# Configure Logging
logLevel = logging.WARN
if args.log:
    logLevel = logging.DEBUG
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

dicts={}
nameDict={} # stores names for dictKeys
threads=[]
for ycsbfile in args.ycsbfiles:
    # Compressing Output
    mime = magic.open(magic.MAGIC_MIME)
    mime.load()
    try:
        basename="%s" %(os.path.splitext(os.path.basename(ycsbfile))[0]).split("_")[1]
    except IndexError:
        logger.warning("'%s' is not a normal filename for ycsb-ts logfiles." %(os.path.basename(ycsbfile)))
        basename="%s" %(os.path.splitext(os.path.basename(ycsbfile))[0])
    except:
        logger.error("Can't process filename '%s' as basename." %(os.path.basename(ycsbfile)))
        os._exit(-1)
    if basename in dicts.keys():
        basename="%s_%s" %(basename,dicts.keys().count(basename)+1)
    # print unicode(ycsbfile.decode('utf8').encode('utf8'))
    if mime.file(ycsbfile) == "application/gzip; charset=binary":
        # if a compressed file is found do decompress or graph
        logger.info("Found Mime type '%s' in '%s'." %(ycsbfile,mime.file(ycsbfile)))
        # if decompress is what you want...
        if Util.check_file_exists(ycsbfile) and os.access(ycsbfile, os.R_OK):
            dicts[basename] = {}
            nameDict[basename]=os.path.splitext(os.path.basename(ycsbfile))[0]
            threads.append(threading.Thread(target=openCompressedFile, args=(ycsbfile, dicts, basename, logger)))
            threads[-1].setDaemon(True)
            threads[-1].start()
        else:
            logger.error("Can't open '%s'. Does it exist?" %(ycsbfile), exc_info=True)
            exit(-1)

    else:
        logger.error("%s has an unkown mimetype '%s', sure it is a ycsb log or .ydc file?" %(ycsbfile,mime.file(ycsbfile)))
        exit(-1)


def generate_plot(dicts, keys, type, overwrite, logger, fileName = None):
    if not fileName:
        fileName = "ycsb_combined_%s_%s.html" % (type.rsplit("(")[0].lower(),datetime.datetime.now().strftime("%Y%m%d%H%M"))
    dataDict={}
    factor=1.0
    if type in convertFromUsToMs:
        factor=0.001
    for dicKey in sorted(dicts.keys()):
        if not "blocks" in dicts[dicKey].keys():
            logger.error("\"blocks\" not found in %s." %(dicKey))
            return False
        else:
            for key in keys:
                if not key in dicts[dicKey]["blocks"].keys():
                    logger.error("\"%s\" not found in %s." %(key, dicKey))
                    return False
                else:
                    if len(dicts[dicKey]["blocks"][key]) < 1:
                        logger.error("\"%s\" has zero arrays in %s." %(key, dicKey))
                        return False
                    elif len(dicts[dicKey]["blocks"][key]) > 1:
                        logger.warning("\"%s\" has more than one array in %s, only using first one." %(key, dicKey))
                    if type not in dicts[dicKey]["blocks"][key][0].keys():
                        logger.error("\"%s\" not in first array of \"%s\" in %s." %(type, key, dicKey))
                        return False
                    if dicKey not in dataDict.keys():
                        dataDict[dicKey]=[]
                    dataDict[dicKey].append(dicts[dicKey]["blocks"][key][0][type]*factor)
    if Util.check_file_exists(fileName):
        if overwrite:
            if not Util.delete_file(fileName, logger, True):
                logger.error("\"%s\" does exist, overwrite is enabled, overwrite failed. Please delete manually. Abort." %(fileName))
                return False
        else:
            logger.error("\"%s\" does exist, overwrite is disabled. Abort." %(fileName))
            return False
    bokeh.plotting.output_file(fileName)
    barPlot = generate_bar_plot(dataDict, keys, "top_right", "Comparison of %s" %(type.rsplit("(")[0]), "Latency in ms", "Querytype", 1000, 650, logger)
    bokeh.io.save(barPlot)
    return True


# Wait until all threads are done
logger.debug("Waiting until all files are loaded...")
# only join() would make ctrl+c not work in combination with daemon=true
# Main thread is always there, because of that: >1
while threading.activeCount() > 1:
    for thread in threads:
        thread.join(100)
threads=[]

if len(dicts.keys())==len(args.ycsbfiles) or True:
    for type in convertFromUsToMs:
        db_names = '-'.join([f.split('_')[1] for f in args.ycsbfiles])
        type_name = type.split("(")[0].lower()
        filename = 'ycsb_combined_%s_%s_%s.html' % (type_name, '-'.join(args.keys) ,db_names)
        print(filename)
        generate_plot(dicts, args.keys, args.type, args.overwrite, logger, filename)
else:
    logger.error(" %s Files and %s Dicts do not match, this should not happen." %(len(args.ycsbfiles),len(dicts.keys())))
    exit(-1)

exit(0)