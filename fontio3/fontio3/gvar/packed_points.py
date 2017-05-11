#
# packed_points.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for arrays of points as represented in 'gvar' tables.
"""

# System imports
import itertools

# Other imports
from fontio3 import utilities
from fontio3.fontdata import seqmeta
from fontio3.utilities import span2

# -----------------------------------------------------------------------------

#
# Functions
#

def _pprint(p, seq, **kwArgs):
    s = span2.Span(seq)
    p.simple(s, **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

class PackedPoints(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    """
    
    seqSpec = dict(
        seq_pprintfunc = _pprint)
    
    #
    # Methods
    #
    
    def __new__(cls, iterable):
        return tuple.__new__(cls, sorted(iterable))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PackedPoints object to the specified
        writer. The following keyword arguments are supported:
        
            pointCount      This is required, and should be the total number of
                            points in this glyph. This should *not* include the
                            4 synthetic points!
            
            stakeValue      This is optional, and is a stake to be used for the
                            start of the binary data.
        
        >>> obj = PackedPoints((3, 4, 5, 19, 20, 31, 40, 41, 42, 43))
        >>> utilities.hexdump(obj.binaryString(pointCount=90))
               0 | 0A09 0301 010E 010B  0901 0101           |............    |
        
        >>> obj = PackedPoints(range(140))
        >>> utilities.hexdump(obj.binaryString(pointCount=200))
               0 | 808C 7F00 0101 0101  0101 0101 0101 0101 |................|
              10 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              20 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              30 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              40 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              50 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              60 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              70 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              80 | 0101 010B 0101 0101  0101 0101 0101 0101 |................|
        
        If the pointCount were 136 (which, with the extra 4 synthetic points,
        would bring the total to 140), the special zero value is used:
        
        >>> utilities.hexdump(obj.binaryString(pointCount=136))
               0 | 00                                       |.               |
        
        If the pointCount is too small for the data, a ValueError is raised:
        >>> utilities.hexdump(obj.binaryString(pointCount=40))
        Traceback (most recent call last):
          ...
        ValueError: Largest point index exceeds glyph's count!
        
        We handle mixed 8-bit and 16-bit deltas:
        
        >>> obj = PackedPoints((14, 15, 280, 281, 282))
        >>> utilities.hexdump(obj.binaryString(pointCount=300))
               0 | 0501 0E01 8001 0901  0101                |..........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        assert 'pointCount' in kwArgs
        pointCount = kwArgs['pointCount']
        v = sorted(set(self))  # probably is already, but just in case...
        
        if v[-1] >= (pointCount + 4):
            raise ValueError("Largest point index exceeds glyph's count!")
        
        if v == list(range(pointCount + 4)):
            w.add("B", 0)
            return
        
        if len(v) < 128:
            w.add("B", len(v))
        else:
            w.add("H", 0x8000 + len(v))
        
        # Remember that the values here are actually deltas, not raw point
        # indices; this means that we can't simply use a Span to break things
        # into groups.
        
        deltas = v[0:1] + [b - a for a, b in utilities.pairwise(v)]
        
        for k, g in itertools.groupby(deltas, (lambda x: x > 255)):
            bigGroup = list(g)
            fmt = ("H" if k else "B")
            
            while len(bigGroup) > 128:
                w.add("B", (0xFF if k else 0x7F))
                w.addGroup(fmt, bigGroup[:128])
                del bigGroup[0:128]
            
            w.add("B", len(bigGroup) - 1 + (0x80 if k else 0))
            w.addGroup(fmt, bigGroup)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PackedPoints object from the specified
        walker, doing validation. The 'pointCount' keyword argument is
        required, and should just be the actual point count, not including the
        4 phantom points.
        
        >>> obj = PackedPoints((3, 4, 5, 19, 20, 31, 40, 41, 42, 43))
        >>> obj.pprint()
        3-5, 19-20, 31, 40-43
        
        >>> bs = obj.binaryString(pointCount=80)
        >>> obj2 = PackedPoints.fromvalidatedbytes(bs, pointCount=80)
        points - DEBUG - Walker has 12 remaining bytes.
        points - DEBUG - Points are [3, 4, 5, 19, 20, 31, 40, 41, 42, 43]
        
        >>> PackedPoints.fromvalidatedbytes(bs[:-1], pointCount=80)
        points - DEBUG - Walker has 11 remaining bytes.
        points - ERROR - The packed point array ends prematurely for runCount 10 and format 'B' (expectedSize 10, available 9).
        
        >>> PackedPoints.fromvalidatedbytes(bs, pointCount=20)
        points - DEBUG - Walker has 12 remaining bytes.
        points - ERROR - The unpacked point array contains point indices that are too large for the specified number of points in the glyph.
        
        >>> PackedPoints.fromvalidatedbytes(bs, pointCount=4)
        points - DEBUG - Walker has 12 remaining bytes.
        points - ERROR - The specified number of points (10) exceeds the number of points in the specified glyph.
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('points')
        else:
            logger = utilities.makeDoctestLogger('points')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        pointCount = kwArgs['pointCount']
        
        if w.length() < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        totalPoints = w.unpack("B")
        
        if not totalPoints:
            logger.debug(('Vxxxx', (), "Using all points in the glyph"))
            return cls(range(pointCount + 4))
        
        if totalPoints > 127:
            if w.length() < 1:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            totalPoints = ((totalPoints - 128) * 256) + w.unpack("B")
        
        if totalPoints > (pointCount + 4):
            logger.error((
              'V0135',
              (totalPoints,),
              "The specified number of points (%d) exceeds the number "
              "of points in the specified glyph."))
            
            return None
        
        pointIndices = []
        
        while totalPoints:
            if w.length() < 1:
                logger.error((
                  'V1036',
                  (),
                  "The packed point array is empty."))
                
                return None
            
            runCount = w.unpack("B")
            fmt = "BH"[runCount > 127]
            runCount = (runCount & 0x7F) + 1
            expectedSize = w.calcsize("%d%s" % (runCount, fmt))
            
            if w.length() < expectedSize:
                logger.error((
                  'V1036',
                  (runCount, fmt, expectedSize, int(w.length())),
                  "The packed point array ends prematurely for "
                  "runCount %d and format '%s' (expectedSize %d, "
                  "available %d)."))
                
                return None
            
            # The data here are not point indices, but packed point indices,
            # stored as deltas from the previous point (except the first).
            
            for n in w.group(fmt, runCount):
                if not pointIndices:
                    pointIndices.append(n)
                else:
                    pointIndices.append(pointIndices[-1] + n)
            
            totalPoints -= runCount
        
        if pointIndices[-1] >= pointCount + 4:
            logger.error((
              'V1035',
              (),
              "The unpacked point array contains point indices that are too "
              "large for the specified number of points in the glyph."))
            
            return None
        
        logger.debug(('Vxxxx', (pointIndices,), "Points are %s"))
        return cls(pointIndices)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PackedPoints object from the specified
        walker.
        
        >>> obj = PackedPoints((3, 4, 5, 19, 20, 31, 40, 41, 42, 43))
        >>> obj.pprint()
        3-5, 19-20, 31, 40-43
        
        >>> bs = obj.binaryString(pointCount=80)
        >>> PackedPoints.frombytes(bs, pointCount=80).pprint()
        3-5, 19-20, 31, 40-43
        
        >>> PackedPoints.frombytes(bytes([0]), pointCount=80).pprint()
        0-83
        """
        
        pointCount = kwArgs['pointCount']
        totalPoints = w.unpack("B")
        pointIndices = []
        
        if not totalPoints:
            pointIndices = list(range(pointCount + 4))
        elif totalPoints > 127:
            totalPoints = (totalPoints - 128) * 256 + w.unpack("B")
        
        while totalPoints:  # if zero, already filled out pointIndices
            runCount = w.unpack("B")
            fmt = "BH"[runCount > 127]
            runCount = (runCount & 0x7F) + 1
            
            # The data here are not point indices, but packed point indices,
            # stored as deltas from the previous point (except the first).
            
            for n in w.group(fmt, runCount):
                if not pointIndices:
                    pointIndices.append(n)
                else:
                    pointIndices.append(pointIndices[-1] + n)
            
            totalPoints -= runCount
        
        return cls(pointIndices)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

