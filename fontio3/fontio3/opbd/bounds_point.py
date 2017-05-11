#
# bounds_point.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the control-point format of 'opbd' bounds data.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class Bounds_Point(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing the actual positions of a single glyph's optical
    bounds. These are control point values within the glyph, or None.
    
    >>> print(_testingValues[0])
    Left point = 1, Top point = 2, Right point = 3, Bottom point = 4
    
    >>> _testingValues[1].pprint()  # only displays non-None values
    Top point: 10
    Bottom point: 0
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = _fakeEditor()
    >>> _testingValues[0].isValid(logger=logger, editor=e, glyphIndex=40)
    True
    
    >>> _testingValues[3].isValid(logger=logger, editor=e, glyphIndex=40)
    val.right - ERROR - Glyph 40 only contains 8 points; point index 45 is out of range.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        left = dict(
            attr_label = "Left point",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None),
            attr_validatefunc = valassist.isPointIndex),
        
        top = dict(
            attr_label = "Top point",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None),
            attr_validatefunc = valassist.isPointIndex),
        
        right = dict(
            attr_label = "Right point",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None),
            attr_validatefunc = valassist.isPointIndex),
        
        bottom = dict(
            attr_label = "Bottom point",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None),
            attr_validatefunc = valassist.isPointIndex))
    
    objSpec = dict(
        obj_enableordering = True)
    
    attrSorted = ('left', 'top', 'right', 'bottom')
    isDistance = False
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Bounds_Point object from the specified
        walker, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Bounds_Point.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.bounds_point - DEBUG - Walker has 8 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:1], logger=logger)
        fvw.bounds_point - DEBUG - Walker has 1 remaining bytes.
        fvw.bounds_point - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("bounds_point")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(*[(None if n == -1 else n) for n in w.group("h", 4)])
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Bounds_Point object from the data in the
        specified walker.
        
        >>> f = Bounds_Point.frombytes
        >>> _testingValues[0] == f(_testingValues[0].binaryString())
        True
        >>> _testingValues[1] == f(_testingValues[1].binaryString())
        True
        >>> _testingValues[2] == f(_testingValues[2].binaryString())
        True
        """
        
        v = [(None if n == -1 else n) for n in w.group("h", 4)]
        return cls(*v)
    
    #
    # Special methods
    #
    
    def __bool__(self):
        """
        We need a custom __bool__ method because a value of zero is good, while
        a value of None is not, and thus we need to distinguish them.
        
        >>> bool(_testingValues[1])
        True
        >>> bool(_testingValues[2])
        False
        """
        
        d = self.__dict__
        
        return any(
          d[k] is not None
          for k in ('left', 'top', 'right', 'bottom'))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Bounds_Point object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0002 0003 0004                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | FFFF 000A FFFF 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | FFFF FFFF FFFF FFFF                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        d = self.__dict__
        v = [d[k] for k in ('left', 'top', 'right', 'bottom')]
        w.addGroup("h", ((-1 if n is None else n) for n in v))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _fakeEditor():
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(0x10000)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        return e
    
    _testingValues = (
        Bounds_Point(1, 2, 3, 4),
        Bounds_Point(None, 10, None, 0),
        Bounds_Point(),
        
        # bad testing values start here
        
        Bounds_Point(None, None, 45, None))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
