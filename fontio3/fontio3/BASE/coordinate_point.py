#
# coordinate_point.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Items relating to hinted coordinate values for OpenType BASE tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import valuemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    r = True
    
    if e is None or (not e.reallyHas(b'head')) or (not e.reallyHas(b'glyf')):
        logger.warning((
          'V0553',
          (),
          "Unable to perform validation because one or more required "
          "tables (or the Editor itself) is missing."))
        
        return True
    
    if obj.glyph in e.glyf:
        thisGlyph = e.glyf[obj.glyph]
        
        try:
            p = int(obj.point)
            count = thisGlyph.pointCount(editor=e)
        
        except:
            return True  # will be caught in valuemeta isValid()
        
        if p >= count:
            logger.error((
              'V0638',
              (p, obj.glyph),
              "Point index %d does not exist in glyph %s."))
            
            r = False
    
    # The else clause is not done here; the valuemeta isValid()
    # code will handle that.
    
    try:
        n = int(round(obj))
    except:
        n = None
    
    # Note that if the value n is None (i.e. conversion or rounding failed)
    # the error is not raised here. Since this function is a partial, the
    # valuemeta isValid() checks will still be done, and the error will be
    # raised there instead.
    
    if n is not None:
        upem = e.head.unitsPerEm
        
        if abs(n) >= 2 * upem:
            logger.warning((
              'V0637',
              (n,),
              "The FUnit value %d is more than two ems away "
              "from the origin, which seems unlikely."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Coordinate_point(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing a coordinate value, a single integer in FUnits. This
    will be interpreted as X or Y depending on whether the object containing it
    is part of the horizontal or vertical baseline data.
    
    In addition, there are the following attributes:
    
        glyph   A reference glyph containing a point (see below) whose hinted
                location will be used as the baseline value.
        
        point   The point within the glyph to be used.
    
    >>> _testingValues[0].pprint()
    Coordinate: 0
    Glyph: 25
    Point: 9
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Coordinate: 0
    Glyph: xyz26
    Point: 9
    
    >>> print(_testingValues[1])
    -10, Glyph = 14, Point = 12
    
    Note that "glyphIndex" does not explicitly need to be set for calls to
    pointsRenumbered, as it is taken from the "glyph" attribute:
    
    >>> print(_testingValues[1].pointsRenumbered({14: {12: 9}}))
    -10, Glyph = 14, Point = 9
    
    >>> logger = utilities.makeDoctestLogger("coordinate_point_test")
    >>> e = _fakeEditor()
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    coordinate_point_test.glyph - ERROR - Glyph index 300 too large.
    False
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    coordinate_point_test - ERROR - Point index 30 does not exist in glyph 40.
    False
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_pprintlabel = "Coordinate",
        value_scales = True,
        value_validatefunc_partial = _validate)
    
    attrSpec = dict(
        glyph = dict(
            attr_label = "Glyph",
            attr_renumberdirect = True,
            attr_usenamerforstr = True),
        
        point = dict(
            attr_label = "Point",
            attr_renumberpointsdirect = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Coordinate_point object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0002 0000 0019 0009                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 FFF6 000E 000C                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("Hh2H", 2, self, self.glyph, self.point)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Coordinate_point object from the specified
        walker, doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("coordinate_point_fvw")
        >>> fvb = Coordinate_point.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        coordinate_point_fvw.coordinate_point - DEBUG - Walker has 8 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:3], logger=logger)
        coordinate_point_fvw.coordinate_point - DEBUG - Walker has 3 remaining bytes.
        coordinate_point_fvw.coordinate_point - ERROR - Insufficient bytes.
        
        >>> fvb(s[4:6] + s[0:4] + s[6:], logger=logger)
        coordinate_point_fvw.coordinate_point - DEBUG - Walker has 8 remaining bytes.
        coordinate_point_fvw.coordinate_point - ERROR - Expected format 2, but got 14 instead.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("coordinate_point")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, n, glyph, point = w.unpack("Hh2H")
        
        if format != 2:
            logger.error((
              'V0002',
              (format,),
              "Expected format 2, but got %d instead."))
            
            return None
        
        return cls(n, glyph=glyph, point=point)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Coordinate_point object from the specified
        walker.
        
        >>> for i in (0, 1):
        ...     obj = _testingValues[i]
        ...     print(obj == Coordinate_point.frombytes(obj.binaryString()))
        True
        True
        """
        
        format = w.unpack("H")
        
        if format != 2:
            raise ValueError(
              "Unknown format for Coordinate_point: %d" % (format,))
        
        n, glyph, point = w.unpack("h2H")
        return cls(n, glyph=glyph, point=point)
    
    def pointsRenumbered(self, mapData, **kwArgs):
        kwArgs['glyphIndex'] = self.glyph
        return valuemeta.M_pointsRenumbered(self, mapData, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    def _fakeEditor():
        from fontio3.head import head
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(200)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        e.head = head.Head()
        return e
    
    _testingValues = (
        Coordinate_point(0, 25, 9),
        Coordinate_point(-10, 14, 12),
        Coordinate_point(-75, 40, 5),
        # bad values start here
        Coordinate_point(-75, 300, 5),
        Coordinate_point(-75, 40, 30))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
