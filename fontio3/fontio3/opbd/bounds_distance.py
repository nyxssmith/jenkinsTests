#
# bounds_distance.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the distance format of 'opbd' bounds data.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not valassist.isFormat_h(obj, logger=logger, label="optical value"):
        return False
    
    editor = kwArgs['editor']
    
    if editor is None or (not editor.reallyHas(b'head')):
        return True
    
    upem = editor.head.unitsPerEm
    
    if abs(obj) >= (upem / 2):
        kwArgs['logger'].warning((
          'V0784',
          (obj,),
          "The optical value %d is improbably large."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Bounds_Distance(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing the side deltas in FUnits for a single glyph's optical
    bounds data. These are simple objects with four attributes: left, top,
    right, and bottom.
    
    >>> print(_testingValues[0])
    Left delta = 5, Top delta = -10, Right delta = -5, Bottom delta = -8
    
    >>> _testingValues[1].pprint()  # only displays nonzero values
    Top delta: -10
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    val.bottom - ERROR - The optical value 29.25 is not an integer.
    val.left - ERROR - The optical value 40000 does not fit in 16 bits.
    val.right - ERROR - The optical value 'x' is not a real number.
    val.top - ERROR - The optical value -40000 does not fit in 16 bits.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        left = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Left delta",
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate),
        
        top = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Top delta",
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate),
        
        right = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Right delta",
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate),
        
        bottom = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Bottom delta",
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate))
    
    objSpec = dict(
        obj_enableordering = True)
    
    attrSorted = ('left', 'top', 'right', 'bottom')
    isDistance = True
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Bounds_Distance object from the specified
        walker, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> s = _testingValues[0].binaryString()
        >>> fvb = Bounds_Distance.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.bounds_distance - DEBUG - Walker has 8 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:1], logger=logger)
        fvw.bounds_distance - DEBUG - Walker has 1 remaining bytes.
        fvw.bounds_distance - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("bounds_distance")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(*w.group("h", 4))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Bounds_Distance object from the data in the
        specified walker.
        
        >>> f = Bounds_Distance.frombytes
        >>> _testingValues[0] == f(_testingValues[0].binaryString())
        True
        >>> _testingValues[1] == f(_testingValues[1].binaryString())
        True
        >>> _testingValues[2] == f(_testingValues[2].binaryString())
        True
        """
        
        return cls(*w.group("h", 4))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Bounds_Distance object to the specified
        LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 0005 FFF6 FFFB FFF8                      |........        |
        
        >>> h(_testingValues[1].binaryString())
               0 | 0000 FFF6 0000 0000                      |........        |
        
        >>> h(_testingValues[2].binaryString())
               0 | 0000 0000 0000 0000                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("4h", self.left, self.top, self.right, self.bottom)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Bounds_Distance(5, -10, -5, -8),
        Bounds_Distance(0, -10, 0, 0),
        Bounds_Distance(),
        
        # bad values start here
        
        Bounds_Distance(40000, -40000, 'x', 29.25))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
