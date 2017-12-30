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
import operator

# This controls how far the ladder reader can see
DYNAMIC_LAYERS = 20

INPUT_PLANES = 18
HISTORY_PLANES = 8
N_RESIDUAL_FILTERS = 64
N_BOARD_FILTERS  = 6
N_STATIC_RESIDUAL_FILTERS = 10
N_DYNAMIC_RESIDUAL_FILTERS = 17
N_UNUSED_RESIDUAL_FILTERS = N_RESIDUAL_FILTERS - N_BOARD_FILTERS - N_STATIC_RESIDUAL_FILTERS - N_DYNAMIC_RESIDUAL_FILTERS
assert(N_UNUSED_RESIDUAL_FILTERS >0)
N_STATIC_FILTERS = N_BOARD_FILTERS + N_STATIC_RESIDUAL_FILTERS
NORMALIZE_BIAS = 1.0

FILTERS = [
    # Static Board filters
    "black_tomove",     # z=0
    "white_tomove",     # z=1
    "my_stones",        # z=2  (O)
    "opp_stones",       # z=3  (X)
    "empty",            # z=4  (.)
    "not_edge",         # z=5

    # Static Patterns
    "ladder_escape",    # z=6
    "ladder_escape2",   # z=7
    "ladder_atari",     # z=8
    "ladder_atari2",    # z=9
    "ladder_o",         # z=10 (O)
    "ladder_x",         # z=11 (X)
    "ladder_continue",  # z=12 (.)
    "ladder_continue2", # z=13
    "ladder_continue3", # z=14
    "ladder_e",         # z=15 (+)

    # Dynamic patterns
    "ladder_e_found",      # z=16
    "ladder_x_found",      # z=17
    "ladder_o_found",      # z=18
    "prev_ladder_e_found", # z=19 -- used to subtract out skip layer
    "prev_ladder_x_found", # z=20 -- used to subtract out skip layer
    "prev_ladder_o_found", # z=21 -- used to subtract out skip layer
    "ladder_e_found_m1",   # z=22 -- used for normalizing
    "ladder_x_found_m1",   # z=23 -- used for normalizing
    "ladder_o_found_m1",   # z=24-- used for normalizing
    # The following act more like static patterns, but are calculated later
    "black_ladder_escape_move",  # z=25
    "black_ladder_atari_move",   # z=26
    "black_ladder_escape_fail",  # z=27
    "black_ladder_atari_fail",   # z=28
    "white_ladder_escape_move",  # z=29
    "white_ladder_atari_move",   # z=30
    "white_ladder_escape_fail",  # z=31
    "white_ladder_atari_fail",   # z=32
]

assert (len(FILTERS) == N_BOARD_FILTERS + N_STATIC_RESIDUAL_FILTERS + N_DYNAMIC_RESIDUAL_FILTERS)

# TODO: Make into 5x5 patterns for more context
# O = escaper's stones
# X = opp_stones's stones
# . = empty
# o = O or .
# x = X or .
# + = outside of board (only used in 2nd set of 3*3 strings)
# ? = wildcard -- match anything
# ! = anti-wildcard -- never match

# [bias, pattern_string]
# bias means must match more than that many points to activate
# The edge pattern (+) is inverted because it uses the not_edge plane.
# It produces -1.0 for each miss.
PATTERN_DICT = {
    "ladder_escape"  : [8, "X.." +
                           "OOX" +
                           "OX."],

    "ladder_escape2" : [8, ".X." +
                           "XO." +
                           "OOX"],

    "ladder_atari"   : [8, "..." +
                           "OX." +
                           "XXO"],

    "ladder_atari2"  : [8, "O.." +
                           "XX." +
                           "XO."],

    # For ladder_o and ladder_x, the ! in the lower left
    # are a trick to avoid matching when next to the ladder_atari
    # or ladder_escape pattern itself.
    # This doesn't break anything because they will all be picked
    # up as the pattern sweeps diagonally from NE to SW.
    "ladder_o"       : [0, "OOO" +
                           "!OO" +
                           "!!O"],

    "ladder_x"       : [0, "XXX" +
                           "!XX" +
                           "!!X"],

    # -9 bias because in the middle hit 9 not_edge, for -9 total
    "ladder_e"        : [-9, "+++" +
                             "+++" +
                             "+++"],

    "ladder_continue" : [8, "..." +
                            "..." +
                            "..."],

    "ladder_continue2": [8, "..." +
                            "..." +
                            "OX."],

    "ladder_continue3": [8, "..." +
                            "X.." +
                            "O.."],
}

# Simple filters
NOT_IDENTITY = [0.0, 0.0, 0.0,
                0.0, -1.0, 0.0,
                0.0, 0.0, 0.0]
IDENTITY = [0.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 0.0]
# TODO: The default rotation of these is upside down from that of the string patterns!
ID_NE     = [0.0, 0.0, 0.0,
             0.0, 0.0, 0.0,
             0.0, 0.0, 1.0]
NOT_ID_NE = [0.0, 0.0, 0.0,
             0.0, 0.0, 0.0,
             0.0, 0.0, -1.0]
ID_S      = [0.0, 1.0, 0.0,
             0.0, 0.0, 0.0,
             0.0, 0.0, 0.0]
NOT_ID_S  = [0.0, -1.0, 0.0,
             0.0, 0.0, 0.0,
             0.0, 0.0, 0.0]
ID_E      = [0.0, 0.0, 0.0,
             0.0, 0.0, 1.0,
             0.0, 0.0, 0.0]
NOT_ID_E  = [0.0, 0.0, 0.0,
             0.0, 0.0, -1.0,
             0.0, 0.0, 0.0]
ID_W      = [0.0, 0.0, 0.0,
             1.0, 0.0, 0.0,
             0.0, 0.0, 0.0]
SUM = [1.0, 1.0, 1.0,
       1.0, 1.0, 1.0,
       1.0, 1.0, 1.0]
ZERO = [0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0]

BOARD_FILTERS = {
    "black_tomove"  :  ([]
        + ZERO*1                       # Most recent me
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent opp
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY                     # Black to move
        + ZERO),                       # White to move
    "white_tomove"  :  ([]
        + ZERO*1                       # Most recent me
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent opp
        + ZERO*(HISTORY_PLANES-1)
        + ZERO                         # Black to move
        + IDENTITY),                   # White to move
    "my_stones" : ([]
        + IDENTITY*1                   # Most recent me
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent opp
        + ZERO*(HISTORY_PLANES-1)
        + ZERO                         # White/Black to move
        + ZERO),                       # White/Black to move
    "opp_stones" : ([]
        + ZERO*1                       # Most recent me
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY*1                   # Most recent opp
        + ZERO*(HISTORY_PLANES-1)
        + ZERO                         # White/Black to move
        + ZERO),                       # White/Black to move
    "empty" : ([]
        + NOT_IDENTITY*1               # Most recent me
        + ZERO*(HISTORY_PLANES-1)
        + NOT_IDENTITY*1               # Most recent opp
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY                     # White/Black to move  -- TODO: This plus next line is a quick and dirty way to add bias of 1.0
        + IDENTITY),                   # White/Black to move
    "not_edge" : ([]
        + ZERO*1                       # Most recent me
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent opp
        + ZERO*(HISTORY_PLANES-1)
        + IDENTITY                     # White/Black to move
        + IDENTITY),                   # White/Black to move
    "init_to_zero" : ([]
        + ZERO*1                       # Most recent me
        + ZERO*(HISTORY_PLANES-1)
        + ZERO*1                       # Most recent opp
        + ZERO*(HISTORY_PLANES-1)
        + ZERO                         # White/Black to move
        + ZERO),                       # White/Black to move
}

BOARD_FILTER = ([]
    + BOARD_FILTERS["black_tomove"]
    + BOARD_FILTERS["white_tomove"]
    + BOARD_FILTERS["my_stones"]
    + BOARD_FILTERS["opp_stones"]
    + BOARD_FILTERS["empty"]
    + BOARD_FILTERS["not_edge"]
    + BOARD_FILTERS["init_to_zero"]*(N_RESIDUAL_FILTERS-N_BOARD_FILTERS)
)

# TODO: Make a loop for this instead of this hardcoded thing
def str2filter(s):
    f = str2filter_9x9(s[0:9])
    if len(s)==9:
        pass
    elif len(s)==18:
        f = sum_filters([f, str2filter_9x9(s[9:18])])
    else:
        raise
    return f

def str2filter_9x9(s):
    # TODO: Support all rotations. For now match rotation of "heatmap 0"
    s = s[6:9]+s[3:6]+s[0:3]
    f = []
    f += ZERO # black_tomove
    f += ZERO # white_tomove
    f += list(map(lambda w : float(w=="?" or w=="O" or w=="o"), [w for w in s[0:9]]))  # my_stones
    f += list(map(lambda w : float(w=="?" or w=="X" or w=="x"), [w for w in s[0:9]]))  # opp_stones
    f += list(map(lambda w : float(w=="?" or w=="." or w=="x" or w=="o"), [w for w in s[0:9]]))  # empty
    f += list(map(lambda w : (0.0, -1.0)[w=="?" or w=="+"], [w for w in s[0:9]]))  # not_edge
    f += ZERO*(N_RESIDUAL_FILTERS-N_BOARD_FILTERS)
    return f

def forward_filter(r, direction=IDENTITY, multiplier=1):
    if type(r) is int: r = [r]
    if multiplier != 1:
        direction = list(x*multiplier for x in direction)
        assert 1   # Not used for now
    f = []
    for num in r:
        f += ZERO*num + direction + ZERO*(N_RESIDUAL_FILTERS-(num+1))
    return f

# This is weird because the meaning of the range input 'r' is
# slightly different from the forward_filter version.
def filter_1x1(r, direction):
    if type(r) is int: r = [r]
    f = [0.0]*N_RESIDUAL_FILTERS
    for num in r:
        f[num] = direction[0]
    return f

# TODO: There must be some way to do this directly
# with map/operator.sum but I couldn't get it to work.
def sum_filters(filters):
    f_total = ZERO*N_RESIDUAL_FILTERS
    for f in filters:
        f_total = list(map(operator.add, f_total, f))
    return f_total

def ip_identity(inputs, inchannels, outputs):
    I = []
    for onum in range(outputs):
        for chnum in range(inchannels):
            for inum in range(inputs):
                if inum == onum:
                    if chnum == 0:
                        I.append(1.0)
                    else:
                        I.append(-1.0)
                else:
                    I.append(0.0)
    return I

def to_string(a):
    return " ".join(map(str, a))

def pretty_print(a):
    it = iter(a)
    while (1):
        f = [x for x in itertools.islice(it, 9)]
        if not f: break
        for e in f:
            print(e, end=" ")
        print()
    #for f in [a[i:i+3*3] for i in range(0, len(a), 9)]:
    #    print(f)

def relu(x):
    if x<0: return 0
    return x

# Example step function using 3 relus in 2 layers
def normalize_test():
    for i in range(5):
        o1a = relu(i)
        o1b = relu(i-NORMALIZE_BIAS)
        o2 = relu(o1a-o1b)
        print(i, o1a, o1b, o2)
    sys.exit()

# Add the layers that propogate the dynamic features
def addDynamicLayer(RESIDUAL_FILTERS):
    # LCCCOCCCXCCCE
    # LCCOOCCXXCCEE
    # LCOOOCXXXCEEE
    # LOOOOXXXXEEEE
    # LOOOOXXXXEEEE
    # LOOOOXXXXEEEE
    #
    # e_found = e || ((continue || continue2) & nw(e_found)
    # x_found = x || ((continue || continue2) & nw(x_found)
    # o_found = o || ((continue || continue2) & nw(o_found)
    ladder_e_found = sum_filters([
        forward_filter(FILTERS.index("ladder_e")),
        forward_filter(FILTERS.index("ladder_e")),
        forward_filter(FILTERS.index("ladder_continue")),
        forward_filter(FILTERS.index("ladder_continue2")),
        forward_filter(FILTERS.index("ladder_continue3")),
        forward_filter(FILTERS.index("ladder_e_found"), ID_NE),
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    ladder_x_found = sum_filters([
        forward_filter(FILTERS.index("ladder_x")),
        forward_filter(FILTERS.index("ladder_x")),
        forward_filter(FILTERS.index("ladder_continue")),
        forward_filter(FILTERS.index("ladder_continue2")),
        forward_filter(FILTERS.index("ladder_continue3")),
        forward_filter(FILTERS.index("ladder_x_found"), ID_NE),
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    ladder_o_found = sum_filters([
        forward_filter(FILTERS.index("ladder_o")),
        forward_filter(FILTERS.index("ladder_o")),
        forward_filter(FILTERS.index("ladder_continue")),
        forward_filter(FILTERS.index("ladder_continue2")),
        forward_filter(FILTERS.index("ladder_continue3")),
        forward_filter(FILTERS.index("ladder_o_found"), ID_NE),
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    ladder_e_found_m1 = sum_filters([
        ladder_e_found,
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    ladder_x_found_m1 = sum_filters([
        ladder_x_found,
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    ladder_o_found_m1 = sum_filters([
        ladder_o_found,
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    RESIDUAL_FILTERS.append([]
        + forward_filter(range(0,N_STATIC_FILTERS))
        + ladder_e_found
        + ladder_x_found
        + ladder_o_found
        + forward_filter(FILTERS.index("ladder_e_found")) # prev_ladder_e_found
        + forward_filter(FILTERS.index("ladder_x_found")) # prev_ladder_x_found
        + forward_filter(FILTERS.index("ladder_o_found")) # prev_ladder_o_found
        + ladder_e_found_m1
        + ladder_x_found_m1
        + ladder_o_found_m1
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_escape_move
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_atari_move
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_escape_fail
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_atari_fail
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_escape_move
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_atari_move
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_escape_fail
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_atari_fail
        + ZERO*N_RESIDUAL_FILTERS*(N_RESIDUAL_FILTERS-N_STATIC_FILTERS-N_DYNAMIC_RESIDUAL_FILTERS)
    )
    # Normalize
    RESIDUAL_FILTERS.append([]
        + ZERO*N_RESIDUAL_FILTERS*N_STATIC_FILTERS
        + sum_filters([
            forward_filter(FILTERS.index("ladder_e_found")),
            forward_filter(FILTERS.index("ladder_e_found_m1"), NOT_IDENTITY), # normalize
            forward_filter(FILTERS.index("prev_ladder_e_found"), NOT_IDENTITY)]) # cancel skip connection
        + sum_filters([
            forward_filter(FILTERS.index("ladder_x_found")),
            forward_filter(FILTERS.index("ladder_x_found_m1"), NOT_IDENTITY), # normalize
            forward_filter(FILTERS.index("prev_ladder_x_found"), NOT_IDENTITY)]) # cancel skip connection
        + sum_filters([
            forward_filter(FILTERS.index("ladder_o_found")),
            forward_filter(FILTERS.index("ladder_o_found_m1"), NOT_IDENTITY), # normalize
            forward_filter(FILTERS.index("prev_ladder_o_found"), NOT_IDENTITY)]) # cancel skip connection
        + ZERO*N_RESIDUAL_FILTERS # prev_ladder_e_found
        + ZERO*N_RESIDUAL_FILTERS # prev_ladder_x_found
        + ZERO*N_RESIDUAL_FILTERS # prev_ladder_o_found
        + ZERO*N_RESIDUAL_FILTERS # prev_ladder_e_found_m1
        + ZERO*N_RESIDUAL_FILTERS # prev_ladder_x_found_m1
        + ZERO*N_RESIDUAL_FILTERS # prev_ladder_o_found_m1
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_escape_move
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_atari_move
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_escape_fail
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_atari_fail
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_escape_move
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_atari_move
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_escape_fail
        + ZERO*N_RESIDUAL_FILTERS # white_ladder_atari_fail
        + ZERO*N_RESIDUAL_FILTERS*(N_RESIDUAL_FILTERS-N_STATIC_FILTERS-N_DYNAMIC_RESIDUAL_FILTERS)
    )


def buildResidualFilters():
    RESIDUAL_FILTERS = []
    RESIDUAL_FILTERS.append([]
        # First ones just copy forward
        + forward_filter(range(0,N_BOARD_FILTERS))
        # New
        + str2filter(PATTERN_DICT[FILTERS[6]][1])   # ladder_escape      # z=6
        + str2filter(PATTERN_DICT[FILTERS[7]][1])   # ladder_escape2     # z=7
        + str2filter(PATTERN_DICT[FILTERS[8]][1])   # ladder_atari       # z=8
        + str2filter(PATTERN_DICT[FILTERS[9]][1])   # ladder_atari2      # z=9
        + str2filter(PATTERN_DICT[FILTERS[10]][1])  # ladder_o           # z=10 (O)
        + str2filter(PATTERN_DICT[FILTERS[11]][1])  # ladder_x           # z=11 (X)
        + str2filter(PATTERN_DICT[FILTERS[12]][1])  # ladder_continue    # z=12 (.)
        + str2filter(PATTERN_DICT[FILTERS[13]][1])  # ladder_continue2   # z=13
        + str2filter(PATTERN_DICT[FILTERS[14]][1])  # ladder_continue3   # z=14
        + str2filter(PATTERN_DICT[FILTERS[15]][1])  # ladder_e           # z=15 (+)
        + ZERO*(N_RESIDUAL_FILTERS-N_STATIC_FILTERS)*N_RESIDUAL_FILTERS
    )
    RESIDUAL_FILTERS.append([]
        # Clear, skip connection will fill back in
        + ZERO*N_BOARD_FILTERS*N_RESIDUAL_FILTERS
        # These are new in first layer, copy forward
        + forward_filter(range(N_BOARD_FILTERS,N_STATIC_FILTERS))
        + ZERO*(N_RESIDUAL_FILTERS-N_STATIC_FILTERS)*N_RESIDUAL_FILTERS
    )

    # Use this layer to normalize outputs to 1 or 0
    RESIDUAL_FILTERS.append([]
        + forward_filter(range(0,N_RESIDUAL_FILTERS))
    )
    RESIDUAL_FILTERS.append([]
        + forward_filter(range(0,N_RESIDUAL_FILTERS), NOT_IDENTITY)
    )

    for i in range(DYNAMIC_LAYERS):
        addDynamicLayer(RESIDUAL_FILTERS)

    # Use this layer to normalize outputs to 1 or 0
    RESIDUAL_FILTERS.append([]
       + forward_filter(range(0,N_RESIDUAL_FILTERS))
    )
    RESIDUAL_FILTERS.append([]
        + forward_filter(range(0,N_RESIDUAL_FILTERS), NOT_IDENTITY)
    )

    # Add some last minute things
    RESIDUAL_FILTERS.append([]
       + forward_filter(range(0,N_RESIDUAL_FILTERS))
    )
    ladder_escape_fail = sum_filters([
        forward_filter(FILTERS.index("ladder_escape"), ID_S),
        forward_filter(FILTERS.index("ladder_escape2"), ID_W),
        forward_filter(FILTERS.index("ladder_e_found"), ID_NE),
        forward_filter(FILTERS.index("ladder_x_found"), ID_NE),
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    ladder_atari_fail = sum_filters([
        forward_filter(FILTERS.index("ladder_atari"), ID_S),
        forward_filter(FILTERS.index("ladder_atari2"), ID_W),
        forward_filter(FILTERS.index("ladder_x_found"), ID_NE),
        forward_filter(FILTERS.index("not_edge"), NOT_IDENTITY)])  # bias
    RESIDUAL_FILTERS.append([]
        + forward_filter(range(0,FILTERS.index("black_ladder_escape_move")), ZERO)
        + sum_filters([ # black_ladder_escape_move
            forward_filter(FILTERS.index("ladder_escape"), ID_S),
            forward_filter(FILTERS.index("ladder_escape2"), ID_W),
            forward_filter(FILTERS.index("white_tomove"), NOT_IDENTITY)])
        + sum_filters([ # black_ladder_atari_move
            forward_filter(FILTERS.index("ladder_atari"), ID_S),
            forward_filter(FILTERS.index("ladder_atari2"), ID_W),
            forward_filter(FILTERS.index("white_tomove"), NOT_IDENTITY)])
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_escape_fail
        + ZERO*N_RESIDUAL_FILTERS # black_ladder_atari_fail
        + sum_filters([ # white_ladder_escape_move
            forward_filter(FILTERS.index("ladder_escape"), ID_S),
            forward_filter(FILTERS.index("ladder_escape2"), ID_W),
            forward_filter(FILTERS.index("black_tomove"), NOT_IDENTITY)])
        + sum_filters([ # white_ladder_atari_move
            forward_filter(FILTERS.index("ladder_atari"), ID_S),
            forward_filter(FILTERS.index("ladder_atari2"), ID_W),
            forward_filter(FILTERS.index("black_tomove"), NOT_IDENTITY)])
        + sum_filters([ # white_ladder_escape_fail
            ladder_escape_fail,
            forward_filter(FILTERS.index("black_tomove"), NOT_IDENTITY)])
        + sum_filters([ # white_ladder_atari_fail
            ladder_atari_fail,
            forward_filter(FILTERS.index("black_tomove"), NOT_IDENTITY)])
        + forward_filter(range(FILTERS.index("white_ladder_atari_fail")+1,N_RESIDUAL_FILTERS), ZERO)
    )
    return RESIDUAL_FILTERS


def dump_patterns():
    print(PATTERN_DICT["ladder_continue"][1])
    print(str2filter(PATTERN_DICT["ladder_continue"][1]))
    pretty_print(str2filter(PATTERN_DICT["ladder_continue"][1]))
    print(PATTERN_DICT["ladder_continue2"][1])
    print(str2filter(PATTERN_DICT["ladder_continue2"][1]))
    pretty_print(str2filter(PATTERN_DICT["ladder_continue2"][1]))
    sys.exit()

def main():
    RESIDUAL_FILTERS = buildResidualFilters()
    #normalize_test()
    #dump_patterns()

    print("1")

    # Input conv
    print(to_string(BOARD_FILTER))
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means    negative increases activations, positive decreases activations
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances


    r_layer = -1

    # Residual layer
    r_layer += 1
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    # TODO: Generalize. For now special case only ladder_continue bias
    print(to_string([0.0]*N_BOARD_FILTERS
           + [PATTERN_DICT[FILTERS[6]][0]]  # batchnorm_means # ladder_escape      # z=6
           + [PATTERN_DICT[FILTERS[7]][0]]  # batchnorm_means # ladder_escape2     # z=7
           + [PATTERN_DICT[FILTERS[8]][0]]  # batchnorm_means # ladder_atari       # z=8
           + [PATTERN_DICT[FILTERS[9]][0]]  # batchnorm_means # ladder_atari2      # z=9
           + [PATTERN_DICT[FILTERS[10]][0]] # batchnorm_means # ladder_o           # z=10 (O)
           + [PATTERN_DICT[FILTERS[11]][0]] # batchnorm_means # ladder_x           # z=11 (X)
           + [PATTERN_DICT[FILTERS[12]][0]] # batchnorm_means # ladder_continue    # z=12 (.)
           + [PATTERN_DICT[FILTERS[13]][0]] # batchnorm_means # ladder_continue2   # z=13
           + [PATTERN_DICT[FILTERS[14]][0]] # batchnorm_means # ladder_continue3   # z=14
           + [PATTERN_DICT[FILTERS[15]][0]] # batchnorm_means # ladder_e           # z=15 (+)
           + [0.0]*(N_RESIDUAL_FILTERS-N_STATIC_FILTERS))) # batchnorm_means
    r_layer += 1
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances

    # Normalize layer
    r_layer += 1
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([NORMALIZE_BIAS]*N_RESIDUAL_FILTERS)) # batchnorm_means <-- normalizing offset
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances
    r_layer += 1
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances

    for _ in range(DYNAMIC_LAYERS):
        r_layer += 1
        print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
        print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
        print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
        print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances
        r_layer += 1
        print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
        print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
        print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
        print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances

    # Normalize layer
    r_layer += 1
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([NORMALIZE_BIAS]*N_RESIDUAL_FILTERS)) # batchnorm_means <-- normalizing offset
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances
    r_layer += 1
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances

    # Last minute layer
    r_layer += 1
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances
    r_layer += 1
    print(to_string(RESIDUAL_FILTERS[r_layer])) # conv_weights
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*N_RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([1.0]*N_RESIDUAL_FILTERS)) # batchnorm_variances

    assert(r_layer+1==len(RESIDUAL_FILTERS))

    # Policy
    # policy0 contains good features, ip_identity multiplies them by 1.0
    # General bonus for continuing all ladders
    policy0 = [0.0]*N_RESIDUAL_FILTERS
    policy0[FILTERS.index("black_ladder_escape_move")] = 8.0
    policy0[FILTERS.index("black_ladder_atari_move")] = 8.0
    policy0[FILTERS.index("white_ladder_escape_move")] = 8.0
    policy0[FILTERS.index("white_ladder_atari_move")] = 8.0
    # policy1 contains bad features, ip_identity multiplies them by -1.0
    # Penalty for continuing ladders that fail
    policy1 = [0.0]*N_RESIDUAL_FILTERS
    policy1[FILTERS.index("black_ladder_escape_fail")] = 16.0
    policy1[FILTERS.index("black_ladder_atari_fail")] = 16.0
    policy1[FILTERS.index("white_ladder_escape_fail")] = 16.0
    policy1[FILTERS.index("white_ladder_atari_fail")] = 16.0
    print(to_string(policy0 + policy1))
    print(to_string([0.0]*2)) # conv_pol_b
    print(to_string([0.0]*2)) # bn_pol_w1
    print(to_string([1.0]*2)) # bn_pol_w2 -- variance
    print(to_string(ip_identity(361, 2, 362)))
    print(to_string([0.0]*362)) # ip_pol_b

    # Value
    value0 = [0.0]*N_RESIDUAL_FILTERS
    value0[FILTERS.index("black_ladder_escape_move")] =  0.2
    value0[FILTERS.index("black_ladder_atari_move")]  =  0.2
    value0[FILTERS.index("black_ladder_escape_fail")] = -1.0
    value0[FILTERS.index("black_ladder_atari_fail")]  = -1.0
    value0[FILTERS.index("white_ladder_escape_move")] = -0.2
    value0[FILTERS.index("white_ladder_atari_move")]  = -0.2
    value0[FILTERS.index("white_ladder_escape_fail")] =  1.0
    value0[FILTERS.index("white_ladder_atari_fail")]  =  1.0
    print(to_string(value0)) # conv_val_w
    print(to_string([0.0])) # conv_val_b -- bias
    print(to_string([-10.0])) # bn_val_w1 -- bias  <<<< all 361 will have +10 so don't lose negative numbers in the relu
    print(to_string([1.0])) # bn_val_w2 -- variance
    # (relu here)
    print(to_string([1.0]*1*361*256)) # ip1_val_w -- weight
    print(to_string([0.0]*256)) # ip1_val_b -- bias
    # (relu here)
    ip_val_w = [0.0]*1*256*1
    ip_val_w[0] = 1.0 # Just take one copy, they're all identical
    print(to_string(ip_val_w)) # ip2_val_w -- weight
    print(to_string([-361.0*10.0]*1)) # ip_val_b -- bias  <<<< subtract out all 361*10


if __name__ == "__main__":
    main()
