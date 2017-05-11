#
# featureinfo.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'Zapf' feature information for a glyph.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.Zapf import featurearray_aat, featurearray_ot, featureinfo_context

# -----------------------------------------------------------------------------

#
# Classes
#

class FeatureInfo(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects providing feature information for a single glyph. These are simple
    objects with three attributes:
    
        context         A featureinfo_context.Context object.
        featuresAAT     A featurearray_aat.FeatureArray_AAT object.
        featuresOT      A faturearray_ot.FeatureArray_OT object.
    
    >>> _testingValues[1].pprint()
    Glyph context:
      line-initial, word-initial
    AAT Features:
      Feature 0:
        Common ligatures on (1, 2)
      Feature 1:
        Rare ligatures on (1, 4)
    OpenType Features:
      Feature 0: 'kern'
      Feature 1: 'liga'
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    val.featuresAAT.[0] - WARNING - The combination of feature -1 and setting 6 is not present in the Apple Font Feature Registry.
    val.featuresAAT.[0].feature - ERROR - The negative value -1 cannot be used in an unsigned field.
    val.featuresAAT.[0].setting - ERROR - The value 6.25 is not an integer.
    val.featuresOT.[0] - ERROR - The feature tag 'too long' is not exactly 4 bytes long.
    val.featuresOT.[1] - ERROR - The feature tag -5.375 cannot be converted to ASCII.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        context = dict(
            attr_followsprotocol = True,
            attr_initfunc = featureinfo_context.Context,
            attr_label = "Glyph context",
            attr_showonlyiftrue = True),
        
        featuresAAT = dict(
            attr_followsprotocol = True,
            attr_initfunc = featurearray_aat.FeatureArray_AAT,
            attr_label = "AAT Features",
            attr_showonlyiftrue = True),
        
        featuresOT = dict(
            attr_followsprotocol = True,
            attr_initfunc = featurearray_ot.FeatureArray_OT,
            attr_label = "OpenType Features",
            attr_showonlyiftrue = True))
    
    attrSorted = ('context', 'featuresAAT', 'featuresOT')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Add the binary data for the FeatureInfo object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0000 0000 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0009 0002 0001 0002  0001 0004 0000 0002 |................|
              10 | 6B65 726E 6C69 6761                      |kernliga        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self.context.buildBinary(w, **kwArgs)
        self.featuresAAT.buildBinary(w, **kwArgs)
        self.featuresOT.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureInfo object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = FeatureInfo.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.featureinfo - DEBUG - Walker has 24 remaining bytes.
        fvw.featureinfo.featureinfo - DEBUG - Walker has 22 remaining bytes.
        fvw.featureinfo.featureinfo.[0].featuresetting - DEBUG - Walker has 20 remaining bytes.
        fvw.featureinfo.featureinfo.[1].featuresetting - DEBUG - Walker has 16 remaining bytes.
        fvw.featureinfo.featurearray_ot - DEBUG - Walker has 12 remaining bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("featureinfo")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        c = featureinfo_context.Context.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if c is None:
            return None
        
        a = featurearray_aat.FeatureArray_AAT.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if a is None:
            return None
        
        o = featurearray_ot.FeatureArray_OT.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if o is None:
            return None
        
        return cls(c, a, o)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureInfo object from the specified walker.
        
        >>> for obj in _testingValues[:2]:
        ...   print(obj == FeatureInfo.frombytes(obj.binaryString()))
        True
        True
        """
        
        c = featureinfo_context.Context.fromwalker(w)
        a = featurearray_aat.FeatureArray_AAT.fromwalker(w)
        o = featurearray_ot.FeatureArray_OT.fromwalker(w)
        return cls(c, a, o)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _cv = featureinfo_context._testingValues
    _atv = featurearray_aat._testingValues
    _otv = featurearray_ot._testingValues
    
    _testingValues = (
        FeatureInfo(),
        FeatureInfo(_cv[1], _atv[1], _otv[1]),
        
        # bad values start here
        
        FeatureInfo(_cv[1], _atv[2], _otv[2]))
    
    del _cv, _atv, _otv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
