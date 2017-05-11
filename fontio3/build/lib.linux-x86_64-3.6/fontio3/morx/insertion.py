#
# insertion.py
#
# Copyright © 2012-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for insertion (type 5) subtables in a 'morx' table.
"""

# System imports
import logging
import operator

# Other imports
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.morx import (
  classtable,
  entry_insertion,
  glyphtuple,
  staterow_insertion)

from fontio3.statetables import namestash, stutils, subtable_glyph_coverage_set

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

class Insertion(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing state-based insertion subtables for new-style 'morx'
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
            attr_pprintfunc = _pprint_mask),

        glyphCoverageSet = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue=True,
            attr_initfunc = subtable_glyph_coverage_set.SubtableGlyphCoverageSet,
            attr_label = 'Glyph Coverage Set'))

    
    attrSorted = ('classTable', 'maskValue', 'coverage', 'glyphCoverageSet')
    
    kind = 5  # class constant
    
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
        Adds the binary data for the Insertion object to the specified writer.
        The following keyword arguments are supported:
        
            stakeValue      A value that will stake the start of the data. This
                            is optional.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0008 0000 0038  0000 0058 0000 00A8 |.......8...X....|
              10 | 0000 00D8 FEED 0004  0144 0161 0165 0176 |.........D.a.e.v|
              20 | 0003 0553 6177 2044  0653 6177 2044 6107 |...Saw D.Saw Da.|
              30 | 5361 7720 4461 7600  0006 0004 0004 0010 |Saw Dav.........|
              40 | 0002 0000 000C 0004  0029 0005 002D 0006 |.........)...-..|
              50 | 003E 0007 FFFF FFFF  0000 0000 0000 0000 |.>..............|
              60 | 0001 0000 0000 0000  0000 0000 0000 0000 |................|
              70 | 0001 0000 0000 0000  0000 0000 0002 0000 |................|
              80 | 0001 0003 0000 0000  0000 0000 0003 0000 |................|
              90 | 0001 0000 0000 0004  0000 0000 0004 0000 |................|
              A0 | 0001 0000 0005 0000  0000 0000 FFFF FFFF |................|
              B0 | 0002 8000 FFFF FFFF  0002 0000 FFFF FFFF |................|
              C0 | 0003 0000 FFFF FFFF  0004 0000 FFFF FFFF |................|
              D0 | 0000 3421 0000 0001  0061 0060           |..4!.....a.`    |
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
        igStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, igStake)
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
                
                w.add("H", entryPool[immut][0])
        
        w.stakeCurrentWithValue(etStake)
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        glyphPool = []
        
        for entryIndex, entryObj in it:
            w.add("H", revStateMap[entryObj.newState])
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
                
                currIndex = utilities.findSubsequence(glyphPool, cig)
                
                if currIndex is None:
                    currIndex = len(glyphPool)
                    glyphPool.extend(cig)
                
                if entryObj.currentIsKashidaLike:
                    flags |= 0x2000
                
                if entryObj.currentInsertBefore:
                    flags |= 0x0800
                
                flags |= (len(cig) << 5)
            
            else:
                currIndex = 0xFFFF
            
            if mig:
                if len(mig) > 31:
                    raise ValueError("Too many marked insertions!")
                
                markIndex = utilities.findSubsequence(glyphPool, mig)
                
                if markIndex is None:
                    markIndex = len(glyphPool)
                    glyphPool.extend(mig)
                
                if entryObj.markedIsKashidaLike:
                    flags |= 0x1000
                
                if entryObj.markedInsertBefore:
                    flags |= 0x0400
                
                flags |= len(mig)
            
            else:
                markIndex = 0xFFFF
            
            w.add("3H", flags, currIndex, markIndex)
        
        # finally, add the glyph tuples
        
        w.stakeCurrentWithValue(igStake)
        w.addGroup("H", glyphPool)
    
    @classmethod
    def fromglyphdict(cls, d, **kwArgs):
        """
        Given a dict mapping trigger glyphs to to-be-inserted sequences,
        returns an Insertion subtable that does this. This is a simple table,
        with only the two fixed states.
    
        >>> d = {20: (50, 51), 21: (52, 53, 54, 55)}
        >>> Insertion.fromglyphdict(d).pprint(onlySignificant=True)
        State 'Start of text':
          Class 'glyph 20':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 50
              1: 51
            Current insertion is kashida-like: True
            Name of next state: Start of text
          Class 'glyph 21':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 52
              1: 53
              2: 54
              3: 55
            Current insertion is kashida-like: True
            Name of next state: Start of text
        State 'Start of line':
          Class 'glyph 20':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 50
              1: 51
            Current insertion is kashida-like: True
            Name of next state: Start of text
          Class 'glyph 21':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 52
              1: 53
              2: 54
              3: 55
            Current insertion is kashida-like: True
            Name of next state: Start of text
        Class table:
          20: glyph 20
          21: glyph 21
        Mask value: (no data)
        Coverage: (no data)
        """
    
        ct = classtable.ClassTable({g: "glyph %d" % (g,) for g in d})
        sot = staterow_insertion.StateRow()
        entryNOP = entry_insertion.Entry()
        sot["End of text"] = entryNOP
        sot["Out of bounds"] = entryNOP
        sot["Deleted glyph"] = entryNOP
        sot["End of line"] = entryNOP
    
        for g, v in d.items():
            sot["glyph %d" % (g,)] = entry_insertion.Entry(
              currentInsertBefore = False,
              currentInsertGlyphs = glyphtuple.GlyphTupleOutput(v),
              currentIsKashidaLike = True)
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = ct,
          **utilities.filterKWArgs(cls, kwArgs))
        
        r["Start of text"] = sot
        r["Start of line"] = sot
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Insertion object from the specified walker,
        doing source validation. The walker must start at the beginning
        (numClasses) of the state table.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("insertion_fvw")
        >>> fvb = Insertion.fromvalidatedbytes
        >>> d = {
        ...   'coverage': _testingValues[0].coverage,
        ...   'maskValue': 0x00000001,
        ...   'fontGlyphCount': 0x1000,
        ...   'logger': logger}
        >>> obj = fvb(s, **d)
        insertion_fvw.insertion - DEBUG - Walker has 220 remaining bytes.
        insertion_fvw.insertion.clstable - DEBUG - Walker has 32 remaining bytes.
        insertion_fvw.insertion.clstable.binsearch.binsrch header - DEBUG - Walker has 30 remaining bytes.
        
        >>> fvb(s[:9], **d)
        insertion_fvw.insertion - DEBUG - Walker has 9 remaining bytes.
        insertion_fvw.insertion - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("insertion")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 20:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        fgc = utilities.getFontGlyphCount(**kwArgs)
        stBaseOffset = w.getOffset()
        tHeader = w.unpack("5L")
        numClasses, oCT, oSA, oET, oIG = tHeader
        
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
        
        wCT, wSA, wET, wIG = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *tHeader[1:])
        
        rawEntries = wET.unpackRest("4H")
        
        numStates = max(
          int(wSA.length()) // (2 * numClasses),
          1 + max(t[0] for t in rawEntries))
        
        if numStates < 2:
            logger.error((
              'V0725',
              (),
              "The number of states in the state table is less than two. "
              "The two fixed states must always be present."))
            
            return None
        
        rawInsertionGlyphs = wIG.unpackRest("H")
        
        nsObj = namestash.NameStash.readormake_validated(
          w,
          tHeader[1:],
          numStates,
          numClasses)
        
        if nsObj is None:
            return None
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        E = entry_insertion.Entry
        GTO = glyphtuple.GlyphTupleOutput
        entries = [None] * len(rawEntries)
        
        for i, raw in enumerate(rawEntries):
            newStateIndex, flags, currIGIndex, markIGIndex = raw
            currCount = (flags & 0x03E0) >> 5
            markCount = flags & 0x001F
            
            if currCount:
                if currIGIndex == 0xFFFF:
                    logger.error((
                      'V0726',
                      (i,),
                      "The current insert count for entry %d is nonzero "
                      "but the corresponding glyph index is missing."))
                    
                    return None
                
                elif currIGIndex + currCount > len(rawInsertionGlyphs):
                    logger.error((
                      'V0727',
                      (i,),
                      "The sum of the current insert count and the starting "
                      "glyph index for entry %d is beyond the end of the "
                      "insertion glyph array."))
                    
                    return None
                
                t = rawInsertionGlyphs[currIGIndex:currIGIndex+currCount]
            
            else:
                t = []
            
            currGlyphs = GTO(t)
            
            if markCount:
                if markIGIndex == 0xFFFF:
                    logger.error((
                      'V0726',
                      (i,),
                      "The marked insert count for entry %d is nonzero "
                      "but the corresponding glyph index is missing."))
                    
                    return None
                
                elif markIGIndex + markCount > len(rawInsertionGlyphs):
                    logger.error((
                      'V0727',
                      (i,),
                      "The sum of the marked insert count and the starting "
                      "glyph index for entry %d is beyond the end of the "
                      "insertion glyph array."))
                    
                    return None
                
                t = rawInsertionGlyphs[markIGIndex:markIGIndex+markCount]
            
            else:
                t = []
            
            markGlyphs = GTO(t)
            
            entries[i] = E(
              newState = stateNames[newStateIndex],
              mark = bool(flags & 0x8000),
              noAdvance = bool(flags & 0x4000),
              currentIsKashidaLike = bool(flags & 0x2000),
              markedIsKashidaLike = bool(flags & 0x1000),
              currentInsertBefore = bool(flags & 0x0800),
              markedInsertBefore = bool(flags & 0x0400),
              currentInsertGlyphs = currGlyphs,
              markedInsertGlyphs = markGlyphs)
        
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
        
        numClasses, oCT, oSA, oET, oIG = w.unpack("5L")
        
        wCT, wSA, wET, wIG = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          oCT,
          oSA,
          oET,
          oIG)
        
        rawEntries = wET.unpackRest("4H")
        
        numStates = max(
          int(wSA.length()) // (2 * numClasses),
          1 + max(t[0] for t in rawEntries))
        
        rawInsertionGlyphs = wIG.unpackRest("H")
        
        nsObj = namestash.NameStash.readormake(
          w,
          (oCT, oSA, oET, oIG),
          numStates,
          numClasses)
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        E = entry_insertion.Entry
        GTO = glyphtuple.GlyphTupleOutput
        entries = [None] * len(rawEntries)
        
        for i, raw in enumerate(rawEntries):
            newStateIndex, flags, currIGIndex, markIGIndex = raw
            currCount = (flags & 0x03E0) >> 5
            markCount = flags & 0x001F
            
            if currCount:
                t = rawInsertionGlyphs[currIGIndex:currIGIndex+currCount]
            else:
                t = []
            
            currGlyphs = GTO(t)
            
            if markCount:
                t = rawInsertionGlyphs[markIGIndex:markIGIndex+markCount]
            else:
                t = []
            
            markGlyphs = GTO(t)
            
            entries[i] = E(
              newState = stateNames[newStateIndex],
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
        
        rawStateArray = wSA.group("H" * numClasses, numStates)
        
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
            sr = staterow_insertion.StateRow()
            
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
        Renames all state names (as keys in the Insertion object, and as
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
        >>> _testingValues[0].run([12, 41, 62, 45])
        [(None, 96), (0, 12), (1, 41), (2, 62), (3, 45), (None, 97)]
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
            
            toBeInserted = {}  # index -> seq of glyphs to be inserted after it
            
            if e.currentInsertGlyphs:
                if e.currentInsertBefore:
                    if (i - 1) in toBeInserted:
                        raise ValueError("Multiple insertions")
                    
                    toBeInserted[i - 1] = list(e.currentInsertGlyphs)
                
                else:
                    if i in toBeInserted:
                        raise ValueError("Multiple insertions")
                    
                    toBeInserted[i] = list(e.currentInsertGlyphs)
            
            if e.markedInsertGlyphs:
                if e.markedInsertBefore:
                    if (markIndex - 1) in toBeInserted:
                        raise ValueError("Multiple insertions")
                    
                    toBeInserted[markIndex - 1] = list(e.markedInsertGlyphs)
                
                else:
                    if markIndex in toBeInserted:
                        raise ValueError("Multiple insertions")
                    
                    toBeInserted[markIndex] = list(e.markedInsertGlyphs)
            
            for place in sorted(toBeInserted, reverse=True):
                piece = toBeInserted[place]
                piece = [(None, g) for g in piece]
                v[place+1:place+1] = piece
                limit += len(piece)
                
                if place < i:
                    i += len(piece)
            
            currState = e.newState
            
            if not e.noAdvance:
                i += delta
        
        currClass = "End of text"
        e = self[currState][currClass]
        
        if e.mark:
            markIndex = i
        
        toBeInserted = {}  # index -> seq of glyphs to be inserted after it
        
        if e.currentInsertGlyphs:
            if e.currentInsertBefore:
                if (i - 1) in toBeInserted:
                    raise ValueError("Multiple insertions")
                
                toBeInserted[i - 1] = list(e.currentInsertGlyphs)
            
            else:
                if i in toBeInserted:
                    raise ValueError("Multiple insertions")
                
                toBeInserted[i] = list(e.currentInsertGlyphs)
        
        if e.markedInsertGlyphs:
            if e.markedInsertBefore:
                if (markIndex - 1) in toBeInserted:
                    raise ValueError("Multiple insertions")
                
                toBeInserted[markIndex - 1] = list(e.markedInsertGlyphs)
            
            else:
                if markIndex in toBeInserted:
                    raise ValueError("Multiple insertions")
                
                toBeInserted[markIndex] = list(e.markedInsertGlyphs)
        
        for place in sorted(toBeInserted, reverse=True):
            piece = toBeInserted[place]
            piece = [(None, g) for g in piece]
            v[place+1:place+1] = piece
        
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
