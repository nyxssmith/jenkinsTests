#
# featurearray_aat.py
#
# Copyright © 2012-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for arrays of 'mort' or 'morx' FeatureSetting objects.
"""

# System imports
import itertools
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.mort import featuresetting

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    if len(obj) > 65535:
        kwArgs['logger'].error((
          'V0749',
          (),
          "The number of AAT features cannot exceed 65,535."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureArray_AAT(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a group of AAT-style metamorphosis features. These are
    tuples of fontio3.mort.featuresetting.FeatureSetting objects.
    
    >>> _testingValues[1].pprint()
    Feature 0:
      Common ligatures on (1, 2)
    Feature 1:
      Rare ligatures on (1, 4)
    
    >>> logger = utilities.makeDoctestLogger("featurearray_aat_val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    featurearray_aat_val.[0] - WARNING - The combination of feature -1 and setting 6 is not present in the Apple Font Feature Registry.
    featurearray_aat_val.[0].feature - ERROR - The negative value -1 cannot be used in an unsigned field.
    featurearray_aat_val.[0].setting - ERROR - The value 6.25 is not an integer.
    False
    
    >>> F = featuresetting.FeatureSetting
    >>> it1 = map(F, itertools.repeat(3, 40000), iter(range(40000)))
    >>> it2 = map(F, itertools.repeat(4, 40000), iter(range(40000)))
    >>> tooBig = FeatureArray_AAT(itertools.chain(it1, it2))
    >>> logger.logger.setLevel(logging.ERROR)
    >>> tooBig.isValid(logger=logger, editor=e)
    featurearray_aat_val - ERROR - The number of AAT features cannot exceed 65,535.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda n: "Feature %d" % (n,)),
        seq_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureArray_AAT object to the specified
        writer.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0001 0002 0001  0004                |..........      |
        """
        
        w.add("H", len(self))
        
        for obj in self:
            obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureInfo object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("featurearray_aat_fvw")
        >>> fvb = FeatureArray_AAT.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        featurearray_aat_fvw.featureinfo - DEBUG - Walker has 10 remaining bytes.
        featurearray_aat_fvw.featureinfo.[0].featuresetting - DEBUG - Walker has 8 remaining bytes.
        featurearray_aat_fvw.featureinfo.[1].featuresetting - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        featurearray_aat_fvw.featureinfo - DEBUG - Walker has 1 remaining bytes.
        featurearray_aat_fvw.featureinfo - ERROR - The AAT feature count is missing or incomplete.
        
        >>> fvb(s[:-1], logger=logger)
        featurearray_aat_fvw.featureinfo - DEBUG - Walker has 9 remaining bytes.
        featurearray_aat_fvw.featureinfo.[0].featuresetting - DEBUG - Walker has 7 remaining bytes.
        featurearray_aat_fvw.featureinfo.[1].featuresetting - DEBUG - Walker has 3 remaining bytes.
        featurearray_aat_fvw.featureinfo.[1].featuresetting - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("featureinfo")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error((
              'V0745',
              (),
              "The AAT feature count is missing or incomplete."))
            
            return None
        
        aatCount = w.unpack("H")
        v = [None] * aatCount
        fvw = featuresetting.FeatureSetting.fromvalidatedwalker
        
        for i in range(aatCount):
            obj = fvw(w, logger=logger.getChild("[%d]" % (i,)))
            
            if obj is None:
                return None
            
            v[i] = obj
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureArray_AAT object from the specified
        walker.
        
        >>> fb = FeatureArray_AAT.frombytes
        >>> for obj in _testingValues[:2]:
        ...   print(obj == fb(obj.binaryString()))
        True
        True
        """
        
        aatCount = w.unpack("H")
        fw = featuresetting.FeatureSetting.fromwalker
        return cls(map(fw, itertools.repeat(w, aatCount)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __debug__:
    from fontio3 import utilities
    
    _fstv = featuresetting._testingValues
    
    _testingValues = (
        FeatureArray_AAT(),
        FeatureArray_AAT([_fstv[6], _fstv[8]]),
        
        # bad entries start here
        
        FeatureArray_AAT([featuresetting.FeatureSetting([-1, 6.25])]))
    
    del _fstv

if __name__ == "__main__":
    if __debug__:
        _test()
