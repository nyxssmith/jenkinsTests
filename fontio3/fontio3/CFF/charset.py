#
# charset.py
#
# Copyright © 2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF Charsets.
"""

# System imports
import logging

# Other imports
from fontio3.CFF import charsets_f0, charsets_f1, charsets_f2, charsets_predefined
from fontio3.CFF.cffutils import stdStrings, nStdStrings, dStdStrings
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_workClasses = {
    0: charsets_f0.Format0,
    1: charsets_f1.Format1,
    2: charsets_f2.Format2}


# -----------------------------------------------------------------------------

#
# Classes
#

class Charset(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing CFF Charsets, a mapping of glyphID to fully-resolved glyph name strings.
    """
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        map_compactremovesfalses = True,
        item_pprintlabelpresort = True)
        
    attrSpec = dict(
        originalFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
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
        Like fromwalker(), this method returns a new Charset. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).

        >>> l = utilities.makeDoctestLogger("test")
        >>> b = utilities.fromhex(_testingData[2])
        >>> Charset.fromvalidatedbytes(b, nGlyphs=4, logger=l)
        test.charset - DEBUG - Walker has 7 remaining bytes.
        test.charset - ERROR - Invalid format (0x00FF).
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
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return None

        workObj = _workClasses[format].fromvalidatedwalker(
            w,
            logger = logger,
            **kwArgs)
            
        if workObj is None: return None

        return cls(workObj, originalFormat=format)
    

    @classmethod
    def fromvalidatednumber(cls, n, **kwArgs):
        """
        Like fromnumber, fromvalidatednumber returns a Charset, using one of the
        3 predefined identifiers. It also performs validation using a logger.
        """
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('charset')
        else:
            logger = logger.getChild('charset')

        d = charsets_predefined.Predefined.fromvalidatednumber(n, logger=logger, **kwArgs)
        return cls(d, predefinedCharset=n)


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initialize Charset data from the stored format from the specified walker.

        >>> b = utilities.fromhex(_testingData[0])
        >>> Charset.frombytes(b, nGlyphs=4).pprint()
        0: .notdef
        1: space
        2: dollar
        3: parenleft
        """
        
        format = w.unpack("B", advance=False)
        workObj = _workClasses[format].fromwalker(w, **kwArgs)
        return cls(workObj, originalFormat=format)


    @classmethod
    def fromnumber(cls, n, **kwArgs):
        """
        Returns a Charset based on a number (one of the 3 Predefined charsets:
        ISOAdobe (0), Expert (1), or Expert Subset (2).
        """
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('charset')
        else:
            logger = logger.getChild('charset')

        d = charsets_predefined.Predefined.fromnumber(n, **kwArgs)
        return cls(d, predefinedCharset=n)

    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Call buildBinary using the appropriate originalFormat method.
        
        >>> print(utilities.hexdumpString(_testingValues[1].binaryString()), end='')
               0 |0000 2300 24                             |..#.$           |
        """
        
        if self.originalFormat is not None:
            c=_workClasses[self.originalFormat]
            c(self).buildBinary(w, **kwArgs)


    def getReverseMap(self):
        """
        Returns a dictionary mapping in the reverse direction (i.e. name to
        glyphID).
        """
        
        r = {}
        
        for gid,gname in self.items():
            r[gname] = gid
        
        return r


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
        Charset(originalFormat=0),
        Charset({0: 'A', 1: 'B', 2: 'C'}, originalFormat=0))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

