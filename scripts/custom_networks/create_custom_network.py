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

#RESIDUAL_FILTERS = 128   !! these aren't correct...
#RESIDUAL_BLOCKS = 6
#RESIDUAL_FILTERS = 64
#RESIDUAL_BLOCKS = 5
RESIDUAL_FILTERS = 2
RESIDUAL_BLOCKS = 1
INPUT_PLANES = 18
HISTORY_PLANES = 8


IDENTITY = [0.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 0.0]
SUM = [0.3, 0.3, 0.3,
       0.3, 0.3, 0.3,
       0.3, 0.3, 0.3]
ZERO = [0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0]
BOARD_IDENTITY = ([]
    + SUM*1                        # Most recent opponent?
    + ZERO*(HISTORY_PLANES-1)
    + SUM*1                        # Most recent me?
    + ZERO*(HISTORY_PLANES-1)
    + ZERO                         # White/Black to move
    + ZERO)                        # White/Black to move

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
    for filter in [a[i:i+3*3] for i in range(0, len(a), 9)]:
        print(filter)

def main():
    # Version
    print("1")

    # Input conv
    print(to_string(BOARD_IDENTITY*RESIDUAL_FILTERS))
    print(to_string([0.0]*RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0, 0.0])) # batchnorm_means    negative increases activations, positive decreases activations
    print(to_string([0.5, 0.5])) # batchnorm_variances

    # Residual layer
    print(to_string(IDENTITY*RESIDUAL_FILTERS**2)) # conv_weights
    print(to_string([0.0]*RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([0.5]*RESIDUAL_FILTERS)) # batchnorm_variances
    print(to_string(IDENTITY*RESIDUAL_FILTERS**2)) # conv_weights
    print(to_string([0.0]*RESIDUAL_FILTERS)) # conv_biases
    print(to_string([0.0]*RESIDUAL_FILTERS)) # batchnorm_means
    print(to_string([0.5]*RESIDUAL_FILTERS)) # batchnorm_variances

    # Policy
    print(to_string([1.0]*RESIDUAL_FILTERS*2))
    print(to_string([0.0]*2)) # conv_pol_b
    print(to_string([0.0]*2)) # bn_pol_w1
    print(to_string([0.5]*2)) # bn_pol_w2 -- variance
    print(to_string(ip_identity(361, 362, 2)))
    print(to_string([0.0]*362)) # ip_pol_b

    # Value
    print(to_string([1.0]*RESIDUAL_FILTERS)) # conv_val_w
    print(to_string([0.0])) # conv_val_b -- bias
    print(to_string([0.0])) # bn_val_w1 -- bias
    print(to_string([0.5])) # bn_val_w2 -- variance
    print(to_string([0.0]*1*361*256)) # ip1_val_w -- weight
    print(to_string([1.0]*256)) # ip1_val_b -- bias
    print(to_string([0.0]*1*256*1)) # ip2_val_w -- weight
    print(to_string([1.0]*1)) # ip_val_b -- bias


if __name__ == "__main__":
    main()
