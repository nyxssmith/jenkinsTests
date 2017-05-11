#
# pslookupgroup.py
#
# Copyright © 2009-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Ordered collections of PSLookupRecords.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.opentype import pslookuprecord

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(seq, **kwArgs):
    """
    This specifically checks for the case where the rule order and the order
    of the associated Lookups are not the same.
    """
    
    editor = kwArgs['editor']
    logger = kwArgs['logger']
    v = [obj.lookup.sequence for obj in seq]
    vNoneCheck = [obj for obj in v if obj is not None]
    
    if len(v) != len(vNoneCheck):
        logger.error((
          'V0997',
          (),
          "One or more Lookup sequence values is None!"))
        
        return False
    
    if v != sorted(v):
        logger.error((
          'V0998',
          (),
          "The order of rules is out-of-sync with respect to the order "
          "of the associated Lookups. This will result in inconsistent "
          "behavior of the font in WTLE and Uniscribe!"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

class PSLookupGroup(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing the set of effects to be performed in a single
    context. These are lists of PSLookupRecord objects; note the order is
    important!
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Effect #1:
      Sequence index: 2
      Lookup:
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
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Effect #%d:" % (i + 1,)),
        seq_compactremovesfalses = True,
        seq_falseifcontentsfalse = True,
        seq_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. Note that the list
        members will, when their buildBinary() methods are called in turn, add
        unresolved lookup list indices, for which a higher-level buildBinary()
        method will have to provide the indexMap.
        
        >>> w = writer.LinkedWriter()
        >>> v = _testingValues
        >>> d = {
        ...   v[0][0].lookup.asImmutable(): 10,
        ...   v[1][0].lookup.asImmutable(): 11,
        ...   v[1][1].lookup.asImmutable(): 5}
        >>> v[0].buildBinary(w, forGPOS=True)
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> utilities.hexdump(w.binaryString())
               0 | 0002 000A                                |....            |
        
        >>> w.reset()
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> v[1].buildBinary(w, forGPOS=True)
        >>> utilities.hexdump(w.binaryString())
               0 | 0000 000B 0001 0005                      |........        |
        """
        
        for obj in self:
            obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSLookupGroup object from the specified
        walker, doing source validation.
        
        >>> s0 = utilities.fromhex("00 02 00 0A")
        >>> s1 = utilities.fromhex("00 00 00 0B 00 01 00 05")
        >>> v = _testingValues
        >>> d = {5: v[1][1].lookup, 10: v[0][0].lookup, 11: v[1][0].lookup}
        >>> FL = []
        >>> fvb = PSLookupGroup.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("pslookupgroup_test")
        >>> obj0 = fvb(s0, count=1, fixupList=FL, logger=logger)
        pslookupgroup_test.pslookupgroup - DEBUG - Walker has 4 bytes remaining.
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 4 remaining bytes.
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 2
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 10
        
        >>> obj1 = fvb(s1, count=2, fixupList=FL, logger=logger)
        pslookupgroup_test.pslookupgroup - DEBUG - Walker has 8 bytes remaining.
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 8 remaining bytes.
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 0
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 11
        pslookupgroup_test.pslookupgroup.[1].pslookuprecord - DEBUG - Walker has 4 remaining bytes.
        pslookupgroup_test.pslookupgroup.[1].pslookuprecord - DEBUG - Sequence index is 1
        pslookupgroup_test.pslookupgroup.[1].pslookuprecord - DEBUG - Lookup index is 5
        
        >>> for llIndex, f in FL:
        ...     f(d[llIndex])
        >>> obj0 == v[0]
        True
        >>> obj1 == v[1]
        True
        
        >>> fvb(s0, count=2, fixupList=FL, logger=logger)
        pslookupgroup_test.pslookupgroup - DEBUG - Walker has 4 bytes remaining.
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 4 remaining bytes.
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 2
        pslookupgroup_test.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 10
        pslookupgroup_test.pslookupgroup - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pslookupgroup")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        assert 'fixupList' in kwArgs
        assert 'count' in kwArgs
        count = kwArgs.pop('count')
        fvw = pslookuprecord.PSLookupRecord.fromvalidatedwalker
        v = [None] * count
        
        for i in range(count):
            if not w.length():
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            obj = fvw(
              w,
              logger = logger.getChild("[%d]" % (i,)),
              **kwArgs)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a PSLookupGroup from the specified walker. The
        following keyword arguments are required:
        
            count       The number of PSLookupRecords in the list.
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookups won't be set
                        in the individual PSLookupRecords until this fixupFunc
                        is called. The call takes one argument, the Lookup
                        being set into it.
        
        >>> s0 = utilities.fromhex("00 02 00 0A")
        >>> s1 = utilities.fromhex("00 00 00 0B 00 01 00 05")
        >>> v = _testingValues
        >>> d = {5: v[1][1].lookup, 10: v[0][0].lookup, 11: v[1][0].lookup}
        >>> FL = []
        >>> obj0 = PSLookupGroup.frombytes(s0, count=1, fixupList=FL)
        >>> obj1 = PSLookupGroup.frombytes(s1, count=2, fixupList=FL)
        >>> for llIndex, f in FL:
        ...     f(d[llIndex])
        >>> obj0 == v[0]
        True
        >>> obj1 == v[1]
        True
        """
        
        assert 'fixupList' in kwArgs
        f = pslookuprecord.PSLookupRecord.fromwalker
        return cls(f(w, **kwArgs) for i in range(kwArgs['count']))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer, writer
    
    rv = pslookuprecord._testingValues
    
    _testingValues = (
        PSLookupGroup(rv[0:1]),
        PSLookupGroup(rv[1:3]),
        PSLookupGroup([rv[2]]),
        PSLookupGroup([rv[3]]),
        PSLookupGroup(rv[3:5]))
    
    del rv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
