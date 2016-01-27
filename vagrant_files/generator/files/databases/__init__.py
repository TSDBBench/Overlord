#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Andreas Bader'
__version__ = "0.01"

import pkgutil

def getDict(logger):
    dbConfig = {}
    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        try:
            m = importer.find_module(modname).load_module(modname)
            dbConfig[modname] = m.getDict()
        except Exception, e:
            logger.error("Can't import %s/%s." %(__path__,modname), exc_info=True)
            return {}
    return dbConfig
