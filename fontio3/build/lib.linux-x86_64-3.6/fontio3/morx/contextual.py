#
# contextual.py
#
# Copyright © 2011-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for contextual (type 1) subtables in a 'morx' table.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.morx import (
  classtable,
  contextanalyzer,
  entry_contextual,
  glyphdict,
  staterow_contextual)

from fontio3.statetables import namestash, stutils, subtable_glyph_coverage_set
from fontio3.utilities import lookup

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
    
    if len(allClassNames) > 65536:
        logger.error((
          'V0689',
          (len(allClassNames),),
          "There are %d classes, which exceeds the 'morx' table limit "
          "of 65,536 classes."))
        
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
    Objects representing state-based contextual subtables for old-style
    'morx' tables. These are dicts mapping state name strings to StateRow
    objects. The following attributes are defined:
    
        classTable      A ClassTable object, mapping glyphs to class strings.
        
        coverage        A Coverage object.
        
        maskValue       The arbitrarily long integer value with the subFeature
                        mask bits for this subtable.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer(), onlySignificant=True)
    State 'Start of text':
      Class 'Trigger':
        Go to state 'Saw trigger'
    State 'Start of line':
      Class 'Trigger':
        Go to state 'Saw trigger'
    State 'Saw trigger':
      Class 'End of text':
        Go to state 'Saw trigger'
      Class 'Out of bounds':
        Go to state 'Saw trigger'
      Class 'Deleted glyph':
        Go to state 'Saw trigger'
      Class 'End of line':
        Go to state 'Saw trigger'
      Class 'Swash':
        Go to state 'Saw trigger' after changing the current glyph thus:
          xyz23: afii60000
          xyz24: afii60001
          xyz25: afii60002
          xyz26: afii60003
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
            attr_pprintfunc = _pprint_mask),

        glyphCoverageSet = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue=True,
            attr_initfunc = subtable_glyph_coverage_set.SubtableGlyphCoverageSet,
            attr_label = 'Glyph Coverage Set'))

    
    attrSorted = ('classTable', 'maskValue', 'coverage', 'glyphCoverageSet')
    
    kind = 1  # class constant
    
    #
    # Methods
    #
    
    def __bool__(self):
        """
        Special-case for state tables: both the dict itself AND the classTable
        need to be non-empty.
        """
        
        return (
          (len(self) > 0) and
          ('Start of text' in self) and
          (len(self['Start of text']) > 0) and
          (len(self.classTable) > 0))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Contextual object to the specified writer.
        The following keyword arguments are supported:
        
            preferredIOLookupFormat     If you need the actual input glyph to
                                        output glyph lookup to be written in a
                                        specific format, use this keyword. The
                                        default (as usual for Lookup objects)
                                        is to use the smallest one possible.
                                        
                                        Note this keyword is usually specified
                                        in the perTableOptions dict passed into
                                        the Editor's writeFont() method.
        
            stakeValue                  A value that will stake the start of
                                        the data. This is optional.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 0000 0006 0000 0034  0000 0052 0000 0076 |.......4...R...v|
              10 | 0000 008E FEED 0002  0553 7761 7368 0754 |.........Swash.T|
              20 | 7269 6767 6572 0001  0B53 6177 2074 7269 |rigger...Saw tri|
              30 | 6767 6572 0002 0006  0002 000C 0001 0000 |gger............|
              40 | 0019 0016 0004 0032  0032 0005 FFFF FFFF |.......2.2......|
              50 | FFFF 0000 0000 0000  0000 0000 0001 0000 |................|
              60 | 0000 0000 0000 0000  0001 0001 0001 0001 |................|
              70 | 0001 0002 0001 0000  0000 FFFF FFFF 0002 |................|
              80 | 0000 FFFF FFFF 0002  0000 FFFF 0000 0000 |................|
              90 | 0004 0008 0016 0004  005F 0060 0061 0062 |........._.`.a.b|
        
        >>> d = {'preferredIOLookupFormat': 2}
        >>> h(_testingValues[0].binaryString(**d))
               0 | 0000 0006 0000 0034  0000 0052 0000 0076 |.......4...R...v|
              10 | 0000 008E FEED 0002  0553 7761 7368 0754 |.........Swash.T|
              20 | 7269 6767 6572 0001  0B53 6177 2074 7269 |rigger...Saw tri|
              30 | 6767 6572 0002 0006  0002 000C 0001 0000 |gger............|
              40 | 0019 0016 0004 0032  0032 0005 FFFF FFFF |.......2.2......|
              50 | FFFF 0000 0000 0000  0000 0000 0001 0000 |................|
              60 | 0000 0000 0000 0000  0001 0001 0001 0001 |................|
              70 | 0001 0002 0001 0000  0000 FFFF FFFF 0002 |................|
              80 | 0000 FFFF FFFF 0002  0000 FFFF 0000 0000 |................|
              90 | 0004 0002 0006 0004  0018 0002 0000 0016 |................|
              A0 | 0016 005F 0017 0017  0060 0018 0018 0061 |..._.....`.....a|
              B0 | 0019 0019 0062 FFFF  FFFF FFFF           |.....b......    |
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
        w.add("L", len(classNames))
        ctStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, ctStake)
        saStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, saStake)
        etStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, etStake)
        gtStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, gtStake)
        kwArgs.pop('neededAlignment', None)
        kwArgs.pop('classDict', None)
        nsObj.buildBinary(w, neededAlignment=2, **kwArgs)
        
        self.classTable.buildBinary(
          w,
          stakeValue = ctStake,
          classDict = revClassMap,
          **kwArgs)
        
        w.stakeCurrentWithValue(saStake)
        entryPool = {}  # immut -> (entryIndex, obj)
        
        for stateName in stateNames:
            row = self[stateName]
            
            for className in classNames:
                thisEntry = row[className]
                immut = thisEntry.asImmutable()
                
                if immut not in entryPool:
                    entryPool[immut] = (len(entryPool), thisEntry)
                
                w.add("H", entryPool[immut][0])
        
        w.stakeCurrentWithValue(etStake)
        lookupPool = {}  # immut -> (lookupIndex, obj)
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        
        for entryIndex, obj in it:
            w.add("H", revStateMap[obj.newState])
            flags = (0x8000 if obj.mark else 0)
            flags += (0x4000 if obj.noAdvance else 0)
            w.add("H", flags)
            md = obj.markSubstitutionDict
            cd = obj.currSubstitutionDict
            
            if md:
                immut = md.asImmutable()
                
                if immut not in lookupPool:
                    lookupPool[immut] = (len(lookupPool), md)
                
                w.add("H", lookupPool[immut][0])
            
            else:
                w.add("h", -1)
            
            if cd:
                immut = cd.asImmutable()
                
                if immut not in lookupPool:
                    lookupPool[immut] = (len(lookupPool), cd)
                
                w.add("H", lookupPool[immut][0])
            
            else:
                w.add("h", -1)
        
        w.stakeCurrentWithValue(gtStake)
        v = sorted(lookupPool.values(), key=operator.itemgetter(0))
        lookupStakes = [w.getNewStake() for obj in v]
        
        for stake in lookupStakes:
            w.addUnresolvedOffset("L", gtStake, stake)
        
        preferredFormat = kwArgs.get('preferredIOLookupFormat', None)
        
        for (lookupIndex, gd), stake in zip(v, lookupStakes):
            lkObj = lookup.Lookup(gd)
            
            if preferredFormat is not None:
                lkObj._preferredFormat = preferredFormat
            
            lkObj.buildBinary(w, stakeValue=stake)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Contextual object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("contextual_fvw")
        >>> fvb = Contextual.fromvalidatedbytes
        >>> d = {
        ...   'fontGlyphCount': 1000,
        ...   'coverage': _testingValues[0].coverage,
        ...   'maskValue': 0x10000000,
        ...   'logger': logger}
        >>> obj = fvb(s, **d)
        contextual_fvw.contextual - DEBUG - Walker has 160 remaining bytes.
        contextual_fvw.contextual.classmap.lookup_aat - DEBUG - Walker has 30 remaining bytes.
        contextual_fvw.contextual.classmap.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 28 remaining bytes.
        contextual_fvw.contextual.per-glyph 0.lookup_aat - DEBUG - Walker has 14 remaining bytes.
        contextual_fvw.contextual.namestash - DEBUG - Walker has 140 remaining bytes.
        contextual_fvw.contextual.clstable - DEBUG - Walker has 30 remaining bytes.
        contextual_fvw.contextual.clstable.binsearch.binsrch header - DEBUG - Walker has 28 remaining bytes.
        
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
        
        t = w.unpack("5L")
        numClasses, oCT, oSA, oET, oGT = t
        
        wCT, wSA, wET, wGT = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *t[1:])
        
        numStates = analyzer.numStates
        
        nsObj = namestash.NameStash.readormake_validated(
          w,
          t[1:],
          numStates,
          numClasses,
          logger = logger)
        
        if nsObj is None:
            return None
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        fgc = utilities.getFontGlyphCount(**kwArgs)
        
        classTable = classtable.ClassTable.fromvalidatedwalker(
          wCT,
          classNames = classNames,
          logger = logger,
          fontGlyphCount = fgc)
        
        if classTable is None:
            return None
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        entryTable = analyzer.entryTable
        Entry = entry_contextual.Entry
        GD = glyphdict.GlyphDict
        StateRow = staterow_contextual.StateRow
        
        for stateIndex, rawState in enumerate(analyzer.stateArray):
            newRow = staterow_contextual.StateRow()
            
            for classIndex, entryIndex in enumerate(rawState):
                if entryIndex >= len(entryTable):
                    logger.error((
                      'V0724',
                      (stateNames[stateIndex], classNames[classIndex]),
                      "The state array cell for state '%s' and class '%s' "
                      "specifies an entry index that is out of range."))
                    
                    return None
                
                newStateIndex, flags = entryTable[entryIndex][0:2]
                
                newEntry = Entry(
                  newState = stateNames[newStateIndex],
                  mark = bool(flags & 0x8000),
                  noAdvance = bool(flags & 0x4000),
                  markSubstitutionDict = GD(markAnalysis.get(entryIndex, {})),
                  currSubstitutionDict = GD(currAnalysis.get(entryIndex, {})))
                
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
        t = w.unpack("5L")
        numClasses, oCT, oSA, oET, oGT = t
        
        wCT, wSA, wET, wGT = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *t[1:])
        
        numStates = analyzer.numStates
        nsObj = namestash.NameStash.readormake(w, t[1:], numStates, numClasses)
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        
        classTable = classtable.ClassTable.fromwalker(
          wCT,
          classNames = classNames)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        entryTable = analyzer.entryTable
        Entry = entry_contextual.Entry
        GD = glyphdict.GlyphDict
        StateRow = staterow_contextual.StateRow
        
        for stateIndex, rawState in enumerate(analyzer.stateArray):
            newRow = staterow_contextual.StateRow()
            
            for classIndex, entryIndex in enumerate(rawState):
                newStateIndex, flags = entryTable[entryIndex][0:2]
                
                newEntry = Entry(
                  newState = stateNames[newStateIndex],
                  mark = bool(flags & 0x8000),
                  noAdvance = bool(flags & 0x4000),
                  markSubstitutionDict = GD(markAnalysis.get(entryIndex, {})),
                  currSubstitutionDict = GD(currAnalysis.get(entryIndex, {})))
                
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
    
    def run(self, glyphArray, **kwArgs):
        """
        Given an input sequence of either glyph indices or (sequence index,
        glyph index) pairs, process them and return a new sequence of (original
        sequence index, output glyph) pairs.
        
        >>> _testingValues[0].run([22, 24])
        [(0, 22), (1, 24)]
        >>> _testingValues[0].run([50, 22, 24])
        [(0, 50), (1, 95), (2, 97)]
        >>> _testingValues[0].run([50, 90, 92, 95, 14, 22, 24])
        [(0, 50), (1, 90), (2, 92), (3, 95), (4, 14), (5, 95), (6, 97)]
        """
        
        currState = kwArgs.get('startState', 'Start of text')
        
        if not isinstance(glyphArray[0], tuple):
            v = list(enumerate(glyphArray))
        else:
            v = list(glyphArray)
        
        markIndex = None
        
        if self.coverage.reverse:
            i, delta, limit = (len(v) - 1, -1, -1)
        else:
            i, delta, limit = (0, 1, len(v))
        
        while i != limit:
            currGlyph = v[i][1]
            
            if currGlyph in {0xFFFF, 0xFFFE, None}:
                currClass = "Deleted glyph"
            else:
                currClass = self.classTable.get(currGlyph, "Out of bounds")
            
            e = self[currState][currClass]
            
            if e.mark:
                markIndex = i
            
            if e.currSubstitutionDict and currGlyph in e.currSubstitutionDict:
                v[i] = (v[i][0], e.currSubstitutionDict[currGlyph])
            
            if e.markSubstitutionDict:
                obj = v[markIndex]
                
                if obj[1] in e.markSubstitutionDict:
                    v[markIndex] = (obj[0], e.markSubstitutionDict[obj[1]])
            
            currState = e.newState
            
            if not e.noAdvance:
                i += delta
        
        currClass = "End of text"
        e = self[currState][currClass]
        
        if e.mark:
            markIndex = i
        
        if e.currSubstitutionDict and currGlyph in e.currSubstitutionDict:
            v[i] = (v[i][0], e.currSubstitutionDict[currGlyph])
        
        if e.markSubstitutionDict:
            obj = v[markIndex]
            
            if obj[1] in e.markSubstitutionDict:
                v[markIndex] = (obj[0], e.markSubstitutionDict[obj[1]])
        
        return v

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.morx import coverage
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
