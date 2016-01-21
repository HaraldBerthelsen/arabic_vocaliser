# -*- coding: utf-8 -*-

import pyaramorph

def run_pyaramorph(ar):
    proc.stdin.write(ar.encode("windows-1256"))
    proc.stdin.write("\n")
    #res = proc.stdout.readline()
    res = proc.stdout.read()
    print "res:", res
    return res

   


ar_list = [u"كتب", u"كتب", u"كتب"]

for ar in ar_list:
    print run_aramorph(ar)
    print "---------------------"




