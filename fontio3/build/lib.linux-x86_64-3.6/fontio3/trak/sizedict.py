#
# sizedict.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
PPEM-specific shifts, measured in FUnits.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class SizeDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    These are dicts mapping floating-point PPEM values to FUnits.
    
    >>> _testingValues[0].pprint()
    9.0 ppem shift in FUnits: -35
    11.5 ppem shift in FUnits: -20
    14.0 ppem shift in FUnits: -1
    22.0 ppem shift in FUnits: 6
    
    >>> e = utilities.fakeEditor(0x10000)
    >>> f = io.StringIO()
    >>> logger = utilities.makeDoctestLogger("val", stream=f)
    >>> _testingValues[3].isValid(editor=e, logger=logger)
    False
    >>> for s in sorted(f.getvalue().splitlines()): print(s)
    val.['v'] - ERROR - The key 'v' is not a real number.
    val.[-3.5] - ERROR - The key -3.5 cannot be represented in unsigned (16.16) format.
    val.[18.25] - ERROR - The value 'j' is not a real number.
    val.[70000] - ERROR - The key 70000 cannot be represented in unsigned (16.16) format.
    >>> f.close()
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelfunc = (lambda k: "%s ppem shift in FUnits" % (k,)),
        item_pprintlabelpresort = True,
        item_scaledirectvalues = True,
        item_validatefunc = valassist.isFormat_h,
        item_validatefunckeys = functools.partial(
          valassist.isNumber_fixed,
          signed = False,
          label = 'key'))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the SizeDict object to the specified
        LinkedWriter. There is one required keyword argument, ppems, which must
        be a sorted list of floating-point ppem values. The keys in self must
        exactly match this list; if there are mismatches, an AssertionError is
        raised.
        
        >>> obj = _testingValues[0]
        >>> ppems = sorted(obj)
        >>> utilities.hexdump(obj.binaryString(ppems=ppems))
               0 | FFDD FFEC FFFF 0006                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        v = sorted(self)
        assert v == kwArgs['ppems'], "Mismatch in PPEM set for trak SizeDict!"
        w.addGroup("h", (self[i] for i in v))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new SizeDict from the data in the specified
        walker, doing source validation. The following keyword arguments are
        used:
        
            logger      A logger to which messages will be posted.
            
            ppems       A sorted sequence of floating-point ppem values. This
                        is required.
        
        >>> ppems = sorted(_testingValues[0])
        >>> s = _testingValues[0].binaryString(ppems=ppems)
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = SizeDict.fromvalidatedbytes
        >>> obj = fvb(s, ppems=ppems, logger=logger)
        fvw.sizedict - DEBUG - Walker has 8 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:-1], ppems=ppems, logger=logger)
        fvw.sizedict - DEBUG - Walker has 7 remaining bytes.
        fvw.sizedict - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("sizedict")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        ppems = kwArgs['ppems']
        assert list(ppems) == sorted(ppems), "Unsorted ppems!"
        
        if w.length() < 2 * len(ppems):
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(zip(ppems, w.group("h", len(ppems))))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new SizeDict from the data in the specified
        walker. The following keyword arguments are used:
        
            ppems       A sorted sequence of floating-point ppem values. This
                        is required.
        
        >>> obj = _testingValues[0]
        >>> d = {'ppems': sorted(obj)}
        >>> obj == SizeDict.frombytes(obj.binaryString(**d), **d)
        True
        """
        
        ppems = kwArgs['ppems']
        assert list(ppems) == sorted(ppems), "Unsorted ppems!"
        
        return cls(zip(ppems, w.group("h", len(ppems))))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import io
    from fontio3 import utilities
    
    _testingValues = (
        SizeDict({9.0: -35, 11.5: -20, 14.0: -1, 22.0: 6}),
        SizeDict({9.0: -15, 11.5: 0, 14.0: 5, 22.0: 18}),
        SizeDict({10.0: -15, 11.5: 0, 14.0: 5, 22.0: 18}),
        
        # bad values start here
        
        SizeDict({'v': -9, 18.25: 'j', 70000: -19, -3.5: -6}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
