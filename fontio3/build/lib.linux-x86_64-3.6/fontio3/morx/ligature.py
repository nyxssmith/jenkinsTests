#
# ligature.py
#
# Copyright © 2011-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ligature (type 2) subtables in a 'morx' table.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.morx import (
  classtable,
  entry_ligature,
  glyphtuple,
  ligatureanalyzer,
  staterow_ligature)

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

class Ligature(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire ligature subtables. These are dicts mapping
    state name strings to staterow_ligature.StateRow objects.
    
    >>> _makeObj().pprint(namer=_testNamer, onlySignificant=True)
    State 'Start of text':
      Class 'f':
        Remember this glyph, then go to state 'Saw f'
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Start of line':
      Class 'f':
        Remember this glyph, then go to state 'Saw f'
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Saw f':
      Class 'f':
        Remember this glyph, then go to state 'Saw ff' after doing these substitutions:
          (letter f, letter f) becomes (ligature ff, None)
      Class 'i':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (letter f, letter i) becomes (ligature fi, None)
          (letter f, letter l) becomes (ligature fl, None)
      Class 'l':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (letter f, letter i) becomes (ligature fi, None)
          (letter f, letter l) becomes (ligature fl, None)
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Saw ff':
      Class 'f':
        Remember this glyph, then go to state 'Saw f'
      Class 'i':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (ligature ff, letter i) becomes (ligature ffi, None)
          (ligature ff, letter l) becomes (ligature ffl, None)
      Class 'l':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (ligature ff, letter i) becomes (ligature ffi, None)
          (ligature ff, letter l) becomes (ligature ffl, None)
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Saw o':
      Class 'f':
        Remember this glyph, then go to state 'Saw of'
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Saw of':
      Class 'f':
        Remember this glyph, then go to state 'Saw off' after doing these substitutions:
          (letter f, letter f) becomes (ligature ff, None)
      Class 'i':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (letter f, letter i) becomes (ligature fi, None)
          (letter f, letter l) becomes (ligature fl, None)
      Class 'l':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (letter f, letter i) becomes (ligature fi, None)
          (letter f, letter l) becomes (ligature fl, None)
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Saw off':
      Class 'f':
        Remember this glyph, then go to state 'Saw f'
      Class 'i':
        Remember this glyph, then go to state 'Saw offi' after doing these substitutions:
          (ligature ff, letter i) becomes (ligature ffi, None)
      Class 'l':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (ligature ff, letter i) becomes (ligature ffi, None)
          (ligature ff, letter l) becomes (ligature ffl, None)
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Saw offi':
      Class 'c':
        Remember this glyph, then go to state 'Saw offic'
      Class 'f':
        Remember this glyph, then go to state 'Saw f'
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Saw offic':
      Class 'e':
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (letter o, ligature ffi, letter c, letter e) becomes (special ligature office, None, None, None)
      Class 'f':
        Remember this glyph, then go to state 'Saw f'
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    Class table:
      letter c: c
      letter e: e
      letter f: f
      letter i: i
      letter l: l
      letter o: o
    Mask value: 00000080
    Coverage:
      Process in both orientations
      Subtable kind: 2
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
    kind = 2  # class constant
    
    #
    # Methods
    #
    
    def __bool__(self):
        """
        Special-case for state tables: both the dict itself AND the classTable
        need to be non-empty, AND there needs to be at least one non-empty
        action in an Entry.
        """
        
        return (
          (len(self) > 0) and
          ('Start of text' in self) and
          (len(self['Start of text']) > 0) and
          (len(self.classTable) > 0) and
          any(
            bool(cell.actions)
            for row in self.values()
            for cell in row.values()))
    
    def _explode(self, d, laList, cpDict, lgDict):
        # Validate
        inGroups = self._explode_validate(d)
        
        # Do ligs
        ligs = [d.get(t, [None])[0] for t in itertools.product(*inGroups)]
        tryDict = {i: lig for i, lig in enumerate(ligs) if lig is not None}
        puzzleSet = utilities.puzzleFit(lgDict, tryDict)
        ligBase = min(puzzleSet)
        
        if not (set(lgDict) & puzzleSet):
            # not reusing, so put the new values into lgDict
            for i, lig in enumerate(ligs, start=ligBase):
                if lig is not None:
                    lgDict[i] = lig
        
        # Do comps
        multiplier = 1
        cpBases = {}
        
        for partsIndex, parts in utilities.enumerateBackwards(inGroups):
            b = cpBases[partsIndex] = min(
              utilities.puzzleFit(cpDict, set(parts)))
            
            if partsIndex:
                for i, g in enumerate(parts):
                    cpDict[g - parts[0] + b] = multiplier * i
            
            else:
                for i, g in enumerate(parts):
                    cpDict[g - parts[0] + b] = ligBase + multiplier * i
            
            multiplier *= len(parts)
        
        # Do lig actions
        for partsIndex, parts in utilities.enumerateBackwards(inGroups):
            laList.append((partsIndex == 0, cpBases[partsIndex] - parts[0]))
    
    @staticmethod
    def _explode_validate(d):
        lenSet = set(len(obj) for part in (d, d.values()) for obj in part)
        
        if len(lenSet) != 1:
            raise ValueError("Inconsistent lengths in GlyphTupleDict!")
        
        v = [set() for i in range(lenSet.pop())]
        
        for key in d:
            for i, glyph in enumerate(key):
                v[i].add(glyph)
        
        for obj in d.values():
            if (obj[0] is None) or any(x is not None for x in obj[1:]):
                raise ValueError(
                  "GlyphTupleDict values not in canonical form!")
        
        return [sorted(s) for s in v]
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Ligature object to the specified writer.
        
        >>> utilities.hexdump(_makeObj().binaryString())
               0 | 0000 000A 0000 0064  0000 0084 0000 0138 |.......d.......8|
              10 | 0000 017C 0000 01B4  0000 01D6 FEED 0006 |...|............|
              20 | 0163 0165 0166 0169  016C 016F 0007 0553 |.c.e.f.i.l.o...S|
              30 | 6177 2066 0653 6177  2066 6605 5361 7720 |aw f.Saw ff.Saw |
              40 | 6F06 5361 7720 6F66  0753 6177 206F 6666 |o.Saw of.Saw off|
              50 | 0853 6177 206F 6666  6909 5361 7720 6F66 |.Saw offi.Saw of|
              60 | 6669 6300 0008 0046  000D 0004 0001 0005 |fic....F........|
              70 | 0006 0001 0001 0007  0001 0001 0008 0001 |................|
              80 | 0001 0009 0000 0000  0000 0000 0000 0000 |................|
              90 | 0001 0000 0000 0002  0000 0000 0000 0000 |................|
              A0 | 0000 0000 0001 0000  0000 0002 0000 0000 |................|
              B0 | 0000 0000 0000 0000  0003 0004 0004 0002 |................|
              C0 | 0000 0000 0000 0000  0000 0000 0001 0005 |................|
              D0 | 0005 0002 0000 0000  0000 0000 0000 0000 |................|
              E0 | 0006 0000 0000 0002  0000 0000 0000 0000 |................|
              F0 | 0000 0000 0007 0004  0004 0002 0000 0000 |................|
             100 | 0000 0000 0000 0000  0001 0008 0005 0002 |................|
             110 | 0000 0000 0000 0000  0009 0000 0001 0000 |................|
             120 | 0000 0002 0000 0000  0000 0000 0000 000A |................|
             130 | 0001 0000 0000 0002  0000 0000 0000 0002 |................|
             140 | 8000 0000 0004 8000  0000 0003 A000 0000 |................|
             150 | 0000 A000 0002 0000  A000 0004 0005 8000 |................|
             160 | 0000 0006 A000 0006  0007 A000 0008 0008 |................|
             170 | 8000 0000 0000 A000  000A 0000 3FFF FFB8 |............?...|
             180 | BFFF FFB9 3FFF FFB7  BFFF FFBB 3FFF FFB9 |....?.......?...|
             190 | BFFF FEBD 3FFF FFC0  BFFF FFC1 3FFF FFBF |....?.......?...|
             1A0 | BFFF FEC2 3FFF FFC5  3FFF FFC8 3FFF FEC4 |....?...?...?...|
             1B0 | BFFF FFBE 0000 0000  0000 0000 0001 0000 |................|
             1C0 | 0001 0003 0001 0000  0000 0000 0003 0000 |................|
             1D0 | 0000 0000 0005 014A  00C0 00C1 014B 014C |.......J.....K.L|
             1E0 | 0369                                     |.i              |
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
        w.add("L", len(classNames))
        ctStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, ctStake)
        saStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, saStake)
        etStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, etStake)
        laStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, laStake)
        cpStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, cpStake)
        lgStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, lgStake)
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
                cell = row[className]
                immut = cell.asImmutable()
                
                if immut not in entryPool:
                    entryPool[immut] = (len(entryPool), cell)
                
                w.add("H", entryPool[immut][0])
        
        w.stakeCurrentWithValue(etStake)
        laList = []
        cpDict = {0: 0}
        lgDict = {}
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        
        for entryIndex, entryObj in it:
            w.add("H", revStateMap[entryObj.newState])
            flags = (0x8000 if entryObj.push else 0)
            flags += (0x4000 if entryObj.noAdvance else 0)
            flags += (0x2000 if entryObj.actions else 0)
            w.add("H", flags)
            
            if entryObj.actions:
                w.add("H", len(laList))
                self._explode(entryObj.actions, laList, cpDict, lgDict)
            
            else:
                w.add("H", 0)
        
        w.alignToByteMultiple(4)
        w.stakeCurrentWithValue(laStake)
        
        for isLast, n in laList:
            n = (n % 0x100000000) & 0x3FFFFFFF
            
            if isLast:
                n |= 0x80000000
            
            w.add("L", n)
        
        w.stakeCurrentWithValue(cpStake)
        
        for i in range(max(cpDict) + 1):
            w.add("H", cpDict.get(i, 0))
        
        w.stakeCurrentWithValue(lgStake)
        
        for i in range(max(lgDict) + 1):
            w.add("H", lgDict.get(i, 0))
    
    def combinedActions(self):
        """
        Returns a new Ligature object where any cells whose flags and nextState
        values are the same and whose keys are identical except for the last
        glyph have their actions combined into a unified dict. This can reduce
        the total number of entries required, which for a 'morx' table can be
        very useful since the limit is 8 bits.
        """
        
        dNew = type(self)(
          coverage = self.coverage.__copy__(),
          classTable = self.classTable.__copy__(),
          maskValue = self.maskValue)
        
        for stateName, row in self.items():
            dNew[stateName] = row.combinedActions()
        
        return dNew
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Ligature object from the specified walker,
        doing source validation. The walker should be based at the state table
        start (i.e. at numClasses).
        
        >>> origObj = _makeObj().trimmedToValidEntries()
        >>> s = origObj.binaryString()
        >>> logger = utilities.makeDoctestLogger("ligature_fvw")
        >>> fvb = Ligature.fromvalidatedbytes
        >>> d = {
        ...   'coverage': origObj.coverage,
        ...   'maskValue': 0x00000080,
        ...   'logger': logger,
        ...   'fontGlyphCount': 0x1000}
        >>> obj = fvb(s, **d)
        ligature_fvw.ligature - DEBUG - Walker has 514 remaining bytes.
        ligature_fvw.ligature.lookup_aat - DEBUG - Walker has 32 remaining bytes.
        ligature_fvw.ligature - WARNING - The entry for state 2, class 6 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature - WARNING - The entry for state 5, class 6 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature - WARNING - The entry for state 6, class 7 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature - WARNING - The entry for state 2, class 6 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature - WARNING - The entry for state 2, class 6 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature - WARNING - The entry for state 2, class 6 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature - WARNING - The entry for state 2, class 6 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature - WARNING - The entry for state 2, class 6 does ligature substitution, but does not lead back to the ground state. This might be problematic.
        ligature_fvw.ligature.namestash - DEBUG - Walker has 486 remaining bytes.
        ligature_fvw.ligature.clstable - DEBUG - Walker has 32 remaining bytes.
        >>> obj == origObj
        True
        
        >>> fvb(s[:19], **d)
        ligature_fvw.ligature - DEBUG - Walker has 19 remaining bytes.
        ligature_fvw.ligature - ERROR - Insufficient bytes.
        
        >>> fvb(s[:39], **d)
        ligature_fvw.ligature - DEBUG - Walker has 39 remaining bytes.
        ligature_fvw.ligature - ERROR - One or more offsets to state table components are outside the bounds of the state table itself.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('ligature')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        analyzer = ligatureanalyzer.Analyzer(w.subWalker(0, relative=True))
        analyzer.analyze(logger=logger, **kwArgs)
        
        if analyzer.analysis is None:
            return None
        
        # Note that some of the size and other validation was already done in
        # the analyze() call, and is not reduplicated here.
        
        numClasses, oCT, oSA, oET, oLA, oCP, oLG = w.unpack("7L")
        offsets = (oCT, oSA, oET, oLA, oCP, oLG)
        
        wCT, wSA, wET, wLA, wCP, wLG = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *offsets)
        
        numStates = analyzer.numStates
        
        nsObj = namestash.NameStash.readormake_validated(
          w,
          offsets,
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
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        entryPool = {}  # entryIndex -> Entry object
        
        for stateIndex, rawStateRow in enumerate(analyzer.stateArray):
            thisRow = staterow_ligature.StateRow()
            
            for classIndex, rawEntryIndex in enumerate(rawStateRow):
                if rawEntryIndex not in entryPool:
                    t = analyzer.entryTable[rawEntryIndex]
                    newStateIndex, flags, laIndex = t
                    
                    entryPool[rawEntryIndex] = entry_ligature.Entry(
                      newState = stateNames[newStateIndex],
                      push = bool(flags & 0x8000),
                      noAdvance = bool(flags & 0x4000))
                
                e = entryPool[rawEntryIndex]
                d = analyzer.finalDicts.get((stateIndex, classIndex), None)
                
                if d is not None:
                    for inGlyphs, outGlyphs in d.items():
                        gti = glyphtuple.GlyphTupleInput(inGlyphs)
                        
                        if gti not in e.actions:
                            gto = glyphtuple.GlyphTupleOutput(outGlyphs)
                            e.actions[gti] = gto
                
                thisRow[classNames[classIndex]] = e
            
            r[stateNames[stateIndex]] = thisRow
        
        return r.trimmedToValidEntries()
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Ligature object from the specified walker,
        which should be based at the state header start (numClasses).
        
        >>> origObj = _makeObj().trimmedToValidEntries()
        >>> d = {'coverage': origObj.coverage, 'maskValue': 0x00000080}
        >>> obj = Ligature.frombytes(origObj.binaryString(), **d)
        >>> obj == origObj
        True
        """
        
        analyzer = ligatureanalyzer.Analyzer(w.subWalker(0, relative=True))
        analyzer.analyze(**kwArgs)
        numClasses, oCT, oSA, oET, oLA, oCP, oLG = w.unpack("7L")
        offsets = (oCT, oSA, oET, oLA, oCP, oLG)
        
        wCT, wSA, wET, wLA, wCP, wLG = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *offsets)
        
        numStates = analyzer.numStates
        
        nsObj = namestash.NameStash.readormake(
          w,
          offsets,
          numStates,
          numClasses)
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        
        classTable = classtable.ClassTable.fromwalker(
          wCT,
          classNames = classNames)
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        entryPool = {}  # entryIndex -> Entry object
        
        for stateIndex, rawStateRow in enumerate(analyzer.stateArray):
            thisRow = staterow_ligature.StateRow()
            
            for classIndex, rawEntryIndex in enumerate(rawStateRow):
                if rawEntryIndex not in entryPool:
                    t = analyzer.entryTable[rawEntryIndex]
                    newStateIndex, flags, laIndex = t
                    
                    entryPool[rawEntryIndex] = entry_ligature.Entry(
                      newState = stateNames[newStateIndex],
                      push = bool(flags & 0x8000),
                      noAdvance = bool(flags & 0x4000))
                
                e = entryPool[rawEntryIndex]
                d = analyzer.finalDicts.get((stateIndex, classIndex), None)
                
                if d is not None:
                    for inGlyphs, outGlyphs in d.items():
                        gti = glyphtuple.GlyphTupleInput(inGlyphs)
                        
                        if gti not in e.actions:
                            gto = glyphtuple.GlyphTupleOutput(outGlyphs)
                            e.actions[gti] = gto
                
                thisRow[classNames[classIndex]] = e
            
            r[stateNames[stateIndex]] = thisRow
        
        return r.trimmedToValidEntries()
    
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
            sr = staterow_ligature.StateRow()
            
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
        >>> _makeObj().run([82, 73, 73, 76, 70, 72])
        [(0, 873), (1, None), (2, None), (3, None), (4, None), (5, None)]
        """
        
        currState = kwArgs.get('startState', 'Start of text')
        
        if not isinstance(glyphArray[0], tuple):
            v = list(enumerate(glyphArray))
        else:
            v = list(glyphArray)
        
        stack = []
        
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
            
            if e.push:
                stack.append((i, currGlyph))
            
            if e.actions:
                cands = []
                
                for inTuple, outTuple in e.actions.items():
                    if inTuple == tuple(t[1] for t in stack[-len(inTuple):]):
                        cands.append(outTuple)
                
                if cands:
                    if len(cands) > 1:
                        raise ValueError()
                    
                    outTuple = cands[0]
                    stackPiece = stack[-len(outTuple):]
                    del stack[-len(outTuple):]
                    
                    for vPart, outGlyph in zip(stackPiece, outTuple):
                        v[vPart[0]] = (v[vPart[0]][0], outGlyph)
                        
                        if outGlyph not in {0xFFFF, 0xFFFE, None}:
                            stack.append((vPart[0], outGlyph))
            
            currState = e.newState
            
            if not e.noAdvance:
                i += delta
        
        currClass = "End of text"
        e = self[currState][currClass]
        
        if e.push:
            stack.append((i, currGlyph))
        
        if e.actions:
            cands = []
            
            for inTuple, outTuple in e.actions.items():
                if inTuple == tuple(t[1] for t in stack[-len(inTuple):]):
                    cands.append(outTuple)
            
            if cands:
                if len(cands) > 1:
                    raise ValueError()
                
                outTuple = cands[0]
                stackPiece = stack[-len(outTuple):]
                del stack[-len(outTuple):]
                
                for vPart, outGlyph in zip(stackPiece, outTuple):
                    v[vPart[0]] = (v[vPart[0][0]], outGlyph)
                    
                    if outGlyph not in {0xFFFF, 0xFFFE, None}:
                        stack.append((vPart[0], outGlyph))
        
        return v
    
    def trimmedToValidEntries(self):
        """
        """
        
        dNew = type(self)(
          coverage = self.coverage.__copy__(),
          classTable = self.classTable.__copy__(),
          maskValue = self.maskValue)
        
        for stateName, row in self.items():
            dNew[stateName] = row.trimmedToValidEntries(self.classTable)
        
        return dNew

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.morx import coverage, glyphtupledict
    
    def _makeObj():
        GLYPH_c = 70
        GLYPH_e = 72
        GLYPH_f = 73
        GLYPH_i = 76
        GLYPH_l = 79
        GLYPH_o = 82
        GLYPH_fi = 192
        GLYPH_fl = 193
        GLYPH_ff = 330
        GLYPH_ffi = 331
        GLYPH_ffl = 332
        GLYPH_special = 873
        
        Entry = entry_ligature.Entry
        GTD = glyphtupledict.GlyphTupleDict
        GTI = glyphtuple.GlyphTupleInput
        GTO = glyphtuple.GlyphTupleOutput
        StateRow = staterow_ligature.StateRow
        
        classTable = classtable.ClassTable({
            GLYPH_c: "c",
            GLYPH_e: "e",
            GLYPH_f: "f",
            GLYPH_i: "i",
            GLYPH_l: "l",
            GLYPH_o: "o"})
        
        cov = coverage.Coverage(always=True, kind=2)
        
        entry0 = Entry(
            newState = "Start of text")
        
        entry1 = Entry(
            newState = "Saw f",
            push = True)
        
        entry2 = Entry(
            newState = "Saw o",
            push = True)
        
        entry3 = Entry(
            newState = "Saw ff",
            push = True,
            actions = GTD({
                GTI((GLYPH_f, GLYPH_f)): GTO((GLYPH_ff, None))}))
        
        entry4 = Entry(
            newState = "Start of text",
            push = True,
            actions = GTD({
                GTI((GLYPH_f, GLYPH_i)): GTO((GLYPH_fi, None)),
                GTI((GLYPH_f, GLYPH_l)): GTO((GLYPH_fl, None))}))
        
        entry5 = Entry(
            newState = "Start of text",
            push = True,
            actions = GTD({
                GTI((GLYPH_ff, GLYPH_i)): GTO((GLYPH_ffi, None)),
                GTI((GLYPH_ff, GLYPH_l)): GTO((GLYPH_ffl, None))}))
        
        entry6 = Entry(
            newState = "Saw of",
            push = True)
        
        entry7 = Entry(
            newState = "Saw off",
            push = True,
            actions = GTD({
                GTI((GLYPH_f, GLYPH_f)): GTO((GLYPH_ff, None))}))
        
        entry8 = Entry(
            newState = "Saw offi",
            push = True,
            actions = GTD({
                GTI((GLYPH_ff, GLYPH_i)): GTO((GLYPH_ffi, None))}))
        
        entry9 = Entry(
            newState = "Saw offic",
            push = True)
        
        entry10 = Entry(
            newState = "Start of text",
            push = True,
            actions = GTD({
                GTI((GLYPH_o, GLYPH_ffi, GLYPH_c, GLYPH_e)):
                GTO((GLYPH_special, None, None, None))}))
        
        row_SOT = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry0,
            "f": entry1,
            "i": entry0,
            "l": entry0,
            "o": entry2})
        
        row_SOL = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry0,
            "f": entry1,
            "i": entry0,
            "l": entry0,
            "o": entry2})
        
        row_Sawf = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry0,
            "f": entry3,
            "i": entry4,
            "l": entry4,
            "o": entry2})
        
        row_Sawff = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry0,
            "f": entry1,
            "i": entry5,
            "l": entry5,
            "o": entry2})
        
        row_Sawo = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry0,
            "f": entry6,
            "i": entry0,
            "l": entry0,
            "o": entry2})
        
        row_Sawof = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry0,
            "f": entry7,
            "i": entry4,
            "l": entry4,
            "o": entry2})
        
        row_Sawoff = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry0,
            "f": entry1,
            "i": entry8,
            "l": entry5,
            "o": entry2})
        
        row_Sawoffi = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry9,
            "e": entry0,
            "f": entry1,
            "i": entry0,
            "l": entry0,
            "o": entry2})
        
        row_Sawoffic = StateRow({
            "End of text": entry0,
            "Out of bounds": entry0,
            "Deleted glyph": entry0,
            "End of line": entry0,
            "c": entry0,
            "e": entry10,
            "f": entry1,
            "i": entry0,
            "l": entry0,
            "o": entry2})
        
        ligTable = Ligature(
            {
                "Start of text": row_SOT,
                "Start of line": row_SOL,
                "Saw f": row_Sawf,
                "Saw ff": row_Sawff,
                "Saw o": row_Sawo,
                "Saw of": row_Sawof,
                "Saw off": row_Sawoff,
                "Saw offi": row_Sawoffi,
                "Saw offic": row_Sawoffic},
            coverage = cov,
            maskValue = 0x00000080,
            classTable = classTable)
        
        return ligTable
    
    class _TestNamer:
        _names = {
          None: None,
          70: "letter c",
          72: "letter e",
          73: "letter f",
          76: "letter i",
          79: "letter l",
          82: "letter o",
          192: "ligature fi",
          193: "ligature fl",
          330: "ligature ff",
          331: "ligature ffi",
          332: "ligature ffl",
          873: "special ligature office"}
        
        def bestNameForGlyphIndex(self, glyphIndex, **kwArgs):
            return self._names[glyphIndex]
    
    _testNamer = _TestNamer()

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
