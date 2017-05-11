#
# group.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for collections of VDMX height records.
"""

# System imports
import operator

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.VDMX import record

# -----------------------------------------------------------------------------

#
# Classes
#

class Group(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dicts mapping PPEM values to Record objects.
    
    >>> _testingValues[1].pprint()
    14 PPEM:
      Maximum y-value (in pixels): 10
      Minimum y-value (in pixels): -3
    15 PPEM:
      Maximum y-value (in pixels): 11
      Minimum y-value (in pixels): -3
    16 PPEM:
      Maximum y-value (in pixels): 11
      Minimum y-value (in pixels): -4
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "%d PPEM" % (i,)),
        item_pprintlabelpresort = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Group object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0003 0E10 000E 000A  FFFD 000F 000B FFFD |................|
              10 | 0010 000B FFFC                           |......          |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0002 0E10 000E 000A  FFFD 0010 000B FFFC |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        minKey = min(self)
        maxKey = max(self)
        
        if not (0 <= minKey < 256):
            raise ValueError("Lowest ppem is out of range!")
        
        if not (0 <= maxKey < 256):
            raise ValueError("Highest ppem is out of range!")
        
        w.add("H2B", len(self), minKey, maxKey)
        
        for ppem, rec in sorted(self.items(), key=operator.itemgetter(0)):
            w.add("H", ppem)
            rec.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Group object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Group.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2 ]
        >>> obj == Group.frombytes(obj.binaryString())
        True
        """
        
        r = cls()
        count = w.unpack("H2x")  # don't care about minKey and maxKey here
        f = record.Record.fromwalker
        
        while count:
            ppem = w.unpack("H")
            r[ppem] = f(w, **kwArgs)
            count -= 1
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Group object from the specified walker.

        logger = utilities.makeDoctestLogger("test")
        """
        logger = kwArgs.pop('logger', None)
        if logger is None:
            logger = logging.getLogger().getChild('Group')
        else:
            logger = logger.getChild('Group')
         
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))

        if byteLength < 4:
            logger.error((
                'V0004',
                (byteLength,),
                'Insufficient bytes (%d) for Group (minimum 4)'))
            return None
        
        r = cls()
        count = w.unpack("H2x")  # don't care about minKey and maxKey here
        f = record.Record.fromvalidatedwalker

        while count:
            byteLength = w.length()

            if byteLength < 6:
                logger.error((
                  'V0004',
                  (byteLength,),
                  'Insuficient bytes (%d) for Group/Record (minimum 6)'))

                return None

            ppem = w.unpack("H")
            r[ppem] = f(w, logger=logger, **kwArgs)
            count -= 1
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _rv = record._testingValues
    
    _testingValues = (
        Group(),
        Group({14: _rv[1], 15: _rv[2], 16: _rv[3]}),
        Group({14: _rv[1], 16: _rv[3]}))
    
    del _rv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
