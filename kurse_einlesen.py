#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
from collections import defaultdict

def kurse_einlesen():
    data=defaultdict(dict)
    with codecs.open('GPU001.TXT','r','iso-8859-1') as f:
        for line in f:
            data0 = line.split(',')
            if data0[1] in ['"10X"','"11X"','"12X"','"13X"']:
                #print data0[1],data0[2],data0[3]
                data[data0[1][1:-1]][data0[3][1:-1]]=data0[2][1:-1]
    #for fach in data['10X']:
    #    print fach, data['10X'][fach]

    #for key in data.keys():
    #    print key, type(key)

    return data

if __name__=="__main__":
    kurse_einlesen()
    
