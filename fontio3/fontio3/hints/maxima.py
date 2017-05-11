#
# maxima.py
#
# Copyright © 2007-2008, 2010-2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for calculating maximum stack depth, storage, CVT and other TrueType-
related 'maxp' values.
"""

# Other imports
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Private functions
#

def _dataString(n):
    return (None if n == -1 else n)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Maxima(object):
    """
    Objects containing maxima for various TrueType hinting-related values.
    These are objects with the following attributes:
        
        cvt         Largest CVT index referred to.
        
        function    Largest FDEF index referred to.
        
        hintSize    Byte size of the binary hints.
        
        point       Largest point index in the glyph zone (zone 1) the hints
                    ever refer to.
        
        pointMoved  Largest point index in the glyph zone that is actually
                    moved by a hint (as opposed to simply being referred to;
                    this is used by the FindHintedPhantoms tool).
        
        stack       Deepest stack level (in 32-bit units).
        
        storage     Largest storage index referred to.
    
        tzPoint     Largest point index in the twilight zone (zone 0) the hints
                    ever refer to.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, setAllAttrs=True):
        """
        Initializes the object to all -1s.
        
        >>> m = Maxima()
        >>> m.asList()
        [-1, -1, -1, -1, -1, -1, -1, -1]
        """
        
        if setAllAttrs:
            self.__dict__ = dict.fromkeys(iter(self.keyData.keys()), -1)
    
    #
    # Class methods
    #
    
    @classmethod
    def fromargs(cls, **kwArgs):
        """
        Class method that can be used as an alternative constructor when actual
        values (as opposed to default values of -1) are needed.
        
        >>> m = Maxima.fromargs(cvt=10)
        >>> m.cvt, m.function
        (10, -1)
        """
        
        r = cls()
        r.__dict__.update(kwArgs)
        return r
    
    #
    # Special methods
    #
    
    def __copy__(self):
        r = Maxima(setAllAttrs=False)
        r.__dict__ = self.__dict__.copy()
        return r
    
    def __deepcopy__(self, memo=None):
        r = Maxima(setAllAttrs=False)
        r.__dict__ = self.__dict__.copy()
        return r
    
    def __eq__(self, other): return self is other or self.__dict__ == other.__dict__
    def __ne__(self, other): return self is not other and self.__dict__ != other.__dict__
    
    #
    # Public methods
    #
    
    def asList(self):
        """
        Returns a list with all the values ordered by keyName.
        
        >>> Maxima().asList()
        [-1, -1, -1, -1, -1, -1, -1, -1]
        """
        
        d = self.__dict__
        return [d[k] for k in self.sortedKeys]
    
    def combine(self, other):
        """
        Modifies self by taking the maxima of both objects.
        
        >>> m1 = Maxima.fromargs(hintSize=100, storage=20, stack=25, cvt=10)
        >>> m1.asList()
        [10, -1, 100, -1, -1, 25, 20, -1]
        >>> m2 = Maxima.fromargs(tzPoint=8, hintSize=80, stack=40)
        >>> m2.asList()
        [-1, -1, 80, -1, -1, 40, -1, 8]
        >>> m1.combine(m2)
        >>> m1.asList()
        [10, -1, 100, -1, -1, 40, 20, 8]
        """
        
        dSelf = self.__dict__
        dOther = other.__dict__
        
        for k in self.keyData:
            dSelf[k] = max(dSelf[k], dOther[k])
    
    def merged(self, other):
        """
        Returns a new Maxima object representing the combination of the two
        input Maxima objects.
        
        >>> m1 = Maxima.fromargs(cvt=10, function=45, stack=200)
        >>> m2 = Maxima.fromargs(cvt=14, function=30, point=18)
        >>> m3 = m1.merged(m2)
        >>> m3.asList()
        [14, 45, -1, 18, -1, 200, -1, -1]
        >>> m1 is m3, m2 is m3
        (False, False)
        """
        
        m = self.__copy__()
        m.combine(other)
        return m
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object to the specified stream. Two keyword arguments
        are used:
        
            indent      How many spaces to indent on left (default 0)
            keys        Which keys to report (default all)
            stream      Stream to receive output (default sys.stdout)
        
        >>> m1 = Maxima.fromargs(cvt=10, function=45, stack=200)
        >>> m2 = Maxima.fromargs(cvt=14, function=30, point=18)
        >>> m3 = m1.merged(m2)
        >>> m3.pprint()
        Highest CVT index referred to: 14
        Highest function number referred to: 45
        Byte size of the binary hints: (no data)
        Highest point index in the glyph zone: 18
        Highest moved point index in the glyph zone: (no data)
        Deepest stack attained: 200
        Highest storage index referred to: (no data)
        Highest point index in the twilight zone: (no data)
        >>> m3.pprint(indent=3, keys=('storage', 'function'))
           Highest storage index referred to: (no data)
           Highest function number referred to: 45
        """
        
        p = pp.PP(**kwArgs)
        d = self.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.sortedKeys):
            p.simple(_dataString(d[k]), kd[k])
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Prints nothing if the two objects are equal. Otherwise prints a label
        (if specified) and what changed. Keyword arguments used are:
        
            indent          How many spaces to indent on left (default 0)
            indentDelta     Extra spaces per new indent (default 2)
            keys            Which keys to report (default all)
            label           Header label (no default)
            stream          Stream to receive output (default sys.stdout)
        
        >>> m = Maxima.fromargs(cvt=10, function=82, stack=200)
        >>> m.pprint_changes(Maxima())
        Highest CVT index referred to changed from (no data) to 10
        Highest function number referred to changed from (no data) to 82
        Deepest stack attained changed from (no data) to 200
        >>> m.pprint_changes(Maxima(), keys=('stack', 'cvt'))
        Deepest stack attained changed from (no data) to 200
        Highest CVT index referred to changed from (no data) to 10
        """
        
        p = pp.PP(**kwArgs)
        dSelf = self.__dict__
        dPrior = prior.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.sortedKeys):
            selfValue = dSelf[k]
            priorValue = dPrior[k]
            
            if selfValue != priorValue:
                p.diff(_dataString(selfValue), _dataString(priorValue), kd[k])
    
    #
    # Dispatch table
    #
    
    # keyData maps keys to labels
    
    keyData = {
      'cvt': "Highest CVT index referred to",
      'function': "Highest function number referred to",
      'hintSize': "Byte size of the binary hints",
      'point': "Highest point index in the glyph zone",
      'pointMoved': "Highest moved point index in the glyph zone",
      'stack': "Deepest stack attained",
      'storage': "Highest storage index referred to",
      'tzPoint': "Highest point index in the twilight zone"}
    
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
    
    >>> m1 = Maxima()
    >>> m1.hintSize = 100; m1.storage = 20; m1.stack = 25; m1.cvt = 10
    >>> m2 = m1.__copy__()
    >>> m1.asList() == m2.asList()
    True
    >>> m1 is m2
    False
    """
    
    pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
        _test_main()
