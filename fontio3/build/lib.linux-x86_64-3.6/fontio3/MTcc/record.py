#
# record.py
#
# Copyright © 2008-2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to cursive connection records (parts of an MTcc table).
"""

# System imports
import itertools

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.MTcc import point

# -----------------------------------------------------------------------------

#
# Classes
#

class Record(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a group of cursive connection points for both entry
    and exit in both x and y.
    
    The data format is:
        entryX (CursiveConnectionPoint)
        exitX (CursiveConnectionPoint)
        entryY (CursiveConnectionPoint)
        exitY (CursiveConnectionPoint)
    
    >>> _testingValues[1].pprint()
    Horizontal entry:
      Connection type: True
      Point index: 69
      X-coordinate: -16
      Y-coordinate: 5
    Horizontal exit:
      Connection type: False
      Point index: 12
      X-coordinate: 30
      Y-coordinate: -30
    Vertical entry:
      Connection type: True
      Point index: 4
      X-coordinate: 0
      Y-coordinate: -90
    Vertical exit:
      Connection type: False
      Point index: (no data)
      X-coordinate: -100
      Y-coordinate: 100
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        entryX = dict(
            attr_followsprotocol = True,
            attr_initfunc = point.Point,
            attr_label = "Horizontal entry"),
        
        exitX = dict(
            attr_followsprotocol = True,
            attr_initfunc = point.Point,
            attr_label = "Horizontal exit"),
        
        entryY = dict(
            attr_followsprotocol = True,
            attr_initfunc = point.Point,
            attr_label = "Vertical entry"),
        
        exitY = dict(
            attr_followsprotocol = True,
            attr_initfunc = point.Point,
            attr_label = "Vertical exit"))
    
    attrSorted = ('entryX', 'exitX', 'entryY', 'exitY')
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Record object from the specified walker.
        
        >>> _testingValues[1] == Record.frombytes(_testingValues[1].binaryString())
        True
        """
        
        fw = point.Point.fromwalker
        return cls(*map(fw, itertools.repeat(w, 4)))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the xxx object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0045 FFF0 0005  0000 000C 001E FFE2 |...E............|
              10 | 0001 0004 0000 FFA6  0000 FFFF FF9C 0064 |...............d|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self.entryX.buildBinary(w, **kwArgs)
        self.exitX.buildBinary(w, **kwArgs)
        self.entryY.buildBinary(w, **kwArgs)
        self.exitY.buildBinary(w, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _pv = point._testingValues
    
    _testingValues = (
        Record(),
        Record(_pv[1], _pv[2], _pv[3], _pv[4]))
    
    del _pv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
