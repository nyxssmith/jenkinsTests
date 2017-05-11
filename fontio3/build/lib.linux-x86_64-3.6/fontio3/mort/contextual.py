#
# contextual.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for contextual (type 1) subtables in a 'mort' table.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.mort import (
  classtable,
  contextanalyzer,
  entry_contextual,
  glyphdict,
  staterow_contextual)

from fontio3.statetables import namestash, stutils

# -----------------------------------------------------------------------------

#
# Private functions
#

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

class Contextual(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing state-based contexutal subtables for old-style
    'mort' tables. These are dicts mapping state name strings to StateRow
    objects. The following attributes are defined:
    
        classTable      A ClassTable object, mapping glyphs to class strings.
        
        coverage        A Coverage object.
        
        maskValue       The arbitrarily long integer value with the subFeature
                        mask bits for this subtable.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    State 'Saw trigger':
      Class 'Deleted glyph':
        Go to state 'Saw trigger'
      Class 'End of line':
        Go to state 'Saw trigger'
      Class 'End of text':
        Go to state 'Saw trigger'
      Class 'Out of bounds':
        Go to state 'Saw trigger'
      Class 'Swash':
        Go to state 'Saw trigger' after changing the current glyph thus:
          xyz23: afii60000
          xyz24: afii60001
          xyz25: afii60002
          xyz26: afii60003
      Class 'Trigger':
        Go to state 'Saw trigger'
    State 'Start of line':
      Class 'Trigger':
        Go to state 'Saw trigger'
    State 'Start of text':
      Class 'Trigger':
        Go to state 'Saw trigger'
    Class table:
      xyz23: Swash
      xyz24: Swash
      xyz25: Swash
      xyz26: Swash
      xyz51: Trigger
    Mask value: 10000000
    Coverage:
      Process in both orientations
      Subtable kind: 1
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda k: "State '%s'" % (k,)),
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
    
    kind = 1  # class constant
    
    #
    # Methods
    #
    
    def _analyzeSubstitutions(self, w):
        self._substInfo = {}  # immut -> (stake, startOutIndex, obj)
        cumulation = set()
        
        for stateObj in self.values():
            for thisEntry in stateObj.values():
                
                for d in (
                  thisEntry.markSubstitutionDict,
                  thisEntry.currSubstitutionDict):
                    
                    if not d:
                        continue
                    
                    immut = d.asImmutable()
                    
                    if immut in self._substInfo:
                        continue
                    
                    # Do the puzzle-fit
                    startOutIndex = self._findPuzzleFit(d, cumulation)
                    
                    # Add the entry
                    self._substInfo[immut] = (w.getNewStake(), startOutIndex, d)
                    
                    # Update the cumulation
                    minGlyph = min(d)
                    cumulation.update({n - minGlyph + startOutIndex for n in d})
    
    @staticmethod
    def _findPuzzleFit(d, cumulation):
        lowGlyph = min(d)
        thisSet = {n - lowGlyph for n in d}
        delta = 0
        
        while thisSet & cumulation:
            delta += 1
            thisSet = {n + 1 for n in thisSet}
        
        return delta
    
    def _writeSubstPiece(self, w):
        # find the total length of the substList and build the index->stake dict
        outListLen = 0
        indexToStake = {}
        
        for stake, startOutIndex, d in self._substInfo.values():
            outListLen = max(outListLen, max(d) - min(d) + 1 + startOutIndex)
            indexToStake[startOutIndex] = stake
        
        outList = [0] * outListLen
        
        # now construct the list
        for t in self._substInfo.values():
            startOutIndex, d = t[1:]
            lowGlyph = min(d)
            
            for inGlyph, outGlyph in d.items():
                outList[inGlyph - lowGlyph + startOutIndex] = outGlyph
        
        # now output the list, staking where indicated
        for i, outGlyph in enumerate(outList):
            if i in indexToStake:
                w.stakeCurrentWithValue(indexToStake[i])
            
            w.add("H", outGlyph)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Contextual object to the specified writer.
        The following keyword arguments are supported:
        
            stakeValue      A value that will stake the start of the data. This
                            is optional.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0006 002A 004C 005E  0076 FEED 0002 0553 |...*.L.^.v.....S|
              10 | 7761 7368 0754 7269  6767 6572 0001 0B53 |wash.Trigger...S|
              20 | 6177 2074 7269 6767  6572 0016 001D 0404 |aw trigger......|
              30 | 0404 0101 0101 0101  0101 0101 0101 0101 |................|
              40 | 0101 0101 0101 0101  0101 0500 0000 0000 |................|
              50 | 0001 0000 0000 0001  0101 0101 0201 004C |...............L|
              60 | 0000 0000 0000 0058  0000 0000 0000 0058 |.......X.......X|
              70 | 0000 0000 0025 005F  0060 0061 0062      |.....%._.`.a.b  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        nsObj = namestash.NameStash.fromstatedict(self)
        classNames = nsObj.allClassNames()
        revClassMap = {s: i for i, s in enumerate(classNames)}
        stateNames = nsObj.allStateNames()
        revStateMap = {s: i for i, s in enumerate(stateNames)}
        assert len(classNames) < 256
        w.add("H", len(classNames))
        ctStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, ctStake)
        saStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, saStake)
        etStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, etStake)
        stStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, stStake)
        kwArgs.pop('neededAlignment', None)
        kwArgs.pop('classDict', None)
        nsObj.buildBinary(w, neededAlignment=2, **kwArgs)
        self.classTable.buildBinary(w, stakeValue=ctStake, classDict=revClassMap, **kwArgs)
        entryPool = {}  # immut -> (entryIndex, obj)
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
        self._analyzeSubstitutions(w)
        # self._substInfo is now immut -> (stake, startOutIndex, obj)
        
        for entryIndex, entryObj in sorted(entryPool.values(), key=operator.itemgetter(0)):
            w.addUnresolvedOffset("H", stakeValue, rowStakes[entryObj.newState])
            flags = (0x8000 if entryObj.mark else 0)
            flags += (0x4000 if entryObj.noAdvance else 0)
            w.add("H", flags)
            
            for d in (entryObj.markSubstitutionDict, entryObj.currSubstitutionDict):
                if d:
                    immut = d.asImmutable()
                    
                    w.addUnresolvedOffset(
                        "h",  # we use this to make it easier to deal with signed offsets
                        stakeValue,
                        self._substInfo[immut][0],
                        negOK = True,
                        offsetDivisor = 2,
                        offsetMultiDelta = -min(d))
                
                else:
                    w.add("H", 0)
        
        w.alignToByteMultiple(2)  # probably superfluous
        w.stakeCurrentWithValue(stStake)
        self._writeSubstPiece(w)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Contextual object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("contextual_fvw")
        >>> fvb = Contextual.fromvalidatedbytes
        >>> d = {
        ...   'coverage': _testingValues[0].coverage,
        ...   'maskValue': 0x10000000,
        ...   'logger': logger}
        >>> obj = fvb(s, **d)
        contextual_fvw.contextual - DEBUG - Walker has 126 remaining bytes.
        contextual_fvw.contextual.namestash - DEBUG - Walker has 116 remaining bytes.
        contextual_fvw.contextual.classtable - DEBUG - Walker has 34 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:5], **d)
        contextual_fvw.contextual - DEBUG - Walker has 5 remaining bytes.
        contextual_fvw.contextual - ERROR - Insufficient bytes.
        
        >>> fvb(s[:23], **d)
        contextual_fvw.contextual - DEBUG - Walker has 23 remaining bytes.
        contextual_fvw.contextual - ERROR - One or more offsets to state table components are outside the bounds of the state table itself.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("contextual")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        analyzer = contextanalyzer.Analyzer(w.subWalker(0, relative=True))
        markAnalysis, currAnalysis = analyzer.analyze(logger=logger)
        
        if markAnalysis is None or currAnalysis is None:
            return None
        
        # Note that some of the size and other validation was already done in
        # the analyze() call, and is not reduplicated here.
        
        t = w.unpack("5H")
        numClasses, oCT, oSA, oET, oST = t
        t = t[1:]
        wCT, wSA, wET, wST = stutils.offsetsToSubWalkers(w.subWalker(0), *t)
        numStates = analyzer.numStates
        
        nsObj = namestash.NameStash.readormake_validated(
          w,
          t,
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
          logger = logger)
        
        if classTable is None:
            return None
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        entryTable = analyzer.entryTable
        Entry = entry_contextual.Entry
        GlyphDict = glyphdict.GlyphDict
        StateRow = staterow_contextual.StateRow
        
        for stateIndex, rawState in enumerate(analyzer.stateArray):
            newRow = staterow_contextual.StateRow()
            
            for classIndex, entryIndex in enumerate(rawState):
                newStateOffset, flags = entryTable[entryIndex][0:2]
                newStateIndex = (newStateOffset - oSA) // numClasses
                
                newEntry = Entry(
                  newState = stateNames[newStateIndex],
                  mark = bool(flags & 0x8000),
                  noAdvance = bool(flags & 0x4000),
                  
                  markSubstitutionDict = GlyphDict(
                    markAnalysis.get(entryIndex, {})),
                  
                  currSubstitutionDict = GlyphDict(
                    currAnalysis.get(entryIndex, {})))
                
                newRow[classNames[classIndex]] = newEntry
            
            r[stateNames[stateIndex]] = newRow
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Contextual object from the specified walker,
        which must start at the beginning (numClasses) of the state table.
        
        >>> obj = _testingValues[0]
        >>> obj == Contextual.frombytes(
        ...     obj.binaryString(), coverage=obj.coverage, maskValue=0x10000000)
        True
        """
        
        analyzer = contextanalyzer.Analyzer(w.subWalker(0, relative=True))
        markAnalysis, currAnalysis = analyzer.analyze()
        numClasses, oCT, oSA, oET, oST = w.unpack("5H")
        # in the following, note that limits are correctly set for all walkers
        wCT, wSA, wET, wST = stutils.offsetsToSubWalkers(w.subWalker(0), oCT, oSA, oET, oST)
        numStates = analyzer.numStates
        nsObj = namestash.NameStash.readormake(w, (oCT, oSA, oET, oST), numStates, numClasses)
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        classTable = classtable.ClassTable.fromwalker(wCT, classNames=classNames)
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        entryTable = analyzer.entryTable
        Entry = entry_contextual.Entry
        GlyphDict = glyphdict.GlyphDict
        StateRow = staterow_contextual.StateRow
        
        for stateIndex, rawState in enumerate(analyzer.stateArray):
            newRow = staterow_contextual.StateRow()
            
            for classIndex, entryIndex in enumerate(rawState):
                newStateOffset, flags = entryTable[entryIndex][0:2]
                newStateIndex = (newStateOffset - oSA) // numClasses
                
                newEntry = Entry(
                  newState = stateNames[newStateIndex],
                  mark = bool(flags & 0x8000),
                  noAdvance = bool(flags & 0x4000),
                  markSubstitutionDict = GlyphDict(markAnalysis.get(entryIndex, {})),
                  currSubstitutionDict = GlyphDict(currAnalysis.get(entryIndex, {})))
                
                newRow[classNames[classIndex]] = newEntry
            
            r[stateNames[stateIndex]] = newRow
        
        return r
    
    def renameClasses(self, oldToNew):
        """
        Renames all class names (in each StateRow, and in the class table) as
        specified by the oldToNew dict, which maps old strings to new ones. If
        an old name is not present as a key in oldToNew, that class name will
        not be changed.
        """
        
        ct = classtable.ClassTable()
        
        for glyph, className in self.classTable.items():
            ct[glyph] = oldToNew.get(className, className)
        
        self.classTable = ct
        
        for stateName in self:
            stateRow = self[stateName]
            sr = staterow_contextual.StateRow()
            
            for className, entryObj in stateRow.items():
                sr[oldToNew.get(className, className)] = entryObj
            
            self[stateName] = sr
    
    def renameClasses_auto(self, namerObj):
        """
        Automatically renames the classes to sensible names based on their
        mappings.
        """
        
        nsObj = namestash.NameStash.fromstatedict(self)
        origExtras = nsObj.addedClassNames
        nsObj.nameClasses(self.classTable, namerObj)
        oldToNew = dict(zip(origExtras, nsObj.addedClassNames))
        self.renameClasses(oldToNew)
    
    def renameStates(self, oldToNew):
        """
        Renames all state names (as keys in the Contextual object, and as
        newStateName values in the individual Entry objects) as specified by
        the oldToNew dict, which maps old strings to new ones. If an old name
        is not present as a key in oldToNew, that class name will not be
        changed.
        """
        
        for stateRow in self.values():
            for entryObj in stateRow.values():
                s = entryObj.newState
                entryObj.newState = oldToNew.get(s, s)
        
        d = {oldToNew.get(s, s): obj for s, obj in self.items()}
        self.clear()
        self.update(d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.mort import coverage
    from fontio3.utilities import namer
    
    # The test case changes input glyphs 22-25 into output glyphs 95-98, but
    # only if glyph 50 is seen earlier in the run.
    
    _classTable = classtable.ClassTable({
      22: "Swash",
      23: "Swash",
      24: "Swash",
      25: "Swash",
      50: "Trigger"})
    
    _entry_NOP_noTrigger = entry_contextual.Entry(newState = "Start of text")
    _entry_NOP_trigger = entry_contextual.Entry(newState = "Saw trigger")
    
    _entry_doSubst = entry_contextual.Entry(
      newState = "Saw trigger",
      currSubstitutionDict = glyphdict.GlyphDict({
        22: 95,
        23: 96,
        24: 97,
        25: 98}))
    
    _row_SOT = staterow_contextual.StateRow({
      "End of text": _entry_NOP_noTrigger,
      "Out of bounds": _entry_NOP_noTrigger,
      "Deleted glyph": _entry_NOP_noTrigger,
      "End of line": _entry_NOP_noTrigger,
      "Trigger": _entry_NOP_trigger,
      "Swash": _entry_NOP_noTrigger})
    
    _row_SOL = staterow_contextual.StateRow({
      "End of text": _entry_NOP_noTrigger,
      "Out of bounds": _entry_NOP_noTrigger,
      "Deleted glyph": _entry_NOP_noTrigger,
      "End of line": _entry_NOP_noTrigger,
      "Trigger": _entry_NOP_trigger,
      "Swash": _entry_NOP_noTrigger})
    
    _row_Trigger = staterow_contextual.StateRow({
      "End of text": _entry_NOP_trigger,
      "Out of bounds": _entry_NOP_trigger,
      "Deleted glyph": _entry_NOP_trigger,
      "End of line": _entry_NOP_trigger,
      "Trigger": _entry_NOP_trigger,
      "Swash": _entry_doSubst})
    
    _coverage = coverage.Coverage(always=True, kind=1)
    
    _testingValues = (
      Contextual(
        { "Start of text": _row_SOT,
          "Start of line": _row_SOL,
          "Saw trigger": _row_Trigger},
        coverage = _coverage,
        maskValue = 0x10000000,
        classTable = _classTable),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
