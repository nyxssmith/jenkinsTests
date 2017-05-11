#
# coordinate.py
#
# Copyright © 2010, 2012, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Factory function for making the three kinds of coordinate objects.
"""

# System imports
import logging

# Other imports
from fontio3.BASE import coordinate_device, coordinate_point, coordinate_simple, coordinate_variation

# -----------------------------------------------------------------------------

#
# Private constants
#

_dispatch = (
  coordinate_simple.Coordinate_simple,
  coordinate_point.Coordinate_point,
  coordinate_device.Coordinate_device)

# -----------------------------------------------------------------------------

#
# Functions
#

def Coordinate(w, **kwArgs):
    """
    A factory function that creates and returns a new Coordinate_simple,
    Coordinate_point, Coordinate_device, or Coordinate_variation object, based
    on the format in the first two bytes of the specified walker.
    
    >>> bs = utilities.fromhex("0001 00AB")
    >>> w = walker.StringWalker(bs)
    >>> Coordinate(w).pprint()
    Coordinate: 171
    """
    
    format = w.unpack("H", advance=False)
    
    if format not in {1, 2, 3}:
        raise ValueError("Unknown anchor format: %d" % (format,))

    if format == 3 and kwArgs.get('otcommondeltas'):
        fw = coordinate_variation.Coordinate_variation.fromwalker
        return fw(w, **kwArgs)

    return _dispatch[format-1].fromwalker(w, **kwArgs)


def Coordinate_validated(w, **kwArgs):
    """
    A factory function that creates and returns a new Coordinate_simple,
    Coordinate_point, Coordinate_device, or Coordinate_variation object, based
    on the format in the first two bytes of the specified walker. This does
    source validation.

    >>> bs = utilities.fromhex("0001 00AB")
    >>> w = walker.StringWalker(bs)
    >>> logger = utilities.makeDoctestLogger("test")
    >>> Coordinate_validated(w, logger=logger).pprint()
    test.coordinate - DEBUG - Coordinate format 1.
    test.coordinate_simple - DEBUG - Walker has 4 remaining bytes.
    Coordinate: 171
    
    >>> bs = utilities.fromhex("0003 00AB 0006 0000 0001 8000")
    >>> fakeDeltas = {(0,1): "FakeLivingDelta"}
    >>> w = walker.StringWalker(bs)
    >>> obj = Coordinate_validated(w, logger=logger, otcommondeltas=fakeDeltas)
    test.coordinate - DEBUG - Coordinate format 3.
    test.coordinate_variation - DEBUG - Walker has 12 remaining bytes.
    test.coordinate_variation.device - DEBUG - Walker has 6 remaining bytes.
    test.coordinate_variation.device - DEBUG - VariationIndex (0, 1)
    test.coordinate_variation - DEBUG - LivingDeltas FakeLivingDelta
    >>> int(obj)
    171
    >>> obj.variation
    'FakeLivingDelta'
    """
    
    logger = kwArgs.get('logger', None)
    if logger is None:
        logger = logging.getLogger().getChild('coordinate')
    else:
        logger = logger.getChild('coordinate')
    
    if w.length() < 2:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    format = w.unpack("H", advance=False)
    
    if format not in {1, 2, 3}:
        logger.error((
          'V0002',
          (format,),
          "Unknown Coordinate format %d."))
          
        return None

    logger.debug((
      'Vxxxx',
      (format,),
      "Coordinate format %d."))

    if format == 3 and kwArgs.get('otcommondeltas'):
        fvw = coordinate_variation.Coordinate_variation.fromvalidatedwalker
        return fvw(w, **kwArgs)
        
    return _dispatch[format - 1].fromvalidatedwalker(w, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walker
    
    _sv = coordinate_simple._testingValues
    _pv = coordinate_point._testingValues
    _dv = coordinate_device._testingValues
    
    _testingValues = _sv[1:4] + _pv[0:2] + _dv[0:3]
    assert len(_testingValues) == 8
    
    del _dv, _pv, _sv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
