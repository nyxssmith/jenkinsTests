#
# psextension.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for extension subtables for GPOS and GSUB tables.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class PSExtension(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing PSExtension tables. These are very simple wrappers,
    being simple objects with a single attribute:
    
        original    The original subtable.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    original:
      afii60003:
        Device for origin's x-coordinate:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
        Device for origin's y-coordinate:
          Tweak at 12 ppem: -5
          Tweak at 13 ppem: -3
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 2
          Tweak at 20 ppem: 3
      xyz46:
        FUnit adjustment to origin's x-coordinate: 30
        Device for vertical advance:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
      xyz6:
        FUnit adjustment to origin's x-coordinate: -10
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        original = dict(
            attr_followsprotocol = True))
    
    #
    # There are no fromwalker() or fromvalidatedwalker() methods for
    # PSExtension objects, as that functionality is handled directly
    # within the Lookup.fromwalker() method itself.
    #
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. The following
        keyword arguments are used:
        
            extensionPool   A dict mapping the id() of non-extension objects to
                            (sortOrderValue, object, stake) triples. At
                            buildBinary time for the top-level object (the GPOS
                            table, in this case), once the lookups have all
                            been added then the pool's values should be sorted
                            and then walked, and those pool tables added. Their
                            32-bit offsets will have already been staked here,
                            and the linkage will thus happen automatically.
            
            stakeValue      The stake value for this PSExtension object. If none
                            is provided, one will be created.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0001 0000 0008  0002 0020 00B1 0003 |........... ....|
              10 | FFF6 0000 0000 0000  001E 0000 0000 0036 |...............6|
              20 | 0000 0036 002A 0000  0001 0003 0005 002D |...6.*.........-|
              30 | 0062 000C 0014 0002  BDF0 0020 3000 000C |.b......... 0...|
              40 | 0012 0001 8C04                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        extPool = kwArgs.get('extensionPool', None)
        
        if extPool is None:
            extPool = {}
            doLocal = True
        
        else:
            doLocal = False
        
        w.add("H", 1)
        w.add("H", self.original.kind[1])
        
        if id(self.original) not in extPool:
            extPool[id(self.original)] = (
              len(extPool),
              self.original,
              w.getNewStake())
        
        w.addUnresolvedOffset("L", stakeValue, extPool[id(self.original)][2])
        
        if doLocal:
            for i, obj, stake in sorted(extPool.values()):
                obj.buildBinary(w, stakeValue=stake, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.GPOS import single
    from fontio3.utilities import namer
    
    _testingValues = (
        PSExtension(original=single._testingValues[1]),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
