#
# jstfscript.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for JstfScript tables.
"""

# System imports
import functools
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.JSTF import extenders, jstflangsys

# -----------------------------------------------------------------------------

#
# Classes
#

class JstfScript(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing JstfScript tables. These are dicts mapping langSys
    tags to JstfLangSys objects. In addition, the following attributes are
    present:
    
        extenders               An Extenders object, or None.
        defaultJstfLangSys      The default JstfLangSys object, or None.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda k:
          "LangSys '%s'" % (utilities.ensureUnicode(k),)))
    
    attrSpec = dict(
        extenders = dict(
            attr_followsprotocol = True,
            attr_label = "Extender glyphs",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        defaultJstfLangSys = dict(
            attr_followsprotocol = True,
            attr_label = "Default JstfLangSys",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)))
    
    attrSorted = ('extenders', 'defaultJstfLangSys')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the JstfScript object to the specified
        LinkedWriter.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self.extenders is None:
            w.add("H", 0)
        else:
            exStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, exStake)
        
        if self.defaultJstfLangSys is None:
            w.add("H", 0)
        else:
            dsStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, dsStake)
        
        w.add("H", len(self))
        dStakes = {}  # immut -> (obj, stake)
        ig0 = operator.itemgetter(0)
        
        for key, obj in sorted(self.items(), key=ig0):
            immut = obj.asImmutable(**kwArgs)
            
            if immut not in dStakes:
                dStakes[immut] = (obj, w.getNewStake())
            
            w.add("4s", key)
            w.addUnresolvedOffset("H", stakeValue, dStakes[immut][1])
        
        # Now add the deferred content
        if self.extenders is not None:
            self.extenders.buildBinary(w, stakeValue=exStake, **kwArgs)
        
        if self.defaultJstfLangSys is not None:
            self.defaultJstfLangSys.buildBinary(
              w,
              stakeValue = dsStake,
              **kwArgs)
        
        for immut, (obj, stake) in sorted(dStakes.items(), key=ig0):
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a JstfScript object from the specified walker.
        """
        
        offset = w.unpack("H")
        fw = extenders.Extenders.fromwalker
        ex = (fw(w.subWalker(offset), **kwArgs) if offset else None)
        
        offset = w.unpack("H")
        fw = jstflangsys.JstfLangSys.fromwalker
        dflt = (fw(w.subWalker(offset), **kwArgs) if offset else None)
        
        r = cls({}, extenders=ex, defaultJstfLangSys=dflt)
        
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
    _testingValues = (
        JstfScript(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
