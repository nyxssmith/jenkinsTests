#
# distancecolor.py
#
# Copyright © 2007-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Classes defining objects which encapsulate TrueType state information.
"""

# System imports
import sys

# Other imports
from fontio3.triple import collection, triple
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Constants
#

T = triple.Triple
C = collection.Collection

zero26Dot6 = C([T(0, 64, 64)], 64)

# -----------------------------------------------------------------------------

#
# Classes
#

class DistanceColor(object):
    """
    Objects representing engine compensation distances for the three standard
    TrueType distance colors (white, gray and black).
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, setAllAttrs=True):
        """
        Initializes the distances as specified (defaulting to zero).
        """
        
        if setAllAttrs:
            self.__dict__ = dict.fromkeys(iter(self.keyData.keys()), zero26Dot6)
    
    #
    # Class methods
    #
    
    @classmethod
    def fromargs(cls, **kwArgs):
        """
        Class method that can be used as an alternative constructor when actual
        values (as opposed to defaults) are needed.
        
        >>> dc = DistanceColor.fromargs(white=C([T(32, 96, 64)], 64))
        >>> dc.white
        Singles: [0.5]
        >>> dc.black
        Singles: [0.0]
        """
        
        r = cls()
        r.__dict__.update(kwArgs)
        return r
    
    #
    # Special methods
    #
    
    def __copy__(self):
        r = DistanceColor(setAllAttrs=False)
        r.__dict__ = self.__dict__.copy()
        return r
    
    def __deepcopy__(self, memo=None):
        r = DistanceColor(setAllAttrs=False)
        r.__dict__ = self.__dict__.copy()
        return r
    
    def __eq__(self, other): return self is other or self.__dict__ == other.__dict__
    def __ne__(self, other): return self is not other and self.__dict__ != other.__dict__
    
    #
    # Public methods
    #
    
    def asDict(self):
        """
        Returns the object as a dict.
        
        >>> dc = DistanceColor.fromargs(gray=C([T(32, 96, 64)], 64))
        >>> d = dc.asDict()
        >>> for key in sorted(d.keys()): print(key, d[key])
        black Singles: [0.0]
        gray Singles: [0.5]
        white Singles: [0.0]
        """
        
        return self.__dict__.copy()
    
    def combine(self, other):
        """
        Combines other's values into self's, via the collection.cluster
        function.
        
        >>> dc1 = DistanceColor()
        >>> dc2 = DistanceColor.fromargs(gray=C([T(32, 96, 64)], 64))
        >>> dc1.combine(dc2)
        >>> dc1.pprint()
        Black distance: Singles: [0.0]
        Gray distance: Singles: [0.0, 0.5]
        White distance: Singles: [0.0]
        """
        
        dSelf = self.__dict__
        dOther = other.__dict__
        c = collection.cluster
        
        for k, n in dSelf.items():
            dSelf[k] = c(n, dOther[k], coerceToNumber=False)
    
    def merged(self, other):
        """
        Returns a new DistanceColor representing the combination of self and
        other.
        
        >>> dc1 = DistanceColor()
        >>> dc2 = DistanceColor.fromargs(gray=C([T(32, 96, 64)], 64))
        >>> dc3 = dc1.merged(dc2)
        >>> dc3.pprint()
        Black distance: Singles: [0.0]
        Gray distance: Singles: [0.0, 0.5]
        White distance: Singles: [0.0]
        """
        
        r = DistanceColor(setAllAttrs=False)
        dSelf = self.__dict__
        dOther = other.__dict__
        dRet = r.__dict__
        c = collection.cluster
        
        for k, valueSelf in dSelf.items():
            valueOther = dOther[k]
            
            if valueSelf != valueOther:
                dRet[k] = c(valueSelf, valueOther, coerceToNumber=False)
            else:
                dRet[k] = valueSelf
        
        return r
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object.
        
        >>> dc = DistanceColor.fromargs(gray=C([T(32, 96, 64)], 64))
        >>> dc.pprint(label="Colors")
        Colors:
          Black distance: Singles: [0.0]
          Gray distance: Singles: [0.5]
          White distance: Singles: [0.0]
        >>> dc.pprint(indent=3, keys=('gray', 'black'))
           Gray distance: Singles: [0.5]
           Black distance: Singles: [0.0]
        """
        
        p = pp.PP(**kwArgs)
        d = self.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.sortedKeys):
            p.simple(d[k], kd[k])
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Prints nothing if the two objects are equal. Otherwise prints what's
        changed.
        
        >>> dc = DistanceColor()
        >>> dc2 = DistanceColor.fromargs(gray=C([T(32, 96, 64)], 64))
        >>> dc2.pprint_changes(dc, label="Summary of changes")
        Summary of changes:
          Gray distance changed from Singles: [0.0] to Singles: [0.5]
        >>> dc2.pprint_changes(dc, label="The Data", keys=('white',))
        """
        
        p = pp.PP(**kwArgs)
        dSelf = self.__dict__
        dPrior = prior.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.sortedKeys):
            selfValue = dSelf[k]
            priorValue = dPrior[k]
            
            if selfValue != priorValue:
                p.diff(selfValue, priorValue, kd[k])

    #
    # Dispatch table
    #
    
    # keyData maps keys to labels
    
    keyData = {
      'black': "Black distance",
      'gray': "Gray distance",
      'white': "White distance"}
    
    sortedKeys = sorted(keyData.keys())

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test_main():
    """
    Run integrated tests for the whole module.
    
    >>> dc = DistanceColor.fromargs(gray=C([T(32, 96, 64)], 64))
    >>> dcCopy = dc.__copy__()
    >>> dc == dcCopy
    True
    >>> dc.black is dcCopy.black
    True
    >>> dc is dcCopy
    False
    """
    
    pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
    _test_main()

