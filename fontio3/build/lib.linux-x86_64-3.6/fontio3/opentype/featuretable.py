#
# featuretable.py
#
# Copyright © 2010-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions of a single FeatureTable, whether for GPOS or GSUB.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class FeatureTable(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing OpenType FeatureTables. These are lists of Lookup
    objects. There is one attribute:
    
        featureParams       If the feature type supports feature parameters,
                            this will be that object.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Lookup 0:
      Subtable 0 (Pair (glyph) positioning table):
        (xyz11, xyz21):
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
        (xyz9, xyz16):
          Second adjustment:
            FUnit adjustment to origin's x-coordinate: -10
        (xyz9, xyz21):
          First adjustment:
            Device for vertical advance:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
      Lookup flags:
        Right-to-left for Cursive: False
        Ignore base glyphs: True
        Ignore ligatures: False
        Ignore marks: False
      Sequence order (lower happens first): 1
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    Feature parameters object:
      Design size in decipoints: 80
      Subfamily value: 4
      Name table index of common subfamily: 300
      Small end of usage range in decipoints: 80
      Large end of usage range in decipoints: 120
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_islookup = True,
        item_pprintlabelfunc = (lambda i: "Lookup %d" % (i,)),
        seq_compactremovesfalses = True,
        seq_mergeappend = True)
    
    attrSpec = dict(
        featureParams = dict(
            attr_followsprotocol = True,
            attr_label = "Feature parameters object",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content to the specified LinkedWriter. The following
        keyword arguments are supported:
        
            lookupList  A correctly sorted LookupList object. Indices into this
                        list will be used during the writing of binary data. If
                        there are any Lookup objects referred to in this
                        FeatureTable but not present in the LookupList, a
                        ValueError is raised. This argument is required.
            
            stakeValue  The stake for the start of the FeatureTable.
        
        >>> ll = _getLL()._testingValues[1]
        >>> utilities.hexdump(_testingValues[0].binaryString(lookupList=ll))
               0 | 0000 0001 0001                           |......          |
        
        >>> utilities.hexdump(_testingValues[1].binaryString(lookupList=ll))
               0 | 0008 0002 0002 0001  003C 0000 0000 0000 |.........<......|
              10 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(lookupList=ll))
               0 | 0004 0000 0050 0004  012C 0050 0078      |.....P...,.P.x  |
        
        >>> utilities.hexdump(_testingValues[3].binaryString(lookupList=ll))
               0 | 0000 0000                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self.featureParams is None:
            w.add("H", 0)
        else:
            fpStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, fpStake)
        
        w.add("H", len(self))
        lkList = kwArgs['lookupList']
        
        for lkObj in self:
            try:
                w.add("H", lkList.index(lkObj))
            except ValueError:
                raise ValueError("At least one lookup not present in lookup list!")
        
        if self.featureParams is not None:
            self.featureParams.buildBinary(w, stakeValue=fpStake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureTable object from the specified
        walker, doing source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('featuretable')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        fpOffset, lookupCount = w.unpack("2H")
        
        logger.debug((
          'Vxxxx',
          (fpOffset, lookupCount),
          "FeatureParams offset is %d, lookupCount is %d"))
        
        if fpOffset:
            maker = kwArgs.get('fpMaker')
            
            if maker is None:
                logger.error((
                  'V0949',
                  (),
                  "There is a nonzero offset to a FeatureParams object, "
                  "but the associated tag has no definitions for one."))
                
                return None
            
            fpObj = maker(w.subWalker(fpOffset), logger=logger, **kwArgs)
            
            if fpObj is None:
                return None
        
        else:
            fpObj = None
        
        if w.length() < 2 * lookupCount:
            logger.error((
              'V0407',
              (),
              "The lookup indices are missing or incomplete."))
            
            return None
        
        indices = w.group("H", lookupCount)
        
        assert 'lookupList' in kwArgs
        lkList = kwArgs['lookupList']
        v = [None] * lookupCount
        
        for i, lkIndex in enumerate(indices):
            logger.debug((
              'Vxxxx',
              (i, lkIndex),
              "Entry %d is Lookup %d"))
            
            if lkIndex >= len(lkList):
                logger.error((
                  'V0408',
                  (lkIndex, i),
                  "Lookup list index %d (at position %d in the FeatureTable) "
                  "is too large for the Lookup list."))
                
                return None
            
            v[i] = lkList[lkIndex]
        
        return cls(v, featureParams=fpObj)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureTable from the specified walker. The
        following keyword arguments are supported:
        
            fpMaker     If the feature tag associated with this feature table
                        supports a FeatureParams object, then this field should
                        be the fromwalker classmethod from the corresponding
                        class. (A dict of tag->makerClass values is available
                        in the featureparams module for both GPOS and GSUB
                        tables)
            
            lookupList  A list whose indices are lookupList sequence values and
                        whose values are the corresponding Lookup objects.
        
        >>> ll = _getLL()._testingValues[1]
        >>> fpm = _getFP().dispatchTableGPOS[b'size']
        >>> bs = _testingValues[0].binaryString(lookupList=ll)
        >>> _testingValues[0] == FeatureTable.frombytes(bs, fpMaker=fpm, lookupList=ll)
        True
        
        >>> bs = _testingValues[1].binaryString(lookupList=ll)
        >>> _testingValues[1] == FeatureTable.frombytes(bs, fpMaker=fpm, lookupList=ll)
        True
        
        >>> bs = _testingValues[2].binaryString(lookupList=ll)
        >>> _testingValues[2] == FeatureTable.frombytes(bs, fpMaker=fpm, lookupList=ll)
        True
        
        >>> bs = _testingValues[3].binaryString(lookupList=ll)
        >>> _testingValues[3] == FeatureTable.frombytes(bs, fpMaker=fpm, lookupList=ll)
        True
        """
        
        fpOffset = w.unpack("H")
        fpObj = (kwArgs['fpMaker'](w.subWalker(fpOffset), **kwArgs) if fpOffset else None)
        lkList = kwArgs['lookupList']
        v = [lkList[lkIndex] for lkIndex in w.group("H", w.unpack("H"))]
        return cls(v, featureParams=fpObj)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    def _getFP():
        from fontio3.opentype import featureparams
        return featureparams
    
    def _getLL():
        from fontio3.opentype import lookuplist
        return lookuplist
    
    fptv = _getFP()._testingValues
    lltv = _getLL()._testingValues
    
    _testingValues = (
        FeatureTable([lltv[1][1]]),
        FeatureTable([lltv[1][2], lltv[1][1]], featureParams=fptv[0]),
        FeatureTable([], featureParams=fptv[1]),
        FeatureTable(),
        FeatureTable([lltv[2][0]]),
        FeatureTable([lltv[4][0], lltv[4][1]]))
    
    del fptv, lltv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
