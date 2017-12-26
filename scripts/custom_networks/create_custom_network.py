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

import sys
import argparse
import itertools

#N_RESIDUAL_FILTERS = 128   !! these aren't correct...
#N_RESIDUAL_BLOCKS = 6
#N_RESIDUAL_FILTERS = 64
#N_RESIDUAL_BLOCKS = 5
N_RESIDUAL_FILTERS = 16
N_RESIDUAL_BLOCKS = 1
INPUT_PLANES = 18
HISTORY_PLANES = 8

PATTERNS = {
    "ladder_escape"  : "X.." +
                       "OOX" +
                       "OX.",

    "ladder_atari"   : "..." +
                       "XO." +
                       "OOX",

    "ladder_maker"   : "ooo" +
                       "ooo" +
                       "ooo",

    "ladder_breaker" : "xxx" +
                       "xxx" +
                       "xxx" +
                       "+++" +
                       "+++" +
                       "+++",

    "ladder_continue" : "..." +
                        "..." +
                        "...",

}


NOT_IDENTITY = [0.0, 0.0, 0.0,
            0.0, -1.0, 0.0,
            0.0, 0.0, 0.0]
IDENTITY = [0.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 0.0]
SUM = [0.3, 0.3, 0.3,
       0.3, 0.3, 0.3,
       0.3, 0.3, 0.3]
ZERO = [0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0]

BOARD_FILTERS = {
    "tomove"  :  ([]
        + ZERO*1                       # Most recent opponent?
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent me?
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY                     # White/Black to move
        + ZERO),                       # White/Black to move
    # TODO: generalize escaper/chaser
    "escaper_stones" : ([]
        + IDENTITY*1                   # Most recent opponent?
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent me?
        + ZERO*(HISTORY_PLANES-1)
        + ZERO                         # White/Black to move
        + ZERO),                       # White/Black to move
    "chaser_stones" : ([]
        + ZERO*1                       # Most recent opponent?
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY*1                   # Most recent me?
        + ZERO*(HISTORY_PLANES-1)
        + ZERO                         # White/Black to move
        + ZERO),                       # White/Black to move
    "empty" : ([]
        + NOT_IDENTITY*1               # Most recent opponent?
        + ZERO*(HISTORY_PLANES-1)
        + NOT_IDENTITY*1               # Most recent me?
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY                     # White/Black to move  -- This plus next line is a quick and dirty way to add bias of 1
        + IDENTITY),                   # White/Black to move
    "not_edge" : ([]
        + ZERO*1                       # Most recent opponent?
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent me?
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY                     # White/Black to move
        + IDENTITY),                   # White/Black to move
    "init_to_zero" : ([]
        + ZERO*1                       # Most recent opponent?
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent me?
        + ZERO*(HISTORY_PLANES-1)
        + ZERO                         # White/Black to move
        + ZERO),                       # White/Black to move
}

#BOARD_IDENTITY = ([]
#    + SUM*1                        # Most recent opponent?
#    + ZERO*(HISTORY_PLANES-1)
#    + SUM*1                        # Most recent me?
#    + ZERO*(HISTORY_PLANES-1)
#    + ZERO                         # White/Black to move
#    + ZERO)                        # White/Black to move

BOARD_FILTER = ([]
    + BOARD_FILTERS["tomove"]
    + BOARD_FILTERS["escaper_stones"]
    + BOARD_FILTERS["chaser_stones"]
    + BOARD_FILTERS["empty"]
    + BOARD_FILTERS["not_edge"]
    + BOARD_FILTERS["init_to_zero"]*(N_RESIDUAL_FILTERS-5)
)

def str2filter(s):
    f = []
    f += ZERO # to move
    f += list(map(lambda w : float(w=="O" or w=="o"), [w for w in s[0:9]]))  # escaper_stones
    f += list(map(lambda w : float(w=="X" or w=="x"), [w for w in s[0:9]]))  # chaser_stones
    f += list(map(lambda w : float(w=="." or w=="x" or w=="o"), [w for w in s[0:9]]))  # empty
    if (len(s) >= 18):
        f += list(map(lambda w : float(not(w=="+")), [w for w in s[9:18]]))  # not_edge
    else:
        f += ZERO
    f += ZERO*(N_RESIDUAL_FILTERS-5)
    return f


RESIDUAL_FILTERS_A = ([]
    #"my_stones",
    #"opp_stones",
    # First ones just copy forward
    + ZERO*0 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(0+1)) # z=0 tomove
    + ZERO*1 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(1+1)) # z=1 escaper_stones
    + ZERO*2 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(2+1)) # z=2 chaser_stones
    + ZERO*3 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(3+1)) # z=3 empty
    + ZERO*4 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(4+1)) # z=4 not_edge
    # New
    + str2filter(PATTERNS["ladder_escape"])           # z=5
    + str2filter(PATTERNS["ladder_atari"])            # z=6
    + str2filter(PATTERNS["ladder_maker"])            # z=7
    + str2filter(PATTERNS["ladder_breaker"])          # z=8
    + str2filter(PATTERNS["ladder_continue"])         # z=9
    + ZERO*(N_RESIDUAL_FILTERS-10)*N_RESIDUAL_FILTERS
)
RESIDUAL_FILTERS_B = ([]
    #"my_stones",
    #"opp_stones",
    # Clear, skip connection will fill back in
    + ZERO*5*N_RESIDUAL_FILTERS
    # These are new in first layer, copy forward
    + ZERO*5 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(5+1)) # z=5
    + ZERO*6 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(6+1)) # z=6
    + ZERO*7 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(7+1)) # z=7
    + ZERO*8 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(8+1)) # z=8
    + ZERO*9 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-(9+1)) # z=9
    + ZERO*(N_RESIDUAL_FILTERS-10)*N_RESIDUAL_FILTERS
)
#print (len( ZERO*0), len(IDENTITY), len( ZERO*(N_RESIDUAL_FILTERS-1))) # tomove
#print(len(ZERO*0 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-1)))
#print(len(ZERO*1 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-2)))
#print(len(ZERO*2 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-3)))
#print(len(ZERO*3 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-4)))
#print(len(ZERO*4 + IDENTITY + ZERO*(N_RESIDUAL_FILTERS-5)))
#print(len(str2filter(PATTERNS["ladder_escape"])))
#print(len(str2filter(PATTERNS["ladder_atari"])))
#print(len(str2filter(PATTERNS["ladder_maker"])))
#print(len(str2filter(PATTERNS["ladder_breaker"])))
#print(len(str2filter(PATTERNS["ladder_continue"])))
#print(len(ZERO*(N_RESIDUAL_FILTERS-10)*N_RESIDUAL_FILTERS))
#sys.exit()
#
def ip_identity(rows, cols, filters):
    I = []
    for c in range(cols):
        for f in range(filters):
            for r in range(rows):
                if r and c and r == c:
                    I.append(1.1)
                else:
                    I.append(0.0)
    return I

def to_string(a):
    return " ".join(map(str, a))

def pretty_print(a):
    for f in [a[i:i+3*3] for i in range(0, len(a), 9)]:
        print(f)

def main():
    # Version
    print("1")

    # Input conv
    print(to_string(BOARD_FILTER))
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means    negative increases activations, positive decreases activations
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances

    # Residual layer
    print(to_string(RESIDUAL_FILTERS_A)) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances
    print(to_string(RESIDUAL_FILTERS_B)) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances

    # Policy
    print(to_string([1.0]*N_RESIDUAL_FILTERS*2))
    print(to_string([0.0]*2)) # conv_pol_b
    print(to_string([0.0]*2)) # bn_pol_w1
    print(to_string([1.0]*2)) # bn_pol_w2 -- variance
    print(to_string(ip_identity(361, 362, 2)))
    print(to_string([0.0]*362)) # ip_pol_b

    # Value
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # conv_val_w
    print(to_string([0.0])) # conv_val_b -- bias
    print(to_string([0.0])) # bn_val_w1 -- bias
    print(to_string([1.0])) # bn_val_w2 -- variance
    print(to_string([0.0]*1*361*256)) # ip1_val_w -- weight
    print(to_string([1.0]*256)) # ip1_val_b -- bias
    print(to_string([0.0]*1*256*1)) # ip2_val_w -- weight
    print(to_string([1.0]*1)) # ip_val_b -- bias


if __name__ == "__main__":
    main()
