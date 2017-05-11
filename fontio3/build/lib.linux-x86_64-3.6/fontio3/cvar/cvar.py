#
# cvar.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the 'cvar' table, used in TrueType variations fonts.
"""

# System imports
import itertools

# Other imports
from fontio3 import utilities
from fontio3.cvar import deltadict
from fontio3.fontdata import mapmeta
from fontio3.gvar import axial_coordinates, packed_points
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

class Cvar(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing 'cvar' tables.
    """
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "CVT %d" % (i,)),
        item_pprintlabelpresort = True,
        item_renumbercvtsdirectkeys = True)
    
    attrSpec = dict(
        axisOrder = dict(
            attr_pprintfunc = _pprint_axisOrder))
    
    VERSION = 0x10000
    
    #
    # Methods
    #
    
    @staticmethod
    def _packDeltas(w, v):
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
    
    @staticmethod
    def _unpackCVTs(w, e):
        fontCVTCount = len(e['cvt '])
        totalCVTs = w.unpack("B")
        cvtIndices = []
        
        if not totalCVTs:
            cvtIndices = list(range(fontCVTCount))
        elif totalCVTs > 127:
            totalCVTs = (totalCVTs - 128) * 256 + w.unpack("B")
        
        while totalCVTs:  # if zero, already filled out cvtIndices
            runCount = w.unpack("B")
            fmt = "BH"[runCount > 127]
            runCount = (runCount & 0x7F) + 1
            
            # The data here are not CVT indices directly, but packed CVT indices,
            # stored as deltas from the previous CVT index (except the first).
            
            for n in w.group(fmt, runCount):
                if not cvtIndices:
                    cvtIndices.append(n)
                else:
                    cvtIndices.append(cvtIndices[-1] + n)
            
            totalCVTs -= runCount
        
        return cvtIndices
    
    @staticmethod
    def _unpackCVTs_validated(w, e, logger):
        fontCVTCount = len(e['cvt '])
        
        if w.length() < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        totalCVTs = w.unpack("B")
        cvtIndices = []
        
        if not totalCVTs:
            cvtIndices = list(range(fontCVTCount))
        
        elif totalCVTs > 127:
            if w.length() < 1:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            totalCVTs = (totalCVTs - 128) * 256 + w.unpack("B")
        
        while totalCVTs:  # if zero, already filled out cvtIndices
            if w.length() < 1:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            runCount = w.unpack("B")
            fmt = "BH"[runCount > 127]
            runCount = (runCount & 0x7F) + 1
            
            # The data here are not CVT indices directly, but packed CVT indices,
            # stored as deltas from the previous CVT index (except the first).
            
            if w.length() < runCount * (2 if fmt == 'H' else 1):
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            for n in w.group(fmt, runCount):
                if not cvtIndices:
                    cvtIndices.append(n)
                else:
                    cvtIndices.append(cvtIndices[-1] + n)
            
            totalCVTs -= runCount
        
        return cvtIndices
    
    @staticmethod
    def _unpackDeltas(w, cvtIndices):
        r = []
        
        while len(r) < len(cvtIndices):
            code = w.unpack("B")
            allZero = bool(code & 0x80)
            allWords = bool(code & 0x40)
            code &= 0x3F
            code += 1
            
            if allZero:
                r.extend([0] * code)
            
            else:
                fmt = ("h" if allWords else "b")
                r.extend(w.group(fmt, code))
        
        return r
    
    @staticmethod
    def _unpackDeltas_validated(w, cvtIndices, logger):
        r = []
        
        while len(r) < len(cvtIndices):
            if w.length() < 1:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            code = w.unpack("B")
            allZero = bool(code & 0x80)
            allWords = bool(code & 0x40)
            code &= 0x3F
            code += 1
            
            if allZero:
                r.extend([0] * code)
            
            else:
                if w.length() < code * (2 if allWords else 1):
                    logger.error(('V0004', (), "Insufficient bytes."))
                    return None
                
                fmt = ("h" if allWords else "b")
                r.extend(w.group(fmt, code))
        
        return r
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Cvar object to the specified writer.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", self.VERSION)
        invDict = self.makeInvertDict()
        sortedCoords = sorted(invDict)
        w.add("H", len(invDict))
        dataStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, dataStake)
        sizeStakes = []
        
        for coord in sortedCoords:
            sizeStakes.append(w.addDeferredValue("H"))
            # we hardwire the flags to 0xA000.
            w.add("H", 0xA000)
            coord.buildBinary(w, axisOrder=self.axisOrder)
        
        # headers are done; now output the data
        w.stakeCurrentWithValue(dataStake)
        
        for coord, stake in zip(sortedCoords, sizeStakes):
            wWork = writer.LinkedWriter()
            dCVTtoDelta = invDict[coord]
            sortedCVTs = sorted(dCVTtoDelta)
            ppObj = packed_points.PackedPoints(sortedCVTs)
            ppObj.buildBinary(wWork, pointCount=32767)
            deltas = [dCVTtoDelta[c] for c in sortedCVTs]
            self._packDeltas(wWork, deltas)
            bs = wWork.binaryString()
            w.setDeferredValue(stake, "H", len(bs))
            w.addString(bs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('cvar')
        else:
            logger = utilities.makeDoctestLogger('cvar')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        e = kwArgs['editor']
        
        if not e.reallyHas('fvar'):
            logger.error((
              'V1037',
              (),
              "Font has a 'cvar' table but no 'fvar' table; this is "
              "not a valid state."))
            
            return None
        
        fvarObj = e.fvar
        ao = fvarObj.axisOrder
        tableSize = w.length()
        
        if tableSize < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        vers, tupleCount, dataOffset = w.unpack("L2H")
        
        if vers != cls.VERSION:
            logger.error((
              'V1051',
              (cls.VERSION, vers),
              "Was expecting version 0x%08X, but got 0x%08X instead."))
            
            return None
        
        if tupleCount & 0x8000:
            logger.error((
              'V1052',
              (),
              "The 'cvar' table's tupleCount field has the 0x8000 bit set. "
              "This is not support for 'cvar' (only for 'gvar')."))
            
            return None
        
        overhead = 8 + (4 + 2 * len(ao)) * tupleCount
        
        if dataOffset < overhead or dataOffset > tableSize:
            logger.error((
              'V1054',
              (dataOffset,),
              "The dataOffset value 0x%04X appears to be invalid."))
            
            return None
        
        tupleHeaders = []
        afvw = axial_coordinates.AxialCoordinates.fromvalidatedwalker
        
        for i in range(tupleCount):
            subLogger = logger.getChild("tuple header %d" % (i,))
            
            if w.length() < 4:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            tupleSize, tupleIndex = w.unpack("2H")
            
            if (tupleIndex & 0xF000) != 0xA000:
                subLogger.error((
                  'V1053',
                  (tupleIndex & 0xF000,),
                  "Expected tupleIndex flags to be 0xA000, but got 0x%04X."))
                
                return None
            
            coords = afvw(w, axisOrder=ao, logger=subLogger)
            tupleHeaders.append((tupleSize, coords))
        
        wData = w.subWalker(dataOffset)
        r = cls({}, axisOrder=ao)
        DD = deltadict.DeltaDict
        
        for tupleSize, coords in tupleHeaders:
            subLogger = logger.getChild("coord %s" % (coords,))
            
            if wData.length() < tupleSize:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            startOffset = wData.getOffset()
            cvtIndices = cls._unpackCVTs_validated(wData, e, subLogger)
            
            if cvtIndices is None:
                return None
            
            deltas = cls._unpackDeltas_validated(wData, cvtIndices, subLogger)
            
            if deltas is None:
                return None
            
            alignSkip = (wData.getOffset() - startOffset) - tupleSize
            
            for cvtIndex, dlt in zip(cvtIndices, deltas):
                if cvtIndex not in r:
                    r[cvtIndex] = DD()
                
                r[cvtIndex][coords] = dlt
            
            if alignSkip:
                wData.skip(alignSkip)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        e = kwArgs['editor']
        fvarObj = e.fvar
        ao = fvarObj.axisOrder
        vers, tupleCount, dataOffset = w.unpack("L2H")
        
        if vers != cls.VERSION:
            raise ValueError("Unknown 'cvar' version!")
        
        if tupleCount & 0x8000:
            raise NotImplementedError("CVT index sharing not implemented!")
        
        tupleHeaders = []
        afw = axial_coordinates.AxialCoordinates.fromwalker
        
        while tupleCount:
            tupleSize, tupleIndex = w.unpack("2H")
            
            if tupleIndex & 0x8000:
                tupleIndex &= 0x7FFF
                coords = afw(w, axisOrder=ao)
            
            else:
                raise NotImplementedError("Non-embedded coordinates not implemented!")
            
            if tupleIndex & 0x4000:
                raise NotImplementedError("Intermediate coordinates not implemented!")
            
            if tupleIndex & 0x2000:
                tupleIndex &= 0xDFFF
                isPrivatePoints = True
            
            else:
                raise NotImplementedError("Non-private points not implemented!")
            
            tupleHeaders.append((tupleSize, coords, isPrivatePoints))
            tupleCount -= 1
        
        wData = w.subWalker(dataOffset)
        r = cls({}, axisOrder=ao)
        DD = deltadict.DeltaDict
        
        for tupleSize, coords, isPrivatePoints in tupleHeaders:
            startOffset = wData.getOffset()
            cvtIndices = cls._unpackCVTs(wData, e)
            deltas = cls._unpackDeltas(wData, cvtIndices)
            alignSkip = (wData.getOffset() - startOffset) - tupleSize
            
            for cvtIndex, dlt in zip(cvtIndices, deltas):
                if cvtIndex not in r:
                    r[cvtIndex] = DD()
                
                r[cvtIndex][coords] = dlt
            
            if alignSkip:
                wData.skip(alignSkip)
        
        return r
    
    def makeInvertDict(self):
        """
        Makes and returns a simple dict of dicts. Normally, a Cvar object
        maps CVT indices to DeltaDict objects. This method inverts that,
        returning a dict of AxialCoordinate objects mapping to subdicts, which
        in turn map cvts to Delta objects.
        """
        
        r = {}
        
        for cvtIndex, ddObj in self.items():
            for coord, deltasObj in ddObj.items():
                r.setdefault(coord, {})[cvtIndex] = deltasObj
        
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

