#
# palette.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Palettes (subtables of CPAL tables).
"""

# System imports
import logging

# Other imports
from fontio3.CPAL import colorrecord
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------
#
# Classes
#

class Palette(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing CPAL Palettes. These are maps of entry indices to
    ColorRecords. There are 4 attributes:
        red     Red value
        green   Green value
        blue    Blue value
        alpha   Alpha value
        
    Note that even though we refer to these in the more common "RGBA" term, the
    binary is actually stored in BGRA order.

    >>> _testingValues[0].pprint()
    0: Red = 0, Green = 0, Blue = 0, Alpha = 0
    1: Red = 51, Green = 34, Blue = 17, Alpha = 68
    """

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. There is one
        required kwArg, numPalettesEntries, which is used as the output count,
        regardless of our own actual count. Any missing keys will be filled
        with zeroed ColorRecords, and any extra keys will not be included.

        >>> h = utilities.hexdumpString
        >>> tv0 = _testingValues[0]
        >>> print(h(tv0.binaryString(numPalettesEntries=2)), end='')
               0 |0000 0000 1122 3344                      |....."3D        |
        >>> print(h(tv0.binaryString(numPalettesEntries=4)), end='')
               0 |0000 0000 1122 3344  0000 0000 0000 0000 |....."3D........|
        """

        numPalettesEntries = kwArgs.pop('numPalettesEntries')

        for recidx in range(numPalettesEntries):
            rec = self.get(recidx, colorrecord.ColorRecord())
            rec.buildBinary(w, **kwArgs)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Palette object. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword argument).

        kwArg 'numPalettesEntries' is required.

        >>> s = _testingValues[0].binaryString(numPalettesEntries=2)
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Palette.fromvalidatedbytes
        >>> obj = fvb(s, numPalettesEntries=2, logger=logger)
        test.palette - DEBUG - Walker has 8 remaining bytes.
        test.palette.colorrecord - DEBUG - Walker has 8 remaining bytes.
        test.palette.colorrecord - INFO - ColorRecord RGBA(0, 0, 0, 0)
        test.palette.colorrecord - DEBUG - Walker has 4 remaining bytes.
        test.palette.colorrecord - INFO - ColorRecord RGBA(51, 34, 17, 68)
        >>> obj == _testingValues[0]
        True
        >>> obj = fvb(s, numPalettesEntries=5, logger=logger)
        test.palette - DEBUG - Walker has 8 remaining bytes.
        test.palette - ERROR - Insufficient bytes for Palette of count 5.
        """

        logger = kwArgs.pop('logger', None)
        numPalettesEntries = kwArgs.pop('numPalettesEntries')

        if logger is None:
            logger = logging.getLogger().getChild('palette')
        else:
            logger = logger.getChild('palette')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < numPalettesEntries * 4:
            logger.error((
              'V0004',
              (numPalettesEntries,),
              "Insufficient bytes for Palette of count %d."))

            return None

        r = cls()

        fvw = colorrecord.ColorRecord.fromvalidatedwalker

        for i in range(numPalettesEntries):
            r[i] = fvw(w, logger=logger, **kwArgs)

        return r


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new colorRecord object from the specified walker.

        >>> s = _testingValues[0].binaryString(numPalettesEntries=2)
        >>> obj = Palette.frombytes(s, numPalettesEntries=2)
        >>> obj == _testingValues[0]
        True
        """

        numPalettesEntries = kwArgs.pop('numPalettesEntries')

        r = cls()

        fw = colorrecord.ColorRecord.fromwalker

        for i in range(numPalettesEntries):
            r[i] = fw(w, **kwArgs)

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
        Palette({
          0: colorrecord._testingValues[0],
          1: colorrecord._testingValues[1]}),
        Palette({0: colorrecord._testingValues[1]}),
        Palette(),
        )

def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

