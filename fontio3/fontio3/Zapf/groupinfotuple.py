#
# groupinfotuple.py
#
# Copyright © 2010-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for groupings of GroupInfo objects. These are the objects contained in
the GlyphInfo record's groups attribute.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.Zapf import groupinfo

# -----------------------------------------------------------------------------

#
# Classes
#

class GroupInfoTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    GroupInfoTuple objects are the objects referred to in the GlyphInfo
    object's groups attribute. They are tuples of GroupInfo objects. There is
    one attribute:
    
        altForms    A GroupInfo representing alternate forms. This will only
                    be non-None for GroupInfoGroup data where the first entry
                    is not 0xFFFFFFFF (see the 'Zapf' table documentation).
    
    >>> nm = namer.testingNamer()
    >>> nm.annotate = True
    >>> fakeNameTable = {
    ...   (1, 0, 0, 289): "Ampersands",
    ...   (1, 0, 0, 290): "Classic",
    ...   (1, 0, 0, 291): "Modern"}
    >>> d = {'namer': nm, 'nameTableObj': fakeNameTable}
    >>> _testingValues[1].pprint(**d)
    GroupInfo #1:
      NamedGroup #1:
        xyz3 (glyph 2)
        xyz20 (glyph 19)
        afii60002 (glyph 97)
    GroupInfo #2:
      NamedGroup #1:
        Group name: 289 ('Ampersands')
      NamedGroup #2:
        xyz3 (glyph 2)
        xyz20 (glyph 19)
        afii60002 (glyph 97)
        Group name: 290 ('Classic')
        Group is a subdivision: True
      NamedGroup #3:
        xyz42 (glyph 41)
        xyz43 (glyph 42)
        Group name: 291 ('Modern')
        Group is a subdivision: True
    
    >>> _testingValues[2].pprint(**d)
    GroupInfo #1:
      NamedGroup #1:
        xyz3 (glyph 2)
        xyz20 (glyph 19)
        afii60002 (glyph 97)
    Alternate forms group:
      NamedGroup #1:
        Group name: 289 ('Ampersands')
      NamedGroup #2:
        xyz3 (glyph 2)
        xyz20 (glyph 19)
        afii60002 (glyph 97)
        Group name: 290 ('Classic')
        Group is a subdivision: True
      NamedGroup #3:
        xyz42 (glyph 41)
        xyz43 (glyph 42)
        Group name: 291 ('Modern')
        Group is a subdivision: True
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "GroupInfo #%d" % (i + 1,)))
    
    attrSpec = dict(
        altForms = dict(
            attr_followsprotocol = True,
            attr_label = "Alternate forms group",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GroupInfoTuple object to the specified
        LinkedWriter. Note that this method is only called when the resulting
        data will be a GroupInfoGroup, and not just a simple GroupInfo.
        
        The following keyword arguments are used:
        
            extraInfoStake      The stake representing the start of the
                                extraInfo space. This is required.
            
            giPool              A dictionary mapping all GroupInfo objects to
                                their associated stakes. This is required.
            
            stakeValue          The stake representing the start of this
                                GlyphInfo record. This is optional (but usual).
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # If there are no altForms and only one entry, this is the simple
        # GroupInfo case, so write that and we're done.
        
        if self.altForms is None and len(self) == 1:
            self[0].buildBinary(w, **kwArgs)
            return
        
        # If we get here, it's a GroupInfoGroup case.
        
        extraInfoStake = kwArgs['extraInfoStake']
        giPool = kwArgs['giPool']
        w.add("Hxx", len(self) + 1)
        
        if self.altForms is None:
            w.add("L", 0xFFFFFFFF)
        else:
            w.addUnresolvedOffset("L", extraInfoStake, giPool[self.altForms])
        
        for obj in self:
            w.addUnresolvedOffset("L", extraInfoStake, giPool[obj])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GroupInfoTuple object from the specified
        walker, doing source validation. The following keyword
        arguments are supported:
        
            groupPool       A dict mapping offsets to GroupInfo objects to the
                            actual objects. This is required.
            
            logger          A logger to which messages will be posted. If not
                            specified, the default logger will be used.
            
            wExtra          A walker whose base is the start of the extraInfo
                            space. This is required.
        """
        
        n = w.unpack("H", advance=False)
        v = []
        af = None
        
        if n & 0x4000:
            # it's a GroupInfoGroup
            n = n & 0x3FFF
            w.skip(4)  # also skips the padding
            offsets = w.group("L", n)
            pool = kwArgs['groupPool']
            
            if offsets[0] != 0xFFFFFFFF:
                offset = offsets[0]
                
                if offset not in pool:
                    wSub = kwArgs['wExtra'].subWalker(offset)
                    pool[offset] = groupinfo.GroupInfo.fromwalker(wSub)
                
                af = pool[offset]
            
            for offset in offsets[1:]:
                if offset not in pool:
                    wSub = kwArgs['wExtra'].subWalker(offset)
                    pool[offset] = groupinfo.GroupInfo.fromwalker(wSub)
                
                v.append(pool[offset])
        
        else:
            # it's a GroupInfo
            v.append(groupinfo.GroupInfo.fromwalker(w))
        
        return cls(v, altForms=af)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GroupInfoTuple object from the specified
        walker. The following required keyword arguments are used:
        
            groupPool       A dict mapping offsets to GroupInfo objects to the
                            actual objects.
            
            wExtra          A walker whose base is the start of the extraInfo
                            space.
        """
        
        n = w.unpack("H", advance=False)
        v = []
        af = None
        
        if n & 0x4000:
            # it's a GroupInfoGroup
            n = n & 0x3FFF
            w.skip(4)  # also skips the padding
            offsets = w.group("L", n)
            
            if offsets[0] != 0xFFFFFFFF:
                offset = offsets[0]
                pool = kwArgs['groupPool']
                
                if offset not in pool:
                    wSub = kwArgs['wExtra'].subWalker(offset)
                    pool[offset] = groupinfo.GroupInfo.fromwalker(wSub)
                
                af = pool[offset]
            
            for offset in offsets[1:]:
                if offset not in pool:
                    wSub = kwArgs['wExtra'].subWalker(offset)
                    pool[offset] = groupinfo.GroupInfo.fromwalker(wSub)
                
                v.append(pool[offset])
        
        else:
            # it's a GroupInfo
            v.append(groupinfo.GroupInfo.fromwalker(w))
        
        return cls(v, altForms=af)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _giv = groupinfo._testingValues
    
    _testingValues = (
        GroupInfoTuple(),
        GroupInfoTuple([_giv[1], _giv[2]]),
        GroupInfoTuple([_giv[1]], altForms=_giv[2]))
    
    del _giv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
