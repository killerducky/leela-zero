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

def sgfauto(testname, movenum):
    logfile = 'auto_%s_%d.log' % (testname, movenum)
    if os.path.isfile(logfile): os.remove(logfile)
    os.system('printf "loadsgf %s.sgf\nauto" | %s -w ladder.txt %s -l %s' % (testname, LEELAZ, opts, logfile))

def sgfplay(testname, movenum, moves, rots):
    logfile = 'play_%s_%d.log' % (testname, movenum)
    if os.path.isfile(logfile): os.remove(logfile)
    gtpcmds = 'loadsgf %s.sgf %d\nheatmap %d' % (testname, movenum, rots[0])
    for move,rot in zip(moves,rots[1:]):
        gtpcmds += '\nplay %s %s\nheatmap %d' % (("W","B")[movenum%2], move, rot)
        movenum += 1
    os.system('printf "%s" | %s -w ladder.txt -l %s' % (gtpcmds, LEELAZ, logfile))
    print(gtpcmds)

#sgfheatmap('ladder_good', 14)
#sgfheatmap('ladder_bad', 14)
#sgfheatmap('ladder_good', 15)
#sgfheatmap('ladder_bad', 15)
#sgfheatmap('ladder_long_bad', 12)
#sgfheatmap('ladder_long_bad', 13)
sgfplay('ladder_long_bad', 12, ["e7", "e8", "f7", "g7", "f8", "f9"], [0,0,4,4,0,0])
#sgfauto('ladder_good', 14)
