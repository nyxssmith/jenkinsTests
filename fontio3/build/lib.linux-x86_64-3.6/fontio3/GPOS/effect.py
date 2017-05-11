#
# effect.py
#
# Copyright © 2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for objects used to identify positioning effects from the effects()
call for all the GPOS subtables. This positioning covers both tweaks (like for
kerning) and move-and-return (for attachment).
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Effect(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing the cumulative effects upon the origin and advance of
    a glyph. See the attribute descriptions below for more details.
    
    These are the attributes; note their ordering is defined in attrSorted:
    
        backIndex           If this glyph is not a combining mark, this
                            attribute will be None. Otherwise it will be
                            relative index within the glyph array to the glyph
                            to which this one is attaching. Note this might be
                            another mark!
        
        xAdvanceDelta       The amount in X by which to alter the glyph's
                            advance. This will need to be added to the
                            font-specified advance by the drawing engine.
        
        xPlacementDelta     The amount to move the pen in X before this glyph
                            is drawn. You can think of the pen implicitly
                            "snapping back" to the original origin before the
                            advance is then applied.
        
        yAdvanceDelta       The amount in Y by which to alter the glyph's
                            advance. This will need to be added to the
                            font-specified advance by the drawing engine.
        
        yPlacementDelta     The amount to move the pen in Y before this glyph
                            is drawn. You can think of the pen implicitly
                            "snapping back" to the original origin before the
                            advance is then applied.
    
    >>> Effect(yPlacementDelta=-30, xAdvanceDelta=25).pprint()
    yPlacementDelta: -30
    xAdvanceDelta: 25
    """
    
    attrSpec = dict(
        backIndex = dict(
            attr_showonlyiffunc = (lambda x: x is not None)),
        
        xAdvanceDelta = dict(
            attr_initfunc = (lambda: 0),
            attr_representsx = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'yAdvanceDelta'),
        
        xPlacementDelta = dict(
            attr_initfunc = (lambda: 0),
            attr_representsx = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'yPlacementDelta'),
        
        yAdvanceDelta = dict(
            attr_initfunc = (lambda: 0),
            attr_representsy = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'xAdvanceDelta'),
        
        yPlacementDelta = dict(
            attr_initfunc = (lambda: 0),
            attr_representsy = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'xPlacementDelta'))
    
    attrSorted = (
      'xPlacementDelta',
      'yPlacementDelta',
      'xAdvanceDelta',
      'yAdvanceDelta',
      'backIndex')
    
    #
    # Methods
    #
    
    def add(self, other):
        """
        Adds all of other's values to self's values. Note this modifies self
        in-place! If you don't want this, use added().
        
        A ValueError will be raised if the two objects' backIndex values are
        both non-None but are numerically unequal. If only one backIndex is
        None, the non-None value will be used.
        
        >>> obj1 = Effect(yPlacementDelta=15, xAdvanceDelta=25)
        >>> obj2 = Effect(xPlacementDelta=-60, xAdvanceDelta=10)
        >>> obj1.pprint()
        yPlacementDelta: 15
        xAdvanceDelta: 25
        
        >>> obj1.add(obj2)
        >>> obj1.pprint()
        xPlacementDelta: -60
        yPlacementDelta: 15
        xAdvanceDelta: 35
        
        >>> obj3 = Effect(backIndex=-2)
        >>> obj1.add(obj3)
        >>> obj1.pprint()
        xPlacementDelta: -60
        yPlacementDelta: 15
        xAdvanceDelta: 35
        backIndex: -2
        
        >>> obj3.backIndex = -4
        >>> obj1.add(obj3)
        Traceback (most recent call last):
          ...
        ValueError: Cannot combine Effect objects with unequal backIndex values!
        """
        
        if other.backIndex is not None:
            if self.backIndex is None:
                self.backIndex = other.backIndex
            
            elif self.backIndex != other.backIndex:
                raise ValueError(
                  "Cannot combine Effect objects with unequal "
                  "backIndex values!")
        
        self.xPlacementDelta += other.xPlacementDelta
        self.yPlacementDelta += other.yPlacementDelta
        self.xAdvanceDelta += other.xAdvanceDelta
        self.yAdvanceDelta += other.yAdvanceDelta
    
    def added(self, other):
        """
        Returns a new Effect object with all of other's values added to self's
        values. If you want to modify self in-place, use add().
        
        >>> obj1 = Effect(yPlacementDelta=15, xAdvanceDelta=25)
        >>> obj2 = Effect(xPlacementDelta=-60, xAdvanceDelta=10)
        >>> obj1.pprint()
        yPlacementDelta: 15
        xAdvanceDelta: 25
        
        >>> r = obj1.added(obj2)
        >>> obj1.pprint()
        yPlacementDelta: 15
        xAdvanceDelta: 25
        >>> r.pprint()
        xPlacementDelta: -60
        yPlacementDelta: 15
        xAdvanceDelta: 35
        """
        
        r = self.__copy__()
        r.add(other)
        return r
    
    def any(self):
        """
        Returns True if at least one of the x or y deltas is nonzero. Returns
        False otherwise.
        
        >>> Effect().any()
        False
        >>> Effect(backIndex=-2).any()
        False
        >>> Effect(xPlacementDelta=10).any()
        True
        """
        
        return bool(
          self.xPlacementDelta or
          self.yPlacementDelta or
          self.xAdvanceDelta or
          self.yAdvanceDelta)
    
    @classmethod
    def fromvalue(cls, valueObj, **kwArgs):
        """
        Given a Value object, returns a new Effect object that captures its
        values. Note that backIndex is not affected here!
        
        >>> vObj = value.Value(xPlacement=25, yAdvance=-30)
        >>> Effect.fromvalue(vObj).pprint()
        xPlacementDelta: 25
        yAdvanceDelta: -30
        """
        
        if valueObj is None:
            return cls()
        
        coordLAC = kwArgs.get('coordinateTuple', None)
        
        if valueObj.xPlaVariation is not None:
            xPlaDelta = int(round(valueObj.xPlaVariation.interpolate(coordLAC)))
        else:
            xPlaDelta = 0
        
        if valueObj.yPlaVariation is not None:
            yPlaDelta = int(round(valueObj.yPlaVariation.interpolate(coordLAC)))
        else:
            yPlaDelta = 0
        
        if valueObj.xAdvVariation is not None:
            xAdvDelta = int(round(valueObj.xAdvVariation.interpolate(coordLAC)))
        else:
            xAdvDelta = 0
        
        if valueObj.yAdvVariation is not None:
            yAdvDelta = int(round(valueObj.yAdvVariation.interpolate(coordLAC)))
        else:
            yAdvDelta = 0
        
        r = cls(
          valueObj.xPlacement + xPlaDelta,
          valueObj.yPlacement + yPlaDelta,
          valueObj.xAdvance + xAdvDelta,
          valueObj.yAdvance + yAdvDelta)
        
        return r
    
    def toPair(self, forHorizontal=True):
        """
        Returns a 2-element tuple with the (posDelta, negDelta) values used by
        effectExtrema. These will be the Y deltas for horizontal text, and the
        X deltas for vertical text (i.e. the cross-stream distances).
        
        Note that the backIndex is ignored here.
        """
        
        if forHorizontal:
            return tuple((
              max(0, self.yPlacementDelta),
              min(0, self.yPlacementDelta)))
        
        return tuple((
          max(0, self.xPlacementDelta),
          min(0, self.xPlacementDelta)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.GPOS import value

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
