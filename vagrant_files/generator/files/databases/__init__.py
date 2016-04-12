#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

import pkgutil
import base
from collections import defaultdict

def getDict(logger):
    dbConfig = {}
    baseConfig = base.getDict(logger)
    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        if modname != "base" and modname not in baseConfig.keys():
            try:
                m = importer.find_module(modname).load_module(modname)
                dbConfig[modname] = m.getDict()
                if "include" in dbConfig[modname].keys():
                    for base_config_module in dbConfig[modname]["include"]:
                        for key in baseConfig[base_config_module]:
                            if key not in dbConfig[modname].keys():
                                logger.error("Can't import base/%s into %s/%s. %s does not exist as key in %s."
                                             % (base_config_module, __path__[0], modname, key, modname), exc_info=True)
                                return {}
                            if type(baseConfig[base_config_module][key]) != type(dbConfig[modname][key]):
                                logger.error("Can't import base/%s into %s/%s. %s does not have the same types."
                                             % (base_config_module, __path__[0], modname, key), exc_info=True)
                                return {}
                            if isinstance(baseConfig[base_config_module][key], list):
                                # if it is  a list
                                dbConfig[modname][key] += baseConfig[base_config_module][key]
                            elif isinstance(baseConfig[base_config_module][key], dict):
                                # if it is a dictionary
                                default_dict = defaultdict(list, dbConfig[modname][key])
                                for i, j in baseConfig[base_config_module][key].items():
                                    default_dict[i].extend(j)
                                dbConfig[modname][key] = dict(default_dict)
                            else:
                                # error
                                logger.error("Can't import base/%s into %s/%s. %s of base is not a list and not a dict."
                                             % (base_config_module, __path__[0], modname, key), exc_info=True)
                                return {}
            except Exception, e:
                logger.error("Can't import %s/%s." %(__path__[0],modname), exc_info=True)
                return {}
    return dbConfig
