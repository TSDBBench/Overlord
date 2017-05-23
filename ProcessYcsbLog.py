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
from itertools import islice
import pdfkit
import pytz
import Util
import webcolors
import threading
import signal

__author__ = 'Andreas Bader'
__version__ = "0.03"

# in 0.02 some dicts were replaced with lists.
# reason: when parsing large result files (100k buckets = 400k lines)
# <dict>.keys() is getting relatevly slow, but amound of keys stays the same
# which is kind of strange
# so replacing those dicts with lists helps a great deal
# also some other speed-affecting changes were made
# Threading, blockwise-reading etc.
# some variable names will a bit weird (like <something>Dict for a list) because of this
# Also since 0.02 we won't save the whole log file into ydc anymore, as this seem to be a bit overkill
# This should not affect older 0.01 logs, but could happen. However, "LatencyList" was renamed, so this version can't read 0.01 anymore.
# Also correct timezone awareness was added
# 0.03 calculates 99% and 95% also in us, old files cannot be read. This reflects the update to YCSB 0.4.0
# For reading 0.2.0 files, replace "99thPercentileLatency(us)" with "99thPercentileLatency(ms)" and for 95th accordingly
# in Line 74, 75, 156, 157, 1207, 1208, 1252, 1253, 1254, 1255, 1296, 1297, 1298, 1299

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
maxTableColumnsSingle=6
maxTableColumnsMulti=10

templateFile="template.html" #Jinja2 Template, see http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh.embed.file_html
templateFileMulti="template_multi.html" #Jinja2 Template, see http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh.embed.file_html

pdfOptions = {
    'page-size': 'A4',
    'margin-top': '0.5cm',
    'margin-right': '0.5cm',
    'margin-bottom': '0.5cm',
    'margin-left': '0.5cm',
    'encoding': "UTF-8",
    'no-outline': None,
    'quiet': '',
    'dpi' : 600,
    'image-dpi' : 600,
    'image-quality' : 94,
    'title' : ""
}

ignoreParams = ["Operations", "Return", "LatencyList"] # parameters that should be ignored (LatencyList e.g.)
possibleMissingParams = ["99thPercentileLatency(us)","95thPercentileLatency(us)"] #Params that can be missing, replaced by -1
convertFromUsToMs = ["AverageLatency(us)", "MinLatency(us)", "MaxLatency(us)", "99thPercentileLatency(us)","95thPercentileLatency(us)" ] # Some special parameters need to be converted

def signal_handler(signal, frame):
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

def find_time(timeString,logger):
    timeRegex="[A-Za-z]+\s+[A-Za-z]+\s+[0-9]+\s+[0-9]+:[0-9]+:[0-9]+\s+[A-Za-z]+\s+[0-9]+"
    if re.search(timeRegex,timeString) != None:
        act_loc=locale.getlocale()
        try:
            locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
        except Exception, e:
            logger.error('Failed to set locale, do you have locale en_US.UTF-8 installed?', exc_info=True)
            os._exit(-1)
        try:
            timeObj=datetime.datetime.strptime(re.search(timeRegex,timeString).group(), '%a %b %d %H:%M:%S %Z %Y')
            timeObj=timeObj.replace(tzinfo=tz.gettz(re.search(timeRegex,timeString).group().split(" ")[4]))
            locale.setlocale(locale.LC_ALL,act_loc)
            return timeObj
        except Exception, e:
            logger.warning("Failed to parste timezone from '%s', got '%s'. Setting it to UTC, this may be wrong."
                           %(re.search(timeRegex,timeString).group(),
                             re.search(timeRegex,timeString).group().split(" ")[4]), exc_info=True)
            timeObj=timeObj.replace(tzinfo=tz.gettz('UTC'))
            locale.setlocale(locale.LC_ALL,act_loc)
            return timeObj
    else:
        logger.error("Can't find time in '%s'." %(timeString))
        os._exit(-1)

# converts timestring to timeobject
# checks if value is already set (should not happen that a value is found twice)
def process_time(line,key,dict,logger):
    if key in dict.keys():
        logger.error("Found two %s, this should not happen!" %(key))
        os._exit(-1)
    dict[key] = find_time(line,logger)

# converts spacestring
def process_space(line, dict,logger):
    spaceSplitters = line.replace("SPACE: ","").split(" ")
    if len(spaceSplitters) == 3:
        dict["spaceBegin"] = spaceSplitters[0]
        dict["spaceBetween"] = spaceSplitters[1]
        dict["spaceEnd"] = spaceSplitters[2]
    else:
        logger.error("Error while processing space string '%s'" %(line))
        os._exit(-1)

# converts float (throughput, runtime)
def process_float(line, dict, key, logger):
    splitters = line.split(", ")
    if len(splitters) == 3:
        dict[key] = float(splitters[2])
    else:
        logger.error("Error while processing float string '%s'" %(line))
        os._exit(-1)

# checks if we have a line according to one of the known blocks
def check_block(line, knownBlocktypes):
    for type in knownBlocktypes:
        if re.search("^\[%s\]" %(type),line) != None:
            return True
    return False

# parses one actual line (=value) into a existing block dict
# blockDict = dict which contains values of the actual block (block ex. READ)
# two typical ycsb lines as example:
# [READ], 99thPercentileLatency(us), 4
# [READ], 0, 397
# this translates as follows to the arguments:
# [blockName], name, value
# rewrote in 0.02 for using lists in some steps instead of dicts, brings some speedup!
def parse_block(blockDict, blockName, name, value, timeSeries, logger):
    # save every known name + conversion method
    knownValues={"Operations": int,
                 "AverageLatency(us)" : float,
                 "MinLatency(us)" : int,
                 "MaxLatency(us)" : int,
                 "95thPercentileLatency(us)": int,
                 "99thPercentileLatency(us)" : int}
    if name in knownValues.keys():
        # Check if value was already found in this block, should not happen!
        if name not in blockDict.keys():
            try:
                blockDict[name] = knownValues[name](value)
            except ValueError:
                logger.error("Error while convertion in block '%s' with value '%s'." %(blockName, value))
                os._exit(-1)
        else:
            logger.error("Found another '%s' value in block '%s' with value '%s'. Should not happen." %(name, blockName, value))
            os._exit(-1)
    elif "Return=" in name:
        # Return Value looks like this name: Return=0, value: 123
        if "Return" not in blockDict.keys():
            blockDict["Return"] = []
        try:
            blockDict["Return"].append([int(name.replace("Return=","")),int(value)])
        except ValueError:
            logger.error("Error while convertion in block '%s' with value '%s'." %(blockName, value))
            os._exit(-1)
    else:
        # here we should have only histogram or timeseries values
        # ex. [READ], 0, 397
        # ex. [READ], 1, 101
        # the last value has propbably a ">" in its name, ignore that.
        try:
            if "LatencyList" not in blockDict.keys():
                blockDict["LatencyList"] = []
            if timeSeries:
                blockDict["LatencyList"].append(float(value)/1000.0)
            else:
                blockDict["LatencyList"].append(int(value))
        except ValueError:
            logger.error("Error while convertion in block '%s' with value '%s' and name '%s'." %(blockName, value, name))
            os._exit(-1)
        except:
            logger.error("Unknown error occured while convertion in block '%s' with value '%s' and name '%s'. Maybe unknwon block value?" %(blockName, value, name))
            os._exit(-1)

# processes one actual known block
# look below at process_file(..) for more explanation (data structure,..)
# actBlock should be mutable, but Strings are immutable, so actBlock should be a list with a string in it.. ;)
# rewrote in 0.02 for using lists in some steps instead of dicts, brings some speedup!
def process_block(fileDict, line, blockIndices, actBlock, timeSeries, logger):
    splitters = line.split(", ")
    if len(splitters) == 3:
        # check if it is the first block we ever encounter or if we are at a new block
        blockName=splitters[0].replace("[","").replace("]","")
        if actBlock[0] == "" or blockName != actBlock[0]:
            # save that we are in a new block
            actBlock[0] = blockName
            # check if fileDict contains the blocks dict
            if "blocks" not in fileDict.keys():
                fileDict["blocks"] = {}
            # check if dict already knews it
            if blockName not in fileDict["blocks"].keys():
                fileDict["blocks"][blockName] = []
                # fileDict["blocks"][blockName] = {}
            # search for new index if types of this block already exist
            newIndex=0
            if len(fileDict["blocks"][blockName]) > 0:
                newIndex = len(fileDict["blocks"][blockName])
            fileDict["blocks"][blockName].append({})
            parse_block(fileDict["blocks"][blockName][newIndex], blockName, splitters[1], splitters[2], timeSeries, logger)
        else:
            # okay we just have to add some value to this already seen block
            parse_block(fileDict["blocks"][blockName][-1], blockName, splitters[1], splitters[2], timeSeries, logger)
    else:
        logger.error("Error while processing line '%s'" %(line))
        os._exit(-1)

def process_file(filename, timeSeries, fileDict, compressedFileName, logger):
    if not Util.check_file_readable(filename):
        logger.error("Can't open %s." % (filename))
        return
    file = open(filename,"r")
    actBlock=[""] # saves in which type of block we are, must be mutable!
    knownBlocktypes=["CLEANUP", "INSERT", "READ", "UPDATE", "SCAN", "AVG", "SUM", "COUNT"] # saves which types of blocks we know
    # fileDict must be mutable!
    # the following keys can exist
    # dbName -> name of dbms (mysql e.q.)
    # dbDesc -> description of dbms (mysql e.q.)
    # description -> description of the workload
    # errors -> [] (errors occured)
    # warnings -> [] (warnings occured)
    # exceptions -> [] (exceptions occured)
    # workload -> name of workload (workloada e.g.)
    # startTime -> overall start time
    # endTime -> overall end time
    # startRunTime -> RUN phase start time
    # endRunTime -> RUN phase end time
    # startLoadTime -> LOAD phase start time
    # endLoadTime -> LOAD phase end time
    # spaceBegin -> Space of DB folder before any workload (before LOAD phase)
    # spaceBetween -> Space of DB folder between LOAD and RUN phase
    # spaceEnd -> Space of DB folder after RUN phase
    # runtimeLoad -> runtime (ycsb) of LOAD phase
    # runtimeRun -> runtime (ycsb) of RUN phase
    # throughputLoad -> throughput (ycsb) of RUN phase
    # throughputRun -> throughput (ycsb) of RUN phase
    # blocks -> dict of blocks (ycsb)
    # filecontent -> content of original ycsb file (ycsb) -> Dropped with 0.02!
    # timeseries -> true/false -> generate ts output (arguments can overwrite it)
    # granularity -> integer for ts granularity
    # bucket -> integer for histogram buckets
    # (ycsb) means that this is measured by ycsb

    # blocks itself looks like:
    # {"CLEANUP": {}, "INSERT": {}, "READ": {}, "UPDATE": {}}
    # the embedded dicts look like this (ex. for INSERT)
    # {0 : {}, 1 : {}} # 0 = first encountered INSERT block, 1 = second encountered INSERT block ...
    # {} contains the actual values of one block
    # ex. one READ Block (latencies are truncated)
    # [READ], Operations, 511
    # [READ], AverageLatency(us), 860.4833659491194
    # [READ], MinLatency(us), 404
    # [READ], MaxLatency(us), 14309
    # [READ], 95thPercentileLatency(us), 1
    # [READ], 99thPercentileLatency(us), 4
    # [READ], Return=0, 511
    # [READ], 0, 397
    # [READ], 1, 101
    # ...
    # the dict would be.: {"Operations" : 511, "AverageLatency(us)" : 860.4833659491194, "MinLatency(us)": 404, "MaxLatency(us)" : 14309 ,"95thPercentileLatency(us)" : 1, "99thPercentileLatency(us)" : 4, "Return" : [0,511] , "LatencyList" : {0 : 397, 1 : 101, ,...} }
    # look at https://github.com/brianfrankcooper/YCSB/wiki/Running-a-Workload how to interpret the ycsb values
    # in case timeseries instead of histogramm is used, there will be floats instead of integers as values (ex. [READ], 1, 101.11)

    # split filename to get db & workload name
    # e.g. ycsb_mysql_workloada_201507282238.log
    fileNameSplitters=filename.split("_")
    if len(fileNameSplitters) >= 4:
        fileDict["dbName"]=fileNameSplitters[1]
        for splitter in fileNameSplitters[2:len(fileNameSplitters)-2]:
            fileDict["dbName"]+="_%s" %(splitter)
        fileDict["workload"]=fileNameSplitters[len(fileNameSplitters)-2]
    else:
        logger.error("Can't parse filename '%s'." %(filename))
        os._exit(-1)
    fileDict["errors"] = [];
    fileDict["warnings"] = [];
    fileDict["exceptions"] = [];
    fileDict["description"] = "";
    # process lines
    # Using the blockwise list(islice(..)) version, as it is a little bit faster than pure 'for line in file:'
    while True:
        lines = list(islice(file, 100))
        if not lines:
            break
        for line in lines:
            if re.search("Start Test$",line) != None:
                # Starttime whole measurement
                process_time(line,"startTime", fileDict, logger)
            elif re.search("error",line.lower()) != None:
                fileDict["errors"].append(line)
            elif re.search("warn",line.lower()) != None:
                fileDict["warnings"].append(line)
            elif re.search("exception",line.lower()) != None:
                fileDict["exceptions"].append(line)
            elif re.search("^\[DESCRIPTION\]",line) != None:
                fileDict["description"] = line.replace("[DESCRIPTION],","")
                if fileDict["description"][0] == " ":
                    fileDict["description"] = fileDict["description"][1:]
                continue
            elif re.search("^DESCRIPTION",line) != None:
                try:
                    fileDict["dbDesc"] = line.split("DESCRIPTION: ")[1]
                except Exception, e:
                    logger.warning("Couldn't process DESCRIPTION line '%s', ignoring it." %(line), exc_info=True)
                    fileDict["dbDesc"] = ""
            elif re.search("Start Load$",line) != None:
                # Starttime LOAD phase
                process_time(line,"startLoadTime", fileDict, logger)
            elif re.search("End Load$",line) != None:
                # Endtime LOAD phase
                process_time(line,"endLoadTime", fileDict, logger)
            elif re.search("Start Run$",line) != None:
                # Starttime RUN phase
                process_time(line,"startRunTime", fileDict, logger)
            elif re.search("End Run$",line) != None:
                # Endtime RUN phase
                process_time(line,"endRunTime", fileDict, logger)
            elif re.search("End Test$",line) != None:
                # Endtime whole measurement
                process_time(line,"endTime", fileDict, logger)
            elif re.search("^SPACE:",line) != None:
                # found line with space
                process_space(line, fileDict, logger)
            elif re.search("^TIMESERIES",line) != None:
                # if Timeseries is set or unset
                if re.search("1$",line) != None:
                    fileDict["timeseries"] = True
                    timeSeries = True
                elif re.search("0$",line) != None:
                    fileDict["timeseries"] = False
                else:
                    logger.warning("Couldn't process TIMESERIES line '%s', ignoring it." %(line))
            elif re.search("^GRANULARITY",line) != None:
                # Granularity for ts
                try:
                    fileDict["granularity"] = int(line.split("GRANULARITY: ")[1])
                except Exception, e:
                    logger.warning("Couldn't process GRANULARITY line '%s', ignoring it." %(line), exc_info=True)
            elif re.search("^BUCKET",line) != None:
                # histogram Buckets
                try:
                    fileDict["bucket"] = int(line.split("BUCKET: ")[1])
                except Exception, e:
                    logger.warning("Couldn't process BUCKET line '%s', ignoring it." %(line), exc_info=True)
            elif re.search("^\[OVERALL\]",line) != None:
                if "RunTime" in line:
                    if "runtimeLoad" in fileDict.keys():
                        # runtimeLoad was found, now it has to be Run
                        process_float(line, fileDict, "runtimeRun", logger)
                    elif "runtimeRun" in fileDict.keys():
                        # both already found, third one should not happen
                        logger.error("Found third runTime in '%s'." %(line))
                        os._exit(-1)
                    else:
                        # nothing set, must be Load phase
                        process_float(line, fileDict, "runtimeLoad", logger)
                elif "Throughput" in line:
                    if "throughputLoad" in fileDict.keys():
                        # throughputLoad was found, now it has to be Run
                        process_float(line, fileDict, "throughputRun", logger)
                    elif "throughputRun" in fileDict.keys():
                        # both already found, third one should not happen
                        logger.error("Found third throughput in '%s'." %(line))
                        os._exit(-1)
                    else:
                        # nothing set, must be Load phase
                        process_float(line, fileDict, "throughputLoad", logger)
                else:
                    logger.error("Did not found 'RunTime' nor 'Throughput' in '%s'." %(line))
                    os._exit(-1)
                # found line with space
                process_space(line, fileDict, logger)
            elif check_block(line, knownBlocktypes):
                # check if fileDict contains the blocks dict
                process_block(fileDict, line, knownBlocktypes, actBlock, timeSeries, logger)
    ## AVG,SUM, usw.
    for blockKey in fileDict["blocks"].keys():
        ## AVG0,SUM0, usw.
        for listBlock in fileDict["blocks"][blockKey]:
            if "LatencyList" not in listBlock.keys():
                logger.error("The 'LatencyList' is missing Block %s in %s." %(blockKey,listBlock,filename))
                os._exit(-1)
            # "0"-"999" + ">1000" = 1001 Entrys for 1000 buckets for ex.
            if len(listBlock["LatencyList"]) != int(fileDict["bucket"])+1:
                logger.error("There are buckets missing for %s%s in %s. Available Buckets: %s, configured amount of buckets: %s(+1)." %(blockKey,listBlock,filename,len(listBlock["LatencyList"]),int(fileDict["bucket"])))
                os._exit(-1)

    try:
        file = gzip.open(compressedFileName,"w")
        cPickle.dump(fileDict,file)
        file.flush()
        file.close()
    except Exception, e:
        logger.error("Can't open '%s' to write. Is it writable?" %(compressedFileName), exc_info=True)
        os._exit(-1)
    return fileDict

# replaces bokeh.charts.Bar because it can't do logarithmic scale
def generate_bar_plot(dataDict, cat, legendPos, legendOri, title, ylabel, xlabel, width, height, logger):
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
        color = Util.get_random_int_with_chosen_default(0, len(webcolors.css3_names_to_hex.keys())-1,chosenColors,defaultColors)
        if color == None:
            logger.error("Not enough colors. Can't generate bar plot.")
            return None
        chosenColors.append(color)
        # for dataPoint in dataDict[dataKey][::-1]:
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
    p.legend.location = legendPos
    p.legend.orientation = legendOri
    return p

# generates plots for every block/index in dict
# Only for one measurement -> "single"
def generate_plot_single(dict, timeseries, logger, tick=1000):
    dataDict = { "histogram" : {}, "general" : {} }
    gridplotList = []
    gridRowCount = 0
    gridRowMax = 2
    # Get Data for both plots
    if args.debug:
        Util.log_timestamp("Start Generating histogramm data",logger)
    for block in dict["blocks"].keys():
        counter=0
        for blockList in dict["blocks"][block]:
            dataDict["histogram"]["%s%s" %(block,counter)] = generate_histogram_data(blockList["LatencyList"], logger)
            counter += 1
    if args.debug:
        Util.log_timestamp("Start Generating general data",logger)
    dataDict["general"] = generate_general_data(dict["blocks"], True, False, logger)
    if "TIMESERIES" in dataDict.keys() and dataDict["TIMESERIES"]:
        timeseries = True
    if "GRANULARITY" in dataDict.keys():
        tick = dataDict["GRANULARITY"]
    elif timeseries:
        try:
            tick = sorted(dataDict["histogram"][dataDict["histogram"].keys()[0]]["cat"])[1]-sorted(dataDict["histogram"][dataDict["histogram"].keys()[0]]["cat"])[0]
        except Exception, e:
            logger.warning("Couldn't process GRANULARITY on base of histogramm data. Default to 1000.", exc_info=True)
            tick=1000
    # generate General block plot
    #p = bokeh.charts.Bar(dataDict["general"]["data"], cat=dataDict["general"]["cat"], legend="top_right", title="Block results:",
    #     ylabel='Latency in ms', xlabel = "Type of latency", width=650, height=350)
    if args.debug:
        Util.log_timestamp("Start Generating bar plot",logger)
    p = generate_bar_plot(dataDict["general"]["data"], dataDict["general"]["cat"], "top_left", "horizontal", "Block results:",
                          "Latency in ms", "Type of latency", 650, 350, logger)
    if args.debug:
        Util.log_timestamp("End Generating bar plot",logger)
    if p == None:
        return None
    if gridRowMax < 2:
        gridplotList.append(p)
    elif gridRowCount == gridRowMax-1:
        gridplotList[-1].append(p)
        gridRowCount=0
    else:
        gridplotList.append([p])
        gridRowCount+=1
    if args.debug:
        Util.log_timestamp("Start Generating histograms",logger)
    # Generate histograms
    for key in dataDict["histogram"].keys():
        if len(dataDict["histogram"][key]["data"]) < 2 and \
           len(dataDict["histogram"][key]["data2"]) < 2 and \
           len(dataDict["histogram"][key]["cat"]) < 2:
           if "CLEANUP" in key and timeseries:
               logger.info("Do not produce '%s' plots since timeseries is active and therefore only 1 value is given." %(key))
           else:
               logger.warning("Only 1 value for '%s', can't produce plots for this block." %(key))
           continue
        p = bokeh.plotting.figure(title="Query time for %s" %(key),
                    x_range=[0,max(dataDict["histogram"][key]["cat"])], y_range=[0, max(dataDict["histogram"][key]["data"])+max(dataDict["histogram"][key]["data"])/10.0],
                                      plot_width=650, plot_height=350)
        p.xaxis.axis_label_text_font_size = "10pt"
        p.yaxis.axis_label_text_font_size = "10pt"
        if timeseries:
            p.yaxis.axis_label = "Avg. Latency since last tick (every %s ms) in ms" %(tick)
            p.xaxis.axis_label = "Elapsed time in ms"
            p.xaxis[0].ticker = bokeh.models.SingleIntervalTicker(interval=tick)
        else:
            p.xaxis.axis_label = "Time in ms"
            p.yaxis.axis_label = "Amount of queries completed"
        color = defaultPlotColor
        if key in plotColorDict.keys():
            color = plotColorDict[key]
        if timeseries:
            sortedCatList, sortedDataList = (list(t) for t in zip(*sorted(zip(dataDict["histogram"][key]["cat"], dataDict["histogram"][key]["data"]))))
            p.line(sortedCatList, sortedDataList, line_width=2)
            p.circle(dataDict["histogram"][key]["cat"], dataDict["histogram"][key]["data"], fill_color="white", size=8)
        else:
            p.rect(x=dataDict["histogram"][key]["cat"], y=dataDict["histogram"][key]["data2"], width=0.8,
               height=dataDict["histogram"][key]["data"], color=color, alpha=1)
        if gridRowMax < 2:
            gridplotList.append(p)
            continue
        if gridRowCount == gridRowMax-1:
            gridplotList[-1].append(p)
            gridRowCount=0
        else:
            gridplotList.append([p])
            gridRowCount+=1
    if args.debug:
        Util.log_timestamp("End Generating histograms",logger)
    if args.debug:
        Util.log_timestamp("Start adding plots to bokeh",logger)
    p = bokeh.io.gridplot(gridplotList)
    if args.debug:
        Util.log_timestamp("End adding plots to bokeh",logger)
    return p

# generates plots for every block/index and every dict in dicts
# Only for more than one measurement -> "multi"
# no histogram in combined plots
# only comparison plots/tables
def generate_plot_multi(dicts, timeseries, logger, tick=1000):
    gridplotList = []
    dataDictBlocks = {}
    # structure of dataDictBlocks should look like this:
    # <blocktype>
    #           -> "data"
    #                  -> <dbName>
    #                         -> [1,2,3]
    #                         ...
    #                  ...
    #           -> "cat"
    #                  -> <paramName>
    #                  -> ...
    # <blockType> e.g. "INSERT0"
    # <dbName> e.g. "MySQL"
    # <paramName> e.g. "AvgLatency"

    # getting blocktypes and data
    generate_block_data(dataDictBlocks, dicts, True, False, logger)

    # generating general graphs like avgLatency etcpp.
    for blockKey in dataDictBlocks.keys():
        #p = bokeh.charts.Bar(dataDictBlocks[blockKey]["data"], cat = dataDictBlocks[blockKey]["cat"], legend = "top_right",
        #    title = "Results for block %s:" % (blockKey), ylabel = 'Latency in ms', xlabel = "Type of latency", width=1300, height=700)
        # dataDictBlocks[blockKey]["cat"]=['Avg.', '95Perc.', '99Perc.',  'Min', 'Max',]
        # p = generate_bar_plot(dataDictBlocks[blockKey]["data"], dataDictBlocks[blockKey]["cat"][::-1],
        p = generate_bar_plot(dataDictBlocks[blockKey]["data"], dataDictBlocks[blockKey]["cat"],
                              "top_left", "horizontal", "Results for block %s:" % (blockKey),
                              "Latency in ms", "Type of latency", 1300, 700, logger)
        if p != None:
            gridplotList.append([p])
        else:
            logger.error("An error occured while generting plot for %s." %(blockKey))

    # generating graphs for runtimeRun/Load
    runtimeDict = { "data" : {}, "cat" : [ "runtimeLoad", "runtimeRun" ] }
    for key in dicts.keys():
        if "runtimeLoad" in dicts[key].keys() and "runtimeRun" in dicts[key].keys():
            runtimeDict["data"][key]=[dicts[key]["runtimeLoad"],dicts[key]["runtimeRun"]]
        else:
            logger.error("Can't find 'runtimeLoad' or/and 'runtimeRun' in %s dict. Can't go on." %(key))
            os._exit(-1)
    # p = bokeh.charts.Bar(runtimeDict["data"], cat = runtimeDict["cat"], legend = "top_right",
    #         title = "Results for runtime:", ylabel = 'Runtime in ms', xlabel = "Type of runtime", width=1300, height=700)
    # gridplotList.append([p])
    p = generate_bar_plot(runtimeDict["data"], runtimeDict["cat"],
                          "top_left", "horizontal", "Results for runtime:",
                          "Runtime in ms", "Type of runtime", 1300, 700, logger)
    if p != None:
        gridplotList.append([p])
    else:
        logger.error("An error occured while generting plot for runtimeDict.")


    # generating graphs for throughputLoad/Run
    runtimeDict = { "data" : {}, "cat" : [ "throughputLoad", "throughputRun" ] }
    for key in dicts.keys():
        if "throughputLoad" in dicts[key].keys() and "throughputRun" in dicts[key].keys():
            runtimeDict["data"][key]=[dicts[key]["throughputLoad"],dicts[key]["throughputRun"]]
        else:
            logger.error("Can't find 'throughputLoad' or/and 'throughputRun' in %s dict. Can't go on." %(key))
            os._exit(-1)
    # p = bokeh.charts.Bar(runtimeDict["data"], cat = runtimeDict["cat"], legend = "top_right",
    #         title = "Results for throughput:", ylabel = 'Throughput in operations per sec.', xlabel = "Type of throughput", width=1300, height=700)
    # gridplotList.append([p])
    p = generate_bar_plot(runtimeDict["data"], runtimeDict["cat"],
                          "top_left", "horizontal", "Results for throughput:",
                          "Throughput in operations per sec.", "Type of throughput", 1300, 700, logger)
    if p != None:
        gridplotList.append([p])
    else:
        logger.error("An error occured while generting plot for throughput.")


    # generating graphs for spaceLoad/spaceRun:
    # spaceLoad = spaceBetween - spaceBegin
    # spaceRun = spaceEnd - spaceBetween
    runtimeDict = { "data" : {}, "cat" : [ "spaceLoad", "spaceRun" ] }
    for key in dicts.keys():
        if "spaceBegin" in dicts[key].keys() and "spaceEnd" in dicts[key].keys() and "spaceBetween" in dicts[key].keys():
            try:
                runtimeDict["data"][key]=[int(dicts[key]["spaceBetween"]) - int(dicts[key]["spaceBegin"]), int(dicts[key]["spaceEnd"]) - int(dicts[key]["spaceBetween"])]
            except:
                logger.error("Error while converting 'spaceBegin' '%s' or/and 'spaceBetween' '%s' or/and 'spaceEnd' '%s' in %s dict to int. Can't go on." %(dicts[key]["spaceBegin"], dicts[key]["spaceBetween"], dicts[key]["spaceEnd"], key))
                os._exit(-1)
        else:
            logger.error("Can't find 'spaceBegin' or/and 'spaceBetween' or/and 'spaceEnd' in %s dict. Can't go on." %(key))
            os._exit(-1)
    # p = bokeh.charts.Bar(runtimeDict["data"], cat = runtimeDict["cat"], legend = "top_right",
    #         title = "Results for space consumption:", ylabel = 'Space consumption in Kilobyte (kB)', xlabel = "Type of space consumption", width=1300, height=700)
    # gridplotList.append([p])
    p = generate_bar_plot(runtimeDict["data"], runtimeDict["cat"],
                          "top_left", "horizontal", "Results for space consumption:",
                          "Space consumption in Kilobyte (kB)", "Type of space consumption", 1300, 700, logger)
    if p != None:
        gridplotList.append([p])
    else:
        logger.error("An error occured while generting plot for space consumption.")


    p = bokeh.io.gridplot(gridplotList)
    return p

# generates block data for multi dict block graphs
# in dataDictBlocks the following structure is found after returning:
# <blocktype>
#           -> "data"
#                  -> <dbName>
#                         -> [1,2,3]
#                         ...
#                  ...
#           -> "cat"
#                  -> <paramName>
#                  -> ...
# <blockType> e.g. "INSERT0"
# <dbName> e.g. "MySQL"
# <paramName> e.g. "AvgLatency"
def generate_block_data(dataDictBlocks, dicts, ignoreSomeParameters, ignoreLess, logger):
    firstRound = True  # check if everyone has same block types
    for key in dicts.keys():
        # generate_general_data deliveres the following structure:
        # "data"
        #    -> <blockType>
        #             -> <parameters>
        # "cat"
        #    -> <paramName>
        #    -> ...
        # we have to move that a little bit...
        data = generate_general_data(dicts[key]["blocks"], ignoreSomeParameters, ignoreLess, logger)
        keyCopyTmp = list(dataDictBlocks.keys())  # True Copy # check if every block is in every dict
        for block in dicts[key]["blocks"].keys():
            for index in range(0,len(dicts[key]["blocks"][block])):
                blockname = "%s%s" % (block, index)
                if firstRound and blockname not in dataDictBlocks.keys():
                    dataDictBlocks[blockname] = {"data": {}, "cat": []}
                    if dataDictBlocks[blockname]["cat"] == []:
                        dataDictBlocks[blockname]["cat"] = data["cat"]
                elif blockname not in dataDictBlocks.keys():
                    logger.error(
                        "Found blocktype '%s' (index '%s') that does only belong to dict '%s'. Can't move on." % (
                        block, index, key))
                    os._exit(-1)
                else:
                    keyCopyTmp.remove(blockname)
                if key not in dataDictBlocks[blockname]["data"].keys():
                    dataDictBlocks[blockname]["data"][key] = data["data"][blockname]
                else:
                    logger.error("Found key '%s' more than once for block '%s', index '%s'. Can't move on." % (
                    key, block, index))
                    os._exit(-1)
                # check if the right amount of parameters is there
                if len(dataDictBlocks[blockname]["data"][key]) != len(dataDictBlocks[blockname]["cat"]) and not ignoreLess:
                    logger.error("Found more or less parameters than needed in key '%s'. Needed: %s, Found: %s." % (
                    key, len(dataDictBlocks[blockname]["cat"]), len(dataDictBlocks[blockname]["data"][key])))
                    os._exit(-1)
        if not firstRound:
            if len(keyCopyTmp) > 0:
                logger.error("Found less keys than needed in '%s'. Needed: '%s'." % (key, keyCopyTmp))
                os._exit(-1)
        firstRound = False


# generates html file for given html text
def generate_html(p, templateFile, templateDict, outputFile, overwrite, logger):
    if not Util.check_file_exists(templateFile):
        logger.error("Template file does not exist: '%s'" %(templateFile))
        os._exit(-1)
    try:
        template = jinja2.Environment(loader = jinja2.FileSystemLoader(searchpath=os.path.split(templateFile)[0])).get_template(os.path.split(templateFile)[1])
    except Exception, e:
        logger.error("Failed load template file '%s'" %(templateFile), exc_info=True)
        os._exit(-1)
    html = bokeh.embed.file_html(models=p, resources=bokeh.resources.INLINE, title=templateDict["title"] , template=template, template_variables=templateDict)
    if Util.check_file_exists(outputFile) and not overwrite:
        logger.error("Html file does exist: '%s'. Delete or use overwrite flag." %(outputFile))
        os._exit(-1)
    try:
        file = open(outputFile,"w")
        file.write(html)
        file.close()
    except Exception, e:
        logger.error("Error while writing html file '%s'" %(outputFile), exc_info=True)
        os._exit(-1)

# generates bokeh histogram_data
# gets data from every "LatencyList"
# data2 is just data/2.0
# commented out code is old and better to read but much slower due to "key not in" - if
def generate_histogram_data(list, logger):
    if args.debug:
        Util.log_timestamp("Start Generating histogram",logger)
    dataDict = { "data" : [], "data2" : [], "cat" : []}
    # consits of dicts: data and cat
    # counter=0
    dataDict["data"]=list
    dataDict["data2"]=[i/2.0 for i in list]
    dataDict["cat"]=range(0,len(list))

    # for value in list:
    #     # factor 2 has to be divided as you set a "center point" for your rectangles, otherwise 0 won't be 0
    #     dataDict["data"].append(value)
    #     dataDict["data2"].append(value/2.0)
    #     if key not in dataDict["cat"]:
    #          Util.log_timestamp(counter,logger)
    #     dataDict["cat"].append(counter)
    #     counter += 1
    if args.debug:
        Util.log_timestamp("End Generating histogram",logger)
    return dataDict

# generates bokeh general block data
# gets the "blocks" key of fileDict (see above method process_file(...))
# use data from every block in blocks, from every index in every block
# gets every "Throughput","AverageLatency",...
# if you set param you only get your chosen value like Throughput e.g.
def generate_general_data(dict, ignoreSomeParameters, ignoreLess, logger):
    dataDict = { "data" : {}, "cat" : [] }
    firstRun = True
    for block in dict.keys():
        for counter in range(0,len(dict[block])):
            dataDict["data"]["%s%s" % (block,counter)] = []
            parameterArrayCopy = list(dataDict["cat"]) # real copy, not just reference!
            for parameter in possibleMissingParams:
                if parameter not in dict[block][counter].keys():
                    logger.warning("Possible that all querys of %s run more than the maximum time measurement period? %s will be -1 for %s." %("%s%s" %(block,counter),parameter, "%s%s" %(block,counter)))
                    dict[block][counter][parameter]=-1
            for parameter in dict[block][counter].keys():
                parameterClean = parameter.replace("(ms)","").replace("(us)","").replace("Latency","").replace("thPercentile","Perc.").replace("Average","Avg.")
                if parameter not in ignoreParams or (not ignoreSomeParameters and parameter != "LatencyList" ):
                    if not firstRun and parameterClean not in dataDict["cat"]:
                            logger.error("There were more parameter in '%s' than in other blocks, that does not work. Parameter %s is too much." %("%s%s" % (block,counter),parameter))
                            os._exit(-1)
                    if parameter in convertFromUsToMs:
                        dataDict["data"]["%s%s" % (block,counter)].append(dict[block][counter][parameter]/1000.0)
                    else:
                        dataDict["data"]["%s%s" % (block,counter)].append(dict[block][counter][parameter])
                    if firstRun:
                        dataDict["cat"].append(parameterClean)
                    else:
                        parameterArrayCopy.remove(parameterClean)
            if not firstRun:
                if len(parameterArrayCopy) > 0:
                    if not ignoreLess:
                        logger.error("There were less parameter in '%s' than in other blocks, that does not work. Parameter left (cleaned -> without (us) or (ms)!): %s." %("%s%s" % (block,counter),parameterArrayCopy))
                        os._exit(-1)
                    else:
                        for param in parameterArrayCopy:
                            dataDict["data"]["%s%s" % (block,counter)].insert(list(dataDict["cat"]).index(param),"-")
            firstRun = False
    return dataDict

# Generate resulting html table for single measurement page
def generate_results_table_single(dict, logger):
    templateDict={}
    templateDict["results_table_name"] = "General results:"
    templateDict["block_results_table_name"] = "Block results:"
    if dict["dbDesc"] != "":
        templateDict["dbdesc_name"] = "Database Description:"
        templateDict["dbdesc"] = dict["dbDesc"]
    if dict["description"] != "":
        templateDict["description_name"] = "Description:"
        templateDict["description"] = dict["description"]
    if dict["errors"] != []:
        templateDict["errors_name"] = "Erros:"
        templateDict["errors"] = ""
        for error in dict["errors"]:
            templateDict["errors"] += "%s<br>" %(error)
    if dict["warnings"] != []:
        templateDict["warnings_name"] = "Warnings:"
        templateDict["warnings"] = ""
        for warning in dict["warnings"]:
            templateDict["warnings"] += "%s<br>" %(warning)
    if dict["exceptions"] != []:
        templateDict["exceptions_name"] = "Exceptions:"
        templateDict["exceptions"] = ""
        for exception in dict["exceptions"]:
            templateDict["exceptions"] += "%s<br>" %(exception)
    templateDict["title"] = "%s_%s_%s" %(dict["dbName"], dict["workload"], dict["startTime"].strftime("%Y%m%d%H%M"))
    # Generate 'General' Results Table
    tableHtml="<thead><tr><th>Parametername:</th><th>Value:</th></tr></thead>"
    tableHtml+="<tbody>"
    for key in dict.keys():
        if key != "blocks":
            tableHtml+="<tr><th scope=\"row\">%s</th><td>%s</td></tr>" % (key,dict[key])
    tableHtml+="</tbody>"
    templateDict["results_table"] = tableHtml
    # Generate 'Block' Results Table
    # which means results of every block
    # no histogram/timeseries data ('LatencyList'), only more general values like throughput,etc.
    paramDict={} # dict of parameterName : [value1,value2..] -> represents table rows!
    firstRun=True # check if all blocks have all parameters (same parameter set)
    # creates dict for html table, every key has an array of one row
    for block in dict["blocks"]:
        for index in range(0,len(dict["blocks"][block])):
            tmpparamDict = paramDict.copy() #check if all entries were there, if not use "-"
            for param in dict["blocks"][block][index]:
                if param == "LatencyList":
                    continue
                if param not in paramDict.keys():
                    if not firstRun:
                        logger.error("Found '%s' in '%s%s' which other blocks do not have." %(param,block,index))
                        os._exit(-1)
                    paramDict[param]=[dict["blocks"][block][index][param]]
                else:
                    paramDict[param].append(dict["blocks"][block][index][param])
                if dict["blocks"][block][index][param] == -1 and param in possibleMissingParams :
                    if dict["warnings"] == []:
                        templateDict["warnings_name"] = "Warnings:"
                        templateDict["warnings"] = ""
                    paramStr = ""
                    for possibleMissingParam in possibleMissingParams:
                        paramStr += ", %s" %(possibleMissingParam)
                    paramStr = paramStr[2:]
                    templateDict["warnings"] += "%s<br>" %("Values of -1 for %s means that these values were not calculated by ycsb, mostly due to query times longer than the given bucketsize." %(paramStr))
                if not firstRun:
                    tmpparamDict.pop(param)
            # Fix missing parameters for this row
            if not firstRun:
                for key in tmpparamDict:
                    paramDict[key].append("-")
            firstRun = False

    # counting amount of columns needed
    tableColumnsCounter = 1 # 1 because left column is already there
    indexSaver = 0 # Saves next index in case of row break
    indexMax = 0
    tableHtml=""
    for block in dict["blocks"]:
        for index in dict["blocks"][block]:
            indexMax += 1
    while indexSaver < indexMax:
        if indexSaver+tableColumnsCounter > indexMax:
            break
        if tableColumnsCounter >= maxTableColumnsSingle:
            indexSaver+=tableColumnsCounter-1
            if indexSaver >= indexMax:
                break
            tableColumnsCounter = 1
            tableHtml+="<tr>"
            for k in range(0,maxTableColumnsSingle+1):
                tableHtml+="<td></td>"
            tableHtml+="</tr></tbody>"
            continue
        tableHtml+="<thead><tr><th>Parametername:</th>"
        indexCounter=0 # to find the right index again
        for block in dict["blocks"]:
            for index in range(0,len(dict["blocks"][block])):
                if indexCounter >= indexSaver:
                    if tableColumnsCounter >= maxTableColumnsSingle:
                        break
                    else:
                        tableHtml+="<th>%s%s:</th>" % (block,index)
                        tableColumnsCounter += 1
                        
                indexCounter+=1
        tableHtml+="</tr></thead>"
        tableHtml+="<tbody>"
        for key in paramDict.keys():
            tableHtml+="<tr><th scope=\"row\">%s</th>" % (key)
            tableColumnsCounter2 = 1
            indexCounter2=0 # to find the right index again
            for number in paramDict[key]:
                if indexCounter2 >= indexSaver:
                    if tableColumnsCounter2 >= maxTableColumnsSingle:
                        break
                    else:
                        tableHtml+="<td>%s</td>" % (number)
                        tableColumnsCounter2+=1
                indexCounter2+=1
            tableHtml+="</tr>"

    tableHtml+="</tbody>"
    templateDict["block_results_table"] = tableHtml
    return templateDict

# Generate resulting html table for multi measurement page
def generate_results_table_multi(dicts, fileName, logger):
    dataDictBlocks = {}
    # structure of dataDictBlocks should look like this:
    # <blocktype>
    #           -> "data"
    #                  -> <dbName>
    #                         -> [1,2,3]
    #                         ...
    #                  ...
    #           -> "cat"
    #                  -> <paramName>
    #                  -> ...
    # <blockType> e.g. "INSERT0"
    # <dbName> e.g. "MySQL"
    # <paramName> e.g. "AvgLatency"
    # we do the same here as for multi dict block plots
    generate_block_data(dataDictBlocks, dicts, False, True, logger)

    templateDict={}
    templateDict["results_table_name"] = "General results:"
    templateDict["block_results_table_name"] = "Block results:"
    templateDict["title"] = fileName
    if len(dicts.keys()) > 0:
        if dicts[dicts.keys()[0]]["description"] != "":
            templateDict["description_name"] = "Description:"
            templateDict["description"] = dicts[dicts.keys()[0]]["description"]
        templateDict["dbdesc_name"] = "Database Descriptions:"
        dbDescStr = "<table class=\"bk-bs-table\"><tbody>"
        counter=0
        for dbKey in sorted(dicts.keys()):
            if counter%2 == 0:
                dbDescStr += "<tr>"
            dbDescStr += "<th scope=\"row\">%s:</th><td>%s</td>" %(dicts[dbKey]["dbName"],dicts[dbKey]["dbDesc"])
            if counter%2 != 0:
                dbDescStr += "</tr>"
            counter+=1
        templateDict["dbdesc"] = dbDescStr + "</tbody></table>"
    errorsOccurred = False
    errors = []
    warningsOccurred = False
    warnings = []
    exceptionsOccurred = False
    exceptions = []
    for dictKey in sorted(dicts.keys()):
        if dicts[dictKey]["errors"] != []:
            errorsOccurred = True
            errors.append(dictKey)
        if dicts[dictKey]["warnings"] != []:
            warningsOccurred = True
            warnings.append(dictKey)
        if dicts[dictKey]["exceptions"] != []:
            exceptionsOccurred = True
            exceptions.append(dictKey)
    if errorsOccurred:
        templateDict["errors"] = "Errors occured in some of the measurements (%s)." %(errors)
    if warningsOccurred:
        templateDict["warnings"] = "Warnings occured in some of the measurements (%s)." %(warnings)
    # Search for -1 in 95th and 99th Percentiles
    minus1Occured = False
    for blockType in dataDictBlocks.keys():
        if "99Perc." in dataDictBlocks[blockType]["cat"] or \
            "95Perc." in dataDictBlocks[blockType]["cat"]:
            for dbKey in dataDictBlocks[blockType]["data"].keys():
                if dataDictBlocks[blockType]["data"][dbKey][dataDictBlocks[blockType]["cat"].index("99Perc.")] == -1 or \
                    dataDictBlocks[blockType]["data"][dbKey][dataDictBlocks[blockType]["cat"].index("95Perc.")] == -1:
                    minus1Occured = True
    if minus1Occured:
        if "warnings" not in templateDict.keys() or templateDict["warnings"] == None or templateDict["warnings"] == "":
            templateDict["warnings"] = "Warning: %s" %("Values of -1 for 99Perc. or 95Perc. means that these values were not calculated by ycsb, mostly due to query times longer than the given bucketsize.")
        else:
            templateDict["warnings"] += "<br>Warning:%s" %("Values of -1 for 99Perc. or 95Perc. means that these values were not calculated by ycsb, mostly due to query times longer than the given bucketsize.")

    if exceptionsOccurred:
        templateDict["exceptions"] = "Exceptions occured in some of the measurements (%s)." %(exceptions)
    # generate for every block one table:
    tableHtml="<h2>Block results:</h2>"
    for blockType in dataDictBlocks.keys():
        tableColumnsCounter = 1 # 1 because left column is already there
        indexSaver = 0 # Saves next index in case of row break
        tableHtml+="<h3>%s</h3><table class=\"bk-bs-table\"><thead>" %(blockType)
        while indexSaver <  len(sorted(dataDictBlocks[blockType]["data"].keys())):
            if tableColumnsCounter > len(dataDictBlocks[blockType]["data"].keys()):
                break
            if tableColumnsCounter >= maxTableColumnsMulti:
                indexSaver+=tableColumnsCounter-1
                if indexSaver >= len(dataDictBlocks[blockType]["data"].keys()) :
                    break
                tableColumnsCounter = 1
                tableHtml+="<tr>"
                for k in range(0,maxTableColumnsMulti+1):
                    tableHtml+="<td></td>"
                tableHtml+="</tr></tbody>"
                continue
            # print blockType
            tableHtml+="<tr><th>Parametername:</th>"
            indexCounter=0 # to find the right index again
            # go through all dbs
            for dbKey in sorted(dataDictBlocks[blockType]["data"].keys()):
                 if indexCounter >= indexSaver:
                    if tableColumnsCounter >= maxTableColumnsMulti:
                        break
                    else:
                        tableHtml+="<th>%s:</th>" % (dbKey)
                        tableColumnsCounter += 1
                 indexCounter+=1
            tableHtml+="</tr></thead>"
            tableHtml+="<tbody>"
            # go through all parameters
            for param in dataDictBlocks[blockType]["cat"]:
                    tableHtml+="<tr><th scope=\"row\">%s</th>" % (param)
                    tableColumnsCounter2 = 1
                    indexCounter2=0 # to find the right index again
                    for dbKey in sorted(dataDictBlocks[blockType]["data"].keys()):
                        if indexCounter2 >= indexSaver:
                            if tableColumnsCounter2 >= maxTableColumnsMulti:
                                break
                            else:
                                tableHtml+="<td>%s</td>" % (dataDictBlocks[blockType]["data"][dbKey][dataDictBlocks[blockType]["cat"].index(param)])
                                tableColumnsCounter2+=1
                        indexCounter2+=1
                    tableHtml+="</tr>"
        tableHtml+="</tbody></table>"
    templateDict["block_results_table"] = tableHtml
    # generate general result table
    tableHtml="<h2>General results:</h2><table class=\"bk-bs-table\"><thead><tr><th>Parametername:</th>"
    parameterArr = []
    ignoreParams = ["blocks"] # ignore complete
    subParams = ["timeseries","granularity", "bucket"] # substitute with "-"
    valueDict = {} # every table row should be inside
    firstRound = True # again to check that every dict has every parameter
    dbNameKey = "dbNameKey" # some name that identifies our dbName row
    for dictKey in dicts:
        if dbNameKey not in valueDict.keys():
            valueDict[dbNameKey] = [dictKey]
        elif dbNameKey in valueDict.keys() and firstRound:
            logger.error("A parameter is named 'dbNameKey', please change it. Abort.")
            os._exit(-1)
        else:
            valueDict[dbNameKey].append(dictKey)
        copyParameterArr = list(parameterArr) #real copy to check if nothings missing
        for key in dicts[dictKey]:
            if key in ignoreParams:
                continue
            if firstRound:
                if key not in parameterArr:
                    parameterArr.append(key)
            else:
                try:
                    copyParameterArr.remove(key)
                except Exception, e:
                    logger.error("Error: '%s' has too many keys." %(key), exc_info=True)
                    os._exit(-1)
            if key not in valueDict.keys():
                valueDict[key] = [dicts[dictKey][key]]
            else:
                valueDict[key].append(dicts[dictKey][key])
        if not firstRound:
            if len(copyParameterArr) > 0:
                for arg in list(copyParameterArr): #copy otherwise removing kills it
                    if arg in subParams:
                        valueDict[arg].append("-")
                        copyParameterArr.remove(arg)
                if len(copyParameterArr) == 0:
                    continue
                logger.error("Error: '%s' has too less keys. Left: '%s'" %(dictKey, copyParameterArr), exc_info=True)
                os._exit(-1)
        firstRound = False

    tableColumnsCounter = 1 # 1 because left column is already there
    indexSaver = 0 # Saves next index in case of row break
    #print valueDict
    for rowKey in valueDict:
        if tableColumnsCounter > len(valueDict[dbNameKey]):
            break
        if tableColumnsCounter >= maxTableColumnsMulti:
            indexSaver+=tableColumnsCounter-1
            if indexSaver >= len(valueDict[dbNameKey]) :
                break
            tableColumnsCounter = 1
            tableHtml+="<tr>"
            for k in range(0,maxTableColumnsMulti+1):
                tableHtml+="<td></td>"
            tableHtml+="</tr></tbody>"
            tableHtml+="<tr><th>Parametername:</th>"
            continue
        indexCounter=0 # to find the right index again
        # go through all dbs
        for dbKey in sorted(valueDict[dbNameKey]):
             if indexCounter >= indexSaver:
                if tableColumnsCounter >= maxTableColumnsMulti:
                    break
                else:
                    tableHtml+="<th>%s:</th>" % (dbKey)
                    tableColumnsCounter += 1
             indexCounter+=1
        tableHtml+="</tr></thead>"
        tableHtml+="<tbody>"
        # go through all parameters
        for param in sorted(valueDict.keys()):
            if param == dbNameKey:
                continue
            tableHtml+="<tr><th scope=\"row\">%s</th>" % (param)
            tableColumnsCounter2 = 1
            indexCounter2=0 # to find the right index again
            for value in valueDict[param]:
                if indexCounter2 >= indexSaver:
                    if tableColumnsCounter2 >= maxTableColumnsMulti:
                        break
                    else:
                        tableHtml+="<td>%s</td>" % (value)
                        tableColumnsCounter2+=1
                indexCounter2+=1
            tableHtml+="</tr>"
    tableHtml+="</tbody></table>"
    templateDict["general_results_table"] = tableHtml
    return templateDict

def generate_pdf(htmlFile, overwrite, pdfOptions, logger):
    if not Util.check_file_exists(htmlFile):
        logger.error("Html file does not exist: '%s'" %(htmlFile))
        os._exit(-1)
    pdfOptions["title"]= "%s" %(os.path.splitext(os.path.basename(htmlFile))[0])
    pdfFile="%s.pdf" % (pdfOptions["title"])
    if Util.check_file_exists(pdfFile) and not overwrite:
        logger.error("Pdf file does already exist: '%s'. Use overwrite flag or delete it." %(pdfFile))
        os._exit(-1)
    try:
        pdfkit.from_file(htmlFile,pdfFile,options=pdfOptions)
    except Exception, e:
        logger.error("Failed to produce pdf file '%s.pdf'" %(pdfFile), exc_info=True)
        os._exit(-1)

def openCompressedFile(ycsbfile, dict, key, decompress, overwrite, logger):
    try:
        file = gzip.open(ycsbfile,"r")
        dict[key]=cPickle.load(file)
        file.close()
    except Exception, e:
        logger.error("Can't open '%s'. Is it really a compressed .ydc file?" %(ycsbfile), exc_info=True)
        os._exit(-1)
    # if you truly just want to decompress it, stop after saving plain ycsb file
    if decompress:
        try:
            newFileName=os.path.splitext(os.path.basename(ycsbfile))[0]+".log"
            if (not Util.check_file_exists(newFileName) or  overwrite) and os.access(".", os.W_OK):
                if key in dict.keys() and dict[key] != None:
                    decompressFile(dict[key], newFileName, logger)
                else:
                    logger.error("Dictionary does not have filecontent or is null." , exc_info=True)
                    os._exit(-1)
            else:
                logger.error("Can't create '%s' to write. Does it already exist?" %(newFileName), exc_info=True)
                os._exit(-1)
        except Exception, e:
            logger.error("Can't open '%s'." %("%s.log.log" %(os.path.basename(ycsbfile))), exc_info=True)
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
            if "95thPercentileLatency(us)" in fileDict["blocks"][key][0].keys():
                file.write("[%s], 95thPercentileLatency(us), %s\n" %(key,fileDict["blocks"][key][0]["95thPercentileLatency(us)"]))
            if "99thPercentileLatency(us)" in fileDict["blocks"][key][0].keys():
                file.write("[%s], 99thPercentileLatency(us), %s\n" %(key,fileDict["blocks"][key][0]["99thPercentileLatency(us)"]))
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
                if "95thPercentileLatency(us)" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], 95thPercentileLatency(us), %s\n" %(key,fileDict["blocks"][key][index]["95thPercentileLatency(us)"]))
                if "99thPercentileLatency(us)" in fileDict["blocks"][key][index].keys():
                    file.write("[%s], 99thPercentileLatency(us), %s\n" %(key,fileDict["blocks"][key][index]["99thPercentileLatency(us)"]))
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


# Generates (html, pdf) Output for every single measurement file
def generate_single_output(dict, templateFile, name, timeseries, overwrite, pdfOptions, logger):
    if args.debug:
        Util.log_timestamp("Start Generating Single Plot",logger)
    p = generate_plot_single(dict, timeseries, logger)
    if p == None:
        logger.error("Can't generate plots for %s." %(name))
        return
    if args.debug:
        Util.log_timestamp("Start Generating Single Results Table",logger)
    templateDict = generate_results_table_single(dict, logger)
    if args.debug:
        Util.log_timestamp("Start Generating HTML File",logger)
    # Generating html
    generate_html(p, templateFile, templateDict, "%s.html" % (name), overwrite, logger)
    # Generating pdf (if wanted)
    if args.pdf:
        if args.debug:
            Util.log_timestamp("Start Generating PDF File",logger)
        generate_pdf("%s.html" % (name), overwrite, pdfOptions, logger)

# Generates (html, pdf) Output for multi (combined) measurement files
def generate_multi_output(dicts, templateFile, timeseries, overwrite, logger, granularity=1000):
    granularity=granularity
    ts=None
    for dictKey in dicts.keys():
        if "granularity" in dicts[dictKey].keys():
            granularity = dicts[dictKey]["granularity"]
        if ts == None and "timeseries" in dicts[dictKey].keys():
            ts = dicts[dictKey]["timeseries"]
        elif ts != None and "timeseries" in dicts[dictKey].keys() and ts != dicts[dictKey]["timeseries"]:
            logger.error("Found one timeseries and one non timeseries type. Abort.")
            exit(-1)
    if not ts and timeseries:
        logger.error("Found at least one non timeseries type and timeseries flag is set. Abort.")
        exit(-1)
    if ts == None and timeseries:
        ts = True
    elif ts == None:
        ts = False
    fileName = "ycsb_combined_%s" % (datetime.datetime.now().strftime("%Y%m%d%H%M"))
    p = generate_plot_multi(dicts, ts, logger, )
    templateDict = generate_results_table_multi(dicts, fileName, logger)
    # Generating html
    generate_html(p, templateFile, templateDict, "%s.html" % (fileName), overwrite, logger)

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="ProcessYcsbLog.py",version=__version__,description="Generates a nice pdf out of YCSB's output.", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-l", "--log", action='store_true', help="Be more verbose")
parser.add_argument("-t", "--timeseries", action='store_true', help="Use this flag if you generated timeseries instead of a histogram in ycsb")
parser.add_argument("-f", "--ycsbfiles", metavar="YCSBFILE", nargs='+', required=True, help="Path to YCSB file(s) (can be ycsb outputfile, compressed .ydc file)")
parser.add_argument("-d", "--decompress", action='store_true', help="Decompress ycsb file out of given ydc file")
parser.add_argument("-c", "--compress", action='store_true', help="Stop after making compressed ydc file (do not generate plots/html/pdf)")
parser.add_argument("-o", "--overwrite", action='store_true', help="Overwrite existing files")
parser.add_argument("-p", "--pdf", action='store_true', help="Generate PDF file. (otherwise only pdf is generated)")
parser.add_argument("-s", "--single", action='store_true', help="if given multiple files, also generate single html/pdf for each")
parser.add_argument("--debug", action='store_true', help="Be much more verbose, print timestamps. (also activates -l)")
args = parser.parse_args()

if args.debug:
    args.log=True

# Configure Logging
logLevel = logging.WARN
if args.log:
    logLevel = logging.DEBUG
if args.debug:
    FORMAT = '%(asctime)-15s: %(message)s'
    logging.basicConfig(level=logLevel,format=FORMAT)
else:
    logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

if args.debug:
    Util.log_timestamp("Start",logger)

# delete non unique files, even if they're given as ycb output and ydc
for ycsbfile in args.ycsbfiles:
    if args.ycsbfiles.count("%s.ydc" %(os.path.splitext(os.path.basename(ycsbfile))[0])) \
            + args.ycsbfiles.count("%s.log" %(os.path.splitext(os.path.basename(ycsbfile))[0])) \
            > 1:
        args.ycsbfiles.remove(ycsbfile)
        logger.warning("'%s' exists more than once (as .log or .ydc), ignoring it." %(ycsbfile))

dicts={}
nameDict={} # stores names for dictKeys
threads=[]
if args.debug:
    Util.log_timestamp("Start Loading/Parsing Files",logger)
for ycsbfile in args.ycsbfiles:
    # Compressing Output
    mime = magic.open(magic.MAGIC_MIME)
    mime.load()
    try:
        basename="%s" %("_".join(os.path.splitext(os.path.basename(ycsbfile))[0].split("_")[1:-2]))
    except IndexError:
        logger.warning("'%s' is not a normal filename for ycsb-ts logfiles." %(os.path.basename(ycsbfile)))
        basename="%s" %(os.path.splitext(os.path.basename(ycsbfile))[0])
    except:
        logger.error("Can't process filename '%s' as basename." %(os.path.basename(ycsbfile)))
        os._exit(-1)
    if basename in dicts.keys():
        basename="%s_%s" %(basename,dicts.keys().count(basename)+1)
    if mime.file(ycsbfile) == "text/plain; charset=us-ascii" or mime.file(ycsbfile) == "text/plain; charset=utf-8":
        newFileName="%s.ydc" %(os.path.splitext(os.path.basename(ycsbfile))[0])
        # if it is an plain ycsb file, compress it
        logger.info("Found Mime type '%s' in '%s'." %(ycsbfile,mime.file(ycsbfile)))
        if (not Util.check_file_exists(newFileName) or args.overwrite) and os.access(".", os.W_OK):
            dicts[basename] = {}
            nameDict[basename]=os.path.splitext(os.path.basename(ycsbfile))[0]
            threads.append(threading.Thread(target=process_file, args=(ycsbfile, args.timeseries, dicts[basename], newFileName, logger)))
            threads[-1].setDaemon(True)
            threads[-1].start()
        else:
            logger.error("Can't create '%s' to write. Does it already exist?" %(newFileName), exc_info=True)
            exit(-1)
    elif mime.file(ycsbfile) == "application/gzip; charset=binary":
        # if a compressed file is found do decompress or graph
        logger.info("Found Mime type '%s' in '%s'." %(ycsbfile,mime.file(ycsbfile)))
        # if decompress is what you want...
        if Util.check_file_exists(ycsbfile) and os.access(ycsbfile, os.R_OK):
            dicts[basename] = {}
            nameDict[basename]=os.path.splitext(os.path.basename(ycsbfile))[0]
            threads.append(threading.Thread(target=openCompressedFile, args=(ycsbfile, dicts, basename, args.decompress, args.overwrite, logger)))
            threads[-1].setDaemon(True)
            threads[-1].start()
        else:
            logger.error("Can't open '%s'. Does it exist?" %(ycsbfile), exc_info=True)
            exit(-1)

    else:
        logger.error("%s has an unkown mimetype '%s', sure it is a ycsb log or .ydc file?" %(ycsbfile,mime.file(ycsbfile)))
        exit(-1)
# Wait until all threads are done
logger.debug("Waiting until all files are loaded...")
# only join() would make ctrl+c not work in combination with daemon=true
# Main thread is always there, because of that: >1
while threading.activeCount() > 1:
    for thread in threads:
        thread.join(100)
threads=[]
if args.debug:
    Util.log_timestamp("End Loading/Parsing Files",logger)

# if only compression/decompression is requested, do it and exit
if args.compress or args.decompress:
    exit(0)

if (len(args.ycsbfiles)==1 and len(dicts.keys())==1) or (len(args.ycsbfiles)>1 and args.single):
    if args.debug:
        Util.log_timestamp("Start Generating Single HTML File",logger)
    for key in dicts.keys():
        # at this stage we should have something in dict, wheter it was from a plain ycsb file or from a compressed ydc file
        # Generating Graph
        if maxTableColumnsSingle < 2:
            logger.error("maxTableColumnsSingle has to be > 1")
            exit(-1)
        threads.append(threading.Thread(target=generate_single_output,
                                        args=(dicts[key], templateFile, nameDict[key],
                                        args.timeseries, args.overwrite, pdfOptions.copy(), logger)))
        threads[-1].setDaemon(True)
        threads[-1].start()

if len(args.ycsbfiles)>1:
    if len(dicts.keys())==len(args.ycsbfiles):
        logger.info("Found more than one ycsb/ydc file, doing combined stuff...")
        if args.debug:
            Util.log_timestamp("Start Generating Multiple HTML Files",logger)
        if maxTableColumnsMulti < 2:
            logger.error("maxTableColumnsMulti has to be > 1")
            exit(-1)
        # in dicts there should be every ycsbfile now
        # First check: are both non timeseries or timeseries
        # 3 cases that are allowed:
        # - all are set as timeseries
        # - all are set as non-timeseries
        # - all have no flag set and are just used as histogram or forced to be used as timeseries by flag
        # Case 1 and 2:
        threads.append(threading.Thread(target=generate_multi_output,
                                        args=(dicts, templateFileMulti, args.timeseries, args.overwrite, logger)))
        threads[-1].setDaemon(True)
        threads[-1].start()
    else:
        logger.error(" %s Files and %s Dicts do not match, this should not happen." %(len(args.ycsbfiles),len(dicts.keys())))
        exit(-1)

# Wait until all threads are done
logger.debug("Waiting until all .html/.pdf files are generated...")
# only join() would make ctrl+c not work in combination with daemon=true
# Main thread is always there, because of that: >1
while threading.activeCount() > 1:
    for thread in threads:
        thread.join(100)
if args.debug:
    Util.log_timestamp("End Generating HTML File(s)",logger)


exit(0)