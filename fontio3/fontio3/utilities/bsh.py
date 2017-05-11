#
# bsh.py
#
# Copyright © 2004-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for reading and generating binary-search headers, as are used in
several places in TrueType.
"""

# System imports
import logging

# Other imports
from fontio3 import utilitiesbackend
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Constants
#

ERR_CODES = ('V0654', 'V0655', 'V0656')
ERR_STRINGS = ("searchRange", "entrySelector", "rangeShift")

# -----------------------------------------------------------------------------

#
# Functions
#

def binsearchheader(n, unitsize, **kwArgs):
    """
    Returns a string with 4 16-bit binary values: nUnits, searchRange,
    entrySelector and rangeShift.
    
    >>> utilities.hexdump(binsearchheader(200, 6))
           0 | 00C8 0300 0007 01B0                      |........        |
    
    >>> utilities.hexdump(binsearchheader(200, 6, use32Bits=True))
           0 | 0000 00C8 0000 0300  0000 0007 0000 01B0 |................|
    """
    
    kwArgs['skipUnitSize'] = True
    return BSH(nUnits=n, unitSize=unitsize).binaryString(**kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class BSH(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing binary-search headers. These are simple objects with
    two attributes, nUnits and unitSize. There are also three read-only
    properties: searchRange, entrySelector, and rangeShift.
    
    >>> bsh = BSH(nUnits=10, unitSize=6)
    >>> utilities.hexdump(bsh.binaryString())
           0 | 0006 000A 0030 0003  000C                |.....0....      |
    
    >>> bsh.nUnits = 11
    >>> utilities.hexdump(bsh.binaryString())
           0 | 0006 000B 0030 0003  0012                |.....0....      |
    
    >>> bsh.nUnits = 0
    >>> utilities.hexdump(bsh.binaryString())
           0 | 0006 0000 0006 0000  0000                |..........      |
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        unitSize = dict(
            attr_initfunc = (lambda: 2),
            attr_label = "Bytes per unit"),
    
        nUnits = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Number of units"),
        
        _cachedKey = dict(
            attr_ignoreforcomparisons = True),
        
        _cachedFields = dict(
            attr_ignoreforcomparisons = True))
    
    attrSorted = ('unitSize', 'nUnits')
        
    #
    # Methods
    #
    
    def _getEntrySelector(self):
        """
        >>> bsh = BSH(nUnits=10, unitSize=6)
        >>> print((bsh._getEntrySelector()))
        3
        """
        self._recalc()
        return self._cachedFields[1]
    
    def _getRangeShift(self):
        """
        >>> bsh = BSH(nUnits=10, unitSize=6)
        >>> print((bsh._getRangeShift()))
        12
        """
        self._recalc()
        return self._cachedFields[2]
    
    def _getSearchRange(self):
        """
        >>> bsh = BSH(nUnits=0, unitSize=6)
        >>> print((bsh._getSearchRange()))
        6
        """
        self._recalc()
        return self._cachedFields[0]
    
    entrySelector = property(_getEntrySelector)
    rangeShift = property(_getRangeShift)
    searchRange = property(_getSearchRange)
    
    def _recalc(self):
        """
        Recalculates (if necessary) the three derived fields of this binary
        search header.
        """
        
        k = (self.unitSize, self.nUnits)
        
        if k != self._cachedKey:
            # the following line uses an exceedingly hacky
            # way of computing the base 2 log!
            es = max(0, [k[1] < 2**x for x in range(32)].index(1) - 1)
            sr = (2 ** es) * k[0]
            rs = k[0] * max(0, k[1] - (2 ** es))
            self._cachedFields = (sr, es, rs)
            self._cachedKey = k
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the BSH object to the specified LinkedWriter.
        The following keyword arguments are optional:
        
            skipUnitSize    If True, the resulting binary data will only
                            comprise nUnits, searchRange, entrySelector, and
                            rangeShift. If False (the default), unitSize will
                            be included (first).
            
            use32Bits       Default is False. If True, all operations will use
                            32-bit words instead of 16-bit words.
        
        >>> d = {'use32Bits': True}
        >>> obj = _testingValues[1]
        >>> utilities.hexdump(obj.binaryString())
               0 | 0006 000A 0030 0003  000C                |.....0....      |
        
        >>> utilities.hexdump(obj.binaryString(**d))
               0 | 0000 0006 0000 000A  0000 0030 0000 0003 |...........0....|
              10 | 0000 000C                                |....            |
        """
        
        self._recalc()
        
        use32Bits = kwArgs.get('use32Bits', False)
        
        if not kwArgs.get('skipUnitSize', False):
            w.add(("L" if use32Bits else "H"), self.unitSize)
        
        w.add(("4L" if use32Bits else "4H"), self.nUnits, *self._cachedFields)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new BSH object from the specified walker, doing
        source validation. The following optional keyword arguments are
        supported:
        
            autoSkip        Default is True. If True, 5 words will be read from
                            the walker, even though only the first two words
                            (unitSize and nUnits) will be used. If False, only
                            2 words will be read, so the caller must skip or
                            otherwise process the walker for the remaining
                            three words.
            
            logger          A logger to which messages will be posted.
            
            recalcFirst     Default is False. If True, the objects three
                            derived values will be recalculated before the
                            object is returned. If False, only nUnits and
                            unitSize will be set.
            
            use32Bits       Default is False. If True, all operations will use
                            32-bit words instead of 16-bit words.
        
        >>> FH = utilities.fromhex
        >>> logger = utilities.makeDoctestLogger("bsh_fvw")
        >>> fvb = BSH.fromvalidatedbytes
        >>> obj = fvb(FH("00 06 00 0A 00 30 00 03 00 0C"), logger=logger)
        bsh_fvw.binsrch header - DEBUG - Walker has 10 remaining bytes.
        >>> fvb(FH("00 06 00 0A 00 00 00 00 00 00"), logger=logger)
        bsh_fvw.binsrch header - DEBUG - Walker has 10 remaining bytes.
        bsh_fvw.binsrch header - ERROR - The searchRange should have a value of 48, but is 0.
        bsh_fvw.binsrch header - ERROR - The entrySelector should have a value of 3, but is 0.
        bsh_fvw.binsrch header - ERROR - The rangeShift should have a value of 12, but is 0.
        
        >>> s = FH("00 00 00 06 00 00 00 0A 00 00 00 30 00 00 00 03 00 00 00 0C")
        >>> obj = fvb(s, logger=logger, use32Bits=True)
        bsh_fvw.binsrch header - DEBUG - Walker has 20 remaining bytes.
        >>> fvb(s[:-1] + FH("99"), logger=logger, use32Bits=True)
        bsh_fvw.binsrch header - DEBUG - Walker has 20 remaining bytes.
        bsh_fvw.binsrch header - ERROR - The rangeShift should have a value of 12, but is 153.

        >>> s = FH("00 00 00 06 ")
        >>> fvb(s[:-1] + FH("99"), logger=logger, use32Bits=True)        
        bsh_fvw.binsrch header - DEBUG - Walker has 4 remaining bytes.
        bsh_fvw.binsrch header - ERROR - Insufficient bytes.

        >>> fvb(s[:-1] + FH("99"), logger=logger, use32Bits=True, autoSkip=False)        
        bsh_fvw.binsrch header - DEBUG - Walker has 4 remaining bytes.
        bsh_fvw.binsrch header - ERROR - Insufficient bytes.

        >>> a = FH("00 00 00 06 10 00 00 00 00 01 02 00 ")
        >>> x = fvb(a[:-1] + FH("99"), logger=logger, use32Bits=True, autoSkip=False)        
        bsh_fvw.binsrch header - DEBUG - Walker has 12 remaining bytes.
        >>> x.nUnits, x.unitSize
        (268435456, 6)

        >>> b = FH("00 00 00 06 10 00 00 00 00 01 02 00 ")
        >>> x = fvb(b[:-1] + FH("99"), logger=logger, use32Bits=False, autoSkip=False)        
        bsh_fvw.binsrch header - DEBUG - Walker has 12 remaining bytes.
        >>> x.nUnits, x.unitSize
        (6, 0)

        >>> c = FH("00 00 00 06 ")
        >>> fvb(c[:-1] + FH("99"), logger=logger, use32Bits=False, autoSkip=True)        
        bsh_fvw.binsrch header - DEBUG - Walker has 4 remaining bytes.
        bsh_fvw.binsrch header - ERROR - Insufficient bytes.

        >>> d = FH("00 00 06 ")
        >>> fvb(d[:-1] + FH("99"), logger=logger, use32Bits=False, autoSkip=False)        
        bsh_fvw.binsrch header - DEBUG - Walker has 3 remaining bytes.
        bsh_fvw.binsrch header - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("binsrch header")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        use32Bits = kwArgs.get('use32Bits', False)
        autoSkip = kwArgs.get('autoSkip', True)
        
        if use32Bits:
            if autoSkip:
                if w.length() < 20:
                    logger.error(('V0004', (), "Insufficient bytes."))
                    return None
                
                t = w.unpack("2L")
                parts = w.unpack("3L")
            
            else:
                if w.length() < 8:
                    logger.error(('V0004', (), "Insufficient bytes."))
                    return None
                
                t = w.unpack("2L")
                parts = None
        
        else:
            if autoSkip:
                if w.length() < 10:
                    logger.error(('V0004', (), "Insufficient bytes."))
                    return None
                
                t = w.unpack("2H")
                parts = w.unpack("3H")
            
            else:
                if w.length() < 4:
                    logger.error(('V0004', (), "Insufficient bytes."))
                    return None
                
                t = w.unpack("2H")
                parts = None
        
        r = cls(*t)
        
        if parts is not None:
            r._recalc()
            it = zip(parts, r._cachedFields, ERR_CODES, ERR_STRINGS)
            
            for part, good, code, s in it:
                if part != good:
                    if all(t):
                        logger.error((
                          code,
                          (s, good, part),
                          "The %s should have a value of %d, but is %d."))
                        
                        r = None
                    
                    else:
                        logger.warning((
                          code,
                          (s, good, part),
                          "The %s should have a value of %d, but is %d. "
                          "However, since nUnits and/or unitSize are zero, "
                          "this is only a warning."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new BSH object from the specified walker. The
        following optional keyword arguments are supported:
        
            autoSkip        Default is True. If True, 5 words will be read from
                            the walker, even though only the first two words
                            (unitSize and nUnits) will be used. If False, only
                            2 words will be read, so the caller must skip or
                            otherwise process the walker for the remaining
                            three words.
            
            recalcFirst     Default is False. If True, the objects three
                            derived values will be recalculated before the
                            object is returned. If False, only nUnits and
                            unitSize will be set.
            
            use32Bits       Default is False. If True, all operations will use
                            32-bit words instead of 16-bit words.
        
        >>> d = {'use32Bits': True}
        >>> obj = _testingValues[1]
        >>> obj == BSH.frombytes(obj.binaryString())
        True
        >>> obj == BSH.frombytes(obj.binaryString(**d), **d)
        True
        """
        
        use32Bits = kwArgs.get('use32Bits', False)
        r = cls(*w.group(("L" if use32Bits else "H"), 2))
        
        if kwArgs.get('autoSkip', True):
            w.skip(12 if use32Bits else 6)
        
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
        BSH(),
        BSH(nUnits=10, unitSize=6))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
