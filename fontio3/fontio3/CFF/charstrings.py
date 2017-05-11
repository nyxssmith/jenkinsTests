#
# charstrings.py
#
# Copyright © 2014-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF CharStrings (INDEX).
"""

# System imports
import logging

# Other imports
from fontio3.CFF import cffindex
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class CharStrings(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing CFF CharStrings (INDEX), a mapping of glyphID
    to glyph charstrings (outlines & hint descriptions; "the glyph data").
    """
    
    mapSpec = dict(
        item_pprintlabelpresort = True,
        item_renumberdirectkeys = True,
        map_compactremovesfalses = True)

    #
    # Methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new CharStrings. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).

        >>> l = utilities.makeDoctestLogger("test")
        >>> fvb = CharStrings.fromvalidatedbytes
        >>> b = utilities.fromhex(_testingData[0])
        >>> obj=fvb(b, logger=l)
        test.charstrings.INDEX - DEBUG - Walker has 8 remaining bytes.
        test.charstrings.INDEX - INFO - INDEX count: 2
        test.charstrings.INDEX - DEBUG - offSize = 1
        >>> b = utilities.fromhex(_testingData[1])
        >>> fvb(b, logger=l)
        test.charstrings.INDEX - DEBUG - Walker has 8 remaining bytes.
        test.charstrings.INDEX - INFO - INDEX count: 255
        test.charstrings.INDEX - DEBUG - offSize = 1
        test.charstrings.INDEX - ERROR - INDEX length too short for count.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('charstrings')
        else:
            logger = logger.getChild('charstrings')

        rawidx = cffindex.fromvalidatedwalker(w, logger=logger, asDict=True)

        if rawidx:
            return cls(rawidx)
        else:
            return None    

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initialize CharStrings data from the stored INDEX structure as a dict.
        >>> fb = CharStrings.frombytes
        >>> b = utilities.fromhex(_testingData[0])
        >>> obj = fb(b)
        >>> len(obj)
        2
        """
        
        rawidx = cffindex.fromwalker(w, asDict=True)

        return cls(rawidx)
    
    def buildBinary(self, w, **kwArgs):
        """
        Add the binary CharStrings INDEX data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0101 0203 0E0E                      |........        |
        """
        
        cffindex.buildBinary(self, w, fromDict=True)

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
        "00 02 01 01 02 03 0e 0e",
        "00 FF 01 01 02 03 0e 0e")

    _testingValues = (
        CharStrings(),
        CharStrings({0: b'\x0E', 1: b'\x0E'}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

