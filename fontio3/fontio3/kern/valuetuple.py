#
# valuetuple.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sequences of values for 'kern' state tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.kern import value

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.warning((
          'V0629',
          (),
          "The kerning value sequence is empty, and will have no effect."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ValueTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a sequence of Value objects.
    
    >>> _testingValues[1].pprint()
    Pop #1:
      Value: 0
    
    >>> _testingValues[2].pprint()
    Pop #1:
      Value: 200
    Pop #2:
      Value: -200
    
    >>> logger = utilities.makeDoctestLogger("valuetuple")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    valuetuple.[0] - WARNING - Kerning value is zero.
    True
    
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    valuetuple - WARNING - The kerning value sequence is empty, and will have no effect.
    True
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i,**k: "Pop #%d" % (i + 1,)),
        seq_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ValueTuple to the specified writer. The
        caller is responsible for setting the isCrossStream keyword argument,
        which is passed through to the Value.buildBinary() method.
        
        >>> h = utilities.hexdump
        >>> d = {'isCrossStream': False}
        >>> h(_testingValues[1].binaryString(**d))
               0 | 0001                                     |..              |
        
        >>> h(_testingValues[2].binaryString(**d))
               0 | 00C8 FF39                                |...9            |
        
        >>> d['isCrossStream'] = True
        >>> h(_testingValues[3].binaryString(**d))
               0 | 8097                                     |..              |
        
        >>> h(_testingValues[4].binaryString(**d))
               0 | FF6A 8096 8001                           |.j....          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        lastIndex = len(self) - 1
        kwArgs.pop('isLast', None)
        
        for i, obj in enumerate(self):
            obj.buildBinary(w, isLast=(i==lastIndex), **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ValueTuple object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[4].binaryString(isCrossStream=True)
        >>> fvb = ValueTuple.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("valuetuple_fvw")
        >>> d = {'logger': logger, 'isCrossStream': True}
        >>> obj = fvb(s, **d)
        valuetuple_fvw.valuetuple - DEBUG - Walker has 6 remaining bytes.
        valuetuple_fvw.valuetuple.value 0.value - DEBUG - Walker has 6 remaining bytes.
        valuetuple_fvw.valuetuple.value 1.value - DEBUG - Walker has 4 remaining bytes.
        valuetuple_fvw.valuetuple.value 2.value - DEBUG - Walker has 2 remaining bytes.
        
        >>> fvb(s[:3], **d)
        valuetuple_fvw.valuetuple - DEBUG - Walker has 3 remaining bytes.
        valuetuple_fvw.valuetuple.value 0.value - DEBUG - Walker has 3 remaining bytes.
        valuetuple_fvw.valuetuple.value 1.value - DEBUG - Walker has 1 remaining bytes.
        valuetuple_fvw.valuetuple.value 1.value - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("valuetuple")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        v = []
        wasLast = [False]
        fvw = value.Value.fromvalidatedwalker
        kwArgs.pop('wasLast', None)
        
        while not wasLast[0]:
            itemLogger = logger.getChild("value %d" % (len(v),))
            obj = fvw(w, wasLast=wasLast, logger=itemLogger, **kwArgs)
            
            if obj is None:
                return None
            
            v.append(obj)
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ValueTuple object from the specified walker.
        The caller is responsible for setting the isCrossStream keyword
        argument, which is passed through to the Value.fromwalker() method.
        
        >>> f = ValueTuple.frombytes
        >>> d = {'isCrossStream': False}
        >>> obj = _testingValues[1]
        >>> obj == f(obj.binaryString(**d), **d)
        True
        
        >>> obj = _testingValues[2]
        >>> obj == f(obj.binaryString(**d), **d)
        True
        
        >>> d['isCrossStream'] = True
        >>> obj = _testingValues[3]
        >>> obj == f(obj.binaryString(**d), **d)
        True
        
        >>> obj = _testingValues[4]
        >>> obj == f(obj.binaryString(**d), **d)
        True
        """
        
        def _it():
            wasLast = [False]
            f = value.Value.fromwalker
            kwArgs.pop('wasLast', None)
            
            while not wasLast[0]:
                yield f(w, wasLast=wasLast, **kwArgs)
        
        return cls(_it())

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _vtv = value._testingValues
    
    _testingValues = (
        ValueTuple(),
        ValueTuple([_vtv[0]]),
        ValueTuple([_vtv[1], _vtv[2]]),
        ValueTuple([_vtv[3]]),
        ValueTuple([_vtv[4], _vtv[3], _vtv[5]])
        )
    
    del _vtv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
