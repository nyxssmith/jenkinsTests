#
# abstuple.py
#
# Copyright © 2008-2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by abs() on NewColl objects.
"""

# -----------------------------------------------------------------------------

#
# Functions
#

def absOp(t):
    """
    Given a (start, stop, skip, phase) tuple, returns a generator over tuples
    of the same shape representing the absolute value of the input tuple.
    
    *** Open on both ends ***
    >>> list(absOp((None, None, 7, 2)))
    [(2, None, 7, 2), (5, None, 7, 5)]
    >>> list(absOp((None, None, 6, 3)))
    [(3, None, 6, 3)]
    
    *** Open on the left ***
    >>> list(absOp((None, -31, 4, 1)))
    [(35, None, 4, 3)]
    >>> list(absOp((None, 19, 7, 5)))
    [(5, 19, 7, 5), (2, None, 7, 2)]
    >>> list(absOp((None, 3, 3, 0)))
    [(0, 3, 3, 0), (3, None, 3, 0)]
    
    *** Open on the right ***
    >>> list(absOp((1, None, 8, 1)))
    [(1, None, 8, 1)]
    >>> list(absOp((-19, None, 4, 1)))
    [(1, None, 4, 1), (3, 23, 4, 3)]
    >>> list(absOp((-21, None, 6, 3)))
    [(3, None, 6, 3)]
    
    *** Closed on both ends ***
    >>> list(absOp((4, 104, 25, 4)))
    [(4, 104, 25, 4)]
    >>> list(absOp((-126, 2, 16, 2)))
    [(14, 142, 16, 14)]
    >>> list(absOp((-126, 162, 16, 2)))
    [(14, 142, 16, 14), (2, 162, 16, 2)]
    >>> list(absOp((-26, 26, 4, 2)))
    [(2, 30, 4, 2)]
    >>> list(absOp((-99, -79, 5, 1)))
    [(84, 104, 5, 4)]
    """
    
    start, stop, skip, phase = t
    
    if start is None and stop is None:
        yield (phase, None, skip, phase)
        
        if phase and (skip != 2 * phase):
            n = skip - phase
            yield (n, None, skip, n)
    
    elif start is None:
        lastVal = stop - skip
        
        if lastVal < 0:
            n = -lastVal
            yield (n, None, skip, n % skip)
        else:
            yield (phase, stop, skip, phase)
            n = skip - phase
            yield (n, None, skip, n % skip)
    
    elif stop is None:
        if start >= 0:
            yield t
        else:
            yield (phase, None, skip, phase)
            
            if skip != 2 * phase:
                n = skip - phase
                yield (n, skip - start, skip, n % skip)
    
    elif start >= 0:
        yield t
    
    elif stop < skip:
        n = skip - stop
        yield (n, skip - start, skip, n % skip)
    
    elif skip == 2 * phase:
        yield (phase, max(skip - start, stop), skip, phase)
    
    else:
        n = skip - phase
        yield (n, skip - start, skip, n % skip)
        yield (phase, stop, skip, phase)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

