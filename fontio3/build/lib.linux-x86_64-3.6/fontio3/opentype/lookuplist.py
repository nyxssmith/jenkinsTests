#
# lookuplist.py
#
# Copyright © 2009-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for LookupLists, a top-level construct used by GPOS and GSUB tables.
"""

# System imports
import gc
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.opentype import lookup

# -----------------------------------------------------------------------------

#
# Classes
#

class LookupList(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Lists of Lookup objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Lookup 0:
      Subtable 0 (Single positioning table):
        xyz11:
          FUnit adjustment to origin's x-coordinate: -10
      Lookup flags:
        Right-to-left for Cursive: False
        Ignore base glyphs: False
        Ignore ligatures: False
        Ignore marks: False
        Mark attachment type: 4
      Sequence order (lower happens first): 0
    Lookup 1:
      Subtable 0 (Pair (glyph) positioning table):
        (xyz11, xyz21):
          First adjustment:
            FUnit adjustment to origin's x-coordinate: 30
            Device for vertical advance:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
          Second adjustment:
            Device for origin's x-coordinate:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
            Device for origin's y-coordinate:
              Tweak at 12 ppem: -5
              Tweak at 13 ppem: -3
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 2
              Tweak at 20 ppem: 3
        (xyz9, xyz16):
          Second adjustment:
            FUnit adjustment to origin's x-coordinate: -10
        (xyz9, xyz21):
          First adjustment:
            Device for vertical advance:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
      Lookup flags:
        Right-to-left for Cursive: False
        Ignore base glyphs: True
        Ignore ligatures: False
        Ignore marks: False
      Sequence order (lower happens first): 1
    Lookup 2:
      Subtable 0 (Pair (class) positioning table):
        (First class 1, Second class 1):
          Second adjustment:
            FUnit adjustment to origin's x-coordinate: -10
        (First class 2, Second class 0):
          First adjustment:
            Device for vertical advance:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
        (First class 2, Second class 1):
          First adjustment:
            FUnit adjustment to origin's x-coordinate: 30
            Device for vertical advance:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
          Second adjustment:
            Device for origin's x-coordinate:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
            Device for origin's y-coordinate:
              Tweak at 12 ppem: -5
              Tweak at 13 ppem: -3
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 2
              Tweak at 20 ppem: 3
        Class definition table for first glyph:
          xyz16: 1
          xyz6: 1
          xyz7: 1
          xyz8: 2
        Class definition table for second glyph:
          xyz21: 1
          xyz22: 1
          xyz23: 1
      Lookup flags:
        Right-to-left for Cursive: True
        Ignore base glyphs: False
        Ignore ligatures: False
        Ignore marks: False
      Sequence order (lower happens first): 2
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_islookup = True,
        item_pprintlabelfunc = (lambda n: "Lookup %d" % (n,)),
        item_usenamerforstr = True,
        seq_compactremovesfalses = True,
        seq_mergeappend = True)
    
    #
    # Methods
    #
    
    def _forceAllExtensions(self):
        """
        Creates and returns a new LookupList whose elements are Extension
        objects of the originals.
        """
        
        v = [None] * len(self)
        
        for i, lkup in enumerate(self):
            if len(lkup):
                k = lkup[0].kind
                
                if k == ('GPOS', 9) or k == ('GSUB', 7):
                    v[i] = lkup
                
                elif k[0] == 'GPOS':
                    from fontio3.GPOS import extension
                    
                    v2 = [extension.Extension(original=obj) for obj in lkup]
                    
                    v[i] = lookup.Lookup(
                      v2,
                      flags = lkup.flags,
                      markFilteringSet = lkup.markFilteringSet,
                      sequence = lkup.sequence)
                
                elif k[0] == 'GSUB':
                    from fontio3.GSUB import extension
                    
                    v2 = [extension.Extension(original=obj) for obj in lkup]
                    
                    v[i] = lookup.Lookup(
                      v2,
                      flags = lkup.flags,
                      markFilteringSet = lkup.markFilteringSet,
                      sequence = lkup.sequence)
                
                else:
                    assert False, "Unknown 'kind' in Lookup!"
            
            else:
                assert False, "Empty Lookup!"
        
        return type(self)(v)
    
    def _sort(self):
        """
        Ensures the lookups contained in the list are in the correct order, as
        determined by their sequence attributes. Lookups whose sequence
        attributes are None will be moved to the end of the list.
        
        >>> t = _testingValues[1].__deepcopy__()
        >>> ids = [id(obj) for obj in t]
        >>> t[0].sequence = 2
        >>> t[1].sequence = None
        >>> t[2].sequence = 0
        >>> t._sort()
        >>> [id(obj) for obj in t] == [ids[2], ids[0], ids[1]]
        True
        """
        
        rawList = list(self)
        nextAvail = len(rawList)
        v = [None] * nextAvail
        
        for i, obj in enumerate(rawList):
            if obj.sequence is None:
                v[i] = (nextAvail, i)
                nextAvail += 1
            
            else:
                v[i] = (obj.sequence, i)
        
        self[:] = list(rawList[t[1]] for t in sorted(v))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> w = writer.LinkedWriter()
        >>> ep = {}
        >>> _testingValues[1].buildBinary(w, extensionPool=ep)
        >>> for i, obj, stake in sorted(ep.values()):
        ...   obj.buildBinary(w, stakeValue=stake)
        >>> utilities.hexdump(w.binaryString())
               0 | 0003 0008 0018 0028  0009 0400 0001 0008 |.......(........|
              10 | 0001 0001 0000 0028  0009 0002 0001 0008 |.......(........|
              20 | 0001 0002 0000 0026  0009 0001 0001 0008 |.......&........|
              30 | 0001 0002 0000 0068  0001 0008 0001 FFF6 |.......h........|
              40 | 0001 0001 000A 0001  000E 0081 0031 0002 |.............1..|
              50 | 0016 0030 0001 0002  0008 000A 0002 000F |...0............|
              60 | 0000 0000 FFF6 0000  0000 0014 0000 0034 |...............4|
              70 | 0000 0000 0000 0001  0014 001E 001A 0000 |................|
              80 | 001A 000E 000C 0014  0002 BDF0 0020 3000 |............. 0.|
              90 | 000C 0012 0001 8C04  0002 004C 0081 0031 |...........L...1|
              A0 | 0058 006E 0003 0002  0000 0000 0000 0000 |.X.n............|
              B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              C0 | 0000 0000 0000 0000  0000 FFF6 0000 0000 |................|
              D0 | 0000 0084 0000 0000  0000 001E 0084 0000 |................|
              E0 | 0084 0078 0001 0004  0005 0006 0007 000F |...x............|
              F0 | 0002 0003 0005 0006  0001 0007 0007 0002 |................|
             100 | 000F 000F 0001 0002  0001 0014 0016 0001 |................|
             110 | 000C 0014 0002 BDF0  0020 3000 000C 0012 |......... 0.....|
             120 | 0001 8C04                                |....            |
        
        >>> w = writer.LinkedWriter()
        >>> ep = {}
        >>> _testingValues[1].buildBinary(w, extensionPool=ep, forceExtensions=False)
        >>> for i, obj, stake in sorted(ep.values()):
        ...   obj.buildBinary(w, stakeValue=stake)
        >>> utilities.hexdump(w.binaryString())
               0 | 0003 0008 001E 0078  0001 0400 0001 0008 |.......x........|
              10 | 0001 0008 0001 FFF6  0001 0001 000A 0002 |................|
              20 | 0002 0001 0008 0001  000E 0081 0031 0002 |.............1..|
              30 | 0016 0030 0001 0002  0008 000A 0002 000F |...0............|
              40 | 0000 0000 FFF6 0000  0000 0014 0000 0034 |...............4|
              50 | 0000 0000 0000 0001  0014 001E 001A 0000 |................|
              60 | 001A 000E 000C 0014  0002 BDF0 0020 3000 |............. 0.|
              70 | 000C 0012 0001 8C04  0002 0001 0001 0008 |................|
              80 | 0002 004C 0081 0031  0058 006E 0003 0002 |...L...1.X.n....|
              90 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              B0 | 0000 FFF6 0000 0000  0000 0084 0000 0000 |................|
              C0 | 0000 001E 0084 0000  0084 0078 0001 0004 |...........x....|
              D0 | 0005 0006 0007 000F  0002 0003 0005 0006 |................|
              E0 | 0001 0007 0007 0002  000F 000F 0001 0002 |................|
              F0 | 0001 0014 0016 0001  000C 0014 0002 BDF0 |................|
             100 | 0020 3000 000C 0012  0001 8C04           |. 0.........    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if kwArgs.get('forceExtensions', True):
            self = self._forceAllExtensions()
        
        w.add("H", len(self))
        self._sort()
        objStakes = list(w.getNewStake() for obj in self)
        
        for i, obj in enumerate(self):
            w.addUnresolvedOffset("H", stakeValue, objStakes[i])
        
        for i, obj in enumerate(self):
            obj.buildBinary(w, stakeValue=objStakes[i], **kwArgs)
    
    @classmethod
    def fromtoplevel(cls, gposOrGsub, **kwArgs):
        """
        Walks the object via the gatheredRefs call to find all Lookup objects,
        and then uses the embedded sequence information to construct and return
        a LookupList in the correct order.
        """
        
        doFrequentGC = kwArgs.get('doFrequentGC', False)
        gathered = gposOrGsub.gatheredRefs(**kwArgs)
        
        # Before proceeding, walk each of the gathered Lookups and check for
        # cycles.
        
        memo = set()
        acc = set()
        
        for lkObj in gathered.values():
            if lkObj.hasCycles(activeCycleCheck=acc, memo=memo):
                raise utilities.CycleError("Cycles in Lookup!")
        
        # Now that we're clear of cycles, proceed.
        r = cls()
        pool = set()
        
        for i, obj in enumerate(gathered.values()):
            if doFrequentGC:
                gc.collect()
            
            immut = obj.asImmutable(**kwArgs)
            
            if immut not in pool:
                pool.add(immut)
                r.append(obj)
        
        r._sort()
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LookupList object from the specified walker,
        doing source validation. The following keyword arguments are passed
        through to the Lookup creation code:
        
            forGPOS     True if a GPOS LookupList is being made; False if a
                        GSUB LookupList is being made.
            
            GDEF        Optional; must be a GDEF object if the font is OpenType
                        1.6 or later.
            
            logger      A logger to which messages will be posted.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('lookuplist')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        offsetCount = w.unpack("H")
        logger.debug(('Vxxxx', (offsetCount,), "Offset count is %d"))
        
        if w.length() < 2 * offsetCount:
            logger.error((
              'V0406',
              (),
              "The Lookup offsets are missing or incomplete."))
            
            return None
        
        offsets = w.group("H", offsetCount)
        fvw = lookup.Lookup.fromvalidatedwalker
        fixupList = []
        v = [None] * offsetCount
        
        for i, offset in enumerate(offsets):
            logger.debug(('Vxxxx', (i, offset), "Offset %d is %d"))
            subLogger = logger.getChild("lookup %d" % (i,))
            
            obj = fvw(
              w.subWalker(offset),
              sequence = i,
              fixupList = fixupList,
              logger = subLogger,
              **kwArgs)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        for llIndex, f in fixupList:
            f(v[llIndex])
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LookupList from the specified walker. The
        following keyword arguments are passed through to the Lookup creation
        code:
        
            forGPOS     True if a GPOS LookupList is being made; False if a
                        GSUB LookupList is being made.
            
            GDEF        Optional; must be a GDEF object if the font is OpenType
                        1.6 or later.
        
        >>> obj = _testingValues[1]
        >>> obj == LookupList.frombytes(obj.binaryString(), forGPOS=True)
        True
        """
        
        offsets = w.group("H", w.unpack("H"))
        f = lookup.Lookup.fromwalker
        fl = []
        
        v = [
          f(w.subWalker(o), sequence=i, fixupList=fl, **kwArgs)
          for i, o in enumerate(offsets)]
        
        for llIndex, f in fl:
            f(v[llIndex])  # does the fixup
        
        return cls(v)
    
    def index(self, lookForObj):
        for i, obj in enumerate(self):
            if lookForObj[0].kind == obj[0].kind:
                if lookForObj == obj:
                    return i
        
        raise IndexError("Lookup not found in LookupList")

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer, writer
    
    ltv = lookup._testingValues
    
    _testingValues = (
        LookupList(),
        LookupList([ltv[0], ltv[1], ltv[2]]),
        LookupList([ltv[3]]),
        LookupList([ltv[4]]),
        LookupList([ltv[5], ltv[4]]))
    
    del ltv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
