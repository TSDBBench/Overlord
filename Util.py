#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.02"

import os
import shutil
import time
import random
import distutils
from distutils import dir_util

def check_file_readable(filename):
    if check_file_exists(filename) and os.access(filename, os.R_OK):
        return True
    return False

def check_file_exists(filename):
    if os.path.isfile(filename):
        return True
    return False

# Check if folder exists
def check_folder(path, logger, reverseLogic=False, noError=False):
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

def check_folders(paths, logger, reverseLogic=False, noError=False, oneIsEnough=False):
    if not oneIsEnough:
        return_value = True
    else:
        return_value = False
    for path in paths:
        if not check_folder(path, logger, reverseLogic, noError):
            if not oneIsEnough:
                return_value = False
        else:
            if oneIsEnough:
                return_value = True
    return return_value

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
        # distutils required here as shutil.copytree can not overwrite directories which is needed for multiple vagrant folders
        distutils.dir_util.copy_tree(path1, path2, preserve_mode=1, preserve_times=1, preserve_symlinks=1, update=0, verbose=0, dry_run=0)
    except distutils.dir_util.DistutilsFileError, e:
        logger.error('Failed to copy %s to %s.' %(path1,path2), exc_info=True)
        return False
    return True

def copy_folders(paths,path2,logger,ignore_not_existing=False):
    return_value = True
    for path in paths:
        if ignore_not_existing and not check_folder(path,logger,False,True):
            continue
        if not copy_folder(path, path2, logger):
            return_value = False
    return return_value

# creates a list from a list of touples (path+folder)
def create_folder_path_list(path_and_folders):
    new_list = []
    for element in path_and_folders:
        new_list.append(os.path.join(element[0], element[1]))
    return new_list

def create_folder_path_list(paths, folders):
    new_list = []
    for path in paths:
        for folder in folders:
            new_list.append(os.path.join(path, folder))
    return new_list

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

def sorted_paths(path_list, logger, append_path="", sort=True, reverse=False, return_seperated=True):
    unsorted_list = []

    for folder in path_list:
        # list of files/dirs inside a directory always sorted
        act_path = os.path.join(folder,append_path)
        if not check_folder(act_path,logger, False,True):
            continue
        for dir in sorted(os.listdir(act_path)):
            if return_seperated:
                unsorted_list.append((act_path,dir))
            else:
                unsorted_list.append(os.path.join(act_path,dir))
    if sort:
        unsorted_list = sorted(unsorted_list)
    if reverse:
        unsorted_list = list(reversed(unsorted_list))
    return unsorted_list

def unsorted_paths(path_list, logger, append_path="", reverse=False, return_seperated=True):
    return sorted_paths(path_list, logger, append_path, False, reverse, return_seperated)