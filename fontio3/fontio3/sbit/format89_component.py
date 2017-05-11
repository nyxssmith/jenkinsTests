#
# format89_component.py
#
# Copyright © 2009, 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ebdtComponent data type.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_offset(n, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        n * 1.5
        isNumber = True
    
    except TypeError:
        isNumber = False
    
    if not isNumber:
        logger.error((
          'G0009',
          (n,),
          "The offset value '%s' is not a number."))
        
        return False
    
    if n != int(n):
        logger.error((
          'G0024',
          (n,),
          "The offset value %s is not a signed integer."))
        
        return False
    
    if n < -128 or n > 127:
        logger.error((
          'G0010',
          (n,),
          "The value %d does not fit in a signed byte."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Private classes
#

if 0:
    def __________________(): pass

class _FakePVS:
    def __contains__(self, key): return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Format89_Component(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single components in a composite embedded bitmap
    glyph. These are simple collections of attributes:
    
        glyphCode   Component glyph code.
        xOffset     X-offset to apply to this component.
        yOffset     Y-offset to apply to this component.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Component glyph: xyz26
    X-offset: 0
    Y-offset: 0
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        glyphCode = dict(
            attr_label = "Component glyph",
            attr_prevalidatedglyphset = _FakePVS(),
            attr_renumberdirect = True,
            attr_usenamerforstr = True),
        
        xOffset = dict(
            attr_label = "X-offset",
            attr_representsx = True,
            attr_validatefunc = _validate_offset),
        
        yOffset = dict(
            attr_label = "Y-offset",
            attr_representsy = True,
            attr_validatefunc = _validate_offset))
    
    #
    # Class methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format89_Component object to the specified
        writer.
        
        >>> obj = _testingValues[0]
        >>> print(utilities.hexdumpString(obj.binaryString()), end='')
               0 |0019 0000                                |....            |
        
        >>> obj = _testingValues[1]
        >>> print(utilities.hexdumpString(obj.binaryString()), end='')
               0 |0061 FB05                                |.a..            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H2b", self.glyphCode, self.xOffset, self.yOffset)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Format8. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.sbit')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format89_Component.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.sbit.format89_component - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:-1], logger=logger)
        test.sbit.format89_component - DEBUG - Walker has 3 remaining bytes.
        test.sbit.format89_component - ERROR - Insufficient bytes
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format89_component')
        else:
            logger = logger.getChild('format89_component')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        return cls(*w.unpack("H2b"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format89_Component object from the specified
        walker.
        
        >>> obj = _testingValues[0]
        >>> obj == Format89_Component.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[1]
        >>> obj == Format89_Component.frombytes(obj.binaryString())
        True
        """
        
        return cls(*w.unpack("H2b"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        Format89_Component(25, 0, 0),
        Format89_Component(97, -5, 5))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
