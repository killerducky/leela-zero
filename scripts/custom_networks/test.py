#!/usr/bin/python3

import os
import sys

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

def sgfplay(testname, movenum, moves):
    logfile = 'play_%s_%d.log' % (testname, movenum)
    if os.path.isfile(logfile): os.remove(logfile)
    gtpcmds = 'loadsgf %s.sgf %d\nheatmap' % (testname, movenum)
    for move in moves:
        gtpcmds += '\nplay %s %s\nheatmap' % (("W","B")[movenum%2], move)
        movenum += 1
    os.system('printf "%s" | %s -w ladder.txt -l %s' % (gtpcmds, LEELAZ, logfile))
    print(gtpcmds)

def ladderseq(start, ladder_length):
    pattern = [[0,1],[1,-1],[1,0],[-1,1]]
    x = ord(start[0])
    y = int(start[1])
    seq = [start]
    while ladder_length>0:
        for p in pattern:
            x += p[0]
            y += p[1]
            sgflet = chr(x)
            if sgflet >= "i": sgflet = chr(x+1)
            seq += [sgflet+str(y)]
            ladder_length -= 1
            if ladder_length==0: break
    return seq

#sgfheatmap('ladder_good', 14)
#sgfheatmap('ladder_bad', 14)
#sgfheatmap('ladder_good', 15)
#sgfheatmap('ladder_bad', 15)
#sgfheatmap('ladder_long_bad', 12)
#sgfheatmap('ladder_long_bad', 13)
seq = ladderseq("e7", 40)
print(seq)
print(len(seq))
sgfplay('ladder_long_bad', 12, seq)
#sgfauto('ladder_good', 14)
