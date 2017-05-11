#
# glyphinfo.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
All the data for a single glyph in a 'Zapf' table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.Zapf import featureinfo, groupinfotuple, kindnames, unicodeset

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphInfo(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects containing all 'Zapf' table information for a single glyph. These
    are simple objects with the following attributes:
    
        groups          A GroupInfoTuple object, or None.
        features        A FeatureInfo object, or None.
        unicodes        A UnicodeSet object, or None.
        kindNames       A KindNames object, or None.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        groups = dict(
            attr_followsprotocol = True,
            attr_label = "Group information",
            attr_showonlyiftrue = True),
        
        features = dict(
            attr_followsprotocol = True,
            attr_label = "Feature information",
            attr_showonlyiftrue = True),
        
        unicodes = dict(
            attr_followsprotocol = True,
            attr_label = "Unicodes for the glyph",
            attr_showonlyiftrue = True),
        
        kindNames = dict(
            attr_followsprotocol = True,
            attr_label = "Kind names",
            attr_showonlyiftrue = True))
    
    attrSorted = ('groups', 'features', 'unicodes', 'kindNames')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GlyphInfo to the specified LinkedWriter.
        The following keyword arguments are used:
        
            extraInfoStake      The stake representing the start of the
                                extraInfo space. This is required.
            
            gigPool             A dictionary mapping all GroupInfoTuple objects
                                to their associated stakes. This is required.
            
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
        
        extraInfoStake = kwArgs['extraInfoStake']
        giPool = kwArgs['giPool']  # just GroupInfos
        gigPool = kwArgs['gigPool']  # just GroupInfos
        groupsObj = self.groups
        
        if groupsObj is None or len(groupsObj) == 0:
            # there is no group info for this glyph
            w.add("L", 0xFFFFFFFF)
        
        elif groupsObj.altForms is None and len(groupsObj) == 1:
            # it's a GroupInfo case
            w.addUnresolvedOffset("L", extraInfoStake, giPool[groupsObj[0]])
        
        else:
            # it's a GroupInfoGroup case
            w.addUnresolvedOffset("L", extraInfoStake, gigPool[groupsObj])
        
        featPool = kwArgs['featPool']
        featObj = self.features
        
        if featObj is None:
            w.add("L", 0xFFFFFFFF)
        
        else:
            immut = featObj.asImmutable()
            w.addUnresolvedOffset("L", extraInfoStake, featPool[immut][1])
        
        if self.unicodes is not None:
            self.unicodes.buildBinary(w)
        else:
            w.add("H", 0)
        
        if self.kindNames is not None:
            self.kindNames.buildBinary(w)
        else:
            w.add("H", 0)
        
        w.alignToByteMultiple(4)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphInfo object from the specified walker,
        doing source validation. There are three required keyword arguments:
        
            featPool        A dict mapping feature offsets to FeatureInfo
                            objects. The dict must have an entry mapping
                            0xFFFFFFFF to None.
            
            groupTuplePool  A dict mapping group offsets to GroupInfoTuple
                            objects. The dict must have an entry mapping
                            0xFFFFFFFF to None.
            
            logger          A logger to which messages will be posted.
            
            wExtra          A walker whose base is the start of the extraInfo
                            in the 'Zapf' binary data. Offsets to features and
                            to groups are from the start of this walker.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("glyphinfo")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        groupOffset, featOffset = w.unpack("2L")
        pool = kwArgs['groupTuplePool']
        
        if groupOffset not in pool:
            obj = groupinfotuple.GroupInfoTuple.fromvalidatedwalker(
              kwArgs['wExtra'].subWalker(groupOffset),
              logger = logger,
              **kwArgs)
            
            if obj is None:
                return None
            
            pool[groupOffset] = obj
        
        gr = pool[groupOffset]
        pool = kwArgs['featPool']
        
        if featOffset not in pool:
            obj = featureinfo.FeatureInfo.fromvalidatedwalker(
              kwArgs['wExtra'].subWalker(featOffset),
              logger = logger)
            
            if obj is None:
                return None
            
            pool[featOffset] = obj
        
        fe = pool[featOffset]
        us = unicodeset.UnicodeSet.fromvalidatedwalker(w, logger=logger)
        
        if us is None:
            return None
        
        kn = kindnames.KindNames.fromvalidatedwalker(w, logger=logger)
        
        if kn is None:
            return None
        
        return cls(gr, fe, us, kn)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphInfo object from the specified walker.
        There are three required keyword arguments:
        
            featPool        A dict mapping feature offsets to FeatureInfo
                            objects. The dict must have an entry mapping
                            0xFFFFFFFF to None.
            
            groupTuplePool  A dict mapping group offsets to GroupInfoTuple
                            objects. The dict must have an entry mapping
                            0xFFFFFFFF to None.
            
            wExtra          A walker whose base is the start of the extraInfo
                            in the 'Zapf' binary data. Offsets to features and
                            to groups are from the start of this walker.
        """
        
        groupOffset, featOffset = w.unpack("2L")
        pool = kwArgs['groupTuplePool']
        
        if groupOffset not in pool:
            f = groupinfotuple.GroupInfoTuple.fromwalker
            pool[groupOffset] = f(kwArgs['wExtra'].subWalker(groupOffset), **kwArgs)
        
        gr = pool[groupOffset]
        pool = kwArgs['featPool']
        
        if featOffset not in pool:
            f = featureinfo.FeatureInfo.fromwalker
            pool[featOffset] = f(kwArgs['wExtra'].subWalker(featOffset))
        
        fe = pool[featOffset]
        us = unicodeset.UnicodeSet.fromwalker(w)
        kn = kindnames.KindNames.fromwalker(w)
        return cls(gr, fe, us, kn)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
