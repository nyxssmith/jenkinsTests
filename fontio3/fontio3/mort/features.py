#
# features.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mapping feature/setting values to associated masks in a 'mort'
table.
"""

# System imports
import logging
import operator

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.mort import featureentry, featuresetting

# -----------------------------------------------------------------------------

#
# Constants
#

LAST_ENTRY = featureentry.FeatureEntry(
  featureSetting = featuresetting.FeatureSetting((0, 1)),
  enableMask = 0,
  disableMask = 0)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _makeClusters(combined):
    """
    Given the combined list produced by makeCombined(), this method produces a
    set of clusters. The members of this returned set are themselves
    frozensets, which collect together indices into the Features object of all
    features which affect the same connected group of subtables.

    Note that we cannot simply look at the feature type to determine this,
    since some effects may rely on other effects before they're performed. For
    instance, in the doctest below, note that feature type 1 is part of several
    different clusters (diphthong ligatures, common ligatures, and rare
    ligatures), which are independent of one another.
    
    >>> obj = _testingValues[2]
    >>> combined = obj.makeCombined()
    >>> clusters = _makeClusters(combined)
    >>> for cluster in sorted(clusters):
    ...     print("For cluster", cluster)
    ...     for featIndex in sorted(cluster):
    ...         print("  ", obj[featIndex].featureSetting)
    For cluster frozenset({3, 4})
       Common ligatures on (1, 2)
       Common ligatures off (1, 3)
    For cluster frozenset({5, 6})
       Rare ligatures on (1, 4)
       Rare ligatures off (1, 5)
    For cluster frozenset({0, 1, 2})
       Cursive connection off (2, 0)
       Partial cursive connection (2, 1)
       Full cursive connection (2, 2)
    """
    
    stillToDo = set(range(len(combined)))
    groups = set()
    
    while stillToDo:
        n = stillToDo.pop()
        thisGroup = {n}
        
        for i, v in enumerate(combined):
            if i == n:
                continue
            
            if any(map(operator.and_, combined[n], combined[i])):
                thisGroup.add(i)
        
        groups.add(frozenset(thisGroup))
        stillToDo -= thisGroup
    
    return groups

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Features(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing the subFeatureFlags in a 'mort' table (all chains
    collected together). These are lists of FeatureEntry objects; note that
    order is important!
    
    The last entry should be the (0, 1) entry, but if it is not present it will
    be added automatically at buildBinary() time.
    
    >>> _testingValues[1].pprint()
    Feature 1:
      Feature/setting: Superiors (10, 1)
      Enable mask: 00000001
      Disable mask: FFFFFFFF
    Feature 2:
      Feature/setting: No alternates (17, 0)
      Enable mask: 00000002
      Disable mask: FFFFFFFE
    Feature 3:
      Feature/setting: All features disabled (0, 1)
      Enable mask: 00000000
      Disable mask: 00000000
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda n: "Feature %d" % (n+1,)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Features object to the specified writer.
        Note the count is not written here.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000A 0001 0000 0001  FFFF FFFF 0011 0000 |................|
              10 | 0000 0002 FFFF FFFE  0000 0001 0000 0000 |................|
              20 | 0000 0000                                |....            |
        """
        
        v = list(self)
        
        if v:
            zeroOne = [
              i
              for i, obj in enumerate(v)
              if obj.featureSetting == (0, 1)]
            
            if zeroOne != [len(v) - 1]:
                if zeroOne:
                    for i in sorted(zeroOne, reverse=True):
                        del v[i]
                
                v.append(LAST_ENTRY)
            
            for obj in v:
                obj.buildBinary(w, **kwArgs)
    
    def compacted(self, **kwArgs):
        """
        Returns a new Features object with any FeatureEntry objects removed
        if their masks no longer refer to any living subtables. Remember that
        the kwArgs will include one called parentObj which contains a compacted
        list of subtables.
        """
        
        compactedSubtables = kwArgs.get('parentObj', None)
        
        if compactedSubtables is None:
            return self.__deepcopy__()
        
        combined = self.makeCombined()
        vNew = []
        
        for i, maskList in enumerate(combined):
            mask = int(''.join(str(n) for n in maskList), 2)
            
            for sub in compactedSubtables:
                if mask & sub.maskValue:
                    vNew.append(self[i])
                    break
        
        vNew.append(LAST_ENTRY)
        return type(self)(vNew)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Features object from the specified walker,
        doing source validation. The following keyword arguments are used:
        
            count       The number of FeatureEntry records to be read. This is
                        required.
            
            logger      A logger to which messages will be posted.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("features_fvw")
        >>> fvb = Features.fromvalidatedbytes
        >>> obj = fvb(s, count=3, logger=logger)
        features_fvw.features - DEBUG - Walker has 36 remaining bytes.
        features_fvw.features.[0].featureentry - DEBUG - Walker has 36 remaining bytes.
        features_fvw.features.[0].featureentry.featuresetting - DEBUG - Walker has 36 remaining bytes.
        features_fvw.features.[1].featureentry - DEBUG - Walker has 24 remaining bytes.
        features_fvw.features.[1].featureentry.featuresetting - DEBUG - Walker has 24 remaining bytes.
        features_fvw.features.[2].featureentry - DEBUG - Walker has 12 remaining bytes.
        features_fvw.features.[2].featureentry.featuresetting - DEBUG - Walker has 12 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:3], count=3, logger=logger)
        features_fvw.features - DEBUG - Walker has 3 remaining bytes.
        features_fvw.features.[0].featureentry - DEBUG - Walker has 3 remaining bytes.
        features_fvw.features.[0].featureentry.featuresetting - DEBUG - Walker has 3 remaining bytes.
        features_fvw.features.[0].featureentry.featuresetting - ERROR - Insufficient bytes.
        """
        
        count = kwArgs['count']
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("features")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        fvw = featureentry.FeatureEntry.fromvalidatedwalker
        v = [None] * count
        
        for i in range(count):
            obj = fvw(
              w,
              logger = logger.getChild("[%d]" % (i,)),
              **kwArgs)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        r = cls(v)
        
        if r:
            zeroOne = [
              i
              for i, obj in enumerate(r)
              if obj.featureSetting == (0, 1)]
            
            if zeroOne != [len(r) - 1]:
                if zeroOne:
                    for i in reversed(zeroOne):
                        del r[i]
                
                r.append(LAST_ENTRY)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Features object from the specified walker.
        There is one keyword argument:
        
            count       The number of FeatureEntry records to be read. This is
                        required.
        
        >>> obj = _testingValues[1]
        >>> obj == Features.frombytes(obj.binaryString(), count=3)
        True
        """
        
        count = kwArgs['count']
        fw = featureentry.FeatureEntry.fromwalker
        r = cls(fw(w, **kwArgs) for i in range(count))
        
        if r:
            zeroOne = [
              i
              for i, obj in enumerate(r)
              if obj.featureSetting == (0, 1)]
            
            if zeroOne != [len(r) - 1]:
                if zeroOne:
                    for i in reversed(zeroOne):
                        del r[i]
                
                r.append(LAST_ENTRY)
        
        return r
    
    def makeCombined(self):
        """
        Returns a list. This list is indexed by the same index as that used in
        self (except the final (0, 1) entry, if present, is not included). The
        elements of the list are themselves lists of zeroes and ones, matching
        the maskValue associated with the features and the subtables. The
        enableMask and the inverse of the disableMask are used (except if the
        disable mask is zero, in which case it does not contribute). These
        values are ORed to get the final list.
        
        Note that the lists will have a uniform length, matching the longest
        mask value specified (padded out appropriately to a 32-bit multiple).
        
        >>> obj = _testingValues[2]
        >>> combined = obj.makeCombined()
        >>> hex(obj[2].enableMask)
        '0x40'
        
        >>> obj[2].disableMask == 0xffffff7f
        True
        
        >>> for v in combined: print(''.join(str(n) for n in v))
        0000000000000000000000000000000000000000000000000000000011000000
        0000000000000000000000000000000000000000000000000000000011000000
        0000000000000000000000000000000000000000000000000000000011000000
        0000000000010000000000000000000000000000000000000000000000000000
        0000000000010000000000000000000000000000000000000000000000000000
        0000000000100000000000000000000000000000000000000000000000000000
        0000000000100000000000000000000000000000000000000000000000000000
        """
        
        # We don't want the (0, 1) entry, if present
        v = [obj for obj in self if obj.featureSetting != (0, 1)]
        
        # First determine the 32-bit granularity
        maxEnableLen = max(f.enableMask.bit_length() for f in v)
        maxDisableLen = max(f.disableMask.bit_length() for f in v)
        grain32 = ((max(maxEnableLen, maxDisableLen) + 31) // 32) * 32
        nybble32 = grain32 // 4
        
        # Make the combined list of lists
        combined = [None] * len(v)
        
        for i, f in enumerate(v):
            n = f.enableMask
            vEnable = [int(s) for s in bin(n)[2:].rjust(grain32, '0')]
            
            n = f.disableMask
            
            vDisable = [
              (1 - int(s) if n else 0)
              for s in bin(int(hex(n)[2:].rjust(nybble32, 'f'), 16))[2:]]
            
            combined[i] = list(map(operator.or_, vEnable, vDisable))
        
        return combined
    
    def masksRenumbered(self, oldToNew, **kwArgs):
        """
        Returns a subset of self with mask values renumbered. The oldToNew dict
        should map single-bit mask values (associated with subtables) to new
        single-bit mask values. Any features not having any significant 1 bits
        (for enable masks) and 0 bits (for disable masks) after renumbering
        will not be included in the result.
        """
        
        r = type(self)()
        newBitLen = ((max(oldToNew.values()).bit_length() + 31) // 32) * 32
        modBase = 1 << newBitLen
        oldBitLen = ((max(oldToNew).bit_length() + 31) // 32) * 32
        
        for fe in self:
            if fe == LAST_ENTRY:
                continue
            
            enableNew = 0
            disableNew = -1
            dm = int(bin(fe.disableMask)[2:].rjust(oldBitLen, '1'), 2)
            
            for old, new in oldToNew.items():
                if fe.enableMask & old:
                    enableNew |= new
                
                if (~dm) & old:
                    disableNew &= (~new)
            
            if enableNew or (disableNew != -1):
                feNew = fe.__deepcopy__()
                feNew.enableMask = enableNew
                feNew.disableMask = disableNew % modBase
                r.append(feNew)
        
        r.append(LAST_ENTRY)
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _fetv = featureentry._testingValues
    
    _testingValues = (
        Features(),
        Features([_fetv[1], _fetv[2], LAST_ENTRY]),
        # feature entries for both cursive, and common and rare ligs
        Features(_fetv[4:11] + (LAST_ENTRY,)))
    
    del _fetv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
