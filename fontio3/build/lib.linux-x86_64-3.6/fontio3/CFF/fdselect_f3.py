#
# fdselect_f3.py
#
# Copyright © 2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Format 3 FDSelect structures.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Format3(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Map of glyphID-to-FontDict.
    """
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        map_compactremovesfalses = True,
        map_validatefunc = _validate)
        
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker, fromvalidatedwalker returns a mapping of
        glyphIDs to FontDicts from a format 3 FDSelect structure.
        However, it also does validation via the logging module (the
        client should have done a logging.basicConfig call prior to
        calling this method, unless a logger is passed in via the
        'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Format3.fromvalidatedbytes
        >>> fvb(_testingData[0], logger=logger)
        test.fdselect_format3 - DEBUG - Walker has 14 remaining bytes.
        test.fdselect_format3 - INFO - 3 ranges.
        Format3({0: 255, 1: 255, 2: 255, 3: 255, 4: 255, 5: 254, 6: 254, 7: 250})

        >>> fvb(_testingData[1], logger=logger)
        test.fdselect_format3 - DEBUG - Walker has 10 remaining bytes.
        test.fdselect_format3 - ERROR - Insufficient bytes.

        >>> fvb(_testingData[2], logger=logger)
        test.fdselect_format3 - DEBUG - Walker has 5 remaining bytes.
        test.fdselect_format3 - ERROR - Insufficient bytes.

        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('fdselect_format3')
        else:
            logger = logger.getChild('fdselect_format3')
            
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))

        format = w.unpack("B")
        nRanges = w.unpack("H")
        
        if w.length() < (nRanges * 3) + 2:
            logger.error(('xxxxx', (), "Insufficient bytes."))
            return None
        
        ranges = list(w.group("HB", nRanges))
        logger.info(('xxxxx', (len(ranges),), "%d ranges."))

        if w.length() < 1:
            logger.error(('xxxxx', (), "Insufficient bytes."))
            return None
        
        ranges.append( (w.unpack("H"), 0) ) # sentinel

        fds = cls()
        for r in range(len(ranges) - 1):
            for g in range(ranges[r][0], ranges[r+1][0]):
                fds[g] = ranges[r][1]
                        
        return fds

    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a list of FD identifiers from a format 3 FDSelect structure.
        
        >>> obj = Format3.frombytes(_testingData[0])
        >>> sorted(_testingValues[1]) == sorted(obj)
        True
        """

        format = w.unpack("B")
        nRanges = w.unpack("H")
        ranges = list(w.group("HB", nRanges))
        ranges.append( (w.unpack("H"), 0) ) # sentinel
        
        fds = cls()
        for r in range(len(ranges) - 1):
            for g in range(ranges[r][0], ranges[r+1][0]):
                fds[g] = ranges[r][1]
                        
        return fds
            
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format 3 FDSelect object to the specified
        LinkedWriter.
        
        >>> print(utilities.hexdumpString(_testingValues[1].binaryString()), end='')
               0 |0300 0300 00FF 0005  FE00 07FA 0008      |..............  |
        """

        w.add("B", 3) # format
        nRangesTag = w.addDeferredValue("H")
        sortedIntKeys = sorted([x for x in self if isinstance(x, int)])
        g = 0
        nRanges = 0
        
        while True:
            nRanges += 1
            w.add("HB", g, self[g])
            g += 1

            if g >= len(sortedIntKeys): break

            while self[g] == self[g-1]:
                g += 1
                if g >= len(sortedIntKeys): break

            if g >= len(sortedIntKeys): break

        w.setDeferredValue(nRangesTag, "H", nRanges)
        w.add("H", sortedIntKeys[-1] + 1) # sentinel == nGlyphs
            
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingData = (
      utilities.fromhex("03 00 03 00 00 FF 00 05 FE 00 07 FA 00 08"),
      utilities.fromhex("03 00 02 00 00 FF 00 05 FE 00"),
      utilities.fromhex("03 00 02 FF FF"))

    _testingValues = (
        Format3(),
        Format3({4: 255, 1: 255, 0: 255, 2: 255, 3: 255, 5: 254, 6: 254, 7:250}),
        Format3.frombytes(_testingData[0]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

