#
# binary.py
#
# Copyright © 2012, 2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for raw binary strings with full protocol methods. These can be useful
for Editors when using unknown tables.
"""

# Other imports
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class Binary(bytes):
    """
    Objects representing raw binary strings.
    """
    
    #
    # Class methods
    #
    
    @classmethod
    def frombytes(cls, s, *a, **k): return cls(s)
    
    @classmethod
    def fromvalidatedbytes(cls, s, *a, **k): return cls(s)
    
    @classmethod
    def fromvalidatedwalker(cls, w, *a, **k): return cls(w.rest())
    
    @classmethod
    def fromwalker(cls, w, *a, **k): return cls(w.rest())
    
    @classmethod
    def getSortedAttrNames(cls, *a, **k): return ()
    
    @classmethod
    def groupfrombytes(cls, s, *a, **k): return [cls(s)]
    
    @classmethod
    def groupfromvalidatedwalker(cls, w, *a, **k): return [cls(w.rest())]
    
    @classmethod
    def groupfromwalker(cls, w, *a, **k): return [cls(w.rest())]
    
    #
    # Special methods
    #
    
    def __copy__(self, *a, **k): return self
    def __deepcopy__(self, *a, **k): return self
    
    #
    # Public methods
    #
    
    def asImmutable(self, *a, **k): return self
    def binaryString(self, *a, **k): return self
    
    def buildBinary(self, w, *a, **k):
        """
        Adds the binary data directly to the specified writer.
        
        >>> w = writer.LinkedWriter()
        >>> obj = Binary(b'This is a test.')
        >>> obj.buildBinary(w)
        >>> utilities.hexdump(w.binaryString())
               0 | 5468 6973 2069 7320  6120 7465 7374 2E   |This is a test. |
        """
        
        if 'stakeValue' in k:
            stakeValue = k.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.addString(self)
    
    def checkInput(self, *a, **k): return True
    def coalesced(self, *a, **k): return self
    def compacted(self, *a, **k): return self
    def cvtsRenumbered(self, *a, **k): return self
    def fdefsRenumbered(self, *a, **k): return self
    def gatheredInputGlyphs(self, *a, **k): return set()
    def gatheredLivingDeltas(self, *a, **k): return set()
    def gatheredMaxContext(self, *a, **k): return 0
    def gatheredOutputGlyphs(self, *a, **k): return set()
    def gatheredRefs(self, *a, **k): return {}
    def getNamer(self, *a, **k): return None
    def glyphsRenumbered(self, *a, **k): return self
    def hasCycles(self, *a, **k): return False
    def isValid(self, *a, **k): return True
    def merged(self, *a, **k): return self
    def namesRenumbered(self, *a, **k): return self
    def pcsRenumbered(self, *a, **k): return self
    def pointsRenumbered(self, *a, **k): return self
    
    def pprint(self, *a, **k):
        """
        Pretty-print the object. This does a hex dump.
        
        >>> Binary(b'In a hole in the ground there lived a hobbit.').pprint()
               0 | 496E 2061 2068 6F6C  6520 696E 2074 6865 |In a hole in the|
              10 | 2067 726F 756E 6420  7468 6572 6520 6C69 | ground there li|
              20 | 7665 6420 6120 686F  6262 6974 2E        |ved a hobbit.   |
        """
        
        if 'p' in k:
            p = k.pop('p')
        else:
            p = pp.PP(**k)
        
        k.pop('label', None)
        p.hexDump(self)
    
    def pprint_changes(self, *a, **k): pass
    def recalculated(self, *a, **k): return self
    def scaled(self, *a, **k): return self
    def setNamer(self, *a, **k): pass
    def storageRenumbered(self, *a, **k): return self
    def transformed(self, *a, **k): return self

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import writer

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
