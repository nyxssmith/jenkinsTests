#
# layer.py
#
# Copyright © 2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#
#

"""
Support for COLR table Layer objects.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------
#
# Classes
#


class Layer(object, metaclass=simplemeta.FontDataMetaclass):
    """
    A Layer is a simple object with 2 attributes:
        glyphIndex      Glyph index of the layer
        paletteIndex    Index into CPAL palette
    
    >>> _testingValues[1].pprint()
    glyphIndex: 8
    paletteIndex: 16
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        glyphIndex=dict(
            attr_initfunc = (lambda: 0),
            attr_renumberdirect = True),
        
        paletteIndex=dict(
            attr_initfunc = (lambda: 0)))

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.

        >>> h = utilities.hexdumpString
        >>> print(h(_testingValues[1].binaryString()), end='')
               0 |0008 0010                                |....            |
        """
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("H", self.glyphIndex)
        w.add("H", self.paletteIndex)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Layer object. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' kwArg).

        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("test")
        >>> obj = Layer.fromvalidatedbytes(s, logger=logger)
        test.layer - DEBUG - Walker has 4 remaining bytes.
        test.layer - INFO - Glyph 8: palette index 16
        """
        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('layer')
        else:
            logger = logger.getChild('layer')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 4:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes for Layer"))

            return None

        gid, pid = w.unpack("2H")

        logger.info((
          'V1003',
          (gid, pid),
          "Glyph %d: palette index %d"))

        r = cls(glyphIndex=gid, paletteIndex=pid)

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Layer object from the specified walker.

        >>> s = _testingValues[1].binaryString()
        >>> _testingValues[1] == Layer.frombytes(s)
        True
        """

        gid, pid = w.unpack("2H")

        r = cls(glyphIndex=gid, paletteIndex=pid)

        return r


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

    _testingValues = (
        Layer(glyphIndex=21, paletteIndex=45),
        Layer(glyphIndex=8, paletteIndex=16),
        Layer())


def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

