#
# marktobase.py
#
# Copyright © 2007-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 4 (Mark-to-Base) subtables for a GPOS table.
"""

# System imports
from collections import defaultdict
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta

from fontio3.GPOS import (
  anchor_coord,
  anchor_point,
  basearray,
  baserecord,
  effect,
  markarray,
  markrecord)

from fontio3.opentype import coverage, runningglyphs
from fontio3.opentype.fontworkersource import fwsint

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    markClassCount = 1 + utilities.safeMax(
      rec.markClass
      for rec in obj.mark.values())
    
    # all BaseRecords must be at least markClassCount long
    if any(len(rec) != markClassCount for rec in obj.base.values()):
        logger.error((
          'V0347',
          (),
          "The BaseRecords' lengths do not match the mark class count."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class MarkToBase(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing OpenType mark-to-base positioning data. These are
    simple objects with two attributes: mark (a MarkArray), and base (a
    BaseArray).
    
    >>> obj, ed = _makeTest()
    >>> obj.pprint()
    Mark Array:
      12:
        Mark Class: 0
        Mark Anchor:
          x-coordinate: 250
          y-coordinate: 110
      13:
        Mark Class: 0
        Mark Anchor:
          x-coordinate: 350
          y-coordinate: 100
      14:
        Mark Class: 1
        Mark Anchor:
          x-coordinate: 350
          y-coordinate: -20
      15:
        Mark Class: 1
        Mark Anchor:
          x-coordinate: 255
          y-coordinate: 5
    Base Array:
      40:
        Class 0:
          x-coordinate: 300
          y-coordinate: 1700
        Class 1:
          x-coordinate: 290
          y-coordinate: -75
      45:
        Class 0:
          x-coordinate: 450
          y-coordinate: 1600
        Class 1:
          x-coordinate: 450
          y-coordinate: -30
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        mark = dict(
            attr_followsprotocol = True,
            attr_initfunc = markarray.MarkArray,
            attr_label = "Mark Array"),
        
        base = dict(
            attr_followsprotocol = True,
            attr_initfunc = basearray.BaseArray,
            attr_label = "Base Array"))
    
    attrSorted = ('mark', 'base')
    
    objSpec = dict(
        obj_boolfalseiffalseset = set(['mark', 'base']),
        obj_validatefunc_partial = _validate)
    
    kind = ('GPOS', 4)
    kindString = "Mark-to-base positioning table"
    
    #
    # Methods
    #
    
    def _runOne_LR(self, glyphArray, startIndex, **kwArgs):
        """
        
        >>> anchor1 = anchor_coord.Anchor_Coord(950, 1100)
        >>> markRec1 = markrecord.MarkRecord(markAnchor=anchor1)  # class 0
        >>> markArray1 = markarray.MarkArray({12: markRec1})
        >>> anchor2 = anchor_coord.Anchor_Coord(1200, 1800)
        >>> baseRec1 = baserecord.BaseRecord([anchor2])
        >>> baseArray1 = basearray.BaseArray({35: baseRec1})
        >>> obj = MarkToBase(mark=markArray1, base=baseArray1)
        >>> ed = utilities.fakeEditor(80, hmtx={35: 1900, 12: 0, 77: 0})
        >>> ga = runningglyphs.GlyphList.fromiterable([35, 77, 12])
        >>> def funcIgs(*a, **k):
        ...   k['wantMarks'][:] = [False, False, True]
        ...   return [False, True, False]
        >>> r, count = obj._runOne_LR(ga, 2, igsFunc=funcIgs, editor=ed)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 35, originalOffset = 0 
        glyph 77, originalOffset = 1 
        glyph 12, originalOffset = 2 xPlacementDelta = -1650, yPlacementDelta = 700, backIndex = -2
        """
        
        igsFunc = kwArgs['igsFunc']
        isMark = []
        igs = igsFunc(glyphArray, wantMarks=isMark, **kwArgs)
        igOrMark = list(map(operator.or_, igs, isMark))
        gMark = glyphArray[startIndex]
        mark = self.mark
        
        if (not isMark[startIndex]) or (gMark not in mark):
            return (None, 0)
        
        walk = startIndex
        
        while (walk >= 0) and igOrMark[walk]:  # look for prior base
            walk -= 1
        
        if walk == -1:
            return (None, 0)
        
        base = self.base
        E = effect.Effect
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        gBase = glyphArray[walk]
        
        if gBase not in base:
            return (None, 0)
        
        ba = base[gBase]
        mo = mark[gMark]
        baseDelta = ba[mo.markClass]
        
        if baseDelta is None:
            return (None, 0)
        
        # Whew. Everything is right, so we actually do the move.
        
        markDelta = mo.markAnchor
        effLeft = r[walk]
        mtxTable = kwArgs['editor'].hmtx  # vertical at some point?
        
        # Because some ignored glyphs might actually have advances, we go thru
        # and accumulate the total advances from the base up to, but NOT
        # including, the mark.
        
        cumulWidth = 0
        
        for cwIndex in range(walk, startIndex):  # *not* including startIndex!
            if not igOrMark[cwIndex]:
                cumulWidth += mtxTable[glyphArray[cwIndex]].advance
            elif r[cwIndex].xAdvanceDelta:
                cumulWidth += r[cwIndex].xAdvanceDelta
        
        # Process variations to the anchors (if any)
        
        varBDelX = varBDelY = varMDelX = varMDelY = 0
        coordLAC = kwArgs.get('coordinateTuple', None)
        
        if coordLAC is not None:
            if baseDelta.anchorKind == 'variation':
                if baseDelta.xVariation is not None:
                    varBDelX = int(round(baseDelta.xVariation.interpolate(coordLAC)))
                if baseDelta.yVariation is not None:
                    varBDelY = int(round(baseDelta.yVariation.interpolate(coordLAC)))
            
            if markDelta.anchorKind == 'variation':
                if markDelta.xVariation is not None:
                    varMDelX = int(round(markDelta.xVariation.interpolate(coordLAC)))
                if markDelta.yVariation is not None:
                    varMDelY = int(round(markDelta.yVariation.interpolate(coordLAC)))
        
        deltaX = sum((
          -(markDelta.x + varMDelX),
          -effLeft.xAdvanceDelta,
          -cumulWidth,
          effLeft.xPlacementDelta,
          (baseDelta.x - varBDelX)))
    
        deltaY = sum((
          -(markDelta.y + varMDelY),
          -effLeft.yAdvanceDelta,
          # 0, -- change this when vertical text is supported
          effLeft.yPlacementDelta,
          (baseDelta.y - varBDelY)))
        
        r[startIndex].xPlacementDelta += deltaX
        r[startIndex].yPlacementDelta += deltaY
        r[startIndex].backIndex = walk - startIndex
        return (r, 1)
    
    def _runOne_RL(self, glyphArray, startIndex, **kwArgs):
        """
        
        >>> anchor1 = anchor_coord.Anchor_Coord(950, 1100)
        >>> markRec1 = markrecord.MarkRecord(markAnchor=anchor1)  # class 0
        >>> markArray1 = markarray.MarkArray({12: markRec1})
        >>> anchor2 = anchor_coord.Anchor_Coord(1200, 1800)
        >>> baseRec1 = baserecord.BaseRecord([anchor2])
        >>> baseArray1 = basearray.BaseArray({35: baseRec1})
        >>> obj = MarkToBase(mark=markArray1, base=baseArray1)
        >>> ed = utilities.fakeEditor(80)
        >>> ga = runningglyphs.GlyphList.fromiterable([35, 77, 12])
        >>> def funcIgs(*a, **k):
        ...   k['wantMarks'][:] = [False, False, True]
        ...   return [False, True, False]
        >>> igsFunc = lambda *a, **k: [False, True, False]
        >>> r, count = obj._runOne_RL(ga, 2, igsFunc=funcIgs, editor=ed)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 35, originalOffset = 0 
        glyph 77, originalOffset = 1 
        glyph 12, originalOffset = 2 xPlacementDelta = 250, yPlacementDelta = 700, backIndex = -2
        """
        
        igsFunc = kwArgs['igsFunc']
        isMark = []
        igs = igsFunc(glyphArray, wantMarks=isMark, **kwArgs)
        igOrMark = list(map(operator.or_, igs, isMark))
        gMark = glyphArray[startIndex]
        mark = self.mark
        
        if (not isMark[startIndex]) or (gMark not in mark):
            return (None, 0)
        
        walk = startIndex
        
        while (walk >= 0) and igOrMark[walk]:  # look for prior base
            walk -= 1
        
        if walk == -1:
            return (None, 0)
        
        base = self.base
        E = effect.Effect
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        gBase = glyphArray[walk]
        
        if gBase not in base:
            return (None, 0)
        
        ba = base[gBase]
        mo = mark[gMark]
        baseDelta = ba[mo.markClass]
        
        if baseDelta is None:
            return (None, 0)
        
        # Whew. Everything is right, so we actually do the move.
        
        markDelta = mo.markAnchor
        
        # Process variations to the anchors (if any)
        
        varBDelX = varBDelY = varMDelX = varMDelY = 0
        coordLAC = kwArgs.get('coordinateTuple', None)
        
        if coordLAC is not None:
            if baseDelta.anchorKind == 'variation':
                if baseDelta.xVariation is not None:
                    varBDelX = int(round(baseDelta.xVariation.interpolate(coordLAC)))
                if baseDelta.yVariation is not None:
                    varBDelY = int(round(baseDelta.yVariation.interpolate(coordLAC)))
            
            if markDelta.anchorKind == 'variation':
                if markDelta.xVariation is not None:
                    varMDelX = int(round(markDelta.xVariation.interpolate(coordLAC)))
                if markDelta.yVariation is not None:
                    varMDelY = int(round(markDelta.yVariation.interpolate(coordLAC)))
        
        # Right now we can ignore the advance metrics. However, if the case is
        # allowed where a base is followed by a ligature and then a mark, and
        # ignoreLigatures is True for the Lookup, then we might need to
        # compensate for the presence of the ligature as a width to be ignored.
        # I don't know what the OT spec says about cases like this:
        # specifically, whether the presence of a non-zero-width ignored glyph
        # between a base and its mark is permitted. It seems a very rare thing,
        # in any case.
        
        deltaX = sum((
          -(markDelta.x + varMDelX),
          -r[startIndex].xPlacementDelta,
          r[walk].xPlacementDelta,
          (baseDelta.x - varBDelX)))
    
        deltaY = sum((
          -(markDelta.y + varMDelY),
          -r[startIndex].yPlacementDelta,
          r[walk].yPlacementDelta,
          (baseDelta.y - varBDelY)))
        
        r[startIndex].xPlacementDelta += deltaX
        r[startIndex].yPlacementDelta += deltaY
        
        # I'm really uncertain whether the backIndex should reflect the
        # pre-bidi glyph array or the post-bidi glyph array. The backIndex is
        # attached to the Effect, and so is presumably used by clients like the
        # OT Debugger. But PFC (for instance) handles the bidi itself, so I'm
        # not sure this actually matters here.
        #
        # In any case, let it be documented that the backIndex here reflect the
        # pre-bidi glyph indices. If we decide to change this, the following
        # calculation should change to startIndex - walk.
        
        r[startIndex].backIndex = walk - startIndex
        return (r, 1)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> obj, ed = _makeTest()
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 000C 0016 0002  001E 0030 0002 0001 |...........0....|
              10 | 000C 000F 0000 0001  0002 0028 002D 0004 |...........(.-..|
              20 | 0000 001C 0000 0022  0001 0028 0001 002E |......."...(....|
              30 | 0002 0022 0028 002E  0034 0001 00FA 006E |...".(...4.....n|
              40 | 0001 015E 0064 0001  015E FFEC 0001 00FF |...^.d...^......|
              50 | 0005 0001 012C 06A4  0001 0122 FFB5 0001 |.....,....."....|
              60 | 01C2 0640 0001 01C2  FFE2                |...@......      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        markBackMap, baseBackMap = {}, {}
        
        markCovTable = coverage.Coverage.fromglyphset(
          self.mark,
          backMap = markBackMap)
        
        markCovStake = w.getNewStake()
        
        baseCovTable = coverage.Coverage.fromglyphset(
          self.base,
          backMap = baseBackMap)
        
        baseCovStake = w.getNewStake()
        
        markClassCount = 1 + utilities.safeMax(
          obj.markClass
          for obj in self.mark.values())
        
        w.add("H", 1)  # format 1
        w.addUnresolvedOffset("H", stakeValue, markCovStake)
        w.addUnresolvedOffset("H", stakeValue, baseCovStake)
        w.add("H", markClassCount)
        markStake = w.getNewStake()
        baseStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, markStake)
        w.addUnresolvedOffset("H", stakeValue, baseStake)
        
        # Resolve the references
        markCovTable.buildBinary(w, stakeValue=markCovStake, **kwArgs)
        baseCovTable.buildBinary(w, stakeValue=baseCovStake, **kwArgs)
        orderedKeys = []
        anchorPool = {}
        devicePool = {}
        
        d = {
          'anchorPool': anchorPool,
          'devicePool': devicePool,
          'orderedKeys': orderedKeys}
        
        self.mark.buildBinary(w, stakeValue=markStake, **d)
        self.base.buildBinary(w, stakeValue=baseStake, **d)
        kwArgs.pop('devicePool', None)
        
        for key in orderedKeys:
            obj, objStake = anchorPool[key]
            
            obj.buildBinary(
              w,
              stakeValue = objStake,
              devicePool = devicePool,
              **kwArgs)
        
        it = sorted(
          (obj.asImmutable(), obj, stake)
          for obj, stake in devicePool.values())
        
        for immut, obj, objStake in it:
            obj.buildBinary(w, stakeValue=objStake, **kwArgs)
    
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
        
        >>> obj, e = _makeTest()
        >>> obj.pprint()
        Mark Array:
          12:
            Mark Class: 0
            Mark Anchor:
              x-coordinate: 250
              y-coordinate: 110
          13:
            Mark Class: 0
            Mark Anchor:
              x-coordinate: 350
              y-coordinate: 100
          14:
            Mark Class: 1
            Mark Anchor:
              x-coordinate: 350
              y-coordinate: -20
          15:
            Mark Class: 1
            Mark Anchor:
              x-coordinate: 255
              y-coordinate: 5
        Base Array:
          40:
            Class 0:
              x-coordinate: 300
              y-coordinate: 1700
            Class 1:
              x-coordinate: 290
              y-coordinate: -75
          45:
            Class 0:
              x-coordinate: 450
              y-coordinate: 1600
            Class 1:
              x-coordinate: 450
              y-coordinate: -30
        
        >>> d = obj.effectExtrema(forHorizontal=True, editor=e)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        12 (1590, 0)
        13 (1600, 0)
        14 (0, -55)
        15 (0, -80)
        
        >>> d = obj.effectExtrema(forHorizontal=False, editor=e)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        12 (200, 0)
        13 (100, -50)
        14 (100, -60)
        15 (195, 0)
        """
        
        cache = kwArgs.get('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        b = self.base
        m = self.mark
        
        for baseGlyph in b:
            ba = b[baseGlyph]
            
            for markGlyph in m:
                mo = m[markGlyph]
                firstAnchor = ba[mo.markClass]
                secondAnchor = mo.markAnchor
                
                if firstAnchor is None or secondAnchor is None:
                    continue
                
                if forHorizontal:
                    shift = firstAnchor.y - secondAnchor.y
                else:
                    shift = firstAnchor.x - secondAnchor.x
                    
                if not shift:
                    continue
                
                if markGlyph not in r:
                    if shift > 0:
                        r[markGlyph] = (shift, 0)
                    else:
                        r[markGlyph] = (0, shift)
                
                else:
                    old = r[markGlyph]
                    
                    if shift > 0:
                        if (old[0] is not None) and (shift > old[0]):
                            r[markGlyph] = (shift, old[1])
                    
                    elif (old[1] is not None) and (shift < old[1]):
                        r[markGlyph] = (old[0], shift)
        
        cache[id(self)] = r
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new MarkToBase from the specified
        FontWorkerSource.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = MarkToBase.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.marktobase - WARNING - line 3 -- unexpected token: foo
        FW_test.marktobase - WARNING - line 7 -- unexpected token: bar
        FW_test.marktobase - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> obj.pprint()
        Mark Array:
          8:
            Mark Class: 1
            Mark Anchor:
              x-coordinate: 123
              y-coordinate: 234
              Contour point index: 12
              Glyph index: 8
          13:
            Mark Class: 2
            Mark Anchor:
              x-coordinate: 345
              y-coordinate: 456
              Contour point index: 23
              Glyph index: 13
          21:
            Mark Class: 2
            Mark Anchor:
              x-coordinate: 567
              y-coordinate: 678
              Contour point index: 34
              Glyph index: 21
        Base Array:
          1:
            Class 0:
              x-coordinate: 789
              y-coordinate: 987
              Contour point index: 56
              Glyph index: 1
            Class 1:
              (no data)
            Class 2:
              (no data)
          3:
            Class 0:
              (no data)
            Class 1:
              x-coordinate: 876
              y-coordinate: 765
              Contour point index: 67
              Glyph index: 3
            Class 2:
              (no data)
          5:
            Class 0:
              (no data)
            Class 1:
              (no data)
            Class 2:
              x-coordinate: 654
              y-coordinate: 543
              Contour point index: 78
              Glyph index: 5
        """
        
        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber = fws.lineNumber
        r = cls()
        logger = kwArgs['logger']
        logger = logger.getChild("marktobase")

        # first pass
        fws.push()
        classSet = set()
        
        for line in fws:
            if line.lower() in terminalStrings:
                break
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() in ('mark', 'base'):
                    classNum = fwsint(tokens[2])
                    classSet.add(classNum)
                else:
                    # ignore any unexpected tokens as they will be caught in
                    # second pass
                    continue

        # map the original classes to 0, 1, 2, 3...
        numClasses = len(classSet)
        classDict = {}
        # temporary base anchor dict to gather multiple base anchor defs
        baseAnchorDict = defaultdict(lambda: [None for _ in range(numClasses)])

        for i, classNum in enumerate(sorted(list(classSet))):
            classDict[classNum] = i

        # go back and do a second pass
        fws.pop()
        
        for line in fws:
            if line in terminalStrings:
                # build baseRecords from baseAnchorDict contents
                for gidx, ganchors in baseAnchorDict.items():
                    r.base[gidx] = baserecord.BaseRecord(ganchors)
                return r

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() in ('mark', 'base'):
                    glyphName = tokens[1]
                    glyphIndex = namer.glyphIndexFromString(glyphName)
                    classNum = classDict[fwsint(tokens[2])]
                    
                    [xCoordinate, yCoordinate] = [
                        int(x) for x in tokens[3].split(',')]

                    if glyphIndex is None:
                        logger.warning((
                          'V0956',
                          (fws.lineNumber, glyphName),
                          "line %d -- glyph '%s' not found"))
                        
                        continue

                    if tokens[0].lower() == 'mark':
                        if len(tokens) == 4:
                            markAnchor = anchor_coord.Anchor_Coord(
                              xCoordinate,
                              yCoordinate)
                        
                        else:
                            contourPointIndex = int(tokens[4])
                            
                            markAnchor = anchor_point.Anchor_Point(
                              xCoordinate,
                              yCoordinate,
                              glyphIndex = glyphIndex,
                              pointIndex = contourPointIndex)
                        
                        if glyphIndex in r.mark:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, glyphName),
                              "line %d -- ignoring duplicated mark definition "
                              "of '%s'"))
                        
                        else:
                            r.mark[glyphIndex] = markrecord.MarkRecord(
                              markClass = classNum,
                              markAnchor = markAnchor)

                    else: # tokens[0] == 'base':
                        anchorList = baseAnchorDict[glyphIndex]
                        if anchorList[classNum] is not None:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, glyphName),
                              "line %d -- ignoring duplicated base definition "
                              "of '%s'"))
                        
                        else:
                            if len(tokens) == 4:
                                anchordef = anchor_coord.Anchor_Coord(
                                    xCoordinate, yCoordinate)
                            else:
                                contourPointIndex = int(tokens[4])
                                anchordef = anchor_point.Anchor_Point(
                                    xCoordinate, yCoordinate,
                                    glyphIndex=glyphIndex,
                                    pointIndex=contourPointIndex)

                            baseAnchorDict[glyphIndex][classNum] = anchordef

                elif tokens[0].lower() == 'marktobase anchorpoints begin':
                    continue # Note: FontWorker apparently ignores this

                else:
                    logger.warning((
                      'V0960',
                      (fws.lineNumber, tokens[0]),
                      'line %d -- unexpected token: %s'))

        logger.warning((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))
        for gidx, ganchors in baseAnchorDict.items():
            r.base[gidx] = baserecord.BaseRecord(ganchors)
        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkToBase object from the specified walker,
        doing source validation.
        
        >>> obj, ed = _makeTest()
        >>> s = obj.binaryString()
        >>> logger = utilities.makeDoctestLogger("marktobase_test")
        >>> fvb = MarkToBase.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        marktobase_test.marktobase - DEBUG - Walker has 106 remaining bytes.
        marktobase_test.marktobase.mark.coverage - DEBUG - Walker has 94 remaining bytes.
        marktobase_test.marktobase.mark.coverage - DEBUG - Format is 2, count is 1
        marktobase_test.marktobase.mark.coverage - DEBUG - Raw data are [(12, 15, 0)]
        marktobase_test.marktobase.base.coverage - DEBUG - Walker has 84 remaining bytes.
        marktobase_test.marktobase.base.coverage - DEBUG - Format is 1, count is 2
        marktobase_test.marktobase.base.coverage - DEBUG - Raw data are [40, 45]
        marktobase_test.marktobase.markarray - DEBUG - Walker has 76 remaining bytes.
        marktobase_test.marktobase.markarray.glyph 12.markrecord - DEBUG - Walker has 74 bytes remaining.
        marktobase_test.marktobase.markarray.glyph 12.markrecord.anchor_coord - DEBUG - Walker has 48 remaining bytes.
        marktobase_test.marktobase.markarray.glyph 13.markrecord - DEBUG - Walker has 70 bytes remaining.
        marktobase_test.marktobase.markarray.glyph 13.markrecord.anchor_coord - DEBUG - Walker has 42 remaining bytes.
        marktobase_test.marktobase.markarray.glyph 14.markrecord - DEBUG - Walker has 66 bytes remaining.
        marktobase_test.marktobase.markarray.glyph 14.markrecord.anchor_coord - DEBUG - Walker has 36 remaining bytes.
        marktobase_test.marktobase.markarray.glyph 15.markrecord - DEBUG - Walker has 62 bytes remaining.
        marktobase_test.marktobase.markarray.glyph 15.markrecord.anchor_coord - DEBUG - Walker has 30 remaining bytes.
        marktobase_test.marktobase.basearray - DEBUG - Walker has 58 remaining bytes.
        marktobase_test.marktobase.basearray.glyph 40.baserecord - DEBUG - Walker has 56 bytes remaining.
        marktobase_test.marktobase.basearray.glyph 40.baserecord.[0].anchor_coord - DEBUG - Walker has 24 remaining bytes.
        marktobase_test.marktobase.basearray.glyph 40.baserecord.[1].anchor_coord - DEBUG - Walker has 18 remaining bytes.
        marktobase_test.marktobase.basearray.glyph 45.baserecord - DEBUG - Walker has 52 bytes remaining.
        marktobase_test.marktobase.basearray.glyph 45.baserecord.[0].anchor_coord - DEBUG - Walker has 12 remaining bytes.
        marktobase_test.marktobase.basearray.glyph 45.baserecord.[1].anchor_coord - DEBUG - Walker has 6 remaining bytes.
        
        >>> fvb(s[:5], logger=logger)
        marktobase_test.marktobase - DEBUG - Walker has 5 remaining bytes.
        marktobase_test.marktobase - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("marktobase")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Was expecting format 1, but got format %d instead."))
            
            return None
        
        markCovTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger.getChild("mark"),
          **kwArgs)
        
        if markCovTable is None:
            return None
        
        baseCovTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger.getChild("base"),
          **kwArgs)
        
        if baseCovTable is None:
            return None
        
        classCount, mOffset, bOffset = w.unpack("3H")
        kwArgs.pop('classCount', None)
        kwArgs.pop('coverage', None)
        
        m = markarray.MarkArray.fromvalidatedwalker(
          w.subWalker(mOffset),
          coverage = markCovTable,
          logger = logger,
          **kwArgs)
        
        if m is None:
            return None
        
        actualCount = 1 + utilities.safeMax(x.markClass for x in m.values())
        
        if classCount != actualCount:
            logger.error((
              'V0343',
              (actualCount, classCount),
              "The number of classes should be %d (based on the actual values "
              "in the MarkRecords), but is actually %d."))
            
            return None
        
        b = basearray.BaseArray.fromvalidatedwalker(
          w.subWalker(bOffset),
          coverage = baseCovTable,
          classCount = classCount,
          logger = logger,
          **kwArgs)
        
        if b is None:
            return None
        
        return cls(mark=m, base=b)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkToBase from the specified walker.
        
        >>> obj, ed = _makeTest()
        >>> obj == MarkToBase.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        
        if format != 1:
            raise ValueError("Unknown MarkToBase format: %d" % (format,))
        
        markCovTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        baseCovTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        classCount, mOffset, bOffset = w.unpack("3H")
        kwArgs.pop('classCount', None)
        kwArgs.pop('coverage', None)
        
        mWalker = w.subWalker(mOffset)
        fw = markarray.MarkArray.fromwalker
        m = fw(mWalker, coverage=markCovTable, **kwArgs)
        
        bWalker = w.subWalker(bOffset)
        fw = basearray.BaseArray.fromwalker
        b = fw(bWalker, coverage=baseCovTable, classCount=classCount, **kwArgs)
        
        return cls(mark=m, base=b)
    
    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        """
        
        if kwArgs.get('isRLCase', False):
            return self._runOne_RL(glyphArray, startIndex, **kwArgs)
        else:
            return self._runOne_LR(glyphArray, startIndex, **kwArgs)

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write Mark To Base lookup as Font Worker-style source.
        """
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex
        getmap = kwArgs.get('datatable').getXYtoPointMap
            
        for k,v in sorted(self.mark.items()):
            if v.markAnchor.anchorKind == 'point':
                map = getmap(k, **kwArgs)
                pt = map.get((v.markAnchor.x, v.markAnchor.y), None)
                pts = "\t%d" % (pt,) if pt else ""
            else:
                pts = ""

            s.write("mark\t%s\t%d\t%d,%d%s\n" % (
              bnfgi(k),
              v.markClass,
              v.markAnchor.x,
              v.markAnchor.y,
              pts))
              
        for k,v in sorted(self.base.items()):
            for vi,vv in enumerate(v):
                if vv is not None:
                    if vv.anchorKind == 'point':
                        map = getmap(k, **kwArgs)
                        pt = map.get((vv.x, vv.y), None)
                        pts = "\t%d" % (pt,) if pt else ""
                    else:
                        pts = ""

                    s.write("base\t%s\t%d\t%d,%d%s\n" % (
                      bnfgi(k),
                      vi,
                      vv.x,
                      vv.y,
                      pts))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from fontio3.utilities import namer
    from io import StringIO

    def _makeTest():
        """
        The test case being made has two base glyphs, glyphs 40 and 45. There
        are 4 marks: glyphs 12 (above), 13 (above), 14 (below), and 15 (below).
        """
        
        from fontio3 import hmtx
        from fontio3.GDEF import GDEF_v1
        
        glyph1_above = anchor_coord.Anchor_Coord(300, 1700)
        glyph1_below = anchor_coord.Anchor_Coord(290, -75)
        glyph2_above = anchor_coord.Anchor_Coord(450, 1600)
        glyph2_below = anchor_coord.Anchor_Coord(450, -30)
        mark1_anchor = anchor_coord.Anchor_Coord(250, 110)
        mark2_anchor = anchor_coord.Anchor_Coord(350, 100)
        mark3_anchor = anchor_coord.Anchor_Coord(350, -20)
        mark4_anchor = anchor_coord.Anchor_Coord(255, 5)
        
        glyph1 = baserecord.BaseRecord([
          glyph1_above,    # class 0
          glyph1_below])   # class 1
        
        glyph2 = baserecord.BaseRecord([
          glyph2_above,    # class 0
          glyph2_below])   # class 1
        
        base = basearray.BaseArray({40: glyph1, 45: glyph2})
        mark1 = markrecord.MarkRecord(0, mark1_anchor)
        mark2 = markrecord.MarkRecord(0, mark2_anchor)
        mark3 = markrecord.MarkRecord(1, mark3_anchor)
        mark4 = markrecord.MarkRecord(1, mark4_anchor)
        
        mark = markarray.MarkArray({
          12: mark1,
          13: mark2,
          14: mark3,
          15: mark4})
        
        r = MarkToBase(mark, base)
        e = utilities.fakeEditor(0x10000)
        e.hmtx = hmtx.Hmtx()
        e.hmtx[12] = hmtx.MtxEntry(0, 50)
        e.hmtx[13] = hmtx.MtxEntry(0, 30)
        e.hmtx[14] = hmtx.MtxEntry(0, 45)
        e.hmtx[15] = hmtx.MtxEntry(0, 55)
        e.hmtx[40] = hmtx.MtxEntry(900, 50)
        e.hmtx[45] = hmtx.MtxEntry(970, 50)
        e.GDEF = GDEF_v1.GDEF()
        e.GDEF.glyphClasses[12] = 3
        e.GDEF.glyphClasses[13] = 3
        e.GDEF.glyphClasses[14] = 3
        e.GDEF.glyphClasses[15] = 3
        
        return r, e

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'B': 3,
        'C': 5,
        'X': 8,
        'Y': 13,
        'Z': 21
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        mark	X	 1	 123, 234	 12
        mark	Y	 2	 345, 456	 23
        mark	Z	 2	 567, 678	 34
        base	A	 0	 789, 987	 56
        base	B	 1	 876, 765	 67
        base	C	 2	 654, 543	 78
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        mark	X	 1	 123, 234	 12
        foo
        mark	Y	 2	 345, 456	 23
        mark	Z	 2	 567, 678	 34
        base	A	 0	 789, 987	 56
        bar
        base	B	 1	 876, 765	 67
        base	C	 2	 654, 543	 78
        """))
    

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
