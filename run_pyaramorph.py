# -*- coding: utf-8 -*-

from pyaramorph.pyaramorph import Analyzer
morph = Analyzer()

def run_pyaramorph(bw):
    return morph.analyze(bw)
   


#bw_list = ["ktb", "ktAbA", "fy", "Almktb"]
bw_list = ["ktb", "AlTfl", "AlwZyfp"]

for bw in bw_list:
    result = run_pyaramorph(bw)
    for line in result:
        print line
    print "---------------------"




