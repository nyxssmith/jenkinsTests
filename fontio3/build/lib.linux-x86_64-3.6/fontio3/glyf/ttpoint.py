#
# ttpoint.py
#
# Copyright © 2004-2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
TrueType points, as used in glyph descriptions.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.fontmath import point

# -----------------------------------------------------------------------------

#
# Classes
#

class TTPoint(point.Point):
    """
    Objects representing single TrueType points. These are simple objects with
    the following attributes:
    
        x
        y
        onCurve
    
    Note that TTPoints do not have fromwalker() or buildBinary() methods; those
    functions are handled at a higher level, given the convoluted nature of the
    TrueType 'glyf' table.
    
    >>> print(_testingValues[0])
    (0, 0), on-curve
    
    >>> print(_testingValues[2])
    (100, -200), off-curve
    
    These objects are immutable:
    >>> d = {TTPoint(1, 2, onCurve=True): 5, TTPoint(1, 2, onCurve=False): 4}
    >>> len(d)
    2
    
    >>> print(_testingValues[1].magnified(1.5, 1.5))
    (150.0, -300.0), on-curve
    
    >>> print(_testingValues[1].magnified(1.0, 1.5))
    (100.0, -300.0), on-curve
    
    The following example shows how to rotate a TTPoint around the point
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
    
    #seqSpec = dict(item_roundfunc = utilities.truncateRound)
    seqSpec = dict(item_roundfunc = utilities.oldRound)
    
    attrSpec = dict(
        onCurve = dict(
            attr_initfunc = (lambda: True),
            attr_label = "On-curve"))
    
    _ocStr = ["off-curve", "on-curve"]
    
    #
    # Special methods
    #
    
    def __str__(self):
        """
        """
        
        return "(%s, %s), %s" % (self.x, self.y, self._ocStr[self.onCurve])
    
    #
    # Public methods
    #
    
    def asList(self):
        """
        Returns a list with the values in the canonical order.
        
        >>> _testingValues[1].asList()
        [100, -200, True]
        """
        
        return [self.x, self.y, self.onCurve]
    
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
        TTPoint(0, 0),
        TTPoint(100, -200),
        TTPoint(100, -200, onCurve=False),
        TTPoint(80, 180, onCurve=True),
        
        # values [4:8] are a rectangular contour's clockwise corners
        TTPoint(20, 10, onCurve=True),
        TTPoint(20, 490, onCurve=True),
        TTPoint(380, 490, onCurve=True),
        TTPoint(380, 10, onCurve=True),
        
        # values [8:12] are like [4:8] shifted right and up by 600)
        TTPoint(620, 610, onCurve=True),
        TTPoint(620, 1090, onCurve=True),
        TTPoint(980, 1090, onCurve=True),
        TTPoint(980, 610, onCurve=True),
        
        # values [12:16] are a counter-clockwise cutout for [8:12]
        TTPoint(750, 750, onCurve=True),
        TTPoint(850, 700, onCurve=False),
        TTPoint(950, 750, onCurve=True),
        TTPoint(850, 1000, onCurve=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
