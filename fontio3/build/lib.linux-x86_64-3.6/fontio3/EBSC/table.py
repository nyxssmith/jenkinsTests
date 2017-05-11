#
# table.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a single bitmapScaleTable in an EBSC object.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.sbit import linemetrics
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs.pop('logger')
    ppemX = kwArgs['ppemX']
    ppemY = kwArgs['ppemY']
    
    if obj.substitutePpemX == ppemX and obj.substitutePpemY == ppemY:
        logger.warning((
          'V0817',
          (),
          "The substitute PPEM values are the same as the original PPEM "
          "values, so this table has no effect."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Table(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing EBSC data for a single size. These are mostly the same
    as bitmapScaleTables, as defined in the spec, but the ppemX and ppemY
    values are not represented here, as they're used in the key for the higher-
    level EBSC object itself (q.v.)
    
    >>> _testingValues[1].pprint()
    Horizontal line metrics:
      Horizontal: True
      Ascent: 12
      Descent: -3
      Maximum pixel width: 16
      Caret slope numerator: 1
      Caret slope denominator: 0
      Caret offset: 0
      Minimum sidebearing on origin side: 1
      Minimum sidebearing on non-origin side: 1
      Maximum positive cross-stream extent: 11
      Minimum negative cross-stream extent: -2
    Vertical line metrics:
      Horizontal: False
      Ascent: 7
      Descent: -7
      Maximum pixel width: 16
      Caret slope numerator: 0
      Caret slope denominator: 1
      Caret offset: 0
      Minimum sidebearing on origin side: -1
      Minimum sidebearing on non-origin side: -1
      Maximum positive cross-stream extent: 6
      Minimum negative cross-stream extent: -6
    Substitute x-PPEM value: 16
    Substitute y-PPEM value: 16
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> d = {'logger': logger, 'editor': e, 'ppemX': 17, 'ppemY': 17}
    >>> _testingValues[1].isValid(**d)
    True
    
    >>> d['ppemX'] = d['ppemY'] = 16
    >>> _testingValues[1].isValid(**d)
    val - WARNING - The substitute PPEM values are the same as the original PPEM values, so this table has no effect.
    True
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        hori = dict(
            attr_followsprotocol = True,
            attr_initfunc = linemetrics.LineMetrics,
            attr_label = "Horizontal line metrics"),
        
        vert = dict(
            attr_followsprotocol = True,
            attr_initfunc = linemetrics.LineMetrics,
            attr_label = "Vertical line metrics"),
        
        substitutePpemX = dict(
            attr_label = "Substitute x-PPEM value",
            attr_validatefunc_partial = valassist.isFormat_B),
        
        substitutePpemY = dict(
            attr_label = "Substitute y-PPEM value",
            attr_validatefunc_partial = valassist.isFormat_B))
    
    attrSorted = ('hori', 'vert', 'substitutePpemX', 'substitutePpemY')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Table to the specified writer. The
        following keyword arguments are used:
        
            ppemX   The ppemX value (from the key). Required.
            ppemY   The ppemY value (from the key). Required.
        
        >>> d = {'ppemX': 17, 'ppemY': 17}
        >>> utilities.hexdump(_testingValues[1].binaryString(**d))
               0 | 0CFD 1001 0000 0101  0BFE 0000 07F9 1000 |................|
              10 | 0100 FFFF 06FA 0000  1111 1010           |............    |
        """
        
        ppemX = kwArgs.pop('ppemX')
        ppemY = kwArgs.pop('ppemY')
        self.hori.buildBinary(w, **kwArgs)
        self.vert.buildBinary(w, **kwArgs)
        w.add("4B", ppemX, ppemY, self.substitutePpemX, self.substitutePpemY)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Table object from the specified walker, doing
        source validation.
        
        >>> d = {'ppemX': 17, 'ppemY': 17}
        >>> s = _testingValues[1].binaryString(**d)
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Table.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.table - DEBUG - Walker has 28 remaining bytes.
        fvw.table.horizontal linemetrics - DEBUG - Walker has 28 remaining bytes.
        fvw.table.vertical linemetrics - DEBUG - Walker has 16 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:-1], logger=logger)
        fvw.table - DEBUG - Walker has 27 remaining bytes.
        fvw.table.horizontal linemetrics - DEBUG - Walker has 27 remaining bytes.
        fvw.table.vertical linemetrics - DEBUG - Walker has 15 remaining bytes.
        fvw.table - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("table")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        fvw = linemetrics.LineMetrics.fromvalidatedwalker
        kwArgs.pop('isHorizontal', None)
        h = fvw(w, isHorizontal=True, logger=logger, **kwArgs)
        
        if h is None:
            return None
        
        v = fvw(w, isHorizontal=False, logger=logger, **kwArgs)
        
        if v is None:
            return None
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        x, y = w.unpack("2x2B")
        return cls(h, v, x, y)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Table object from the specified walker.
        
        >>> d = {'ppemX': 17, 'ppemY': 17}
        >>> s = _testingValues[1].binaryString(**d)
        >>> obj = Table.frombytes(s)
        >>> obj == _testingValues[1]
        True
        """
        
        fw = linemetrics.LineMetrics.fromwalker
        kwArgs.pop('isHorizontal', None)
        h = fw(w, isHorizontal=True, **kwArgs)
        v = fw(w, isHorizontal=False, **kwArgs)
        x, y = w.unpack("2x2B")
        return cls(h, v, x, y)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _hm = linemetrics.LineMetrics(
      isHorizontal = True,
      ascent = 12,
      descent = -3,
      widthMax = 16,
      caretSlopeNumerator = 1,
      caretSlopeDenominator = 0,
      caretOffset = 0,
      minOriginSB = 1,
      minAdvanceSB = 1,
      maxBeforeBL = 11,
      minAfterBL = -2)
    
    _vm = linemetrics.LineMetrics(
      isHorizontal = False,
      ascent = 7,
      descent = -7,
      widthMax = 16,
      caretSlopeNumerator = 0,
      caretSlopeDenominator = 1,
      caretOffset = 0,
      minOriginSB = -1,
      minAdvanceSB = -1,
      maxBeforeBL = 6,
      minAfterBL = -6)
    
    _testingValues = (
        Table(),
        
        Table(
          hori = _hm,
          vert = _vm,
          substitutePpemX = 16,
          substitutePpemY = 16))
    
    del _hm, _vm

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
