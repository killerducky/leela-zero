#!/usr/bin/python3

import os

LEELAZ = '/home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz'
opts = '-p 1 --noponder'

def sgfheatmap(testname, movenum, rots=[0]):
    if movenum:
        logfile = '%s_%d.log' % (testname, movenum)
        if os.path.isfile(logfile): os.remove(logfile)
        for rot in rots:
            os.system('printf "loadsgf %s.sgf %d\nheatmap %d" | %s -w ladder.txt -l %s' % (testname, movenum, rot, LEELAZ, logfile))
    else:
        logfile = '%s_end.log' % (testname)
        if os.path.isfile(testname): os.remove(testname)
        for rot in rots:
            os.system('printf "loadsgf %s.sgf\nheatmap %d" | %s -w ladder.txt -l %s' % (testname, LEELAZ, rot, logfile))

def sgfplay(testname, movenum):
    logfile = 'play_%s_%d.log' % (testname, movenum)
    if os.path.isfile(logfile): os.remove(logfile)
    os.system('printf "loadsgf %s.sgf\nauto" | %s -w ladder.txt %s -l %s' % (testname, LEELAZ, opts, logfile))

sgfheatmap('ladder_good', 14)
sgfheatmap('ladder_bad', 14)
sgfheatmap('ladder_good', 15)
sgfheatmap('ladder_bad', 15)
sgfheatmap('ladder_long_bad', 12)
sgfheatmap('ladder_long_bad', 13)
#sgfplay('ladder_good', 14)
