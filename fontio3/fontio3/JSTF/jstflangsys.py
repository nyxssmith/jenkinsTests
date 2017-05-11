#
# jstflangsys.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for JstfLangSys tables.
"""

# System imports
import operator

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.JSTF import jstfpriority

# -----------------------------------------------------------------------------

#
# Private functions
#

def _lblFunc(i):
    if i == 0:
        return "Highest priority"
    elif i == 1:
        return "Second-highest priority"
    elif i == 2:
        return "Third-highest priority"
    else:
        return "Priority %d" % (i + 1,)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class JstfLangSys(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing JstfLangSys tables. These are lists of JstfPriority
    objects.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = _lblFunc)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the JstfLangSys object to the specified
        LinkedWriter.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        dStakes = {}  # immut -> (obj, stake)
        
        for obj in self:
            immut = obj.asImmutable(**kwArgs)
            
            if immut not in dStakes:
                dStakes[immut] = (obj, w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, dStakes[immut][1])
        
        it = sorted(dStakes.items(), key=operator.itemgetter(0))
        
        for immut, (obj, stake) in it:
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a JstfLangSys object from the specified walker.
        """
        
        fw = jstfpriority.JstfPriority.fromwalker
        
        it = (
          fw(w.subWalker(offset), **kwArgs)
          for offset in w.group("H", w.unpack("H")))
        
        return cls(it)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        JstfLangSys(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
