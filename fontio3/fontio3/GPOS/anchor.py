#
# anchor.py
#
# Copyright © 2007-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Common anchor objects for OpenType tables.
"""

# Other imports
from fontio3.GPOS import anchor_coord, anchor_device, anchor_point, anchor_variation

# -----------------------------------------------------------------------------

#
# Private constants
#

_dispatch = (
  anchor_coord.Anchor_Coord,
  anchor_point.Anchor_Point,
  anchor_device.Anchor_Device)

# -----------------------------------------------------------------------------

#
# Functions
#

def Anchor(w, **kwArgs):
    """
    Factory function for Anchor objects of various classes.
    
    >>> w = walker.StringWalker(utilities.fromhex("00 01 FF E0 00 18"))
    >>> Anchor(w).pprint()
    x-coordinate: -32
    y-coordinate: 24
    """
    
    format = w.unpack("H", advance=False)
    
    if format not in {1, 2, 3}:
        raise ValueError("Unknown anchor format: %d" % format)
    
    if format == 3 and kwArgs.get('otcommondeltas'):
        fw = anchor_variation.Anchor_Variation.fromwalker
        return fw(w, **kwArgs)
    
    return _dispatch[format - 1].fromwalker(w, **kwArgs)

def Anchor_validated(w, **kwArgs):
    """
    Factory function for Anchor objects, with source validation.
    
    >>> w = walker.StringWalker(utilities.fromhex("00 01 FF E0 00 18"))
    >>> logger = utilities.makeDoctestLogger("anchor")
    >>> Anchor_validated(w, logger=logger).pprint()
    anchor.anchor_coord - DEBUG - Walker has 6 remaining bytes.
    x-coordinate: -32
    y-coordinate: 24
    """
    
    logger = kwArgs['logger']
    
    if w.length() < 2:
        logger.error(('V0004', (), "Insufficient bytes"))
        return None
    
    format = w.unpack("H", advance=False)
    
    if format not in {1, 2, 3}:
        logger.error((
          'E4100',
          (format,),
          "Unknown Anchor format %d."))
        
        return None
    
    if format == 3 and kwArgs.get('otcommondeltas'):
        fvw = anchor_variation.Anchor_Variation.fromvalidatedwalker
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

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
