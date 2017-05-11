#
# csmentry.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Collections of CSMRecords.
"""

# System imports
import itertools
import logging

# Other imports
from fontio3.ADFH import csmrecord
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.warning((
          'V0568',
          (),
          "The CSMEntry has no CSMRecords, and may be removed."))
        
        return True
    
    if not all(hasattr(entry, 'size') for entry in obj):
        logger.error((
          'V0569',
          (),
          "One or more components of the CSMEntry are not CSMRecords."))
        
        return False
    
    if len({entry.size for entry in obj}) != len(obj):
        logger.error((
          'V0570',
          (),
          "One or more CSMRecords in the CSMEntry share the same lower-limit "
          "size, which means some CSMRecords will be ignored."))
        
        return False
    
    v = [(x.gamma, x.insideCutoff, x.outsideCutoff) for x in obj]
    
    if len(v) > len(set(v)):
        logger.warning((
          'V0600',
          (),
          "One or more CSMRecords share all the same values, and are thus "
          "redundant."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CSMEntry(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing collections of CSMRecords. These are tuples.
    
    >>> _testingValues[1].pprint()
    Entry #1:
      Lower limit of size range (inclusive): 12
      Inside cutoff: 0.25
      Outside cutoff: -2.0
      Gamma: -0.25
    Entry #2:
      Lower limit of size range (inclusive): 20
      Inside cutoff: 0.75
      Outside cutoff: -1.0
      Gamma: -0.25
    
    >>> logger = utilities.makeDoctestLogger("csmentry_test")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[1].isValid(editor=e, logger=logger)
    True
    
    >>> _testingValues[3].isValid(editor=e, logger=logger)
    csmentry_test - ERROR - One or more CSMRecords in the CSMEntry share the same lower-limit size, which means some CSMRecords will be ignored.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda k: "Entry #%d" % (k + 1,)),
        seq_mergeappend = True,
        seq_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CSMEntry to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 000C 0000 4000  FFFE 0000 FFFF C000 |......@.........|
              10 | 0014 0000 C000 FFFF  0000 FFFF C000      |..............  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        
        for obj in self:
            obj.buildBinary(w)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new CSMEntry from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("csmentry_fvw")
        >>> fvb = CSMEntry.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        csmentry_fvw.csmentry - DEBUG - Walker has 30 remaining bytes.
        csmentry_fvw.csmentry.entry 0.csmrecord - DEBUG - Walker has 28 remaining bytes.
        csmentry_fvw.csmentry.entry 1.csmrecord - DEBUG - Walker has 14 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        csmentry_fvw.csmentry - DEBUG - Walker has 1 remaining bytes.
        csmentry_fvw.csmentry - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        csmentry_fvw.csmentry - DEBUG - Walker has 29 remaining bytes.
        csmentry_fvw.csmentry.entry 0.csmrecord - DEBUG - Walker has 27 remaining bytes.
        csmentry_fvw.csmentry.entry 1.csmrecord - DEBUG - Walker has 13 remaining bytes.
        csmentry_fvw.csmentry.entry 1.csmrecord - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("csmentry")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        v = [None] * count
        fvw = csmrecord.CSMRecord.fromvalidatedwalker
        
        for i in range(count):
            obj = fvw(w, logger=logger.getChild("entry %d" % (i,)), **kwArgs)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a CSMEntry from the specified walker.
        
        >>> fb = CSMEntry.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        f = csmrecord.CSMRecord.fromwalker
        return cls(map(f, itertools.repeat(w, w.unpack("H"))))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _rv = csmrecord._testingValues
    
    _testingValues = (
        CSMEntry(),
        CSMEntry([_rv[1], _rv[2]]),
        CSMEntry([_rv[3]]),
        
        # bad entries start here
        CSMEntry([_rv[1], _rv[1]]))
    
    del _rv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
