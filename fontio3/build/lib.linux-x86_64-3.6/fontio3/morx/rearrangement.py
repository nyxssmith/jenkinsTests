#
# rearrangement.py
#
# Copyright © 2011-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for rearrangement (type 0) subtables in a 'morx' table.
"""

# System imports
import logging
import operator

# Other imports
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.morx import (
  classtable,
  entry_rearrangement,
  staterow_rearrangement,
  verbs_rearrangement)

from fontio3.statetables import namestash, stutils, subtable_glyph_coverage_set

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, d, **kwArgs):
    vFixed = ["Start of text", "Start of line"]
    sFixed = set(vFixed)
    
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

class Rearrangement(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing state-based rearrangement subtables for new-style
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
    State 'Saw first':
      Class 'End of text':
        Go to state 'Saw first'
      Class 'Out of bounds':
        Go to state 'Saw first'
      Class 'Deleted glyph':
        Go to state 'Saw first'
      Class 'End of line':
        Go to state 'Saw first'
      Class 'First':
        Mark start of grouping, then go to state 'Saw first'
      Class 'Last':
        Mark end of grouping and process the group via rule AxD => DxA, then go to state 'Start of text'
      Class 'Trigger':
        Go to state 'Saw first'
    State 'Saw trigger':
      Class 'End of text':
        Go to state 'Saw trigger'
      Class 'Out of bounds':
        Go to state 'Saw trigger'
      Class 'Deleted glyph':
        Go to state 'Saw trigger'
      Class 'End of line':
        Go to state 'Saw trigger'
      Class 'First':
        Mark start of grouping, then go to state 'Saw first'
      Class 'Last':
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
            attr_pprintfunc = _pprint_mask),

        glyphCoverageSet = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue=True,
            attr_initfunc = subtable_glyph_coverage_set.SubtableGlyphCoverageSet,
            attr_label = 'Glyph Coverage Set'))

    attrSorted = ('classTable', 'maskValue', 'coverage', 'glyphCoverageSet')
    
    kind = 0  # class constant
    
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
        Adds the binary data for the Rearrangement object to the specified
        writer. The following keyword arguments are supported:
        
            stakeValue      A value that will stake the start of the data. This
                            is optional.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0007 0000 0040  0000 005C 0000 0094 |.......@...\....|
              10 | FEED 0003 0546 6972  7374 044C 6173 7407 |.....First.Last.|
              20 | 5472 6967 6765 7200  0209 5361 7720 6669 |Trigger...Saw fi|
              30 | 7273 740B 5361 7720  7472 6967 6765 7200 |rst.Saw trigger.|
              40 | 0006 0004 0003 0008  0001 0004 000C 0004 |................|
              50 | 0013 0005 0032 0006  FFFF FFFF 0000 0000 |.....2..........|
              60 | 0000 0000 0000 0000  0001 0000 0000 0000 |................|
              70 | 0000 0000 0000 0001  0002 0002 0002 0002 |................|
              80 | 0003 0004 0002 0001  0001 0001 0001 0003 |................|
              90 | 0001 0001 0000 0000  0003 0000 0002 0000 |................|
              A0 | 0002 8000 0000 2003                      |...... .        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        nsObj = namestash.NameStash.fromstatedict(self)
        classNames = nsObj.allClassNames()
        w.add("xxH", len(classNames))
        revClassMap = {s: i for i, s in enumerate(classNames)}
        stateNames = nsObj.allStateNames()
        revStateMap = {s: i for i, s in enumerate(stateNames)}
        ctStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, ctStake)
        saStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, saStake)
        etStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, etStake)
        nsObj.buildBinary(w, neededAlignment=2, **kwArgs)
        
        self.classTable.buildBinary(
          w,
          stakeValue = ctStake,
          classDict = revClassMap,
          **kwArgs)
        
        entryPool = {}
        w.stakeCurrentWithValue(saStake)
        
        for stateName in stateNames:
            for className in classNames:
                thisEntry = self[stateName][className]
                immut = thisEntry.asImmutable()
                
                if immut not in entryPool:
                    entryPool[immut] = (len(entryPool), thisEntry)
                
                w.add("H", entryPool[immut][0])
        
        w.stakeCurrentWithValue(etStake)
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        
        for entryIndex, entryObj in it:
            w.add("H", revStateMap[entryObj.newState])
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
        ...   'coverage': _testingValues[0].coverage,
        ...   'maskValue': 0x04000000,
        ...   'fontGlyphCount': 0x1000,
        ...   'logger': logger}
        >>> obj = fvb(s, **d)
        rearrangement_fvw.rearrangement - DEBUG - Walker has 168 remaining bytes.
        rearrangement_fvw.rearrangement.namestash - DEBUG - Walker has 152 remaining bytes.
        rearrangement_fvw.rearrangement.clstable - DEBUG - Walker has 28 remaining bytes.
        rearrangement_fvw.rearrangement.clstable.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
        >>> _testingValues[0].pprint_changes(obj)
        
        >>> fvb(s[:6], **d)
        rearrangement_fvw.rearrangement - DEBUG - Walker has 6 remaining bytes.
        rearrangement_fvw.rearrangement - ERROR - Insufficient bytes.
        
        >>> fvb(utilities.fromhex("00 00 00 02") + s[4:], **d)
        rearrangement_fvw.rearrangement - DEBUG - Walker has 168 remaining bytes.
        rearrangement_fvw.rearrangement - ERROR - The number of classes in the state table must be at least four, but is only 2.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("rearrangement")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 16:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        stBaseOffset = w.getOffset()
        t = w.unpack("4L")
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
        
        rawEntries = wET.unpackRest("2H", strict=False)
        
        numStates = max(
          int(wSA.length()) // (2 * numClasses),
          1 + max(x[0] for x in rawEntries))
        
        if numStates < 2:
            logger.error((
              'V0725',
              (),
              "The number of states in the state table is less than two. "
              "The two fixed states must always be present."))
            
            return None
        
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
        
        if wSA.length() < 2 * numClasses * numStates:
            logger.error((
              'V0676',
              (),
              "The state array is missing or incomplete."))
            
            return None
        
        rawStateArray = wSA.group("H" * numClasses, numStates)
        
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
                
                newStateIndex, flags = rawEntries[entryIndex]
                
                thisRow[classNames[classIndex]] = E(
                  markFirst = bool(flags & 0x8000),
                  markLast = bool(flags & 0x2000),
                  newState = stateNames[newStateIndex],
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
        
        numClasses, oCT, oSA, oET = w.unpack("4L")
        
        wCT, wSA, wET = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          oCT,
          oSA,
          oET)
        
        rawEntries = wET.unpackRest("2H", strict=False)
        
        numStates = max(
          int(wSA.length()) // (2 * numClasses),
          1 + max(x[0] for x in rawEntries))
        
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
        
        rawStateArray = wSA.group("H" * numClasses, numStates)
        
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
                newStateIndex, flags = rawEntries[entryIndex]
                
                thisRow[classNames[classIndex]] = E(
                  markFirst = bool(flags & 0x8000),
                  markLast = bool(flags & 0x2000),
                  newState = stateNames[newStateIndex],
                  noAdvance = bool(flags & 0x4000),
                  verb = V(flags & 0x000F))
            
            r[stateNames[stateIndex]] = thisRow
        
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
            sr = staterow_rearrangement.StateRow()
            
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
        Renames all state names (as keys in the Rearrangement object, and as
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
        Runs the specified glyph array through the rearrangement subtable.
        
        >>> _testingValues[0].run([30, 12, 1, 2, 3, 19])
        [(0, 30), (1, 12), (2, 1), (3, 2), (4, 3), (5, 19)]
        
        >>> _testingValues[0].run([50, 12, 1, 2, 3, 19])
        [(0, 50), (5, 19), (2, 1), (3, 2), (4, 3), (1, 12)]
        """
        
        currState = kwArgs.get('startState', 'Start of text')
        
        if not isinstance(glyphArray[0], tuple):
            v = list(enumerate(glyphArray))
        else:
            v = list(glyphArray)
        
        firstMark, lastMark = (None, None)
        
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
            
            if e.markFirst:
                firstMark = i
            
            if e.markLast:
                lastMark = i
            
            if e.verb:
                doVerb = e.verb
                
                if delta == -1:
                    firstMark, lastMark = lastMark, firstMark
                    
                    if doVerb == 1:
                        doVerb = 2
                    
                    elif doVerb == 2:
                        doVerb = 1
                
                if doVerb == 1:  # Ax -> xA
                    v[firstMark:lastMark+1] = (
                      v[firstMark+1:lastMark+1] +
                      v[firstMark:firstMark+1])
                
                elif doVerb == 2:  # xD -> Dx
                    v[firstMark:lastMark+1] = (
                      v[lastMark:lastMark+1] +
                      v[firstMark:lastMark])
                
                elif doVerb == 3:  # AxD -> DxA
                    v[firstMark:lastMark+1] = (
                      v[lastMark:lastMark+1] +
                      v[firstMark+1:lastMark] +
                      v[firstMark:firstMark+1])
            
            currState = e.newState
            
            if not e.noAdvance:
                i += delta
        
        currClass = "End of text"
        e = self[currState][currClass]
        
        if e.markFirst:
            firstMark = i
        
        if e.markLast:
            lastMark = i
        
        if e.verb:
            if delta == -1:
                firstMark, lastMark = lastMark, firstMark
            
            if e.verb == 1:  # Ax -> xA
                v[firstMark:lastMark+1] = (
                  v[firstMark+1:lastMark+1] +
                  v[firstMark:firstMark+1])
            
            elif e.verb == 2:  # xD -> Dx
                v[firstMark:lastMark+1] = (
                  v[lastMark:lastMark+1] +
                  v[firstMark:lastMark])
        
        return v

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.morx import coverage
    from fontio3.utilities import namer
    
    # The test case does an AxD => DxA rearrangement on a grouping starting
    # with glyph 12 and ending with glyph 19, but only if glyph 50 has been
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
