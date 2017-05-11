#
# lookupsequence.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sequences of Lookup objects.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class LookupSequence(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing sequences of Lookups (order is important!) These are
    used in JstfPriority objects.
    
    Note that all Lookups represented in these objects must also be present
    already in the relevant GPOS or GSUB object. If not, then at buildBinary
    time a ValueError will be raised.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_islookup = True,
        item_pprintlabelfunc = (lambda i: "Lookup #%d" % (i + 1,)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the LookupSequence object to the specified
        LinkedWriter. There is one required keyword argument:
        
            lookupList      A list of Lookups for the relevant table (GPOS or
                            GSUB). Note that this list should refer to the
                            original content for this method, and not to a
                            subsequently edited GPOS or GSUB object, since the
                            index references will be to the unmodified lists.
        
        >>> obj = _testingValues[0]
        >>> d = {'lookupList': _lookupList}
        >>> utilities.hexdump(obj.binaryString(**d))
               0 | 0000                                     |..              |
        
        >>> obj = _testingValues[1]
        >>> utilities.hexdump(obj.binaryString(**d))
               0 | 0003 0002 0001 0000                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # LookupLists have their own explicit index methods, so this works OK
        ll = kwArgs['lookupList']
        v = [ll.index(obj) for obj in self]
        w.add("H", len(v))
        w.addGroup("H", v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a LookupSequence object from the specified walker.
        There is one required keyword argument:
        
            lookupList      A list of Lookups for the relevant table (GPOS or
                            GSUB). Note that this list should refer to the
                            original content for this method, and not to a
                            subsequently edited GPOS or GSUB object, since the
                            index references will be to the unmodified lists.
        
        >>> obj = _testingValues[1]
        >>> d = {'lookupList': _lookupList}
        >>> obj == LookupSequence.frombytes(obj.binaryString(**d), **d)
        True
        """
        
        ll = kwArgs['lookupList']
        return cls(ll[i] for i in w.group("H", w.unpack("H")))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.opentype import lookuplist
    
    _ltv = lookuplist._testingValues
    _lookupList = _ltv[1]
    
    _testingValues = (
        LookupSequence(),
        LookupSequence(reversed(_ltv[1])))
    
    del _ltv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
