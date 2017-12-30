# The Ladder Detector

This is a proof of concept for a ladder detector in the
Alpha Go Zero network architecture. I created custom
patterns that match ladders, and scan the board diagonally
to see if the ladder will work. Finally the
policy and value heads gather the result and output
if the ladder should be played, and a value.

The policy prior for escaping when it works, or playing
atari when it works is high. If network cannot look far
enough to determine the ladder, then policy prior for both
escaping *and* playing atari is high, to encourage the
search to expand this path and read it.

The value is high for the side that has a good ladder.
When the ladder is unknown, both sides get high values,
again to encourage the search to read the ladder.

## Take this board example:

       a b c d e f g h j k l m n o p q r s t
    19 . . . . . . . . . . . . . . . . . . . 19
    18 . . . . . . . . . . . . . . . . . . . 18
    17 . . . . . . . . . . . . . . . . . . . 17
    16 . . . + . . . . . + . . . X . + . . . 16
    15 . . . . . . . . . . . . . . . . . . . 15
    14 . . . . . . . . . . . . . . . . . . . 14
    13 . . . . . . . . . . . . . . . . . . . 13
    12 . . . . . . . . . . . . . . . . . . . 12
    11 . . . . . . . . . . . . . . . . . . . 11
    10 . . . + . . . O . + . . . . . + . . . 10
     9 . . . . . . . . . . . . . . . . . . .  9
     8 . . . . . . . . . . . . . . . . . . .  8
     7 . . . X . . . . . . . . . . . . . . .  7
     6 . . X O O(X). . . . . . . . . . . . .  6
     5 . . X O X . . . . . . . . . . . . . .  5
     4 . . O X . . . . . + . . . . . + . . .  4
     3 . . O . . . . . . . . . . . . . . . .  3
     2 . . . . . . . . . . . . . . . . . . .  2
     1 . . . . . . . . . . . . . . . . . . .  1
       a b c d e f g h j k l m n o p q r s t

- O is always the player to move.
- X is the opponent.

## Static features:
       a b c d e f g h j k l m n o p q r s t
    19 e e e e e e e e e e e e e e e e e e e 19
    18 e                                   e 18
    17 e                       x x x       e 17
    16 e     +           +       X x +     e 16
    15 e                           x       e 15
    14 e                                   e 14
    13 e                                   e 13
    12 e                                   e 12
    11 e           o o o                   e 11
    10 e     +       O o +           +     e 10
     9 e               o                   e  9
     8 e                                   e  8
     7 e     X L                           e  7
     6 e   X O O X                         e  6
     5 e   X O X                           e  5
     4 e   O X           +           +     e  4
     3 e   O                               e  3
     2 e                                   e  2
     1 e e e e e e e e e e e e e e e e e e e  1
       a b c d e f g h j k l m n o p q r s t

- e = edge of the board
- o = friendly stones of the side to move
- L = ladder escape or ladder atari position

## Dynamic features after one step:
       a b c d e f g h j k l m n o p q r s t
    19 e e e e e e e e e e e e e e e e e e e 19
    18 e e e e e e e e e e e e e e e e e e e 18
    17 e                       x x x     e e 17
    16 e     +           +   x x X x +   e e 16
    15 e                       x x x     e e 15
    14 e                         x       e e 14
    13 e                                 e e 13
    12 e                                 e e 12
    11 e           o o o                 e e 11
    10 e     +   o o O o +           +   e e 10
     9 e           o o o                 e e  9
     8 e             o                   e e  8
     7 e     X L                         e e  7
     6 e   X O O X                       e e  6
     5 e x X O X                         e e  5
     4 e x O X           +           +   e e  4
     3 e o O                             e e  3
     2 e o                               e e  2
     1 e e e e e e e e e e e e e e e e e e e  1
       a b c d e f g h j k l m n o p q r s t

e, o, and x features are propogated to the southeast
one space diagonally every step. Intersections can have
more than one feature (both x and e, or both o and e).
But some features block others (o blocks x, and vice-versa).
The most relevant feature is shown above for clarity.

## Dynamic features after three steps:
       a b c d e f g h j k l m n o p q r s t
    19 e e e e e e e e e e e e e e e e e e e 19
    18 e e e e e e e e e e e e e e e e e e e 18
    17 e e e e e e e e e e e e x x x e e e e 17
    16 e e e e e e e e e e e x x X x e e e e 16
    15 e e e e e e e e e e x x x x x e e e e 15
    14 e                 x x x x x e e e e e 14
    13 e                   x x x   e e e e e 13
    12 e                     x     e e e e e 12
    11 e           o o o           e e e e e 11
    10 e     +   o o O o +         e e e e e 10
     9 e       o o o o o           e e e e e  9
     8 e     o o o o o             e e e e e  8
     7 e     X L o o               e e e e e  7
     6 e   X O O X                 e e e e e  6
     5 e x X O X                   e e e e e  5
     4 e x O X           +         e e e e e  4
     3 e o O                       e e e e e  3
     2 e o                         e e e e e  2
     1 e e e e e e e e e e e e e e e e e e e  1
       a b c d e f g h j k l m n o p q r s t

In the final layers, another filter determines if a potential
ladder escape is next to:
- o (good)
- e (bad)
- x (bad)
- . (unknown -- haven't read far enough)
Or if a potential ladder atari is next to:
- o (good)
- e (good - note this is opposite of the escape case)
- x (bad)
- . (unknown -- haven't read far enough)

The policy and value heads are calculated accordingly.

In this example, the networks determines the ladder does not work, so
it outputs a low value on the policy prior for that move, and gives
a winrate of 83% black to win.

On the next move, it gives a 89% chance that black should atari the
ladder stones. It gives black a 59% chance to win (I'm not quite sure
why it's not the same winrate as the previous move, something to look
into later).

## Creating the network
Get this branch, go to the scripts/custom_networks directory, and run:

    ./create_custom_network.py > ladder.txt

Then you can run some examples:

    ./test.py

And look at the *.log file outputs. You can also change how far the
network sees by modifying `DYNAMIC_LAYERS=20`

## Caveats:
- Only works on ladders going to the northeast.
- Does not count liberties. Any ladder shape is assumed to be in atari!
- Only looks at a 3x3 area on the diagonal. Ladder breakers/makers
  outside that will be overlooked.
- Doesn't attempt to read what happens if there are multiple stones
  of both colors in one area.
- Current implementation is wasteful on both filters and blocks.
    - Uses an entire residual block to take one diagonal step.
      Each residual block has two layers, so it's possible to use half
      as many layers as I currently do.
    - Uses 33 filters. This could probably be compressed, but also need
      more if you want to support all four diagonals.
- I disabled rotations in the LZ code. Be careful not to merge this back into master/next.

## FAQ:
### I heard it's theoretically possible a single fully connected layer to learn arbitraty functions, including ladders.

Yes but you need a really big FC layer to do that. Also I believe it's easier
to train deeper networks instead of wider ones
(the buzzword is Deep neural networks, not wide neural networks).
See also RavnaBergsndot's and zebub9's comments here [Reddit on ladders](https://www.reddit.com/r/cbaduk/comments/7mud9z/is_it_theoretically_possible_for_leela_zero_to)

### Can this be integrated into the existing Leela weights?

I think it's possible, but for now I will work on other projects.

