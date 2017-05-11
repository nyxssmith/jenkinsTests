#
# positions_distance.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the distance format of 'bsln' baseline data.
"""

# System imports
import logging

# Other imports
from fontio3.bsln import baselinekinds
from fontio3.fontdata import seqmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprintFunc(p, seq, **k):
    STRINGS = baselinekinds.STRINGS
    
    for i, n in enumerate(seq):
        if i in STRINGS:
            p.simple("%d FUnits" % (n,), label=STRINGS[i])

def _validate(obj, **kwArgs):
    okSet = set(baselinekinds.STRINGS)
    unexpected = [i for i, n in enumerate(obj) if n and (i not in okSet)]
    
    if unexpected:
        kwArgs['logger'].warning((
          'V0811',
          (unexpected,),
          "The following baseline kinds had nonzero values, but are not "
          "defined in this version of the 'bsln' table: %s"))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Positions_Distance(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    >>> _testingValues[0].pprint(label="Baselines")
    Baselines:
      Roman: 0 FUnits
      Ideographic (centered): 1024 FUnits
      Ideographic (low): -20 FUnits
      Hanging: 1800 FUnits
      Mathematical: 900 FUnits
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    True
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    val - WARNING - The following baseline kinds had nonzero values, but are not defined in this version of the 'bsln' table: [5]
    val.[0] - ERROR - The signed value -50000 does not fit in 16 bits.
    val.[1] - ERROR - The signed value 50000 does not fit in 16 bits.
    val.[2] - ERROR - The value 4.25 is not an integer.
    val.[3] - ERROR - The value 'fred' is not a real number.
    val.[4] - ERROR - The value [] is not a real number.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_scaledirect = True,  # they're FUnit values
        item_validatefunc = valassist.isFormat_h,
        seq_fixedlength = 32,
        seq_pprintfunc = _pprintFunc,
        seq_validatefunc_partial = _validate)
    
    isDistance = True
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Positions_Distance object from the specified
        walker, doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Positions_Distance.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.positions_distance - DEBUG - Walker has 64 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:-1], logger=logger)
        fvw.positions_distance - DEBUG - Walker has 63 remaining bytes.
        fvw.positions_distance - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("positions_distance")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 64:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(w.group("h", 32))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Positions_Distance object from the data in
        the specified walker.
        
        >>> t = _testingValues[0]
        >>> t == Positions_Distance.frombytes(t.binaryString())
        True
        """
        
        return cls(w.group("h", 32))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Positions_Distance object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0400 FFEC 0708  0384 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
        """
        
        w.addGroup("h", self)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Positions_Distance([0, 1024, -20, 1800, 900] + ([0] * 27)),
        
        # bad values start here
        
        Positions_Distance([-50000, 50000, 4.25, "fred", [], 3] + ([0] * 26)))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
