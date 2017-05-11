#
# featuretablesubst.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for FeatureTableSubsitution Tables as found in GSUB v1.1 (OpenType
1.8) or later.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.opentype import featuretable
from fontio3.opentype import version as otversion
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureTableSubst(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing FeatureTableSubstitution Tables. These are maps of
    default feature tags to alternate FeatureTables to be applied if the
    object's corresponding ConditionSet (from the parent
    FeatureVariationRecord) is met.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True)

    version = otversion.Version(major=1, minor=0)  # currently only version defined


    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureTableSubst Table object to the
        specified LinkedWriter. The following kwArgs are recognized:
        
            tagToFeatureIndex   A dict mapping feature tags to indices in the
                                top-level table's FeatureTable.
        
        >>> ttfi = {b'test0001':1, b'foob0002':0}
        >>> b = _testingValues[0].binaryString(tagToFeatureIndex=ttfi)
        >>> utilities.hexdump(b)
               0 | 0001 0000 0000                           |......          |

        >>> ll = lltv[1]
        >>> b = _testingValues[1].binaryString(lookupList=ll, tagToFeatureIndex=ttfi)
        >>> utilities.hexdump(b)
               0 | 0001 0000 0001 0001  0000 000C 0000 0001 |................|
              10 | 0001                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        ttfi = kwArgs.pop('tagToFeatureIndex')

        FeatureTableSubst.version.buildBinary(w, **kwArgs)
        substCount = len(self)
        w.add("H", substCount)

        if substCount:
            featureSubs = [(ttfi[tag], self[tag]) for tag in self]

            stakesDict = {locIdx:w.getNewStake() for locIdx in range(substCount)}

            for locIdx, (fidx, aft) in enumerate(sorted(featureSubs)):
                w.add("H", fidx)  # index into default FeatureTable
                w.addUnresolvedOffset("L", stakeValue, stakesDict[locIdx])  # local idx

            for locIdx, (fidx, aft) in enumerate(sorted(featureSubs)):
                aft.buildBinary(w, stakeValue=stakesDict[locIdx], **kwArgs)
        
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureTableSubst object from the specified walker,
        doing source validation.
        
        The following kwArgs are recognized:
            logger              A logger to post messages to (required).
            
            defaultFeatures     The default GSUB FeatureTable to index into
                                for replacement (required).
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fitt = [b'test0001', b'foob0002']
        >>> s = ("00010000 0000")
        >>> b = utilities.fromhex(s)
        >>> fvb = FeatureTableSubst.fromvalidatedbytes
        >>> obj = fvb(b, featureIndexToTag=fitt, logger=logger)
        test.featuretablesubst - DEBUG - Walker has 6 remaining bytes.
        test.version - DEBUG - Walker has 6 remaining bytes.
        test.featuretablesubst - INFO - SubstitutionCount is 0

        >>> ll = lltv[1]
        >>> s = ("00010000"       # Version
        ...      "0001"           # count = 1
        ...      "0001 0000000C"  # feature index, offset to alt feature table
        ...      "0000 0000")     # alt feature table data (@offset)
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, featureIndexToTag = fitt, logger=logger, lookupList=ll)
        test.featuretablesubst - DEBUG - Walker has 16 remaining bytes.
        test.version - DEBUG - Walker has 16 remaining bytes.
        test.featuretablesubst - INFO - SubstitutionCount is 1
        test.featuretablesubst - DEBUG - Feature index 1, offset 0x0000000C
        test.featuretable - DEBUG - Walker has 4 remaining bytes.
        test.featuretable - DEBUG - FeatureParams offset is 0, lookupCount is 0

        >>> obj = fvb(b[0:4], featureIndexToTag = fitt, logger=logger, lookupList=ll)
        test.featuretablesubst - DEBUG - Walker has 4 remaining bytes.
        test.featuretablesubst - ERROR - Insufficient bytes.
        
        >>> s = "00010000 0005 0001 0000000C"
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, featureIndexToTag = fitt, logger=logger, lookupList=ll)
        test.featuretablesubst - DEBUG - Walker has 12 remaining bytes.
        test.version - DEBUG - Walker has 12 remaining bytes.
        test.featuretablesubst - ERROR - Insufficient bytes for declared count of 5.
        """

        logger = kwArgs.get('logger', None)

        if logger is None:
            logger = logging.getLogger()

        logger = logger.getChild("featuretablesubst")
        
        fitt = kwArgs.pop('featureIndexToTag')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        vers = otversion.Version.fromvalidatedwalker(w, **kwArgs)
        
        count = w.unpack("H")
        
        if w.length() < count * 6:
            logger.error((
              'V0004',
              (count,),
              "Insufficient bytes for declared count of %d."))
            return None
        
        logger.info(('Vxxxx', (count,), "SubstitutionCount is %d"))
        
        idxOffs = w.group("HL", count)
        d = {}
        fvw = featuretable.FeatureTable.fromvalidatedwalker
        for fidx, offset in idxOffs:
            logger.debug(('Vxxxx', (fidx, offset), "Feature index %d, offset 0x%08X"))
            wSub = w.subWalker(offset)
            tag = fitt[fidx]
            d[tag] = fvw(wSub, **kwArgs)

        r = cls(d)

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureTableSubst object from the specified
        walker.

        >>> ll = lltv[1]
        >>> fitt = [b'test0001', b'foob0002']
        >>> s = ("00010000 0001 0001 0000000C"  # FeatTableSubst header
        ...      "0000 0000")                   # AltFeatureTable
        >>> b = utilities.fromhex(s)
        >>> fb = FeatureTableSubst.frombytes
        >>> obj = fb(b, featureIndexToTag=fitt, lookupList=ll)
        >>> sorted(obj.keys())
        [b'foob0002']
        """

        fitt = kwArgs.pop('featureIndexToTag')

        vers = otversion.Version.fromwalker(w, **kwArgs)
        count = w.unpack("H")
        
        idxOffs = w.group("HL", count)
        d = {}
        fw = featuretable.FeatureTable.fromwalker

        for fidx, offset in idxOffs:
            wSub = w.subWalker(offset)
            tag = fitt[fidx]
            d[tag] = fw(wSub, **kwArgs)
            
        r = cls(d)

        return r


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import lookuplist

    lltv = lookuplist._testingValues
    fttv = featuretable._testingValues
    
    _testingValues = (
        FeatureTableSubst(),
        FeatureTableSubst({b'test0001': fttv[0]}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
