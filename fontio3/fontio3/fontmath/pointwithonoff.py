#
# pointwithonoff.py
#
# Copyright © 2004-2011, 2013, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Points with indications of on-curve status, as used in glyph descriptions for
both TrueType and CFF contours.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.fontmath import point

# -----------------------------------------------------------------------------

#
# Classes
#

class PointWithOnOff(point.Point):
    """
    Objects representing single points which indicate whether they're on-curve
    or off-curve. These are Point objects (i.e. named tuples with 'x' and 'y'
    as the [0] and [1] elements) with an attribute named 'onCurve'.
    
    Note that PointWithOnOffs do not have fromwalker() or buildBinary()
    methods; those functions are handled at a higher level, given the
    convoluted nature of both the TrueType 'glyf' table and the 'CFF ' table.
    
    >>> print(_testingValues[0])
    (0, 0), on-curve
    
    >>> print(_testingValues[2])
    (100, -200), off-curve
    
    These objects are immutable:
    >>> d = {PointWithOnOff(1, 2, onCurve=True): 5, PointWithOnOff(1, 2, onCurve=False): 4}
    >>> len(d)
    2
    
    >>> print(_testingValues[1].magnified(1.5, 1.5))
    (150.0, -300.0), on-curve
    
    >>> print(_testingValues[1].magnified(1.0, 1.5))
    (100.0, -300.0), on-curve
    
    The following example shows how to rotate a PointWithOnOff around the point
    (50, 120).
    
    >>> m = matrix.Matrix.forShift(-50, -120)
    >>> m = m.multiply(matrix.Matrix.forRotation(90))  # counterclockwise
    >>> m = m.multiply(matrix.Matrix.forShift(50, 120))
    >>> print(_testingValues[2].transformed(m))
    (370, 170), off-curve
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_roundfunc = utilities.oldRound)
    
    attrSpec = dict(
        onCurve = dict(
            attr_initfunc = (lambda: True),
            attr_label = "On-curve"))
    
    _ocStr = ["off-curve", "on-curve"]
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a custom string representation of the object.
        """
        
        return "(%s, %s), %s" % (self.x, self.y, self._ocStr[self.onCurve])
    
    def asList(self):
        """
        Returns a list with the values in the canonical order.
        
        >>> _testingValues[1].asList()
        [100, -200, True]
        """
        
        return [self.x, self.y, self.onCurve]
    
    @classmethod
    def fromTTPoint(cls, ttp):
        """
        Class method to explicitly convert a TTPoint (as used in fontio3.glyf)
        into a PointWithOnOff.
        
        >>> p = _makeTTPoint(20, 25, False)
        >>> print(PointWithOnOff.fromTTPoint(p).simpleStr())
        (20, 25), off-curve
        """
        
        r = cls(ttp.x, ttp.y)
        r.onCurve = ttp.onCurve
        return r
    
    def simpleStr(self):
        """
        Returns a simplified string representation of the point.
        
        >>> print(_testingValues[0].simpleStr())
        (0, 0), on-curve
        
        >>> print(_testingValues[2].simpleStr())
        (100, -200), off-curve
        """
        
        s = ("on-curve" if self.onCurve else "off-curve")
        return "(%d, %d), %s" % (self.x, self.y, s)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.fontmath import matrix
    
    _testingValues = (
        PointWithOnOff(0, 0),
        PointWithOnOff(100, -200),
        PointWithOnOff(100, -200, onCurve=False),
        PointWithOnOff(80, 180, onCurve=True),
        
        # values [4:8] are a rectangular contour's clockwise corners
        PointWithOnOff(20, 10, onCurve=True),
        PointWithOnOff(20, 490, onCurve=True),
        PointWithOnOff(380, 490, onCurve=True),
        PointWithOnOff(380, 10, onCurve=True),
        
        # values [8:12] are like [4:8] shifted right and up by 600)
        PointWithOnOff(620, 610, onCurve=True),
        PointWithOnOff(620, 1090, onCurve=True),
        PointWithOnOff(980, 1090, onCurve=True),
        PointWithOnOff(980, 610, onCurve=True),
        
        # values [12:16] are a counter-clockwise cutout for [8:12]
        PointWithOnOff(750, 750, onCurve=True),
        PointWithOnOff(850, 700, onCurve=False),
        PointWithOnOff(950, 750, onCurve=True),
        PointWithOnOff(850, 1000, onCurve=True))
    
    def _makeTTPoint(x, y, onCurve):
        from fontio3.glyf import ttpoint
        
        return ttpoint.TTPoint(x, y, onCurve=onCurve)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
