#
# postcomp_ductile.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for action type 4 (ductile) in a 'just' postcompensation table.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    r = True
    
    if len(utilities.ensureBytes(obj.variationAxis)) != 4:
        logger.error((
          'V0739',
          (),
          "The variationAxis is not a bytestring of length 4."))
        
        r = False
    
    if r:
        v = [obj.minimumLimit, obj.noStretchValue, obj.maximumLimit]
        
        if v != sorted(v):
            logger.error((
              'V0735',
              (),
              "The limit values are not well-ordered."))
            
            r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Postcomp_Ductile(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing ductile actions. These are simple collections of
    the following attributes:
    
        maximumLimit        A floating-point value representing the highest
                            value along the ductility axis that still yields an
                            acceptable appearance. No default.
        
        minimumLimit        A floating-point value representing the lowest
                            value along the ductility axis that still yields an
                            acceptable appearance. Default is 1.0.
        
        noStretchValue      A floating-point value representing no change in
                            appearance. Default is 1.0.
        
        variationAxis       A four-byte binary string representing the axis tag
                            for the variation axis used for ductility. Default
                            is b'duct'.
    
    >>> _testingValues[1].pprint()
    Ductility axis: 'duct'
    Lower limit for ductility: 1.0
    Default value: 1.0
    Upper limit for ductility: 2.0
    
    >>> _testingValues[2].pprint()
    Ductility axis: 'duck'
    Lower limit for ductility: 0.25
    Default value: 1.0
    Upper limit for ductility: 1.75
    
    >>> logger = utilities.makeDoctestLogger("pc_ductile_val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    pc_ductile_val - ERROR - The variationAxis is not a bytestring of length 4.
    pc_ductile_val.minimumLimit - ERROR - The value 'x' is not a real number.
    False
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    pc_ductile_val - ERROR - The limit values are not well-ordered.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        maximumLimit = dict(
            attr_label = "Upper limit for ductility",
            attr_validatefunc = valassist.isNumber_fixed),
        
        minimumLimit = dict(
            attr_initfunc = (lambda: 1.0),
            attr_label = "Lower limit for ductility",
            attr_validatefunc = valassist.isNumber_fixed),
        
        noStretchValue = dict(
            attr_initfunc = (lambda: 1.0),
            attr_label = "Default value",
            attr_validatefunc = valassist.isNumber_fixed),
        
        variationAxis = dict(
            attr_initfunc = (lambda: b'duct'),
            attr_label = "Ductility axis",
            attr_pprintfunc = (
              lambda p, x, label, **kwArgs:
              p.simple(ascii(x)[1:], label=label, **kwArgs))))
    
    attrSorted = (
      'variationAxis',
      'minimumLimit',
      'noStretchValue',
      'maximumLimit')
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    kind = 4  # Class constant for this action kind
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_Ductile object from the
        specified walker, doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Postcomp_Ductile.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("pc_ductile_fvw")
        >>> obj = fvb(s, logger=logger)
        pc_ductile_fvw.postcomp_ductile - DEBUG - Walker has 16 remaining bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("postcomp_ductile")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 16:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        tag, lo, mid, hi = w.unpack("4s3l")
        
        return cls(
          variationAxis = tag,
          minimumLimit = lo / 65536,
          noStretchValue = mid / 65536,
          maximumLimit = hi / 65536)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_Ductile object from the
        specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Postcomp_Ductile.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == Postcomp_Ductile.frombytes(obj.binaryString())
        True
        """
        
        tag, lo, mid, hi = w.unpack("4s3l")
        
        return cls(
          variationAxis = tag,
          minimumLimit = lo / 65536,
          noStretchValue = mid / 65536,
          maximumLimit = hi / 65536)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Postcomp_Ductile object to the
        specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 6475 6374 0001 0000  0001 0000 0002 0000 |duct............|
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 6475 636B 0000 4000  0001 0000 0001 C000 |duck..@.........|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("4s", self.variationAxis)
        w.add("l", int(round(self.minimumLimit * 65536)))
        w.add("l", int(round(self.noStretchValue * 65536)))
        w.add("l", int(round(self.maximumLimit * 65536)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Postcomp_Ductile(),
        Postcomp_Ductile(b'duct', 1.0, 1.0, 2.0),
        Postcomp_Ductile(b'duck', 0.25, 1.0, 1.75),
        
        # the following are bad (for validation testing)
        
        Postcomp_Ductile(b'a bad axis tag', 'x', 1.0, 1.0),
        Postcomp_Ductile(b'whee', 1.25, 1.0, 1.25))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
