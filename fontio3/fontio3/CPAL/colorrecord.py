#
# colorrecord.py
#
# Copyright © 2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Color Records (subtables of CPAL tables).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------
#
# Classes
#

class ColorRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing RGBA colors. These are simple objects with 4
    attributes: red, green, blue, and alpha.

    >>> _testingValues[2].pprint()
    Red: 111
    Green: 222
    Blue: 123
    Alpha: 234
    """
    
    #
    # Class definition variables
    #

    attrSpec = dict(
        alpha = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Alpha"), 
        
        blue = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Blue"),

        green = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Green"), 
    
        red = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Red")) 

    attrSorted = ('red', 'green', 'blue', 'alpha')

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        >>> h = utilities.hexdumpString
        >>> print(h(_testingValues[1].binaryString()), end='')
               0 |1122 3344                                |."3D            |
        >>> print(h(_testingValues[2].binaryString()), end='')
               0 |7BDE 6FEA                                |{.o.            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        # NOTE: BGRA order!
        w.add("B", self.blue)
        w.add("B", self.green)
        w.add("B", self.red)
        w.add("B", self.alpha)

                
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new ColorRecord object.
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("test")
        >>> obj = ColorRecord.fromvalidatedbytes(s, logger=logger)
        test.colorrecord - DEBUG - Walker has 4 remaining bytes.
        test.colorrecord - INFO - ColorRecord RGBA(51, 34, 17, 68)
        >>> s = b"xxx"
        >>> obj = ColorRecord.fromvalidatedbytes(s, logger=logger)
        test.colorrecord - DEBUG - Walker has 3 remaining bytes.
        test.colorrecord - ERROR - Insufficient bytes for ColorRecord.
        """

        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('colorrecord')
        else:
            logger = logger.getChild('colorrecord')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes for ColorRecord."))
            
            return None

        b, g, r, a = w.unpack("4B")

        logger.info((
          'Vxxxx',
          (r, g, b, a),
          "ColorRecord RGBA(%d, %d, %d, %d)"))

        rv = cls(red=r, green=g, blue=b, alpha=a)
        return rv
       
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new colorRecord object from the specified walker.

        >>> s = _testingValues[1].binaryString()
        >>> obj = ColorRecord.frombytes(s)
        >>> obj == _testingValues[1]
        True
        """
        
        if w.length() < 4:            
            return None

        b, g, r, a = w.unpack("4B")
        rv = cls(red=r, green=g, blue=b, alpha=a)
        return rv
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

    _c1 = ColorRecord (
                blue=0x11,
                green=0x22,
                red=0x33,
                alpha=0x44)

    _c2 = ColorRecord (
                red=111,
                green=222,
                blue=123,
                alpha=234)

    _testingValues = (
        ColorRecord(),
        _c1,
        _c2,
        )

def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()
