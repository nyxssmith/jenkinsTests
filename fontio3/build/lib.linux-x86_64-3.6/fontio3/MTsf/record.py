#
# record.py
#
# Copyright © 2007-2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single records in a MTsf object.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Record(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Single records in a MTsf object. These are simple objects with the
    following attributes:
    
        baselineShifted
        className
        originalClassIndex
        proportionCorrection
    
    >>> _testingValues[1].pprint()
    Use proportion correction: False
    Baseline is shifted: True
    Class name: 'fred'
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        proportionCorrection = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Use proportion correction"),
        
        baselineShifted = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Baseline is shifted"),
        
        className = dict(
            attr_label = "Class name",
            attr_pprintfunc = (lambda p,x,label,**k: p.simple(ascii(x)[1:], label=label)),
            attr_strusesrepr = True),
        
        originalClassIndex = dict(
            attr_ignoreforcomparisons = True))
    
    attrSorted = ('proportionCorrection', 'baselineShifted', 'className')
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Record object from the specified walker. There is
        one required keyword argument:
        
            classMap    A MTsc object.
        
        >>> obj = _testingValues[1]
        >>> obj == Record.frombytes(obj.binaryString(classRevMap=_classRevMap), classMap=_classMap)
        True
        """
        
        classMap = kwArgs['classMap']
        pc, bs, index = w.unpack("2BH6x")
        r = cls(bool(pc), bool(bs), (None if index == 0xFFFF else classMap[index]))
        r.originalClassIndex = index
        return r
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Record object to the specified
        LinkedWriter. There is one required keyword argument:
        
            classRevMap     A reverse-mapped MTsc object (name->index)
        
        >>> obj = _testingValues[1]
        >>> utilities.hexdump(obj.binaryString(classRevMap=_classRevMap))
               0 | 0001 0002 0000 0000  0000                |..........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        d = self.__dict__
        crm = kwArgs['classRevMap']
        index = crm.get(self.className, 0xFFFF)
        w.add("2BH6x", d['proportionCorrection'], d['baselineShifted'], index)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import MTsc, utilities
    
    _classMap = MTsc._testingValues[1]
    _classRevMap = {v: k for k, v in enumerate(_classMap)}
    
    _testingValues = (
        Record(),
        Record(False, True, b'fred'),
        Record(True, False, b'wxyz'),
        Record(False, False, b'abcdef'))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
