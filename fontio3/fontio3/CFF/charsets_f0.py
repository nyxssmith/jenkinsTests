#
# charsets_f0.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 0 CFF Charsets.
"""

# System imports
import logging

# Other imports
from fontio3.CFF.cffutils import stdStrings, nStdStrings, dStdStrings
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Format0(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing Format 0 CFF Charsets.
    """
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        map_compactremovesfalses = True,
        item_pprintlabelpresort = True)
    
    attrSpec = dict(
        originalFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: 0),
            attr_showonlyiftrue = True),
        predefinedCharset = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True))
    
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
        >>> b = utilities.fromhex(_testingData[0])
        >>> obj = Format0.fromvalidatedbytes(b, nGlyphs=4, logger=logger)
        test.format0 - DEBUG - Walker has 7 remaining bytes.
        test.format0 - INFO - 3 codes.
        >>> b = utilities.fromhex(_testingData[1])
        >>> obj = Format0.fromvalidatedbytes(b, nGlyphs=9, logger=logger, strings=['test'])
        test.format0 - DEBUG - Walker has 11 remaining bytes.
        test.format0 - INFO - 8 codes.
        test.format0 - ERROR - Insufficient bytes.
        test.format0 - ERROR - SID 1315 out of range
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format0')
        else:
            logger = logger.getChild('format0')
        
        strings = kwArgs.get('strings', None)
        
        byteLength = w.length()
        logger.debug(('V0001', (byteLength,), "Walker has %d remaining bytes."))
        
        if byteLength < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("B")
        
        if format != 0:
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return None

        nCodes = kwArgs.get('nGlyphs', 1) - 1
        if nCodes < 0:
            logger.error(('V0871', (nCodes,), "Invalid number of codes for CFF Charsets (%d)."))
            return None

        isCID = kwArgs.get('isCID', False)

        logger.info(('V0873', (nCodes,), "%d codes."))
        
        charmap = {0: stdStrings[0]} # assumed
        
        if w.length() < nCodes * 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            nCodes = int(w.length()) // 2
        
        for k,v in enumerate(w.group("H", nCodes)):
            if isCID:
                charmap[k+1] = "CID%d" % (v,)
            else:
                if v < nStdStrings:
                    charmap[k+1] = stdStrings[v]
                else:
                    if v-nStdStrings < len(strings):
                        charmap[k+1] = strings[v-nStdStrings]
                    else:
                        logger.error(('V0872', (v,), "SID %d out of range"))
                        charmap[k+1] = "SID%d" % (v,)

        return cls(charmap)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Build a Format0 charset, mapping glyphID:glyphName from the specified Walker.
        
        >>> b = utilities.fromhex(_testingData[0])
        >>> obj = Format0.frombytes(b, nGlyphs=4)
        """
        
        strings = kwArgs.get('strings', [])
        
        format = w.unpack("B")
        
        if format != 0:
            raise ValueError("Invalid format (%d)" % (format,))

        nCodes = kwArgs.get('nGlyphs', 1) - 1

        isCID = kwArgs.get('isCID', False)

        charmap = {0: stdStrings[0]} # assumed
        for k,v in enumerate(w.group("H", nCodes)):
            if isCID:
                charmap[k+1] = "CID%d" % (v,)
            else:
                if v < nStdStrings:
                    charmap[k+1] = stdStrings[v]
                else:
                    charmap[k+1] = strings[v-nStdStrings]

        return cls(charmap)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format0 object to the specified
        LinkedWriter. If any keys or values do not fit in a single byte, a
        ValueError is raised.
        
        >>> obj = Format0.frombytes(utilities.fromhex(_testingData[0]), nGlyphs=4)
        >>> print(utilities.hexdumpString(obj.binaryString()), end='')
               0 |0000 0100 0500 09                        |.......         |
        """

        strings = kwArgs.get('strings', [])

        w.add("B", 0) #format
        gids = sorted(self)
        gids.pop(0) # assumed/required mapping to .notdef
        for g in gids:
            sidx = dStdStrings.get(self[g], None)
            if sidx is None:
                if self[g][0:3] == "CID":
                    sidx = int(self[g][3:])
                else:
                    sidx = strings.index(self[g]) + nStdStrings

            w.add("H", sidx)

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
        "00 00 01 00 05 00 09",
        "00 05 23 01 87 00 02 00 03 00 04")

    _testingValues = (
        Format0(),
        Format0({0: 'A', 1: 'B', 2: 'C'}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

