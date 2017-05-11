#
# fdselect.py
#
# Copyright © 2013-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF FDSelects.
"""

# System imports
import logging

# Other imports
from fontio3.CFF import fdselect_f0, fdselect_f3
#from fontio3.CFF.cffutils import stdStrings, nStdStrings, dStdStrings
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_workClasses = {
    0: fdselect_f0.Format0,
    3: fdselect_f3.Format3}


# -----------------------------------------------------------------------------

#
# Classes
#

class FDSelect(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing CFF FDSelects, a mapping of glyphs to FontDict
    indices.
    """
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        map_compactremovesfalses = True,
        item_pprintlabelpresort = True)
        
    attrSpec = dict(
        originalFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True))

    #
    # Initialization and class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new FDSelect. However,
        it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to
        calling this method, unless a logger is passed in via the
        'logger' keyword argument).

        >>> l = utilities.makeDoctestLogger("test")
        >>> b = utilities.fromhex(_testingData[2])
        >>> FDSelect.fromvalidatedbytes(b, nGlyphs=4, logger=l)
        test.charset - DEBUG - Walker has 7 remaining bytes.
        test.charset - ERROR - Invalid format (0xFF).
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('charset')
        else:
            logger = logger.getChild('charset')

        byteLength = w.length()
        logger.debug(('V0001', (byteLength,), "Walker has %d remaining bytes."))
        
        if byteLength < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("B", advance=False)
        
        if format not in _workClasses:
            logger.error(('V0002', (format,), "Invalid format (0x%02X)."))
            return None

        workObj = _workClasses[format].fromvalidatedwalker(
            w,
            logger = logger,
            **kwArgs)
            
        if workObj is None: return None

        return cls(workObj, originalFormat=format)
    

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initialize FDSelect data from the stored format from the
        specified walker.

        >>> b = utilities.fromhex(_testingData[0])
        >>> FDSelect.frombytes(b, nGlyphs=4)
        FDSelect({0: 0, 1: 1, 2: 0, 3: 5}, originalFormat=0)
        """
        
        format = w.unpack("B", advance=False)
        workObj = _workClasses[format].fromwalker(w, **kwArgs)
        return cls(workObj, originalFormat=format)

    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Call buildBinary using the appropriate originalFormat method.
        
        >>> print(utilities.hexdumpString(_testingValues[1].binaryString()), end='')
               0 |0001 0101 0202 02                        |.......         |
        >>> t = FDSelect({0: 0, 1: 1, 2: 0, 3: 1, 4:1, 5:1}, originalFormat=3)
        >>> print(utilities.hexdumpString(t.binaryString()), end='')
               0 |0300 0400 0000 0001  0100 0200 0003 0100 |................|
              10 |06                                       |.               |
        """
        
        if self.originalFormat is not None:
            c=_workClasses[self.originalFormat]
            c(self).buildBinary(w, **kwArgs)


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
        "00 05 23 01 87 00 02 00 03 00 04",
        "FF 00 01 00 05 00 09")

    _testingValues = (
        FDSelect(originalFormat=0),
        FDSelect({0: 1, 1:1, 2:1, 3:2, 4:2, 5:2}, originalFormat=0))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

