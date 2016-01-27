#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

import os
import shutil
import time
import random

def check_file_readable(filename):
    if check_file_exists(filename) and os.access(filename, os.R_OK):
        return True
    return False

def check_file_exists(filename):
    if os.path.isfile(filename):
        return True
    return False

# Check if folder exists
def check_folder(path,logger,reverseLogic=False, noError=False):
    if not(os.path.isdir(path) and os.path.exists(path)):
        if not reverseLogic:
            if not noError:
                logger.error("%s does not exist." %(path))
            return False
        else:
            return True
    if not reverseLogic:
        return True
    else:
        if not noError:
            logger.error("%s does exist." %(path))
        return False

def delete_folder(path,logger,no_error=False):
    if check_folder(path,logger):
        try:
            shutil.rmtree(path)
        except Exception, e:
            logger.warning('Failed to delete %s.' %(path), exc_info=True)
            return False
        return True
    else:
        if no_error:
            return True
        return False

def delete_file(path,logger,no_error=False):
    if os.path.isfile(path):
        try:
            os.remove(path)
        except Exception, e:
            logger.error('Failed to remove file', exc_info=True)
            return False
        return True
    else:
        if no_error:
            return True
        return False


def copy_folder(path1,path2,logger):
    try:
        shutil.copytree(path1, path2, symlinks=False, ignore=None)
    except Exception, e:
        logger.error('Failed to copy %s to %s.' %(path1,path2), exc_info=True)
        return False
    return True

def copy_file(path1,path2,logger):
    try:
        shutil.copyfile(path1,path2)
    except Exception, e:
        logger.error('Failed to copy %s to %s.' %(path1,path2), exc_info=True)
        return False
    return True

# delete *.vagrant files in given path
def clear_vagrant_files(path,logger):
    if check_folder(path,logger):
        for path2 in os.listdir(path):
            if os.path.isfile(os.path.join(path,path2)):
                split = path2.rsplit(".vagrant",1)
                # if rsplit is used on bla.vagrant, the result should be ["bla",""]
                if len(split) > 1 and split[1] == "":
                    try:
                        os.remove(os.path.join(path,path2))
                    except Exception, e:
                        logger.warning('Failed to remove file.', exc_info=True)
    else:
        logger.warning("Can't clean %s." %(path))

def check_if_in_databases(str, databases):
    for database in databases:
        if str.lower() in database.lower():
            return True
    return False

def check_if_in_databases_rsplit(str, databases):
    for database in databases:
        if str.lower() in database.rsplit("_",1)[0].lower():
            return True
    return False

def check_if_eq_databases(str, databases):
    for database in databases:
        if str.lower() in database.lower():
            return True
    return False

def check_if_eq_databases_rsplit(str, databases):
    for database in databases:
        if str.lower() == database.rsplit("_",1)[0].lower():
            return True
    return False

def clean_space(line):
    str = line
    while str[0] == ' ':
        str = str[1:]
    while str[-1] == ' ':
        str = str[:-1]
    return str

def clean_quote(line):
    str = line
    while str[0] == '\'':
        str = str[1:]
    while str[-1] == '\'':
        str = str[:-1]
    return str

def clean_newline(line):
    str = line
    while str[0] == '\n':
        str = str[1:]
    while str[-1] == '\n':
        str = str[:-1]
    return str

def clean_newline_space(line):
    str = line
    while str[0] == '\n' or str[0] == ' ':
        str = str[1:]
    while str[-1] == '\n' or str[-1] == ' ':
        str = str[:-1]
    return str

def clean_quote_space(line):
    str = line
    while str[0] == '\'' or str[0] == ' ':
        str = str[1:]
    while str[-1] == '\'' or str[-1] == ' ':
        str = str[:-1]
    return str

def create_folder(folder):
    try:
        os.makedirs(folder)
    except:
        return False
    return True

def get_random_int(start,end):
    return random.randint(start,end)

def get_random_float(start,end):
    return random.uniform(start,end)

def sleep_random(start,end):
    time.sleep(get_random_float(start,end))

def get_random_int_with_chosen(start, end, chosenList):
    return get_random_int_with_chosen_default(start,end,chosenList,[])

def get_random_int_with_chosen_default(start, end, chosenList, defaultList):
    if abs(end-start) <= len(chosenList):
        return None
    for value in defaultList:
        if value not in chosenList and value >= start and value <= end:
            return value
    randomInt = random.randint(start,end)
    while randomInt in chosenList:
        randomInt = random.randint(start,end)
    return randomInt

def log_timestamp(str,logger):
    logger.debug("Timestamp at %s" %(str))