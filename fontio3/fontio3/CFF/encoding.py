#
# encoding.py
#
# Copyright © 2013-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF Encodings.
"""

# System imports
import logging

# Other imports
from fontio3.CFF import encodings_f0, encodings_f1, encodings_predefined
from fontio3.CFF.cffutils import stdStrings, nStdStrings, dStdStrings
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_workClasses = {
    0: encodings_f0.Format0,
    1: encodings_f1.Format1}


# -----------------------------------------------------------------------------

#
# Classes
#

class Encoding(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing CFF Encodings, a mapping of codes to glyphIDs.
    """
    
    mapSpec = dict(
        item_renumberdirectvalues = True,
        map_compactremovesfalses = True)
        
    attrSpec = dict(
        originalFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True),
        predefinedFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True))
    #
    # Initialization and class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Encoding. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
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
        Like fromnumber, fromvalidatednumber returns an Encoding based
        on a number (one of the 2 Predefined encodings: Standard
        Encoding (0) or Expert Encoding (1)). It also performs
        validation using a logger.
        """
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('encoding')
        else:
            logger = logger.getChild('encoding')

        d = encodings_predefined.Predefined.fromvalidatednumber(
          n,
          logger=logger,
          **kwArgs)
        return cls(d, predefinedFormat=n)


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initialize Encoding data from the stored format from the
        specified walker.
        """
        
        format = w.unpack("B", advance=False)
        workObj = _workClasses[format].fromwalker(w, **kwArgs)
        return cls(workObj, originalFormat=format)


    @classmethod
    def fromnumber(cls, n, **kwArgs):
        """
        Returns an Encoding based on a number (one of the 2 Predefined
        encodings: Standard Encoding (0) or Expert Encoding (1)).
        """

        d = encodings_predefined.Predefined.fromnumber(n, **kwArgs)
        return cls(d, predefinedFormat=n)

    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Call buildBinary using the appropriate originalFormat method.
        
        >>> print(utilities.hexdumpString(_testingValues[1].binaryString()), end='')
               0 |0003 0203 04                             |.....           |
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
    
    _testingValues = (
        Encoding(originalFormat=0),
        Encoding({1:2, 2:3, 3:4}, originalFormat=0))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

