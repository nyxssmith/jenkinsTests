#
# cursive.py
#
# Copyright © 2007-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 1 GPOS cursive positioning tables.
"""

# System imports
import itertools
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GPOS import anchor, effect, entryexit, anchor_coord, anchor_point
from fontio3.opentype import coverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs.pop('logger')
    
    for glyph, eeObj in obj.items():
        if not (eeObj.entry or eeObj.exit):
            logger.warning((
              'V0336',
              (glyph,),
              "Glyph %d has neither an Entry nor an Exit."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Cursive(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing format 1 cursive GPOS tables.
    
    These are dicts mapping glyph indices to EntryExit records.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    xyz13:
      Entry anchor:
        x-coordinate: -40
        y-coordinate: 18
    xyz41:
      Entry anchor:
        x-coordinate: 10
        y-coordinate: 20
        Device for x:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
      Exit anchor:
        x-coordinate: -40
        y-coordinate: 18
        Contour point index: 6
        Glyph index: 40
    xyz6:
      Exit anchor:
        x-coordinate: -40
        y-coordinate: 18
    
    >>> logger = utilities.makeDoctestLogger("cursivetest")
    >>> e = _fakeEditor()
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    cursivetest.[40].exit - WARNING - Point 6 in glyph 40 has coordinates (950, 750), but the Anchor data in this object are (-40, 18).
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        item_validatekwargsfunc = (lambda x, k: {'glyphIndex': k}),
        map_maxcontextfunc = (lambda d: 1),
        map_validatefunc_partial = _validate)
    
    kind = ('GPOS', 3)
    kindString = "Cursive positioning table"
    
    #
    # Methods
    #
    
    def _runOne_LR(self, glyphArray, startIndex, **kwArgs):
        """
        Private method used by runOne().
        
        >>> anchor1 = anchor_coord.Anchor_Coord(1800, 200)
        >>> anchor2 = anchor_coord.Anchor_Coord(50, 375)
        >>> ee1 = entryexit.EntryExit(exit=anchor1)
        >>> ee2 = entryexit.EntryExit(entry=anchor2)
        >>> obj = Cursive({35: ee1, 39: ee2})
        >>> ed = utilities.fakeEditor(50, hmtx={35: 1900, 39: 420})
        >>> ga = runningglyphs.GlyphList.fromiterable([35, 77, 39])
        >>> igsFunc = lambda *a, **k: [False, True, False]
        >>> r, count = obj._runOne_LR(ga, 0, igsFunc=igsFunc, editor=ed)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 35, originalOffset = 0 
        glyph 77, originalOffset = 1 
        glyph 39, originalOffset = 2 xPlacementDelta = -150, yPlacementDelta = -175, xAdvanceDelta = -150
        """
        
        igsFunc = kwArgs['igsFunc']
        igs = igsFunc(glyphArray, **kwArgs)
        
        v = [
          (g, i)
          for i, g in enumerate(glyphArray)
          if (not igs[i])]
        
        if len(v) < 2:
            return (None, 0)
        
        vNonIgs = [x[0] for x in v]
        vBackMap = [x[1] for x in v]
        startIndexNI = vBackMap.index(startIndex)
        
        if startIndexNI == len(vNonIgs) - 1:
            return (None, 0)
        
        g1, g2 = vNonIgs[startIndexNI:startIndexNI+2]
        
        if (g1 not in self) or (g2 not in self):
            return (None, 0)
        
        exit = self[g1].exit
        entry = self[g2].entry
        
        if (exit is None) or (entry is None):
            return (None, 0)
        
        # Whew. If we get here it's an actual connecting case. Since this is
        # the LR case, we move the second glyph.
        
        secondIndex = vBackMap[startIndexNI+1]
        mtxTable = kwArgs['editor'].hmtx
        E = effect.Effect
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        effLeft = r[startIndex]

        # Process variations to the anchors (if any)
        
        varBDelX = varBDelY = varMDelX = varMDelY = 0
        coordLAC = kwArgs.get('coordinateTuple', None)
        
        if coordLAC is not None:
            if exit.anchorKind == 'variation':
                if exit.xVariation is not None:
                    varBDelX = int(round(exit.xVariation.interpolate(coordLAC)))
                if exit.yVariation is not None:
                    varBDelY = int(round(exit.yVariation.interpolate(coordLAC)))
            
            if entry.anchorKind == 'variation':
                if entry.xVariation is not None:
                    varMDelX = int(round(entry.xVariation.interpolate(coordLAC)))
                if entry.yVariation is not None:
                    varMDelY = int(round(entry.yVariation.interpolate(coordLAC)))
        
        deltaX = sum((
          -(entry.x + varMDelX),
          -effLeft.xAdvanceDelta,
          -mtxTable[g1].advance,
          effLeft.xPlacementDelta,
          (exit.x + varBDelX)))

        deltaY = sum((
          -(entry.y + varMDelY),
          -effLeft.yAdvanceDelta,
          # 0, -- change this when vertical text is supported
          effLeft.yPlacementDelta,
          (exit.y + varBDelY)))

        r[secondIndex].xPlacementDelta += deltaX
        r[secondIndex].yPlacementDelta += deltaY
        penned = max(deltaX, -mtxTable[g2].advance)
        r[secondIndex].xAdvanceDelta += penned
        return (r, 1)
    
    def _runOne_RL(self, glyphArray, startIndex, **kwArgs):
        """
        Note that the expectation here is that startIndex will march backward
        through the glyph array (the rightToLeft flag in the Lookup dictates
        this).
        
        For the example here, imagine glyph 31 is initial lam, glyph 38 is
        medial meem, and glyph 44 is final jeem. This is best thought of as a
        Nastaliq example; makes the vertical movement more obvious.
        
        The metrics are:
        
        glyph       adv         exit        entry
           31       325        (5, 8)         -
           38       530        (7, 1)     (490, 265)
           44      1175           -       (800, 710)
        
        >>> g31Exit = anchor_coord.Anchor_Coord(5, 8)
        >>> g31EE = entryexit.EntryExit(exit=g31Exit)
        >>> g38Entry = anchor_coord.Anchor_Coord(490, 265)
        >>> g38Exit = anchor_coord.Anchor_Coord(7, 1)
        >>> g38EE = entryexit.EntryExit(entry=g38Entry, exit=g38Exit)
        >>> g44Entry = anchor_coord.Anchor_Coord(800, 710)
        >>> g44EE = entryexit.EntryExit(entry=g44Entry)
        >>> obj = Cursive({31: g31EE, 38: g38EE, 44: g44EE})
        >>> ed = utilities.fakeEditor(50, hmtx={31: 325, 38: 530, 44: 1175})
        >>> ga = runningglyphs.GlyphList.fromiterable([31, 77, 38, 77, 44])
        >>> igsFunc = lambda *a, **k: [False, True, False, True, False]
        
        Since we march in reverse order we start with startIndex=4:
        
        >>> r, count = obj._runOne_RL(ga, 4, igsFunc=igsFunc, editor=ed)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 31, originalOffset = 0 
        glyph 77, originalOffset = 1 
        glyph 38, originalOffset = 2 xPlacementDelta = -382, yPlacementDelta = 709, xAdvanceDelta = -382
        glyph 77, originalOffset = 3 
        glyph 44, originalOffset = 4 
        
        Then we do the next (in reverse order), startIndex=2. Note that we pass
        in the cumulative effects here!
        
        >>> r, count = obj._runOne_RL(ga, 2, igsFunc=igsFunc, editor=ed, cumulEffects=r)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 31, originalOffset = 0 xPlacementDelta = -45, yPlacementDelta = 966, xAdvanceDelta = -45
        glyph 77, originalOffset = 1 
        glyph 38, originalOffset = 2 xPlacementDelta = -382, yPlacementDelta = 709, xAdvanceDelta = -382
        glyph 77, originalOffset = 3 
        glyph 44, originalOffset = 4 
        """
        
        igsFunc = kwArgs['igsFunc']
        igs = igsFunc(glyphArray, **kwArgs)
        
        v = [
          (g, i)
          for i, g in enumerate(glyphArray)
          if (not igs[i])]
        
        if len(v) < 2:
            return (None, 0)
        
        vNonIgs = [x[0] for x in v]
        vBackMap = [x[1] for x in v]
        startIndexNI = vBackMap.index(startIndex)
        
        if startIndexNI == 0:
            return (None, 0)
        
        g2, g1 = vNonIgs[startIndexNI-1:startIndexNI+1]
        
        if (g1 not in self) or (g2 not in self):
            return (None, 0)
        
        entry = self[g1].entry
        exit = self[g2].exit
        
        if (exit is None) or (entry is None):
            return (None, 0)
        
        # Whew. If we get here it's an actual connecting case.
        
        mtxTable = kwArgs['editor'].hmtx
        E = effect.Effect
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        effRight = r[startIndex]  # right eventually...
        
        # Process variations to the anchors (if any)
        
        varBDelX = varBDelY = varMDelX = varMDelY = 0
        coordLAC = kwArgs.get('coordinateTuple', None)
        
        if coordLAC is not None:
            if entry.anchorKind == 'variation':
                if entry.xVariation is not None:
                    varBDelX = int(round(entry.xVariation.interpolate(coordLAC)))
                if entry.yVariation is not None:
                    varBDelY = int(round(entry.yVariation.interpolate(coordLAC)))
            
            if exit.anchorKind == 'variation':
                if exit.xVariation is not None:
                    varMDelX = int(round(exit.xVariation.interpolate(coordLAC)))
                if exit.yVariation is not None:
                    varMDelY = int(round(exit.yVariation.interpolate(coordLAC)))
        
        deltaX = sum((
          -(exit.x + varMDelX),
          -effRight.xAdvanceDelta,
          -mtxTable[g1].advance,
          effRight.xPlacementDelta,
          (entry.x + varBDelX)))
        
        deltaY = sum((
          -(exit.y + varMDelY),
          -effRight.yAdvanceDelta,
          # 0, -- change this when vertical text is supported
          effRight.yPlacementDelta,
          (entry.y + varBDelY)))
        
        secondIndex = vBackMap[startIndexNI-1]
        r[secondIndex].xPlacementDelta += deltaX
        r[secondIndex].yPlacementDelta += deltaY
        penned = max(deltaX, -mtxTable[g2].advance)
        r[secondIndex].xAdvanceDelta += penned
        return (r, 1)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Cursive object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0012 0003 0000  001C 001C 0000 0022 |..............."|
              10 | 002C 0001 0003 0005  000C 0028 0001 FFD8 |.,.........(....|
              20 | 0012 0003 000A 0014  0012 0000 0002 FFD8 |................|
              30 | 0012 0006 000C 0012  0001 8C04           |............    |
        """
        
        # Add the fixed and unresolved content
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format
        covIndexToGlyphMap = {}
        
        covTable = coverage.Coverage.fromglyphset(
          self,
          backMap = covIndexToGlyphMap)
        
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        w.add("H", len(self))
        pool = {}
        orderedKeys = []
        
        for covIndex in range(len(self)):
            obj = self[covIndexToGlyphMap[covIndex]]
            
            for anchorObj in (obj.entry, obj.exit):
                if anchorObj is None:
                    w.add("H", 0)
                
                else:
                    immut = anchorObj.asImmutable()
                    
                    if immut not in pool:
                        pool[immut] = (anchorObj, w.getNewStake())
                        orderedKeys.append(immut)
                    
                    w.addUnresolvedOffset("H", stakeValue, pool[immut][1])
        
        # Resolve the references
        covTable.buildBinary(w, stakeValue=covStake)
        devicePool = {}
        
        for key in orderedKeys:
            obj, objStake = pool[key]
            
            obj.buildBinary(
              w,
              stakeValue = objStake,
              posBase = stakeValue,
              devicePool = devicePool)
        
        it = sorted(
          (obj.asImmutable(), obj, stake)
          for obj, stake in devicePool.values())
        
        for t in it:
            t[1].buildBinary(w, stakeValue=t[2])
    
    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectExtrema() instead.")
    
    def effectExtrema(self, forHorizontal=True, **kwArgs):
        """
        Because of the nature of cursive connections, most of the time this
        method would result in values of None for all glyphs, since at least
        one glyph is likely to have both an entry and an exit at different
        y-values. So we elide processing for cursive subtables altogether.
        """
        
        return {}

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new Cursive object from the specified
        FontWorkerSource with source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = Cursive.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.cursive - WARNING - line 4 -- glyph 'sigma' not found
        FW_test.cursive - WARNING - line 5 -- glyph 'sigma' not found
        FW_test.cursive - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> obj.pprint()
        42:
          Entry anchor:
            x-coordinate: 318
            y-coordinate: 108
            Contour point index: 26
            Glyph index: 42
          Exit anchor:
            x-coordinate: 0
            y-coordinate: 134
            Contour point index: 9
            Glyph index: 42
        """
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("cursive")

        startingLineNumber=fws.lineNumber
        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')

        r = cls()

        for line in fws:
            if line in terminalStrings:
                return r
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                if tokens[0].lower() == 'entry':
                    glyphName = tokens[1]
                    glyphIndex = namer.glyphIndexFromString(glyphName)
                    [xCoordinate, yCoordinate] = [
                        int(x) for x in tokens[2].split(',')]
                    if glyphIndex is None:
                        logger.warning(('V0956', (fws.lineNumber, glyphName),
                            "line %d -- glyph '%s' not found"))
                        continue

                    if glyphIndex in r and r[glyphIndex].entry:
                        logger.warning((
                            'Vxxxx',
                            (fws.lineNumber, glyphName),
                            "line %d -- ignoring duplicated entry anchor for '%s'"))

                    else:
                        if not glyphIndex in r:
                            r[glyphIndex] = entryexit.EntryExit()

                        if len(tokens) == 3:
                            r[glyphIndex].entry=anchor_coord.Anchor_Coord(
                                xCoordinate, yCoordinate)
                        else:
                            contourPointIndex = int(tokens[3])
                            r[glyphIndex].entry=anchor_point.Anchor_Point(
                                xCoordinate, yCoordinate, glyphIndex=glyphIndex,
                                pointIndex=contourPointIndex)

                elif tokens[0].lower() == 'exit':
                    glyphName = tokens[1]
                    glyphIndex = namer.glyphIndexFromString(glyphName)
                    [xCoordinate, yCoordinate] = [
                        int(x) for x in tokens[2].split(',')]

                    if glyphIndex is None:
                        logger.warning(('V0956', (fws.lineNumber, glyphName),
                            "line %d -- glyph '%s' not found"))
                        continue

                    if glyphIndex in r and r[glyphIndex].exit:
                        logger.warning((
                            'Vxxxx',
                            (fws.lineNumber, glyphName),
                            "line %d -- ignoring duplicated exit anchor for '%s'"))

                    else:
                        if not glyphIndex in r:
                            r[glyphIndex] = entryexit.EntryExit()

                        if len(tokens) == 3:
                            r[glyphIndex].exit=anchor_coord.Anchor_Coord(
                                xCoordinate, yCoordinate)
                        else:
                            contourPointIndex = int(tokens[3])
                            r[glyphIndex].exit=anchor_point.Anchor_Point(
                                xCoordinate, yCoordinate, glyphIndex=glyphIndex,
                                pointIndex=contourPointIndex)

                else:
                    logger.warning((
                        'V0960',
                        (fws.lineNumber, tokens[0]),
                        'line %d -- unexpected token: %s'))

        logger.warning(('V0958', (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))

        return r


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Cursive object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Cursive.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.cursive - DEBUG - Walker has 60 remaining bytes.
        test.cursive.coverage - DEBUG - Walker has 42 remaining bytes.
        test.cursive.coverage - DEBUG - Format is 1, count is 3
        test.cursive.coverage - DEBUG - Raw data are [5, 12, 40]
        test.cursive.glyph 5.anchor_coord - DEBUG - Walker has 32 remaining bytes.
        test.cursive.glyph 12.anchor_coord - DEBUG - Walker has 32 remaining bytes.
        test.cursive.glyph 40.anchor_device - DEBUG - Walker has 26 remaining bytes.
        test.cursive.glyph 40.anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        test.cursive.glyph 40.anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        test.cursive.glyph 40.anchor_device.x.device - DEBUG - Data are (35844,)
        test.cursive.glyph 40.anchor_point - DEBUG - Walker has 16 remaining bytes.
        
        >>> fvb(s[:4], logger=logger)
        test.cursive - DEBUG - Walker has 4 remaining bytes.
        test.cursive - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("cursive")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Unknown format %d for Cursive table."))
            
            return None
        
        covOffset, count = w.unpack("2H")
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger)
        
        if covTable is None:
            return None
        
        firstGlyphs = sorted(covTable)
        
        if count != len(firstGlyphs):
            logger.error((
              'V0334',
              (count, len(firstGlyphs)),
              "The EntryExitCount (%d) does not match the length of "
              "the Coverage (%d)."))
            
            return None
        
        if w.length() < 4 * count:
            logger.error((
              'V0335',
              (),
              "Insufficient bytes for the EntryExitRecords."))
            
            return None
        
        offsetPairs = w.group("2H", count)
        r = cls()
        fvw = anchor.Anchor_validated
        EntryExit = entryexit.EntryExit
        
        for glyph, (offset1, offset2) in zip(firstGlyphs, offsetPairs):
            subLogger = logger.getChild("glyph %d" % (glyph,))
            
            if offset1:
                rec1 = fvw(
                  w.subWalker(offset1),
                  glyphIndex = glyph,
                  logger = subLogger)
            
            else:
                rec1 = None
            
            if offset2:
                rec2 = fvw(
                  w.subWalker(offset2),
                  glyphIndex = glyph,
                  logger = subLogger)
            
            else:
                rec2 = None
            
            if rec1 or rec2:
                r[glyph] = EntryExit(rec1, rec2)
            
            else:
                logger.warning((
                  'V0336',
                  (glyph,),
                  "Glyph %d has neither an Entry nor an Exit."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Cursive object from the specified walker.
        
        >>> obj = Cursive.frombytes(_testingValues[0].binaryString())
        >>> obj.pprint_changes(_testingValues[0])
        """
        
        format = w.unpack("H")
        assert format == 1
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        firstGlyphs = sorted(covTable)
        count = w.unpack("H")
        assert count == len(firstGlyphs)
        offsetPairs = w.group("2H", count)
        r = cls()
        f = anchor.Anchor
        EntryExit = entryexit.EntryExit
        
        for glyph, (offset1, offset2) in zip(firstGlyphs, offsetPairs):
            if offset1:
                rec1 = f(w.subWalker(offset1), glyphIndex=glyph)
            else:
                rec1 = None
            
            if offset2:
                rec2 = f(w.subWalker(offset2), glyphIndex=glyph)
            else:
                rec2 = None
            
            if rec1 or rec2:
                r[glyph] = EntryExit(rec1, rec2)
        
        return r
    
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
        Writes contents of lookup to provided stream 's'.
        """
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex
        getmap = kwArgs.get('datatable').getXYtoPointMap
            
        for k,v in sorted(self.items()):
            m = getmap(k, **kwArgs)
            v.writeFontWorkerSource(s, lbl=bnfgi(k), map=m, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
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
        e.hmtx[40] = hmtx.MtxEntry(1900, 30)
        return e
    
    eev = entryexit._testingValues
    
    _testingValues = (
        Cursive({5: eev[0], 12: eev[1], 40: eev[2]}),)
    
    del eev
    
    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'BehxIni.11': 42
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        entry	BehxIni.11	 318, 108	 26
        exit	BehxIni.11	 0, 134	 9
        
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        entry	BehxIni.11	 318, 108	 26
        exit	BehxIni.11	 0, 134	 9
        entry	sigma	 123, 456	 78
        exit	sigma	 98, 765	 4
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
