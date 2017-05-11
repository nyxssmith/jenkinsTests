#
# format8.py
#
# Copyright © 2009, 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 8 embedded bitmaps.
"""

# System imports
import functools
import logging

# Other imports
from fontio3 import bitmap
from fontio3.fontdata import seqmeta
from fontio3.sbit import format89_component, smallglyphmetrics

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(fmt8Obj, **kwArgs):
    logger = kwArgs['logger']
    stk = kwArgs['strike']
    thisGlyphIndex = kwArgs['glyphIndex']
    badCycles = set()
    badGlyphs = set()
    allGlyphs = set()
    
    fmt8Obj.allReferencedGlyphs(
      allGlyphs,
      badCycles = badCycles,
      badGlyphs = badGlyphs,
      **kwArgs)
    
    if badCycles:
        logger.error((
          'V0485',
          (thisGlyphIndex, sorted(badCycles),),
          "Glyph %d has circular glyph index references %s."))
        
        return False
    
    if badGlyphs:
        logger.error((
          'V0486',
          (thisGlyphIndex, sorted(badGlyphs),),
          "Glyph %d includes unknown glyphs %s."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Format8(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing composite embedded bitmaps with small metrics. These
    are lists of Format89_Component objects.
    
    >>> _testingValues[1].pprint(strike=_fakeStrike())
       ----+++++++++
       4321012345678
    +7 XXX..........
    +6 X.X..........
    +5 XXX..........
    +4 .............
    +3 .............
    +2 .............
    +1 .............
    +0 .............
    -1 .....X......X
    -2 ......X....X.
    -3 .......X..X..
    -4 ........XX...
    -5 ........XX...
    -6 .......X..X..
    -7 ......X....X.
    Bit depth: 1
    Y-coordinate of topmost gridline: 8
    X-coordinate of leftmost gridline: -4
    Metrics:
      Horizontal: True
      Height: 7
      Width: 5
      Origin-to-left: 1
      Origin-to-top: 4
      Advance: 7
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        seq_pprintfunc = (
          lambda p, x, **k:
          p.deep(x.getBitmap(k['strike']), **k)),
        seq_validatefunc_partial = _validate)
    
    attrSpec = dict(
        metrics = dict(
            attr_followsprotocol = True,
            attr_initfunc = smallglyphmetrics.SmallGlyphMetrics,
            attr_label = "Metrics"))
    
    imageFormat = 8  # class constant
    
    #
    # Methods
    #
    
    def allReferencedGlyphs(self, setToFill, **kwArgs):
        """
        Adds to a set containing all component glyph indices, recursively
        nested as needed.
        
        Supported keyword arguments are:
            
            badCycles   A set which, on output, contains any glyphs containing
                        circular references. This is optional.
            
            badGlyphs   A set which, on output, contains any out-of-bounds (or
                        otherwise invalid) glyph indices that were encountered
                        during the recursive walk. This is optional.
            
            strike      A Strike. This is required.
        """
        
        stk = kwArgs['strike']
        newAdditions = set()
        badGlyphs = kwArgs.get('badGlyphs', set())
        badCycles = kwArgs.get('badCycles', set())
        
        for part in self:
            pieceIndex = part.glyphCode
            
            if pieceIndex in setToFill:
                badCycles.add(pieceIndex)  # circular
            
            elif pieceIndex in stk:
                newAdditions.add(pieceIndex)
                subGlyph = stk[pieceIndex]
                
                if (subGlyph is not None) and (subGlyph.imageFormat in {8, 9}):
                    tempSet = setToFill | newAdditions
                    subGlyph.allReferencedGlyphs(tempSet, **kwArgs)
                    newAdditions.update(tempSet - setToFill)
            
            else:
                badGlyphs.add(pieceIndex)  # out of bounds
        
        setToFill.update(newAdditions)
    
    def binarySize(self):
        """
        Returns the byte size of the binary string, without having to actually
        construct it. This is useful in the analysis phase of sbit writing.
        """
        
        return 4 * len(self) + 8
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format8 object to the specified writer.
        
        >>> obj = _testingValues[1]
        >>> print(utilities.hexdumpString(obj.binaryString()), end='')
               0 |0705 0104 0700 0002  0019 0000 0061 FB05 |.............a..|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self.metrics.buildBinary(w, **kwArgs)
        w.add("xH", len(self))
        
        for obj in self:
            obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Format8. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.sbit')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format8.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.sbit.format8 - DEBUG - Walker has 16 remaining bytes.
        test.sbit.format8.smallglyphmetrics - DEBUG - Walker has 16 remaining bytes.
        test.sbit.format8.[0].format89_component - DEBUG - Walker has 8 remaining bytes.
        test.sbit.format8.[1].format89_component - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:2], logger=logger)
        test.sbit.format8 - DEBUG - Walker has 2 remaining bytes.
        test.sbit.format8.smallglyphmetrics - DEBUG - Walker has 2 remaining bytes.
        test.sbit.format8.smallglyphmetrics - ERROR - Insufficient bytes
        
        >>> fvb(s[:7], logger=logger)
        test.sbit.format8 - DEBUG - Walker has 7 remaining bytes.
        test.sbit.format8.smallglyphmetrics - DEBUG - Walker has 7 remaining bytes.
        test.sbit.format8 - ERROR - Insufficient bytes for count
        
        >>> fvb(s[:14], logger=logger)
        test.sbit.format8 - DEBUG - Walker has 14 remaining bytes.
        test.sbit.format8.smallglyphmetrics - DEBUG - Walker has 14 remaining bytes.
        test.sbit.format8.[0].format89_component - DEBUG - Walker has 6 remaining bytes.
        test.sbit.format8.[1].format89_component - DEBUG - Walker has 2 remaining bytes.
        test.sbit.format8.[1].format89_component - ERROR - Insufficient bytes
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format8')
        else:
            logger = logger.getChild('format8')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        m = smallglyphmetrics.SmallGlyphMetrics.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if m is None:
            return None
        
        if w.length() < 3:
            logger.error((
              'V0224',
              (),
              "Insufficient bytes for count"))
            
            return None
        
        pad, count = w.unpack("BH")
        
        if pad:
            logger.warning((
              'V0225',
              (pad,),
              "Pad byte should be zero, but is %d"))
        
        v = []
        fw = format89_component.Format89_Component.fromvalidatedwalker
        
        for i in range(count):
            itemLogger = logger.getChild("[%d]" % (i,))
            obj = fw(w, logger=itemLogger, **kwArgs)
            
            if obj is None:
                return None
            
            v.append(obj)
        
        return cls(v, metrics=m)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format8 object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Format8.frombytes(obj.binaryString())
        True
        """
        
        m = smallglyphmetrics.SmallGlyphMetrics.fromwalker(w, **kwArgs)
        count = w.unpack("xH")
        fw = format89_component.Format89_Component.fromwalker
        return cls((fw(w, **kwArgs) for i in range(count)), metrics=m)
    
    def getBitmap(self, strike):
        """
        Returns a Bitmap object with the composited image.
        
        >>> _testingValues[1].getBitmap(strike=_fakeStrike()).pprint()
           ----+++++++++
           4321012345678
        +7 XXX..........
        +6 X.X..........
        +5 XXX..........
        +4 .............
        +3 .............
        +2 .............
        +1 .............
        +0 .............
        -1 .....X......X
        -2 ......X....X.
        -3 .......X..X..
        -4 ........XX...
        -5 ........XX...
        -6 .......X..X..
        -7 ......X....X.
        Bit depth: 1
        Y-coordinate of topmost gridline: 8
        X-coordinate of leftmost gridline: -4
        """
        
        v = []
        
        for obj in self:
            b = strike[obj.glyphCode]
            
            if b.imageFormat < 8:
                b = b.image
            else:
                b = b.getBitmap(strike)
            
            v.append(b.moved(obj.xOffset, obj.yOffset))
        
        if len(v) == 1:
            return v[0]
        
        r = functools.reduce(bitmap.Bitmap.unioned, v)
        r.metrics = self.metrics.__copy__()
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _ctv = format89_component._testingValues
    _mtv = smallglyphmetrics._testingValues
    
    def _fakeStrike():
        from fontio3.sbit import format1
        
        _tv = format1._testingValues
        
        d = {
          25: _tv[1],
          97: _tv[3]}
        
        return d
    
    _testingValues = (
        Format8(),
        Format8(_ctv[0:2], metrics=_mtv[3]))
    
    del _ctv, _mtv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
