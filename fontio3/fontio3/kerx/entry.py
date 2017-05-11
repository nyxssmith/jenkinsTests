#
# entry.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entries in a 'kerx' state table.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.kerx import valuetuple
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, **k):
    if obj.push:
        if obj.noAdvance:
            if obj.reset:
                sv = ["Reset kerning and push this glyph (without "
                      "advancing), then g"]
            
            else:
                sv = ["Push this glyph (without advancing), then g"]
        
        else:
            if obj.reset:
                sv = ["Reset kerning and push this glyph, then g"]
            else:
                sv = ["Push this glyph, then g"]
    
    else:
        if obj.noAdvance:
            if obj.reset:
                sv = ["Reset kerning (without advancing), then g"]
            else:
                sv = ["Without advancing, g"]
        
        else:
            if obj.reset:
                sv = ["Reset kerning, then g"]
            else:
                sv = ["G"]
    
    sv.append("o to state '%s'" % (obj.newState,))
    v = obj.values
    specialCase = False
    
    if (v is not None) and (obj.push) and (len(v) == 1) and (not v[0]):
        specialCase = True
    
    if v and (not specialCase):
        sv.append(" after applying these kerning shifts to the popped glyphs")
        p.deep(v, label = ''.join(sv))
    
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
    Objects representing single entries in an entry table. These are the
    contents of a single cell in the state array.

    These are simple objects with the following attributes:
    
        newState        A string representing the new state to go to after this
                        Entry is finished. Default is "Start of text".
        
        noAdvance       A Boolean which, if True, prevents the glyph pointer
                        from advancing to the next glyph after this Entry is
                        finished. Default is False.
        
        push            A Boolean which, if True, causes the current glyph to
                        be "pushed" onto the AAT stack. The glyph may be
                        immediately "popped" off the stack if the values
                        attribute is not None; otherwise, this flag marks this
                        glyph for some future processing. Default is False.
        
        reset           A Boolean which, if True, causes the current kerning
                        stack and value to be reset. This can be used to reset
                        cross-stream kerning.
        
        values          A ValueTuple object, or None. Default is None.
    
    >>> for obj in _testingValues[2:10]:
    ...     obj.pprint()
    Go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    Reset kerning, then go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    Without advancing, go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    Reset kerning (without advancing), then go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    Push this glyph, then go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    Reset kerning and push this glyph, then go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    Push this glyph (without advancing), then go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    Reset kerning and push this glyph (without advancing), then go to state 'Saw A' after applying these kerning shifts to the popped glyphs:
      Pop #1: -200
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[12].isValid(logger=logger, editor=e)
    val.newState - ERROR - The new state 3.75 is not a Unicode string.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        newState = dict(
            attr_initfunc = (lambda: "Start of text"),
            attr_label = "Name of next state",
            attr_strusesrepr = True,
            attr_validatefunc = functools.partial(
              valassist.isString,
              label = "new state")),
        
        push = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Push this glyph",
            attr_showonlyiftrue = True),
        
        noAdvance = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Don't advance to next glyph",
            attr_showonlyiftrue = True),
        
        reset = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Reset kerning",
            attr_showonlyiftrue = True),
        
        values = dict(
            attr_followsprotocol = True,
            attr_label = "Values"))
    
    objSpec = dict(
        obj_pprintfunc = _ppf)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Entry to the specified walker. The
        following keyword arguments are used:
        
            stateDict       A dict mapping state names to their row indices
                            within the state array. This is required.
            
            valueRevDict    A dict mapping immutable versions of ValueTuple
                            objects to the single 16-bit value index within the
                            final value table. This is required.
        
        >>> obj1 = _testingValues[1]
        >>> obj2 = _testingValues[9]
        >>> obj3 = _testingValues[10]
        >>> sn = ["Start of text", "Start of line", "Saw f", "Saw A"]
        >>> sd = {s: i for i, s in enumerate(sn)}
        >>> vrd = {obj1.values.asImmutable(): 5, obj2.values.asImmutable(): 18}
        >>> hd = utilities.hexdump
        >>> kw = {'stateDict': sd, 'valueRevDict': vrd}
        >>> hd(obj1.binaryString(**kw))
               0 | 0002 0000 0005                           |......          |
        
        >>> hd(obj2.binaryString(**kw))
               0 | 0003 E000 0012                           |......          |
        
        >>> hd(obj3.binaryString(**kw))
               0 | 0002 2000 FFFF                           |.. ...          |
        """
        
        w.add("H", kwArgs['stateDict'][self.newState])
        flags = (0x8000 if self.push else 0)
        flags += (0x4000 if self.noAdvance else 0)
        flags += (0x2000 if self.reset else 0)
        w.add("H", flags)
        
        if self.values:
            w.add("H", kwArgs['valueRevDict'][self.values.asImmutable()])
        else:
            w.add("h", -1)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and reutrns a new Entry from the specified walker. The
        following keyword arguments are used:
        
            logger          A logger to which messages will be posted.
            
            stateNames      A sequence of state names. This is required.
            
            valueDict       A dict mapping indices of single 16-bit values in
                            the valueTable to ValueTuple objects. Note that
                            this dict will be sparse. This is required.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("entry")
        
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
              'V0774',
              (newStateIndex,),
              "The new state index value %d is out of range."))
            
            return None
        
        return cls(
          newState = stateNames[newStateIndex],
          push = bool(flags & 0x8000),
          noAdvance = bool(flags & 0x4000),
          reset = bool(flags & 0x2000),
          values = kwArgs['valueDict'].get(actionIndex, None))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and reutrns a new Entry from the specified walker. The
        following keyword arguments are used:
        
            stateNames      A sequence of state names. This is required.
            
            valueDict       A dict mapping indices of single 16-bit values in
                            the valueTable to ValueTuple objects. Note that
                            this dict will be sparse. This is required.
        """
        
        newStateIndex, flags, actionIndex = w.unpack("3H")
        
        return cls(
          newState = kwArgs['stateNames'][newStateIndex],
          push = bool(flags & 0x8000),
          noAdvance = bool(flags & 0x4000),
          reset = bool(flags & 0x2000),
          values = kwArgs['valueDict'].get(actionIndex, None))
    
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
        
        if self.push or self.noAdvance or self.reset:
            return True
        
        if self.values:
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
    
    _vttv = valuetuple._testingValues
    
    _testingValues = (
        Entry(),
        Entry(newState="Saw f", values=_vttv[2]),
        
        Entry(
          newState = "Saw A",
          push = False,
          noAdvance = False,
          reset = False,
          values = _vttv[3]),
        
        Entry(
          newState="Saw A",
          push=False,
          noAdvance=False,
          reset=True,
          values=_vttv[3]),
        
        Entry(
          newState="Saw A",
          push=False,
          noAdvance=True,
          reset=False,
          values=_vttv[3]),
        
        Entry(
          newState="Saw A",
          push=False,
          noAdvance=True,
          reset=True,
          values=_vttv[3]),
        
        Entry(
          newState="Saw A",
          push=True,
          noAdvance=False,
          reset=False,
          values=_vttv[3]),
        
        Entry(
          newState="Saw A",
          push=True,
          noAdvance=False,
          reset=True,
          values=_vttv[3]),
        
        Entry(
          newState="Saw A",
          push=True,
          noAdvance=True,
          reset=False,
          values=_vttv[3]),
        
        Entry(
          newState="Saw A",
          push=True,
          noAdvance=True,
          reset=True,
          values=_vttv[3]),
        
        Entry(newState="Saw f", reset=True),
        Entry(newState="Start of text"),
        
        # bad values start here
        
        Entry(newState=3.75))
    
    del _vttv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
