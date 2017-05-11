#
# insertion.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for insertion (type 5) subtables in a 'mort' table.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.mort import (
  classtable,
  entry_insertion,
  glyphtuple,
  staterow_insertion)

from fontio3.statetables import namestash, stutils

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, d, **kwArgs):
    vFixed = ["Start of text", "Start of line"]
    sFixed = set(vFixed)
    kwArgs.pop('label', None)
    
    for s in vFixed:
        p.deep(d[s], label=("State '%s'" % (s,)), **kwArgs)
    
    for s in sorted(d):
        if s not in sFixed:
            p.deep(d[s], label=("State '%s'" % (s,)), **kwArgs)
    
    attrhelper.M_pprint(d, p, d.getNamer, **kwArgs)

def _pprint_mask(p, value, label, **kwArgs):
    s = "%X" % (value,)
    extra = len(s) % 8
    
    if extra:
        s = "0" * (8 - extra) + s
    
    p.simple(s, label=label, **kwArgs)

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    referredToStates = {e.newState for sr in obj.values() for e in sr.values()}
    unknownStates = referredToStates - set(obj)
    
    if unknownStates:
        logger.error((
          'V0677',
          (sorted(unknownStates),),
          "These states are referred to but undefined: %s"))
        
        return False
    
    for stateName, sr in obj.items():
        for className, e in sr.items():
            if (e.newState == stateName) and e.noAdvance:
                logger.error((
                  'V0678',
                  (stateName, className, e.newState),
                  "The entry in state '%s', class '%s' has its new state "
                  "set to '%s' and the noAdvance bit set True. This will "
                  "result in an infinite loop."))
                
                return False
    
    allClassNames = set(k for sr in obj.values() for k in sr)
    
    if len(allClassNames) > 256:
        logger.error((
          'V0689',
          (len(allClassNames),),
          "There are %d classes, which exceeds the 'mort' table limit "
          "of 256 classes."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Insertion(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing state-based insertion subtables for old-style 'mort'
    tables. These are dicts mapping state name strings to StateRow objects. The
    following attributes are supported:
    
        classTable      A ClassTable object, mapping glyphs to class strings.
        
        coverage        A Coverage object.
        
        maskValue       The arbitrarily long integer value with the subFeature
                        mask bits for this subtable.
    
    >>> _testingValues[0].pprint(onlySignificant=True)
    State 'Start of text':
      Class 'D':
        Mark current location: True
        Name of next state: Saw D
    State 'Start of line':
      Class 'D':
        Mark current location: True
        Name of next state: Saw D
    State 'Saw D':
      Class 'Deleted glyph':
        Name of next state: Saw D
      Class 'D':
        Mark current location: True
        Name of next state: Saw D
      Class 'a':
        Name of next state: Saw Da
    State 'Saw Da':
      Class 'Deleted glyph':
        Name of next state: Saw Da
      Class 'D':
        Mark current location: True
        Name of next state: Saw D
      Class 'v':
        Name of next state: Saw Dav
    State 'Saw Dav':
      Class 'Deleted glyph':
        Name of next state: Saw Dav
      Class 'D':
        Mark current location: True
        Name of next state: Saw D
      Class 'e':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 97
        Current insertion is kashida-like: True
        Insert glyphs before mark: True
        Glyphs to insert at mark:
          0: 96
        Marked insertion is kashida-like: True
        Name of next state: Start of text
    Class table:
      12: D
      41: a
      45: e
      62: v
    Mask value: 00000001
    Coverage:
      Process in both orientations
      Subtable kind: 5
    
    >>> logger = utilities.makeDoctestLogger("insertion_test")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        map_pprintfunc = _pprint,
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        coverage = dict(
            attr_followsprotocol = True,
            attr_label = "Coverage"),
        
        classTable = dict(
            attr_followsprotocol = True,
            attr_initfunc = classtable.ClassTable,
            attr_label = "Class table"),
        
        maskValue = dict(
            attr_label = "Mask value",
            attr_pprintfunc = _pprint_mask))
    
    attrSorted = ('classTable', 'maskValue', 'coverage')
    
    kind = 5  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Insertion object to the specified writer.
        The following keyword arguments are supported:
        
            stakeValue      A value that will stake the start of the data. This
                            is optional.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0008 002C 0064 008C  FEED 0004 0144 0161 |...,.d.......D.a|
              10 | 0165 0176 0003 0553  6177 2044 0653 6177 |.e.v...Saw D.Saw|
              20 | 2044 6107 5361 7720  4461 7600 000C 0033 | Da.Saw Dav....3|
              30 | 0401 0101 0101 0101  0101 0101 0101 0101 |................|
              40 | 0101 0101 0101 0101  0101 0101 0105 0101 |................|
              50 | 0106 0101 0101 0101  0101 0101 0101 0101 |................|
              60 | 0101 0700 0000 0000  0100 0000 0000 0000 |................|
              70 | 0100 0000 0000 0200  0103 0000 0000 0300 |................|
              80 | 0100 0004 0000 0400  0100 0500 0064 0000 |.............d..|
              90 | 0000 0000 0074 8000  0000 0000 0074 0000 |.....t.......t..|
              A0 | 0000 0000 007C 0000  0000 0000 0084 0000 |.....|..........|
              B0 | 0000 0000 0064 3421  00BE 00BC 0060 0061 |.....d4!.....`.a|
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        nsObj = namestash.NameStash.fromstatedict(self)
        classNames = nsObj.allClassNames()
        w.add("xB", len(classNames))
        revClassMap = {s: i for i, s in enumerate(classNames)}
        stateNames = nsObj.allStateNames()
        ctStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, ctStake)
        saStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, saStake)
        etStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, etStake)
        kwArgs.pop('neededAlignment', None)
        kwArgs.pop('classDict', None)
        nsObj.buildBinary(w, neededAlignment=2, **kwArgs)
        
        self.classTable.buildBinary(
          w,
          stakeValue = ctStake,
          classDict = revClassMap,
          **kwArgs)
        
        entryPool = {}
        w.stakeCurrentWithValue(saStake)
        rowStakes = {name: w.getNewStake() for name in stateNames}
        
        for stateName in stateNames:
            w.stakeCurrentWithValue(rowStakes[stateName])
            
            for className in classNames:
                thisEntry = self[stateName][className]
                immut = thisEntry.asImmutable()
                
                if immut not in entryPool:
                    entryPool[immut] = (len(entryPool), thisEntry)
                
                w.add("B", entryPool[immut][0])
        
        w.alignToByteMultiple(2)
        w.stakeCurrentWithValue(etStake)
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        glyphTuplePool = {}
        
        for entryIndex, entryObj in it:
            w.addUnresolvedOffset(
              "H",
              stakeValue,
              rowStakes[entryObj.newState])
            
            flags = currOffsetStake = markOffsetStake = 0
            
            if entryObj.mark:
                flags |= 0x8000
            
            if entryObj.noAdvance:
                flags |= 0x4000
            
            cig = entryObj.currentInsertGlyphs
            mig = entryObj.markedInsertGlyphs
            
            if cig:
                if len(cig) > 31:
                    raise ValueError("Too many current insertions!")
                
                if cig not in glyphTuplePool:
                    glyphTuplePool[cig] = w.getNewStake()
                
                currOffsetStake = glyphTuplePool[cig]
                
                if entryObj.currentIsKashidaLike:
                    flags |= 0x2000
                
                if entryObj.currentInsertBefore:
                    flags |= 0x0800
                
                flags |= (len(cig) << 5)
            
            if mig:
                if len(mig) > 31:
                    raise ValueError("Too many marked insertions!")
                
                if mig not in glyphTuplePool:
                    glyphTuplePool[mig] = w.getNewStake()
                
                markOffsetStake = glyphTuplePool[mig]
                
                if entryObj.markedIsKashidaLike:
                    flags |= 0x1000
                
                if entryObj.markedInsertBefore:
                    flags |= 0x0400
                
                flags |= len(mig)
            
            w.add("H", flags)
            
            if currOffsetStake:
                w.addUnresolvedOffset("H", stakeValue, currOffsetStake)
            else:
                w.add("H", 0)
            
            if markOffsetStake:
                w.addUnresolvedOffset("H", stakeValue, markOffsetStake)
            else:
                w.add("H", 0)
        
        # finally, add the glyph tuples
        
        for t, stake in sorted(glyphTuplePool.items()):
            w.stakeCurrentWithValue(stake)
            w.addGroup("H", t)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Insertion object from the specified walker,
        doing source validation. The walker must start at the beginning
        (numClasses) of the state table.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("insertion")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        stBaseOffset = w.getOffset()
        tHeader = w.unpack("4H")
        numClasses, oCT, oSA, oET = tHeader
        
        if numClasses < 4:
            logger.error((
              'V0634',
              (numClasses,),
              "The number of classes in the state table must be at least "
              "four, but is only %d."))
            
            return None
        
        firstValid = w.getOffset() - stBaseOffset
        lastValidPlusOne = firstValid + w.length()
        
        if any(o < firstValid or o >= lastValidPlusOne for o in tHeader[1:]):
            logger.error((
              'V0635',
              (),
              "One or more offsets to state table components are outside "
              "the bounds of the state table itself."))
            
            return None
        
        wCT, wSA, wET = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *tHeader[1:])
        
        if wET.length() < 8:
            logger.error((
              'V0636',
              (),
              "The entry table is missing or incomplete."))
            
            return None
        
        rawEntries = wET.unpackRest("4H")
        maxOffset = max(t[0] for t in rawEntries)
        numStates = 1 + (maxOffset - oSA) // numClasses
        
        nsObj = namestash.NameStash.readormake_validated(
          w,
          tHeader[1:],
          numStates,
          numClasses,
          logger = logger)
        
        if nsObj is None:
            return None
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        
        classTable = classtable.ClassTable.fromvalidatedwalker(
          wCT,
          classNames = classNames,
          logger = logger,
          fontGlyphCount = kwArgs.pop('fontGlyphCount'))
        
        if classTable is None:
            return None
        
        E = entry_insertion.Entry
        GTO = glyphtuple.GlyphTupleOutput
        entries = [None] * len(rawEntries)
        
        for i, raw in enumerate(rawEntries):
            newStateOffset, flags, currOffset, markOffset = raw
            currCount = (flags & 0x03E0) >> 5
            markCount = flags & 0x001F
            
            if currCount:
                if currOffset == 0xFFFF:
                    logger.error((
                      'V0720',
                      (i,),
                      "The current insert count for entry %d is nonzero "
                      "but the corresponding offset is the missing value."))
                    
                    return None
                
                wSub = w.subWalker(currOffset)
                
                if wSub.length() < 2 * currCount:
                    logger.error((
                      'V0721',
                      (i,),
                      "The current insert list for entry %d is missing "
                      "or incomplete."))
                    
                    return None
                
                t = wSub.group("H", currCount)
            
            else:
                t = []
            
            currGlyphs = GTO(t)
            
            if markCount:
                if markOffset == 0xFFFF:
                    logger.error((
                      'V0722',
                      (i,),
                      "The marked insert count for entry %d is nonzero "
                      "but the corresponding offset is the missing value."))
                    
                    return None
                
                wSub = w.subWalker(markOffset)
                
                if wSub.length() < 2 * markCount:
                    logger.error((
                      'V0723',
                      (i,),
                      "The marked insert list for entry %d is missing "
                      "or incomplete."))
                    
                    return None
                
                t = wSub.group("H", markCount)
            
            else:
                t = []
            
            markGlyphs = GTO(t)
            
            entries[i] = E(
              newState = stateNames[(newStateOffset - oSA) // numClasses],
              mark = bool(flags & 0x8000),
              noAdvance = bool(flags & 0x4000),
              currentIsKashidaLike = bool(flags & 0x2000),
              markedIsKashidaLike = bool(flags & 0x1000),
              currentInsertBefore = bool(flags & 0x0800),
              markedInsertBefore = bool(flags & 0x0400),
              currentInsertGlyphs = currGlyphs,
              markedInsertGlyphs = markGlyphs)
        
        if wSA.length() < numClasses * numStates:
            logger.error((
              'V0676',
              (),
              "The state array is missing or incomplete."))
            
            return None
        
        rawStateArray = wSA.group("B" * numClasses, numStates)
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        S = staterow_insertion.StateRow
        
        for stateIndex, rawState in enumerate(rawStateArray):
            r[stateNames[stateIndex]] = thisRow = S()
            
            for classIndex, entryIndex in enumerate(rawState):
                if entryIndex >= len(entries):
                    logger.error((
                      'V0724',
                      (stateNames[stateIndex], classNames[classIndex]),
                      "The state array cell for state '%s' and class '%s' "
                      "specifies an entry index that is out of range."))
                    
                    return None
                
                thisRow[classNames[classIndex]] = entries[entryIndex]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Insertion object from the specified walker,
        which must start at the beginning (numClasses) of the state table.
        
        >>> obj = _testingValues[0]
        >>> s = obj.binaryString()
        >>> d = {
        ...   'maskValue': obj.maskValue,
        ...   'coverage': obj.coverage.__deepcopy__()}
        >>> obj == Insertion.frombytes(s, **d)
        True
        """
        
        numClasses, oCT, oSA, oET = w.unpack("4H")
        
        wCT, wSA, wET = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          oCT,
          oSA,
          oET)
        
        numEntries = max(wSA.subWalker(0).unpackRest("B")) + 1
        rawEntries = wET.group("4H", numEntries)
        maxOffset = max(t[0] for t in rawEntries)
        numStates = 1 + (maxOffset - oSA) // numClasses
        
        nsObj = namestash.NameStash.readormake(
          w,
          (oCT, oSA, oET),
          numStates,
          numClasses)
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        E = entry_insertion.Entry
        GTO = glyphtuple.GlyphTupleOutput
        entries = [None] * len(rawEntries)
        
        for i, raw in enumerate(rawEntries):
            newStateOffset, flags, currOffset, markOffset = raw
            currCount = (flags & 0x03E0) >> 5
            markCount = flags & 0x001F
            
            if currCount:
                t = w.subWalker(currOffset).group("H", currCount)
            else:
                t = []
            
            currGlyphs = GTO(t)
            
            if markCount:
                t = w.subWalker(markOffset).group("H", markCount)
            else:
                t = []
            
            markGlyphs = GTO(t)
            
            entries[i] = E(
              newState = stateNames[(newStateOffset - oSA) // numClasses],
              mark = bool(flags & 0x8000),
              noAdvance = bool(flags & 0x4000),
              currentIsKashidaLike = bool(flags & 0x2000),
              markedIsKashidaLike = bool(flags & 0x1000),
              currentInsertBefore = bool(flags & 0x0800),
              markedInsertBefore = bool(flags & 0x0400),
              currentInsertGlyphs = currGlyphs,
              markedInsertGlyphs = markGlyphs)
        
        classTable = classtable.ClassTable.fromwalker(
          wCT,
          classNames = classNames)
        
        rawStateArray = wSA.group("B" * numClasses, numStates)
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        S = staterow_insertion.StateRow
        
        for stateIndex, rawState in enumerate(rawStateArray):
            r[stateNames[stateIndex]] = thisRow = S()
            
            for classIndex, entryIndex in enumerate(rawState):
                thisRow[classNames[classIndex]] = entries[entryIndex]
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.mort import coverage
    
    # _testingValues[0] is an insertion action that looks for the string "Dave"
    # and, if found, puts a fleuron at each end. The glyph codes are as follow:
    #
    #    'D' is glyph 12
    #    'a' is glyph 41
    #    'v' is glyph 62
    #    'e' is glyph 45
    #    left fleuron is glyph 96
    #    right fleuron is glyph 97
    
    _classTable = classtable.ClassTable({
      12: "D",
      41: "a",
      62: "v",
      45: "e"})
    
    E = entry_insertion.Entry
    GTO = glyphtuple.GlyphTupleOutput
    
    _entry_NOP = E()
    _entry_D = E(newState="Saw D", mark=True)
    _entry_D_nomark = E(newState="Saw D")
    _entry_Da = E(newState="Saw Da")
    _entry_Dav = E(newState="Saw Dav")
    _entry_Dave = E(
      newState = "Start of text",
      currentInsertGlyphs = GTO([97]),
      currentIsKashidaLike = True,
      markedInsertGlyphs = GTO([96]),
      markedIsKashidaLike = True,
      markedInsertBefore = True)
    
    SR = staterow_insertion.StateRow
    
    _row_SOT = SR({
      "End of text": _entry_NOP,
      "Out of bounds": _entry_NOP,
      "Deleted glyph": _entry_NOP,
      "End of line": _entry_NOP,
      "D": _entry_D,
      "a": _entry_NOP,
      "v": _entry_NOP,
      "e": _entry_NOP})
    
    _row_SOL = _row_SOT
    
    _row_SawD = SR({
      "End of text": _entry_NOP,
      "Out of bounds": _entry_NOP,
      "Deleted glyph": _entry_D_nomark,
      "End of line": _entry_NOP,
      "D": _entry_D,
      "a": _entry_Da,
      "v": _entry_NOP,
      "e": _entry_NOP})
    
    _row_SawDa = SR({
      "End of text": _entry_NOP,
      "Out of bounds": _entry_NOP,
      "Deleted glyph": _entry_Da,
      "End of line": _entry_NOP,
      "D": _entry_D,
      "a": _entry_NOP,
      "v": _entry_Dav,
      "e": _entry_NOP})
    
    _row_SawDav = SR({
      "End of text": _entry_NOP,
      "Out of bounds": _entry_NOP,
      "Deleted glyph": _entry_Dav,
      "End of line": _entry_NOP,
      "D": _entry_D,
      "a": _entry_NOP,
      "v": _entry_NOP,
      "e": _entry_Dave})
    
    _coverage = coverage.Coverage(always=True, kind=5)
    
    _testingValues= (
        Insertion(
          { "Start of text": _row_SOT,
            "Start of line": _row_SOL,
            "Saw D": _row_SawD,
            "Saw Da": _row_SawDa,
            "Saw Dav": _row_SawDav},
          coverage = _coverage,
          maskValue = 0x00000001,
          classTable = _classTable),)
    
    del SR, GTO, E, _classTable

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
