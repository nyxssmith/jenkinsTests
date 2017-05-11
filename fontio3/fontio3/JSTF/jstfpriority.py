#
# jstfpriority.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for JstfPriority tables.
"""

# System imports
import functools
import operator

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.JSTF import lookupsequence
from fontio3.opentype import lookuplist

# -----------------------------------------------------------------------------

#
# Classes
#

class JstfPriority(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing JstfPriority tables. These are simple objects with the
    following attributes:
    
        shrinkEnableGSUB
        shrinkDisableGSUB
        shrinkEnableGPOS
        shrinkDisableGPOS
        shrinkJstfMax           A LookupList object.
        growEnableGSUB
        growDisableGSUB
        growEnableGPOS
        growDisableGPOS
        growJstfMax             A LookupList object.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        shrinkEnableGSUB = dict(
            attr_followsprotocol = True,
            attr_label = "GSUB Lookups enabled for shrink case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        shrinkDisableGSUB = dict(
            attr_followsprotocol = True,
            attr_label = "GSUB Lookups disabled for shrink case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        shrinkEnableGPOS = dict(
            attr_followsprotocol = True,
            attr_label = "GPOS Lookups enabled for shrink case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        shrinkDisableGPOS = dict(
            attr_followsprotocol = True,
            attr_label = "GPOS Lookups disabled for shrink case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        shrinkJstfMax = dict(
            attr_followsprotocol = True,
            attr_label = "JstfMax for shrink case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        growEnableGSUB = dict(
            attr_followsprotocol = True,
            attr_label = "GSUB Lookups enabled for grow case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        growDisableGSUB = dict(
            attr_followsprotocol = True,
            attr_label = "GSUB Lookups disabled for grow case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        growEnableGPOS = dict(
            attr_followsprotocol = True,
            attr_label = "GPOS Lookups enabled for grow case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        growDisableGPOS = dict(
            attr_followsprotocol = True,
            attr_label = "GPOS Lookups disabled for grow case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        growJstfMax = dict(
            attr_followsprotocol = True,
            attr_label = "JstfMax for grow case",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)))
    
    attrSorted = (
      'shrinkEnableGSUB',
      'shrinkDisableGSUB',
      'shrinkEnableGPOS',
      'shrinkDisableGPOS',
      'shrinkJstfMax',
      'growEnableGSUB',
      'growDisableGSUB',
      'growEnableGPOS',
      'growDisableGPOS',
      'growJstfMax')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the JstfPriority object to the specified
        LinkedWriter. There is one required keyword argument:
        
            editor      The Editor-class object for the font.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        d = self.__dict__
        e = kwArgs['editor']
        llGPOS = llGSUB = None  # make lookup lists as needed; it's expensive
        ftl = lookuplist.LookupList.fromtoplevel
        toBeWrittenLS = []  # (s, stake, whichLL), for LookupSequences
        toBeWrittenLL = []  # (s, stake), for LookupLists
        
        for i, s in enumerate(self.getSortedAttrNames()):
            obj = d[s]
            
            if obj is None:
                w.add("H", 0)
            
            else:
                m = i % 5
                
                if m == 4:
                    toBeWrittenLL.append((s, w.getNewStake()))
                    
                    w.addUnresolvedOffset(
                      "H",
                      stakeValue,
                      toBeWrittenLL[-1][1])
                
                else:
                    if m < 2:
                        if llGSUB is None:
                            llGSUB = ftl(e.GSUB.features)
                        
                        ll = llGSUB
                    
                    else:
                        if llGPOS is None:
                            llGPOS = ftl(e.GPOS.features)
                        
                        ll = llGPOS
                    
                    toBeWrittenLS.append((s, w.getNewStake(), ll))
                    
                    w.addUnresolvedOffset(
                      "H",
                      stakeValue,
                      toBeWrittenLS[-1][1])
        
        kwArgs.pop('lookupList', None)
        
        for s, stake, ll in toBeWrittenLS:
            obj = d[s]
            obj.buildBinary(w, stakeValue=stake, lookupList=ll, **kwArgs)
        
        for s, stake in toBeWrittenLL:
            obj = d[s]
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a JstfPriority object from the specified walker.
        There is one required keyword argument:
        
            editor      The Editor-class object for the font. This is used to
                        get the lookuplists from the GPOS and GSUB objects.
        """
        
        e = kwArgs['editor']
        llGPOS = (e.GPOS.getOriginalLookupList() if b'GPOS' in e else None)
        llGSUB = (e.GSUB.getOriginalLookupList() if b'GSUB' in e else None)
        fwSeq = lookupsequence.LookupSequence.fromwalker
        fwMax = lookuplist.LookupList.fromwalker
        gd = e.get(b'GDEF', None)
        v = [None] * 10
        
        for i, offset in enumerate(w.group("H", 10)):
            m = i % 5
            
            if offset:
                ll = (llGSUB if 0 <= m < 2 else llGPOS)
                wSub = w.subWalker(offset)
                
                if m == 4:
                    kwArgs.pop('forGPOS', None)
                    kwArgs.pop('GDEF', None)
                    v[i] = fwMax(wSub, forGPOS=True, GDEF=gd, **kwArgs)
                
                else:
                    kwArgs.pop('lookupList', None)
                    v[i] = fwSeq(wSub, lookupList=ll, **kwArgs)
        
        return cls(*v)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        JstfPriority())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
