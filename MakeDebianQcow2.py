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

neededTools = ["which", "qemu-img","kvm"]

# Configure ArgumentParser
parser = argparse.ArgumentParser(prog="MakeDebianQcow2.py",version=__version__,description="Bla", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="")
parser.add_argument("-i", "--isofile", metavar="ISOFILE", required=True, help="path to Debian Autoinstall Iso")
parser.add_argument("-f", "--outputfolder", metavar="OUTPUTFOLDER", required=True, help="path to outputfolder (will be created if not existent) (> 5 gb)")
parser.add_argument("-g", "--graphic", action="store_true", help="show graphic output, normally -nographic is used. Useful if you don't use a preseeded iso.")
parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite if QCOW2 File is existing")
parser.add_argument("-l", "--log", action='store_true', help="Be more verbose, log vagrant output.")
parser.add_argument("-s", "--size", metavar="SIZE", type=int, default=50, help="Size in Gigabyte (50 is default), e.g. 50 for 50G (will be compressed, Qcow2 file size will be much lesser!)")
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

if not (Util.check_file_exists(args.isofile) and Util.check_file_readable(args.isofile)):
    logger.error("Isofile %s does not exist or is not readable." %(args.isofile))
    exit(-1)

if not Util.check_folder(args.outputfolder,logger,False,True):
    if not Util.create_folder(args.outputfolder) or not Util.check_folder(args.outputfolder,logger):
        logger.error("Can't create %s." %(args.outputfolder))
        exit(-1)

isoFileName=os.path.basename(args.isofile)
imgFileBase="default"
if len(os.path.splitext(args.isofile)) > 0:
    imgFileBase=os.path.splitext(isoFileName)[0]
imgFileExtRaw=".img"
imgFileExtQcow2=".qcow2"
imgFileRaw="%s%s" %(imgFileBase,imgFileExtRaw)
imgFileQcow2="%s%s" %(imgFileBase, imgFileExtQcow2)

for file in [imgFileRaw,imgFileQcow2]:
    if Util.check_file_exists(os.path.join(args.outputfolder,file)):
        if args.overwrite:
            if not Util.delete_file(os.path.join(args.outputfolder,file),logger):
                logger.error("Error while deleting %s." %(os.path.join(args.outputfolder,file)))
                exit(-1)
        else:
            logger.error("Outputfile %s does exist." %(os.path.join(args.outputfolder,file)))
            exit(-1)

with lcd(os.path.join(args.outputfolder)), settings(warn_only=True), hide('output','running','warnings'):
    ret=local("qemu-img create -f qcow2 \"%s\" %sG" %(imgFileRaw,args.size))
    if ret.return_code != 0:
        logger.error("Can't create %s. Error: %s" %(os.path.join(args.outputfolder,imgFileRaw),ret.stderr))
        exit(-1)
    graphic=" -nographic"
    if args.graphic:
        graphic=""
    ret=local("kvm -hda \"%s\" -cdrom \"%s\" -m 2048 -smp 2%s" %(imgFileRaw,args.isofile,graphic))
    if ret.return_code != 0:
        logger.error("Can't install %s on %s with kvm. Error: %s" %(args.isofile,os.path.join(args.outputfolder,imgFileRaw),ret.stderr))
        exit(-1)
    # compat needed if NOT using an very old qemu-img!
    ret=local("qemu-img convert -f qcow2 -c \"%s\" -o compat=0.10 -O qcow2 \"%s\"" %(imgFileRaw,imgFileQcow2))
    if ret.return_code != 0:
        logger.error("Can't compress %s to %s. Error: %s" %(os.path.join(args.outputfolder,imgFileRaw),os.path.join(args.outputfolder,imgFileQcow2),ret.stderr))
        exit(-1)

if not Util.delete_file(os.path.join(args.outputfolder,imgFileRaw), logger):
    logger.error("Can't delete %s." %(os.path.join(args.outputfolder,imgFileRaw)))
    exit(-1)
exit(0)