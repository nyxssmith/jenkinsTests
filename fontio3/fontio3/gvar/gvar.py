#
# gvar.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'gvar' tables.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta

from fontio3.gvar import (
  axial_coordinates,
  deltas,
  deltas_dict,
  domain,
  glyph_dict,
  packed_points,
  point_dict)

from fontio3.utilities import writer
    
# -----------------------------------------------------------------------------

#
# Functions
#

def _pprint_axisOrder(p, obj, label, **kwArgs):
    if 'editor' not in kwArgs:
        p.simple(obj, label=label, **kwArgs)
        return
    
    e = kwArgs['editor']
    fvarObj = e.fvar
    nameObj = e.name
    sv = []
    
    for tag in obj:
        axisInfo = fvarObj[tag]
        nm = nameObj.getNameFromID(axisInfo.nameID)
        sv.append("'%s' (%s)" % (tag, nm))
    
    p.simple('(' + ', '.join(sv) + ')', label=label, **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Gvar(object, metaclass=simplemeta.FontDataMetaclass):
    """
    """
    
    attrSpec = dict(
        axisOrder = dict(
            attr_pprintfunc = _pprint_axisOrder),
        
        glyphData = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyph_dict.GlyphDict))
    
    VERSION = 0x10000  # class constant
    
    #
    # Methods
    #
    
    @staticmethod
    def _emitDeltaBand(w, v):
        """
        Emit a group of delta values.
        
        >>> v = [
        ...   -29, 15, 27, -26, -30, 36, 21, 22, -34, -36, -30, -3, -4, 11,
        ...   -15, 7, 7, 3, -10, -5, -12, -9, -12, -14, -29, -12, -4, -25,
        ...   26, 12, -19, -15, 38, 27, -41, -33, 34, 28, -19, -36, -36, -31,
        ...   -22, -6, 1, 2, -4, 2, -4, -1, 21, 19, 24, -5, -26, -18, 27, 32,
        ...   34, -24, -21, -20, 30, -17, -28]
        >>> w = writer.LinkedWriter()
        >>> Gvar._emitDeltaBand(w, v)
        >>> utilities.hexdump(w.binaryString())
               0 | 3FE3 0F1B E6E2 2415  16DE DCE2 FDFC 0BF1 |?.....$.........|
              10 | 0707 03F6 FBF4 F7F4  F2E3 F4FC E71A 0CED |................|
              20 | F126 1BD7 DF22 1CED  DCDC E1EA FA01 02FC |.&..."..........|
              30 | 02FC FF15 1318 FBE6  EE1B 2022 E8EB EC1E |.......... "....|
              40 | EF00 E4                                  |...             |
        """
        
        for k, g in itertools.groupby(v, bool):
            group = list(g)
            
            if not k:
                while len(group) > 64:
                    w.add("B", 0xBF)  # 64 zeroes
                    del group[:64]
                
                w.add("B", 0x80 + len(group) - 1)
                continue
            
            funcFitsByte = (lambda x: -128 <= x < 128)
            
            for k2, g2 in itertools.groupby(group, funcFitsByte):
                subGroup = list(g2)
                mask = (0 if k2 else 0x40)
                fmt = ("b" if k2 else "h")
                
                while len(subGroup) > 64:
                    w.add("B", mask + 63)
                    w.addGroup(fmt, subGroup[:64])
                    del subGroup[:64]
                
                w.add("B", mask + len(subGroup) - 1)
                w.addGroup(fmt, subGroup)
    
    def _fillGlyph(self, w, glyphIndex, globalCoords, pointCount, **kwArgs):
        """
        Given a walker whose base is the start of the header for a single
        glyph, add the entry for self.glyphData[glyphIndex].
        """
        
        nTuples, dataOffset = w.unpack("2H")
        sharedPointCase = bool(nTuples & 0x8000)
        nTuples &= 0x0FFF
        wSub = w.subWalker(dataOffset)
        
        if sharedPointCase:
            # note the call here leaves wSub pointing past the shared data
            sharedPoints = self._findSharedPoints(wSub, pointCount)
        
        else:
            sharedPoints = None
        
        pd = self.glyphData[glyphIndex] = point_dict.PointDict()
        fw = axial_coordinates.AxialCoordinates.fromwalker
        
        while nTuples:
            tupleSize, tupleIndex = w.unpack("2H")  # w, not wSub!
            embeddedFlag = bool(tupleIndex & 0x8000)
            intermediateFlag = bool(tupleIndex & 0x4000)
            privateFlag = bool(tupleIndex & 0x2000)
            
            if embeddedFlag:
                coord = fw(w, axisOrder=self.axisOrder)
            
            else:
                tupleIndex &= 0x0FFF
                coord = globalCoords[tupleIndex]
            
            if intermediateFlag:
                coord1 = fw(w, axisOrder=self.axisOrder)
                coord2 = fw(w, axisOrder=self.axisOrder)
                effDomain = domain.Domain(coord1, coord2)
            
            else:
                effDomain = None
            
            if privateFlag:
                dPoints = self._fillGlyph_unpack(wSub, pointCount, None)
            else:
                dPoints = self._fillGlyph_unpack(wSub, pointCount, sharedPoints)
            
            # Here dPoints maps point indices to pairs (xDelta, yDelta). This
            # needs to be integrated into self.glyphData.
            
            for pointIndex, (xDelta, yDelta) in dPoints.items():
                if pointIndex not in pd:
                    pd[pointIndex] = deltas_dict.DeltasDict()
                
                dd = pd[pointIndex]
                
                dd[coord] = deltas.Deltas(
                  xDelta,
                  yDelta,
                  effectiveDomain=effDomain)
            
            nTuples -= 1
    
    def _fillGlyph_unpack(self, w, pointCount, prefilled):
        """
        """
        
        if prefilled is None:
            pointIndices = packed_points.PackedPoints.fromwalker(
              w,
              pointCount = pointCount)
        
        else:
            pointIndices = prefilled
        
        # Now that we have the point indices, process the deltas.
        xDeltas = []
        
        while len(xDeltas) < len(pointIndices):
            code = w.unpack("B")
            allZero = bool(code & 0x80)
            allWords = bool(code & 0x40)
            code &= 0x3F
            code += 1
            
            if allZero:
                xDeltas.extend([0] * code)
            
            else:
                fmt = ("h" if allWords else "b")
                xDeltas.extend(w.group(fmt, code))
        
        yDeltas = []
        
        while len(yDeltas) < len(pointIndices):
            code = w.unpack("B")
            allZero = bool(code & 0x80)
            allWords = bool(code & 0x40)
            code &= 0x3F
            code += 1
            
            if allZero:
                yDeltas.extend([0] * code)
            
            else:
                fmt = ("h" if allWords else "b")
                yDeltas.extend(w.group(fmt, code))
        
        r = {}
        
        for point, xDelta, yDelta in zip(pointIndices, xDeltas, yDeltas):
            r[point] = (xDelta, yDelta)
        
        return r
    
    def _fillGlyph_unpack_validated(self, w, pointCount, prefilled, logger):
        """
        """
        
        if prefilled is None:
            pointIndices = packed_points.PackedPoints.fromvalidatedwalker(
              w,
              pointCount = pointCount,
              logger = logger)
            
            if pointIndices is None:
                return None
        
        else:
            pointIndices = prefilled
        
        # Now that we have the point indices, process the deltas.
        xDeltas = []
        
        while len(xDeltas) < len(pointIndices):
            if w.length() < 1:
                logger.error(('V1049', (), "Delta data ended too early."))
                return None
            
            code = w.unpack("B")
            allZero = bool(code & 0x80)
            allWords = bool(code & 0x40)
            code &= 0x3F
            code += 1
            
            if allZero:
                xDeltas.extend([0] * code)
            
            else:
                fmt = ("h" if allWords else "b")
                needed = code * (2 if fmt == 'h' else 1)
                
                if w.length() < needed:
                    logger.error(('V1049', (), "Delta data ended too early."))
                    return None
                
                xDeltas.extend(w.group(fmt, code))
        
        logger.debug(('Vxxxx', (xDeltas,), "xDeltas are %s"))
        yDeltas = []
        
        while len(yDeltas) < len(pointIndices):
            if w.length() < 1:
                logger.error(('V1049', (), "Delta data ended too early."))
                return None
            
            code = w.unpack("B")
            allZero = bool(code & 0x80)
            allWords = bool(code & 0x40)
            code &= 0x3F
            code += 1
            
            if allZero:
                yDeltas.extend([0] * code)
            
            else:
                fmt = ("h" if allWords else "b")
                needed = code * (2 if fmt == 'h' else 1)
                
                if w.length() < needed:
                    logger.error(('V1049', (), "Delta data ended too early."))
                    return None
                
                yDeltas.extend(w.group(fmt, code))
        
        logger.debug(('Vxxxx', (yDeltas,), "yDeltas are %s"))
        r = {}
        
        for point, xDelta, yDelta in zip(pointIndices, xDeltas, yDeltas):
            r[point] = (xDelta, yDelta)
        
        return r
    
    def _fillGlyph_validated(
      self,
      w,
      glyphIndex,
      globalCoords,
      pointCount,
      **kwArgs):
        
        """
        Given a walker whose base is the start of the header for a single
        glyph, add the entry for self.glyphData[glyphIndex]. This does
        validation on the various parts.
        """
        
        logger = kwArgs['logger']
        
        if w.length() < 4:
            logger.error((
              'V1045'
              (),
              "The glyph variation array header ended too soon."))
            
            return False
        
        nTuples, dataOffset = w.unpack("2H")
        logger.debug(('Vxxxx', (nTuples,), "nTuples is %d"))
        logger.debug(('Vxxxx', (dataOffset,), "dataOffset is 0x%04X"))
        
        if (nTuples & 0x7000):
            logger.warning((
              'V1046',
              (nTuples,),
              "The tupleCount is 0x%04X which contains undefined flags."))
        
        sharedPointCase = bool(nTuples & 0x8000)
        nTuples &= 0x0FFF
        
        if not nTuples:
            logger.warning((
              'V1047',
              (),
              "The tupleCount is zero; this is suspicious."))
            
            return True
        
        wSub = w.subWalker(dataOffset)
        
        if sharedPointCase:
            # note the call here leaves wSub pointing past the shared data
            sharedPoints = self._findSharedPoints_validated(
              wSub,
              pointCount,
              logger)
            
            if sharedPoints is None:
                return False
        
        else:
            sharedPoints = None
        
        pd = self.glyphData[glyphIndex] = point_dict.PointDict()
        fvw = axial_coordinates.AxialCoordinates.fromvalidatedwalker
        
        for iTuple in range(nTuples):
            subLogger = logger.getChild("tuple %d" % (iTuple,))
            
            if w.length() < 4:
                subLogger.error((
                  'V1048',
                  (),
                  "Insufficient bytes for the tuple"))
                
                return False
            
            tupleSize, tupleIndex = w.unpack("2H")  # w, not wSub!
            embeddedFlag = bool(tupleIndex & 0x8000)
            intermediateFlag = bool(tupleIndex & 0x4000)
            privateFlag = bool(tupleIndex & 0x2000)
            
            if embeddedFlag:
                coord = fvw(w, axisOrder=self.axisOrder, logger=subLogger)
            
            else:
                tupleIndex &= 0x0FFF
                
                if tupleIndex >= len(globalCoords):
                    logger.error((
                      'Vxxxx',
                      (tupleIndex, len(globalCoords)),
                      "A global coordinate index of %d was encountered, "
                      "but there are only %d global coordinates."))
                    
                    return False
                
                coord = globalCoords[tupleIndex]
            
            if intermediateFlag:
                coord1 = fvw(w, axisOrder=self.axisOrder, logger=subLogger)
                coord2 = fvw(w, axisOrder=self.axisOrder, logger=subLogger)
                effDomain = domain.Domain(coord1, coord2)
            
            else:
                effDomain = None
            
            if privateFlag:
                dPoints = self._fillGlyph_unpack_validated(
                  wSub,
                  pointCount,
                  None,
                  subLogger)
            
            else:
                dPoints = self._fillGlyph_unpack_validated(
                  wSub,
                  pointCount,
                  sharedPoints,
                  subLogger)
            
            if dPoints is None:
                return False
            
            # Here dPoints maps point indices to pairs (xDelta, yDelta). This
            # needs to be integrated into self.glyphData.
            
            for pointIndex, (xDelta, yDelta) in dPoints.items():
                if pointIndex not in pd:
                    pd[pointIndex] = deltas_dict.DeltasDict()
                
                dd = pd[pointIndex]
                
                dd[coord] = deltas.Deltas(
                  xDelta,
                  yDelta,
                  effectiveDomain = effDomain)
            
            nTuples -= 1
        
        return True
    
    def _findGlobalCoords(self, **kwArgs):
        """
        Analyze the coordinates present in the data, and return a dict of them
        that occur in at or above a number of times indicated by the value of
        reuseThreshold. The dict will map the coordinate to its global index,
        where the most frequent have lower global indices.
        """
        
        reuseThreshold = kwArgs.get('reuseThreshold', 10)
        counts = collections.defaultdict(int)
        
        for glyphIndex, pd in self.glyphData.items():
            for dd in pd.values():
                for coord in dd:
                    counts[coord] += 1
        
        toDel = set()
        
        for coord, count in counts.items():
            if count < reuseThreshold:
                toDel.add(coord)
        
        for coord in toDel:
            del counts[coord]
        
        it = sorted(
          iter(counts.items()),
          key = operator.itemgetter(1),
          reverse = True)
        
        if kwArgs.get('debugPrint', False):
            print("Global coordinates:")
            
            for obj, count in it:
                print("  ", count, obj)
        
        return {coord: i for i, (coord, count) in enumerate(it)}
    
    def _findSharedPoints(self, w, pointCount):
        """
        Note that w starts off at the base of the serialized data for this
        glyph; since the shared points are the first thing in this area we use
        this walker directly, so the caller has a walker that has advanced past
        the shared points to the start of the actual data.
        """
        
        return packed_points.PackedPoints.fromwalker(w, pointCount=pointCount)
    
    def _findSharedPoints_validated(self, w, pointCount, logger):
        """
        Note that w starts off at the base of the serialized data for this
        glyph; since the shared points are the first thing in this area we use
        this walker directly, so the caller has a walker that has advanced past
        the shared points to the start of the actual data.
        """
        
        return packed_points.PackedPoints.fromvalidatedwalker(
          w,
          pointCount = pointCount,
          logger = logger)
    
    def buildBinary(self, w, **kwArgs):
        """
        Add the binary data for the Gvar object to the specified writer.
        
        Apart from the usual keyword argument ('stakeValue'), this method also
        supports the 'sharedPointsAllowed' keyword argument (default True).
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        sharingEnabled = kwArgs.pop('sharedPointsAllowed', True)
        e = kwArgs['editor']
        w.add("L", self.VERSION)
        w.add("H", len(self.axisOrder))
        dGlobalCoords = self._findGlobalCoords(**kwArgs)
        w.add("H", len(dGlobalCoords))
        
        if dGlobalCoords:
            globalCoordsStake = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, globalCoordsStake)
        
        else:
            w.add("L", 0)
        
        w.add("H", e.maxp.numGlyphs)
        w.add("H", 1)  # hard-code for 32-bit offsets, for now
        dataStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, dataStake)
        numGlyphs = utilities.getFontGlyphCount(**kwArgs)
        glyphStakes = [w.getNewStake() for i in range(numGlyphs + 1)]
        
        for stake in glyphStakes:
            w.addUnresolvedOffset("L", dataStake, stake)
        
        # Now emit the global coordinates:
        
        if dGlobalCoords:
            w.stakeCurrentWithValue(globalCoordsStake)
            it = sorted(iter(dGlobalCoords.items()), key=operator.itemgetter(1))
            
            for coord, globalIndex in it:
                coord.buildBinary(w, axisOrder=self.axisOrder, **kwArgs)
        
        # Now emit the actual variation data
        
        w.stakeCurrentWithValue(dataStake)
        gd = self.glyphData
        glyfTable = e.glyf
        hmtxTable = e.hmtx
        
        for glyphIndex in range(numGlyphs):
            w.alignToByteMultiple(2)
            w.stakeCurrentWithValue(glyphStakes[glyphIndex])
            
            if glyphIndex not in gd:
                continue
            
            glyphObj = glyfTable[glyphIndex]
            
            # We only skip this glyph if it has neither outline nor advance.
            # Zero-advance accents can still vary, as can the width of a space
            # glyph, so both criteria must be met to be skipped.
            
            if not (glyphObj or hmtxTable[glyphIndex].advance):
                continue
            
            if glyphObj.isComposite:
                pointCount = len(glyphObj.components) + 4
            else:
                pointCount = glyphObj.pointCount(editor=e) + 4
            
            pd = gd[glyphIndex]
            
            if sharingEnabled:
                commonPoints = pd.findCommonPoints()
            else:
                commonPoints = None
            
            invDict = pd.makeInvertDict()
            tupleCount = len(invDict)
            
            if commonPoints is not None:
                tupleCount |= 0x8000
            
            w.add("H", tupleCount)
            sortedCoords = sorted(invDict)
            tupleDataStake = w.getNewStake()
            w.addUnresolvedOffset("H", glyphStakes[glyphIndex], tupleDataStake)
            tupleSizeStakes = []
            privatePoints = []  # bools
            
            for coord in sortedCoords:
                dPointToDelta = invDict[coord]
                tupleSizeStakes.append(w.addDeferredValue("H"))
                mask = 0
                
                if coord not in dGlobalCoords:
                    mask |= 0x8000
                else:
                    mask = dGlobalCoords[coord]
                
                if any(obj.effectiveDomain for obj in dPointToDelta.values()):
                    mask |= 0x4000
                
                if commonPoints is not None and frozenset(dPointToDelta) == commonPoints:
                #if commonPoints is not None and set(dPointToDelta) in commonPoints:
                    privatePoints.append(False)
                
                else:
                    mask |= 0x2000
                    privatePoints.append(True)
                
                w.add("H", mask)
                
                if mask & 0x8000:
                    coord.buildBinary(w)
                
                if mask & 0x4000:
                    # we assume there's one unique domain; check this?
                    domPts = [
                      p
                      for p, delta in dPointToDelta.items()
                      if delta.effectiveDomain]
                    
                    dom = dPointToDelta[domPts[0]]
                    dom.effectiveDomain.edge1.buildBinary(w)
                    dom.effectiveDomain.edge2.buildBinary(w)
            
            # The array header is now done, so put out the shared points (if
            # any), and then stake the start of the actual tuple data.
            
            w.stakeCurrentWithValue(tupleDataStake)
            
            if commonPoints is not None:
                packedCommons = packed_points.PackedPoints(commonPoints)
                packedCommons.buildBinary(w, pointCount=pointCount-4)
            
            # Now that the header is done, emit the actual points/deltas
            
            for t in zip(sortedCoords, tupleSizeStakes, privatePoints):
                coord, stake, isPrivate = t
                wSub = writer.LinkedWriter()
                dPointToDelta = invDict[coord]
                sortedPoints = sorted(dPointToDelta)
                
                if isPrivate:
                    packed_points.PackedPoints(dPointToDelta).buildBinary(
                      wSub,
                      pointCount = pointCount - 4)
                
                # Emit x-deltas, in order, to wSub
                
                vx = [dPointToDelta[i].x for i in sortedPoints]
                self._emitDeltaBand(wSub, vx)
                
                # Emit y-deltas, in order, to wSub
                
                vy = [dPointToDelta[i].y for i in sortedPoints]
                self._emitDeltaBand(wSub, vy)
                
                bs = wSub.binaryString()
                w.setDeferredValue(stake, "H", len(bs))
                w.addString(bs)
        
        w.alignToByteMultiple(2)
        w.stakeCurrentWithValue(glyphStakes[-1])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('gvar')
        else:
            logger = utilities.makeDoctestLogger('gvar')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        e = kwArgs['editor']
        
        if not e.reallyHas('fvar'):
            logger.error((
              'V1037',
              (),
              "Font has a 'gvar' table but no 'fvar' table; this is "
              "not a valid state."))
            
            return None
        
        fvarObj = e.fvar
        ao = fvarObj.axisOrder
        r = cls(axisOrder=ao)
        origTableSize = w.length()
        
        if origTableSize < 20:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        t = w.unpack("L2HL2HL")
        vers, axisCount, coordCount, coordOff, glyphCount, flags, dataOff = t
        logger.debug(('Vxxxx', (vers,), "Version is 0x%08X"))
        logger.debug(('Vxxxx', (axisCount,), "Axis count is %d"))
        logger.debug(('Vxxxx', (coordCount,), "Global coord count is %d"))
        logger.debug(('Vxxxx', (coordOff,), "Global coord offset is 0x%08X"))
        logger.debug(('Vxxxx', (glyphCount,), "Glyph count is %d"))
        logger.debug(('Vxxxx', (flags,), "Flags is 0x%04X"))
        logger.debug(('Vxxxx', (dataOff,), "Data offset is 0x%08X"))
        
        if vers != r.VERSION:
            logger.error((
              'V1038',
              (r.VERSION, vers,),
              "Unknown 'gvar' version; was expecting 0x%08X but "
              "got 0x%08X instead."))
            
            return None
        
        if axisCount != len(ao):
            logger.error((
              'V1039',
              (len(ao), axisCount),
              "Mismatch between the axis counts in 'fvar' (%d) and "
              "'gvar' (%d)."))
            
            return None
        
        if glyphCount != utilities.getFontGlyphCount(**kwArgs):
            logger.error((
              'V1040',
              (),
              "Mismatch between the 'maxp' and 'gvar' glyph counts."))
            
            return None
        
        if flags not in {0, 1}:
            logger.warning((
              'V1041',
              (flags,),
              "The 'gvar' flags value is 0x%04X; this includes bits "
              "that are not defined. These will be ignored."))
        
        # Check the offsets for reasonableness
        
        offsetSize = (4 if (flags & 1) else 2)
        
        if coordCount:
            globStop = coordOff + (coordCount * len(ao) * 2)
            lowBounds = 20 + (glyphCount + 1) * offsetSize
            
            if (coordOff < lowBounds) or (globStop > origTableSize):
                logger.error((
                  'V1042',
                  (),
                  "The 'gvar' global coordinates do not fit within the bounds "
                  "of the entire 'gvar' table."))
                
                return None
        
        if (dataOff < 20) or (dataOff >= origTableSize):
            logger.error((
              'V1043',
              (),
              "The 'gvar' variations data starting offset is outside "
              "the bounds of the entire 'gvar' table"))
            
            return None
        
        # Read the global coordinates (if any)
        
        globalCoords = []
        
        if coordCount:
            wSub = w.subWalker(coordOff)
            fvw = axial_coordinates.AxialCoordinates.fromvalidatedwalker
            globalCoords = [None] * coordCount
            
            for i in range(coordCount):
                subLogger = logger.getChild("globalCoord %d" % (i,))
                obj = fvw(wSub, axisOrder=ao, logger=subLogger)
                
                if obj is None:
                    return None
                
                globalCoords[i] = obj
        
        # Get the offsets to the actual glyph variation data
        
        if w.length() < offsetSize * (glyphCount + 1):
            logger.error((
              'V1043',
              (),
              "The 'gvar' glyph variation array extends past the "
              "table boundaries."))
            
            return None
        
        offsets = w.group("HL"[flags & 1], glyphCount + 1)
        
        if offsetSize == 2:
            offsets = [2 * n for n in offsets]
        
        if list(offsets) != sorted(offsets):
            logger.error((
              'V1044',
              (),
              "The per-glyph offsets are not monotonically increasing."))
            
            return None
        
        for glyphIndex, (off1, off2) in enumerate(utilities.pairwise(offsets)):
            w.align(2)
            
            if off1 == off2:
                continue
            
            # For now I'm assuming the presence of a 'glyf' table...
            
            glyphObj = e.glyf[glyphIndex]
            
            if glyphObj.isComposite:
                pointCount = len(glyphObj.components)
            else:
                pointCount = glyphObj.pointCount()
            
            wSub = w.subWalker(off1 + dataOff)
            subLogger = logger.getChild("glyph %d" % (glyphIndex,))
            
            wasOK = r._fillGlyph_validated(
              wSub,
              glyphIndex,
              globalCoords,
              pointCount,
              logger = subLogger,
              **kwArgs)
            
            if not wasOK:
                return None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        e = kwArgs['editor']
        fvarObj = e.fvar
        ao = fvarObj.axisOrder
        r = cls(axisOrder=ao)
        t = w.unpack("L2HL2HL")
        vers, axisCount, coordCount, coordOff, glyphCount, flags, dataOff = t
        
        if vers != cls.VERSION:
            raise ValueError("Unknown 'gvar' version: 0x%08X" % (vers,))
        
        assert len(ao) == axisCount, "Mismatch in number of axes!"
        #assert editor.maxp.numGlyphs == glyphCount
        wSub = w.subWalker(coordOff)
        globalCoords = []
        fw = axial_coordinates.AxialCoordinates.fromwalker
        
        while coordCount:
            globalCoords.append(fw(wSub, axisOrder=ao))
            coordCount -= 1
        
        fmt = ("L" if (flags & 1) else "H")
        offsets = w.group(fmt, glyphCount + 1)
        
        if fmt == "H":
            offsets = [2 * n for n in offsets]
        
        if kwArgs.get('showHexOffsets', False):
            print("Per-glyph 'gvar' offsets:")
            
            for t in enumerate(offsets):
                print("  %d: 0x%08X" % t)
        
        for glyphIndex, (off1, off2) in enumerate(utilities.pairwise(offsets)):
            w.align(2)
            
            if off1 == off2:
                continue
            
            glyphObj = e.glyf[glyphIndex]
            
            if glyphObj.isComposite:
                pointCount = len(glyphObj.components)
            else:
                pointCount = glyphObj.pointCount()
            
            wSub = w.subWalker(off1 + dataOff)
            r._fillGlyph(wSub, glyphIndex, globalCoords, pointCount, **kwArgs)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

