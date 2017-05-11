#
# fdselect_f0.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Format 0 FDSelect structures.
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

class Format0(dict, metaclass=mapmeta.FontDataMetaclass):
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
        Like fromwalker, fromvalidatedwalker returns a list of FD identifiers
        from a format 0 FDSelect structure. However, it also does validation via
        the logging module (the client should have done a logging.basicConfig
        call prior to calling this method, unless a logger is passed in via the
        'logger' keyword argument).
        
        >>> logger=utilities.makeDoctestLogger("test")
        >>> Format0.fromvalidatedbytes(_testingData[0], nGlyphs=5, logger=logger)
        test.fdselect_format0 - DEBUG - Walker has 6 remaining bytes.
        Format0({0: 255, 1: 254, 2: 255, 3: 254, 4: 1})
        >>> Format0.fromvalidatedbytes(_testingData[0], nGlyphs=7, logger=logger)
        test.fdselect_format0 - DEBUG - Walker has 6 remaining bytes.
        test.fdselect_format0 - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('fdselect_format0')
        else:
            logger = logger.getChild('fdselect_format0')
            
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))

        format = w.unpack("B")
        if format != 0:
            logger.error(('xxxxx', (format,), "Format is %d, expected 0."))
            return None

        nGlyphs = kwArgs.pop('nGlyphs')
        if w.length() < nGlyphs:
            logger.error(('xxxxx', (), "Insufficient bytes."))
            return None
        fds = w.group("B", nGlyphs)
        d = {g:fds[g] for g in range(nGlyphs)}

        return cls(d)

    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a list of FD identifiers from a format 0 FDSelect structure. The
        'nGlyphs' kwArg is required.
        
        >>> Format0.frombytes(_testingData[0], nGlyphs=5)
        Format0({0: 255, 1: 254, 2: 255, 3: 254, 4: 1})
        """

        format = w.unpack("B")
        nGlyphs = kwArgs.pop('nGlyphs')
        fds = w.group("B", nGlyphs)
        d = {g:fds[g] for g in range(nGlyphs)}

        return cls(d)
            
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format 0 FDSelect object to the specified
        LinkedWriter.
        
        >>> print(utilities.hexdumpString(_testingValues[1].binaryString()), end='')
               0 |0000 0000 0101 0102  0202                |..........      |
        """

        w.add("B", 0) # format
        fdkeys = sorted([x for x in self if isinstance(x, int)])
        w.addGroup("B", [self[k] for k in fdkeys])

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingData = (utilities.fromhex("00 FF FE FF FE 01"),)

    _testingValues = (
        Format0(),
        Format0({3:1, 4:1, 5:1, 6:2, 7:2, 8:2, 0:0, 1:0, 2:0}, nGlyphs=9),
        Format0.frombytes(_testingData[0], nGlyphs=5))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

