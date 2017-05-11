#
# pairclasses.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 GPOS pair positioning tables.
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
from fontio3.GPOS import effect, pairclasses_key, pairvalues, value

from fontio3.opentype import (
  classdef,
  coverage,
  coverageset,
  coverageutilities,
  glyphset,
  runningglyphs)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _canRemove(obj, key, **kwArgs):
    if (
      key[0] not in set(obj.classDef1.values()) or
      key[1] not in set(obj.classDef2.values())):
        
        return True
    
    if not obj[key]:
        return True
    
    return False


def _getremapping(classDef, **kwArgs):
    """
    Return an oldToNew map of classDef mappings, removing gaps and explicit 0
    mappings.
    """
    allclasses = set(classDef.values())
    haszero = 0 in allclasses
    if haszero:
        allclasses.remove(0)
    oldtonew = {cv:i+1 for i,cv in enumerate(sorted(allclasses))}
    if haszero:
        oldtonew[0] = max(oldtonew.values()) + 1
    
    return oldtonew


def _reindexed(pairmap, cd1, cd2, **kwArgs):
    """
    Return a 3-tuple consisting of a re-mapped pairmap, classDef1, and
    classDef2, removing all non-contiguous class entries and unused keys.
    """
    logger = kwArgs['logger']

    # first clean up
    cd1v = set(cd1.values())
    cd2v = set(cd2.values())

    newpairs_1 = {}
    for pairkey in pairmap:
        if pairkey[0] in cd1v and pairkey[1] in cd2v:
            newpairs_1[pairkey] = pairmap[pairkey]
        else:
            logger.warning((
                'Vxxxx',
                (pairkey,),
                "Removing class pair %s: first or second not listed in class defs"))

    k0 = [k[0] for k in newpairs_1]
    k1 = [k[1] for k in newpairs_1]

    cd1todelete = [k for k,v in cd1.items() if v not in k0]
    cd2todelete = [k for k,v in cd2.items() if v not in k1]

    for k in cd1todelete:
        logger.warning((
            'Vxxxx',
            (k, cd1[k]),
            "Removing glyph %d from firstclasses because its "
            "class (%d) is not used in any PairClasses key"))
        del(cd1[k])
        
    for k in cd2todelete:
        logger.warning((
            'Vxxxx',
            (k, cd2[k]),
            "Removing glyph %d from secondclasses because its "
            "class (%d) is not used in any PairClasses key"))
        del(cd2[k])


    # now reindex
    oldtonew1 = _getremapping(cd1)
    oldtonew2 = _getremapping(cd2)

    newpairs_2 = {}
    for pairkey in newpairs_1:
        newkey = (oldtonew1.get(pairkey[0]), oldtonew2.get(pairkey[1]))
        if newkey[0] and newkey[1]:
            vv = pairmap[pairkey]
            newpairs_2[newkey] = pairvalues.PairValues(vv[0], vv[1])
        else:
            logger.warning((
                'Vxxxx',
                (pairkey,),
                "Removing class pair %s: first or second class empty or missing"))
                
    newcd1 = {g:oldtonew1[cl] for g,cl in cd1.items()}
    newcd2 = {g:oldtonew2[cl] for g,cl in cd2.items()}

    return newpairs_2, classdef.ClassDef(newcd1), classdef.ClassDef(newcd2)


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

class PairClasses(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing format 2 pair GPOS tables.
    
    These are dicts mapping Keys to PairValues.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    (First class 1, Second class 1):
      Second adjustment:
        FUnit adjustment to origin's x-coordinate: -10
    (First class 2, Second class 0):
      First adjustment:
        Device for vertical advance:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
    (First class 2, Second class 1):
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
    Class definition table for first glyph:
      xyz16: 1
      xyz6: 1
      xyz7: 1
      xyz8: 2
    Class definition table for second glyph:
      xyz21: 1
      xyz22: 1
      xyz23: 1
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_keyfollowsprotocol = True,
        
        item_pprintlabelfunc = (
          lambda k:
          "(First class %d, Second class %d)" % k),
        
        item_pprintlabelpresort = True,
        map_compactiblefunc = _canRemove,
        map_compactremovesfalses = True,
        map_maxcontextfunc = (lambda d: 2),
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        classDef1 = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Class definition table for first glyph"),
        
        classDef2 = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Class definition table for second glyph"),
        
        coverageExtras = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = glyphset.GlyphSet,
            attr_label = "Coverage glyphs not in ClassDef1",
            attr_showonlyiftrue = True))
    
    kind = ('GPOS', 2)
    kindString = "Pair (class) positioning table"
    
    #
    # Methods
    #
    
    def asVOLT(self, lookupLabel, **kwArgs):
        """
        Returns 1) VOLT-compatible Glyph Group definitions (.vtg) and 2)
        VOLT-compatible lookup definition (.vtl) for the object using the label
        'lookupLabel', or None if the Value mask is something other than
        horizontal advance. The following keyword arguments are supported:
        
            editor      An Editor-class object, used to obtain glyph names.
        """
        
        if self.coverageExtras:
            raise ValueError("VOLT doesn't represent coverage extras!")
        
        editor = kwArgs.get('editor')
        mFirst, mSecond = self.getMasks()
        
        if (mFirst & 0xFFFB) or (mSecond & 0xFFFB) or (editor is None):
            return None
        
        gv = ["\r"]
        groupsafelabel = lookupLabel.replace("\\", "")
        s = r'DEF_LOOKUP "%s" PROCESS_BASE SKIP_MARKS DIRECTION LTR'
        
        sv = [
          s % (lookupLabel,),
          "IN_CONTEXT",
          "END_CONTEXT",
          "AS_POSITION",
          "ADJUST_PAIR"]

        nm = editor.getNamer().bestNameForGlyphIndex
        
        # Build class:glyphlist dicts for GROUP definitions
        firstClasses = {}
        secondClasses = {}
        
        for g in sorted(self.classDef1):
            gclass = self.classDef1[g]
            firstClasses.setdefault(gclass, []).append(g)
        
        for g in sorted(self.classDef2):
            gclass = self.classDef2[g]
            secondClasses.setdefault(gclass, []).append(g)

        #build groups string
        for c in sorted(firstClasses):
            gv.append('DEF_GROUP "kern_1ST_%d_%s"' % (c, groupsafelabel))
            gs = ['GLYPH "%s"' % (nm(i),) for i in firstClasses[c]]
            gv.append("ENUM %s END_ENUM" % (' '.join(gs),))
            gv.append("END_GROUP")
            
        for c in sorted(secondClasses):
            gv.append('DEF_GROUP "kern_2ND_%d_%s"' % (c, groupsafelabel))
            gs = ['GLYPH "%s"' % (nm(i),) for i in secondClasses[c]]
            gv.append("ENUM %s END_ENUM" % (' '.join(gs),))
            gv.append("END_GROUP")
        
        gv.append("END")
            
        # the lookup itself is just enumerating self.keys and the values.
        firstIndices = set(x[0] for x in self)
        secondIndices = set(x[1] for x in self)
        
        s = ' '.join(
          'FIRST  GROUP "kern_1ST_%d_%s"' % (i, groupsafelabel)
          for i in firstIndices)
        
        sv.append(s)
        
        s = ' '.join(
          'SECOND  GROUP "kern_2ND_%d_%s"' % (i, groupsafelabel)
          for i in secondIndices)
        
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
            
            d[key] = (
              " %d %d BY POS ADV %sEND_POS POS %sEND_POS" %
              (key[0], key[1], part1, part2))
        
        for key in sorted(d):
            sv.append(d[key])
        
        sv.extend(["END_ADJUST", "END_POSITION", " END"])
        return ('\r'.join(gv), '\r'.join(sv))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PairClasses object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0002 004C 0081 0031  0058 006E 0003 0002 |...L...1.X.n....|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 FFF6 0000 0000  0000 0084 0000 0000 |................|
              40 | 0000 001E 0084 0000  0084 0078 0001 0004 |...........x....|
              50 | 0005 0006 0007 000F  0002 0003 0005 0006 |................|
              60 | 0001 0007 0007 0002  000F 000F 0001 0002 |................|
              70 | 0001 0014 0016 0001  000C 0014 0002 BDF0 |................|
              80 | 0020 3000 000C 0012  0001 8C04           |. 0.........    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 2)  # format 2
        s = set(self.classDef1) | self.coverageExtras
        covTable = coverage.Coverage.fromglyphset(s)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        vf1, vf2 = self.getMasks()
        w.add("HH", vf1, vf2)
        cd1Stake = w.getNewStake()
        cd2Stake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, cd1Stake)
        w.addUnresolvedOffset("H", stakeValue, cd2Stake)
        count1 = 1 + utilities.safeMax(self.classDef1.values())
        count2 = 1 + utilities.safeMax(self.classDef2.values())
        w.add("HH", count1, count2)
        emptyPV = pairvalues.PairValues(value.Value(), value.Value())
        devicePool = {}
        Key = pairclasses_key.Key
        
        for c1 in range(count1):
            for c2 in range(count2):
                obj = self.get(Key([c1, c2]), emptyPV)
                
                obj.buildBinary(
                  w,
                  devicePool = devicePool,
                  posBase = stakeValue,
                  valueFormatFirst = vf1,
                  valueFormatSecond = vf2,
                  **kwArgs)
        
        # Now add the deferred objects
        covTable.buildBinary(w, stakeValue=covStake)
        self.classDef1.buildBinary(w, stakeValue=cd1Stake)
        self.classDef2.buildBinary(w, stakeValue=cd2Stake)
        
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
        
        >>> K = pairclasses_key.Key
        >>> V = value.Value
        >>> PV = pairvalues.PairValues
        >>> obj = PairClasses({
        ...   K([1, 2]): PV(V(xAdvance=20), V(xPlacement=30)),
        ...   K([2, 1]): PV(V(xAdvance=20), V(yPlacement=30)),
        ...   K([2, 2]): PV(V(xAdvance=20), V(xAdvance=30))},
        ...   classDef1 = classdef.ClassDef({40: 1, 50: 2, 60: 1}),
        ...   classDef2 = classdef.ClassDef({75: 1, 92: 2}))
        >>> d = obj.effectExtrema(forHorizontal=True)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        75 (30, 0)
        
        >>> d = obj.effectExtrema(forHorizontal=False)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        92 (30, 0)
        """
        
        cache = kwArgs.get('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        fv = effect.Effect.fromvalue
        others1 = others2 = None  # only fill these on-demand
        invMap1 = utilities.invertDictFull(self.classDef1, asSets=True)
        invMap2 = utilities.invertDictFull(self.classDef2, asSets=True)
        
        for (cls1, cls2), pvObj in self.items():
            if pvObj.first is not None:
                p = fv(pvObj.first).toPair(forHorizontal)
                
                if any(p):
                    if cls1:
                        glyphSet = invMap1[cls1]
                    
                    else:
                        if others1 is None:
                            fgc = utilities.getFontGlyphCount(**kwArgs)
                            others1 = set(range(fgc)) - set(self.classDef1)
                        
                        glyphSet = others1
                    
                    for g in glyphSet:
                        if g not in r:
                            r[g] = p
                        
                        else:
                            old = r[g]
                            
                            r[g] = tuple((
                              max(old[0], p[0]),
                              min(old[1], p[1])))
            
            if pvObj.second is not None:
                p = fv(pvObj.second).toPair(forHorizontal)
                
                if any(p):
                    if cls2:
                        glyphSet = invMap2[cls2]
                    
                    else:
                        if others2 is None:
                            fgc = utilities.getFontGlyphCount(**kwArgs)
                            others2 = set(range(fgc)) - set(self.classDef2)
                        
                        glyphSet = others2
                    
                    for g in glyphSet:
                        if g not in r:
                            r[g] = p
                        
                        else:
                            old = r[g]
                            
                            r[g] = tuple((
                              max(old[0], p[0]),
                              min(old[1], p[1])))
        
        cache[id(self)] = r
        return r
    
    @classmethod
    def fromformat2(cls, f2, **kwArgs):
        """
        Creates and returns a new PairClasses object from the specified
        kern.Format2 object.
        """
        
        r = cls(
          {},
          classDef1 = f2.leftClassDef,
          classDef2 = f2.rightClassDef)
        
        kFunc = pairclasses_key.Key
        vFunc = value.Value
        pvFunc = pairvalues.PairValues
        vPool = {}
        
        for cpObj, dist in f2.items():
            if not dist:
                continue
            
            if dist not in vPool:
                vPool[dist] = pvFunc(second=vFunc(xPlacement=dist))
            
            r[kFunc(cpObj)] = vPool[dist]
        
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new PairClasses object from the specified
        FontWorkerSource, with validation of the source data.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> pc = PairClasses.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.pairclasses - ERROR - line 13 -- unexpected token: foo
        >>> pc.pprint()
        (First class 1, Second class 2):
          First adjustment:
            FUnit adjustment to origin's x-coordinate: -123
        (First class 2, Second class 1):
          Second adjustment:
            FUnit adjustment to origin's x-coordinate: -456
        Class definition table for first glyph:
          2: 1
          3: 2
        Class definition table for second glyph:
          23: 1
          29: 2
        """

        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber=fws.lineNumber
        iskernset = kwArgs.get('iskernset', False)
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pairclasses")
        fvfws = classdef.ClassDef.fromValidatedFontWorkerSource
        PV = pairvalues.PairValues
        V = value.Value
        
        tokenSet = frozenset({
          'left x advance',
          'left x placement',
          'left y advance',
          'left y placement',
          'right x advance',
          'right x placement',
          'right y advance',
          'right y placement'})

        # place-holders
        classDef1 = classdef.ClassDef()
        classDef2 = classdef.ClassDef()
        pairDict = defaultdict(lambda: [None, None])
        
        for line in fws:
            if line.lower().strip() in terminalStrings:
                if iskernset and line.lower() == 'subtable end':
                    continue
                
                else:
                    npd, nc1, nc2 = _reindexed(
                      pairDict,
                      classDef1,
                      classDef2,
                      logger = logger)
                    
                    return cls(npd, classDef1=nc1, classDef2=nc2)

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]

                if tokens[0].lower() == 'firstclass definition begin':
                    classDef1 = fvfws(fws, logger=logger, **kwArgs)

                elif tokens[0].lower() == 'secondclass definition begin':
                    classDef2 = fvfws(fws, logger=logger, **kwArgs)

                elif tokens[0].lower() in tokenSet:
                    class1 = int(tokens[1])
                    class2 = int(tokens[2])
                    key = (class1, class2)
                    val= int(tokens[3])
                    
                    if val != 0:
                        pval = pairDict[key]
                        if tokens[0].lower() == 'left x advance':
                            if pval[0] and pval[0].xAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for class "
                                  "pair %s,%s"))
                            else:
                                if pval[0] is None:
                                    pval[0] = value.Value()
                                pval[0].xAdvance=val

                        elif tokens[0].lower() == 'right x advance':
                            if pval[1] and pval[1].xAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for class "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].xAdvance=val

                        elif tokens[0].lower() == 'left x placement':
                            if pval[0] and pval[0].xPlacement:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for class "
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
                                  "line %d -- ignoring duplicate %s for class "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].xPlacement = val

                        elif tokens[0].lower() == 'left y advance':
                            if pval[0] and pval[0].yAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for class "
                                  "pair %s,%s"))
                            else:
                                if pval[0] is None:
                                    pval[0] = value.Value()
                                pval[0].yAdvance=val

                        elif tokens[0].lower() == 'right y advance':
                            if pval[1] and pval[1].yAdvance:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for class "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].yAdvance=val

                        elif tokens[0].lower() == 'left y placement':
                            if pval[0] and pval[0].yPlacement:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for class "
                                  "pair %s,%s"))
                            else:
                                if pval[0] is None:
                                    pval[0] = value.Value()
                                pval[0].yPlacement=val

                        elif tokens[0].lower() == 'right y placement':
                            if pval[1] and pval[1].yPlacement:
                                logger.warning((
                                  'Vxxxx',
                                  (fws.lineNumber, tokens[0], tokens[1], tokens[2]),
                                  "line %d -- ignoring duplicate %s for class "
                                  "pair %s,%s"))
                            else:
                                if pval[1] is None:
                                    pval[1] = value.Value()
                                pval[1].yPlacement=val

                else:
                    logger.error((
                        'V0960',
                        (fws.lineNumber, tokens[0]),
                        'line %d -- unexpected token: %s'))
                
        logger.error((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))

        if pairDict and classDef1 and classDef2:
            r = cls(pairDict, classDef1=classDef1, classDef2=classDef2)

        else:
            logger.error((
              'Vxxxx',
              (),
              "Incomplete or invalid lookup data for pair classes."))
            
            r = None

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PairClasses object from the specified walker,
        with validation of the source data.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("pctest")
        >>> fvb = PairClasses.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        pctest.pairclasses - DEBUG - Walker has 140 remaining bytes.
        pctest.pairclasses.coverage - DEBUG - Walker has 64 remaining bytes.
        pctest.pairclasses.coverage - DEBUG - Format is 1, count is 4
        pctest.pairclasses.coverage - DEBUG - Raw data are [5, 6, 7, 15]
        pctest.pairclasses.first.classDef - DEBUG - Walker has 52 remaining bytes.
        pctest.pairclasses.first.classDef - DEBUG - ClassDef is format 2.
        pctest.pairclasses.first.classDef - DEBUG - Count is 3
        pctest.pairclasses.first.classDef - DEBUG - Raw data are [(5, 6, 1), (7, 7, 2), (15, 15, 1)]
        pctest.pairclasses.second.classDef - DEBUG - Walker has 30 remaining bytes.
        pctest.pairclasses.second.classDef - DEBUG - ClassDef is format 2.
        pctest.pairclasses.second.classDef - DEBUG - Count is 1
        pctest.pairclasses.second.classDef - DEBUG - Raw data are [(20, 22, 1)]
        pctest.pairclasses.class (0,0).pairvalues - DEBUG - Walker has 124 remaining bytes.
        pctest.pairclasses.class (0,0).pairvalues.value - DEBUG - Walker has 124 remaining bytes.
        pctest.pairclasses.class (0,0).pairvalues.value - DEBUG - Walker has 120 remaining bytes.
        pctest.pairclasses.class (0,1).pairvalues - DEBUG - Walker has 114 remaining bytes.
        pctest.pairclasses.class (0,1).pairvalues.value - DEBUG - Walker has 114 remaining bytes.
        pctest.pairclasses.class (0,1).pairvalues.value - DEBUG - Walker has 110 remaining bytes.
        pctest.pairclasses.class (1,0).pairvalues - DEBUG - Walker has 104 remaining bytes.
        pctest.pairclasses.class (1,0).pairvalues.value - DEBUG - Walker has 104 remaining bytes.
        pctest.pairclasses.class (1,0).pairvalues.value - DEBUG - Walker has 100 remaining bytes.
        pctest.pairclasses.class (1,1).pairvalues - DEBUG - Walker has 94 remaining bytes.
        pctest.pairclasses.class (1,1).pairvalues.value - DEBUG - Walker has 94 remaining bytes.
        pctest.pairclasses.class (1,1).pairvalues.value - DEBUG - Walker has 90 remaining bytes.
        pctest.pairclasses.class (2,0).pairvalues - DEBUG - Walker has 84 remaining bytes.
        pctest.pairclasses.class (2,0).pairvalues.value - DEBUG - Walker has 84 remaining bytes.
        pctest.pairclasses.class (2,0).pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
        pctest.pairclasses.class (2,0).pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        pctest.pairclasses.class (2,0).pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
        pctest.pairclasses.class (2,0).pairvalues.value - DEBUG - Walker has 80 remaining bytes.
        pctest.pairclasses.class (2,1).pairvalues - DEBUG - Walker has 74 remaining bytes.
        pctest.pairclasses.class (2,1).pairvalues.value - DEBUG - Walker has 74 remaining bytes.
        pctest.pairclasses.class (2,1).pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
        pctest.pairclasses.class (2,1).pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        pctest.pairclasses.class (2,1).pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
        pctest.pairclasses.class (2,1).pairvalues.value - DEBUG - Walker has 70 remaining bytes.
        pctest.pairclasses.class (2,1).pairvalues.value.xPlaDevice.device - DEBUG - Walker has 8 remaining bytes.
        pctest.pairclasses.class (2,1).pairvalues.value.xPlaDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        pctest.pairclasses.class (2,1).pairvalues.value.xPlaDevice.device - DEBUG - Data are (35844,)
        pctest.pairclasses.class (2,1).pairvalues.value.yPlaDevice.device - DEBUG - Walker has 20 remaining bytes.
        pctest.pairclasses.class (2,1).pairvalues.value.yPlaDevice.device - DEBUG - StartSize=12, endSize=20, format=2
        pctest.pairclasses.class (2,1).pairvalues.value.yPlaDevice.device - DEBUG - Data are (48624, 32, 12288)
        pctest.pairclasses - INFO - The following glyphs appear in non-first ClassDefs only, and are not in the Coverage: [20, 21, 22]
        pctest.pairclasses - INFO - The following glyphs appear in the Coverage and in only the first ClassDef: [5, 6, 7, 15]
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pairclasses")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 16:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 2:
            logger.error((
              'V0002',
              (format,),
              "Expected format 2, but got %d instead."))
            
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
        
        vf1, vf2 = w.unpack("2H")
        
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
            
            return None
        
        cdOffset1, cdOffset2, count1, count2 = w.unpack("4H")
        r = cls()
        fvw = classdef.ClassDef.fromvalidatedwalker
        subLogger = logger.getChild("first")
        r.classDef1 = fvw(w.subWalker(cdOffset1), logger=subLogger)
        
        if r.classDef1 is None:
            return None
        
        if count1 != len({0} | set(r.classDef1.values())):
            if count1 == (utilities.safeMax(r.classDef1.values()) + 1):
                logger.warning((
                  'V0911',
                  (),
                  "The values in ClassDef1 are sparse; they should be dense."))
            
            else:
                logger.error((
                  'V0332',
                  (),
                  "The Class1Count does not match the values in ClassDef1."))
            
                return None
        
        subLogger = logger.getChild("second")
        r.classDef2 = fvw(w.subWalker(cdOffset2), logger=subLogger)
        
        if r.classDef2 is None:
            return None
        
        if count2 != len({0} | set(r.classDef2.values())):
            if count2 == (utilities.safeMax(r.classDef2.values()) + 1):
                logger.warning((
                  'V0911',
                  (),
                  "The values in ClassDef2 are sparse; they should be dense."))
            
            else:
                logger.error((
                  'V0332',
                  (),
                  "The Class2Count does not match the values in ClassDef2."))
            
                return None
        
        fvw = pairvalues.PairValues.fromvalidatedwalker
        Key = pairclasses_key.Key
        unusedFirst = set(range(1, count1))
        unusedSecond = set(range(1, count2))
        
        for c1 in range(count1):
            for c2 in range(count2):
                subLogger = logger.getChild("class (%d,%d)" % (c1, c2))
                
                obj = fvw(
                  w,
                  posBase = w,
                  valueFormatFirst = vf1,
                  valueFormatSecond = vf2,
                  logger = subLogger,
                  **kwArgs)
                
                if obj is None:
                    return None
                
                if obj:  # only bother with nonzero PairValues
                    r[Key([c1, c2])] = obj
                    unusedFirst.discard(c1)
                    unusedSecond.discard(c2)
                
                elif c1 and c2:
                    logger.info((
                      'V0333',
                      (c1, c2),
                      "The PairValue for class (%d,%d) has no effect."))
        
        if unusedFirst:
            logger.warning((
              'V1073',
              (sorted(unusedFirst),),
              "The following classes are defined for ClassDef1 but "
              "no rules using them are present: %s"))
        
        if unusedSecond:
            logger.warning((
              'V1073',
              (sorted(unusedSecond),),
              "The following classes are defined for ClassDef2 but "
              "no rules using them are present: %s"))
        
        # Now that we have the keys we can reconcile
        
        okToProceed, covSet = coverageutilities.reconcile(
          covTable,
          r,
          [r.classDef1, r.classDef2],
          logger = logger,
          **kwArgs)
        
        r.coverageExtras.update(covSet - set(r.classDef1))
        
        if not okToProceed:
            r.clear()
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PairClasses object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == PairClasses.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        assert format == 2
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        vf1, vf2 = w.unpack("HH")
        r = cls()
        r.classDef1 = classdef.ClassDef.fromwalker(w.subWalker(w.unpack("H")))
        r.classDef2 = classdef.ClassDef.fromwalker(w.subWalker(w.unpack("H")))
        count1, count2 = w.unpack("HH")
        f = pairvalues.PairValues.fromwalker
        Key = pairclasses_key.Key
        
        for c1 in range(count1):
            for c2 in range(count2):
                obj = f(
                  w,
                  posBase = w,
                  valueFormatFirst = vf1,
                  valueFormatSecond = vf2,
                  **kwArgs)
                
                if obj:  # only bother with nonzero PairValues
                    r[Key([c1, c2])] = obj
        
        # Now that we have the keys we can reconcile
        
        okToProceed, covSet = coverageutilities.reconcile(
          covTable,
          r,
          [r.classDef1, r.classDef2],
          **kwArgs)
        
        r.coverageExtras.update(covSet - set(r.classDef1))
        
        if not okToProceed:
            r.clear()
        
        return r
    
    def getMasks(self):
        """
        Returns a pair with the computed mask values for first and second,
        which will range over all contained PairValues objects.
        """
        
        v = [obj.getMasks() for obj in self.values()]
        
        if not v:
            return (0, 0)
        
        m1 = functools.reduce(operator.or_, (obj[0] for obj in v))
        m2 = functools.reduce(operator.or_, (obj[1] for obj in v))
        return (m1, m2)
    
    def glyphsRenumbered(self, oldToNew, **kwArgs):
        """
        Returns a new PairClasses object whose classDefs are renumbered as
        specified. Note that this method also compacts the newly-renumbered
        class indices.
        """
        
        newCD1 = self.classDef1.glyphsRenumbered(oldToNew, **kwArgs)
        newCD2 = self.classDef2.glyphsRenumbered(oldToNew, **kwArgs)
        
        if not (newCD1 and newCD2):
            return type(self)()
        
        valid1 = set(newCD1.values())
        valid2 = set(newCD2.values())
        
        mNew = {}
        
        for key, value in self.items():
            if key[0] in valid1 and key[1] in valid2:
                mNew[key] = value
        
        # Remove any classDef entries that are not used
        
        cActuals = set(k[0] for k in mNew)
        cToDel = valid1 - cActuals
        valid1 = cActuals
        gToDel = set(g for g, c in newCD1.items() if c in cToDel)
        
        for g in gToDel:
            del newCD1[g]
        
        cActuals = set(k[1] for k in mNew)
        cToDel = valid2 - cActuals
        valid2 = cActuals
        gToDel = set(g for g, c in newCD2.items() if c in cToDel)
        
        for g in gToDel:
            del newCD2[g]
        
        # Now renumber the classes to a tight set
        
        if 0 in valid1:
            renum1 = {n: i for i, n in enumerate(sorted(valid1))}
        else:
            renum1 = {n: i+1 for i, n in enumerate(sorted(valid1))}
        
        if 0 in valid2:
            renum2 = {n: i for i, n in enumerate(sorted(valid2))}
        else:
            renum2 = {n: i+1 for i, n in enumerate(sorted(valid2))}
        
        for g in newCD1:
            newCD1[g] = renum1[newCD1[g]]
        
        for g in newCD2:
            newCD2[g] = renum2[newCD2[g]]
        
        mNew2 = {}
        K = pairclasses_key.Key
        
        for key, value in mNew.items():
            mNew2[K([renum1[key[0]], renum2[key[1]]])] = value
        
        # Renumber the coverageExtras
        if 'keepMissing' in kwArgs:
            del kwArgs['keepMissing']
        
        covExtra = self.coverageExtras.glyphsRenumbered(
          oldToNew,
          keepMissing = False)
        
        r = type(self)(mNew2)
        r.classDef1 = newCD1
        r.classDef2 = newCD2
        r.coverageExtras.update(covExtra or set())
        return r
    
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
        >>> key1 = pairclasses_key.Key([1, 1])
        >>> key2 = pairclasses_key.Key([1, 2])
        >>> obj = PairClasses(
        ...   {key1: pvObj1, key2: pvObj2},
        ...   classDef1 = classdef.ClassDef({8: 1}),
        ...   classDef2 = classdef.ClassDef({15: 2, 20: 1}))
        >>> obj.pprint()
        (First class 1, Second class 1):
          First adjustment:
            FUnit adjustment to horizontal advance: -15
        (First class 1, Second class 2):
          First adjustment:
            FUnit adjustment to horizontal advance: -15
          Second adjustment:
            FUnit adjustment to origin's y-coordinate: 20
        Class definition table for first glyph:
          8: 1
        Class definition table for second glyph:
          15: 2
          20: 1
        
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
        keyG = tuple(vNonIgs[:2])
        g1, g2 = keyG
        cd1 = self.classDef1
        cd2 = self.classDef2
        c1 = cd1.get(g1, (0 if g1 in self.coverageExtras else -1))
        c2 = cd2.get(g2, 0)
        keyC = (c1, c2)
        
        if keyC not in self:
            return (None, 0)
        
        # If we get here it's an actual kerning pair
        
        E = effect.Effect
        fv = E.fromvalue
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        pvObj = self[keyC]
        r[vBackMap[0]].add(fv(pvObj.first, **kwArgs))
        r[vBackMap[1]].add(fv(pvObj.second, **kwArgs))
        return (r, (2 if pvObj.second is not None else 1))

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write Class definitions and PairValues for our keys. Must pass
        in the following kwArgs to PairValues.writeFontWorkerSource():
            lbl_first: string to use for 'first'
            lbl_second: string to use for 'second'
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        # re-map implied first class 0 (coverageExtras) to real class
        ceclass = (
          max(list(self.classDef1.values()) or [0]) + 1 if self.coverageExtras
          else None)

        s.write("firstclass definition begin\n")
        
        for gi in sorted(self.classDef1, key=lambda x:(self.classDef1[x], x)):
            s.write("%s\t%d\n" % (bnfgi(gi), self.classDef1[gi]))
            
            if ceclass is not None:
                s.write("%% NOTE: class 0 was renumbered to class %d\n" % (ceclass,))
                
                for ceg in sorted(self.coverageExtras):
                    s.write("%s\t%d\n" % (bnfgi(ceg), ceclass))
        
        s.write("class definition end\n\n")
        s.write("secondclass definition begin\n")
        
        for gi in sorted(self.classDef2, key=lambda x:(self.classDef2[x], x)):
            s.write("%s\t%d\n" % (bnfgi(gi), self.classDef2[gi]))
        
        s.write("class definition end\n\n")
        renumberedentries = {}
        
        for k in sorted(self):
            first = k[0]
            
            if ceclass is not None and first == 0:
                renumberedentries[(first, k[1])] = self[k]

            else:
                self[k].writeFontWorkerSource(
                  s,
                  lbl_first=str(first),
                  lbl_second=str(k[1]))

        for k in sorted(renumberedentries):
            self[k].writeFontWorkerSource(
              s,
              lbl_first=str(ceclass),
              lbl_second=str(k[1]))

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
    
    c1 = classdef.ClassDef({5: 1, 6: 1, 7: 2, 15: 1})
    c2 = classdef.ClassDef({20: 1, 21: 1, 22: 1})
    pv = pairvalues._testingValues
    kv = pairclasses_key._testingValues
    
    _testingValues = (
        PairClasses(
            {kv[0]: pv[0], kv[1]: pv[1], kv[2]: pv[2]},
            classDef1 = c1,
            classDef2 = c2),)
    
    del c1, c2, pv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 2,
        'B': 3,
        'C': 5,
        'D': 7,
        'E': 11,
        'F': 13,
        'G': 17,
        'H': 19,
        'I': 23,
        'J': 29,
        'K': 31,
        'L': 37,
        'M': 41,
        'N': 43,
        'O': 47,
        'P': 53
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        firstclass definition begin
        A	1
        B	2
        C	3
        D	4
        E	5
        F	6
        G	7
        H	8
        class definition end
        
        secondclass definition begin
        I	1
        J	2
        class definition end
        
        left x placement	1	2	-123
        right x placement	2	1	-456
        left x advance	3	1	789
        right x advance	4	2	987
        left y placement	5	1	-654
        right y placement	6	2	-321
        left y advance	7	1	246
        right y advance	8	2	802
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        firstclass definition begin
        A	1
        B	2
        class definition end
        
        secondclass definition begin
        I	1
        J	2
        class definition end
        
        left x placement	1	2	-123
        foo
        right x placement	2	1	-456
        lookup end
        """))


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
