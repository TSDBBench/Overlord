#!/usr/bin/python2
import sys
from random import randint
print "FIELD1,FIELD2,FIELD3,FIELD4,FIELD5,FIELD6,FIELD7,FIELD8,FIELD9,FIELD10"
for i in range(0,1000000):
    print "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" %(randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),randint(0,sys.maxint),)
