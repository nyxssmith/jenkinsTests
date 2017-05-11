#
# entry4.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entries in a format 4 subtable of a 'kerx' table.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, **k):
    if obj.mark:
        if obj.noAdvance:
            sv = ["Mark this glyph (without advancing), then g"]
        else:
            sv = ["Mark this glyph, then g"]
    
    else:
        if obj.noAdvance:
            sv = ["Without advancing, g"]
        else:
            sv = ["G"]
    
    sv.append("o to state '%s'" % (obj.newState,))
    a = obj.action
    
    if a is not None:
        sv.append(" after doing this alignment")
        p.deep(a, label = ''.join(sv))
    
    else:
        p(''.join(sv))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Entry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single entries in an entry table for a format 4
    subtable (i.e. the contents of a single cell in the state array).

    These are simple objects with the following attributes:
        
        action          A PointEntry, AnchorEntry, CoordEntry, or None. Default
                        is None.
        
        mark            A Boolean which, if True, causes the current glyph to
                        be "marked". Default is False.
    
        newState        A string representing the new state to go to after this
                        Entry is finished. Default is "Start of text".
        
        noAdvance       A Boolean which, if True, prevents the glyph pointer
                        from advancing to the next glyph after this Entry is
                        finished. Default is False.
    
    >>> _testingValues[1].pprint()
    Mark this glyph, then go to state 'Saw Base'
    
    >>> _testingValues[2].pprint()
    Go to state 'Start of text' after doing this alignment:
      Marked glyph's point: 2
      Current glyph's point: 5
    
    >>> _testingValues[3].pprint()
    Without advancing, go to state 'Part 2' after doing this alignment:
      Marked glyph's X-coordinate: 200
      Marked glyph's Y-coordinate: -130
      Current glyph's X-coordinate: 50
      Current glyph's Y-coordinate: 190
    
    >>> _testingValues[4].pprint()
    Go to state 'Start of text' after doing this alignment:
      Marked glyph's anchor: 4
      Current glyph's anchor: 3
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        newState = dict(
            attr_initfunc = (lambda: "Start of text"),
            attr_label = "Name of next state",
            attr_strusesrepr = True,
            attr_validatefunc_partial = functools.partial(
              valassist.isString,
              label = "new state")),
        
        mark = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Mark this glyph",
            attr_showonlyiftrue = True),
        
        noAdvance = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Don't advance to next glyph",
            attr_showonlyiftrue = True),
        
        action = dict(
            attr_followsprotocol = True,
            attr_label = "Action to perform",
            attr_showonlyiffunc = (lambda x: x is not None)))
    
    objSpec = dict(
        obj_pprintfunc = _ppf)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Entry object to the specified writer. The
        following keyword arguments are used:
        
            revDict     A dict mapping immutable versions of (non-None) action
                        objects to the single 16-bit value index within the
                        final value table. This is required for Entry objects
                        whose action attribute is not None.
            
            stateDict   A dict mapping state names to their row indices within
                        the state array. This is required.
        
        >>> h = utilities.hexdump
        >>> bs = _testingValues[1].binaryString(stateDict = {"Saw Base": 5})
        >>> h(bs)
               0 | 0005 8000 FFFF                           |......          |
        
        >>> obj = _testingValues[2]
        >>> bs = obj.binaryString(
        ...     stateDict = {"Start of text": 0},
        ...     revDict = {obj.action.asImmutable(): 4})
        >>> h(bs)
               0 | 0000 0000 0004                           |......          |
        """
        
        w.add("H", kwArgs['stateDict'][self.newState])
        flags = 0
        
        if self.mark:
            flags += 0x8000
        
        if self.noAdvance:
            flags += 0x4000
        
        w.add("H", flags)
        
        if self.action is None:
            w.add("h", -1)
        else:
            w.add("H", kwArgs['revDict'][self.action.asImmutable()])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Entry object from the specified walker. The
        following keyword arguments are supported:
        
            actionMap       A sequence mapping a 16-bit index to an object of
                            the appropriate kind. This is required.
            
            logger          A logging object to which messages will be posted.
            
            stateNames      A mappable object taking a 16-bit index and having
                            the corresponding state name as a value. This is
                            required.
        
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Entry.fromvalidatedbytes
        >>> bs = utilities.fromhex("00 00 80 00 FF FF")
        >>> sn = ["Start of text"]
        >>> fvb(bs, stateNames=sn, logger=logger).pprint()
        fvw.entry4 - DEBUG - Walker has 6 remaining bytes.
        Mark this glyph, then go to state 'Start of text'
        
        >>> fvb(bs[:-1], stateNames=sn, logger=logger)
        fvw.entry4 - DEBUG - Walker has 5 remaining bytes.
        fvw.entry4 - ERROR - Insufficient bytes.
        
        >>> bs = utilities.fromhex("00 00 00 C0 FF FF")
        >>> fvb(bs, stateNames=sn, logger=logger).pprint()
        fvw.entry4 - DEBUG - Walker has 6 remaining bytes.
        fvw.entry4 - WARNING - One or more reserved bits are set in the flags.
        Go to state 'Start of text'
        
        >>> bs = utilities.fromhex("00 00 00 00 00 00")
        >>> am = {0: pointentry.PointEntry(19, 2)}
        >>> fvb(bs, stateNames=sn, actionMap=am, logger=logger).pprint()
        fvw.entry4 - DEBUG - Walker has 6 remaining bytes.
        Go to state 'Start of text' after doing this alignment:
          Marked glyph's point: 19
          Current glyph's point: 2
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("entry4")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        newStateIndex, flags, actionIndex = w.unpack("3H")
        stateNames = kwArgs['stateNames']
        
        if newStateIndex >= len(stateNames):
            logger.error((
              'V0786',
              (len(stateNames) - 1, newStateIndex),
              "The new state index should be a value from zero through %d, "
              "but is %d."))
            
            return None
        
        if flags & 0x3FFF:
            logger.warning((
              'V0787',
              (),
              "One or more reserved bits are set in the flags."))
        
        actions = kwArgs.get('actionMap', {})
        
        if actionIndex != 0xFFFF:
            try:
                actions[actionIndex]
                wasBad = False
            
            except (IndexError, KeyError):
                wasBad = True
            
            if wasBad:
                logger.error((
                  'V0789',
                  (actionIndex,),
                  "The action index %d is not present."))
            
                return None
        
        return cls(
          newState = stateNames[newStateIndex],
          mark = bool(flags & 0x8000),
          noAdvance = bool(flags & 0x4000),
          action = (None if actionIndex == 0xFFFF else actions[actionIndex]))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Entry object from the specified walker. The
        following keyword arguments are supported:
        
            actionMap       A mappable object (could be a sequence too) taking
                            a 16-bit index and returning an object of the
                            appropriate kind. This is required.
            
            stateNames      A mappable object taking a 16-bit index and having
                            the corresponding state name as a value. This is
                            required.
        
        >>> bs = utilities.fromhex("00 00 80 00 FF FF")
        >>> sn = ["Start of text"]
        >>> Entry.frombytes(bs, stateNames=sn).pprint()
        Mark this glyph, then go to state 'Start of text'
        
        >>> bs = utilities.fromhex("00 00 00 00 00 00")
        >>> am = {0: pointentry.PointEntry(19, 2)}
        >>> Entry.frombytes(bs, stateNames=sn, actionMap=am).pprint()
        Go to state 'Start of text' after doing this alignment:
          Marked glyph's point: 19
          Current glyph's point: 2
        """
        
        newStateIndex, flags, actionIndex = w.unpack("3H")
        newState = kwArgs['stateNames'][newStateIndex]
        mark = bool(flags & 0x8000)
        noAdvance = bool(flags & 0x4000)
        
        if actionIndex == 0xFFFF:
            action = None
        else:
            action = kwArgs['actionMap'][actionIndex]
        
        return cls(
            newState = newState,
            mark = mark,
            noAdvance = noAdvance,
            action = action)
    
    def isSignificant(self):
        """
        Returns False if the Entry goes to "Start of text" and has no other
        effects. Returns True otherwise.
        
        >>> _testingValues[0].isSignificant()
        False
        >>> _testingValues[1].isSignificant()
        True
        """
        
        if self.newState != "Start of text":
            return True
        
        if self.mark or self.noAdvance:
            return True
        
        if self.action is not None:
            return True
        
        return False

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.kerx import anchorentry, coordentry, pointentry
    
    _atv = anchorentry._testingValues
    _ctv = coordentry._testingValues
    _ptv = pointentry._testingValues
    
    _testingValues = (
        Entry(),
        
        Entry(newState="Saw Base", mark=True),
        
        Entry(action=_ptv[1]),
        
        Entry(noAdvance=True, newState='Part 2', action=_ctv[1]),
        
        Entry(action=_atv[1]))
    
    del _ptv, _ctv, _atv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
