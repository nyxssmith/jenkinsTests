#
# attachpoint.py
#
# Copyright © 2005-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to attachment points for a single glyph in GDEF tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _valFunc(obj, **kwArgs):
    if list(obj) != sorted(obj):
        kwArgs['logger'].error((
          'V0303',
          (),
          "Attachment points not sorted."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class AttachPointTable(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects defining a group of glyph point indices to be used as attachment
    points.
    
    These are lists of glyph point numbers.
    
    >>> apt = _testingValues[2]
    >>> apt.pprint()
    0: 3
    1: 19
    2: 20
    
    >>> apt.pointsRenumbered({20: {19: 40}}, glyphIndex=20).pprint()
    0: 3
    1: 20
    2: 40
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_renumberpointsdirect = True,
        seq_keepsorted = True,
        seq_validatefunc = _valFunc)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0003 0004 0006 0007                      |........        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0003 0003 0013 0014                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        w.addGroup("H", self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new AttachPointTable. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test.GDEF')
        >>> fvb = AttachPointTable.fromvalidatedbytes
        
        *** Normal cases ***
        
        >>> s = _testingValues[1].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.GDEF.attachpoint - DEBUG - Walker has 8 remaining bytes.
        test.GDEF.attachpoint - INFO - Number of AttachPointTable entries: 3.
        
        >>> obj = fvb(_testingValues[0].binaryString(), logger=logger)
        test.GDEF.attachpoint - DEBUG - Walker has 2 remaining bytes.
        test.GDEF.attachpoint - WARNING - Zero entries in AttachPointTable data.
        
        *** Error cases ***
        
        >>> fvb(s[:1], logger=logger)
        test.GDEF.attachpoint - DEBUG - Walker has 1 remaining bytes.
        test.GDEF.attachpoint - ERROR - Insufficient bytes.
        
        >>> fvb(s[:2], logger=logger)
        test.GDEF.attachpoint - DEBUG - Walker has 2 remaining bytes.
        test.GDEF.attachpoint - INFO - Number of AttachPointTable entries: 3.
        test.GDEF.attachpoint - ERROR - Insufficient bytes for table.
        
        >>> fvb(s[:2] + s[4:6] + s[2:4] + s[6:], logger=logger)
        test.GDEF.attachpoint - DEBUG - Walker has 8 remaining bytes.
        test.GDEF.attachpoint - INFO - Number of AttachPointTable entries: 3.
        test.GDEF.attachpoint - ERROR - Point indices not sorted.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('attachpoint')
        else:
            logger = logger.getChild('attachpoint')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        
        if count:
            logger.info((
              'V0076',
              (count,),
              "Number of AttachPointTable entries: %d."))
        
        else:
            logger.warning((
              'V0077',
              (),
              "Zero entries in AttachPointTable data."))
        
        if w.length() < 2 * count:
            logger.error(('E4000', (), "Insufficient bytes for table."))
            return None
        
        v = list(w.group("H", count))
        
        if v != sorted(v):
            logger.error(('V0078', (), "Point indices not sorted."))
            return None
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new AttachPointTable object from the specified walker.
        
        >>> apt = _testingValues[1]
        >>> apt == AttachPointTable.frombytes(apt.binaryString())
        True
        
        >>> apt = _testingValues[2]
        >>> apt == AttachPointTable.frombytes(apt.binaryString())
        True
        """
        
        return cls(w.group("H", w.unpack("H")))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        AttachPointTable(),
        AttachPointTable([4, 6, 7]),
        AttachPointTable([3, 19, 20]),
        AttachPointTable([1, 4]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
