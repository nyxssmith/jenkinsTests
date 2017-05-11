#
# pairglyphs.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 1 GPOS pair positioning tables.
"""

# System imports
from collections import defaultdict
import functools
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.GPOS import effect, pairglyphs_key, pairvalues
from fontio3.opentype import coverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    for k, pv in obj.items():
        if not pv:
            logger.warning((
              'V0333',
              (k,),
              "The PairValue associated with key %s has no effect."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PairGlyphs(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing format 1 pair GPOS tables.
    
    These are dicts mapping Keys to PairValues.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    (xyz11, xyz21):
      First adjustment:
        FUnit adjustment to origin's x-coordinate: 30
        Device for vertical advance:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
      Second adjustment:
        Device for origin's x-coordinate:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
        Device for origin's y-coordinate:
          Tweak at 12 ppem: -5
          Tweak at 13 ppem: -3
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 2
          Tweak at 20 ppem: 3
    (xyz9, xyz16):
      Second adjustment:
        FUnit adjustment to origin's x-coordinate: -10
    (xyz9, xyz21):
      First adjustment:
        Device for vertical advance:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
    
    >>> _testingValues[0].gatheredMaxContext()
    2
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdeepkeys = True,
        item_usenamerforstr = True,
        map_compactremovesfalses = True,
        map_maxcontextfunc = (lambda d: 2),
        map_validatefunc_partial = _validate)
    
    kind = ('GPOS', 2)
    kindString = "Pair (glyph) positioning table"
    
    #
    # Methods
    #
    
    def asVOLT(self, lookupLabel, **kwArgs):
        """
        Returns VOLT-compatible source for the object using the label
        'lookupLabel', or None if the Value mask is something other than
        horizontal advance. The following keyword arguments are supported:
        
            editor      An Editor-class object, used to obtain glyph names.
        """
        
        editor = kwArgs.get('editor')
        mFirst, mSecond = self.getMasks()
        
        if (mFirst & 0xFFFB) or (mSecond & 0xFFFB) or (editor is None):
            return None
        
        sv = [
          r'DEF_LOOKUP "%s" PROCESS_BASE SKIP_MARKS DIRECTION LTR' % (lookupLabel,),
          "IN_CONTEXT",
          "END_CONTEXT",
          "AS_POSITION",
          "ADJUST_PAIR"]
        
        nm = editor.getNamer().bestNameForGlyphIndex
        firstIndices = set(x[0] for x in self)
        firstSort = sorted((nm(gi), gi) for gi in firstIndices)
        firstGlyphToIndex = {gi: i+1 for i, (s, gi) in enumerate(firstSort)}
        secondIndices = set(x[1] for x in self)
        secondSort = sorted((nm(gi), gi) for gi in secondIndices)
        secondGlyphToIndex = {gi: i+1 for i, (s, gi) in enumerate(secondSort)}
        s = ' '.join('FIRST  GLYPH "%s"' % (s,) for s, gi in firstSort)
        sv.append(s)
        s = ' '.join('SECOND  GLYPH "%s"' % (s,) for s, gi in secondSort)
        sv.append(s)
        d = {}
        
        for key, val in self.items():
            if val.first is None or (not val.first.xAdvance):
                part1 = ""
            else:
                part1 = str(val.first.xAdvance) + " "
            
            if val.second is None or (not val.second.xAdvance):
                part2 = ""
            else:
                part2 = str(val.second.xAdvance) + " "
            
            index1 = firstGlyphToIndex[key[0]]
            index2 = secondGlyphToIndex[key[1]]
            
            d[(index1, index2)] = (
              " %d %d BY POS ADV %sEND_POS POS %sEND_POS" %
              (index1, index2, part1, part2))
        
        for key in sorted(d):
            sv.append(d[key])
        
        sv.extend(["END_ADJUST", "END_POSITION", " END"])
        return '\r'.join(sv)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 000E 0081 0031  0002 0016 0030 0001 |.......1.....0..|
              10 | 0002 0008 000A 0002  000F 0000 0000 FFF6 |................|
              20 | 0000 0000 0014 0000  0034 0000 0000 0000 |.........4......|
              30 | 0001 0014 001E 001A  0000 001A 000E 000C |................|
              40 | 0014 0002 BDF0 0020  3000 000C 0012 0001 |....... 0.......|
              50 | 8C04                                     |..              |
        """
        
        # Add the fixed and unresolved content
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format 1
        firstGlyphs = sorted(set(k[0] for k in self))
        covIndexToGlyphMap = {}
        
        covTable = coverage.Coverage.fromglyphset(
          firstGlyphs,
          backMap = covIndexToGlyphMap)
        
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        forVariable = 'otIVS' in kwArgs
        vf1, vf2 = self.getMasks()
        w.add("3H", vf1, vf2, len(firstGlyphs))
        secondData = {}  # sorted(secondSet) -> {
                         # immut(pairvalues) -> (firstGlyph, stake, pairvalue)}
        
        for firstGlyph in firstGlyphs:
            seconds = tuple(sorted(k[1] for k in self if k[0] == firstGlyph))
            objs = [self[(firstGlyph, secondGlyph)] for secondGlyph in seconds]
            immut = tuple(obj.asImmutable() for obj in objs)
            d = secondData.setdefault(seconds, {})
            
            if immut not in d:
                d[immut] = (firstGlyph, w.getNewStake(), objs)
            
            w.addUnresolvedOffset("H", stakeValue, d[immut][1])
        
        covTable.buildBinary(w, stakeValue=covStake)
        devicePool = {}
        v = [(k,) + t for k, d in secondData.items() for t in d.values()]
        it = sorted(v, key=operator.itemgetter(1))
        
        for seconds, firstGlyph, stake, objs in it:
            w.stakeCurrentWithValue(stake)
            w.add("H", len(objs))
            
            for secondGlyph, obj in zip(seconds, objs):
                w.add("H", secondGlyph)
                
                self[(firstGlyph, secondGlyph)].buildBinary(
                  w,
                  devicePool = devicePool,
                  posBase = stake,
                  valueFormatFirst = vf1,
                  valueFormatSecond = vf2,
                  **kwArgs)
        
        it = sorted(
          (sorted(obj.asImmutable()[1]), obj, stake)
          for obj, stake in devicePool.values())
        
        for t in it:
            t[1].buildBinary(w, stakeValue=t[2], **kwArgs)

    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectExtrema() instead.")
    
    def effectExtrema(self, forHorizontal=True, **kwArgs):
        """
        Returns a dict, indexed by glyph, of pairs of values. If
        forHorizontal is True, these values will be the yMaxDelta and
        yMinDelta; if False, they will be the xMaxDelta and xMinDelta. These
        values can then be used to test against the font's ascent/descent
        values in order to show VDMA-like output, or to be accumulated across
        all the features that are performed for a given script and lang/sys.
        
        Note that either or both of these values may be None; this can arise
        for cases like mark-to-mark, where potentially infinite stacking of
        marks can occur.
        
        The following keyword arguments are used:
            
            cache               A dict mapping object IDs to result dicts.
                                This is used during processing to speed up
                                analysis of deeply nested subtables, so the
                                effectExtrema() call need only be made once per
                                subtable.
            
            editor              The Editor object containing this subtable.
        
        >>> d = _testingValues[0].effectExtrema(forHorizontal=False)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        10 (30, 0)
        15 (0, -10)
        """
        
        cache = kwArgs.get('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        fv = effect.Effect.fromvalue
        
        for (glyph1, glyph2), pvObj in self.items():
            if pvObj.first is not None:
                p = fv(pvObj.first).toPair(forHorizontal)
                
                if any(p):
                    if glyph1 not in r:
                        r[glyph1] = p
                    
                    else:
                        old = r[glyph1]
                        
                        r[glyph1] = tuple((
                          max(old[0], p[0]),
                          min(old[1], p[1])))
            
            if pvObj.second is not None:
                p = fv(pvObj.second).toPair(forHorizontal)
                
                if any(p):
                    if glyph2 not in r:
                        r[glyph2] = p
                    
                    else:
                        old = r[glyph2]
                        
                        r[glyph2] = tuple((
                          max(old[0], p[0]),
                          min(old[1], p[1])))
        
        cache[id(self)] = r
        return r
    
    @classmethod
    def frompairclasses(cls, pcObj, **kwArgs):
        """
        Given a PairClasses object, flatten it into a PairGlyphs object.
        
        The useSpecialClass0 keyword (default True) will take a class value of
        zero and map it to the special glyph code None, in order to keep the
        size of the resulting conversion reasonable. If the keyword is False
        then all the class 0 entries will be skipped.
        
        However, if you want a full expansion, including all the exceptions,
        then specify the fullExpansion=True keyword. Note that in this case you
        will also have to provide either an editor or a fontGlyphCount
        keyword argument, so that the class 0 expansions can be done.
        
        If both useSpecialClass0 and fullExpansion are True, useSpecialClass0
        wins.
        """
        
        r = cls()
        cd1 = utilities.invertDictFull(pcObj.classDef1, asSets=True)
        cd2 = utilities.invertDictFull(pcObj.classDef2, asSets=True)
        K = pairglyphs_key.Key
        useSpecial = kwArgs.get('useSpecialClass0', True)
        
        if kwArgs.get('fullExpansion', False):
            fullExpansion = True
            c1Set = pcObj.coverageExtras
            fgc = utilities.getFontGlyphCount(**kwArgs)
            c2Set = set(range(fgc))
            excludes = {g for c, s in cd2.items() if c for g in s}
            c2Set -= excludes
        
        else:
            fullExpansion = False
        
        for cKey, cValue in pcObj.items():
            if cKey[0]:
                it1 = cd1[cKey[0]]
            elif useSpecial:
                it1 = [None]
            elif fullExpansion:
                it1 = c1Set
            else:
                it1 = []
            
            for g1 in it1:
                if cKey[1]:
                    it2 = cd2[cKey[1]]
                elif useSpecial:
                    it2 = [None]
                elif fullExpansion:
                    it2 = c2Set
                else:
                    it2 = []
                
                for g2 in it2:
                    r[K([g1, g2])] = cValue
        
        return r

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new PairGlyphs object from the specified
        FontWorkerSource, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> pg = PairGlyphs.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.pairglyphs - WARNING - line 3 -- glyph 'X' not found
        FW_test.pairglyphs - WARNING - line 4 -- glyph 'Y' not found
        >>> pg.pprint()
        Key((1, 2)):
          First adjustment:
            FUnit adjustment to origin's x-coordinate: -123
        Key((7, 8)):
          Second adjustment:
            FUnit adjustment to horizontal advance: 987
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('pairglyphs')
        iskernset = kwArgs.get('iskernset', False)
        namer = kwArgs['namer']
        terminalStrings = ['subtable end', 'lookup end']
        
        if iskernset:
            terminalStrings += [
              'firstclass definition begin', 
              'secondclass definition begin']
        
        tokenSet = frozenset({
          'left x advance',
          'left x placement',
          'left y advance',
          'left y placement',
          'right x advance',
          'right x placement',
          'right y advance',
          'right y placement'})    
        
        startingLineNumber = fws.lineNumber
        pvdict = defaultdict(lambda: [None, None])
        PV = pairvalues.PairValues
        V = value.Value
        r = cls()

        for line in fws:
            if line.lower().strip() in terminalStrings:
                for pkey, pvals in pvdict.items():
                    r[pkey] = PV(pvals[0], pvals[1])
            
                return r

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() in tokenSet:
                    glyph1Name = tokens[1]
                    glyph1Index = namer.glyphIndexFromString(glyph1Name)
                    
                    if glyph1Index is None:
                        logger.warning((
                          'V0956',
                          (fws.lineNumber, glyph1Name),
                          "line %d -- glyph '%s' not found"))
                        
                        continue

                    glyph2Name = tokens[2]
                    glyph2Index = namer.glyphIndexFromString(glyph2Name)
                    
                    if glyph2Index is None:
                        logger.warning((
                          'V0956',
                          (fws.lineNumber, glyph2Name),
                          "line %d -- glyph '%s' not found"))
                        
                        continue

                    key = pairglyphs_key.Key((glyph1Index, glyph2Index))
                    
                    if key in r:
                        logger.warning((
                          'Vxxxx',
                          (fws.lineNumber, glyph1Name, glyph2Name),
                          "line %d -- ignoring duplicated entry for '%s,%s'"))
                    
                    else:
                        val = int(tokens[3])
                        pval = pvdict[key]
                        
                        if tokens[0].lower() == 'left x placement':
                            if pval[0] and pval[0].xPlacement:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[0] is None:
                                    pval[0] = value.Value()
                                pval[0].xPlacement = val

                        elif tokens[0].lower() == 'right x placement':
                            if pval[1] and pval[1].xPlacement:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].xPlacement = val

                        elif tokens[0].lower() == 'left x advance':
                            if pval[0] and pval[0].xAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[0] is None:
                                    pval[0] = value.Value()
                                pval[0].xAdvance = val

                        elif tokens[0].lower() == 'right x advance':
                            if pval[1] and pval[1].xAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].xAdvance = val

                        elif tokens[0].lower() == 'left y placement':
                            if pval[0] and pval[0].yPlacement:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[0] is None:
                                    pval[0] = value.Value()
                                pval[0].yPlacement = val

                        elif tokens[0].lower() == 'right y placement':
                            if pval[1] and pval[1].yPlacement:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].yPlacement = val

                        elif tokens[0].lower() == 'left y advance':
                            if pval[0] and pval[0].yAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[0] is None:
                                    pval[0] = value.Value()
                                pval[0].yAdvance = val

                        elif tokens[0].lower() == 'right y advance':
                            if pval[1] and pval[1].yAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for glyph "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].yAdvance = val


                else:
                    logger.warning((
                      'V0960',
                      (fws.lineNumber, tokens[0]),
                      'line %d -- unexpected token: %s'))
                
        logger.warning((
          'V0958',
          (startingLineNumber, "/".join(terminalStrings)),
          'line %d -- did not find matching \'%s\''))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PairGlyphs object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("test_pairglyphs")
        >>> fvb = PairGlyphs.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger).pprint()
        test_pairglyphs.pairglyphs - DEBUG - Walker has 82 remaining bytes.
        test_pairglyphs.pairglyphs.coverage - DEBUG - Walker has 68 remaining bytes.
        test_pairglyphs.pairglyphs.coverage - DEBUG - Format is 1, count is 2
        test_pairglyphs.pairglyphs.coverage - DEBUG - Raw data are [8, 10]
        test_pairglyphs.pairglyphs.second glyph 15.pairvalues - DEBUG - Walker has 56 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 15.pairvalues.value - DEBUG - Walker has 56 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 15.pairvalues.value - DEBUG - Walker has 52 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues - DEBUG - Walker has 44 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 44 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 40 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues - DEBUG - Walker has 30 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 30 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 26 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - Walker has 8 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - Data are (35844,)
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - Walker has 20 remaining bytes.
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - StartSize=12, endSize=20, format=2
        test_pairglyphs.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - Data are (48624, 32, 12288)
        Key((8, 15)):
          Second adjustment:
            FUnit adjustment to origin's x-coordinate: -10
        Key((8, 20)):
          First adjustment:
            Device for vertical advance:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
        Key((10, 20)):
          First adjustment:
            FUnit adjustment to origin's x-coordinate: 30
            Device for vertical advance:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
          Second adjustment:
            Device for origin's x-coordinate:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
            Device for origin's y-coordinate:
              Tweak at 12 ppem: -5
              Tweak at 13 ppem: -3
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 2
              Tweak at 20 ppem: 3
        
        >>> fvb(s[:1], logger=logger)
        test_pairglyphs.pairglyphs - DEBUG - Walker has 1 remaining bytes.
        test_pairglyphs.pairglyphs - ERROR - Insufficient bytes.
        
        >>> fvb(s[:10], logger=logger)
        test_pairglyphs.pairglyphs - DEBUG - Walker has 10 remaining bytes.
        test_pairglyphs.pairglyphs.coverage - DEBUG - Walker has 0 remaining bytes.
        test_pairglyphs.pairglyphs.coverage - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('pairglyphs')
        otcd = kwArgs.get('otcommondeltas')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 10:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        r = cls()
        format = w.unpack("H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1, but got %d."))
            
            return None
        
        covOffset = w.unpack("H")
        
        if not covOffset:
            logger.error((
              'V0330',
              (),
              "The offset to the Coverage is zero."))
            
            return None
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger)
        
        if covTable is None:
            return None
        
        firstGlyphs = sorted(covTable)
        vf1, vf2, count = w.unpack("3H")
        
        if vf1 & 0xFF00:
            logger.error((
              'E4110',
              (vf1,),
              "Reserved bits are set in the 0x%04X ValueFormat1 field."))
            
            return None
        
        if vf2 & 0xFF00:
            logger.error((
              'E4110',
              (vf2,),
              "Reserved bits are set in the 0x%04X ValueFormat2 field."))
            
            return None
        
        if not (vf1 or vf2):
            logger.warning((
              'V0328',
              (),
              "Both ValueFormat1 and ValueFormat2 are zero, so there is "
              "no data to unpack."))
            
            return r
        
        if count != len(firstGlyphs):
            logger.error((
              'V0324',
              (count, len(firstGlyphs)),
              "The PairSetCount is %d, which does not match the "
              "Coverage length %d."))
            
            return None
        
        if w.length() < 2 * count:
            logger.error((
              'V0325',
              (),
              "Insufficient bytes for the PairSetOffset table."))
            
            return None
        
        offsets = w.group("H", count)
        f = pairvalues.PairValues.fromvalidatedwalker
        Key = pairglyphs_key.Key
        
        for i, firstGlyph in enumerate(firstGlyphs):
            wSub = w.subWalker(offsets[i])
            
            if wSub.length() < 2:
                logger.error((
                  'V0326',
                  (),
                  "Insufficient bytes for the PairValueCount."))
                
                return None
            
            wSubBase = wSub.subWalker(0, relative=True)
            count = wSub.unpack("H")
            prevSecondGlyph = None
            
            while count:
                if wSub.length() < 2:
                    logger.error((
                      'V0327',
                      (),
                      "Insufficient bytes for the PairValueRecord."))
                    
                    return None
                
                secondGlyph = wSub.unpack("H")
                
                if prevSecondGlyph is not None:
                    if secondGlyph < prevSecondGlyph:
                        logger.error((
                          'E4101',
                          (),
                          "PairValueRecords not sorted by second glyph."))
                        
                        return None
                    
                    elif secondGlyph == prevSecondGlyph:
                        logger.error((
                          'V0329',
                          (secondGlyph,),
                          "Glyph %d appears multiple times in the "
                          "same PairValueRecord."))
                        
                        return None
                
                prevSecondGlyph = secondGlyph
                itemLogger = logger.getChild("second glyph %d" % (secondGlyph,))
                
                pv = f(
                  wSub,
                  posBase = wSubBase,
                  valueFormatFirst = vf1,
                  valueFormatSecond = vf2,
                  logger = itemLogger,
                  otcommondeltas = otcd)
                
                if pv is None:
                    return None
                
                r[Key([firstGlyph, secondGlyph])] = pv
                count -= 1
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PairGlyphs object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == PairGlyphs.frombytes(obj.binaryString())
        True
        """
        
        otcd = kwArgs.get('otcommondeltas')
        
        format = w.unpack("H")
        assert format == 1
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        firstGlyphs = sorted(covTable)
        vf1, vf2, count = w.unpack("3H")
        assert count == len(firstGlyphs)
        offsets = w.group("H", count)
        r = cls()
        f = pairvalues.PairValues.fromwalker
        Key = pairglyphs_key.Key
        
        for i, firstGlyph in enumerate(firstGlyphs):
            wSub = w.subWalker(offsets[i])
            wSubBase = wSub.subWalker(0, relative=True)
            count = wSub.unpack("H")
            
            while count:
                secondGlyph = wSub.unpack("H")
                
                pv = f(
                  wSub,
                  posBase = wSubBase,
                  valueFormatFirst = vf1,
                  valueFormatSecond = vf2,
                  otcommondeltas=otcd)
                
                r[Key([firstGlyph, secondGlyph])] = pv
                count -= 1
        
        return r
    
    def getMasks(self):
        """
        Returns a pair with the computed mask values for first and second,
        which will range over all contained PairValues objects.
        """
        
        v = [obj.getMasks() for obj in self.values()]
        m1 = functools.reduce(operator.or_, (obj[0] for obj in v), False)
        m2 = functools.reduce(operator.or_, (obj[1] for obj in v), False)
        return (m1, m2)
    
    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        Do the processing for a single glyph in the specified glyph array. This
        method is called by the runOne_GPOS() method of the Lookup (which is,
        in turn, called by the run() method there).
        
        This method returns a pair of values. The first value will be None if
        no processing was actually done; otherwise it will be an array of
        Effect objects of the same length as glyphArray. The second value is
        the number of glyph indices involved (or zero if no matching occurred).
        
        The OpenType spec states that the second glyph of the pair is only
        eligible to be the first glyph of a subsequent pair if its Value is
        None (i.e. zero) in the first pair. Otherwise the second glyph is
        considered the same as any other context glyph, and is skipped by all
        subsequent subtables in the Lookup. See the examples below for cases
        where the returned count is 1 or 2.
        
        >>> valObj1 = value.Value(xAdvance=-15)
        >>> valObj2 = value.Value(yPlacement=20)
        >>> pvObj1 = pairvalues.PairValues(first=valObj1)
        >>> pvObj2 = pairvalues.PairValues(first=valObj1, second=valObj2)
        >>> key1 = pairglyphs_key.Key([8, 20])
        >>> key2 = pairglyphs_key.Key([8, 15])
        >>> obj = PairGlyphs({key1: pvObj1, key2: pvObj2})
        >>> obj.pprint()
        Key((8, 15)):
          First adjustment:
            FUnit adjustment to horizontal advance: -15
          Second adjustment:
            FUnit adjustment to origin's y-coordinate: 20
        Key((8, 20)):
          First adjustment:
            FUnit adjustment to horizontal advance: -15
        
        >>> ga = runningglyphs.GlyphList.fromiterable([8, 8, 77, 20, 8, 77, 15])
        >>> igsFunc = lambda *a, **k: [False, False, True, False, False, True, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> (r, count)
        (None, 0)
        
        >>> r, count = obj.runOne(ga, 1, igsFunc=igsFunc)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 8, originalOffset = 0 
        glyph 8, originalOffset = 1 xAdvanceDelta = -15
        glyph 77, originalOffset = 2 
        glyph 20, originalOffset = 3 
        glyph 8, originalOffset = 4 
        glyph 77, originalOffset = 5 
        glyph 15, originalOffset = 6 
        
        >>> r, count = obj.runOne(ga, 4, igsFunc=igsFunc, cumulEffects=r)
        >>> count
        2
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 8, originalOffset = 0 
        glyph 8, originalOffset = 1 xAdvanceDelta = -15
        glyph 77, originalOffset = 2 
        glyph 20, originalOffset = 3 
        glyph 8, originalOffset = 4 xAdvanceDelta = -15
        glyph 77, originalOffset = 5 
        glyph 15, originalOffset = 6 yPlacementDelta = 20
        """
        
        igsFunc = kwArgs['igsFunc']
        igs = igsFunc(glyphArray, **kwArgs)
        
        v = [
          (g, i)
          for i, g in enumerate(glyphArray[startIndex:], start=startIndex)
          if (not igs[i])]
        
        if len(v) < 2:
            return (None, 0)
        
        vNonIgs = [x[0] for x in v]
        vBackMap = [x[1] for x in v]
        key = tuple(vNonIgs[:2])
        
        if key not in self:
            return (None, 0)
        
        # If we get here it's an actual kerning pair
        
        E = effect.Effect
        fv = E.fromvalue
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        pvObj = self[key]
        r[vBackMap[0]].add(fv(pvObj.first, **kwArgs))
        r[vBackMap[1]].add(fv(pvObj.second, **kwArgs))
        return (r, (2 if pvObj.second is not None else 1))

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write PairValues for our keys. Must pass in the following kwArgs
        to PairValues.writeFontWorkerSource():
            lbl_first: string to use for 'first'
            lbl_second: string to use for 'second'
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        for k in sorted(self):
            self[k].writeFontWorkerSource(
              s,
              lbl_first = bnfgi(k[0]),
              lbl_second = bnfgi(k[1]))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.GPOS import value
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    kv = pairglyphs_key._testingValues
    pv = pairvalues._testingValues
    
    _testingValues = (
        PairGlyphs({
          kv[0]: pv[0],
          kv[1]: pv[1],
          kv[2]: pv[2]}),)
    
    del kv, pv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'B': 2,
        'C': 3,
        'D': 4,
        'E': 5,
        'F': 6,
        'G': 7,
        'H': 8,
        'I': 9,
        'J': 10,
        'K': 11,
        'L': 12,
        'M': 13,
        'N': 14,
        'O': 15,
        'P': 16
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        left x placement	A	B	-123
        right x placement	C	D	-456
        left x advance	E	F	789
        right x advance	G	H	987
        left y placement	I	J	-654
        right y placement	K	L	-321
        left y advance	M	N	246
        right y advance	O	P	802
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        left x placement	A	B	-123
        right x placement	X	D	-456
        left x advance	E	Y	789
        right x advance	G	H	987
        lookup end
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
