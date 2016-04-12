#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

import pkgutil
from collections import defaultdict

def getDict(logger):
    baseConfig = {}
    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        try:
            m = importer.find_module(modname).load_module(modname)
            baseConfig[modname] = m.getDict()
        except Exception, e:
            logger.error("Can't import %s/%s." %(__path__[0],modname), exc_info=True)
            return {}
        for modname in baseConfig.keys():
            if "include" in baseConfig[modname].keys():
                for base_config_module in baseConfig[modname]["include"]:
                    for key in baseConfig[base_config_module]:
                        if key not in baseConfig[modname].keys():
                            logger.error("Can't import base/%s into base/%s. %s does not exist as key in %s."
                                         % (base_config_module, modname, key, modname), exc_info=True)
                            return {}
                        if type(baseConfig[base_config_module][key]) != type(baseConfig[modname][key]):
                            logger.error("Can't import base/%s into base/%s. %s does not have the same types."
                                         % (base_config_module, modname, key), exc_info=True)
                            return {}
                        if isinstance(baseConfig[base_config_module][key], basestring):
                            # if it is  a list
                            baseConfig[modname][key] += baseConfig[base_config_module][key]
                        elif isinstance(baseConfig[base_config_module][key], dict):
                            # if it is a dictionary
                            default_dict = defaultdict(list, baseConfig[modname][key])
                            for i, j in baseConfig[base_config_module][key].items():
                                default_dict[i].extend(j)
                            baseConfig[modname][key] = dict(default_dict)
                        else:
                            # error
                            logger.error("Can't import base/%s into base/%s. %s of base is not a list and not a dict."
                                         % (base_config_module, modname, key), exc_info=True)
                            return {}
    return baseConfig
