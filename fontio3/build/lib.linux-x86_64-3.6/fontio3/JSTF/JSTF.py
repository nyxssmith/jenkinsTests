#
# JSTF.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType 'JSTF' tables.
"""

# System imports
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.JSTF import jstfscript

# -----------------------------------------------------------------------------

#
# Classes
#

class JSTF(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'JSTF' tables. These are dicts whose keys are
    script tags and whose values are JstfScript objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda k:
          "Script '%s'" % (utilities.ensureUnicode(k),)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the JSTF object to the specified LinkedWriter.
        There is one required keyword argument:
        
            editor      The Editor-class object. This is used to obtain the
                        LookupLists for the GPOS and GSUB references made in
                        this JSTF table.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)  # version
        w.add("H", len(self))
        dStakes = {}  # immut -> (obj, stake)
        ig0 = operator.itemgetter(0)
        
        for key, obj in sorted(self.items(), key=ig0):
            immut = obj.asImmutable(**kwArgs)
            
            if immut not in dStakes:
                dStakes[immut] = (obj, w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, dStakes[immut][1])
        
        for immut, (obj, stake) in sorted(dStakes.items(), key=ig0):
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a JSTF object from the specified walker. There is
        one required keyword argument:
        
            editor      The Editor-class object. This is used to obtain the
                        LookupLists for the GPOS and GSUB references made in
                        this JSTF table.
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'JSTF' version: 0x%08X" % (version,))
        
        r = cls()
        fw = jstfscript.JstfScript.fromwalker
        
        for tag, offset in w.group("4sH", w.unpack("H")):
            r[tag] = fw(w.subWalker(offset), **kwArgs)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        JSTF(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
