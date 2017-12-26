#!/usr/bin/python3

import os

LEELAZ = '/home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz'

#os.system('rm 30f4_normal.log')
#os.system('rm 30f4_hack.log')
#os.system('printf "play b q4\nheatmap" | /home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz -w 30f4_normal.txt -l 30f4_normal.log')
#os.system('printf "play b q4\nheatmap" | /home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz -w 30f4_hack.txt -l 30f4_hack.log')
#os.system('printf "loadsgf hi.sgf\nheatmap" | /home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz -w 30f4_normal.txt -s 1 -l 30f4_normal.log')
#os.system('printf "loadsgf hi.sgf\nheatmap" | /home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz -w 30f4_hack.txt -s 1 -l 30f4_hack.log')

#os.system('rm one.log')
#os.system('rm two.log')
#os.system('printf "play b q4\nheatmap" | /home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz -w one.txt -l one.log')
#os.system('printf "play b q4\nheatmap" | /home/aolsen/projects/leela-zero-nn/leela-zero/src/leelaz -w two.txt -l two.log')

def sgftest(testname, movenum, rots=[0]):
    if movenum:
        logfile = '%s_%d.log' % (testname, movenum)
        os.system('rm %s' % (logfile))
        for rot in rots:
            os.system('printf "loadsgf %s.sgf %d\nheatmap %d" | %s -w ladder.txt -l %s' % (testname, movenum, rot, LEELAZ, logfile))
    else:
        logfile = '%s_end.log' % (testname)
        os.system('rm %s' % (testname))
        for rot in rots:
            os.system('printf "loadsgf %s.sgf\nheatmap %d" | %s -w ladder.txt -l %s' % (testname, LEELAZ, rot, logfile))

sgftest('ladder_good', 14)
sgftest('ladder_bad', 14)
sgftest('ladder_good', 15)
sgftest('ladder_bad', 15)

