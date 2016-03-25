#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

import threading
import time
import vagrant
import os
import Util
import re
from fabric.api import *

class Vm():

    vagrantFolders=None
    pathVagrantfile=None
    credFiles=None
    basicFilesFolder=None
    pathFolder=None
    tmpFolder=None
    name=None
    logging=False
    logger=None
    created=False
    vm=None
    thread=None
    provider=None
    ip=None

    # vagrantFolders: Folders inside which vagrantfiles+folders are
    # tmpFolder: Path to tempfolder
    # name: name of the VM
    # logger: Logger instance
    # logging: if true, vagrant debug logging will be done
    def __init__(self, vagrantFolders, credFiles, basicFilesFolder, tmpFolder, name, logger, provider, logging):
        self.vagrantFolders = vagrantFolders
        self.credFiles=credFiles
        self.basicFilesFolder=basicFilesFolder
        self.tmpFolder = tmpFolder
        self.name = name
        self.logger = logger
        self.logging = logging
        self.provider = provider

    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def join(self):
        self.thread.join()

    def run(self):
        if not self.created:
            self.create_vm()
        else:
            self.destroy()

    def destroy(self):
        if self.vm != None:
            return self.vm.destroy()
        return True

    def create_vm(self):
        # Check if you want to log
        log_cm=None
        self.logger.info("BEGIN Creating %s." %(self.name))
        if self.logging:
            try:
                filename="%s_%s.log" %(self.name,time.strftime("%Y%m%d%H%M%S", time.localtime()))
                log_cm = vagrant.make_file_cm(filename)
                self.logger.info("Logging creation of %s to %s." % (self.name,filename))
            except Exception, e:
                self.logger.error('Failed to open file', exc_info=True)
                return False
        pathName=self.name.rsplit("_",1)[0] # Name is something like VMNAME_1, split _1 away!
        # copy to tmpfolder (already checked that it exist, need to check if vm folder exists)
        paths=Util.create_folder_path_list(self.vagrantFolders, [pathName])
        pathTmp=os.path.join(self.tmpFolder,self.name)
        if not Util.check_folders(paths, self.logger, False, True, True):
            return False
        if not Util.check_folder(pathTmp, self.logger, True):
            return False
        # Copy Vagrantfile in place
        pathVagrantFileOld=os.path.join(pathTmp,"%s.vagrant"%(self.name))
        pathVagrantFileNew=os.path.join(pathTmp,"Vagrantfile")
        if not Util.copy_folders(paths,pathTmp,self.logger, True):
            return False
        self.pathFolder=pathTmp
        for credFile in self.credFiles:
            credFilesOld = Util.create_folder_path_list(self.vagrantFolders, [credFile])
            pathCredFileNew = os.path.join(pathTmp,credFile)
            for credFileOld in credFilesOld:
                if Util.check_file_exists(credFileOld):
                    if not Util.copy_file(credFileOld,pathCredFileNew,self.logger):
                        return False
        basicFileFoldersOld=Util.create_folder_path_list(self.vagrantFolders, [self.basicFilesFolder])
        pathBasicFileFolderNew=os.path.join(pathTmp,self.basicFilesFolder)
        if not Util.copy_folders(basicFileFoldersOld,pathBasicFileFolderNew,self.logger, True):
                return False
        if self.provider == "digital_ocean":
            # digital ocean needs a random name, otherwise we always get problems with multiple measurements
            if Util.check_file_exists(pathVagrantFileNew):
                self.logger.error("'%s' does already exist." %(pathVagrantFileNew))
                return False
            try:
                file_old = open(pathVagrantFileOld, "r")
                file_new = open(pathVagrantFileNew, "w")
                for line in file_old:
                    if re.match(r'^\s*HOSTNAME\s+=\s+("[^"]+"|\'[^\']+\')\s*$',line) != None:
                        split_res = re.search(r'("[^"]+"|\'[^\']+\')',line)
                        if split_res != None:
                            # allowed are numbers, letters, hyphens and dots
                            file_new.write("HOSTNAME = \"%s-%s\"\n" %(split_res.group()[1:-1],
                                                                      Util.get_random_string(10)))
                        else:
                            self.logger.warning("Could not parse hostname out of '%s'. "
                                                "Using the default. Errors can occur." % (line))
                            file_new.write(line)
                    else:
                        file_new.write(line)
                file_new.flush()
                file_new.close()
                file_old.close()
            except Exception,e:
                self.logger.error("An error occured while copying '%s' to '%s'." % (pathVagrantFileOld,
                                                                                    pathVagrantFileNew), exc_info=True)
        else:
            if not Util.copy_file(pathVagrantFileOld,pathVagrantFileNew,self.logger):
                return False
        self.pathVagrantfile=pathVagrantFileNew
        Util.clear_vagrant_files(pathTmp,self.logger)
        # Create VM
        try:
            vm = vagrant.Vagrant(root=pathTmp, out_cm=log_cm, err_cm=log_cm)
            self.vm=vm
            vm.up(provider=self.provider)
            # with settings(host_string= vm.user_hostname_port(),
            #                  key_filename = vm.keyfile(),
            #                  disable_known_hosts = True):
            #         run("uname -a")
        except Exception, e:
            self.logger.error('Failed while creating vm %s.' %(self.name), exc_info=True)
            self.logger.info('Since creation failed, trying to destroy vm %s.' %(self.name), exc_info=True)
            #if not self.vm.destroy():
                # self.logger.error('Can not destroy %s.' %(self.name), exc_info=True)
            ## vm.destroy() seems to be always returning false at this stage (opentsack), but destroying works fine -> Ignore it.
            self.vm.destroy()
            return False
        self.logger.info("END Creating %s." %(self.name))
        self.logger.info("GET IP of %s." %(self.name))
        self.ip = self.get_ip()
        # the IP Part is needed, because on OpenStack the 'internal' IP differs from the 'external' (SSH) IP
        if self.ip == None:
            self.logger.error('Failed getting IP while creating vm %s.' %(self.name), exc_info=True)
            self.logger.info('Since creation failed, trying to destroy vm %s.' %(self.name), exc_info=True)
            self.vm.destroy()
            return False
        self.created=True
        return True

    # Return the output
    def run_with_output (self,disableKnownHosts,command,warn_only=False,quiet=False):
        with settings(host_string = self.vm.user_hostname_port(),
                     key_filename = self.vm.keyfile(),
                     disable_known_hosts = disableKnownHosts):
            result = run(command,warn_only=warn_only, quiet=quiet)
            return result

    # Only return true/false
    def run_without_output (self,disableKnownHosts,command,warn_only=False,quiet=False,test=False):
        result = self.run_with_output (disableKnownHosts,command,warn_only,quiet)
        if result.return_code == 0 or (warn_only and result.return_code == 255) or (test and result.return_code == -1):
            return True
        else:
            self.logger.error("Command '%s' on %s returned %s." %(command, self.vm.user_hostname_port(), result.return_code))
            return False

    def get_ip(self):
        head_str = " | head -n1"
        if self.provider in ["virtualbox", "digital_ocean"]:
            # virtualbox uses second network interface for vm-interconnections
            head_str =  " | head -n4 | tail -n1"
        result = self.run_with_output (True,'sudo ifconfig | grep -E -o "(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"%s' % (head_str),True, True)
        if result.return_code == 0:
            return result.stdout
        else:
            self.logger.error("Can't get IP on %s, command returned %s." %(self.vm.user_hostname_port(), result.return_code))
            return None