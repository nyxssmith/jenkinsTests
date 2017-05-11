#
# featurevariations.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for FeatureVariations Tables as found in GSUB v1.1 (OpenType 1.8) or
later.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.opentype import conditionset, featuretablesubst
from fontio3.opentype import version as otversion

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureVariations(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing FeatureVariations Tables. These are maps of
    ConditionSets to FeatureTableSubsts. Clients can test a given set of axial
    coordinates against each ConditionSet to obtain a FeatureTableSubst to use
    in the case of a match.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_keyfollowsprotocol = True,
        item_followsprotocol = True)

    version = otversion.Version(major=1, minor=0)
    
    def __iter__(self):
        """
        Returns a custom iterator that respects the ConditionSet ordering.
        
        xxx add doctests...
        """
        
        d = dict(self)  # avoid infinite loop in __iter__()...
        
        for k in sorted(d, key=operator.attrgetter('sequence')):
            yield k

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureVariations Table object to the
        specified LinkedWriter.
        
        >>> b = _testingValues[0].binaryString()
        >>> utilities.hexdump(b)
               0 | 0001 0000 0000 0000                      |........        |
        
        >>> ao = ('wght', 'wdth')
        >>> ll = lltv[1]
        >>> ttfi = {b'fea10001':0, b'test0001':1}
        >>> bsf = _testingValues[1].binaryString
        >>> b = bsf(axisOrder=ao, lookupList=ll, tagToFeatureIndex=ttfi)
        >>> utilities.hexdump(b)
               0 | 0001 0000 0000 0001  0000 0010 0000 002A |...............*|
              10 | 0002 0000 000A 0000  0012 0001 0001 C000 |................|
              20 | 4000 0001 0000 0010  4000 0001 0000 0001 |@.......@.......|
              30 | 0001 0000 000C 0000  0001 0001           |............    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        FeatureVariations.version.buildBinary(w, **kwArgs)

        reccount = len(self)
        w.add("L", reccount)
        
        stakesDict = dict()

        for i in range(len(self)):
            stakesDict[i] = (w.getNewStake(), w.getNewStake())
            w.addUnresolvedOffset("L", stakeValue, stakesDict[i][0])
            w.addUnresolvedOffset("L", stakeValue, stakesDict[i][1])

        for i, cs in enumerate(sorted(self)):  # seq order thanks to __iter__()
            fts = self[cs]
            w.stakeCurrentWithValue(stakesDict[i][0])
            cs.buildBinary(w, **kwArgs)
            w.stakeCurrentWithValue(stakesDict[i][1])
            fts.buildBinary(w, **kwArgs)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureVariations object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = ("00010000"                                # Version
        ...      "00000001"                                # count
        ...      "00000010 0000001E"                       # offsets[0]
        ...      "0001 00000006 0001 0000 0666 4000"       # CondSetData [0]
        ...      "00010000 0001 0001 0000000C 0000 0000")  # FeatTableSubst data [0]
        >>> b = utilities.fromhex(s)
        >>> ll = lltv[1]
        >>> ao = ('wght', 'wdth')
        >>> fitt = [b'fea10001', b'feat20002']
        >>> fvb = FeatureVariations.fromvalidatedbytes
        >>> obj = fvb(b, featureIndexToTag=fitt, logger=logger, lookupList=ll, axisOrder=ao)
        test.featurevariations - DEBUG - Walker has 46 remaining bytes.
        test.version - DEBUG - Walker has 46 remaining bytes.
        test.featurevariations - INFO - FeatureVariationRecordCount is 1
        test.featurevariations - DEBUG - offsetConditionSet: 0x00000010, offsetFeatureTableSubst: 0x0000001E
        test.conditionset - DEBUG - Walker has 30 remaining bytes.
        test.conditionset - INFO - ConditionCount is 1
        test.condition - DEBUG - Walker has 24 remaining bytes.
        test.condition - INFO - AxisTag 'wght'
        test.condition - INFO - Min: 0.099976, Max: 1.000000
        test.featuretablesubst - DEBUG - Walker has 16 remaining bytes.
        test.version - DEBUG - Walker has 16 remaining bytes.
        test.featuretablesubst - INFO - SubstitutionCount is 1
        test.featuretablesubst - DEBUG - Feature index 1, offset 0x0000000C
        test.featuretable - DEBUG - Walker has 4 remaining bytes.
        test.featuretable - DEBUG - FeatureParams offset is 0, lookupCount is 0

        >>> sorted(obj.keys())
        [ConditionSet(frozenset({Condition(axisTag='wght', filterMin=0.0999755859375, filterMax=1.0)}), sequence=0)]
        """

        logger = kwArgs.get('logger', None)

        if logger is None:
            logger = logging.getLogger()

        logger = logger.getChild("featurevariations")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        vers = otversion.Version.fromvalidatedwalker(w, **kwArgs)
        
        if (vers.major != FeatureVariations.version.major or 
            vers.minor != FeatureVariations.version.minor):
            logger.error((
              'V0002',
              (vers,),
              "Expected Version 1.0, got %s"))
              
            return None

        count = w.unpack("L")
        
        logger.info((
          'Vxxxx',
          (count,),
          "FeatureVariationRecordCount is %d"))

        if w.length() < count * 8:
            logger.error((
              'V0004',
              (count,),
              "Insufficient bytes for count of %d"))
            return None

        offsets = w.group("LL", count)  # pre-check offsets before attempting read?

        csfvw = conditionset.ConditionSet.fromvalidatedwalker
        ftsfvw = featuretablesubst.FeatureTableSubst.fromvalidatedwalker

        d = {}

        for seq, (cso, ftso) in enumerate(offsets):
            logger.debug((
              'Vxxxx',
              (cso, ftso),
              "offsetConditionSet: 0x%08X, offsetFeatureTableSubst: 0x%08X"))

            if cso:
                wSubC = w.subWalker(cso)
                cs = csfvw(wSubC, sequence=seq, **kwArgs)  # ConditionSet
            else:
                cs = None

            if ftso:
                wSubF = w.subWalker(ftso)
                fts = ftsfvw(wSubF, **kwArgs)
            else:
                fts = None
                
            d[cs] = fts

        r = cls(d)
            
        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureVariations object from the specified
        walker.

        >>> s = ("00010000"                                # Version
        ...      "00000001"                                # count
        ...      "00000010 0000001E"                       # offsets[0]
        ...      "0001 00000006 0001 0000 0666 4000"       # CondSetData [0]
        ...      "00010000 0001 0001 0000000C 0000 0000")  # FeatTableSubst data [0]
        >>> b = utilities.fromhex(s)
        >>> ll = lltv[1]
        >>> ao = ('wght', 'wdth')
        >>> fb = FeatureVariations.frombytes
        >>> fitt = [b'fea10001', b'fea20002']
        >>> obj = fb(b, featureIndexToTag=fitt, lookupList=ll, axisOrder=ao)
        >>> sorted(obj.keys())
        [ConditionSet(frozenset({Condition(axisTag='wght', filterMin=0.0999755859375, filterMax=1.0)}), sequence=0)]
        """

        vers = otversion.Version.fromwalker(w, **kwArgs)
        
        if vers.major != 1 and vers.minor != 0:
            raise ValueError("Expected version 1.0, got %s" % (vers,))
        
        count = w.unpack("L")
        offsets = w.group("LL", count)

        csfw = conditionset.ConditionSet.fromwalker
        ftsfw = featuretablesubst.FeatureTableSubst.fromwalker


        d = {}

        for seq, (cso, ftso) in enumerate(offsets):
            if cso:
                wSubC = w.subWalker(cso)
                cs = csfw(wSubC, sequence=seq, **kwArgs)
            else:
                cs = None

            if ftso:
                wSubF = w.subWalker(ftso)
                fts = ftsfw(wSubF, **kwArgs)
            else:
                fts = None
                
            d[cs] = fts

        r = cls(d)
            
        return r


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import living_variations, lookuplist

    cstv = conditionset._testingValues
    ftstv = featuretablesubst._testingValues
    lltv = lookuplist._testingValues
    
    _testingValues = (
        FeatureVariations(),
        FeatureVariations({cstv[2]: ftstv[1]}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
