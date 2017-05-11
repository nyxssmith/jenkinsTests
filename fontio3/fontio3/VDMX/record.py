#
# record.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single VDMX height records.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Record(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing the maximum and minimum pixel y-values for a single
    PPEM. These are simple objects with two attributes:
    
        yMax
        yMin
    
    >>> _testingValues[1].pprint()
    Maximum y-value (in pixels): 10
    Minimum y-value (in pixels): -3
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        yMax = dict(
            attr_label = "Maximum y-value (in pixels)",
            attr_scaledirect = True,
            attr_representsy = True),
        
        yMin = dict(
            attr_label = "Minimum y-value (in pixels)",
            attr_scaledirect = True,
            attr_representsy = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Record object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000A FFFD                                |....            |
        """
        
        w.add("2h", (self.yMax or 0), (self.yMin or 0))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Record object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Record.frombytes(obj.binaryString())
        True
        """
        
        return cls(*w.unpack("2h"))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Record object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = obj.binaryString()
        >>> obj = Record.fromvalidatedbytes(s, logger=logger)
        test.Record - DEBUG - Walker has 4 remaining bytes.
        >>> obj = Record.fromvalidatedbytes(s[0:3], logger=logger)
        test.Record - DEBUG - Walker has 3 remaining bytes.
        test.Record - ERROR - Insufficient bytes (3) for Record (minimum 4)
        """
        logger = kwArgs.pop('logger', None)
        if logger is None:
            logger = logging.getLogger().getChild('Record')
        else:
            logger = logger.getChild('Record')

        remaining_length = w.length()
        logger.debug(('V0001', (remaining_length,), "Walker has %d remaining bytes."))

        if remaining_length < 4:
            logger.error((
              'V0004',
              (remaining_length,),
              "Insufficient bytes (%d) for Record (minimum 4)"))
            
            return None

        return cls(*w.unpack("2h"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Record(),
        Record(10, -3),
        Record(11, -3),
        Record(11, -4))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
