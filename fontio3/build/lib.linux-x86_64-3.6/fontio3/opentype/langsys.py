#
# langsys.py
#
# Copyright © 2010-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType LangSys objects (in a slightly altered form).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.opentype import langsys_optfeatset

# -----------------------------------------------------------------------------

#
# Classes
#

class LangSys(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing which required and optional features are available for
    a particular script/language combination. These are simple objects with two
    attributes:
    
        requiredFeature     The feature tag for any required feature, or None
                            if there is no required feature.
        
        optionalFeatures    A set of all feature tags.
    
    >>> _testingValues[3].pprint()
    Required feature tag: wxyz0003
    Optional feature tags:
      abcd0001
      size0002
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        requiredFeature = dict(
            attr_label = "Required feature tag",
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(ascii(x)[2:-1], label=label)),
            attr_showonlyiftrue = True),
        
        optionalFeatures = dict(
            attr_followsprotocol = True,
            attr_initfunc = langsys_optfeatset.OptFeatSet,
            attr_label = "Optional feature tags",
            attr_showonlyiftrue = True))
    
    attrSorted = ('requiredFeature', 'optionalFeatures')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the LangSys object to the specified
        LinkedWriter. The following keyword arguments are supported:
        
            stakeValue          The stake value to use for the start of the
                                LangSys.
            
            tagToFeatureIndex   A dict mapping feature tags to their equivalent
                                index values within the FeatureList. This
                                argument is required.
        
        >>> ttfi = {b'abcd0001': 4, b'wxyz0003': 5, b'size0002': 9}
        >>> d = {'tagToFeatureIndex': ttfi}
        >>> utilities.hexdump(_testingValues[0].binaryString(**d))
               0 | 0000 FFFF 0000                           |......          |
        
        >>> utilities.hexdump(_testingValues[1].binaryString(**d))
               0 | 0000 FFFF 0002 0004  0009                |..........      |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(**d))
               0 | 0000 0005 0000                           |......          |
        
        >>> utilities.hexdump(_testingValues[3].binaryString(**d))
               0 | 0000 0005 0002 0004  0009                |..........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 0)  # LookupOrder is not currently defined in OT 1.6
        ttfi = kwArgs['tagToFeatureIndex']
        
        if self.requiredFeature is not None:
            w.add("H", ttfi[self.requiredFeature])
        else:
            w.add("H", 0xFFFF)
        
        v = sorted(ttfi[tag] for tag in self.optionalFeatures)
        w.add("H", len(v))
        w.addGroup("H", v)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LangSys object from the specified walker,
        doing source validation. The
        following keyword arguments are supported:
        
            featureIndexToTag   A sequence whose indices are original feature
                                list indices and whose values are the feature
                                tags. This argument is required.
            
            logger              A logger to which messages will be posted.
        """
        
        assert 'featureIndexToTag' in kwArgs
        fitt = kwArgs['featureIndexToTag']
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('langsys')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        lookupOrder, reqIndex, featCount = w.unpack("3H")
        
        logger.debug((
          'Vxxxx',
          (lookupOrder, reqIndex, featCount),
          "Lookup order is %d, Required index is %d, feature count is %d"))
        
        if lookupOrder:
            logger.warning((
              'V0409',
              (lookupOrder,),
              "The reserved LookupOrder field (0x%04X) is nonzero."))
        
        r = cls()
        
        if reqIndex != 0xFFFF:
            r.requiredFeature = fitt[reqIndex]
        
        if w.length() < 2 * featCount:
            logger.error((
              'V0410',
              (),
              "The FeatureIndex array is missing or incomplete."))
            
            return None
        
        featIndices = w.group("H", featCount)
        
        for i, optIndex in enumerate(featIndices):
            logger.debug((
              'Vxxxx',
              (i, optIndex),
              "Optional feature %d is %d"))
            
            if optIndex >= len(fitt):
                logger.error((
                  'V0411',
                  (optIndex, i),
                  "The FeatureIndex %d (array position %d) is out of range."))
                
                return None
            
            r.optionalFeatures.add(fitt[optIndex])
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LangSys object from the specified walker. The
        following keyword arguments are supported:
        
            featureIndexToTag   A list, whose indices are original feature list
                                indices and whose values are the feature tags.
                                This argument is required.
        
        >>> fitt = [
        ...   b'aaaa0008',
        ...   b'bbbb0006',
        ...   b'cccc0004',
        ...   b'dddd0005',
        ...   b'abcd0001',
        ...   b'wxyz0003',
        ...   b'eeee0007',
        ...   b'ffff0009',
        ...   b'gggg0010',
        ...   b'size0002']
        >>> ttfi = dict((tag, i) for i, tag in enumerate(fitt))
        
        >>> bs = _testingValues[0].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[0] == LangSys.frombytes(bs, featureIndexToTag=fitt)
        True
        
        >>> bs = _testingValues[1].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[1] == LangSys.frombytes(bs, featureIndexToTag=fitt)
        True
        
        >>> bs = _testingValues[2].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[2] == LangSys.frombytes(bs, featureIndexToTag=fitt)
        True
        
        >>> bs = _testingValues[3].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[3] == LangSys.frombytes(bs, featureIndexToTag=fitt)
        True
        """
        
        w.skip(2)  # LookupOrder is not currently defined in OT 1.6
        r = cls()
        reqIndex = w.unpack("H")
        fitt = kwArgs['featureIndexToTag']
        
        if reqIndex != 0xFFFF:
            r.requiredFeature = fitt[reqIndex]
        
        r.optionalFeatures.update(
          fitt[optIndex]
          for optIndex in w.group("H", w.unpack("H")))
        
        return r
    
    def tagsRenamed(self, oldToNew):
        """
        Returns a new LangSys object where feature tags are changed as in the
        specified dict. If a tag is not in the dict, it is not modified.
        """
        
        oldRF = self.requiredFeature
        
        if oldRF is not None:
            newRF = oldToNew.get(oldRF, oldRF)
        else:
            newRF = None
        
        it = (oldToNew.get(tag, tag) for tag in self.optionalFeatures)
        newOF = langsys_optfeatset.OptFeatSet(it)
        
        return type(self)(
          requiredFeature = newRF,
          optionalFeatures = newOF)
    
    def trimToValidFeatures(self, validSet):
        """
        Walks down all contained objects and prunes out any whose feature tags
        are not contained in the specified validSet.
        """
        
        if (
          self.requiredFeature is not None and
          self.requiredFeature not in validSet):
            
            self.requiredFeature = None
        
        self.optionalFeatures &= validSet

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    ofsv = langsys_optfeatset._testingValues
    
    _testingValues = (
        LangSys(),
        LangSys(None, ofsv[1]),
        LangSys(b'wxyz0003', ofsv[0]),
        LangSys(b'wxyz0003', ofsv[1]),
        LangSys(b'efgh0001', ofsv[0]))
    
    del ofsv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
