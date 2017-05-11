#
# charsets_f2.py
#
# Copyright © 2012, 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 CFF Charsets.
"""

# System imports
import logging

# Other imports
from fontio3.CFF.cffutils import stdStrings, dStdStrings, nStdStrings
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Format2(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing Format 2 CFF Charsets (glyphID-to-character
    [glyphname] mappings).
    """
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        map_compactremovesfalses = True,
        item_pprintlabelpresort = True)

    attrSpec = dict(
        originalFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: 2),
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
        Like fromwalker(), this method returns a new Format2. However,
        it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to
        calling this method, unless a logger is passed in via the
        'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> fvb = Format2.fromvalidatedbytes
        >>> obj = fvb(utilities.fromhex(_testingData[1]), logger=logger, nGlyphs=5)
        test.format2 - DEBUG - Walker has 4 remaining bytes.
        test.format2 - DEBUG - nCodes: 5
        test.format2 - DEBUG - first: 5, nLeft: 3
        test.format2 - INFO - 5 codes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format2')
        else:
            logger = logger.getChild('format2')
            
        format = w.unpack("B")
        
        if format != 2:
            logger.error(('V0002', (format,), "Invalid format (%d)."))
            return None

        strings=kwArgs.get('strings')

        isCID=kwArgs.get('isCID', False)
        
        nCodes = kwArgs.get('nGlyphs', 0)
        
        byteLength = w.length()
        logger.debug(('V0001', (byteLength,), "Walker has %d remaining bytes."))

        if byteLength < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        logger.debug(('V0001', (nCodes,), "nCodes: %d"))
        
        charmap = {0:stdStrings[0]}
 
        while True:
            first, nLeft = w.unpack("HH") #  only difference between Format1 and Format2
            logger.debug(('V0001', (first, nLeft), "first: %d, nLeft: %d"))
            for c in range(first, first + nLeft + 1):
                if isCID:
                    s = "CID%d" % (c,)
                else:
                    if c >= nStdStrings:
                        if c-nStdStrings >= len(strings):
                            logger.error(('V0872', 
                              (c-nStdStrings,len(strings)), 
                              "Non-standard SID index %d out of range (%d)"))
                            s="OutOfRange_%d" % (c,)
                        else:
                            s = strings[c-nStdStrings]
                    else:
                        s = stdStrings[c]

                charmap[len(charmap)] = s
                
            if len(charmap) >= nCodes : break

        logger.info(('V0873', (len(charmap),), "%d codes."))

        return cls(charmap)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initialize from the data in the subtable the specified StringWalker
        currently points to.
        
        >>> obj = Format2.frombytes(utilities.fromhex(_testingData[1]))
        >>> obj.pprint()
        0: .notdef
        1: dollar
        2: percent
        3: ampersand
        4: quoteright
        originalFormat: 2
        """
        
        format = w.unpack("B")
        strings=kwArgs.get('strings')
        isCID=kwArgs.get('isCID', False)
        nCodes = kwArgs.get('nGlyphs', 0)

        charmap = {0:stdStrings[0]}

        while True:
            first, nLeft = w.unpack("HH")
            for c in range(first, first + nLeft + 1):
                if isCID:
                    s = "CID%d" % (c,)
                else:
                    if c >= nStdStrings:
                        s = strings[c-nStdStrings]
                    else:
                        s = stdStrings[c]

                charmap[len(charmap)] = s
                
            if len(charmap) >= nCodes : break

        return cls(charmap)                
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format0 object to the specified
        LinkedWriter. If any keys or values do not fit in a single byte, a
        ValueError is raised.
        
        >>> _testingValues[1].binaryString() == utilities.fromhex(_testingData[1])
        True
        >>> print(utilities.hexdumpString(_testingValues[1].binaryString()), end='')
               0 |0200 0500 03                             |.....           |
        >>> print(utilities.hexdumpString(_testingValues[2].binaryString(strings=["customName"])), end='')
               0 |0200 0700 0000 0500  0001 8700 00        |.............   |
        """

        strings = kwArgs.get('strings', [])
        w.add("B", 2) #format
        gids = sorted(self)
        gids.pop(0) # assumed/required mapping to .notdef
        nextinrange = 0
        rangecount = -1
        for g in gids:
            sidx = dStdStrings.get(self[g], None)
            if sidx is None:
                if self[g][0:3] == "CID":
                    sidx = int(self[g][3:])
                else:
                    sidx = strings.index(self[g]) + nStdStrings

            if sidx != nextinrange:
                if rangecount != -1:
                    w.add("H", rangecount) # close previous range, except on initial
                w.add("H", sidx) # start new range
                rangecount = 0
                nextinrange = sidx + 1
            else:
                rangecount += 1
                nextinrange += 1
        w.add("H", rangecount) # close final range
        

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
        "02 00 01 00 FF",
        "02 00 05 00 03")
    
    _testingValues = (
        Format2(),
        Format2({0:stdStrings[0], 1:stdStrings[5], 2:stdStrings[6], 3:stdStrings[7], 4:stdStrings[8]}),
        Format2({0:stdStrings[0], 1:stdStrings[7], 2:stdStrings[5], 3:"customName"}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

