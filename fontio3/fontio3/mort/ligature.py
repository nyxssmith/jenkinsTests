#
# ligature.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ligature (type 2) subtables in a 'mort' table.
"""

# System imports
import functools
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.mort import (
  classtable,
  entry_ligature,
  glyphtuple,
  ligatureanalyzer,
  staterow_ligature)

from fontio3.statetables import namestash, stutils
from fontio3.utilities import span

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

class Ligature(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire ligature subtables. These are dicts mapping
    state name strings to staterow_ligature.StateRow objects.
    
    >>> _makeObj().pprint(namer=_testNamer)
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
    State 'Start of line':
      Class 'f':
        Remember this glyph, then go to state 'Saw f'
      Class 'o':
        Remember this glyph, then go to state 'Saw o'
    State 'Start of text':
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
        item_pprintlabelfunc = (lambda k: "State '%s'" % (k,)))
    
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
    
    kind = 2  # class constant
    
    #
    # Methods
    #

    def _explodeEntry(self, gtd, laPool, cpPool, lgPool):
        """
        laPool is a list of (last, store, glyph, cpByteOffset) tuples. These
        are all offsets relative to cpStake.
        
        cpPool is a dict mapping cpByteOffset to (addLGBase?, lgByteOffset)
        pairs.
        
        lgPool is the ligature pool.
        """
        
        laCount, inGroups = self._explodeEntry_validate(gtd)
        inGroups = [sorted(s) for s in inGroups]
        
        # Add the ligatures
        theseLigs = [gtd[t][0] for t in itertools.product(*inGroups)]
        lgIndex = utilities.findSubsequence(lgPool, theseLigs)
        
        if lgIndex is None:
            ligBase = 2 * len(lgPool)
            lgPool.extend(theseLigs)
        
        else:
            ligBase = 2 * lgIndex
        
        # Add the component offsets
        needLGBase = True
        multiplier = 2  # granularity is a single short
        cpBases = [None] * len(inGroups)
        
        for j, subList in utilities.enumerateBackwards(inGroups):
            #subListRange = subList[-1] - subList[0] + 1
            cpBaseOffset = self._explodeEntry_findCPRoom(cpPool, subList)
            cpBases[j] = cpBaseOffset
            
            for i, glyph in enumerate(subList):
                value = (needLGBase, ligBase + (multiplier * i))
                offset = cpBaseOffset + (glyph - subList[0]) * 2
                assert offset not in cpPool
                cpPool[offset] = value
            
            ligBase = 0
            needLGBase = False
            multiplier *= len(subList)
        
        # Add the ligActions
        for i, subList in utilities.enumerateBackwards(inGroups):
            t = (i == 0, False, subList[0], cpBases[i])
            laPool.append(t)
    
    @staticmethod
    def _explodeEntry_findCPRoom(cpPool, glyphs):
        minGlyph = min(glyphs)
        news = {(i - minGlyph) * 2 for i in glyphs}
        olds = set(cpPool)
        
        while news & olds:
            news = {i + 2 for i in news}
        
        return min(news)
    
    @staticmethod
    def _explodeEntry_validate(d):
        """
        Most generic case:
        (a, m, x) -> (amx, None, None)
        (a, m, z) -> (amz, None, None)
        (a, n, x) -> (anx, nSpecial, None)
        (a, n, y) -> (any, None, None)
        (a, n, z) -> (anz, None, None)
        (b, m, x) -> (bmx, None, None)
        (b, m, y) -> (bmy, None, None)
        (b, m, z) -> (bmz, None, None)
        
        Theoretically, this could result from a Saw_ab, Saw_mn, Saw_xyz series
        of transitions, which means we're at the last position and have this
        entire dict to transcribe. How to do it? One way: fill in the gaps:
        
        (a, m, x) -> (amx, None, None)
        (a, m, y) -> (a, m, y)                  Synthetic
        (a, m, z) -> (amz, None, None)
        (a, n, x) -> (anx, nSpecial, None)
        (a, n, y) -> (any, None, None)
        (a, n, z) -> (anz, None, None)
        (b, m, x) -> (bmx, None, None)
        (b, m, y) -> (bmy, None, None)
        (b, m, z) -> (bmz, None, None)
        (b, n, x) -> (b, n, x)                  Synthetic
        (b, n, y) -> (b, n, y)                  Synthetic
        (b, n, z) -> (b, n, z)                  Synthetic
        
        This would require stores for all three positions, which means the
        missing glyph would have to be explicitly stored. This might be a
        problem, since the ligated glyphs are pushed back onto the stack.
        
        In terms of ligature offsets, these then break down as follows:
        x  y  z  ->  0  1  2, leaves x3
        m  n  -->  0  3, leaves x2x3 = x6
        a  b  -->  0  6
        
        The problem is that the above only works for the pure ligature case,
        and not for the intermediate store case. There is no way I can see to
        do a store on the stack top 'y', for example, that chooses 'y' in some
        cases and the deleted glyph in others.
        
        For these reasons, this validation method checks not only that the keys
        and values in d all have the same length, but it also does two extra
        checks:
        
            1.  That all input sequences are combinatorially complete; and
            2.  That all output sequences are (non-None, None, None...)
        
        It's not a total loss; if a client wishes to do something like the
        (a, n, x) -> (anx, nSpecial, None) line above, it can be done by a
        following contextual pass.
        """
        
        # Check that all keys and values have the same length
        lenSet = set(len(obj) for part in (d, d.values()) for obj in part)
        
        if len(lenSet) != 1:
            raise ValueError("Inconsistent lengths in GlyphTupleDict!")
        
        # Check that all keys are combinatorially complete
        count = lenSet.pop()
        v = [set() for i in range(count)]
        
        for key in d:
            for i, glyph in enumerate(key):
                v[i].add(glyph)
        
        if len(d) != functools.reduce(operator.mul, (len(s) for s in v)):
            raise ValueError(
              "GlyphTupleDict keys not combinatorially complete!")
        
        for obj in d.values():
            if (obj[0] is None) or any(x is not None for x in obj[1:]):
                raise ValueError(
                  "GlyphTupleDict values not in canonical form!")
        
        return count, v
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Ligature object to the specified writer.
        
        >>> utilities.hexdump(_makeObj().binaryString())
               0 | 000A 0056 0068 00C2  00F0 0128 0148 FEED |...V.h.....(.H..|
              10 | 0006 0163 0165 0166  0169 016C 016F 0007 |...c.e.f.i.l.o..|
              20 | 0553 6177 2066 0653  6177 2066 6605 5361 |.Saw f.Saw ff.Sa|
              30 | 7720 6F06 5361 7720  6F66 0753 6177 206F |w o.Saw of.Saw o|
              40 | 6666 0853 6177 206F  6666 6909 5361 7720 |ff.Saw offi.Saw |
              50 | 6F66 6669 6300 0046  000D 0401 0506 0101 |offic..F........|
              60 | 0701 0108 0101 0900  0000 0000 0000 0100 |................|
              70 | 0002 0000 0000 0000  0100 0002 0000 0000 |................|
              80 | 0000 0304 0402 0000  0000 0000 0105 0502 |................|
              90 | 0000 0000 0000 0600  0002 0000 0000 0000 |................|
              A0 | 0704 0402 0000 0000  0000 0108 0502 0000 |................|
              B0 | 0000 0900 0100 0002  0000 0000 000A 0100 |................|
              C0 | 0002 0068 0000 007C  8000 0090 8000 0086 |...h...|........|
              D0 | 80F0 0068 80F8 0068  8100 009A 8000 00A4 |...h...h........|
              E0 | 8108 00AE 8110 00B8  8000 0068 8118 0000 |...........h....|
              F0 | 0000 004B 8000 004C  0000 004A 8000 004E |...K...L...J...N|
             100 | 0000 004C BFFF FF50  0000 0053 8000 0054 |...L...P...S...T|
             110 | 0000 0052 BFFF FF55  0000 0058 0000 005B |...R...U...X...[|
             120 | 3FFF FF57 8000 0051  0148 0000 014A 0000 |?..W...Q.H...J..|
             130 | 014E 014C 0000 0150  0148 0000 014E 0000 |.N.L...P.H...N..|
             140 | 0152 0000 0000 0000  014A 00C0 00C1 014B |.R.......J.....K|
             150 | 014C 0369                                |.L.i            |
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
        laStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, laStake)
        cpStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, cpStake)
        lgStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, lgStake)
        kwArgs.pop('neededAlignment', None)
        kwArgs.pop('classDict', None)
        nsObj.buildBinary(w, neededAlignment=2, **kwArgs)
        
        self.classTable.buildBinary(
          w,
          stakeValue = ctStake,
          classDict = revClassMap,
          **kwArgs)
        
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
        
        # laPool is a list of (last, store, glyph, cpByteOffset) tuples. These
        # are all offsets relative to cpStake.
        
        # cpPool is a dict mapping cpByteOffset to (addLGBase?, lgByteOffset)
        # pairs.
        
        # lgPool is the ligature pool.
        
        laPool = []
        cpPool = {}
        lgPool = []
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        
        for entryIndex, entryObj in it:
            w.addUnresolvedOffset(
              "H",
              stakeValue,
              rowStakes[entryObj.newState])
            
            d = entryObj.actions
            
            if d:
                w.addBitsFromNumber(entryObj.push, 1)
                w.addBitsFromNumber(entryObj.noAdvance, 1)
                
                w.addUnresolvedOffset(
                  "H",
                  stakeValue,
                  laStake,
                  bitLength = 14,
                  offsetByteDelta = 4 * len(laPool))
                
                self._explodeEntry(d, laPool, cpPool, lgPool)
            
            else:
                n = (0x8000 if entryObj.push else 0)
                n += (0x4000 if entryObj.noAdvance else 0)
                w.add("H", n)
        
        w.alignToByteMultiple(4)
        w.stakeCurrentWithValue(laStake)
        
        for last, store, glyph, cpByteOffset in laPool:
            w.addBitsFromNumber(last, 1)
            w.addBitsFromNumber(store, 1)
            
            w.addUnresolvedOffset(
              "L",
              stakeValue,
              cpStake,
              bitLength = 30,
              negOK = True,
              offsetDivisor = 2,
              offsetMultiDelta = (cpByteOffset // 2) - glyph)
        
        w.stakeCurrentWithValue(cpStake)
        
        for cpOffset in range(0, max(cpPool) + 2, 2):
            if cpOffset in cpPool:
                addBase, lgOffset = cpPool[cpOffset]
                
                if addBase:
                    w.addUnresolvedOffset(
                      "H",
                      stakeValue,
                      lgStake,
                      offsetByteDelta = lgOffset)
                
                else:
                    w.add("h", lgOffset)
            
            else:
                w.add("H", 0)
        
        w.stakeCurrentWithValue(lgStake)
        w.addGroup("H", lgPool)
    
    def combinedActions(self):
        """
        Returns a new Ligature object where any cells whose flags and nextState
        values are the same and whose keys are identical except for the last
        glyph have their actions combined into a unified dict. This can reduce
        the total number of entries required, which for a 'mort' table can be
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
        
        >>> origObj = _makeObj()
        >>> s = origObj.binaryString()
        >>> logger = utilities.makeDoctestLogger("ligature_fvw")
        >>> fvb = Ligature.fromvalidatedbytes
        >>> d = {
        ...   'coverage': origObj.coverage,
        ...   'maskValue': 0x00000080,
        ...   'logger': logger}
        >>> obj = fvb(s, **d)
        ligature_fvw.ligature - DEBUG - Walker has 340 remaining bytes.
        ligature_fvw.ligature.namestash - DEBUG - Walker has 326 remaining bytes.
        ligature_fvw.ligature.classtable - DEBUG - Walker has 18 remaining bytes.
        >>> obj == origObj.trimmedToValidEntries()
        True
        
        >>> fvb(s[:9], **d)
        ligature_fvw.ligature - DEBUG - Walker has 9 remaining bytes.
        ligature_fvw.ligature - ERROR - Insufficient bytes.
        
        >>> fvb(s[:20], **d)
        ligature_fvw.ligature - DEBUG - Walker has 20 remaining bytes.
        ligature_fvw.ligature - ERROR - One or more offsets to state table components are outside the bounds of the state table itself.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('ligature')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        analyzer = ligatureanalyzer.Analyzer(w.subWalker(0, relative=True))
        analyzer.analyze(logger=logger)
        
        if analyzer.analysis is None:
            return None
        
        # Note that some of the size and other validation was already done in
        # the analyze() call, and is not reduplicated here.
        
        t = w.unpack("7H")
        numClasses, *offsets = t  # Python 3 only
        oCT, oSA, oET, oLA, oCP, oLG = offsets
    
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
        
        entryPool = {}  # entryIndex -> Entry object
        
        for stateIndex, rawStateRow in enumerate(analyzer.stateArray):
            thisRow = staterow_ligature.StateRow()
            
            for classIndex, rawEntryIndex in enumerate(rawStateRow):
                if rawEntryIndex not in entryPool:
                    newStateOffset, flags = analyzer.entryTable[rawEntryIndex]
                    newStateIndex = (newStateOffset - oSA) // numClasses
                    
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
        
        >>> origObj = _makeObj()
        >>> d = {'coverage': origObj.coverage, 'maskValue': 0x00000080}
        >>> obj = Ligature.frombytes(origObj.binaryString(), **d)
        >>> obj == origObj.trimmedToValidEntries()
        True
        """
        
        analyzer = ligatureanalyzer.Analyzer(w.subWalker(0, relative=True))
        analyzer.analyze()
        numClasses, oCT, oSA, oET, oLA, oCP, oLG = w.unpack("7H")
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
                    newStateOffset, flags = analyzer.entryTable[rawEntryIndex]
                    newStateIndex = (newStateOffset - oSA) // numClasses
                    
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
    from fontio3.mort import coverage, glyphtupledict
    
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
