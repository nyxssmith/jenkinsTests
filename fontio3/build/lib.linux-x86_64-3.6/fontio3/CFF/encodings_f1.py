#
# encodings_f1.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 1 CFF Encodings.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import span

# -----------------------------------------------------------------------------

#
# Classes
#

class Format1(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing Format 1 CFF Encodings (code-to-glyph mappings).
    """
    
    mapSpec = dict(
        item_renumberdirectvalues = True,
        map_compactremovesfalses = True)
    
    
    #
    # Initialization and class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Format0. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.CFF')
        >>> obj = Format1.fromvalidatedbytes(utilities.fromhex(_testingData[0]), logger=logger)
        test.CFF.encodings.format1 - DEBUG - Walker has 4 remaining bytes.
        test.CFF.encodings.format1 - INFO - Format1 Encoding.
        test.CFF.encodings.format1 - INFO - 1 ranges.
        >>> obj == _testingValues[0]
        True
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('encodings.format1')
        else:
            logger = logger.getChild('encodings.format1')
        
        byteLength = w.length()
        logger.debug(('V0001', (byteLength,), "Walker has %d remaining bytes."))
        
        if byteLength < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, nRanges = w.unpack("2B")
        
        if format != 1:
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return None
        
        logger.info(('V0868', (), "Format1 Encoding."))

        r = cls()

        if nRanges:
            logger.info(('V0869', (nRanges,), "%d ranges."))
        else:
            logger.warning(('V0870', (), "Encoding does not map any ranges."))
            return r

        g = 0
        for i in range(nRanges):
            first, nLeft = w.unpack("2B")
            for c in range(first, first + nLeft + 1):
                r[c] = g
                g += 1

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initialize from the data in the subtable the specified StringWalker
        currently points to.
        
        >>> obj = Format1.frombytes(utilities.fromhex(_testingData[0]))
        >>> obj.pprint()
        51: 0
        52: 1
        53: 2
        54: 3
        55: 4
        """
        
        format, nRanges = w.unpack("2B")
        
        r = cls()

        g = 0
        for i in range(nRanges):
            first, nLeft = w.unpack("2B")
            for c in range(first, first + nLeft + 1):
                r[c] = g
                g += 1
                
        return r

    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format0 object to the specified
        LinkedWriter.
        
        >>> _testingValues[0].binaryString() == utilities.fromhex(_testingData[0])
        True
        >>> print(utilities.hexdumpString(_testingValues[0].binaryString()), end='')
               0 |0101 3304                                |..3.            |
        >>> print(utilities.hexdumpString(_testingValues[1].binaryString()), end='')
               0 |0104 0A03 6401 C800  DC00                |....d.....      |
        """
            
        contigRanges = span.Span(self)
        
        w.add("B", 1) # format
        w.add("B", len(contigRanges))
        
        pairsList = sorted(contigRanges.asPairsList())
        for i, flPair in enumerate(pairsList):
            first = flPair[0]
            nCodes = flPair[1] - first
            if i == 0:
                if self[first] != 0: raise ValueError("First entry of first range does not map to glyph zero!")
            w.add("B", first)
            w.add("B", nCodes)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import pp
    
    _testingData = (
        "01 01 33 04",
        "01 00 FF") 
    
    _testingValues = (
        Format1({51:0, 52:1, 53:2, 54:3, 55:4}),
        Format1({10:0, 11:1, 12:2, 13:3, 100:4, 101:5, 200:6, 220:7}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

