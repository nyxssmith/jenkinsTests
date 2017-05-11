#
# featureentry.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single entries in a 'mort' table's feature subtable.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.mort import featuresetting

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_mask(p, value, label, **kwArgs):
    s = "%X" % (value,)
    extra = len(s) % 8
    
    if extra:
        s = "0" * (8 - extra) + s
    
    p.simple(s, label=label, **kwArgs)

def _validate_disableMask(obj, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        n = int(obj)
    except:
        n = None
    
    if n is None or n != obj:
        logger.error((
          'V0674',
          (obj,),
          "The disableMask %r is not an integer."))
        
        return False
    
    # We check the highest and lowest 0-bits to make sure they're not separated
    # by more than 30 bits (i.e. it has to fit in 32 bits). Note that the logic
    # that shifts things around is not here; that's done by Features objects.
    
    s = bin(n)[2:]
    
    if n and ('0' in s):
        left = s.index('0')
        right = s.rindex('0')
        
        if (right - left) >= 32:
            logger.error((
              'V0675',
              (n,),
              "The diableMask 0x%X has zero-bits too widely separated."))
            
            return False
    
    return True

def _validate_enableMask(obj, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        n = int(obj)
    except:
        n = None
    
    if n is None or n != obj:
        logger.error((
          'V0672',
          (obj,),
          "The enableMask %r is not an integer."))
        
        return False
    
    # We check the highest and lowest 1-bits to make sure they're not separated
    # by more than 30 bits (i.e. it has to fit in 32 bits). Note that the logic
    # that shifts things around is not here; that's done by Features objects.
    
    if n:  # only bother to check nonzero values
        s = bin(n)[2:]
        left = s.index('1')
        right = s.rindex('1')
        
        if (right - left) >= 32:
            logger.error((
              'V0673',
              (n,),
              "The enableMask 0x%X has one-bits too widely separated."))
            
            return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureEntry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single entries in a 'mort' table's feature table.
    These are simple collections of attributes:
    
        featureSetting      A FeatureSetting object which describes which
                            particular feature is being controlled.
    
        disableMask         An integer of arbitrary size (note specifically
                            that this is not limited to 32 bits!) representing
                            the set of bits that disable other features. This
                            will usually be a value whose binary representation
                            is mostly 1 bits.
        
        enableMask          An integer of arbitrary size (note specifically
                            that this is not limited to 32 bits!) representing
                            the set of bits that enable this feature. This will
                            usually be a value whose binary representation is
                            mostly 0 bits.
    
    A note about 'mort' limitations: the featureSetting and featureType values
    are restricted to 32 bits per chain; that detail is handled by the class,
    and should not be worried about by implementors. See the "extraShift" note
    in the docstrings for the fromwalker() and buildBinary() methods for more
    details on this.
    
    >>> _testingValues[1].pprint()
    Feature/setting: Superiors (10, 1)
    Enable mask: 00000001
    Disable mask: FFFFFFFF
    
    >>> _testingValues[2].pprint()
    Feature/setting: No alternates (17, 0)
    Enable mask: 00000002
    Disable mask: FFFFFFFE
    
    >>> _testingValues[3].pprint()
    Feature/setting: Character alternative 4 (17, 4)
    Enable mask: 000400000000000000000000
    Disable mask: FFFDFFFFFFFFFFFFFFFFFFFF
    
    >>> logger = utilities.makeDoctestLogger("featureentry_test")
    >>> e = utilities.fakeEditor(0x1000)
    >>> print(
    ...   all(
    ...     _testingValues[i].isValid(logger=logger, editor=e)
    ...     for i in range(1, 11)))
    True
    
    >>> obj = _testingValues[7].__deepcopy__()
    >>> obj.enableMask |= 8
    >>> obj.isValid(logger=logger, editor=e)
    featureentry_test.enableMask - ERROR - The enableMask 0x10000000000008 has one-bits too widely separated.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        featureSetting = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: featuresetting.FeatureSetting((0, 0))),
            attr_label = "Feature/setting",
            
            attr_pprintfunc = (
              lambda p, obj, label, **k:
              p.simple(str(obj), label = label, **k))),
        
        enableMask = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Enable mask",
            attr_pprintfunc = _pprint_mask,
            attr_validatefunc = _validate_enableMask),
        
        disableMask = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Disable mask",
            attr_pprintfunc = _pprint_mask,
            attr_validatefunc = _validate_disableMask))
    
    attrSorted = ('featureSetting', 'enableMask', 'disableMask')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureEntry to the specified writer.
        There is one keyword argument:
        
            extraShift      A bit count (which should be a multiple of 32)
                            representing the amount by which the masks should
                            be shifted to the right before being written. The
                            client should pass a different value for this
                            argument for each chain.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000A 0001 0000 0001  FFFF FFFF           |............    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0011 0000 0000 0002  FFFF FFFE           |............    |
        
        >>> utilities.hexdump(_testingValues[3].binaryString(extraShift=64))
               0 | 0011 0004 0004 0000  FFFD FFFF           |............    |
        """
        
        self.featureSetting.buildBinary(w, **kwArgs)
        extraShift = kwArgs.get('extraShift', 0)
        
        if extraShift:
            e = (self.enableMask >> extraShift) & 0xFFFFFFFF
            d = (self.disableMask >> extraShift) & 0xFFFFFFFF
        else:
            e = self.enableMask
            d = self.disableMask
        
        w.add("2L", e, d)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureEntry from the specified walker, doing
        source validation. The following keyword arguments are supported:
        
            extraShift      A bit count (which should be a multiple of 32)
                            representing the amount by which the masks should
                            be shifted to the left before being written. The
                            client should pass a different value for this
                            argument for each chain. Default is zero.
            
            logger          A logger to which messages will be posted.
        
        >>> s = _testingValues[2].binaryString()
        >>> logger = utilities.makeDoctestLogger("featureentry_fvw")
        >>> fvb = FeatureEntry.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        featureentry_fvw.featureentry - DEBUG - Walker has 12 remaining bytes.
        featureentry_fvw.featureentry.featuresetting - DEBUG - Walker has 12 remaining bytes.
        >>> obj == _testingValues[2]
        True
        
        >>> fvb(s[:3], logger=logger)
        featureentry_fvw.featureentry - DEBUG - Walker has 3 remaining bytes.
        featureentry_fvw.featureentry.featuresetting - DEBUG - Walker has 3 remaining bytes.
        featureentry_fvw.featureentry.featuresetting - ERROR - Insufficient bytes.
        """
        
        extraShift = kwArgs.get('extraShift', 0)
        assert (extraShift % 32) == 0
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("featureentry")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        fs = featuresetting.FeatureSetting.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if fs is None:
            return None
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        e, d = w.unpack("2L")
        
        if extraShift:
            e <<= extraShift
            d <<= extraShift
            
            if d:  # we don't augment the special (1, 0) disable value of zero
                d += (2 ** extraShift) - 1
        
        return cls(featureSetting=fs, enableMask=e, disableMask=d)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureEntry from the specified walker. There
        is one keyword argument:
        
            extraShift      A bit count (which should be a multiple of 32)
                            representing the amount by which the masks should
                            be shifted to the left before being written. The
                            client should pass a different value for this
                            argument for each chain. Default is zero.
        
        >>> obj = _testingValues[1]
        >>> obj == FeatureEntry.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == FeatureEntry.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[3]
        >>> d = {'extraShift': 64}
        >>> obj == FeatureEntry.frombytes(obj.binaryString(**d), **d)
        True
        """
        
        extraShift = kwArgs.get('extraShift', 0)
        assert (extraShift % 32) == 0
        
        fs = featuresetting.FeatureSetting.fromwalker(w, **kwArgs)
        e, d = w.unpack("2L")
        
        if extraShift:
            e <<= extraShift
            d <<= extraShift
            
            if d:  # we don't augment the special (1, 0) disable value of zero
                d += (2 ** extraShift) - 1
        
        return cls(featureSetting=fs, enableMask=e, disableMask=d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _fstv = featuresetting._testingValues
    
    _testingValues = (
        FeatureEntry(),
        FeatureEntry(_fstv[0], 1, 0xFFFFFFFF),
        FeatureEntry(_fstv[1], 2, 0xFFFFFFFE),
        FeatureEntry(_fstv[2], 0x40000 << 64, 0xFFFDFFFFFFFFFFFFFFFFFFFF),
        
        # FeatureEntry values for cursive connection
        FeatureEntry(_fstv[3], 0x00000000, 0xFFFFFF3F),
        FeatureEntry(_fstv[4], 0x00000080, 0xFFFFFFBF),
        FeatureEntry(_fstv[5], 0x00000040, 0xFFFFFF7F),
        
        # FeatureEntry values for common and rare ligs
        FeatureEntry(_fstv[6], 0x0010000000000000, 0xFFFFFFFFFFFFFFFF),
        FeatureEntry(_fstv[7], 0x0000000000000000, 0xFFEFFFFFFFFFFFFF),
        FeatureEntry(_fstv[8], 0x0020000000000000, 0xFFFFFFFFFFFFFFFF),
        FeatureEntry(_fstv[9], 0x0000000000000000, 0xFFDFFFFFFFFFFFFF))
    
    del _fstv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
