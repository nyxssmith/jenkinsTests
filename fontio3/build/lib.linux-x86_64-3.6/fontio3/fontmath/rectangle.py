#
# rectangle.py
#
# Copyright © 2004-2006, 2011-2012, 2017 Monotype Imaging Inc. All Rights Reserved.
#

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.fontmath import point

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if obj.xMin > obj.xMax:
        logger.error(('G0016', (), "Rectangle xMin > xMax"))
        return False
    
    if obj.yMin > obj.yMax:
        logger.error(('G0017', (), "Rectangle yMin > yMax"))
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Rectangle(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing rectangles. Conceptually the coordinate values
    associated with a Rectangle refer to the infinitely thin lines surrounding
    the rectangle, and not pixel centers or pixel coordinates.
    
    These are simple objects with 4 signed integer attributes: xMin, yMin,
    xMax, and yMax (in that order).
    
    >>> logger = utilities.makeDoctestLogger("rectangle")
    >>> r = Rectangle(5, 10, 10, 40)
    >>> r.isValid(logger=logger)
    True
    
    >>> r = Rectangle(10, 40, 5, 100)
    >>> r.isValid(logger=logger)
    rectangle - ERROR - Rectangle xMin > xMax
    False
    
    >>> r = Rectangle(5, 100, 10, 40)
    >>> r.isValid(logger=logger)
    rectangle - ERROR - Rectangle yMin > yMax
    False
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        xMin = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Minimum X",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'yMin'),
        
        yMin = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Minimum Y",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'xMin'),
        
        xMax = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Maximum X",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'yMax'),
        
        yMax = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Maximum Y",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'xMax'))
    
    attrSorted = ('xMin', 'yMin', 'xMax', 'yMax')
    
    #
    # Class methods
    #
    
    @classmethod
    def frompoints(cls, p1, p2):
        """
        Creates and returns a Rectangle from the two specified Points.
        
        >>> P = point.Point
        >>> Rectangle.frompoints(P(5, 20), P(-10, -10)).pprint()
        Minimum X: -10
        Minimum Y: -10
        Maximum X: 5
        Maximum Y: 20
        """
        
        return cls(
          min(p1.x, p2.x),
          min(p1.y, p2.y),
          max(p1.x, p2.x),
          max(p1.y, p2.y))
    
    #
    # Special methods
    #
    
    def __bool__(self):
        """
        Returns True if the Rectangle is not empty.
        
        >>> bool(_testingValues[0])
        False
        >>> bool(_testingValues[1])
        True
        >>> bool(_testingValues[3])
        False
        """
        
        return (self.xMin != self.xMax) and (self.yMin != self.yMax)
    
    #
    # Public methods
    #
    
    def area(self):
        """
        Returns the area.
        
        >>> _testingValues[1].area()
        9600
        """
        
        return self.width() * self.height()
    
    def asList(self):
        """
        Returns a simple list with the 4 values in attrSorted order.
        
        >>> _testingValues[1].asList()
        [10, -20, 90, 100]
        """
        
        return [self.xMin, self.yMin, self.xMax, self.yMax]
    
    def center(self):
        """
        Returns a Point representing the center of the rectangle.
        
        >>> print(_testingValues[1].center())
        (50.0, 40.0)
        """
        
        return point.Point(
          (self.xMin + self.xMax) / 2,
          (self.yMin + self.yMax) / 2)
    
    def corners(self):
        """
        Returns a tuple with the two corners as Points.
        
        >>> for obj in _testingValues[1].corners(): print(obj)
        (10, -20)
        (90, 100)
        """
        
        p1 = point.Point(self.xMin, self.yMin)
        p2 = point.Point(self.xMax, self.yMax)
        return (p1, p2)
    
    def height(self):
        """
        Returns the height.
        
        >>> _testingValues[1].height()
        120
        """
        
        return self.yMax - self.yMin
    
    def intersected(self, other):
        """
        Returns a new Rectangle representing the common intersection of the two
        input Rectangles.
        
        >>> print(_testingValues[1].intersected(_testingValues[2]))
        Minimum X = 10, Minimum Y = 5, Maximum X = 90, Maximum Y = 80
        
        >>> print(_testingValues[1].intersected(_testingValues[3]))
        Minimum X = 0, Minimum Y = 0, Maximum X = 0, Maximum Y = 0
        
        >>> R1 = Rectangle(0, 10, 50, 50)
        >>> R2 = Rectangle(70, 80, 140, 100)
        >>> print(R1.intersected(R2))
        Minimum X = 0, Minimum Y = 0, Maximum X = 0, Maximum Y = 0
        
        >>> R1 = Rectangle(0, 10, 50, 50)
        >>> R2 = Rectangle(10, 80, 40, 100)
        >>> print(R1.intersected(R2))
        Minimum X = 0, Minimum Y = 0, Maximum X = 0, Maximum Y = 0
        """
        
        if (not self) or (not other):
            return type(self)()
        
        if self.xMax < other.xMin or self.xMin > other.xMax:
            return type(self)()
        
        if self.yMax < other.yMin or self.yMin > other.yMax:
            return type(self)()
        
        return type(self)(
          max(self.xMin, other.xMin), max(self.yMin, other.yMin),
          min(self.xMax, other.xMax), min(self.yMax, other.yMax))
    
    def isEmpty(self):
        """
        Returns True if either dimension is zero.
        
        >>> _testingValues[0].isEmpty()
        True
        >>> _testingValues[1].isEmpty()
        False
        """
        
        return (self.xMin == self.xMax) or (self.yMin == self.yMax)
    
    def overlapDegrees(self, other):
        """
        Returns a pair of floating-point numbers representing ratios of the
        area of the intersection Rectangle to the areas of the two specified
        Rectangles.
        
        >>> _testingValues[1].overlapDegrees(_testingValues[1])
        (1.0, 1.0)
        
        >>> _testingValues[1].overlapDegrees(_testingValues[2])
        (0.625, 0.6956521739130435)
        
        >>> _testingValues[0].overlapDegrees(_testingValues[1])
        (0.0, 0.0)
        """
        
        area1 = self.area()
        area2 = other.area()
        sectArea = self.intersected(other).area()
        
        return (
          (sectArea / area1 if area1 else 0.0),
          (sectArea / area2 if area2 else 0.0))
    
    def unioned(self, other):
        """
        Returns a new Rectangle with values that exactly cover both inputs.
        
        >>> print(_testingValues[1].unioned(_testingValues[2]))
        Minimum X = 5, Minimum Y = -20, Maximum X = 120, Maximum Y = 100
        
        >>> print(_testingValues[1].unioned(_testingValues[3]))
        Minimum X = 10, Minimum Y = -20, Maximum X = 90, Maximum Y = 100
        
        >>> print(_testingValues[3].unioned(_testingValues[1]))
        Minimum X = 10, Minimum Y = -20, Maximum X = 90, Maximum Y = 100
        
        >>> print(_testingValues[3].unioned(_testingValues[3]))
        Minimum X = 20, Minimum Y = -5, Maximum X = 20, Maximum Y = 100
        """
        
        return type(self)(
          min(self.xMin, other.xMin),
          min(self.yMin, other.yMin),
          max(self.xMax, other.xMax),
          max(self.yMax, other.yMax))
    
    def width(self):
        """
        Returns the width.
        
        >>> _testingValues[1].width()
        80
        """
        
        return self.xMax - self.xMin

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Rectangle(),
        Rectangle(10, -20, 90, 100),
        Rectangle(5, 5, 120, 80),
        Rectangle(20, -5, 20, 100))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
