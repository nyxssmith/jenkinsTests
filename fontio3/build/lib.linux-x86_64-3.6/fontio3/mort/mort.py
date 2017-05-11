#
# mort.py
#
# Copyright © 2011-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for AAT (and GX) 'mort' tables.
"""

# System imports
import collections
import functools
import itertools
import logging
import operator

# Other imports
from fontio3.fontdata import seqmeta

from fontio3.mort import (
  contextual,
  coverage,
  features,
  insertion,
  ligature,
  noncontextual,
  rearrangement)

# -----------------------------------------------------------------------------

#
# Private constants
#

_makers = {
  0: rearrangement.Rearrangement.fromwalker,
  1: contextual.Contextual.fromwalker,
  2: ligature.Ligature.fromwalker,
  4: noncontextual.Noncontextual.fromwalker,
  5: insertion.Insertion.fromwalker}

_makers_validated = {
  0: rearrangement.Rearrangement.fromvalidatedwalker,
  1: contextual.Contextual.fromvalidatedwalker,
  2: ligature.Ligature.fromvalidatedwalker,
  4: noncontextual.Noncontextual.fromvalidatedwalker,
  5: insertion.Insertion.fromvalidatedwalker}

_kindStrings = {
  0: "rearrangement",
  1: "contextual",
  2: "ligature",
  4: "noncontextual",
  5: "insertion"}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _defaultFlags_ppf(p, value, label, **kwArgs):
    s = "%X" % (value,)
    extra = len(s) % 8
    
    if extra:
        s = "0" * (8 - extra) + s
    
    p.simple(s, label=label, **kwArgs)

def _labelFunc(n, **kwArgs):
    kind = kwArgs['obj'].kind
    return "Subtable %d (%s)" % (n, _kindStrings[kind])

def _orLists(v1, v2):
    return list(map(operator.or_, v1, v2))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Mort(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing entire 'mort' tables. These are lists of subtable
    objects of the various kinds. There are two attributes:
    
        defaultFlags    An int of arbitary size, containing the total bit mask
                        for all features that are enabled by default.
    
        features        A Features object. Note that the mask values in this
                        object may span multiple chains; the internal logic
                        here will separate out individual chains.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = _labelFunc,
        item_pprintlabelfuncneedsobj = True,
        seq_compactremovesfalses = True)
    
    attrSpec = dict(
        defaultFlags = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Default flags",
            attr_pprintfunc = _defaultFlags_ppf),
        
        features = dict(
            attr_followsprotocol = True,
            attr_initfunc = features.Features,
            attr_label = "Feature map"))
    
    #
    # Methods
    #
    
    def _divideIntoChains(self, candidates):
        """
        Returns an iterator over Mort objects that will fit into a single
        chain. Note that depending on circumstances, the bit masks (in both
        the subtables and the features) may be redone.
        """
        
        # Determine how many bits each candidate needs
        
        nBits = [0] * len(candidates)
        
        for i, c in enumerate(candidates):
            for subtableIndex in c:
                nBits[i] += bin(self[subtableIndex].maskValue)[2:].count('1')
        
        # Now group 32 bits or less for the new chains, rebuilding the bit
        # masks for the enable and disable flags at the same time.
        
        currBitCount = 0
        cumulIndices = set()
        
        for i, c in enumerate(candidates):
            thisBitCount = nBits[i]
            
            if currBitCount + thisBitCount > 32:
                # emit this chain, then start the next one
                yield self._subset(sorted(cumulIndices))
                currBitCount = thisBitCount
                cumulIndices = set(c)
            
            else:
                currBitCount += thisBitCount
                cumulIndices.update(c)
        
        # emit this final chain
        yield self._subset(sorted(cumulIndices))
    
    def _makeChainGroupCandidates(self):
        """
        Returns a list of sets, each of which contains indices into self
        representing a connected group of subtables (connected via the info in
        the derived clusters). Each set therefore represents a group that could
        make up a single chain -- more can be added to a chain, but the group
        cannot be subdivided without causing potential glyph dependency bugs.
        """
        
        f = self.features
        combined = self.features.makeCombined()
        clusters = features._makeClusters(combined)
        r = []
        d = {}  # {featIndices} -> collector-OR'ed mask
        
        for c in clusters:
            d[c] = functools.reduce(operator.or_, (f[i].enableMask for i in c))
        
        featSetToSubtableIndices = collections.defaultdict(set)
        
        for i, subtable in enumerate(self):
            for fs, mask in d.items():
                if subtable.maskValue & mask:
                    featSetToSubtableIndices[fs].add(i)
        
        v = sorted(sorted(obj) for obj in featSetToSubtableIndices.values())
        cumul = set()
        
        for i, this in enumerate(v):
            if i == 0:
                newOne = max(this) + 1
                groupStartIndex = 0
                cumul = set(this)
            
            elif newOne == this[0]:  # should this be "newOne in this"?
                r.append(cumul)
                groupStartIndex = i
                newOne = max(newOne, max(this) + 1)
                cumul = set(this)
            
            else:
                cumul.update(this)
        
        r.append(cumul)
        return r
    
    def _subset(self, indices):
        """
        """
        
        v = [None] * len(indices)
        oldToNew = {}
        newDefaultFlags = 0
        nextBit = 1
        
        for newIndex, oldIndex in enumerate(indices):
            obj = self[oldIndex].__deepcopy__()
            old = obj.maskValue
            
            if old not in oldToNew:
                if bin(old)[2:].count('1') != 1:
                    raise ValueError(
                     "Subtable has maskValue with more than one bit set!")
                
                oldToNew[old] = nextBit
                
                if self.defaultFlags & old:
                    newDefaultFlags |= nextBit
                
                nextBit *= 2
            
            obj.maskValue = oldToNew[old]
            v[newIndex] = obj
        
        return type(self)(
          v,
          defaultFlags = newDefaultFlags,
          features = self.features.masksRenumbered(oldToNew))
    
    def buildBinary(self, w, **kwArgs):
        """
        The following keyword arguments are used:
        
            stakeValue      The stake value to be used at the start of this
                            output.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x00010000)  # version
        chainCountStake = w.addDeferredValue("L")
        chainCount = 0
        noFalses = self.__copy__()  # yes, shallow
        
        for i in range(len(noFalses) - 1, -1, -1):
            if not noFalses[i]:
                del noFalses[i]
        
        for chain in noFalses.chainIterator():
            chainStartLength = w.byteLength
            w.add("L", chain.defaultFlags)
            chainLengthStake = w.addDeferredValue("L")
            
            w.add(
              "H",
              1 + sum(obj.featureSetting != (0, 1) for obj in chain.features))
            
            w.add("H", len(chain))
            chain.features.buildBinary(w)
            
            for i, table in enumerate(chain):
                if table.kind == 2:
                    table = table.combinedActions()
                
                tableStartLength = w.byteLength
                tableLengthStake = w.addDeferredValue("H")
                table.coverage.buildBinary(w)
                w.add("L", table.maskValue)
                table.buildBinary(w)
                w.alignToByteMultiple(4)
                
                w.setDeferredValue(
                  tableLengthStake,
                  "H",
                  int(w.byteLength - tableStartLength))
            
            w.setDeferredValue(
              chainLengthStake,
              "L",
              int(w.byteLength - chainStartLength))
            
            chainCount += 1
        
        w.setDeferredValue(chainCountStake, "L", chainCount)
    
    def chainIterator(self):
        """
        """
        
        candidates = self._makeChainGroupCandidates()
        
        for chain in self._divideIntoChains(candidates):
            yield chain
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Mort object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('mort')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, chainCount = w.unpack("2L")
        
        if version != 0x10000:
            logger.error((
              'V0764',
              (version,),
              "Expected version 0x00010000, but got 0x%08X instead."))
            
            return None
        
        r = cls()
        kwArgs.pop('coverage', None)
        kwArgs.pop('maskValue', None)
        
        for chainIndex in range(chainCount):
            if w.length() < 12:
                logger.error((
                  'V0765',
                  (chainIndex,),
                  "The chain header for chain %d is missing or incomplete."))
                
                return None
            
            chainDefFlags, flagCount, subtableCount = w.unpack("L4x2H")
            extraShift = 32 * chainIndex
            r.defaultFlags |= (chainDefFlags << extraShift)
            itemLogger = logger.getChild("chain %d" % (chainIndex,))
            
            chainFeatures = features.Features.fromvalidatedwalker(
              w,
              count = flagCount,
              extraShift = extraShift,
              logger = itemLogger)
            
            # If this isn't the last chain, remove the (0, 1) entry
            if chainIndex < (chainCount - 1):
                if chainFeatures[-1].featureSetting != (0, 1):
                    itemLogger.warning((
                      'V0766',
                      (),
                      "The final feature is not (0, 1)."))
                
                del chainFeatures[-1]
            
            r.features.extend(chainFeatures)
            
            for subtableIndex in range(subtableCount):
                subtableLogger = itemLogger.getChild(
                  "subtable %d" % (subtableIndex,))
                
                if w.length() < 2:
                    subtableLogger.error(('V0004', (), "Insufficient bytes."))
                    return None
                
                subtableLength = w.unpack("H")
                
                cov = coverage.Coverage.fromvalidatedwalker(
                  w,
                  logger = subtableLogger,
                  **kwArgs)
                
                if cov is None:
                    return None
                
                if w.length() < 4:
                    subtableLogger.error((
                      'V0767',
                      (),
                      "Mask is missing or incomplete."))
                    
                    return None
                
                mask = w.unpack("L") << extraShift
                wSub = w.subWalker(0, relative=True, newLimit=subtableLength-8)
                w.skip(subtableLength - 8)
                
                if cov.kind not in _makers_validated:
                    subtableLogger.error((
                      'V0768',
                      (cov.kind,),
                      "Subtable kind %d is not recognized."))
                    
                    return None
                
                newTable = _makers_validated[cov.kind](
                  wSub,
                  coverage = cov,
                  maskValue = mask,
                  logger = subtableLogger,
                  **kwArgs)
                
                if newTable is None:
                    return None
                
                r.append(newTable)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Mort object from the specified walker.
        """
        
        version, chainCount = w.unpack("2L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'mort' version: 0x%08X" % (version,))
        
        r = cls()
        kwArgs.pop('coverage', None)
        kwArgs.pop('maskValue', None)
        
        for chainIndex in range(chainCount):
            extraShift = 32 * chainIndex
            chainDefFlags, flagCount, subtableCount = w.unpack("L4x2H")
            r.defaultFlags |= (chainDefFlags << extraShift)
            
            chainFeatures = features.Features.fromwalker(
              w,
              count = flagCount,
              extraShift = extraShift)
            
            # If this isn't the last chain, remove the (0, 1) entry
            if chainIndex < (chainCount - 1):
                assert chainFeatures[-1].featureSetting == (0, 1)
                del chainFeatures[-1]
            
            r.features.extend(chainFeatures)
            
            while subtableCount:
                #print("%08X" % (w.getOffset(),))
                subtableLength = w.unpack("H")
                cov = coverage.Coverage.fromwalker(w, **kwArgs)
                mask = w.unpack("L") << extraShift
                wSub = w.subWalker(0, relative=True, newLimit=subtableLength-8)
                w.skip(subtableLength - 8)
                maker = _makers[cov.kind]
                newTable = maker(wSub, coverage=cov, maskValue=mask, **kwArgs)
                r.append(newTable)
                subtableCount -= 1
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import pp
    
    def _makeObj():
        from fontio3 import fontedit
        e = fontedit.Editor.frompath("/Users/opstadd/Desktop/From other/HT.ttf")
        s = e.getRawTable(b'mort')
        m = Mort.frombytes(s)
        return m

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
