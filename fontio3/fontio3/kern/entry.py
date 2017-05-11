#
# entry.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entries in a 'kern' state table.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.kern import valuetuple
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, **k):
    if obj.push:
        sv = ["Push this glyph, then go to state "]
    else:
        sv = ["Go to state "]
    
    sv.append("'%s'" % (obj.newState,))
    
    if obj.noAdvance:
        sv.append(" (without advancing the glyph pointer)")
    
    v = obj.values
    specialCase = False
    
    if (v is not None) and (obj.push) and (len(v) == 1):
        x = v[0]
        
        if (int(x) == 0) and (not x.resetCrossStream):
            specialCase = True
    
    if obj.values and (not specialCase):
        sv.append(" after performing these actions")
        p.deep(obj.values, label = ''.join(sv))
    
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
        
        values          A ValueTuple object, or None. Default is None.
    
    >>> _testingValues[1].pprint()
    Go to state 'Saw f' after performing these actions:
      Pop #1:
        Value: 200
      Pop #2:
        Value: -200
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    val.newState - ERROR - The new state -3 is not a Unicode string.
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
        Adds the binary data for the Entry object to the specified writer. The
        following keyword arguments are used:
            
            stateArrayStakes        A dict mapping state name strings to their
                                    state row stake values. This is required.
            
            stateTableBase          A stake value for the base of the entire
                                    state table. Most internal state table
                                    offsets are measured from this point. This
                                    is required.
        
            valueTuplePool          A dict mapping immutable values of
                                    ValueTuple objects to (stake, ValueTuple)
                                    pairs. This pool may be added to by this
                                    method. This is optional; if not specified,
                                    a local pool will be used. The ValueTuples
                                    will only be actually added if a
                                    valueTuplePool is not specified; if it is
                                    specified, a higher-level client is
                                    responsible for this.
        
        >>> w = writer.LinkedWriter()
        >>> stBase = w.stakeCurrent()
        >>> w.add("l", -1)
        >>> saStakes = {'Saw f': w.stakeCurrent()}
        >>> _testingValues[1].buildBinary(
        ...   w,
        ...   stateArrayStakes = saStakes,
        ...   stateTableBase = stBase,
        ...   isCrossStream = False)
        >>> utilities.hexdump(w.binaryString())
               0 | FFFF FFFF 0004 0008  00C8 FF39           |...........9    |
        """
        
        vtPool = kwArgs.pop('valueTuplePool', None)
        
        if vtPool is None:
            vtPool = {}
            doLocal = True
        
        else:
            doLocal = False
        
        stBase = kwArgs['stateTableBase']
        
        w.addUnresolvedOffset(
          "H",
          stBase,
          kwArgs['stateArrayStakes'][self.newState])
        
        w.addBits((b'\x80' if self.push else b'\x00'), 1)
        w.addBits((b'\x80' if self.noAdvance else b'\x00'), 1)
        
        if self.values:
            immut = self.values.asImmutable()
            
            if immut not in vtPool:
                vtPool[immut] = (w.getNewStake(), self.values)
            
            w.addUnresolvedOffset("H", stBase, vtPool[immut][0], bitLength=14)
        
        else:
            w.addBits(b'\x00\x00', 14)
        
        if doLocal:
            it = sorted(vtPool.items(), key=operator.itemgetter(0))
            
            for key, t in it:
                t[1].buildBinary(w, stakeValue=t[0], **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Entry object from the specified walker, doing
        source validation. There are many keyword arguments:
        
            isCrossStream           True if the state table is cross-stream,
                                    False otherwise. This is required (although
                                    it is only passed through, and not actually
                                    used in the implementation of the method).
            
            logger                  The logger to which messages will be
                                    posted.
            
            numClasses              Number of classes (including the 4 fixed
                                    classes). This is required.
            
            stateArrayBaseOffset    Byte offset from the start of the state
                                    table to the start of the state array. This
                                    is required.
            
            stateNames              A sequence of the state names (including
                                    the fixed names). This is required.
            
            valueTuplePool          A dict mapping ValueOffsets (as present in
                                    the binary data) to ValueTuples. It is used
                                    to ensure equal offsets get identical
                                    objects. This is optional.
            
            wSubtable               A walker whose base address is the start of
                                    the entire state table. This is required.
        
        See test/test_kern_format1.py for unittests.
        """
        
        assert 'isCrossStream' in kwArgs
        logger = kwArgs.pop('logger', logging.getLogger())
        logger.getChild("entry")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        newStateOffset, flags = w.unpack("2H")
        stateArrayBaseOffset = kwArgs['stateArrayBaseOffset']
        numClasses = kwArgs['numClasses']
        stateNames = kwArgs['stateNames']
        
        newStateIndex, remainder = divmod(
          newStateOffset - stateArrayBaseOffset,
          numClasses)
        
        if remainder or (not (0 <= newStateIndex < len(stateNames))):
            logger.error((
              'V0630',
              (),
              "New state offset is not valid (does not refer to the "
              "start of an actual state row)."))
            
            return None
        
        newState = stateNames[newStateIndex]
        push = bool(flags & 0x8000)
        noAdvance = bool(flags & 0x4000)
        valueOffset = flags & 0x3FFF
        fvw = valuetuple.ValueTuple.fromvalidatedwalker
        
        if valueOffset:
            vtPool = kwArgs.get('valueTuplePool', {})
            
            if valueOffset not in vtPool:
                w = kwArgs['wSubtable'].subWalker(valueOffset)
                vtPool[valueOffset] = fvw(w, logger=logger, **kwArgs)
            
            values = vtPool[valueOffset]
        
        else:
            values = None
        
        return cls(
          newState = newState,
          push = push,
          noAdvance = noAdvance,
          values = values)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Entry object from the specified walker. There
        are many keyword arguments:
        
            isCrossStream           True if the state table is cross-stream,
                                    False otherwise. This is required (although
                                    it is only passed through, and not actually
                                    used in the implementation of the method).
            
            numClasses              Number of classes (including the 4 fixed
                                    classes). This is required.
            
            stateArrayBaseOffset    Byte offset from the start of the state
                                    table to the start of the state array. This
                                    is required.
            
            stateNames              A sequence of the state names (including
                                    the fixed names). This is required.
            
            valueTuplePool          A dict mapping ValueOffsets (as present in
                                    the binary data) to ValueTuples. It is used
                                    to ensure equal offsets get identical
                                    objects. This is optional.
            
            wSubtable               A walker whose base address is the start of
                                    the entire state table. This is required.
        
        See test/test_kern_format1.py for unittests.
        """
        
        assert 'isCrossStream' in kwArgs
        newStateOffset, flags = w.unpack("2H")
        stateArrayBaseOffset = kwArgs['stateArrayBaseOffset']
        numClasses = kwArgs['numClasses']
        newStateIndex = (newStateOffset - stateArrayBaseOffset) // numClasses
        newState = kwArgs['stateNames'][newStateIndex]
        push = bool(flags & 0x8000)
        noAdvance = bool(flags & 0x4000)
        valueOffset = flags & 0x3FFF
        fw = valuetuple.ValueTuple.fromwalker
        
        if valueOffset:
            vtPool = kwArgs.get('valueTuplePool', {})
            
            if valueOffset not in vtPool:
                w = kwArgs['wSubtable'].subWalker(valueOffset)
                vtPool[valueOffset] = fw(w, **kwArgs)
            
            values = vtPool[valueOffset]
        
        else:
            values = None
        
        return cls(
          newState = newState,
          push = push,
          noAdvance = noAdvance,
          values = values)
    
    def isSignificant(self):
        """
        Returns False if the Entry goes to "Start of text" and has no other
        effects. Returns True otherwise.
        
        Note specifically that the currentInsertGlyphs and markedInsertGlyphs
        fields are checked, but not the "InsertBefore" or "IsKashidaLike"
        bits. This is because in the absence of glyph data, those flags are
        effectively NOPs.
        
        >>> _testingValues[0].isSignificant()
        False
        >>> _testingValues[1].isSignificant()
        True
        """
        
        if self.newState != "Start of text":
            return True
        
        if self.push or self.noAdvance:
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
    from fontio3.utilities import writer
    
    _vttv = valuetuple._testingValues
    
    _testingValues = (
        Entry(),
        Entry(newState="Saw f", values=_vttv[2]),
        
        # bad values start here
        
        Entry(newState=-3))
    
    del _vttv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
