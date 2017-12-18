#!/usr/bin/env python3
#
#    This file is part of Leela Zero.
#    Copyright (C) 2017 Andy Olsen
#
#    Leela Zero is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Leela Zero is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Leela Zero.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import gzip
import math
import fileinput
import collections
import os
import itertools
import functools
import sys

NIBBLE = 4
BOARDSIZE = 19
TURNSIZE = 19
HISTORY_PLANES = 8
TOMOVE = 16
POLICY = 17
WINNER = 18
ZERO_LINE = "0"*math.ceil((BOARDSIZE**2+1)/NIBBLE) + "\n" # 361+1 bits in hex nibbles

class Turn():
    def __init__(self, turn):
        self.valid = len(turn) == TURNSIZE
        if not self.valid: return
        self.board = turn[:HISTORY_PLANES*2]
        self.to_move = int(turn[TOMOVE])              # 0 = black, 1 = white
        self.policy_weights = turn[POLICY].split()    # 361 moves + 1 pass
        self.side_to_move_won = int(turn[WINNER])     # 1 = side to move won, -1 = lost
        self.empty_board = all(line == ZERO_LINE for line in self.board)
        self.early_board = self.board[-1] == ZERO_LINE
    def pass_weight(self):
        return float(self.policy_weights[-1])

def findEmptyBoard(filename):
    tfh = fileinput.FileInput(filename, mode="rb", openhook=fileinput.hook_compressed)
    count = collections.Counter()
    prev_turn = None
    while (1):
        turn = Turn([line.decode("utf-8") for line in itertools.islice(tfh, TURNSIZE)])
        if not turn.valid: break
        if turn.empty_board and turn.to_move == 0:
            count["first_move"] += 1
        if turn.board[-1] == ZERO_LINE and turn.to_move == 1:
            count["white_early"] += 1
        if prev_turn and turn.early_board and prev_turn.board == turn.board and turn.to_move == 1:
            # black passed on previous turn in the very early game, check stats
            print("black passed. empty_board:%s file:%s lineno:%d black pass:%0.2f%% white pass:%0.2f%%" %
                (turn.empty_board, filename, tfh.filelineno(), prev_turn.pass_weight()*100, turn.pass_weight()*100))
            if not turn.empty_board:
                for line in turn.board:
                    print(line, eol="")
            count["black_pass"] += 1
            count[turn.policy_weights.count("0")] += 1
        policy_sum = sum(map(float, turn.policy_weights))
        if abs(1.0 - policy_sum) > 0.001:
            print("policy_sum:%0.2f file:%s %lienno:5d" % (policy_sum, filename, tfh.filelineno()))
        prev_turn = turn
    return count

def main():
    usage_str = """
This script analyzes training data for abnormal results.
"""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=usage_str)
    parser.add_argument("files", metavar="files", type=str, nargs="+", help="training files (with or without *.gz)")
    args = parser.parse_args()
    total_first_move_cnt = 0
    totalCount = collections.Counter()
    for filename in args.files:
        sys.stderr.write(filename + "\n")
        fileCount = findEmptyBoard(filename)
        totalCount.update(fileCount)
    for k in sorted(totalCount.keys(), key=lambda k: (type(k)==int, k)):
        print(k,totalCount[k])

if __name__ == "__main__":
    main()


