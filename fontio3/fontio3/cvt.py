#
# cvt.py
#
# Copyright © 2004-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entries in the 'cvt ' table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Cvt(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects containing a list of CVT values.
    
    >>> c = Cvt([22, 0, 24, 26])
    >>> c.pprint(label="CVT Values")
    CVT Values:
      0: 22
      1: 0
      2: 24
      3: 26
    
    >>> c.scaled(1.5).pprint(label="Scaled values")
    Scaled values:
      0: 33
      1: 0
      2: 36
      3: 39
    
    >>> c.cvtsRenumbered(oldToNew={3: 0, 0:3}).pprint(label="CVTs renumbered")
    CVTs renumbered:
      0: 26
      1: 0
      2: 24
      3: 22
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_scaledirect = True,
        seq_indexiscvtindex = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Cmap object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0002 0003 FFFB                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.addGroup("h", self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Cvt. However, it also does
        extensive validation via the logging module (the client should have
        done a logging.basicConfig call prior to calling this method, unless a
        logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> b = utilities.fromhex("00 44 FF F2 19 38")
        >>> Cvt.fromvalidatedbytes(b, logger=logger).pprint()
        test.cvt - DEBUG - Walker has 6 remaining bytes.
        test.cvt - INFO - 'cvt ' table has 3 entries.
        0: 68
        1: -14
        2: 6456
        
        >>> Cvt.fromvalidatedbytes(b[:-1], logger=logger)
        test.cvt - DEBUG - Walker has 5 remaining bytes.
        test.cvt - ERROR - 'cvt ' table has odd number of bytes.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('cvt')
        else:
            logger = logger.getChild('cvt')
        
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength % 2:
            logger.error((
              'E0400',
              (),
              "'cvt ' table has odd number of bytes."))
            
            return None
        
        count = int(byteLength // 2)
        logger.info(('V0003', (count,), "'cvt ' table has %d entries."))
        return cls(w.groupIterator("h", count))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Cvt object from the specified walker.
        
        >>> fb = Cvt.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        count = int(w.length() // 2)
        return cls(w.groupIterator("h", count))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Cvt(),
        Cvt([1, 2, 3, -5]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
