#
# bitmap.py
#
# Copyright © 2004-2011, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for definitions of bitmaps and pixmaps. No actual scaler rendering
happens here (since fontio should exist as a standalone module).
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.fontmath import rectangle

# -----------------------------------------------------------------------------

#
# Private constants
#

_pixelRepresentations = {
    1: ('.', 'X'),
    2: ('.', '1', '2', '3'),
    4: ('.',) + tuple("%X" % (n,) for n in range(1, 16))}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, seq, **kwArgs):
    seq = seq.regularized()
    
    if seq:
        xStart = seq.lo_x
        xStartStrLen = len("%+d" % (xStart,))
        xEndPlusOne = xStart + len(seq[0])
        xLastStrLen = len("%+d" % (xEndPlusOne - 1,))
        fmt = "%%+0%sd" % (max(xStartStrLen, xLastStrLen),)
        j = (' ' if seq.bitDepth == 8 else '')
        svs = _transposed([fmt % (x,) for x in range(xStart, xEndPlusOne)])
        yTop = seq.hi_y - 1
        yFirstStrLen = len("%+d" % (yTop,))
        yBottomMinusOne = yTop - len(seq)
        yLastStrLen = len("%+d" % (yBottomMinusOne + 1,))
        yLen = max(yFirstStrLen, yLastStrLen)
        yLenPad = " " * (yLen + 1)
        fmt = "%%+0%sd %%s" % (yLen,)
        
        for sv in svs:
            p("%s%s" % (yLenPad, j.join(sv)))
            
        if seq.bitDepth == 8:
            fmt2 = "%s%s"
            
            for row, rowIndex in zip(seq, range(yTop, yBottomMinusOne, -1)):
                sv = ["%04d" % (n,) for n in row]
                p(fmt % (rowIndex, ''.join(s[0:2] for s in sv)))
                p(fmt2 % (yLenPad, ''.join(s[2:4] for s in sv)))
        
        else:
            c = _pixelRepresentations[seq.bitDepth]
            
            for row, rowIndex in zip(seq, range(yTop, yBottomMinusOne, -1)):
                p(fmt % (rowIndex, ''.join(c[n] for n in row)))
    
    else:
        p("(empty bitmap)")

def _transposed(seq):
    """
    Returns the seq transposed.
    
    >>> seq = list(_testingValues[0])
    >>> seq
    [[0, 1, 0], [1, 0, 1], [1, 0, 1], [0, 1, 0]]
    >>> _transposed(seq)
    [[0, 1, 1, 0], [1, 0, 0, 1], [0, 1, 1, 0]]
    """
    
    if seq:
        return list(map(lambda *x: list(x), *seq))
    else:
        return seq

def _validate(seq, **kwArgs):
    logger = kwArgs['logger']
    limit = 1 << seq.bitDepth
    
    if not all((0 <= n < limit) for row in seq for n in row):
        logger.error(('G0018', (), "Values out-of-range for bitDepth"))
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Bitmap(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing bitmap or pixmap data. These are lists of rows, where
    each row is in turn a list of numeric values.
    
    >>> _testingValues[0].pprint()
       +++
       012
    +2 .X.
    +1 X.X
    +0 X.X
    -1 .X.
    Bit depth: 1
    Y-coordinate of topmost gridline: 3
    X-coordinate of leftmost gridline: 0
    
    >>> _testingValues[1].pprint()
          ---
          111
          555
          222
          543
    +1292 .X.
    +1291 X.X
    +1290 X.X
    +1289 .X.
    Bit depth: 1
    Y-coordinate of topmost gridline: 1293
    X-coordinate of leftmost gridline: -1525
    
    >>> _testingValues[2].pprint()
         + + + +
         1 1 1 1
         2 3 4 5
    -126 01000002
         29420455
    -127 00000001
         00153131
    Bit depth: 8
    Y-coordinate of topmost gridline: -125
    X-coordinate of leftmost gridline: 12
    
    >>> for obj in _testingValues[0].asImmutable(): print(obj)
    ('Bitmap', (0, 1, 0), (1, 0, 1), (1, 0, 1), (0, 1, 0))
    ('bitDepth', 1)
    ('hi_y', 3)
    ('lo_x', 0)
    
    >>> logger = utilities.makeDoctestLogger("valtest")
    >>> _testingValues[4].isValid(logger=logger)
    valtest - ERROR - Values out-of-range for bitDepth
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_asimmutablefunc = tuple,
        item_deepcopyfunc = (lambda x, memo: list(x)),
        seq_pprintfunc = _pprint,
        seq_validatefunc = _validate)
    
    attrSpec = dict(
        lo_x = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 0),
            attr_label = "X-coordinate of leftmost gridline"),
        
        hi_y = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Y-coordinate of topmost gridline"),
        
        bitDepth = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 1),
            attr_label = "Bit depth"))
    
    #
    # Public methods
    #
    
    def bounds(self):
        """
        Returns a Rectangle with the bounds of the bitmap. No trimming is done,
        although the Rectangle is regularized first.
        
        >>> print(_testingValues[0].bounds())
        Minimum X = 0, Minimum Y = -1, Maximum X = 3, Maximum Y = 3
        
        >>> print(_testingValues[1].bounds())
        Minimum X = -1525, Minimum Y = 1289, Maximum X = -1522, Maximum Y = 1293
        
        >>> print(_testingValues[2].bounds())
        Minimum X = 12, Minimum Y = -127, Maximum X = 16, Maximum Y = -125
        """
        
        self = self.regularized()
        
        if not self:
            return rectangle.Rectangle()
        
        return rectangle.Rectangle(
          self.lo_x,
          self.hi_y - len(self),
          self.lo_x + len(self[0]),
          self.hi_y)
    
    def clipped(self, newImageRect):
        """
        Returns a new Bitmap object whose image intersects the specified new
        image Rectangle.
        
        >>> _testingValues[0].pprint()
           +++
           012
        +2 .X.
        +1 X.X
        +0 X.X
        -1 .X.
        Bit depth: 1
        Y-coordinate of topmost gridline: 3
        X-coordinate of leftmost gridline: 0
        
        >>> r = rectangle.Rectangle(1, 0, 10, 10)
        >>> _testingValues[0].clipped(r).pprint()
           ++
           12
        +2 X.
        +1 .X
        +0 .X
        Bit depth: 1
        Y-coordinate of topmost gridline: 3
        X-coordinate of leftmost gridline: 1
        """
        
        self = self.regularized()
        selfBounds = self.bounds()
        clipBounds = selfBounds.intersected(newImageRect)
        
        if not clipBounds:
            return type(self)()
        
        rowStart = clipBounds.yMax - selfBounds.yMax
        rowStop = rowStart + clipBounds.height()
        colStart = clipBounds.xMin - selfBounds.xMin
        colStop = colStart + clipBounds.width()
        
        return type(self)(
          (self[row][colStart:colStop] for row in range(rowStart, rowStop)),
          lo_x = self.lo_x + colStart,
          hi_y = self.hi_y - rowStart,
          bitDepth = self.bitDepth)
    
    def commonFrame(self, other):
        """
        Given two Bitmaps, determines the union boundary that fits both of
        them, and then creates new Bitmap objects for each, clipped to that
        Rectangle. Returns the pair (selfCommon, otherCommon).
        
        >>> for obj in _testingValues[0].commonFrame(_testingValues[3]):
        ...   obj.pprint()
           ++++
           0123
        +7 ....
        +6 ....
        +5 ....
        +4 ....
        +3 ....
        +2 .X..
        +1 X.X.
        +0 X.X.
        -1 .X..
        Bit depth: 1
        Y-coordinate of topmost gridline: 8
        X-coordinate of leftmost gridline: 0
           ++++
           0123
        +7 ....
        +6 ..X.
        +5 ....
        +4 ....
        +3 ....
        +2 ....
        +1 ....
        +0 ....
        -1 ....
        Bit depth: 1
        Y-coordinate of topmost gridline: 8
        X-coordinate of leftmost gridline: 0
        """
        
        unionRect = self.bounds().unioned(other.bounds())
        return self.fittedToRect(unionRect), other.fittedToRect(unionRect)
    
    def fittedToRect(self, r):
        """
        Returns a new Bitmap whose bounds match r, with contents moved
        appropriately. This may involve padding and/or clipping of edges.
        
        >>> r = rectangle.Rectangle(-3, -4, 13, 15)
        >>> _testingValues[0].fittedToRect(r).pprint()
            ---+++++++++++++
            0000000000000111
            3210123456789012
        +14 ................
        +13 ................
        +12 ................
        +11 ................
        +10 ................
        +09 ................
        +08 ................
        +07 ................
        +06 ................
        +05 ................
        +04 ................
        +03 ................
        +02 ....X...........
        +01 ...X.X..........
        +00 ...X.X..........
        -01 ....X...........
        -02 ................
        -03 ................
        -04 ................
        Bit depth: 1
        Y-coordinate of topmost gridline: 15
        X-coordinate of leftmost gridline: -3
        """
        
        # First, clip to r
        self = self.clipped(r)
        
        # Then, pad as needed
        v = [list(obj) for obj in self]
        selfBounds = self.bounds()
        newLowX = self.lo_x
        newHighY = self.hi_y
        
        # right edge first
        addCount = r.xMax - selfBounds.xMax
        
        if addCount > 0:  # can't be less, since we already clipped...
            extra = [0] * addCount
            
            for row in v:
                row.extend(extra)
        
        # left edge next
        addCount = selfBounds.xMin - r.xMin
        
        if addCount > 0:  # ditto
            extra = [0] * addCount
            newLowX -= addCount
            
            for row in v:
                row[0:0] = extra
        
        # Bottom edge next
        addCount = selfBounds.yMin - r.yMin
        
        while addCount > 0:  # ditto
            v.append([0] * len(v[0]))
            addCount -= 1
        
        # Top edge last
        addCount = r.yMax - selfBounds.yMax
        
        if addCount > 0:
            newHighY += addCount
        
        while addCount > 0:  # ditto
            v[0:0] = [[0] * len(v[0])]
            addCount -= 1
        
        return type(self)(
          v,
          lo_x = newLowX,
          hi_y = newHighY,
          bitDepth = self.bitDepth)
    
    def moved(self, deltaX=0, deltaY=0):
        """
        Returns a new Bitmap shifted as indicated.
        
        >>> _testingValues[0].pprint()
           +++
           012
        +2 .X.
        +1 X.X
        +0 X.X
        -1 .X.
        Bit depth: 1
        Y-coordinate of topmost gridline: 3
        X-coordinate of leftmost gridline: 0
        
        >>> _testingValues[0].moved(-2, 15).pprint()
            --+
            210
        +17 .X.
        +16 X.X
        +15 X.X
        +14 .X.
        Bit depth: 1
        Y-coordinate of topmost gridline: 18
        X-coordinate of leftmost gridline: -2
        """
        
        if not self:
            return self.__deepcopy__()
        
        return type(self)(
          self,
          lo_x = self.lo_x + deltaX,
          hi_y = self.hi_y + deltaY,
          bitDepth = self.bitDepth)
    
    def regularized(self):
        """
        Returns a new Bitmap whose rows are all of equal length. This may end
        up simply being a deep copy of self.
        
        >>> _testingValues[0].regularized() == _testingValues[0]
        True
        
        >>> obj = _testingValues[0].__deepcopy__()
        >>> obj[0].append(1)
        >>> print(list(obj.regularized()))
        [[0, 1, 0, 1], [1, 0, 1, 0], [1, 0, 1, 0], [0, 1, 0, 0]]
        """
        
        if not self:
            return self.__deepcopy__()
        
        lenSet = {len(row) for row in self}
        
        if len(lenSet) == 1:
            return self.__deepcopy__()
        
        maxLen = max(lenSet)
        it = (row + [0] * (maxLen - len(row)) for row in self)
        return type(self)(it, **self.__dict__)
    
    def transposed(self):
        """
        Returns a new Bitmap transposed from the original. Note the lo_x and
        hi_y values will not be changed; this can be interpreted as having the
        upper-left corner of the bitmap remain anchored during transposition.
        
        Note that the output Bitmap is not regularized.
        
        >>> _testingValues[2].pprint()
             + + + +
             1 1 1 1
             2 3 4 5
        -126 01000002
             29420455
        -127 00000001
             00153131
        Bit depth: 8
        Y-coordinate of topmost gridline: -125
        X-coordinate of leftmost gridline: 12
        
        >>> _testingValues[2].transposed().pprint()
             + +
             1 1
             2 3
        -126 0100
             2900
        -127 0000
             4215
        -128 0000
             0431
        -129 0201
             5531
        Bit depth: 8
        Y-coordinate of topmost gridline: -125
        X-coordinate of leftmost gridline: 12
        """
        
        if not self:
            return self.__deepcopy__()
        
        return type(self)(
          _transposed(self),
          lo_x = self.lo_x,
          hi_y = self.hi_y,
          bitDepth = self.bitDepth)
    
    def trimmed(self):
        """
        Returns a new Bitmap with any all-zero rows or columns at the edges
        removed.
        
        >>> _testingValues[3].pprint()
           +++
           123
        +7 ...
        +6 .X.
        +5 ...
        Bit depth: 1
        Y-coordinate of topmost gridline: 8
        X-coordinate of leftmost gridline: 1
        
        >>> _testingValues[3].trimmed().pprint()
           +
           2
        +6 X
        Bit depth: 1
        Y-coordinate of topmost gridline: 7
        X-coordinate of leftmost gridline: 2
        """
        
        if not self:
            return self.__deepcopy__()
        
        if len({len(row) for row in self}) > 1:
            # needs to be regularized
            self = self.regularized()
        
        rowStart = 0
        rowStop = len(self)
        colStart = 0
        colStop = len(self[0])
        newLowX = self.lo_x
        newHighY = self.hi_y
        
        while (rowStart < rowStop) and (not any(self[rowStart])):
            rowStart += 1
            newHighY -= 1
        
        while (rowStart < rowStop) and (not any(self[rowStop - 1])):
            rowStop -= 1
        
        flipped = _transposed(self)
        
        while (colStart < colStop) and (not any(flipped[colStart])):
            colStart += 1
            newLowX += 1
        
        while (colStart < colStop) and (not any(flipped[colStop - 1])):
            colStop -= 1
        
        if rowStart == rowStop or colStart == colStop:
            return type(self)()
        
        return type(self)(
          (self[row][colStart:colStop] for row in range(rowStart, rowStop)),
          lo_x = newLowX,
          hi_y = newHighY,
          bitDepth = self.bitDepth)
    
    def unioned(self, other):
        """
        Creates and returns a new Bitmap which represents the "union" of the
        two input Bitmaps. For given combining cells that contain differing
        nonzero values, the greater value is retained.
        
        The bitDepths of the two Bitmaps must match; a ValueError will be
        raised if they don't.
        
        >>> _testingValues[0].unioned(_testingValues[3]).pprint()
           ++++
           0123
        +7 ....
        +6 ..X.
        +5 ....
        +4 ....
        +3 ....
        +2 .X..
        +1 X.X.
        +0 X.X.
        -1 .X..
        Bit depth: 1
        Y-coordinate of topmost gridline: 8
        X-coordinate of leftmost gridline: 0
        
        >>> _testingValues[0].unioned(_testingValues[2])
        Traceback (most recent call last):
          ...
        ValueError: Bit depths must match for unioned()!
        """
        
        if self.bitDepth != other.bitDepth:
            raise ValueError("Bit depths must match for unioned()!")
        
        if not self:
            return other.__deepcopy__()
        
        if not other:
            return self.__deepcopy__()
        
        sCommon, oCommon = self.commonFrame(other)
        vNew = []
        
        for sRow, oRow in zip(sCommon, oCommon):
            vNew.append([max(x, oRow[i]) for i, x in enumerate(sRow)])
        
        return type(self)(
          vNew,
          lo_x = sCommon.lo_x,
          hi_y = sCommon.hi_y,
          bitDepth = sCommon.bitDepth)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Bitmap([[0, 1, 0], [1, 0, 1], [1, 0, 1], [0, 1, 0]], hi_y=3),
        Bitmap([[0, 1, 0], [1, 0, 1], [1, 0, 1], [0, 1, 0]], lo_x=-1525, hi_y=1293),
        Bitmap([[129, 42, 4, 255], [0, 15, 31, 131]], bitDepth=8, hi_y=-125, lo_x=12),
        Bitmap([[0, 0, 0], [0, 1, 0], [0, 0, 0]], lo_x=1, hi_y=8),
        Bitmap([[0, 1], [2, 3]], bitDepth=1))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
