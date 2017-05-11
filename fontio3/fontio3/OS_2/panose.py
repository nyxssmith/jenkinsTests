#
# panose.py
#
# Copyright © 2004-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for representations of PANOSE data for OS/2 tables.
"""

# System imports
import logging

# Other imports
from fontio3.OS_2 import (
  panose_fam0,
  panose_fam1,
  panose_fam2_v0,
  panose_fam2_v2,
  panose_fam3,
  panose_fam4,
  panose_fam5)
from fontio3 import utilities
from fontio3.utilities import walker

# -----------------------------------------------------------------------------

#
# Private constants
#

_dispatch = {
  0: panose_fam0.Panose_fam0,
  1: panose_fam1.Panose_fam1,
  (2,0): panose_fam2_v0.Panose_fam2,
  (2,2): panose_fam2_v2.Panose_fam2,
  3: panose_fam3.Panose_fam3,
  4: panose_fam4.Panose_fam4,
  5: panose_fam5.Panose_fam5}

# -----------------------------------------------------------------------------

#
# Functions
#

def Panose(w, **kwArgs):
    """
    Factory function for the various family-differentiated kinds of Panose
    objects.

    The 'os2panver' keyword is used to distinguish older OS/2 versions
    which used a different definition for family kind of 2 (Text and
    Display). If you want to have the values interpreted by that
    standard, pass in 'os2panver=0'.
    
    >>> w = walker.StringWalker(b'\x02\x01\x01\x01\x01\x05\x01\x01\x01\x01')
    >>> Panose(w).stroke
    'Gradual/Vertical'
    >>> w.reset()
    >>> Panose(w, os2panver=0).stroke
    'Gradual/Horizontal'
    """
    
    famKind = w.unpack("B", advance=False)
    os2panver = kwArgs.get('os2panver', 2)

    if famKind == 2:
        dKey = famKind,os2panver
    else:
        dKey = famKind
    
    if dKey not in _dispatch:
        raise ValueError("Unknown PANOSE family: %d" % (famKind,))
    
    return _dispatch[dKey].fromwalker(w, **kwArgs)

def Panose_validated(w, **kwArgs):
    r"""
    Factory function for the various family-differentiated kinds of Panose
    objects that does validation.
    
    The 'os2panver' keyword is used to distinguish older OS/2 versions
    which used a different definition for family kind of 2 (Text and
    Display). If you want to have the values interpreted by that
    standard, pass in 'os2panver=0'.
    
    >>> w = walker.StringWalker(b'\x02\x01\x01\x01\x01\x05\x01\x01\x01\xFF')
    >>> logger=utilities.makeDoctestLogger("Panose")
    >>> Panose_validated(w, logger=logger).stroke
    Panose.PANOSE.xHeight - ERROR - Value 255 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    'Gradual/Vertical'
    """
    
    famKind = w.unpack("B", advance=False)
    os2panver = kwArgs.get('os2panver', 2)
    
    if famKind == 2:
        dKey = famKind,os2panver
    else:
        dKey = famKind

    if dKey not in _dispatch:
        logger = kwArgs.pop('logger', logging.getLogger()).getChild('PANOSE')
        
        logger.error((
          'E2105',
          (famKind,),
          "Unknown PANOSE family kind: %d"))
        
        return None
    
    return _dispatch[dKey].fromvalidatedwalker(w, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

