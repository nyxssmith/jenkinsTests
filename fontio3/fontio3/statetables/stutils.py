#
# stutils.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utilities for state table processing.
"""

# System imports
import logging
import operator

# -----------------------------------------------------------------------------

#
# Functions
#

def isValid(stateArray, **kwArgs):
    """
    Utility function to do general, overall validation of a state array. This
    function checks things like: fixed states are present; fixed classes are
    present; all state rows have the same set of keys; and so on. True is
    returned if the state array passes all the tests, and False otherwise; note
    this isn't really a final answer on its validity, since the various
    analyses may reveal other kinds of structural problems.
    
    The following keyword arguments are used:
    
        logger      A logger to which messages will be posted.
    
    >>> logger = utilities.makeDoctestLogger("isValid")
    >>> d = {}
    >>> isValid(d, logger=logger)
    isValid - ERROR - One or more of the fixed states are not present in the state array.
    False
    
    >>> d["Start of text"] = {}
    >>> d["Start of line"] = {}
    >>> isValid(d, logger=logger)
    isValid - ERROR - One or more of the fixed classes are not present in one or more rows of the state array.
    False
    
    >>> d["Start of text"] = {
    ...     "End of text": _FakeEntry("Start of text"),
    ...     "Out of bounds": _FakeEntry("Start of text"),
    ...     "Deleted glyph": _FakeEntry("Start of text"),
    ...     "Letter": _FakeEntry("Saw letter")}
    >>> d["Start of line"] = {
    ...     "End of text": _FakeEntry("Start of text"),
    ...     "Out of bounds": None,
    ...     "Deleted glyph": _FakeEntry("Start of text"),
    ...     "End of line": _FakeEntry("Start of text"),
    ...     "Letter": _FakeEntry("Saw letter")}
    >>> isValid(d, logger=logger)
    isValid - ERROR - The class labels across two or more rows of the state array are not the same. All rows must have the same set of class names.
    False
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    r = True
    
    if any(k not in stateArray for k in ("Start of text", "Start of line")):
        logger.error((
          'V0883',
          (),
          "One or more of the fixed states are not "
          "present in the state array."))
        
        r = False
    
    keySets = {frozenset(row) for row in stateArray.values()}
    
    if len(keySets) > 1:
        logger.error((
          'V0884',
          (),
          "The class labels across two or more rows of the state array are "
          "not the same. All rows must have the same set of class names."))
        
        r = False
    
    if not (keySets and r):
        return False
    
    presentStates = frozenset(stateArray)
    presentClasses = keySets.pop()
    fixed = ("End of text", "Out of bounds", "Deleted glyph", "End of line")
    
    if any(k not in presentClasses for k in fixed):
        logger.error((
          'V0885',
          (),
          "One or more of the fixed classes are not present in one or "
          "more rows of the state array."))
        
        r = False
    
    for stateName in sorted(stateArray):
        row = stateArray[stateName]
        
        for className in sorted(row):
            entryObj = row[className]
            
            if entryObj is None:
                logger.error((
                  'V0886',
                  (),
                  "Cells in a state array must not be None."))
                
                r = False
                continue
            
            if entryObj.newState not in presentStates:
                logger.error((
                  'V0887',
                  (stateName, className, entryObj.newState),
                  "The state array cell for state '%s' and class '%s' "
                  "refers to the new state '%s', which is undefined."))
                
                r = False
    
    return r

def normalize(stateArray, rowFunc, entryFunc, **kwArgs):
    """
    Given a state array, fill it out, making sure every cell has an entry of
    the correct type. Note this changes stateArray in situ.
    
    The following keyword arguments are supported:
    
        addTransitions      If True (the default) this function will
                            automatically add the transitions associated with
                            busted matches. So for example, in a font with st
                            ligs, the sequence s-s-t would force the addition
                            of a transition in "Saw s" if another s is seen,
                            but only if the value in that cell is just a NOP.

                            Only top-level elisions are added; this does not
                            cover things like "office" and "ffl" seeing "offl".
    """
    
    if 'Start of text' not in stateArray:
        st = stateArray['Start of text'] = rowFunc()
    else:
        st = stateArray['Start of text']
    
    if 'Start of line' not in stateArray:
        stateArray['Start of line'] = st.__deepcopy__()
    
    fc = {"End of text", "Out of bounds", "Deleted glyph", "End of line"}
    fs = {"Start of text", "Start of line"}
    allClasses = {c for row in stateArray.values() for c in row}
    allClasses.update(fc)
    nop = entryFunc()
    startingClasses = set(c for c in st if c not in fc if st[c] != nop)
    
    for row in stateArray.values():
        for c in allClasses:
            if c not in row:
                row[c] = nop
    
    if kwArgs.get('addTransitions', True):
        # Make sure the deleted glyph stays in state
        for s, row in stateArray.items():
            if s in fs:
                continue
            
            if row['Deleted glyph'] == nop:
                row['Deleted glyph'] = entryFunc(newState=s)
        
        # Now add the actual internal transitions
        for s, row in stateArray.items():
            if s in fs:
                continue
            
            for c, e in row.items():
                if (c in fc) or (c not in startingClasses) or (e != nop):
                    continue
                
                row[c] = st[c]  # can it really be this simple??!?

def offsetsToSubWalkers(w, *offsets, **kwArgs):
    """
    Given a walker and a collection of walker-specific offsets, returns a list
    of walkers whose limits are appropriately set. The offsets may be out of
    order. Whichever offset ends up being last will use the walker's original
    limit; all others will use the start of the nearest following offset as
    their limits.
    
    The offsets are relative to the input walker's original start; they are not
    relative.
    
    The following keyword arguments are used:
    
        granularity     A dict which maps indices within offsets to a needed
                        number of bytes per record. The limits of the returned
                        walkers will respect this granularity, if present. The
                        dict is optional, and may be sparse.
        
        ignoreZeroes    A Boolean which, if True, causes any zero offsets to be
                        ignored (and None will be used instead of a returned
                        walker for those entries). Default is False.
        
        restoreOffset   A Boolean which, if True, will cause the input walker
                        w to have its offset restored to what it was on entry.
                        Default is False.
    
    >>> s = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    >>> w = walkerbit.StringWalker(s)
    >>> v = offsetsToSubWalkers(w, 6, 20, 12, 15)
    >>> len(v) == 4
    True
    
    >>> v[0].rest()
    b'GHIJKL'
    
    >>> v[1].rest()
    b'UVWXYZ'
    
    >>> v[2].rest()
    b'MNO'
    
    >>> v[3].rest()
    b'PQRST'
    
    >>> w = walkerbit.StringWalker(s, start=2)
    >>> v = offsetsToSubWalkers(w, 6, 20, 12, 15)
    >>> len(v) == 4
    True
    
    >>> v[0].rest()
    b'IJKLMN'
    
    >>> v[1].rest()
    b'WXYZ'
    
    >>> v[2].rest()
    b'OPQ'
    
    >>> v[3].rest()
    b'RSTUV'
    
    >>> w = walkerbit.StringWalker(s, start=2)
    >>> v = offsetsToSubWalkers(w, 6, 20, 12, 15, granularity={0:4, 3:4})
    >>> len(v) == 4
    True
    
    >>> v[0].rest()
    b'IJKL'
    
    >>> v[1].rest()
    b'WXYZ'
    
    >>> v[2].rest()
    b'OPQ'
    
    >>> v[3].rest()
    b'RSTU'
    
    >>> w = walkerbit.StringWalker(s, start=2)
    >>> v = offsetsToSubWalkers(w, 6, 0, 0, 15, granularity={0:4, 3:4}, ignoreZeroes=True)
    >>> v[1:3] == [None, None]
    True
    
    >>> w = walkerbit.StringWalker(s)
    >>> w.skip(4)
    >>> w.getOffset()
    4
    >>> v = offsetsToSubWalkers(w, 6, 20, 12, 15)
    >>> w.getOffset()
    0
    >>> w.skip(4)
    >>> w.getOffset()
    4
    >>> v2 = offsetsToSubWalkers(w, 6, 20, 12, 15, restoreOffset=True)
    >>> [v[0].rest(), v[1].rest(), v[2].rest(), v[3].rest()]
    [b'GHIJKL', b'UVWXYZ', b'MNO', b'PQRST']
    >>> [v2[0].rest(), v2[1].rest(), v2[2].rest(), v2[3].rest()]
    [b'GHIJKL', b'UVWXYZ', b'MNO', b'PQRST']
    >>> w.getOffset()
    4
    """
    
    grain = kwArgs.get('granularity', {})
    ignoreZeroes = kwArgs.get('ignoreZeroes', False)
    vSorted = sorted(enumerate(offsets), key=operator.itemgetter(1))
    r = [None] * len(vSorted)
    savedOffset = w.getOffset()
    w.reset()
    origOffset = w.getOffset()
    finalOffset = origOffset + w.length()
    
    for i, (origIndex, offset) in enumerate(vSorted):
        if offset or (not ignoreZeroes):
            # do granularity check to determine actual limit for this one
            lim = (finalOffset if i == (len(vSorted) - 1) else vSorted[i+1][1])
            thisLength = lim - offset
            
            if origIndex in grain:
                thisGrain = grain[origIndex]
                leftOver = thisLength % thisGrain
                
                if leftOver:
                    lim -= leftOver
            
            r[origIndex] = w.subWalker(offset, newLimit=lim+origOffset)
    
    if kwArgs.get('restoreOffset', False):
        w.setOffset(savedOffset - origOffset)
    
    return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walkerbit
    
    class _FakeEntry:
        def __init__(self, newState): self.newState = newState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
