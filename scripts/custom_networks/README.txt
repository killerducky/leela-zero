training
91 hex nibbles = 16*361bits - history
0=black 1=white
362 policy priors
1=tomove_won, -1=tomove_lost

convolution weights = [output, input, filter_size, filter_size]
fully connected = [output, input]

version
    1
input
    10368  - conv_weights - 18*64*3*3 (18 input planes, 64 filters, 3x3)
    64     - conv_biases (all zeros)
    64     - batchnorm_means
    64     - batchnorm_variances
             (rectifier)
residual xN
    36864  - conv_weights - 64*64*3*3  (64 input planes, 64 filters, 3x3)
    64     - conv_biases (all zeros)
    64     - batchnorm_means
    64     - batchnorm_variances
             (rectifier)
    36864  - conv_weights - 64*64*3*3  (64 input planes, 64 filters, 3x3)
    64     - conv_biases (all zeros)
    64     - batchnorm_means
    64     - batchnorm_variances
             (skip connection)
             (rectifier)
policy
    128    - conv_pol_w weight    std::move  64*2*1*1 (64 input planes, 2 filters, 1x1)
    2      - conv_pol_b biases    std::move
    2      - bn_pol_w1 means?     std::copy (copy for arrays, move for vectors)
    2      - bn_pol_w2 variances? std::copy
             (rectifier)
    261364 - ip_pol_w innerproduct weight 2*361*362 (2 input planes, 361*362 IP)
    362    - ip_pol_b innerproduct biases
             (logit probabilities -- softmax?)
value
    64     - conv_val_w conv weight 64*1*1*1 (64 input planes, 1 filter, 1x1)
    1      - conv_val_b conv bias
    1      - bn_val_w1 means?
    1      - bn_val_w2 variances?
             (rectifier)
    92416  - ip1_val_w innerproduct weight 1*361*256 (1 input plane, 361*256 IP)
    256    - ip1_val_b innerproduct biases
             (rectifier)
    256    - ip2_val_w innerproduct weight 1*256*1 (1 input plane, 256*1 IP)
    1      - ip2_val_b innerproduct biases
             (tanh)


O to escape N
X..
OOX
OX.

X to atari N
...
XO.
OOX

X to atari
????....
???.XO..
?..XOOX.
?.XOOX.?
.XOOX.??
XOOX.???
XOX.????
?X??????

O to escape
????....
???.X...
??.XOOX.
?.XOOX.?
.XOOX.??
XOOX.???
XOX.????
?X??????



flood fill pseudo liberties
match ladder
diagonal search maker/breaker/edge

first conv:
identity on most recent my_color
   stones !to_move
    000     000
    010     010
    000     000
identity on most recent opp_color
   stones to_move
    000     000
    010     010
    000     000
O to escape N
    me    opp  empty  edge
    ---   1--  -11    000
    11-   --1  ---    000
    1--   -1-  --1    000
X to atari N
    me    opp  empty  edge
    ---   ---  111    000
    -1-   1--  --1    000
    11-   --1  --1    000
ladder maker
    me    opp  empty  edge
    111   ---  000    000
    111   ---  000    000
    111   ---  000    000
ladder breaker
    me    opp  empty  edge
    ---   111  000    111
    ---   111  000    111
    ---   111  000    111
ladder continue break
                          prev
    me   opp  empty edge  break
    ---  ---  111   ---   001
    ---  ---  111   ---   000
    ---  ---  111   ---   000
ladder continue make
                          prev
    me   opp  empty edge  make
    ---  ---  111   ---   001
    ---  ---  111   ---   000
    ---  ---  111   ---   000


BCCCCMCCCCCBCCCC
BBBBBMMMMMMBBBBB


OOOOOO..
OXXXOO..
OX.XXXXO
OXXXOOO.
OOOOO...

 010
 1.1001
 010


OOOOOO..
OOOOOO..
OOXXXXXO
O.XXOOO.
OOOOO...


  00001
  10

