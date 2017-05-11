#
# ligature.py
#
# Copyright © 2007-2010, 2012-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 4 (Ligature Substitution) subtables for a GSUB table.
"""

# System imports
import collections
import functools
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta, seqmeta
from fontio3.GSUB import ligature_glyphtuple
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import coverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Constants
#

GT = ligature_glyphtuple.Ligature_GlyphTuple

# -----------------------------------------------------------------------------

#
# Private functions
#

@functools.cmp_to_key
def _canonicalCompare(x, y):
    if len(x) == len(y):
        if x == y:
            return 0
        elif x > y:
            return 1
        else:
            return -1
    
    elif len(x) > len(y):
        a = x[:len(y)]
        
        if a > y:
            return 1
        else:
            return -1
    
    else:
        b = y[:len(x)]
        
        if x >= b:
            return 1
        else:
            return -1

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    invDict = utilities.invertDictFull(obj, asSets=True)
    
    for ligGlyph, inSeqs in invDict.items():
        if len(inSeqs) > 1:
            logger.info((
              'V0445',
              (ligGlyph, inSeqs),
              "Ligature glyph %d can be made in the "
              "following different ways: %s."))
    
    return True

# -----------------------------------------------------------------------------

#
# Private classes
#

if 0:
    def __________________(): pass

class _GlyphList(list, metaclass=seqmeta.FontDataMetaclass):
    """
    This is used to construct the Ligature's keyOrder, which is a list of
    tuples of glyph indices.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True)
    
    #
    # Methods
    #
    
    def doCanonicalKeyOrdering(self):
        """
        This method sorts a list of tuples of glyph indices in ascending
        numeric order with the special case that longer sequences precede
        shorter sequences if the overlap in the sequence matches.  This ensures
        that a ligature like "ffi" will be formed even if there is a shorter
        ligature like "ff" in the list.
        
        >>> obj = _GlyphList([(3,4), (1,2,3,4), (1,2), (1,2,3), (3,4,5)])
        >>> obj.doCanonicalKeyOrdering()
        >>> obj
        _GlyphList([(1, 2, 3, 4), (1, 2, 3), (1, 2), (3, 4, 5), (3, 4)])
        """

        self.sort(key=_canonicalCompare)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Ligature(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Ligature substitution subtables for a GSUB table. These are dicts whose keys
    are GlyphTuples and whose values are glyph indices. There is one attribute:
    
        keyOrder    A list of keys for the dict in their order of application.
                    Note that this class has a custom __iter__() method that
                    guarantees the keys will always be produced in an order
                    that respects this keyOrder list; see the docstring for the
                    __iter__() method for more details.
    
    >>> _testingValues[1].pprint()
    Ligature_GlyphTuple((4, 11, 29)): 97
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    (xyz5, xyz12, xyz30): afii60002
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    (xyz6, xyz10): xyz33
    (xyz6, xyz4): xyz32
    (xyz12, xyz13): xyz14
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelnosort = True,  # we have a custom __iter__()
        item_renumberdeepkeysnoshrink = True,
        item_renumberdirectvalues = True,
        item_usenamerforstr = True,
        item_valueisoutputglyph = True,
        map_maxcontextfunc = (lambda d: utilities.safeMax(len(k) for k in d)),
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        keyOrder = dict(
            attr_followsprotocol = True,
            attr_ignoreforcomparisons = True,
            attr_initfunc = _GlyphList))
    
    attrSorted = ()
    
    kind = ('GSUB', 4)
    kindString = "Ligature substitution table"
    
    #
    # Methods
    #
    
    def __iter__(self):
        """
        Returns an iterator over keys. The keys are returned sorted by first
        glyph in the key, and then as specified by the keyOrder list. Any keys
        not present in the keyOrder list will be returned last in their
        respective first-glyph groups.
        
        >>> for k in _testingValues[2]: print(k)
        (5, 9)
        (5, 3)
        (11, 12)
        """
        
        actuals = set(super(Ligature, self).__iter__())
        ko = list(self.keyOrder)
        ko.extend(actuals - set(ko))
        firsts = {k[0] for k in actuals}
        
        for first in sorted(firsts):
            it = (x for x in ko if x[0] == first)
            
            for k, g in itertools.groupby(it, key=operator.itemgetter(0)):
                for obj in g:
                    yield obj
    
    @staticmethod
    def _classTableFromKeyGroup(keyGroup, nm):
        """
        Creates and returns a new ClassTable object based on an analysis of the
        specified keyGroup, which should be a dict mapping input glyph tuples
        to ligature glyphs. This analysis takes into account sharing classes
        for glyphs whose behaviors are similar enough.
        
        Note that partial overlaps should already have been resolved (i.e. the
        keyGroup passed in should have passed a prior _separatedKeys() call)
        before this method is called.
        
        <<< tm = _getTestDataModule()
        <<< ligObj = tm.makeGSUBObj()
        <<< postObj = tm.makePOSTObj()
        <<< vKeyGroups = ligObj._separatedKeys()
        <<< len(vKeyGroups)
        1
        <<< nm = lambda n: postObj[n]
        <<< Ligature._classTableFromKeyGroup(ligObj, nm).pprint()
        4: group candrabindudeva
        5: group candrabindudeva
        11: group iideva
        16: group iideva
        17: group iideva
        19: group iideva
        20: group iideva
        21: group iideva
        22: group iideva
        23: group iideva
        65: group iivowelsigndeva
        70: group iivowelsigndeva
        71: group iivowelsigndeva
        72: group iivowelsigndeva
        73: group iivowelsigndeva
        74: group iivowelsigndeva
        75: group iivowelsigndeva
        76: group iivowelsigndeva
        77: group iivowelsigndeva
        110: group iideva
        122: group iideva
        125: group iideva
        126: group iideva
        128: group iideva
        129: group iideva
        130: group iideva
        131: group iideva
        132: group iideva
        158: group rephdeva
        412: group rephdeva
        """
        
        from fontio3.morx import classtable
        ct = classtable.ClassTable()
        d = {}
        
        for inTuple, lig in keyGroup.items():
            currState = "SOT"
            
            for i, glyph in enumerate(inTuple):
                sr = d.setdefault(currState, {})
                
                if i == (len(inTuple) - 1):
                    t = ("SOT", lig)
                
                else:
                    if i:
                        s = "%s-%d" % (currState, glyph)
                    else:
                        s = "Saw %d" % (glyph,)
                    
                    t = (s, None)
                
                sr[glyph] = t
                currState = t[0]
        
        leafTriggers = {k[-1] for k in keyGroup}
        dTailSames = {}
        
        for trigger in leafTriggers:
            s = {
              stateName
              for stateName, dSub in d.items()
              if (stateName != "SOT") and (trigger in dSub)}
            
            dTailSames.setdefault(frozenset(s), set()).add(trigger)
        
        for tailSameSet in dTailSames.values():
            if len(tailSameSet) == 1:
                trigger = tailSameSet.pop()
                ct[trigger] = nm(trigger)
            
            else:
                s = "group %s" % (nm(min(tailSameSet)),)
                
                for trigger in tailSameSet:
                    ct[trigger] = s
        
        headTriggers = set(d) - {'SOT'}
        dHeadSames = {}
        
        for trigger in headTriggers:
            dSub = d[trigger]
            dHeadSames.setdefault(frozenset(dSub), set()).add(trigger)
        
        for headSameSet in dHeadSames.values():
            if len(headSameSet) > 1:
                glyphs = {int(s[4:]) for s in headSameSet if '-' not in s}
                
                if glyphs:
                    s = "group %s" % (nm(min(glyphs)),)
                    
                    for glyph in glyphs:
                        ct[glyph] = s
        
        allSingleGlyphs = {glyph for key in keyGroup for glyph in key}
        
        for glyph in allSingleGlyphs:
            if glyph not in ct:
                ct[glyph] = nm(glyph)
        
        return ct
    
    def _separatedKeys(self):
        """
        Returns a list of sets of keys. The union of all sets in the list is
        the same as the set of self. The reason for this is to separate keys
        which have potential intersecting effects and to segregate them into
        their own separate AAT ligature table. This is important since AAT does
        not allow control over the ordering in the same way OpenType does, so
        it's possible to have an OpenType Ligature object that cannot be
        represented in a single-pass AAT ligature subtable. For instance, if
        two rules are for "ff" and "ffi", and the "ffi" rule has higher
        priority, AAT cannot just form the "ff" since the "ffi" rule's inputs
        are not ligated, but are just simple glyphs. This results from AAT's
        single-pass approach.
        
        >>> k1 = GT(['f', 'f', 'i'])
        >>> k2 = GT(['f', 'f'])
        >>> Ligature({k1: 30, k2: 40}, keyOrder=[k1, k2])._separatedKeys()
        [[Ligature_GlyphTuple(('f', 'f', 'i'))], [Ligature_GlyphTuple(('f', 'f'))]]
        >>> Ligature({k1: 30, k2: 40}, keyOrder=[k2, k1])._separatedKeys()
        [[Ligature_GlyphTuple(('f', 'f')), Ligature_GlyphTuple(('f', 'f', 'i'))]]
        """
        
        fullList = list(self)  # order is important from obj's __iter__()
        rv = []
    
        while fullList:
            v = []
            startSet = set()
        
            for key in fullList:
                testSet = {key[n:] for n in range(1, len(key))}
            
                if not (testSet & startSet):
                    v.append(key)
                    startSet.update(key[:n] for n in range(1, len(key)))
        
            thisGroup = set(v)
        
            for i in range(len(fullList) - 1, -1, -1):
                if fullList[i] in thisGroup:
                    del fullList[i]
        
            rv.append(v)
    
        return rv
    
    def asAAT(self, **kwArgs):
        """
        Returns a list of AAT 'morx' subtable objects that have the same effect
        as this Ligature object.
        <<<
        <<< tm = _getTestDataModule()
        <<< ligObj = tm.makeGSUBObj()
        <<< v = ligObj.asAAT()
        <<< len(v)
        1
        <<< v[0].pprint(onlySignificant=True)
        State 'Start of text':
          Class 'group glyph 11':
            Remember this glyph, then go to state 'Saw group glyph 11'
          Class 'group glyph 65':
            Remember this glyph, then go to state 'Saw group glyph 65'
        State 'Start of line':
          Class 'group glyph 11':
            Remember this glyph, then go to state 'Saw group glyph 11'
          Class 'group glyph 65':
            Remember this glyph, then go to state 'Saw group glyph 65'
        State 'Saw group glyph 11':
          Class 'group glyph 4':
            Remember this glyph, then go to state 'Start of text' after doing these substitutions:
              (11, 4) becomes (413, None)
              (11, 5) becomes (413, None)
              (16, 4) becomes (414, None)
              (16, 5) becomes (414, None)
              (17, 4) becomes (415, None)
              (17, 5) becomes (415, None)
              (19, 4) becomes (416, None)
              (19, 5) becomes (416, None)
              (20, 4) becomes (417, None)
              (20, 5) becomes (417, None)
              (21, 4) becomes (418, None)
              (21, 5) becomes (418, None)
              (22, 4) becomes (419, None)
              (22, 5) becomes (419, None)
              (23, 4) becomes (420, None)
              (23, 5) becomes (420, None)
              (110, 4) becomes (429, None)
              (110, 5) becomes (429, None)
              (122, 4) becomes (421, None)
              (122, 5) becomes (421, None)
              (125, 4) becomes (422, None)
              (125, 5) becomes (422, None)
              (126, 4) becomes (423, None)
              (126, 5) becomes (423, None)
              (128, 4) becomes (424, None)
              (128, 5) becomes (424, None)
              (129, 4) becomes (425, None)
              (129, 5) becomes (425, None)
              (130, 4) becomes (426, None)
              (130, 5) becomes (426, None)
              (131, 4) becomes (427, None)
              (131, 5) becomes (427, None)
              (132, 4) becomes (428, None)
              (132, 5) becomes (428, None)
        State 'Saw group glyph 65':
          Class 'group glyph 158':
            Remember this glyph, then go to state 'Start of text' after doing these substitutions:
              (65, 158) becomes (386, None)
              (65, 412) becomes (387, None)
              (70, 158) becomes (389, None)
              (70, 412) becomes (390, None)
              (71, 158) becomes (392, None)
              (71, 412) becomes (393, None)
              (72, 158) becomes (395, None)
              (72, 412) becomes (396, None)
              (73, 158) becomes (398, None)
              (73, 412) becomes (399, None)
              (74, 158) becomes (401, None)
              (74, 412) becomes (402, None)
              (75, 158) becomes (404, None)
              (75, 412) becomes (405, None)
              (76, 158) becomes (407, None)
              (76, 412) becomes (408, None)
              (77, 158) becomes (410, None)
              (77, 412) becomes (411, None)
          Class 'group glyph 4':
            Remember this glyph, then go to state 'Start of text' after doing these substitutions:
              (65, 4) becomes (385, None)
              (65, 5) becomes (385, None)
              (70, 4) becomes (388, None)
              (70, 5) becomes (388, None)
              (71, 4) becomes (391, None)
              (71, 5) becomes (391, None)
              (72, 4) becomes (394, None)
              (72, 5) becomes (394, None)
              (73, 4) becomes (397, None)
              (73, 5) becomes (397, None)
              (74, 4) becomes (400, None)
              (74, 5) becomes (400, None)
              (75, 4) becomes (403, None)
              (75, 5) becomes (403, None)
              (76, 4) becomes (406, None)
              (76, 5) becomes (406, None)
              (77, 4) becomes (409, None)
              (77, 5) becomes (409, None)
        Class table:
          4: group glyph 4
          5: group glyph 4
          11: group glyph 11
          16: group glyph 11
          17: group glyph 11
          19: group glyph 11
          20: group glyph 11
          21: group glyph 11
          22: group glyph 11
          23: group glyph 11
          65: group glyph 65
          70: group glyph 65
          71: group glyph 65
          72: group glyph 65
          73: group glyph 65
          74: group glyph 65
          75: group glyph 65
          76: group glyph 65
          77: group glyph 65
          110: group glyph 11
          122: group glyph 11
          125: group glyph 11
          126: group glyph 11
          128: group glyph 11
          129: group glyph 11
          130: group glyph 11
          131: group glyph 11
          132: group glyph 11
          158: group glyph 158
          412: group glyph 158
        Mask value: (no data)
        Coverage: (no data)
        """
        
        if not self:
            return []
        
        from fontio3.morx import (
          entry_ligature,
          glyphtuple,
          glyphtupledict,
          ligature,
          staterow_ligature)
        
        if 'namerObj' in kwArgs:
            nm = kwArgs['namerObj'].bestNameForGlyphIndex
        else:
            nm = (lambda n: "glyph %d" % (n,))
    
        keyGroups = self._separatedKeys()
        rv = []
        entryNOP = entry_ligature.Entry()
    
        for keyGroup in keyGroups:
            dLigPiece = {k: self[k] for k in keyGroup}
            
            # Each keyGroup represents a complete Ligature subtable. All
            # potential conflicts have already been ironed out by the
            # separation logic, so here we can just put things together.
        
            ct = self._classTableFromKeyGroup(dLigPiece, nm)
            d = {}
        
            for key in keyGroup:
                currState = 'Start of text'
            
                for i, inGlyph in enumerate(key):
                    if currState not in d:
                        d[currState] = staterow_ligature.StateRow({
                          'End of text': entryNOP,
                          'Out of bounds': entryNOP,
                          'Deleted glyph': entryNOP,
                          'End of line': entryNOP})
                
                    currClass = ct[inGlyph]
                
                    if currClass not in d[currState]:
                        if i == len(key) - 1:
                            tIn = glyphtuple.GlyphTupleInput(key)
                            v = [None] * len(tIn)
                            v[0] = self[key]
                            tOut = glyphtuple.GlyphTupleOutput(v)
                            gtd = glyphtupledict.GlyphTupleDict({tIn: tOut})
                        
                            d[currState][currClass] = entry_ligature.Entry(
                              newState = "Start of text",
                              push = True,
                              actions = gtd)
                    
                        else:
                            if i:
                                newState = "%s-%s" % (currState, currClass)
                            else:
                                newState = "Saw %s" % (currClass,)
                    
                            d[currState][currClass] = entry_ligature.Entry(
                              newState = newState,
                              push = True)
                
                    elif i == len(key) - 1:
                        tIn = glyphtuple.GlyphTupleInput(key)
                        v = [None] * len(tIn)
                        v[0] = self[key]
                        tOut = glyphtuple.GlyphTupleOutput(v)
                        gtd = glyphtupledict.GlyphTupleDict({tIn: tOut})
                        d[currState][currClass].actions[tIn] = tOut
                
                    currState = d[currState][currClass].newState
        
            allClasses = set(ct.values())
        
            for stateName, row in d.items():
                for className in allClasses:
                    if className not in row:
                        row[className] = entryNOP
        
            d['Start of line'] = d['Start of text']
            rv.append(ligature.Ligature(d, classTable=ct))
    
        return rv
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Ligature object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0006 0000 0001  0000                |..........      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0008 0001 000E  0001 0001 0004 0001 |................|
              10 | 0004 0061 0003 000B  001D                |...a......      |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 000A 0002 0012  0018 0001 0002 0005 |................|
              10 | 000B 0002 000A 0010  0001 0010 0020 0002 |............. ..|
              20 | 0009 001F 0002 0003  000D 0002 000C      |..............  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format
        
        # Create a dict whose keys are firstGlyphs and whose values are lists,
        # in sequence order, of (fullKey, ligature) pairs. This will make the
        # writing of the sets much easier later on.
        
        fgMap = {}
        
        for k, g in itertools.groupby(self, operator.itemgetter(0)):
            fgMap[k] = [(key, self[key]) for key in g]
        
        sortedFirstGlyphs = sorted(fgMap)
        covTable = coverage.Coverage.fromglyphset(sortedFirstGlyphs)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        w.add("H", len(sortedFirstGlyphs))
        setStakes = list(w.getNewStake() for firstGlyph in sortedFirstGlyphs)
        
        for setStake in setStakes:
            w.addUnresolvedOffset("H", stakeValue, setStake)
        
        covTable.buildBinary(w, stakeValue=covStake)
        ligStakes = {}  # firstGlyph -> list of stakes
        
        for firstGlyph, setStake in zip(sortedFirstGlyphs, setStakes):
            w.stakeCurrentWithValue(setStake)
            v = fgMap[firstGlyph]
            w.add("H", len(v))
            ligStakes[firstGlyph] = list(w.getNewStake() for obj in v)
            
            for ligStake in ligStakes[firstGlyph]:
                w.addUnresolvedOffset("H", setStake, ligStake)
        
        for firstGlyph in sortedFirstGlyphs:
            for t, ligStake in zip(fgMap[firstGlyph], ligStakes[firstGlyph]):
                w.stakeCurrentWithValue(ligStake)
                key, lig = t
                w.add("H", lig)
                w.add("H", len(key))
                w.addGroup("H", key[1:])
    
    def componentCounts(self):
        """
        Returns a dict mapping ligature glyph indices to counts of input glyphs
        that went into that ligature's making. This only counts the substantive
        contributors, and is only one-level.
        
        >>> _testingValues[2].pprint()
        Ligature_GlyphTuple((5, 9)): 32
        Ligature_GlyphTuple((5, 3)): 31
        Ligature_GlyphTuple((11, 12)): 13
        
        >>> d = _testingValues[2].componentCounts()
        >>> for ligGlyph in sorted(d):
        ...   print(ligGlyph, d[ligGlyph])
        13 2
        31 2
        32 2
        """
        
        return {g: len(t) for t, g in self.items()}
    
    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectsSummary() instead.")
    
    def effectsSummary(self, **kwArgs):
        """
        Returns an EffectsSummary object. If present, notes will be made in a
        provided memo kwArgs to allow elision of reprocessing, which should
        eliminate the combinatoric explosion.
        
        >>> obj = _testingValues[2]
        >>> memo = {}
        >>> es = obj.effectsSummary(memo=memo)
        >>> es.pprint()
        3:
          31
        5:
          31
          32
        9:
          32
        11:
          13
        12:
          13
        >>> id(obj) in memo
        True
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for tIn, gOut in self.items():
            for gIn in tIn:
                r[gIn].add(gOut)
        
        memo[id(self)] = r
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new Ligature constructed from the specified FontWorkerSource,
        with source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> _test_FW_fws.goto(1) # go back to start of file
        >>> l = Ligature.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger)
        >>> l.pprint()
        Ligature_GlyphTuple((2, 2, 3)): 11
        Ligature_GlyphTuple((2, 2)): 15
        Ligature_GlyphTuple((2, 3)): 7
        Ligature_GlyphTuple((2, 5)): 17
        >>> l = Ligature.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.ligature - WARNING - line 3 -- incorrect number of tokens, expected 2 or more, found 1
        FW_test.ligature - WARNING - line 6 -- ignoring duplicated entry for 'f,f,i'
        FW_test.ligature - WARNING - line 8 -- glyph 'B' not found
        FW_test.ligature - WARNING - line 8 -- glyph 'C' not found
        FW_test.ligature - ERROR - line 0 -- did not find matching 'subtable end/lookup end'
        >>> l.pprint()
        Ligature_GlyphTuple((2, 2, 3)): 11
        Ligature_GlyphTuple((2, 2)): 15
        Ligature_GlyphTuple((2, 3)): 7
        Ligature_GlyphTuple((2, 5)): 17
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("ligature")
        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber = fws.lineNumber
        sawTerminalString = False
        keyOrder = _GlyphList()
        ligatureDict = {}
        
        for line in fws:
            if line in terminalStrings:
                sawTerminalString = True
                break
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if len(tokens) < 2:
                    logger.warning((
                      'V0957',
                      (fws.lineNumber, len(tokens)), 
                      "line %d -- incorrect number of tokens, expected "
                      "2 or more, found %d"))
                    
                    continue

                glyphsOK = True
                glyphIndices = [namer.glyphIndexFromString(t) for t in tokens]
                
                for i in range(len(tokens)):
                    if glyphIndices[i] is None:
                        logger.warning((
                          'V0956',
                          (fws.lineNumber, tokens[i]),
                          "line %d -- glyph '%s' not found"))
                        
                        glyphsOK = False

                if glyphsOK:
                    key = ligature_glyphtuple.Ligature_GlyphTuple(glyphIndices[1:])
                    value = glyphIndices[0]
                    
                    if key not in ligatureDict:  # there are occasionally duplicates
                        ligatureDict[key] = value
                        keyOrder.append(key)
                    
                    else:
                        keyStr = ",".join([t for t in tokens[1:]])
                        
                        logger.warning((
                          'V0963',
                          (fws.lineNumber, keyStr),
                          "line %d -- ignoring duplicated entry for '%s'"))
        
        if not sawTerminalString:
            logger.error((
              'V0958',
              (startingLineNumber, "/".join(terminalStrings)),
              'line %d -- did not find matching \'%s\''))

        keyOrder.doCanonicalKeyOrdering()
        return cls(ligatureDict, keyOrder=keyOrder)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Ligature object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("ligature_test")
        >>> fvb = Ligature.fromvalidatedbytes
        >>> s = _testingValues[2].binaryString()
        >>> obj = fvb(s, logger=logger)
        ligature_test.ligature - DEBUG - Walker has 46 remaining bytes.
        ligature_test.ligature.coverage - DEBUG - Walker has 36 remaining bytes.
        ligature_test.ligature.coverage - DEBUG - Format is 1, count is 2
        ligature_test.ligature.coverage - DEBUG - Raw data are [5, 11]
        
        >>> h = utilities.fromhex
        >>> fvb(s[:2], logger=logger)
        ligature_test.ligature - DEBUG - Walker has 2 remaining bytes.
        ligature_test.ligature - ERROR - Insufficient bytes.
        
        >>> fvb(h("00 02") + s[2:], logger=logger)
        ligature_test.ligature - DEBUG - Walker has 46 remaining bytes.
        ligature_test.ligature - ERROR - Expected format 1, but got format 2.
        
        >>> fvb(s[:6], logger=logger)
        ligature_test.ligature - DEBUG - Walker has 6 remaining bytes.
        ligature_test.ligature.coverage - DEBUG - Walker has 0 remaining bytes.
        ligature_test.ligature.coverage - ERROR - Insufficient bytes.
        
        >>> s = h("00 01 00 08 00 01 00 12 00 01 00 02 00 05 00 0B")
        >>> fvb(s, logger=logger)
        ligature_test.ligature - DEBUG - Walker has 16 remaining bytes.
        ligature_test.ligature.coverage - DEBUG - Walker has 8 remaining bytes.
        ligature_test.ligature.coverage - DEBUG - Format is 1, count is 2
        ligature_test.ligature.coverage - DEBUG - Raw data are [5, 11]
        ligature_test.ligature - ERROR - The LigSetCount (1) does not match the length of the Coverage (2).
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("ligature")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, covOffset, setCount = w.unpack("3H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1, but got format %d."))
            
            return None
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger,
          **kwArgs)
        
        if covTable is None:
            return None
        
        if setCount != len(covTable):
            logger.error((
              'V0430',
              (setCount, len(covTable)),
              "The LigSetCount (%d) does not match the length of "
              "the Coverage (%d)."))
            
            return None
        
        firstGlyphs = sorted(covTable)
        r = cls()
        
        if w.length() < 2 * setCount:
            logger.error((
              'V0431',
              (),
              "The LigatureSet offsets are missing or incomplete."))
            
            return None
        
        if not setCount:
            logger.warning((
              'V0432',
              (),
              "The LigSetCount is zero, so the Lookup has no effect."))
            
            return r
        
        setOffsets = w.group("H", setCount)
        
        for firstGlyph, setOffset in zip(firstGlyphs, setOffsets):
            wSet = w.subWalker(setOffset)
            setLogger = logger.getChild("first glyph %d" % (firstGlyph,))
            
            if wSet.length() < 2:
                setLogger.error((
                  'V0433',
                  (),
                  "The LigatureCount is missing or incomplete."))
                
                return None
            
            ligCount = wSet.unpack("H")
            
            if wSet.length() < 2 * ligCount:
                setLogger.error((
                  'V0434',
                  (),
                  "The Ligature offsets are missing or incomplete."))
                
                return None
            
            if not ligCount:
                setLogger.warning((
                  'V0438',
                  (),
                  "The LigatureCount is zero, so this first glyph "
                  "will not have any ligatures made."))
            
            for i, ligOffset in enumerate(wSet.group("H", ligCount)):
                wLig = wSet.subWalker(ligOffset)
                ligLogger = setLogger.getChild("array entry %d" % (i,))
                
                if wLig.length() < 4:
                    ligLogger.error((
                      'V0435',
                      (),
                      "The Ligature table header is missing or incomplete."))
                    
                    return None
                
                ligGlyph, fullCount = wLig.unpack("2H")
                
                if not fullCount:
                    ligLogger.error((
                      'V0439',
                      (),
                      "The CompCount is zero, which is invalid."))
                    
                    return None
                
                elif fullCount == 1:
                    ligLogger.warning((
                      'V0440',
                      (),
                      "The CompCount is one, which means substitution on "
                      "the first glyph alone. Use a Single Lookup instead."))
                
                if wLig.length() < 2 * (fullCount - 1):
                    ligLogger.error((
                      'V0436',
                      (),
                      "The Component array is missing or incomplete."))
                    
                    return None
                
                key = GT((firstGlyph,) + wLig.group("H", fullCount - 1))
                
                if key in r:
                    ligLogger.warning((
                      'V0437',
                      (key,),
                      "There are duplicate entries with key %s."))
                
                else:
                    r.keyOrder.append(key)
                    r[key] = ligGlyph
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Ligature object from the specified walker.
        
        >>> _testingValues[0] == Ligature.frombytes(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == Ligature.frombytes(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == Ligature.frombytes(_testingValues[2].binaryString())
        True
        """
        
        format, covOffset, setCount = w.unpack("3H")
        
        if format != 1:
            raise ValueError("Unknown format for Ligature subtable: %s" % (format,))
        
        covTable = coverage.Coverage.fromwalker(w.subWalker(covOffset))
        
        if setCount != len(covTable):
            raise ValueError("Internal conflict in Ligature data!")
        
        firstGlyphs = sorted(covTable)
        r = cls()
        setOffsets = w.group("H", setCount)
        
        for firstGlyph, setOffset in zip(firstGlyphs, setOffsets):
            wSet = w.subWalker(setOffset)
            
            for ligOffset in wSet.group("H", wSet.unpack("H")):
                wLig = wSet.subWalker(ligOffset)
                ligGlyph, fullCount = wLig.unpack("2H")
                key = GT((firstGlyph,) + wLig.group("H", fullCount - 1))
                
                if key not in r:  # there are occasionally duplicates
                    r.keyOrder.append(key)
                    r[key] = ligGlyph
        
        return r
    
    def glyphsRenumbered(self, oldToNew, **kwArgs):
        """
        We put a 'shim' layer here to ensure that keyOrder is renumbered first,
        since the __iter__() method uses it to walk the actual dict.
        """
        
        r = mapmeta.M_glyphsRenumbered(self, oldToNew, **kwArgs)
        s = set(super(Ligature, r).__iter__())
        r.keyOrder[:] = [x for x in r.keyOrder if x in s]
        return r
    
    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        Do the processing for a single (initial) glyph in a glyph array. This
        method is called by the Lookup object's run() method (and possibly by
        actions within contextual or related subtables).
        
        This method returns a pair: the new output GlyphList, and a count of
        the number of glyph indices involved (or zero, if no action happened).
        
        Note that the igsFunc and useEmpties are used in this method.
        
        >>> inTuple = ligature_glyphtuple.Ligature_GlyphTuple([4, 5, 7])
        >>> obj = Ligature({inTuple: 77}, keyOrder=_GlyphList([(4, 5, 7)]))
        >>> ga = runningglyphs.GlyphList.fromiterable([3, 4, 5, 60, 7, 8])
        >>> igsFunc = lambda *a, **k: [False, False, False, True, False, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> count
        0
        
        When no match is found, the same (input) glyphArray is returned:
        
        >>> r is ga
        True
        
        >>> r, count = obj.runOne(ga, 1, igsFunc=igsFunc)
        >>> count
        4
        
        >>> r.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 77
          originalOffset: 1
        2:
          Value: -1
          originalOffset: 2
        3:
          Value: 60
          originalOffset: 3
        4:
          Value: -1
          originalOffset: 4
        5:
          Value: 8
          originalOffset: 5
        
        >>> r[1].ligInputOffsets
        (1, 2, 4)
        
        >>> r, count = obj.runOne(ga, 1, igsFunc=igsFunc, useEmpties=False)
        >>> count
        2
        
        >>> r.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 77
          originalOffset: 1
        2:
          Value: 60
          originalOffset: 3
        3:
          Value: 8
          originalOffset: 5
        
        Note that the ligInputOffsets will refer to offsets whose associated
        glyphs are no longer present!
        
        >>> r[1].ligInputOffsets
        (1, 2, 4)
        """
        
        igs = kwArgs['igsFunc'](glyphArray, **kwArgs)
        useEmpties = kwArgs.get('useEmpties', True)
        firstGlyph = glyphArray[startIndex]
        
        # To make comparisons in the loop easier, we use the igs data to
        # extract just the non-ignorables starting with startIndex into a
        # separate list called vNonIgs.
        
        v = [
          (g, i)
          for i, g in enumerate(glyphArray[startIndex:], start=startIndex)
          if (not igs[i])]
        
        vNonIgs = [x[0] for x in v]
        vBackMap = [x[1] for x in v]
        G = runningglyphs.Glyph
        
        for key in self:  # custom order, remember...
            if firstGlyph != key[0]:
                continue
            
            if len(key) > len(vNonIgs):
                continue
            
            if not all(a == b for a, b in zip(key, vNonIgs)):
                continue
            
            # If we get here the key is a match
            
            r = glyphArray.fromiterable(glyphArray)  # preserves offsets
            it = (g.shaperClass for g in vNonIgs[:len(key)] if g.shaperClass)
            sc = '+'.join(it) or None
            lastIndex = None
            lio = []
            toDel = []
            
            for i in vBackMap[:len(key)]:
                if i == startIndex:
                    r[i] = G(
                      self[key],
                      originalOffset = firstGlyph.originalOffset,
                      shaperClass = sc)
                    
                    lio.append(firstGlyph.originalOffset)
                
                else:
                    lastIndex = i
                    lio.append(r[i].originalOffset)
                    
                    if useEmpties:
                        r[i] = G(-1, originalOffset=r[i].originalOffset)
                    else:
                        toDel.append(i)
            
            for i in reversed(toDel):
                del r[i]
            
            r[startIndex].ligInputOffsets = tuple(lio)
            assert lastIndex is not None
            count = lastIndex - startIndex + 1
            
            if not useEmpties:
                count -= (len(key) - 1)
            
            return (r, count)
        
        return (glyphArray, 0)

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of lookup to provided stream 's'. Uses
        namer.bestNameForGlyphIndex if a namer is provided, otherwise
        uses Font Worker glyph index labeling ("# <id>").
        """
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        for inTuple in iter(self):
            outGlyph = self[inTuple]
            inTupleStr = "\t".join([bnfgi(g) for g in inTuple])
            s.write("%s\t%s\n" % (bnfgi(outGlyph), inTupleStr))
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    lgtv = ligature_glyphtuple._testingValues
    
    _testingValues = (
        Ligature(),
        
        Ligature(
          {lgtv[0]: 97},
          keyOrder = [lgtv[0]]),
        
        Ligature(
          {lgtv[1]: 32, lgtv[2]: 31, lgtv[3]: 13},
          keyOrder = [lgtv[1], lgtv[2], lgtv[3]]))
    
    del lgtv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'f': 2,
        'i': 3,
        'l': 5,
        'fi': 7,
        'ffi': 11,
        'ff': 15,
        'fl': 17,
        'X': 19
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        fl	f	l
        ff	f	f
        ffi	f	f	i
        fi	f	i
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        fi	f	i
        A
        ff	f	f
        ffi	f	f	i
        X	f	f	i
        fl	f	l
        B	C
        """))
    
#     def _getTestDataModule():
#         from fontio3.GSUB import ligature_testdata
#         
#         return ligature_testdata

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
