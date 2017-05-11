#
# staterow.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single states in a 'kerx' state table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.statetables import classmap

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, d, **kwArgs):
    sigOnly = kwArgs.get('onlySignificant', False)
    vFixed = classmap.fixedNames
    sFixed = set(vFixed)
    kwArgs.pop('label', None)
    
    for s in vFixed:
        if (not sigOnly) or d[s].isSignificant():
            p.deep(d[s], label=("Class '%s'" % (s,)), **kwArgs)
    
    for s in sorted(d):
        if s in sFixed:
            continue
        
        if (not sigOnly) or d[s].isSignificant():
            p.deep(d[s], label=("Class '%s'" % (s,)), **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class StateRow(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing single rows in a state array. These are dicts whose
    keys are class names and whose values are Entry objects.
    
    >>> _testingValues[2].pprint(onlySignificant=True)
    Class 'Out of bounds':
      Go to state 'In word'
    Class 'Deleted glyph':
      Go to state 'In word'
    Class 'Letter':
      Push this glyph, then go to state 'In word' after applying these kerning shifts to the popped glyphs:
        Pop #1: 682
    Class 'Punctuation':
      Go to state 'In word'
    Class 'Space':
      Reset kerning, then go to state 'Start of text'
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        map_pprintfunc = _pprint)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the StateRow to the specified writer. The
        following keyword arguments are used:
        
            classNames      A sequence of class name strings. The order is
                            important, but is not simple string ordering;
                            rather, the order should correspond to the class
                            index values. Thus, "End of text" should be first,
                            "Out of bounds" second, etc. This is required.
            
            entryPool       A dict mapping immutable versions of all Entry
                            objects to (entryIndex, entryObj) pairs. This is
                            required.
        
            stakeValue      A value that will stake the start of the subtable.
                            This is optional.
        
        >>> ep = {
        ...   obj.asImmutable(): (i, obj)
        ...   for i, obj in enumerate(_entries)}
        >>> cn = [
        ...   "End of text", "Out of bounds", "Deleted glyph", "End of line",
        ...   "Letter", "Space", "Punctuation"]
        >>> d = {'classNames': cn, 'entryPool': ep}
        >>> h = utilities.hexdump
        >>> h(_testingValues[1].binaryString(**d))
               0 | 0000 0000 0000 0000  0001 0000 0000      |..............  |
        
        >>> h(_testingValues[2].binaryString(**d))
               0 | 0000 0001 0001 0000  0002 0003 0001      |..............  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        entryPool = kwArgs['entryPool']
        
        for className in kwArgs['classNames']:
            w.add("H", entryPool[self[className].asImmutable()][0])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new StateRow object from the specified walker.
        The following keyword arguments are used:
        
            classNames      A sequence of class name strings. The order is
                            important, but is not simple string ordering;
                            rather, the order should correspond to the class
                            index values. Thus, "End of text" should be first,
                            "Out of bounds" second, etc. This is required.
            
            entries         A sequence of Entry objects. This is required.
            
            logger          A logger to which messages will be posted.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("staterow")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        r = cls()
        entries = kwArgs['entries']
        cn = kwArgs['classNames']
        
        if w.length() < 2 * len(cn):
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        for className, index in zip(cn, w.group("H", len(cn))):
            r[className] = entries[index]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new StateRow object from the specified walker.
        The following keyword arguments are used:
        
            classNames      A sequence of class name strings. The order is
                            important, but is not simple string ordering;
                            rather, the order should correspond to the class
                            index values. Thus, "End of text" should be first,
                            "Out of bounds" second, etc. This is required.
            
            entries         A sequence of Entry objects. This is required.
        
        >>> ep = {
        ...   obj.asImmutable(): (i, obj)
        ...   for i, obj in enumerate(_entries)}
        >>> cn = [
        ...   "End of text", "Out of bounds", "Deleted glyph", "End of line",
        ...   "Letter", "Space", "Punctuation"]
        >>> dBS = {'classNames': cn, 'entryPool': ep}
        >>> dFW = {'classNames': cn, 'entries': _entries}
        >>> obj = _testingValues[1]
        >>> obj == StateRow.frombytes(obj.binaryString(**dBS), **dFW)
        True
        >>> obj = _testingValues[2]
        >>> obj == StateRow.frombytes(obj.binaryString(**dBS), **dFW)
        True
        """
        
        r = cls()
        entries = kwArgs['entries']
        cn = kwArgs['classNames']
        
        for className, index in zip(cn, w.group("H", len(cn))):
            r[className] = entries[index]
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.kerx import entry, valuetuple
    
    _entries = (
        entry.Entry(newState="Start of text"),
        entry.Entry(newState="In word"),
        
        entry.Entry(
          newState = "In word",
          push = True,
          values = valuetuple.ValueTuple([682])),
        
        entry.Entry(newState="Start of text", reset=True))
    
    _testingValues = (
        StateRow(),
        
        StateRow({
          "End of text": _entries[0],
          "Out of bounds": _entries[0],
          "Deleted glyph": _entries[0],
          "End of line": _entries[0],
          "Letter": _entries[1],
          "Space": _entries[0],
          "Punctuation": _entries[0]}),
        
        StateRow({
          "End of text": _entries[0],
          "Out of bounds": _entries[1],
          "Deleted glyph": _entries[1],
          "End of line": _entries[0],
          "Letter": _entries[2],
          "Space": _entries[3],
          "Punctuation": _entries[1]}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
