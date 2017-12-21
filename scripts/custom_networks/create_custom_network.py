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


#RESIDUAL_FILTERS = 128   !! these aren't correct...
#RESIDUAL_BLOCKS = 6
#RESIDUAL_FILTERS = 64
#RESIDUAL_BLOCKS = 5
RESIDUAL_FILTERS = 2
RESIDUAL_BLOCKS = 1
INPUT_PLANES = 18

IDENTITY = "0.1 0.1 0.1 0.1 0.9 0.1 0.1 0.1 0.1"
SUM = "0.9 0.9 0.9 0.9 0.9 0.9 0.9 0.9 0.9"

# Version
print("1")

# Input conv
print((IDENTITY+" ")*INPUT_PLANES*RESIDUAL_FILTERS)
print("0.1 "*RESIDUAL_FILTERS) # conv_biases
print("0.1 "*RESIDUAL_FILTERS) # batchnorm_means
print("0.1 "*RESIDUAL_FILTERS) # batchnorm_variances

# Residual layer
print((IDENTITY+" ")*RESIDUAL_FILTERS**2) # conv_weights
print("0.1 "*RESIDUAL_FILTERS) # conv_biases
print("0.1 "*RESIDUAL_FILTERS) # batchnorm_means
print("0.1 "*RESIDUAL_FILTERS) # batchnorm_variances
print((IDENTITY+" ")*RESIDUAL_FILTERS**2)
print("0.1 "*RESIDUAL_FILTERS) # conv_biases
print("0.1 "*RESIDUAL_FILTERS) # batchnorm_means
print("0.1 "*RESIDUAL_FILTERS) # batchnorm_variances

# Policy
print("0.9 "*RESIDUAL_FILTERS*2)
print("0.9 "*2) # conv_pol_b
print("0.1 "*2) # bn_pol_w1
print("0.1 "*2) # bn_pol_w2
print("0.9 "*361*362*2) # ip_pol_w
print("0.1 "*362) # ip_pol_b

# Value
print("0.9 "*RESIDUAL_FILTERS) # conv_val_w
print("0.1") # conv_val_b
print("0.1") # bn_val_w1
print("0.1") # bn_val_w2
print("0.9 "*1*361*256) # ip1_val_w
print("0.1 "*256) # ip1_val_b
print("0.9 "*1*256*1) # ip2_val_w
print("0.1"*1) # ip_val_b

