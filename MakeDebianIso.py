#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

import argparse
import logging
import Util
import os
import shutil
from fabric.api import *

outputFileNameSuffix="-autoinstall"

neededTools = ["which", "sed","7z", "genisoimage", "gzip", "find", "cpio", "md5sum"]

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="MakeDebianIso.py",version=__version__,description="Bla", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-t", "--tmpfolder", metavar="TMPFOLDER", required=True, help="path to tmp space (> 5 gb)")
parser.add_argument("-i", "--isofile", metavar="ISOFILE", required=True, help="path to Debian Iso")
parser.add_argument("-f", "--outputfolder", metavar="OUTPUTFOLDER", required=True, help="path to outputfolder (will be created if not existent)")
parser.add_argument("-p", "--presseedfile", metavar="PRESEEDFILE", required=True, help="path to preseedfile")
parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite if ISO is existing")
parser.add_argument("-l", "--log", action='store_true', help="Be more verbose, log vagrant output.")
args = parser.parse_args()

# Configure Logging
logLevel = logging.WARN
if args.log:
    logLevel = logging.DEBUG
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

# Check ob alle Tools da sind
for tool in neededTools:
    with settings(warn_only=True), hide('output','running','warnings'):
        ret=local("which '%s'" %(tool))
        if ret.return_code != 0:
            logger.error("'%s' not found, please install." %(tool))
            exit(-1)

if not (Util.check_file_exists(args.presseedfile) and Util.check_file_readable(args.presseedfile)):
    logger.error("Preseedfile %s does not exist or is not readable." %(args.presseedfile))
    exit(-1)

if not (Util.check_file_exists(args.isofile) and Util.check_file_readable(args.isofile)):
    logger.error("Isofile %s does not exist or is not readable." %(args.isofile))
    exit(-1)

if not Util.check_folder(args.outputfolder,logger,False,True):
    if not Util.create_folder(args.outputfolder) or not Util.check_folder(args.outputfolder,logger):
        logger.error("Can't create %s." %(args.outputfolder))
        exit(-1)

if not Util.check_folder(args.tmpfolder,logger,False,True):
    if not Util.create_folder(args.tmpfolder) or not Util.check_folder(args.tmpfolder,logger):
        logger.error("Can't create %s." %(args.tmpfolder))
        exit(-1)
else:
    Util.delete_folder(args.tmpfolder,logger)
    if not Util.create_folder(args.tmpfolder) or not Util.check_folder(args.tmpfolder,logger):
        logger.error("Can't create %s." %(args.tmpfolder))
        exit(-1)

isoFileName=os.path.basename(args.isofile)
isoFileBase="default"
if len(os.path.splitext(args.isofile)) > 0:
    isoFileBase=os.path.splitext(isoFileName)[0]
isoFileExt=".iso"
if len(os.path.splitext(args.isofile)) > 1:
    isoFileExt=os.path.splitext(isoFileName)[1]
preseedSuffix=""
if len(os.path.splitext(os.path.basename(args.presseedfile))[0].split("-")) > 1:
    for suffix in os.path.splitext(os.path.basename(args.presseedfile))[0].split("-")[1:]:
        preseedSuffix += "-%s" %(suffix)
newIsoFileName="%s%s%s%s" %(isoFileBase,preseedSuffix,outputFileNameSuffix,isoFileExt)
isoPath=os.path.join(args.tmpfolder,isoFileName)

if Util.check_file_exists(os.path.join(args.outputfolder,newIsoFileName)):
    if args.overwrite:
        if not Util.delete_file(os.path.join(args.outputfolder,newIsoFileName),logger):
            logger.error("Error while deleting %s." %(os.path.join(args.outputfolder,newIsoFileName)))
            exit(-1)
    else:
        logger.error("Outputfile %s does exist." %(os.path.join(args.outputfolder,newIsoFileName)))
        exit(-1)

# Copy Iso to tmpfolder
try:
    shutil.copy(args.isofile, isoPath)
except Exception, e:
    logger.error("Can't copy %s to %s." %(args.isofile,args.tmpfolder), exc_info=True)
    exit(-1)

# Unpack it with 7z
with lcd(args.tmpfolder), settings(warn_only=True), hide('output','running','warnings'):
    ret=local("7z x '%s'" %(isoFileName), capture=True)
    if not ret.succeeded:
        logger.error("Can't unpack %s. Error: %s" %(isoPath,ret.stderr))
        exit(-1)

# Delete ISO
if not Util.delete_file(isoPath, logger):
    logger.error("Can't delete %s." %(isoPath))
    exit(-1)

# mkdir irmod, unzip initrd.gz
if not Util.create_folder(os.path.join(args.tmpfolder,"irmod")):
    logger.error("Can't create %s." %(os.path.join(args.tmpfolder,"irmod")))
    exit(-1)
with lcd(os.path.join(args.tmpfolder,"irmod")), settings(warn_only=True), hide('output','running','warnings'):
    ret=local("gzip -d < ../install.amd/initrd.gz | cpio --extract --verbose --make-directories --no-absolute-filenames")
    if ret.return_code != 2:
        logger.error("Can't unpack %s. Error: %s" %(os.path.join(args.tmpfolder,"install.amd/initrd.gz"),ret.stderr))
        exit(-1)

# Copy Pressed file in place
if not Util.copy_file(args.presseedfile, os.path.join(args.tmpfolder,"irmod","preseed.cfg"),logger):
    logger.error("Can't copy %s to %s." %(args.presseedfile, os.path.join(args.tmpfolder,"irmod","preseed.cfg")))
    exit(-1)

# Pack & Compress it again
with lcd(os.path.join(args.tmpfolder,"irmod")), settings(warn_only=True), hide('output','running','warnings'):
    ret=local("find . | cpio -H newc --create --verbose | gzip -9 > ../install.amd/initrd.gz")
    if not ret.succeeded:
        logger.error("Can't pack %s. Error: %s" %(os.path.join(args.tmpfolder,"install.amd/initrd.gz"),ret.stderr))
        exit(-1)

# Delete irmod
if not Util.delete_folder(os.path.join(args.tmpfolder,"irmod"),logger):
    logger.error("Can't delete %s." %(os.path.join(args.tmpfolder,"irmod")))
    exit(-1)

# Running sed + generating md5sum + genisoimage
with lcd(args.tmpfolder), settings(warn_only=True), hide('output','running','warnings'):
    ret=local("sed -i \"s/timeout 0/timeout 2/g\" isolinux/isolinux.cfg")
    if not ret.succeeded:
        logger.error("Error while sed run on %s. Error: %s" %(os.path.join(args.tmpfolder,"isolinux/isolinux.cfg"),ret.stderr))
        exit(-1)
    ret=local("sed -i \"s/quiet/ipv6.disable=1 quiet/g\" isolinux/txt.cfg")
    if not ret.succeeded:
        logger.error("Error while sed run on %s. Error: %s" %(os.path.join(args.tmpfolder,"isolinux/txt.cfg"),ret.stderr))
        exit(-1)
    ret=local("md5sum `find -follow -type f` > md5sum.txt")
    if not ret.succeeded:
        logger.error("Error while md5sum+find run. Error: %s" %(ret.stderr))
        exit(-1)
    ret=local("genisoimage -o \"%s\" -r -J -no-emul-boot -boot-load-size 4 -boot-info-table -b isolinux/isolinux.bin -c isolinux/boot.cat ." %(os.path.join(args.tmpfolder,newIsoFileName)))
    if not ret.succeeded:
        logger.error("Error while genisoimage run. Error: %s" %(ret.stderr))
        exit(-1)

# Copy Iso, delete tmpfolder
if os.path.join(args.tmpfolder,newIsoFileName) != os.path.join(args.outputfolder,newIsoFileName):
    if not Util.copy_file(os.path.join(args.tmpfolder,newIsoFileName),os.path.join(args.outputfolder,newIsoFileName),logger):
        logger.error("Could not copy %s to %s." %(os.path.join(args.tmpfolder,newIsoFileName),os.path.join(args.outputfolder,newIsoFileName)))
        exit(-1)
if not Util.delete_folder(args.tmpfolder,logger):
    logger.error("Can't delete %s." %(args.tmpfolder))
    exit(-1)
logger.info("Done.")
exit(0)