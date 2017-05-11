#
# marktoligature.py
#
# Copyright © 2007-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 5 (Mark-to-Ligature) subtables for a GPOS table.
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
  componentrecord,
  effect,
  ligaturearray,
  ligatureattach,
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
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'hmtx')):
        logger.error((
          'V0553',
          (),
          "Unable to validate marks, because no 'hmtx' table is present."))
    
    mtxTable = editor.hmtx  # what about vertical at some point?
    badMarks = {g for g in obj.mark if g not in mtxTable}
    
    if badMarks:
        logger.error((
          'V1058',
          (sorted(badMarks),),
          "Mark glyphs not found in 'hmtx' or 'vmtx': %s"))
        
        return False
    
    nz = set(g for g in obj.mark if mtxTable[g].advance)
    
    if nz:
        logger.warning((
          'V1059',
          (sorted(nz),),
          "The following mark glyphs have nonzero advances: %s"))

    markClassCount = 1 + utilities.safeMax(
      rec.markClass
      for rec in obj.mark.values())
    
    for rec in obj.ligature.values():
        for subObj in rec:
            if len(subObj) != markClassCount:
                logger.error((
                  'V0348',
                  (),
                  "The ComponentRecords' lengths do not match "
                  "the mark class count."))
                
                return False
    
    if (editor is None) or (not editor.reallyHas(b'GSUB')):
        logger.warning((
          'V1060',
          (),
          "Unable to validate ligatures in mark-to-ligature table, "
          "because no Editor was supplied or the supplied Editor "
          "does not have a GSUB table."))
        
        return True
    
    dCounts = {}
    sI = editor.GSUB.features.subtableIterator
    
    for ligSubtable in sI(kindStringSet={"Ligature substitution table"}):
        d = ligSubtable.componentCounts()
        
        for lig, count in d.items():
            if lig not in dCounts:
                dCounts[lig] = d[lig]
                continue
            
            if dCounts[lig] != d[lig]:
                logger.error((
                  'Vxxxx',
                  (lig,),
                  "The ligature glyph %d has an inconsistent number "
                  "of input components."))
                
                return False
    
    absentLigs = set()
    conflictLigs = set()
    
    for lig, ligAttach in obj.ligature.items():
        if lig not in dCounts:
            absentLigs.add(lig)
            continue
        
        if len(ligAttach) != dCounts[lig]:
            conflictLigs.add(lig)
    
    if absentLigs:
        logger.warning((
          'V1061',
          (sorted(absentLigs),),
          "The following ligatures are present in this mark-to-ligature "
          "table, but no rule to make them appears in the GSUB table: %s"))
    
    if conflictLigs:
        logger.error((
          'V1062',
          (sorted(conflictLigs),),
          "The following ligatures have inconsistent counts between "
          "the GSUB Ligature Lookup that created them and the length "
          "of the mark-to-ligature data in this table: %s"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class MarkToLigature(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing OpenType mark-to-ligature positioning data. These are
    simple objects with two attributes: mark (a MarkArray), and ligature
    (a LigatureArray).
    
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
          y-coordinate: 115
    Ligature Array:
      40:
        Ligature Component #1:
          Class 0:
            x-coordinate: 300
            y-coordinate: 1700
          Class 1:
            x-coordinate: 290
            y-coordinate: -75
        Ligature Component #2:
          Class 0:
            x-coordinate: 900
            y-coordinate: 1740
          Class 1:
            x-coordinate: 890
            y-coordinate: -75
        Ligature Component #3:
          Class 0:
            x-coordinate: 1500
            y-coordinate: 1690
          Class 1:
            x-coordinate: 1495
            y-coordinate: -75
      45:
        Ligature Component #1:
          Class 0:
            x-coordinate: 450
            y-coordinate: 1600
          Class 1:
            x-coordinate: 450
            y-coordinate: -30
        Ligature Component #2:
          Class 0:
            x-coordinate: 1350
            y-coordinate: 1600
          Class 1:
            x-coordinate: 1350
            y-coordinate: -45
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        mark = dict(
            attr_followsprotocol = True,
            attr_initfunc = markarray.MarkArray,
            attr_label = "Mark Array"),
        
        ligature = dict(
            attr_followsprotocol = True,
            attr_initfunc = ligaturearray.LigatureArray,
            attr_label = "Ligature Array"))
    
    attrSorted = ('mark', 'ligature')
    
    objSpec = dict(
        obj_boolfalseiffalseset = set(['mark', 'ligature']),
        obj_validatefunc_partial = _validate)
    
    kind = ('GPOS', 5)
    kindString = "Mark-to-ligature positioning table"
    
    #
    # Methods
    #
    
    def _runOne_LR(self, glyphArray, startIndex, **kwArgs):
        """
        
        >>> anchor1 = anchor_coord.Anchor_Coord(950, 1100)
        >>> markRec1 = markrecord.MarkRecord(markAnchor=anchor1)  # class 0
        >>> markArray1 = markarray.MarkArray({12: markRec1})
        >>> anchor2 = anchor_coord.Anchor_Coord(400, 1800)
        >>> compRec1 = componentrecord.ComponentRecord([anchor2])
        >>> anchor3 = anchor_coord.Anchor_Coord(800, 1800)
        >>> compRec2 = componentrecord.ComponentRecord([anchor3])
        >>> anchor4 = anchor_coord.Anchor_Coord(1200, 1800)
        >>> compRec3 = componentrecord.ComponentRecord([anchor4])
        >>> attRec1 = ligatureattach.LigatureAttach([compRec1, compRec2, compRec3])
        >>> ligArray1 = ligaturearray.LigatureArray({38: attRec1})
        >>> obj = MarkToLigature(mark=markArray1, ligature=ligArray1)
        >>> ed = utilities.fakeEditor(80, hmtx={38: 1900, 12: 0, 77: 0})
        >>> ga = runningglyphs.GlyphList.fromiterable([38, -1, 77, 12, -1])
        >>> ga[0].ligInputOffsets = (0, 1, 4)
        >>> def funcIgs(*a, **k):
        ...   k['wantMarks'][:] = [False, False, False, True, False]
        ...   return [False, True, True, False, True]
        >>> igsFunc = lambda *a, **k: [False, True, False]
        >>> r, count = obj._runOne_LR(ga, 3, igsFunc=funcIgs, editor=ed)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 38, originalOffset = 0 
        glyph -1, originalOffset = 1 
        glyph 77, originalOffset = 2 
        glyph 12, originalOffset = 3 xPlacementDelta = -2050, yPlacementDelta = 700, backIndex = -3
        glyph -1, originalOffset = 4 
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
        
        while (walk >= 0) and igOrMark[walk]:  # look for prior ligature
            walk -= 1
        
        if walk == -1:
            return (None, 0)
        
        lig = self.ligature
        E = effect.Effect
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        gLig = glyphArray[walk]
        
        if gLig not in lig:
            return (None, 0)
        
        # Determine which split index this is
        
        moo = gMark.originalOffset
        
        if getattr(gLig, 'ligInputOffsets', None):
            splitIndex = sum(moo >= n for n in gLig.ligInputOffsets) - 1
        else:
            splitIndex = -1
        
        ba = lig[gLig][splitIndex]
        mo = mark[gMark]
        baseDelta = ba[mo.markClass]
        
        if baseDelta is None:
            return (None, 0)
        
        # Whew. Everything is right, so we actually do the move.
        
        markDelta = mo.markAnchor
        effLeft = r[walk]
        mtxTable = kwArgs['editor'].hmtx  # vertical at some point?
        
        # Because some ignored glyphs might actually have advances, we go thru
        # and accumulate the total advances from the ligature up to, but NOT
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
        >>> anchor2 = anchor_coord.Anchor_Coord(400, 1800)
        >>> compRec1 = componentrecord.ComponentRecord([anchor2])
        >>> anchor3 = anchor_coord.Anchor_Coord(800, 1800)
        >>> compRec2 = componentrecord.ComponentRecord([anchor3])
        >>> anchor4 = anchor_coord.Anchor_Coord(1200, 1800)
        >>> compRec3 = componentrecord.ComponentRecord([anchor4])
        >>> attRec1 = ligatureattach.LigatureAttach([compRec1, compRec2, compRec3])
        >>> ligArray1 = ligaturearray.LigatureArray({38: attRec1})
        >>> obj = MarkToLigature(mark=markArray1, ligature=ligArray1)
        >>> ed = utilities.fakeEditor(80)
        >>> ga = runningglyphs.GlyphList.fromiterable([38, -1, 77, 12, -1])
        >>> ga[0].ligInputOffsets = (0, 1, 4)
        >>> def funcIgs(*a, **k):
        ...   k['wantMarks'][:] = [False, False, False, True, False]
        ...   return [False, True, True, False, True]
        >>> igsFunc = lambda *a, **k: [False, True, False]
        >>> r, count = obj._runOne_RL(ga, 3, igsFunc=funcIgs, editor=ed)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 38, originalOffset = 0 
        glyph -1, originalOffset = 1 
        glyph 77, originalOffset = 2 
        glyph 12, originalOffset = 3 xPlacementDelta = -150, yPlacementDelta = 700, backIndex = -3
        glyph -1, originalOffset = 4 
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
        
        while (walk >= 0) and igOrMark[walk]:  # look for prior ligature
            walk -= 1
        
        if walk == -1:
            return (None, 0)
        
        lig = self.ligature
        E = effect.Effect
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        gLig = glyphArray[walk]
        
        if gLig not in lig:
            return (None, 0)
        
        # Determine which split index this is
        
        moo = gMark.originalOffset
        
        if getattr(gLig, 'ligInputOffsets', None):
            splitIndex = sum(moo >= n for n in gLig.ligInputOffsets) - 1
        else:
            splitIndex = -1
        
        ba = lig[gLig][splitIndex]
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
        Adds the binary data to the specified LinkedWriter. No keyword
        arguments are used; however, at some point we may change this to allow
        shared device and anchor pools across multiple lookups.
        
        >>> obj, ed = _makeTest()
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 000C 0016 0002  001E 0030 0002 0001 |...........0....|
              10 | 000C 000F 0000 0001  0002 0028 002D 0004 |...........(.-..|
              20 | 0000 0030 0000 0036  0001 003C 0001 0042 |...0...6...<...B|
              30 | 0002 0006 0014 0003  0030 0036 003C 0042 |.........0.6.<.B|
              40 | 0048 004E 0002 0046  004C 0052 0058 0001 |.H.N...F.L.R.X..|
              50 | 00FA 006E 0001 015E  0064 0001 015E FFEC |...n...^.d...^..|
              60 | 0001 00FF 0073 0001  012C 06A4 0001 0122 |.....s...,....."|
              70 | FFB5 0001 0384 06CC  0001 037A FFB5 0001 |...........z....|
              80 | 05DC 069A 0001 05D7  FFB5 0001 01C2 0640 |...............@|
              90 | 0001 01C2 FFE2 0001  0546 0640 0001 0546 |.........F.@...F|
              A0 | FFD3                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        markBackMap, ligBackMap = {}, {}
        
        markCovTable = coverage.Coverage.fromglyphset(
          self.mark,
          backMap = markBackMap)
        
        markCovStake = w.getNewStake()
        
        ligCovTable = coverage.Coverage.fromglyphset(
          self.ligature,
          backMap = ligBackMap)
        
        ligCovStake = w.getNewStake()
        
        markClassCount = 1 + utilities.safeMax(
          obj.markClass
          for obj in self.mark.values())
        
        w.add("H", 1)  # format 1
        w.addUnresolvedOffset("H", stakeValue, markCovStake)
        w.addUnresolvedOffset("H", stakeValue, ligCovStake)
        w.add("H", markClassCount)
        markStake = w.getNewStake()
        ligStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, markStake)
        w.addUnresolvedOffset("H", stakeValue, ligStake)
        
        # Resolve the references
        markCovTable.buildBinary(w, stakeValue=markCovStake, **kwArgs)
        ligCovTable.buildBinary(w, stakeValue=ligCovStake, **kwArgs)
        orderedKeys = []
        anchorPool = {}
        devicePool = {}
        
        d = {
          'anchorPool': anchorPool,
          'devicePool': devicePool,
          'orderedKeys': orderedKeys}
        
        self.mark.buildBinary(w, stakeValue=markStake, **d)
        self.ligature.buildBinary(w, stakeValue=ligStake, **d)
        
        for key in orderedKeys:
            obj, objStake = anchorPool[key]
            obj.buildBinary(w, stakeValue=objStake, devicePool=devicePool, **kwArgs)
        
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
              y-coordinate: 115
        Ligature Array:
          40:
            Ligature Component #1:
              Class 0:
                x-coordinate: 300
                y-coordinate: 1700
              Class 1:
                x-coordinate: 290
                y-coordinate: -75
            Ligature Component #2:
              Class 0:
                x-coordinate: 900
                y-coordinate: 1740
              Class 1:
                x-coordinate: 890
                y-coordinate: -75
            Ligature Component #3:
              Class 0:
                x-coordinate: 1500
                y-coordinate: 1690
              Class 1:
                x-coordinate: 1495
                y-coordinate: -75
          45:
            Ligature Component #1:
              Class 0:
                x-coordinate: 450
                y-coordinate: 1600
              Class 1:
                x-coordinate: 450
                y-coordinate: -30
            Ligature Component #2:
              Class 0:
                x-coordinate: 1350
                y-coordinate: 1600
              Class 1:
                x-coordinate: 1350
                y-coordinate: -45
        
        >>> d = obj.effectExtrema(forHorizontal=True, editor=e)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        12 (1630, 0)
        13 (1640, 0)
        14 (0, -55)
        15 (0, -190)
        
        >>> d = obj.effectExtrema(forHorizontal=False, editor=e)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        12 (1250, 0)
        13 (1150, -50)
        14 (1145, -60)
        15 (1240, 0)
        """
        
        cache = kwArgs.get('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        lig = self.ligature
        m = self.mark
        
        for baseGlyph in lig:
            for relIndex, ba in enumerate(lig[baseGlyph]):
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
        Creates and returns a new MarkToLigature from the specified
        FontWorkerSource, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> _test_FW_fws.goto(1) # go back to start of file
        >>> mtl = MarkToLigature.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger)
        >>> mtl.pprint()
        Mark Array:
          3:
            Mark Class: 1
            Mark Anchor:
              x-coordinate: 123
              y-coordinate: 234
              Contour point index: 12
              Glyph index: 3
          5:
            Mark Class: 2
            Mark Anchor:
              x-coordinate: 345
              y-coordinate: 456
              Contour point index: 23
              Glyph index: 5
          8:
            Mark Class: 2
            Mark Anchor:
              x-coordinate: 567
              y-coordinate: 678
              Contour point index: 34
              Glyph index: 8
          9:
            Mark Class: 2
            Mark Anchor:
              x-coordinate: 123
              y-coordinate: 987
        Ligature Array:
          13:
            Ligature Component #1:
              Class 0:
                x-coordinate: 789
                y-coordinate: 890
                Contour point index: 45
                Glyph index: 13
              Class 1:
                (no data)
              Class 2:
                (no data)
            Ligature Component #2:
              Class 0:
                (no data)
              Class 1:
                x-coordinate: 987
                y-coordinate: 876
                Contour point index: 56
                Glyph index: 13
              Class 2:
                (no data)
          21:
            Ligature Component #1:
              Class 0:
                (no data)
            Ligature Component #2:
              Class 0:
                (no data)
              Class 1:
                (no data)
              Class 2:
                x-coordinate: 765
                y-coordinate: 654
                Contour point index: 67
                Glyph index: 21
        >>> mtl = MarkToLigature.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.marktoligature - WARNING - line 4 -- glyph 'xyz' not found
        FW_test.marktoligature - WARNING - line 5 -- unexpected token: foo
        FW_test.marktoligature - WARNING - line 9 -- glyph 'abc' not found
        FW_test.marktoligature - WARNING - line 10 -- unexpected token: bar
        FW_test.marktoligature - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> mtl.pprint()
        Mark Array:
          3:
            Mark Class: 1
            Mark Anchor:
              x-coordinate: 123
              y-coordinate: 234
              Contour point index: 12
              Glyph index: 3
          5:
            Mark Class: 2
            Mark Anchor:
              x-coordinate: 345
              y-coordinate: 456
              Contour point index: 23
              Glyph index: 5
          8:
            Mark Class: 2
            Mark Anchor:
              x-coordinate: 567
              y-coordinate: 678
              Contour point index: 34
              Glyph index: 8
        Ligature Array:
          13:
            Ligature Component #1:
              Class 0:
                x-coordinate: 789
                y-coordinate: 890
                Contour point index: 45
                Glyph index: 13
              Class 1:
                (no data)
              Class 2:
                (no data)
            Ligature Component #2:
              Class 0:
                (no data)
              Class 1:
                x-coordinate: 987
                y-coordinate: 876
                Contour point index: 56
                Glyph index: 13
              Class 2:
                (no data)
          21:
            Ligature Component #1:
              Class 0:
                (no data)
            Ligature Component #2:
              Class 0:
                (no data)
              Class 1:
                (no data)
              Class 2:
                x-coordinate: 765
                y-coordinate: 654
                Contour point index: 67
                Glyph index: 21
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("marktoligature")
        startingLineNumber = fws.lineNumber
        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        LA = ligatureattach.LigatureAttach
        r = cls()

        # first pass
        fws.push()
        classSet = set()
        
        for line in fws:
            if line in terminalStrings:
                break

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0] == 'mark':
                    classNum = fwsint(tokens[2])
                    classSet.add(classNum)
                
                elif tokens[0] == 'ligature':
                    classNum = fwsint(tokens[4])
                    classSet.add(classNum)
                
                else:
                    # ignore any unexpected tokens as they will be caught in
                    # second pass
                    continue

        # map the original classes to 0, 1, 2, 3...
        numClasses = len(classSet)
        classDict = {}
        # temporary ligature component anchor dict to gather multiple anchor defs
        ligComponentDict = defaultdict(lambda: [None for _ in range(numClasses)])
        
        for i, classNum in enumerate(sorted(list(classSet))):
            classDict[classNum] = i

        # go back and do a second pass
        fws.pop()
        
        for line in fws:
            if line in terminalStrings:
                # build componentRecords from entries. Keys are 3-tuples of
                # glyphIndex, componentIndex, componentCount
                for grec, cmpr in ligComponentDict.items():
                    gi, ci, cc = grec
                    if gi not in r.ligature:
                        r.ligature[gi] = ligatureattach.LigatureAttach(
                          cc * [componentrecord.ComponentRecord((None,))])
                    r.ligature[gi][ci - 1] = componentrecord.ComponentRecord(cmpr)

                return r

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() in ('mark', 'ligature'):
                    glyphName = tokens[1]
                    glyphIndex = namer.glyphIndexFromString(glyphName)
                    
                    if glyphIndex is None:
                        logger.warning((
                          'V0956',
                          (fws.lineNumber, glyphName),
                          "line %d -- glyph '%s' not found"))
                        
                        continue
                    
                    if tokens[0].lower() == 'mark':
                        if glyphIndex in r.mark:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, glyphName),
                              "line %d -- ignoring duplicated mark definition "
                              "of '%s'"))
                        
                        else:
                            markClass = classDict[int(tokens[2])]
                            [xCoordinate, yCoordinate] = [
                                int(x) for x in tokens[3].split(',')]

                            if len(tokens) == 4:
                                markAnchor = anchor_coord.Anchor_Coord(
                                    xCoordinate,
                                    yCoordinate)
                            
                            else:
                                apd = {'glyphIndex': glyphIndex}
                                contourPointIndex = fwsint(tokens[4])
                                apd['pointIndex'] = contourPointIndex
                                markAnchor = anchor_point.Anchor_Point(
                                    xCoordinate,
                                    yCoordinate,
                                    **apd)

                            r.mark[glyphIndex] = markrecord.MarkRecord(
                                markClass = markClass,
                                markAnchor = markAnchor)

                    else: # tokens[0] == 'ligature':
                        componentIndex = int(tokens[2])
                        componentCount = int(tokens[3])
                        anchorClass = classDict[int(tokens[4])]
                        ligKey = (glyphIndex, componentIndex, componentCount)
                        anchorList = ligComponentDict[ligKey]
                        [xCoordinate, yCoordinate] = [
                            int(x) for x in tokens[5].split(',')]

                        if anchorList[anchorClass] is not None:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, glyphName, componentIndex),
                              "line %d -- ignoring duplicated ligature "
                              "defninition of '%s[%d]'"))
                        
                        else:
                            if len(tokens) == 6:
                                anchordef = anchor_coord.Anchor_Coord(
                                    xCoordinate, yCoordinate)
                            else:
                                apd = {'glyphIndex': glyphIndex}
                                if len(tokens) > 6:
                                    contourPointIndex = fwsint(tokens[6])
                                    apd['pointIndex'] = contourPointIndex

                                anchordef = anchor_point.Anchor_Point(
                                    xCoordinate, yCoordinate, **apd)
                                    
                            ligComponentDict[ligKey][anchorClass] = anchordef

                else:
                    logger.warning((
                        'V0960',
                        (fws.lineNumber, tokens[0]),
                        'line %d -- unexpected token: %s'))

        logger.warning((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))
        for grec, cmpr in ligComponentDict.items():
            gi, ci, cc = grec
            if gi not in r.ligature:
                r.ligature[gi] = ligatureattach.LigatureAttach(
                  cc * [componentrecord.ComponentRecord((None,))])
            r.ligature[gi][ci - 1] = componentrecord.ComponentRecord(cmpr)
        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkToLigature object from the specified
        walker, doing source validation.
        
        >>> s = _makeTest()[0].binaryString()
        >>> fvb = MarkToLigature.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("marktoligature_test")
        >>> obj = fvb(s, logger=logger)
        marktoligature_test.marktoligature - DEBUG - Walker has 162 bytes remaining.
        marktoligature_test.marktoligature.mark.coverage - DEBUG - Walker has 150 remaining bytes.
        marktoligature_test.marktoligature.mark.coverage - DEBUG - Format is 2, count is 1
        marktoligature_test.marktoligature.mark.coverage - DEBUG - Raw data are [(12, 15, 0)]
        marktoligature_test.marktoligature.ligature.coverage - DEBUG - Walker has 140 remaining bytes.
        marktoligature_test.marktoligature.ligature.coverage - DEBUG - Format is 1, count is 2
        marktoligature_test.marktoligature.ligature.coverage - DEBUG - Raw data are [40, 45]
        marktoligature_test.marktoligature.markarray - DEBUG - Walker has 132 remaining bytes.
        marktoligature_test.marktoligature.markarray.glyph 12.markrecord - DEBUG - Walker has 130 bytes remaining.
        marktoligature_test.marktoligature.markarray.glyph 12.markrecord.anchor_coord - DEBUG - Walker has 84 remaining bytes.
        marktoligature_test.marktoligature.markarray.glyph 13.markrecord - DEBUG - Walker has 126 bytes remaining.
        marktoligature_test.marktoligature.markarray.glyph 13.markrecord.anchor_coord - DEBUG - Walker has 78 remaining bytes.
        marktoligature_test.marktoligature.markarray.glyph 14.markrecord - DEBUG - Walker has 122 bytes remaining.
        marktoligature_test.marktoligature.markarray.glyph 14.markrecord.anchor_coord - DEBUG - Walker has 72 remaining bytes.
        marktoligature_test.marktoligature.markarray.glyph 15.markrecord - DEBUG - Walker has 118 bytes remaining.
        marktoligature_test.marktoligature.markarray.glyph 15.markrecord.anchor_coord - DEBUG - Walker has 66 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray - DEBUG - Walker has 114 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach - DEBUG - Walker has 108 bytes remaining.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 0.componentrecord - DEBUG - Walker has 106 bytes remaining.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 0.componentrecord.[0].anchor_coord - DEBUG - Walker has 60 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 0.componentrecord.[1].anchor_coord - DEBUG - Walker has 54 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord - DEBUG - Walker has 102 bytes remaining.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord.[0].anchor_coord - DEBUG - Walker has 48 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord.[1].anchor_coord - DEBUG - Walker has 42 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 2.componentrecord - DEBUG - Walker has 98 bytes remaining.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 2.componentrecord.[0].anchor_coord - DEBUG - Walker has 36 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 40.ligatureattach.ligature component 2.componentrecord.[1].anchor_coord - DEBUG - Walker has 30 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 45.ligatureattach - DEBUG - Walker has 94 bytes remaining.
        marktoligature_test.marktoligature.ligaturearray.glyph 45.ligatureattach.ligature component 0.componentrecord - DEBUG - Walker has 92 bytes remaining.
        marktoligature_test.marktoligature.ligaturearray.glyph 45.ligatureattach.ligature component 0.componentrecord.[0].anchor_coord - DEBUG - Walker has 24 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 45.ligatureattach.ligature component 0.componentrecord.[1].anchor_coord - DEBUG - Walker has 18 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 45.ligatureattach.ligature component 1.componentrecord - DEBUG - Walker has 88 bytes remaining.
        marktoligature_test.marktoligature.ligaturearray.glyph 45.ligatureattach.ligature component 1.componentrecord.[0].anchor_coord - DEBUG - Walker has 12 remaining bytes.
        marktoligature_test.marktoligature.ligaturearray.glyph 45.ligatureattach.ligature component 1.componentrecord.[1].anchor_coord - DEBUG - Walker has 6 remaining bytes.
        
        >>> fvb(s[:5], logger=logger)
        marktoligature_test.marktoligature - DEBUG - Walker has 5 bytes remaining.
        marktoligature_test.marktoligature - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("marktoligature")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1, but got format %d."))
            
            return None
        
        markCovTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger.getChild("mark"),
          **kwArgs)
        
        if markCovTable is None:
            return None
        
        ligCovTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger.getChild("ligature"),
          **kwArgs)
        
        if ligCovTable is None:
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
        
        b = ligaturearray.LigatureArray.fromvalidatedwalker(
          w.subWalker(bOffset),
          coverage = ligCovTable,
          classCount = classCount,
          logger = logger,
          **kwArgs)
        
        if b is None:
            return None
        
        return cls(mark=m, ligature=b)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkToLigature from the specified walker.
        
        >>> mtl = _makeTest()[0]
        >>> mtl == MarkToLigature.frombytes(mtl.binaryString())
        True
        """
        
        format = w.unpack("H")
        
        if format != 1:
            raise ValueError("Unknown MarkToLigature format: %d" % (format,))
        
        cFunc = coverage.Coverage.fromwalker
        markCovTable = cFunc(w.subWalker(w.unpack("H")))
        ligCovTable = cFunc(w.subWalker(w.unpack("H")))
        classCount, mOffset, bOffset = w.unpack("3H")
        kwArgs.pop('classCount', None)
        kwArgs.pop('coverage', None)
        
        m = markarray.MarkArray.fromwalker(
          w.subWalker(mOffset),
          coverage = markCovTable,
          **kwArgs)
        
        b = ligaturearray.LigatureArray.fromwalker(
          w.subWalker(bOffset),
          coverage = ligCovTable,
          classCount = classCount,
          **kwArgs)
        
        return cls(mark=m, ligature=b)
    
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
        Write Mark To Ligature lookup as Font Worker-style source.
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex
        getmap = kwArgs.get('datatable').getXYtoPointMap
            
        for k, v in sorted(self.mark.items()):
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
              
        for k, v in sorted(self.ligature.items()):
            for vi, vv in enumerate(v):
                if vv is not None:
                    for lci, lc in enumerate(vv):
                        if lc is not None:
                            if lc.anchorKind == 'point':
                                map = getmap(k, **kwArgs)
                                pt = map.get((lc.x, lc.y), None)
                                pts = "\t%d" % (pt,) if pt else ""
                            else:
                                pts = ""

                            t = (
                              bnfgi(k),
                              vi + 1,
                              len(v),
                              lci,
                              lc.x,
                              lc.y,
                              pts)

                            s.write("ligature\t%s\t%d\t%d\t%d\t%d,%d%s\n" % t)

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
        The test case being made has two ligatures, glyph 40 (a 3-component
        ligature) and glyph 45 (a 2-component ligature). There are 4 marks:
        glyphs 12 (above), 13 (above), 14 (below), and 15 (below).
        """
        
        from fontio3 import hmtx
        from fontio3.GDEF import GDEF_v1
        
        lig1_split1_above = anchor_coord.Anchor_Coord(300, 1700)
        lig1_split2_above = anchor_coord.Anchor_Coord(900, 1740)
        lig1_split3_above = anchor_coord.Anchor_Coord(1500, 1690)
        lig1_split1_below = anchor_coord.Anchor_Coord(290, -75)
        lig1_split2_below = anchor_coord.Anchor_Coord(890, -75)
        lig1_split3_below = anchor_coord.Anchor_Coord(1495, -75)
        lig2_split1_above = anchor_coord.Anchor_Coord(450, 1600)
        lig2_split2_above = anchor_coord.Anchor_Coord(1350, 1600)
        lig2_split1_below = anchor_coord.Anchor_Coord(450, -30)
        lig2_split2_below = anchor_coord.Anchor_Coord(1350, -45)
        mark1_anchor = anchor_coord.Anchor_Coord(250, 110)
        mark2_anchor = anchor_coord.Anchor_Coord(350, 100)
        mark3_anchor = anchor_coord.Anchor_Coord(350, -20)
        mark4_anchor = anchor_coord.Anchor_Coord(255, 115)
        
        lig1_split1 = componentrecord.ComponentRecord([
          lig1_split1_above,    # class 0
          lig1_split1_below])   # class 1
        
        lig1_split2 = componentrecord.ComponentRecord([
          lig1_split2_above,    # class 0
          lig1_split2_below])   # class 1
        
        lig1_split3 = componentrecord.ComponentRecord([
          lig1_split3_above,    # class 0
          lig1_split3_below])   # class 1
        
        lig2_split1 = componentrecord.ComponentRecord([
          lig2_split1_above,    # class 0
          lig2_split1_below])   # class 1
        
        lig2_split2 = componentrecord.ComponentRecord([
          lig2_split2_above,    # class 0
          lig2_split2_below])   # class 1
        
        lig1 = ligatureattach.LigatureAttach([
          lig1_split1,
          lig1_split2,
          lig1_split3])
        
        lig2 = ligatureattach.LigatureAttach([
          lig2_split1,
          lig2_split2])
        
        lig = ligaturearray.LigatureArray({40: lig1, 45: lig2})
        mark1 = markrecord.MarkRecord(0, mark1_anchor)
        mark2 = markrecord.MarkRecord(0, mark2_anchor)
        mark3 = markrecord.MarkRecord(1, mark3_anchor)
        mark4 = markrecord.MarkRecord(1, mark4_anchor)
        
        mark = markarray.MarkArray({
          12: mark1,
          13: mark2,
          14: mark3,
          15: mark4})
        
        r = MarkToLigature(mark, lig)
        e = utilities.fakeEditor(0x10000)
        e.hmtx = hmtx.Hmtx()
        e.hmtx[12] = hmtx.MtxEntry(0, 50)
        e.hmtx[13] = hmtx.MtxEntry(0, 30)
        e.hmtx[14] = hmtx.MtxEntry(0, 45)
        e.hmtx[15] = hmtx.MtxEntry(0, 55)
        e.hmtx[40] = hmtx.MtxEntry(1900, 50)
        e.hmtx[45] = hmtx.MtxEntry(1970, 50)
        e.GDEF = GDEF_v1.GDEF()
        e.GDEF.glyphClasses[12] = 3
        e.GDEF.glyphClasses[13] = 3
        e.GDEF.glyphClasses[14] = 3
        e.GDEF.glyphClasses[15] = 3
        
        return r, e

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'X': 3,
        'Y': 5,
        'Z': 8,
        'AB': 13,
        'BC': 21,
        'x': 9,
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        mark	X	 1	 123, 234	 12
        mark	Y	 2	 345, 456	 23
        mark	Z	 2	 567, 678	 34
        mark	x	 2	 123, 987
        ligature	AB	1	 2	 0	 789,890	 45
        ligature	AB	2	 2	 1	 987,876	 56
        ligature	BC	2	 2	 2	 765,654	 67
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        mark	X	 1	 123, 234	 12
        mark	Y	 2	 345, 456	 23
        mark	xyz	 2	 345, 456	 23
        foo
        mark	Z	 2	 567, 678	 34
        ligature	AB	1	 2	 0	 789,890	 45
        ligature	AB	2	 2	 1	 987,876	 56
        ligature	abc	2	 2	 1	 987,876	 56
        bar
        ligature	BC	2	 2	 2	 765,654	 67
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
