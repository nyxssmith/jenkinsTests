#
# anchorpoints.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to sequences of anchor points for a single glyph.
"""

# System imports
import logging

# Other imports
from fontio3.ankr import anchorpoint
from fontio3.fontdata import seqmeta
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    r = True
    
    if len(obj) != len(set(obj)):
        logger.warning((
          'V0859',
          (),
          "There are duplicate entries in the anchorpoints for the glyph."))
        
        r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class AnchorPoints(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing all the AnchorPoint objects for a single glyph. These
    are lists of AnchorPoint objects.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintfunc = pp.PP.simple,
        item_pprintlabelfunc = (lambda i: "Anchor point %d" % (i,)),
        seq_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the AnchorPoints object to the specified
        writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0002 0064 FF9C  0102 0304           |.....d......    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", len(self))
        
        for obj in self:
            obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AnchorPoints object from the specified
        walker, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> bs = _testingValues[1].binaryString()
        >>> fvb = AnchorPoints.fromvalidatedbytes
        >>> fvb(bs, logger=logger).pprint()
        fvw.anchorpoints - DEBUG - Walker has 12 remaining bytes.
        fvw.anchorpoints.[0].anchorpoint - DEBUG - Walker has 8 remaining bytes.
        fvw.anchorpoints.[1].anchorpoint - DEBUG - Walker has 4 remaining bytes.
        Anchor point 0: (100, -100)
        Anchor point 1: (258, 772)
        
        >>> obj = fvb(bs[:-1], logger=logger)
        fvw.anchorpoints - DEBUG - Walker has 11 remaining bytes.
        fvw.anchorpoints.[0].anchorpoint - DEBUG - Walker has 7 remaining bytes.
        fvw.anchorpoints.[1].anchorpoint - DEBUG - Walker has 3 remaining bytes.
        fvw.anchorpoints.[1].anchorpoint - ERROR - Insufficient bytes
        
        >>> obj = fvb(bs[2:], logger=logger)
        fvw.anchorpoints - DEBUG - Walker has 10 remaining bytes.
        fvw.anchorpoints - WARNING - The number of anchor points is 131172, which is greater than 255 and very unlikely.
        fvw.anchorpoints.[0].anchorpoint - DEBUG - Walker has 6 remaining bytes.
        fvw.anchorpoints.[1].anchorpoint - DEBUG - Walker has 2 remaining bytes.
        fvw.anchorpoints.[1].anchorpoint - ERROR - Insufficient bytes
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("anchorpoints")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        count = w.unpack("L")
        
        if count > 255:
            logger.warning((
              'V0852',
              (count,),
              "The number of anchor points is %d, which is greater than "
              "255 and very unlikely."))
        
        fvw = anchorpoint.AnchorPoint.fromvalidatedwalker
        v = []
        
        for i in range(count):
            obj = fvw(w, logger=logger.getChild("[%d]" % (i,)))
            
            if obj is None:
                return None
            
            v.append(obj)
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AnchorPoints object from the specified
        walker.
        
        >>> bs = _testingValues[1].binaryString()
        >>> AnchorPoints.frombytes(bs).pprint()
        Anchor point 0: (100, -100)
        Anchor point 1: (258, 772)
        """
        
        count = w.unpack("L")
        fw = anchorpoint.AnchorPoint.fromwalker
        return cls(fw(w, **kwArgs) for i in range(count))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    A = anchorpoint.AnchorPoint
    _tv = anchorpoint._testingValues
    
    _testingValues = (
        AnchorPoints([]),
        AnchorPoints([A(100, -100), A(258, 772)]),
        AnchorPoints([_tv[0], _tv[1]]),
        AnchorPoints(_tv[2:5]),
        AnchorPoints(_tv[5:]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
