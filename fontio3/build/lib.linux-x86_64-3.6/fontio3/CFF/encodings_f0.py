#
# encodings_f0.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 0 CFF Encodings.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Format0(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing Format 0 CFF Encodings (code-to-glyph mappings).
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
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> obj = Format0.fromvalidatedbytes(utilities.fromhex(_testingData[0]), logger=logger)
        test.encodings.format0 - DEBUG - Walker has 7 remaining bytes.
        test.encodings.format0 - INFO - Format0 Encoding.
        test.encodings.format0 - INFO - 5 codes.

        >>> obj = Format0.fromvalidatedbytes(utilities.fromhex(_testingData[1]), logger=logger)
        test.encodings.format0 - DEBUG - Walker has 2 remaining bytes.
        test.encodings.format0 - INFO - Format0 Encoding.
        test.encodings.format0 - ERROR - Invalid number of codes for CFF Encoding (0).
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('encodings.format0')
        else:
            logger = logger.getChild('encodings.format0')
        
        byteLength = w.length()
        logger.debug(('V0001', (byteLength,), "Walker has %d remaining bytes."))
        
        if byteLength < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, nCodes = w.unpack("2B")
        
        if format != 0:
            logger.error(('V0002', (format,), "Invalid format (%d)."))
            return None
        
        logger.info(('V0868', (), "Format0 Encoding."))

        if nCodes < 1:
            logger.error(('V0871', (nCodes,), "Invalid number of codes for CFF Encoding (%d)."))
            return None
        
        logger.info(('V0869', (nCodes,), "%d codes."))

        r = cls()
        mapCount = 0
        
        for glyph, code in enumerate(w.group("B", nCodes)):
            r[code] = glyph
            mapCount += 1

#         if not mapCount:
#             logger.warning(('V0006', (), "All characters were mapped to the missing glyph."))
#         else:
#             logger.info(('V0007', (mapCount, 256 - mapCount), "%d character(s) mapped, %d unmapped"))
#         
#         t = (len(set(r)), len(set(r.itervalues())))
#         logger.info(('V0008', t, "%d unique character codes mapped to %d unique glyphs."))
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initialize from the data in the subtable the specified StringWalker
        currently points to.
        
        >>> obj = Format0.frombytes(utilities.fromhex(_testingData[0]))
        >>> obj.pprint()
        1: 0
        2: 1
        3: 2
        4: 3
        5: 4
        """
        
        format, nCodes = w.unpack("2B")
        r = cls()
        for glyph, code in enumerate(w.group("B", nCodes)):
            r[code] = glyph
            
        return r
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format0 object to the specified
        LinkedWriter. If any keys or values do not fit in a single byte, a
        ValueError is raised.
        
        >>> print(utilities.hexdumpString(_testingValues[0].binaryString()), end='')
               0 |0005 0102 0304 05                        |.......         |
        >>> _testingValues[0].binaryString() == utilities.fromhex(_testingData[0])
        True
        """

        glyphToCodeMap = {v:k for [v,k] in list(self.items())}

        w.add("B", 0) # format
        w.add("B", len(self)) # nCodes
        for g in sorted(glyphToCodeMap):
            w.add("B", glyphToCodeMap[g])
        

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
        "00 05 01 02 03 04 05",
        "00 00")
    
    _testingValues = (
        Format0( {0:1, 1:2, 2:3, 3:4, 4:5} ),
        Format0({}) )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

