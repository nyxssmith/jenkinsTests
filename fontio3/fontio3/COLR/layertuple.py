#
# layertuple.py
#
# Copyright © 2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#
#

"""
Tuples of COLR table layer information.
"""

# System imports
import logging

# Other imports
from fontio3.COLR import layer
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------
#
# Classes
#


class LayerTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    A LayerTuple is a sequence of Layers.

    >>> _testingValues[1].pprint()
    0: glyphIndex = 8, paletteIndex = 16
    1: glyphIndex = 21, paletteIndex = 45
    2: glyphIndex = 8, paletteIndex = 16
    """

    #
    # Class definition variables
    #
    
    objSpec = dict(
        item_followsprotocol = True)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.

        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0008 0010 0015 002D  0008 0010           |.......-....    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        for lyr in self:
            lyr.buildBinary(w, **kwArgs)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new LayerTuple object.
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).

        The 'numLayers' kwArg is required.

        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("test")
        >>> obj = LayerTuple.fromvalidatedbytes(s, numLayers=2, logger=logger)
        test.layertuple - DEBUG - Walker has 8 remaining bytes.
        test.layertuple.layer - DEBUG - Walker has 8 remaining bytes.
        test.layertuple.layer - INFO - Glyph 21: palette index 45
        test.layertuple.layer - DEBUG - Walker has 4 remaining bytes.
        test.layertuple.layer - INFO - Glyph 8: palette index 16
        >>> obj == _testingValues[0]
        True
        """
        logger = kwArgs.pop('logger', None)
        numLayers = kwArgs.pop('numLayers')

        if logger is None:
            logger = logging.getLogger().getChild('layertuple')
        else:
            logger = logger.getChild('layertuple')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < numLayers * 4:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes for LayerTuple."))

            return None

        fvw = layer.Layer.fromvalidatedwalker
        r = cls([fvw(w, logger=logger, **kwArgs) for _ in range(numLayers)])

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Layer object from the specified walker.

        The 'numLayers' kwArg is required.

        >>> s = _testingValues[0].binaryString()
        >>> _testingValues[0] == LayerTuple.frombytes(s, numLayers=2)
        True
        """

        numLayers = kwArgs.pop('numLayers')
        fw = layer.Layer.fromwalker
        r = cls([fw(w, **kwArgs) for _ in range(numLayers)])
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
        LayerTuple([
          layer._testingValues[0],
          layer._testingValues[1]]),
        LayerTuple([
          layer._testingValues[1],
          layer._testingValues[0],
          layer._testingValues[1]]),
        LayerTuple(),
        )


def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

