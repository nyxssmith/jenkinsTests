#
# marktomark.py
#
# Copyright © 2007-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 6 (Mark-to-Mark) subtables for a GPOS table.
"""

# System imports
from collections import defaultdict
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
      for rec in obj.attachingMark.values())
    
    # all BaseRecords must be at least markClassCount long
    if any(len(rec) != markClassCount for rec in obj.baseMark.values()):
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

class MarkToMark(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing OpenType mark-to-mark positioning data. These are
    simple objects with two attributes: attachingMark (a MarkArray), and
    baseMark (a BaseArray).
    
    >>> obj, ed = _makeTest()
    >>> obj.pprint()
    Attaching mark Array:
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
    Base mark Array:
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
        attachingMark = dict(
            attr_followsprotocol = True,
            attr_initfunc = markarray.MarkArray,
            attr_label = "Attaching mark Array"),
        
        baseMark = dict(
            attr_followsprotocol = True,
            attr_initfunc = basearray.BaseArray,
            attr_label = "Base mark Array"))
    
    objSpec = dict(
        obj_boolfalseiffalseset = set(['attachingMark', 'baseMark']),
        obj_validatefunc_partial = _validate)
    
    kind = ('GPOS', 6)
    kindString = "Mark-to-mark positioning table"
    
    #
    # Methods
    #
    
    def _runOne_LR(self, glyphArray, startIndex, **kwArgs):
        """
        
        >>> anchor1 = anchor_coord.Anchor_Coord(400, 500)
        >>> markRec1 = markrecord.MarkRecord(markAnchor=anchor1)  # class 0
        >>> markArray1 = markarray.MarkArray({15: markRec1})
        >>> anchor2 = anchor_coord.Anchor_Coord(950, 1300)
        >>> baseRec1 = baserecord.BaseRecord([anchor2])
        >>> baseArray1 = basearray.BaseArray({12: baseRec1})
        >>> obj = MarkToMark(attachingMark=markArray1, baseMark=baseArray1)
        >>> ed = utilities.fakeEditor(80, hmtx={35: 1900, 12: 0, 15: 0, 77: 0})
        >>> ga = runningglyphs.GlyphList.fromiterable([35, 12, 77, 15])
        >>> def funcIgs(*a, **k):
        ...   k['wantMarks'][:] = [False, True, False, True]
        ...   return [False, False, True, False]
        >>> ce = [effect.Effect() for g in ga]
        >>> ce[1].xPlacementDelta = -1650
        >>> ce[1].yPlacementDelta = 700
        >>> ce[1].backIndex = -1
        >>> r, count = obj._runOne_LR(ga, 3, igsFunc=funcIgs, editor=ed, cumulEffects=ce)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 35, originalOffset = 0 
        glyph 12, originalOffset = 1 xPlacementDelta = -1650, yPlacementDelta = 700, backIndex = -1
        glyph 77, originalOffset = 2 
        glyph 15, originalOffset = 3 xPlacementDelta = -1100, yPlacementDelta = 1500, backIndex = -2
        """
        
        igsFunc = kwArgs['igsFunc']
        isMark = []
        igs = igsFunc(glyphArray, wantMarks=isMark, **kwArgs)
        igOrMark = list(map(operator.or_, igs, isMark))
        gMark = glyphArray[startIndex]
        mark = self.attachingMark
        
        if (not isMark[startIndex]) or (gMark not in mark):
            return (None, 0)
        
        walk = startIndex - 1
        
        while (walk >= 0) and igs[walk]:  # look for previous mark
            walk -= 1
        
        if walk == -1:
            return (None, 0)
        
        base = self.baseMark
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
            if not igs[cwIndex]:
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
          effLeft.yPlacementDelta,
          (baseDelta.y - varBDelY)))
        
        r[startIndex].xPlacementDelta = deltaX
        r[startIndex].yPlacementDelta = deltaY
        r[startIndex].backIndex = walk - startIndex
        return (r, 1)
    
    def _runOne_RL(self, glyphArray, startIndex, **kwArgs):
        """
        
        >>> anchor1 = anchor_coord.Anchor_Coord(400, 500)
        >>> markRec1 = markrecord.MarkRecord(markAnchor=anchor1)  # class 0
        >>> markArray1 = markarray.MarkArray({15: markRec1})
        >>> anchor2 = anchor_coord.Anchor_Coord(950, 1300)
        >>> baseRec1 = baserecord.BaseRecord([anchor2])
        >>> baseArray1 = basearray.BaseArray({12: baseRec1})
        >>> obj = MarkToMark(attachingMark=markArray1, baseMark=baseArray1)
        >>> ed = utilities.fakeEditor(80)
        >>> ga = runningglyphs.GlyphList.fromiterable([35, 12, 77, 15])
        >>> def funcIgs(*a, **k):
        ...   k['wantMarks'][:] = [False, True, False, True]
        ...   return [False, False, True, False]
        >>> ce = [effect.Effect() for g in ga]
        >>> ce[1].xPlacementDelta = -1650
        >>> ce[1].yPlacementDelta = 700
        >>> ce[1].backIndex = -1
        >>> r, count = obj._runOne_RL(ga, 3, igsFunc=funcIgs, editor=ed, cumulEffects=ce)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 35, originalOffset = 0 
        glyph 12, originalOffset = 1 xPlacementDelta = -1650, yPlacementDelta = 700, backIndex = -1
        glyph 77, originalOffset = 2 
        glyph 15, originalOffset = 3 xPlacementDelta = -1100, yPlacementDelta = 1500, backIndex = -2
        """
        
        igsFunc = kwArgs['igsFunc']
        isMark = []
        igs = igsFunc(glyphArray, wantMarks=isMark, **kwArgs)
        igOrMark = list(map(operator.or_, igs, isMark))
        gMark = glyphArray[startIndex]
        mark = self.attachingMark
        
        if (not isMark[startIndex]) or (gMark not in mark):
            return (None, 0)
        
        # Note that we're still pre-bidi, so the logically previous mark is
        # still the previous glyph index (i.e. move by -1, not +1).
        
        walk = startIndex - 1
        
        while (walk >= 0) and igs[walk]:  # look for previous mark
            walk -= 1
        
        if walk == -1:
            return (None, 0)
        
        base = self.baseMark
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
          effLeft.xPlacementDelta,
          (baseDelta.x - varBDelX)))
    
        deltaY = sum((
          -(markDelta.y + varMDelY),
          effLeft.yPlacementDelta,
          (baseDelta.y - varBDelY)))
        
        r[startIndex].xPlacementDelta = deltaX
        r[startIndex].yPlacementDelta = deltaY
        r[startIndex].backIndex = walk - startIndex
        return (r, 1)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. No keyword
        arguments are used; however, at some point we may change this to allow
        shared device and anchor pools across multiple lookups.
        
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
        
        aMarkBackMap, bMarkBackMap = {}, {}
        
        aMarkCovTable = coverage.Coverage.fromglyphset(
          self.attachingMark,
          backMap = aMarkBackMap)
        
        aMarkCovStake = w.getNewStake()
        
        bMarkCovTable = coverage.Coverage.fromglyphset(
          self.baseMark,
          backMap = bMarkBackMap)
        
        bMarkCovStake = w.getNewStake()
        
        markClassCount = 1 + utilities.safeMax(
          obj.markClass
          for obj in self.attachingMark.values())
        
        w.add("H", 1)  # format 1
        w.addUnresolvedOffset("H", stakeValue, aMarkCovStake)
        w.addUnresolvedOffset("H", stakeValue, bMarkCovStake)
        w.add("H", markClassCount)
        aMarkStake = w.getNewStake()
        bMarkStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, aMarkStake)
        w.addUnresolvedOffset("H", stakeValue, bMarkStake)
        
        # Resolve the references
        aMarkCovTable.buildBinary(w, stakeValue=aMarkCovStake, **kwArgs)
        bMarkCovTable.buildBinary(w, stakeValue=bMarkCovStake, **kwArgs)
        orderedKeys = []
        anchorPool = {}
        devicePool = {}
        
        d = {
          'anchorPool': anchorPool,
          'devicePool': devicePool,
          'orderedKeys': orderedKeys}
        
        self.attachingMark.buildBinary(w, stakeValue=aMarkStake, **d)
        self.baseMark.buildBinary(w, stakeValue=bMarkStake, **d)
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
        Attaching mark Array:
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
        Base mark Array:
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
        
        We now create slightly different test data, involving glyph 40 being
        allowed to stack; note the difference here from the first call to
        effectExtrema above:
        
        >>> obj, e = _makeTest(True)
        >>> d = obj.effectExtrema(forHorizontal=True, editor=e)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        12 (1590, 0)
        13 (1600, 0)
        14 (0, -55)
        15 (0, -80)
        40 (None, 0)
        """
        
        cache = kwArgs.get('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        b = self.baseMark
        m = self.attachingMark
        
        # The mark-to-mark subtable introduces the possibility of stacking
        # marks indefinitely -- a case signalled by the presence of the same
        # glyph in both the baseMark and the attachingMark tables. For any
        # glyph that behaves this way we make sure the appropriate entry in
        # the returns dict is None; clients should look for this as a clue that
        # potentially infinite stacking is permitted.
        
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
                        if markGlyph in b:
                            r[markGlyph] = (None, 0)
                        else:
                            r[markGlyph] = (shift, 0)
                    
                    elif markGlyph in b:
                        r[markGlyph] = (0, None)
                    
                    else:
                        r[markGlyph] = (0, shift)
                
                else:
                    old = r[markGlyph]
                    
                    if shift > 0:
                        if markGlyph in b:
                            r[markGlyph] = (None, old[1])
                        elif (old[0] is not None) and (shift > old[0]):
                            r[markGlyph] = (shift, old[1])
                    
                    elif markGlyph in b:
                        r[markGlyph] = (old[0], None)
                    
                    elif (old[1] is not None) and (shift < old[1]):
                        r[markGlyph] = (old[0], shift)
        
        cache[id(self)] = r
        return r

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new MarkToMark from the specified
        FontWorkerSource, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> mtm = MarkToMark.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.marktobase - WARNING - line 3 -- unexpected token: foo
        FW_test.marktobase - WARNING - line 7 -- unexpected token: bar
        FW_test.marktobase - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> mtm.pprint()
        Attaching mark Array:
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
        Base mark Array:
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
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("marktobase")
        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber = fws.lineNumber
        MR = markrecord.MarkRecord
        r = cls()

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
        # temporary baseMark anchor dict to gather multiple baseMark anchor defs
        baseMarkAnchorDict = defaultdict(lambda: [None for _ in range(numClasses)])
        
        for i, classNum in enumerate(sorted(list(classSet))):
            classDict[classNum] = i

        # go back and do a second pass
        fws.pop()
        for line in fws:
            if line in terminalStrings:
                # build BaseRecords from baseMarkAnchorDict contents
                for gidx, ganchors in baseMarkAnchorDict.items():
                    r.baseMark[gidx] = baserecord.BaseRecord(ganchors)
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
                        if glyphIndex in r.attachingMark:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, glyphName),
                              "line %d -- ignoring duplicated attaching "
                              "mark definition of '%s'"))
                        
                        else:
                            if len(tokens) == 4:
                                r.attachingMark[glyphIndex] = MR(
                                    markClass = classNum,
                                    markAnchor = anchor_coord.Anchor_Coord(
                                      xCoordinate,
                                      yCoordinate))
                            
                            else:
                                contourPointIndex = int(tokens[4])
                                
                                r.attachingMark[glyphIndex] = MR(
                                    markClass=classNum,
                                    markAnchor=anchor_point.Anchor_Point(
                                        xCoordinate,
                                        yCoordinate,
                                        glyphIndex = glyphIndex,
                                        pointIndex = contourPointIndex))

                    else: # tokens[0] == 'base':
                        anchorList = baseMarkAnchorDict[glyphIndex]
                        if anchorList[classNum] is not None:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, glyphName),
                              "line %d -- ignoring duplicated base "
                              "mark definition of '%s'"))
                        
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
                                    
                            baseMarkAnchorDict[glyphIndex][classNum] = anchordef

                else:
                    logger.warning((
                        'V0960',
                        (fws.lineNumber, tokens[0]),
                        'line %d -- unexpected token: %s'))

        logger.warning((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))
        for gidx, ganchors in baseMarkAnchorDict.items():
            r.baseMark[gidx] = baserecord.BaseRecord(ganchors)

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkToMark object from the specified walker,
        doing source validation.
        
        >>> obj, ed = _makeTest()
        >>> logger = utilities.makeDoctestLogger("marktomark_test")
        >>> s = obj.binaryString()
        >>> fvb = MarkToMark.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        marktomark_test.marktobase - DEBUG - Walker has 106 remaining bytes.
        marktomark_test.marktobase.attachingmark.coverage - DEBUG - Walker has 94 remaining bytes.
        marktomark_test.marktobase.attachingmark.coverage - DEBUG - Format is 2, count is 1
        marktomark_test.marktobase.attachingmark.coverage - DEBUG - Raw data are [(12, 15, 0)]
        marktomark_test.marktobase.basemark.coverage - DEBUG - Walker has 84 remaining bytes.
        marktomark_test.marktobase.basemark.coverage - DEBUG - Format is 1, count is 2
        marktomark_test.marktobase.basemark.coverage - DEBUG - Raw data are [40, 45]
        marktomark_test.marktobase.markarray - DEBUG - Walker has 76 remaining bytes.
        marktomark_test.marktobase.markarray.glyph 12.markrecord - DEBUG - Walker has 74 bytes remaining.
        marktomark_test.marktobase.markarray.glyph 12.markrecord.anchor_coord - DEBUG - Walker has 48 remaining bytes.
        marktomark_test.marktobase.markarray.glyph 13.markrecord - DEBUG - Walker has 70 bytes remaining.
        marktomark_test.marktobase.markarray.glyph 13.markrecord.anchor_coord - DEBUG - Walker has 42 remaining bytes.
        marktomark_test.marktobase.markarray.glyph 14.markrecord - DEBUG - Walker has 66 bytes remaining.
        marktomark_test.marktobase.markarray.glyph 14.markrecord.anchor_coord - DEBUG - Walker has 36 remaining bytes.
        marktomark_test.marktobase.markarray.glyph 15.markrecord - DEBUG - Walker has 62 bytes remaining.
        marktomark_test.marktobase.markarray.glyph 15.markrecord.anchor_coord - DEBUG - Walker has 30 remaining bytes.
        marktomark_test.marktobase.basearray - DEBUG - Walker has 58 remaining bytes.
        marktomark_test.marktobase.basearray.glyph 40.baserecord - DEBUG - Walker has 56 bytes remaining.
        marktomark_test.marktobase.basearray.glyph 40.baserecord.[0].anchor_coord - DEBUG - Walker has 24 remaining bytes.
        marktomark_test.marktobase.basearray.glyph 40.baserecord.[1].anchor_coord - DEBUG - Walker has 18 remaining bytes.
        marktomark_test.marktobase.basearray.glyph 45.baserecord - DEBUG - Walker has 52 bytes remaining.
        marktomark_test.marktobase.basearray.glyph 45.baserecord.[0].anchor_coord - DEBUG - Walker has 12 remaining bytes.
        marktomark_test.marktobase.basearray.glyph 45.baserecord.[1].anchor_coord - DEBUG - Walker has 6 remaining bytes.
        
        >>> fvb(s[:5], logger=logger)
        marktomark_test.marktobase - DEBUG - Walker has 5 remaining bytes.
        marktomark_test.marktobase - ERROR - Insufficient bytes.
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
        
        aMarkCovTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger.getChild("attachingmark"),
          **kwArgs)
        
        if aMarkCovTable is None:
            return None
        
        bMarkCovTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger.getChild("basemark"),
          **kwArgs)
        
        if bMarkCovTable is None:
            return None
        
        classCount, aOffset, bOffset = w.unpack("3H")
        kwArgs.pop('coverage', None)
        kwArgs.pop('classCount', None)
        
        m = markarray.MarkArray.fromvalidatedwalker(
          w.subWalker(aOffset),
          coverage = aMarkCovTable,
          logger = logger,
          **kwArgs)
        
        if m is None:
            return None
        
        actualCount = 1 + utilities.safeMax(
          obj.markClass
          for obj in m.values())
        
        if classCount != actualCount:
            logger.error((
              'V0343',
              (actualCount, classCount),
              "The number of classes should be %d (based on the actual values "
              "in the MarkRecords), but is actually %d."))
            
            return None
        
        b = basearray.BaseArray.fromvalidatedwalker(
          w.subWalker(bOffset),
          coverage = bMarkCovTable,
          classCount = classCount,
          logger = logger,
          **kwArgs)
        
        if b is None:
            return None
        
        return cls(attachingMark=m, baseMark=b)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkToMark from the specified walker.
        
        >>> mmt, ed = _makeTest()
        >>> mmt == MarkToMark.frombytes(mmt.binaryString())
        True
        """
        
        format = w.unpack("H")
        
        if format != 1:
            raise ValueError("Unknown MarkToMark format: %d" % (format,))
        
        aMarkCovTable = coverage.Coverage.fromwalker(
          w.subWalker(w.unpack("H")))
        
        bMarkCovTable = coverage.Coverage.fromwalker(
          w.subWalker(w.unpack("H")))
        
        classCount, aOffset, bOffset = w.unpack("3H")
        
        aWalker = w.subWalker(aOffset)
        aFunc = markarray.MarkArray.fromwalker
        kwArgs.pop('classCount', None)
        kwArgs.pop('coverage', None)
        a = aFunc(aWalker, coverage=aMarkCovTable, **kwArgs)
        
        bWalker = w.subWalker(bOffset)
        bFunc = basearray.BaseArray.fromwalker
        
        b = bFunc(
          bWalker,
          coverage=bMarkCovTable,
          classCount=classCount,
          **kwArgs)
        
        return cls(attachingMark=a, baseMark=b)
    
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
        Write Mark To Mark lookup as Font Worker-style source.
        """
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex
        getmap = kwArgs.get('datatable').getXYtoPointMap
            
        for k,v in sorted(self.attachingMark.items()):
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
              
        for k,v in sorted(self.baseMark.items()):
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
    
    def _fakeEditor():
        from fontio3 import hmtx
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(0x10000)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        e.hmtx = hmtx.Hmtx()
        e.hmtx[5] = hmtx.MtxEntry(2000, 50)
        e.hmtx[12] = hmtx.MtxEntry(2100, 40)
        e.hmtx[40] = hmtx.MtxEntry(0, 30)
        return e

    def _makeTest(addStacker=False):
        """
        The test case being made has two base marks, glyphs 40 and 45. There
        are 4 attaching marks: glyphs 12 (above), 13 (above), 14 (below), and
        15 (below). If addStacker is True, glyph 40 will also be added as an
        attaching mark, as well as remaining a base mark.
        """
        
        from fontio3 import hmtx
        from fontio3.GDEF import GDEF_v1
        
        base1_above = anchor_coord.Anchor_Coord(300, 1700)
        base1_below = anchor_coord.Anchor_Coord(290, -75)
        base2_above = anchor_coord.Anchor_Coord(450, 1600)
        base2_below = anchor_coord.Anchor_Coord(450, -30)
        mark1_anchor = anchor_coord.Anchor_Coord(250, 110)
        mark2_anchor = anchor_coord.Anchor_Coord(350, 100)
        mark3_anchor = anchor_coord.Anchor_Coord(350, -20)
        mark4_anchor = anchor_coord.Anchor_Coord(255, 5)
        
        base1 = baserecord.BaseRecord([
          base1_above,    # class 0
          base1_below])   # class 1
        
        base2 = baserecord.BaseRecord([
          base2_above,    # class 0
          base2_below])   # class 1
        
        base = basearray.BaseArray({40: base1, 45: base2})
        mark1 = markrecord.MarkRecord(0, mark1_anchor)
        mark2 = markrecord.MarkRecord(0, mark2_anchor)
        mark3 = markrecord.MarkRecord(1, mark3_anchor)
        mark4 = markrecord.MarkRecord(1, mark4_anchor)
        
        mark = markarray.MarkArray({
          12: mark1,
          13: mark2,
          14: mark3,
          15: mark4})
        
        if addStacker:
            mark5_anchor = anchor_coord.Anchor_Coord(102, 104)
            mark5 = markrecord.MarkRecord(0, mark5_anchor)
            mark[40] = mark5
        
        r = MarkToMark(mark, base)
        e = utilities.fakeEditor(0x10000)
        e.hmtx = hmtx.Hmtx()
        e.hmtx[12] = hmtx.MtxEntry(0, 50)
        e.hmtx[30] = hmtx.MtxEntry(900, 50)
        e.hmtx[40] = hmtx.MtxEntry(0, 50)
        e.GDEF = GDEF_v1.GDEF()
        e.GDEF.glyphClasses[12] = 3
        e.GDEF.glyphClasses[30] = 1
        e.GDEF.glyphClasses[40] = 3
        
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
