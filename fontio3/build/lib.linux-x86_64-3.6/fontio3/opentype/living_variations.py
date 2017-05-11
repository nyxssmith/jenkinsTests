#
# living_variations.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Versions of various variation-related data structures that are used in living
fontio3 objects. Note that, for the most part, these classes do not define
fromwalker() or buildBinary() methods -- those details are handled by the
classes defined in opentype/item_variation_store.py.
"""

# System imports
import collections
import operator

# Other imports
from fontio3.fontdata import keymeta, mapmeta, seqmeta, setmeta
from fontio3.gvar import axial_coordinate
from fontio3.utilities import filewriter

# -----------------------------------------------------------------------------

#
# Functions
#

def _findBestRegionOrder(iterable):
    """
    Given an iterable of LivingDeltas, return a tuple whose first element is a
    tuple of LivingRegions whose ordering allows the smallest binary data size;
    and whose second element is a count of how many of the initial members of
    the first tuple need 16-bit representation for their deltas.
    
    Note that decisions as to whether a group of LivingDeltas could be split
    into multiple ItemVariationData subtables, perhaps saving space, is not
    made here. It could be done as a post-process. This function puts
    everything into a single ItemVariationData subtable.
    
    >>> reg1 = {'wght': (-0.75, 0.0, 1.0), 'wdth': (-1.0, 0.25, 0.75)}
    >>> key1 = LivingRegion.fromdict(reg1)
    >>> mem1 = LivingDeltasMember((key1, -180))
    >>> ld1 = LivingDeltas({mem1})
    >>> reg23 = {'wght': (0.5, 0.75, 1.0), 'wdth': (-1.0, -0.75, -0.5)}
    >>> key23 = LivingRegion.fromdict(reg23)
    >>> mem2 = LivingDeltasMember((key23, -18))
    >>> ld2 = LivingDeltas({mem2})
    >>> mem3 = LivingDeltasMember((key23, -25))
    >>> ld3 = LivingDeltas({mem3})
    >>> tLR, num16 = _findBestRegionOrder([ld1, ld2, ld3])
    >>> print(len(tLR), num16)
    2 1
    >>> for lr in tLR:
    ...   print(lr)
    'wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0)
    'wdth': (start -1.0, peak -0.75, end -0.5), 'wght': (start 0.5, peak 0.75, end 1.0)
    """
    
    dUse8 = set()
    dUse16 = set()
    lrCumul = set()
    
    for ld in iterable:
        for lr, delta in ld:
            lrCumul.add(lr)
            
            if -128 <= delta < 128:
                dUse8.add(lr)
            else:
                dUse16.add(lr)
    
    only8s = {r for r in lrCumul if (r in dUse8) and (r not in dUse16)}
    v8 = sorted(only8s, key=str)
    v16 = sorted(lrCumul - only8s, key=str)
    return (tuple(v16 + v8), len(v16))

def _LivingDeltas_pprint(p, obj, **kwArgs):
    for rgn, dlt in sorted(obj, key=operator.itemgetter(1)):
        s = "A delta of %d applies in region %s" % (dlt, str(rgn))
        p(s)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class IVS(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dicts mapping (outer-level index, inner-level index) pairs to LivingDeltas
    objects. This is used to convert the indices in raw table data to living
    references.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda k: "(outer %d, inner %d)" % k),
        item_pprintlabelpresort = True)
    
    #
    # Methods
    #
    
    @staticmethod
    def binaryStringFromDeltas(it, **kwArgs):
        """
        Given an iterator over LivingDeltas objects, return a binary
        string representing the item variation store, along with a map from
        LivingDeltas to (outerIndex, innerIndex) pairs.
        
        >>> lr1 = LivingRegion.fromdict({b'wght': (-1.0, -1.0, 0.0)})
        >>> lr2 = LivingRegion.fromdict({b'wght': (0.5, 0.75, 1.0)})
        >>> lr3 = LivingRegion.fromdict({b'wght': (0.0, 0.25, 0.5)})
        >>> ldm1 = LivingDeltasMember((lr1, -150))
        >>> ldm2 = LivingDeltasMember((lr2, 100))
        >>> ldm3 = LivingDeltasMember((lr1, 150))
        >>> ldm4 = LivingDeltasMember((lr3, -75))
        >>> ld1 = LivingDeltas({ldm1})
        >>> ld2 = LivingDeltas({ldm2, ldm3})
        >>> ld3 = LivingDeltas({ldm4})
        >>> obj = IVS({(0, 0): ld1, (1, 0): ld2, (2, 0): ld3})
        >>> obj.pprint()
        (outer 0, inner 0):
          A delta of -150 applies in region 'b'wght'': (start -1.0, peak -1.0, end 0.0)
        (outer 1, inner 0):
          A delta of 100 applies in region 'b'wght'': (start 0.5, peak 0.75, end 1.0)
          A delta of 150 applies in region 'b'wght'': (start -1.0, peak -1.0, end 0.0)
        (outer 2, inner 0):
          A delta of -75 applies in region 'b'wght'': (start 0.0, peak 0.25, end 0.5)
        
        >>> bs, d = obj.binaryStringFromDeltas([ld1, ld2, ld3], axisOrder=(b'wght',))
        >>> len(bs)
        74
        
        >>> obj2 = IVS.frombytes(bs, axisOrder=('wght',))
        >>> sorted(obj2) == sorted(obj)
        True
        """
        
        w = filewriter.LinkedFileWriter()
        stakeValue = w.stakeCurrent()
        ao = kwArgs['axisOrder']
        lrCumul = set()  # all LivingRegions
        dLRtoLD = collections.defaultdict(set)  # frozenset(LivingRegions) -> set of LivingDeltas
        
        for livingDelta in it:
            allLivingRegions = frozenset(t[0] for t in livingDelta)
            lrCumul.update(allLivingRegions)
            dLRtoLD[allLivingRegions].add(livingDelta)
        
        if not lrCumul:
            return b''
        
        allLens = {len(obj) for obj in lrCumul}
        
        if len(allLens) > 1:
            raise ValueError("LivingRegions of inconsistent length!")
        
        if next(iter(allLens)) != len(ao):
            raise ValueError("LivingRegion length doesn't match axis count!")
        
        w.add("H", 1)  # format
        vrlStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, vrlStake)
        itSrt = sorted(lrCumul, key=str)
        dLRtoIndex = {lr: i for i, lr in enumerate(itSrt)}
        
        # Note that dLRtoLD is essentially dOuters, and so its length is what
        # goes into the itemVariationDataCount field
        
        w.add("H", len(dLRtoLD))
        ivdStakes = [w.getNewStake() for obj in dLRtoLD]
        
        for stake in ivdStakes:
            w.addUnresolvedOffset("L", stakeValue, stake)
        
        # Write each ItemVariationData object
        
        rLDtoOuterInner = {}
        itSrt = sorted(dLRtoLD.items(), key=str)
        
        for outerIndex, (lrSet, ldSet) in enumerate(itSrt):
            w.stakeCurrentWithValue(ivdStakes[outerIndex])
            lrTuple, need16 = _findBestRegionOrder(ldSet)
            w.add("3H", len(ldSet), need16, len(lrTuple))
            w.addGroup("H", (dLRtoIndex[lr] for lr in lrTuple))
            
            for innerIndex, ld in enumerate(sorted(ldSet, key=str)):
                rLDtoOuterInner[ld] = (outerIndex, innerIndex)
                d = dict(ld)  # LivingRegion -> FUnit delta
                
                for i, lr in enumerate(lrTuple):
                    fmt = ('h' if i < need16 else 'b')
                    w.add(fmt, d[lr])
        
        # Now output the VariationRegionList
        
        w.stakeCurrentWithValue(vrlStake)
        w.add("H", len(ao))
        w.add("H", len(dLRtoIndex))
        
        for obj in sorted(dLRtoIndex.items(), key=operator.itemgetter(1)):
            obj[0].buildBinary(w, axisOrder=ao)
        
        r = w.binaryString()
        return r, rLDtoOuterInner
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns an IVS object from the specified walker. Note that
        clients will usually just use the mappings contained in this object to
        set up their objects, and then discard the IVS. It's not really set up
        to be kept around; rather, reconstuct it before writing.
        
        >>> bs = bytes.fromhex(
        ...   "0001"                            # offset 00: format
        ...   "0000000C"                        # offset 02: offset to regions
        ...   "0001"                            # offset 06: outer count
        ...   "00000028"                        # offset 08: offset to outer 0
        ...   "0002"                            # offset 0C: (start of regions) axisCount
        ...   "0002"                            # offset 0E: regionCount
        ...   "E000 1000 4000 C000 0000 4000"   # offset 10: region 0
        ...   "C000 C800 E000 C000 1000 2000"   # offset 1C: region 1
        ...   "0001"                            # offset 28: (start of outer 0) itemCount
        ...   "0001"                            # offset 2A: shortDeltaCount
        ...   "0002"                            # offset 2C: regionCount
        ...   "0001 0000"                       # offset 2E: region indices
        ...   "FF4C 45")                        # offset 32: inner 0 deltas
        >>> IVS.frombytes(bs, axisOrder=('wght', 'wdth')).pprint()
        (outer 0, inner 0):
          A delta of -180 applies in region 'wdth': (start -1.0, peak 0.25, end 0.5), 'wght': (start -1.0, peak -0.875, end -0.5)
          A delta of 69 applies in region 'wdth': (start -1.0, peak 0.0, end 1.0), 'wght': (start -0.5, peak 0.25, end 1.0)
        """
        
        axisOrder = kwArgs['axisOrder']
        format, regOffset, dataCount = w.unpack("HLH")
        
        if format != 1:
            raise ValueError("Unknown item variation store format!")
        
        # Make the region list
        
        wReg = w.subWalker(regOffset)
        axisCount, regCount = wReg.unpack("2H")
        assert axisCount == len(axisOrder)
        regList = [None] * regCount
        fd = LivingRegion.fromdict
        
        for i in range(regCount):
            d = {
              tag: [n / 16384 for n in wReg.group("h", 3)]
              for tag in axisOrder}
            
            regList[i] = fd(d)
        
        # Process the actual deltas
        
        outerOffsets = w.group("L", dataCount)
        r = cls()
        
        for outerIndex, outerOffset in enumerate(outerOffsets):
            wOut = w.subWalker(outerOffset)
            itemCount, shortCount, regIndexCount = wOut.unpack("3H")
            regIndices = wOut.group("H", regIndexCount)
            
            if shortCount:
                if shortCount == regIndexCount:
                    fmt = "%dh" % (regIndexCount,)
                else:
                    fmt = "%dh%db" % (shortCount, regIndexCount - shortCount)
            else:
                fmt = "%db" % (regIndexCount,)
            
            for innerIndex in range(itemCount):
                deltas = wOut.unpack(fmt, coerce=False)
                ds = set()
                
                for i, regIndex in enumerate(regIndices):
                    dsm = LivingDeltasMember((regList[regIndex], deltas[i]))
                    ds.add(dsm)
                
                r[(outerIndex, innerIndex)] = LivingDeltas(ds)
        
        return r


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns an IVS object from the specified walker, like
        fromwalker, but with validation. A 'logger' keyword arg is required.
        
        >>> bs = bytes.fromhex(
        ...   "0001"                            # offset 00: format
        ...   "0000000C"                        # offset 02: offset to regions
        ...   "0001"                            # offset 06: outer count
        ...   "00000028"                        # offset 08: offset to outer 0
        ...   "0002"                            # offset 0C: (start of regions) axisCount
        ...   "0002"                            # offset 0E: regionCount
        ...   "E000 1000 4000 C000 0000 4000"   # offset 10: region 0
        ...   "C000 C800 E000 C000 1000 2000"   # offset 1C: region 1
        ...   "0001"                            # offset 28: (start of outer 0) itemCount
        ...   "0001"                            # offset 2A: shortDeltaCount
        ...   "0002"                            # offset 2C: regionCount
        ...   "0001 0000"                       # offset 2E: region indices
        ...   "FF4C 45")                        # offset 32: inner 0 deltas
        >>> logger = utilities.makeDoctestLogger('test')
        >>> obj = IVS.fromvalidatedbytes(bs, axisOrder=('wght', 'wdth'), logger=logger)
        test.IVS - DEBUG - Walker has 53 remaining bytes.
        test.IVS - INFO - Format 1
        test.IVS - DEBUG - Data count is 1
        test.IVS - DEBUG - Axis count is 2
        test.IVS - DEBUG - Region count is 2
        test.IVS - DEBUG - Delta (0, 0)

        >>> obj.pprint()
        (outer 0, inner 0):
          A delta of -180 applies in region 'wdth': (start -1.0, peak 0.25, end 0.5), 'wght': (start -1.0, peak -0.875, end -0.5)
          A delta of 69 applies in region 'wdth': (start -1.0, peak 0.0, end 1.0), 'wght': (start -0.5, peak 0.25, end 1.0)
        """
        
        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('IVS')
        else:
            logger = logger.getChild('IVS')

        axisOrder = kwArgs['axisOrder']

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 8:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes for item variation store."))
            return None

        format, regOffset, dataCount = w.unpack("HLH")

        if format != 1:
            logger.error((
              'Vxxxx',
              (format,),
              "Unknown item variation store format!"))
            return None
            
        else:
            logger.info((
              'Vxxxx',
              (format,),
              "Format %d"))

        if regOffset > w.length():
            logger.error((
              'V0004',
              (),
              "Region offset extends past end of table!"))
            return None

        logger.debug((
          'Vxxxx',
          (dataCount,),
          "Data count is %d"))

        # Make the region list
        
        wReg = w.subWalker(regOffset)

        if wReg.length() < 4:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes for region list."))
            return None

        axisCount, regCount = wReg.unpack("2H")
 
        if axisCount != len(axisOrder):
            logger.error((
              'Vxxxx',
              (axisCount, len(axisOrder)),
              "Axis count %d does not match size of axisOrder %d!"))
            return None

        logger.debug(('Vxxxx', (axisCount,), "Axis count is %d"))
        logger.debug(('Vxxxx', (regCount,), "Region count is %d"))
 
        regList = [None] * regCount
        fd = LivingRegion.fromdict
        
        for i in range(regCount):
            d = {
              tag: [n / 16384 for n in wReg.group("h", 3)]
              for tag in axisOrder}
            
            regList[i] = fd(d)
        
        # Process the actual deltas
        
        outerOffsets = w.group("L", dataCount)
        r = cls()
        
        for outerIndex, outerOffset in enumerate(outerOffsets):
            wOut = w.subWalker(outerOffset)
            itemCount, shortCount, regIndexCount = wOut.unpack("3H")
            regIndices = wOut.group("H", regIndexCount)
            
            if shortCount:
                if shortCount == regIndexCount:
                    fmt = "%dh" % (regIndexCount,)
                else:
                    fmt = "%dh%db" % (shortCount, regIndexCount - shortCount)
            else:
                fmt = "%db" % (regIndexCount,)
            
            for innerIndex in range(itemCount):
                deltas = wOut.unpack(fmt, coerce=False)
                ds = set()
                
                for i, regIndex in enumerate(regIndices):
                    dsm = LivingDeltasMember((regList[regIndex], deltas[i]))
                    ds.add(dsm)

                logger.debug(('Vxxxx', (outerIndex, innerIndex), "Delta (%d, %d)"))
                r[(outerIndex, innerIndex)] = LivingDeltas(ds)
        
        return r

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class LivingAxialCoordinate(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing a complete coordinate (point within the design space)
    with an AcialCoordinate for each axis. These are frozensets of
    LivingAxialCoordinateMembers.
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_followsprotocol = True,
        set_showpresorted = True)
    
    #
    # Methods
    #
    
    def __str__(self):
        sv = []
        
        for t in sorted(self, key=operator.itemgetter(0)):
            sv.append("'%s': %s" % t)
        
        return ', '.join(sv)
    
    def asCanonicalTuple(self, ao):
        """
        Given an axisOrder, returns a tuple representing this LAC with the
        coordinates in that order.
        
        >>> d = {'wght': -0.75, 'wdth': 1.0}
        >>> obj = LivingAxialCoordinate.fromdict(d)
        >>> obj.asCanonicalTuple(('wght', 'wdth'))
        (-0.75, 1.0)
        """
        
        d = dict(self)
        return tuple(float(d[k]) for k in ao)
    
    @classmethod
    def fromdict(cls, d, **kwArgs):
        """
        Utility method to create a LivingAxialCoordinate from a simple dict.
        
        >>> d = {'wght': -0.75, 'wdth': 1.0}
        >>> print(LivingAxialCoordinate.fromdict(d))
        'wdth': 1.0, 'wght': -0.75
        """
        
        AC = axial_coordinate.AxialCoordinate
        LACM = LivingAxialCoordinateMember
        d2 = {k: AC(v) for k, v in d.items()}
        return cls(LACM(t) for t in d2.items())

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class LivingAxialCoordinateMember(tuple, metaclass=keymeta.FontDataMetaclass):
    """
    These are tuples comprising two members: an axis tag string, and a
    AxialCoordinate object.
    """
    
    #
    # Class definition variables
    #
    
    itemSpec = (
        dict(),
        dict(item_followsprotocol = True))

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

_LAR = collections.namedtuple(
  "_LAR",
  ['start', 'peak', 'end'])

class LivingAxialRegion(_LAR, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a single region (that is, start, peak, and end
    coordinate values) as used in the living forms of the variation-specific
    objects. These are named tuples comprising exactly three AxialCoordinate
    values: start, peak, and end.
    
    >>> AC = axial_coordinate.AxialCoordinate
    >>> print(LivingAxialRegion(AC(-0.5), AC(0.25), AC(1.0)))
    (start -0.5, peak 0.25, end 1.0)
    >>> LivingAxialRegion(AC(-0.5), AC(0.25), AC(1.0)).pprint()
    (start -0.5, peak 0.25, end 1.0)
    
    Note that the values in this tuple should be AxialCoordinate values, and
    not simply floats; item_followsprotocol is True here.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        seq_fixedlength = 3,
        seq_pprintfunc = (lambda p, obj, **k: p(str(obj))))
    
    #
    # Methods
    #
    
    def __str__(self):
        return "(start %s, peak %s, end %s)" % self
    
    def buildBinary(self, w, **kwArgs):
        """
        """
        
        self.start.buildBinary(w)
        self.peak.buildBinary(w)
        self.end.buildBinary(w)
    
    def intersects(self, other):
        """
        Returns True if the two LivingAxialRegions intersect; False otherwise.
        Note that a single-point intersection at zero is treated as a
        non-intersection; any other single-point intersections return True.
        
        >>> AC = axial_coordinate.AxialCoordinate
        >>> LAR = LivingAxialRegion
        >>> LAR(AC(-1), AC(-0.5), AC(0)).intersects(LAR(AC(-0.75), AC(-0.5), AC(-0.25)))
        True
        >>> LAR(AC(-0.75), AC(-0.5), AC(-0.25)).intersects(LAR(AC(-1), AC(-0.5), AC(0)))
        True
        
        >>> LAR(AC(-1), AC(-0.5), AC(0)).intersects(LAR(AC(0.25), AC(0.5), AC(0.75)))
        False
        >>> LAR(AC(0.25), AC(0.5), AC(0.75)).intersects(LAR(AC(-1), AC(-0.5), AC(0)))
        False
        
        >>> LAR(AC(-1), AC(-0.75), AC(-0.5)).intersects(LAR(AC(-0.5), AC(-0.25), AC(0)))
        True
        >>> LAR(AC(-0.5), AC(-0.25), AC(0)).intersects(LAR(AC(-1), AC(-0.75), AC(-0.5)))
        True
        
        >>> LAR(AC(-1), AC(-0.5), AC(0)).intersects(LAR(AC(0), AC(0.5), AC(1)))
        False
        >>> LAR(AC(0), AC(0.5), AC(1)).intersects(LAR(AC(-1), AC(-0.5), AC(0)))
        False
        """
        
        if (self.start > other.end) or (other.start > self.end):
            return False
        
        if (self.start == other.end) and (not other.end):
            return False
        
        if (other.start == self.end) and (not self.end):
            return False
        
        return True

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class LivingDeltas(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    These are the top-level objects that other tables, like MVAR and HVAR,
    refer to in order to give variation deltas for various regions. These are
    frozensets of LivingDeltaMember objects.
    
    Think of these as single Delta-set rows in terms of the binary data.
    
    >>> d = {'wght': (-0.75, 0.0, 1.0), 'wdth': (-1.0, 0.25, 0.75)}
    >>> key = LivingRegion.fromdict(d)
    >>> LivingDeltas({LivingDeltasMember((key, -180))}).pprint()
    A delta of -180 applies in region 'wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0)
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_followsprotocol = True,
        set_pprintfunc = _LivingDeltas_pprint,
        set_showpresorted = True)
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string in a reproducible order.
        
        >>> d1 = {'wght': (-0.75, -0.25, 0), 'wdth': (0, 0.5, 0.75)}
        >>> key1 = LivingRegion.fromdict(d1)
        >>> memb1 = LivingDeltasMember((key1, -180))
        >>> d2 = {'wght': (0.25, 0.5, 1.0), 'wdth': (-1, -1, 0)}
        >>> key2 = LivingRegion.fromdict(d2)
        >>> memb2 = LivingDeltasMember((key2, 40))
        >>> obj = LivingDeltas({memb1, memb2})
        >>> print(str(obj))
        ('wdth': (start -1.0, peak -1.0, end 0.0), 'wght': (start 0.25, peak 0.5, end 1.0), 40); ('wdth': (start 0.0, peak 0.5, end 0.75), 'wght': (start -0.75, peak -0.25, end 0.0), -180)
        """
        
        sv = [str(obj) for obj in sorted(self, key=str)]
        return '; '.join(sv)
    
    @classmethod
    def fromdeltasdict(cls, dd, **kwArgs):
        """
        Create a LivingDeltas object from supplied DeltasDict (gvar-style
        Deltas).
        
        Two kwArgs are recognized:
            representsy     if True, use the Y-component of the DeltasDict
                            members, otherwise the X-component will be used.
                            Default False.
                            
            skipZeroes      if True, does not include Deltas of zero value, UNLESS
                            all values are zero.
                            Default True.
        
        """

        representsy = kwArgs.get('representsy', False)
        skipZeroes = kwArgs.get('skipZeroes', True)

        ldmembers = set()

        for dk, dv in dd.items():

            # build LivingRegion. These are triangles of (start, peak, end) with
            #   start = dv.effectiveDomain.edge1[axisTag]
            #   peak = dk[axisTag]
            #   end = dv.effectiveDomain.edge2[axisTag]
            lrd = {}
            for i, dkk in enumerate(dk):
                tag = dk.axisOrder[i]
                ed0 = dv.effectiveDomain.edge1[i]
                ed1 = dv.effectiveDomain.edge2[i]
                lrd[tag] = (ed0, dk[i], ed1)
            region = LivingRegion.fromdict(lrd)

            # build LivingDeltasMember from region + Deltas value and add to members set
            v = dv.y if representsy else dv.x
            ldmembers.add(LivingDeltasMember((region, v)))

        # zero-cases
        allzeroes = list(set([v[1] for v in sorted(ldmembers)])) == [0]
        if skipZeroes and not allzeroes:
            # eject any zero-value ldms
            ldmembers = set([x for x in sorted(ldmembers) if x[1] != 0])

        return cls(ldmembers)


    def interpolate(self, coordLAC, **kwArgs):
        """
        Given a specified LivingAxialCoordinate return the interpolated delta.
        
        >>> d1 = {'wght': (-1.0, -0.5, 0), 'wdth': (0, 0.25, 0.75)}
        >>> obj1 = LivingRegion.fromdict(d1)
        >>> d2 = {'wght': (-1.0, -0.75, -0.5), 'wdth': (0.5, 0.75, 1.0)}
        >>> obj2 = LivingRegion.fromdict(d2)
        >>> ldm1 = LivingDeltasMember((obj1, 100))
        >>> ldm2 = LivingDeltasMember((obj2, -40))
        >>> ld = LivingDeltas({ldm1})
        >>> fd = LivingAxialCoordinate.fromdict
        >>> ld.interpolate(fd({'wght': -0.5, 'wdth': 0.625}))
        25.0
        >>> ld.interpolate(fd({'wght': -0.625, 'wdth': 0.625}))
        18.75
        >>> ld.interpolate(fd({'wght': -0.25, 'wdth': 0.625}))
        12.5
        >>> ld.interpolate(fd({'wght': -0.25, 'wdth': 0.5}))
        25.0
        >>> ld = LivingDeltas({ldm1, ldm2})
        >>> ld.interpolate(fd({'wght': -0.625, 'wdth': 0.625}))
        8.75
        """
        
        return sum(
          lrObj.factorFromLAC(coordLAC) * delta
          for lrObj, delta in self)

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class LivingDeltasMember(tuple, metaclass=keymeta.FontDataMetaclass):
    """
    These are pairs (LivingRegion, delta). They are used as elements in a
    LivingDeltas object.
    """
    
    #
    # Class definition variables
    #
    
    itemSpec = (
        dict(item_followsprotocol = True),
        dict())

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class LivingRegion(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing a complete region (subspace of the entire variation
    space) with a LivingAxialRegion for each axis. These are frozensets of
    LivingRegionMembers.
    
    As immutable objects these are useful as dict keys, specifically for
    instances of the LivingDeltas class (q.v.)
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_followsprotocol = True,
        set_showpresorted = True)
    
    #
    # Methods
    #
    
    def __str__(self):
        sv = []
        
        for t in sorted(self, key=operator.itemgetter(0)):
            sv.append("'%s': %s" % t)
        
        return ', '.join(sv)
    
    def buildBinary(self, w, **kwArgs):
        """
        
        >>> ao = (b'wght', b'wdth')
        >>> d = {b'wght': (-0.75, 0.0, 1.0), b'wdth': (-1.0, 0.25, 0.75)}
        >>> obj = LivingRegion.fromdict(d)
        >>> utilities.hexdump(obj.binaryString(axisOrder=ao))
               0 | D000 0000 4000 C000  1000 3000           |....@.....0.    |
        """
        
        d = dict(self)  # axis tag -> LivingAxialRegion
        
        for tag in kwArgs['axisOrder']:
            d[tag].buildBinary(w)
    
    def factorFromLAC(self, coordLAC):
        """
        Given a LivingAxialCoordinate determine the multiplicative factor that
        applies to self. This returned factor will be between zero and one,
        inclusive.
        
        >>> d = {'wght': (-0.75, -0.5, 0), 'wdth': (0, 0.25, 0.75)}
        >>> obj = LivingRegion.fromdict(d)
        >>> fd = LivingAxialCoordinate.fromdict
        >>> obj.factorFromLAC(fd({'wght': -0.5, 'wdth': 0.25}))
        1.0
        >>> obj.factorFromLAC(fd({'wght': -0.25, 'wdth': 0.25}))
        0.5
        >>> obj.factorFromLAC(fd({'wght': -0.25, 'wdth': 0.5}))
        0.25
        >>> obj.factorFromLAC(fd({'wght': -0.75, 'wdth': 0.25}))
        0.0
        """
        
        dC = dict(coordLAC)
        dS = dict(self)
        r = 1
        
        for tag, tS in dS.items():
            if not r:
                return r
            
            coordC = dC[tag]
            start, peak, end = tS
            
            if not peak:
                continue
            
            if start > end:
                start, end = end, start
            
            if (
              (not coordC) or
              (coordC < 0 and peak > 0) or
              (coordC > 0 and peak < 0) or
              (not start <= coordC <= end)):
                
                r = 0
            
            elif coordC < peak:  # all "<" means here is "to the left of"
                if peak != start:
                    r *= (coordC - start) / (peak - start)
            
            elif end != peak:
                r *= (end - coordC) / (end - peak)
        
        return r
    
    @classmethod
    def fromdict(cls, d, **kwArgs):
        """
        Creates and returns a new LivingRegion object from the specified dict,
        which should map axis tag strings to tuples that are the equivalent of
        LivingAxialRegion objects.
        
        >>> d = {'wght': (-0.75, 0.0, 1.0), 'wdth': (-1.0, 0.25, 0.75)}
        >>> obj = LivingRegion.fromdict(d)
        >>> print(obj)
        'wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0)
        >>> dTest = {obj: 15}  # it can be used as a dict key
        """
        
        AC = axial_coordinate.AxialCoordinate
        LAR = LivingAxialRegion
        LRM = LivingRegionMember
        return cls(LRM([k, LAR(*(AC(x) for x in t))]) for k, t in d.items())
    
    def intersects(self, other, **kwArgs):
        """
        Given two LivingRegions, returns True if they intersect and False if
        they don't.
        
        >>> d1 = {'wght': (-0.75, -0.5, 0), 'wdth': (0, 0.25, 0.75)}
        >>> obj1 = LivingRegion.fromdict(d1)
        >>> d2 = {'wght': (-1.0, -0.75, -0.5), 'wdth': (0.5, 0.9, 1.0)}
        >>> obj2 = LivingRegion.fromdict(d2)
        >>> obj1.intersects(obj2)
        True
        >>> d2['wdth'] = (0.8, 0.9, 1)
        >>> obj2 = LivingRegion.fromdict(d2)
        >>> obj1.intersects(obj2)
        False
        """
        
        d1 = dict(self)
        d2 = dict(other)
        tags = set(d1)
        assert tags == set(d2)
        return all(d1[t].intersects(d2[t]) for t in tags)

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class LivingRegionMember(tuple, metaclass=keymeta.FontDataMetaclass):
    """
    These are tuples comprising two members: an axis tag string, and a
    LivingAxialRegion object.
    """
    
    #
    # Class definition variables
    #
    
    itemSpec = (
        dict(),
        dict(item_followsprotocol = True))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
