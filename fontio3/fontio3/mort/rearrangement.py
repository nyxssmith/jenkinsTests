#
# rearrangement.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for rearrangement (type 0) subtables in a 'mort' table.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.mort import (
  classtable,
  entry_rearrangement,
  staterow_rearrangement,
  verbs_rearrangement)

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

class Rearrangement(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing state-based rearrangement subtables for old-style
    'mort' tables. These are dicts mapping state name strings to StateRow
    objects. The following attributes are defined:
    
        classTable      A ClassTable object, mapping glyphs to class strings.
        
        coverage        A Coverage object.
        
        maskValue       The arbitrarily long integer value with the subFeature
                        mask bits for this subtable.
    
    >>> _testingValues[0].pprint(
    ...   namer = namer.testingNamer(),
    ...   onlySignificant = True)
    State 'Start of text':
      Class 'Trigger':
        Go to state 'Saw trigger'
    State 'Start of line':
      Class 'Trigger':
        Go to state 'Saw trigger'
    State 'Saw first':
      Class 'Deleted glyph':
        Go to state 'Saw first'
      Class 'End of line':
        Go to state 'Saw first'
      Class 'End of text':
        Go to state 'Saw first'
      Class 'First':
        Mark start of grouping, then go to state 'Saw first'
      Class 'Last':
        Mark end of grouping and process the group via rule AxD => DxA, then go to state 'Start of text'
      Class 'Out of bounds':
        Go to state 'Saw first'
      Class 'Trigger':
        Go to state 'Saw first'
    State 'Saw trigger':
      Class 'Deleted glyph':
        Go to state 'Saw trigger'
      Class 'End of line':
        Go to state 'Saw trigger'
      Class 'End of text':
        Go to state 'Saw trigger'
      Class 'First':
        Mark start of grouping, then go to state 'Saw first'
      Class 'Last':
        Go to state 'Saw trigger'
      Class 'Out of bounds':
        Go to state 'Saw trigger'
      Class 'Trigger':
        Go to state 'Saw trigger'
    Class table:
      xyz13: First
      xyz20: Last
      xyz51: Trigger
    Mask value: 04000000
    Coverage:
      Process in both orientations
      Subtable kind: 0
    
    >>> logger = utilities.makeDoctestLogger("rearrangement_test")
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
    
    kind = 0  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Rearrangement object to the specified
        writer. The following keyword arguments are supported:
        
            stakeValue      A value that will stake the start of the data. This
                            is optional.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0007 0038 0064 0080  FEED 0003 0546 6972 |...8.d.......Fir|
              10 | 7374 044C 6173 7407  5472 6967 6765 7200 |st.Last.Trigger.|
              20 | 0209 5361 7720 6669  7273 740B 5361 7720 |..Saw first.Saw |
              30 | 7472 6967 6765 7200  000C 0027 0401 0101 |trigger....'....|
              40 | 0101 0105 0101 0101  0101 0101 0101 0101 |................|
              50 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              60 | 0101 0600 0000 0000  0000 0100 0000 0000 |................|
              70 | 0001 0202 0202 0304  0201 0101 0103 0101 |................|
              80 | 0064 0000 0079 0000  0072 0000 0072 8000 |.d...y...r...r..|
              90 | 0064 2003                                |.d .            |
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
        
        for entryIndex, entryObj in it:
            w.addUnresolvedOffset(
              "H",
              stakeValue,
              rowStakes[entryObj.newState])
            
            flags = (0x8000 if entryObj.markFirst else 0)
            flags += (0x4000 if entryObj.noAdvance else 0)
            flags += (0x2000 if entryObj.markLast else 0)
            flags += entryObj.verb
            w.add("H", flags)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Rearrangement object from the specified
        walker, doing source validation. The walker must start at the
        beginning (numClasses) of the state table.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("rearrangement_fvw")
        >>> fvb = Rearrangement.fromvalidatedbytes
        >>> d = {
        ...   'logger': logger,
        ...   'fontGlyphCount': 0x1000,
        ...   'coverage': _testingValues[0].coverage,
        ...   'maskValue': 0x04000000}
        >>> obj = fvb(s, **d)
        rearrangement_fvw.rearrangement - DEBUG - Walker has 148 remaining bytes.
        rearrangement_fvw.rearrangement.namestash - DEBUG - Walker has 140 remaining bytes.
        rearrangement_fvw.rearrangement.classtable - DEBUG - Walker has 44 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:6], **d)
        rearrangement_fvw.rearrangement - DEBUG - Walker has 6 remaining bytes.
        rearrangement_fvw.rearrangement - ERROR - Insufficient bytes.
        
        >>> fvb(utilities.fromhex("00 02") + s[2:], **d)
        rearrangement_fvw.rearrangement - DEBUG - Walker has 148 remaining bytes.
        rearrangement_fvw.rearrangement - ERROR - The number of classes in the state table must be at least four, but is only 2.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("rearrangement")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        stBaseOffset = w.getOffset()
        t = w.unpack("4H")
        numClasses, oCT, oSA, oET = t
        
        if numClasses < 4:
            logger.error((
              'V0634',
              (numClasses,),
              "The number of classes in the state table must be at least "
              "four, but is only %d."))
            
            return None
        
        firstValid = w.getOffset() - stBaseOffset
        lastValidPlusOne = firstValid + w.length()
        
        if any(o < firstValid or o >= lastValidPlusOne for o in t[1:]):
            logger.error((
              'V0635',
              (),
              "One or more offsets to state table components are outside "
              "the bounds of the state table itself."))
            
            return None
        
        wCT, wSA, wET = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *t[1:])
        
        wETCopy = wET.subWalker(0, relative=True)
        
        if wETCopy.length() < 4:
            logger.error((
              'V0636',
              (),
              "The entry table is missing or incomplete."))
            
            return None
        
        rawEntries = wET.unpackRest("2H")
        maxOffset = max(offset for offset, flags in rawEntries)
        numStates = 1 + (maxOffset - oSA) // numClasses
        
        nsObj = namestash.NameStash.readormake_validated(
          w,
          t[1:],
          numStates,
          numClasses,
          logger = logger)
        
        if nsObj is None:
            return nsObj
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        fgc = kwArgs.pop('fontGlyphCount')
        
        classTable = classtable.ClassTable.fromvalidatedwalker(
          wCT,
          classNames = classNames,
          logger = logger,
          fontGlyphCount = fgc)
        
        if classTable is None:
            return None
        
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
        
        S = staterow_rearrangement.StateRow
        E = entry_rearrangement.Entry
        V = verbs_rearrangement.Verb
        
        for stateIndex, rawState in enumerate(rawStateArray):
            thisRow = S()
            
            for classIndex, entryIndex in enumerate(rawState):
                if entryIndex >= len(rawEntries):
                    logger.error((
                      'V0724',
                      (stateNames[stateIndex], classNames[classIndex]),
                      "The state array cell for state '%s' and class '%s' "
                      "specifies an entry index that is out of range."))
                    
                    return None
                
                newStateOffset, flags = rawEntries[entryIndex]
                
                thisRow[classNames[classIndex]] = E(
                  markFirst = bool(flags & 0x8000),
                  markLast = bool(flags & 0x2000),
                  newState = stateNames[(newStateOffset - oSA) // numClasses],
                  noAdvance = bool(flags & 0x4000),
                  verb = V(flags & 0x000F))
            
            r[stateNames[stateIndex]] = thisRow
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Rearrangement object from the specified
        walker, which must start at the beginning (numClasses) of the state
        table.
        
        >>> obj = _testingValues[0]
        >>> obj == Rearrangement.frombytes(
        ...   obj.binaryString(),
        ...   coverage = obj.coverage,
        ...   maskValue = 0x04000000)
        True
        """
        
        numClasses, oCT, oSA, oET = w.unpack("4H")
        
        wCT, wSA, wET = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          oCT,
          oSA,
          oET)
        
        rawEntries = wET.unpackRest("2H")
        maxOffset = max(offset for offset, flags in rawEntries)
        numStates = 1 + (maxOffset - oSA) // numClasses
        
        nsObj = namestash.NameStash.readormake(
          w,
          (oCT, oSA, oET),
          numStates,
          numClasses)
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        
        classTable = classtable.ClassTable.fromwalker(
          wCT,
          classNames = classNames)
        
        rawStateArray = wSA.group("B" * numClasses, numStates)
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        S = staterow_rearrangement.StateRow
        E = entry_rearrangement.Entry
        V = verbs_rearrangement.Verb
        
        for stateIndex, rawState in enumerate(rawStateArray):
            thisRow = S()
            
            for classIndex, entryIndex in enumerate(rawState):
                newStateOffset, flags = rawEntries[entryIndex]
                
                thisRow[classNames[classIndex]] = E(
                  markFirst = bool(flags & 0x8000),
                  markLast = bool(flags & 0x2000),
                  newState = stateNames[(newStateOffset - oSA) // numClasses],
                  noAdvance = bool(flags & 0x4000),
                  verb = V(flags & 0x000F))
            
            r[stateNames[stateIndex]] = thisRow
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.mort import coverage
    from fontio3.utilities import namer
    
    # The test case does an AxD => DxA rearrangement on a grouping starting
    # with glyph 19 and ending with glyph 12, but only if glyph 50 has been
    # seen first.
    
    _classTable = classtable.ClassTable({
      12: "First",
      19: "Last",
      50: "Trigger"})
    
    E = entry_rearrangement.Entry
    V = verbs_rearrangement.Verb
    _entry_NOP_noTrigger = E()
    _entry_NOP_trigger = E(newState="Saw trigger")
    _entry_first = E(newState="Saw first", markFirst=True)
    _entry_NOP_first = E(newState="Saw first")
    _entry_last = E(markLast=True, verb=V(3))
    del E, V
    
    _row_SOT = staterow_rearrangement.StateRow({
      "End of text": _entry_NOP_noTrigger,
      "Out of bounds": _entry_NOP_noTrigger,
      "Deleted glyph": _entry_NOP_noTrigger,
      "End of line": _entry_NOP_noTrigger,
      "First": _entry_NOP_noTrigger,
      "Last": _entry_NOP_noTrigger,
      "Trigger": _entry_NOP_trigger})
    
    _row_SOL = _row_SOT
    
    _row_sawTrigger = staterow_rearrangement.StateRow({
      "End of text": _entry_NOP_trigger,
      "Out of bounds": _entry_NOP_trigger,
      "Deleted glyph": _entry_NOP_trigger,
      "End of line": _entry_NOP_trigger,
      "First": _entry_first,
      "Last": _entry_NOP_trigger,
      "Trigger": _entry_NOP_trigger})
    
    _row_sawFirst = staterow_rearrangement.StateRow({
      "End of text": _entry_NOP_first,
      "Out of bounds": _entry_NOP_first,
      "Deleted glyph": _entry_NOP_first,
      "End of line": _entry_NOP_first,
      "First": _entry_first,
      "Last": _entry_last,
      "Trigger": _entry_NOP_first})
    
    _coverage = coverage.Coverage(always=True, kind=0)
    
    _testingValues = (
        Rearrangement(
            { "Start of text": _row_SOT,
              "Start of line": _row_SOL,
              "Saw trigger": _row_sawTrigger,
              "Saw first": _row_sawFirst},
            coverage = _coverage,
            maskValue = 0x04000000,
            classTable = _classTable),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
