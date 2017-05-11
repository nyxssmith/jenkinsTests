#
# value.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single values in a 'kern' table. A value (as distinct from an
entry) is a shift distance, with (optionally, and only for cross-stream
kerning) a flag indicating whether the cross-stream distance should be reset to
zero.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import valuemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    n = int(obj)
    
    if n == -1:
        logger.warning((
          'V0625',
          (),
          "A value of -1 cannot be used. -2 will be used instead."))
        
        n = -2
    
    elif n % 2:
        logger.warning((
          'V0624',
          (n,),
          "The value %d is odd. The least significant bit will be discarded "
          "since that bit is used as a flag."))
        
        n += (-1 if n > 0 else 1)
    
    if kwArgs.get('isCrossStream', False):
        if n < -16384:
            logger.error((
             'V0626',
             (n,),
             "The value %d is too low and cannot be used without losing "
             "significant digits."))
            
            return False
        
        elif n > 16382:
            logger.error((
             'V0627',
             (n,),
             "The value %d is too high and cannot be used without losing "
             "significant digits."))
            
            return False
    
    else:
        if n < -32768:
            logger.error((
             'V0626',
             (n,),
             "The value %d is too low and cannot be used without losing "
             "significant digits."))
            
            return False
        
        elif n > 32766:
            logger.error((
             'V0627',
             (n,),
             "The value %d is too high and cannot be used without losing "
             "significant digits."))
            
            return False
    
    if (not n):
        logger.warning((
          'V0628',
          (),
          "Kerning value is zero."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Value(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing single values. A Value is a signed FUnit distance,
    with this attribute:
    
        resetCrossStream        If True, the cross-stream shift will be reset
                                to zero.
    
    >>> print(Value(200))
    200
    >>> print(isinstance(Value(200), int))
    True
    >>> print(Value(-200))
    -200
    >>> print(Value(0, resetCrossStream=True))
    0, Reset shift to baseline = True
    
    >>> logger = utilities.makeDoctestLogger("value")
    >>> e = utilities.fakeEditor(0x10000)
    >>> d = {'logger': logger, 'editor': e, 'isCrossStream': False}
    >>> Value(200).isValid(**d)
    True
    
    >>> Value(201).isValid(**d)
    value - WARNING - The value 201 is odd. The least significant bit will be discarded since that bit is used as a flag.
    True
    
    >>> Value(-1).isValid(**d)
    value - WARNING - A value of -1 cannot be used. -2 will be used instead.
    True
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_scales = True,
        value_validatefunc_partial = _validate)
    
    attrSpec = dict(
        resetCrossStream = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Reset shift to baseline",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for the Value to the specified writer. The
        following keyword arguments are supported:
        
            isCrossStream   If True, this is the cross-stream kerning case, so
                            a 0x8000 bit on means the resetCrossStream
                            attribute will be set True. If False, the 0x8000
                            bit contributes to the value, as usual
            
            isLast          If True, the value will have the 0x0001 bit turned
                            on; otherwise this bit will be cleared. There is no
                            default; this must be present.
        
        >>> h = utilities.hexdump
        >>> for i, n in enumerate(_testingValues):
        ...     for ics in ((True,) if n.resetCrossStream else (False, True)):
        ...         for il in (False, True):
        ...             print(
        ...               "Index %d, Reset cross-stream %s, Last %s" %
        ...               (i, ics, il))
        ...             h(n.binaryString(isCrossStream=ics, isLast=il))
        Index 0, Reset cross-stream False, Last False
               0 | 0000                                     |..              |
        Index 0, Reset cross-stream False, Last True
               0 | 0001                                     |..              |
        Index 0, Reset cross-stream True, Last False
               0 | 0000                                     |..              |
        Index 0, Reset cross-stream True, Last True
               0 | 0001                                     |..              |
        Index 1, Reset cross-stream False, Last False
               0 | 00C8                                     |..              |
        Index 1, Reset cross-stream False, Last True
               0 | 00C9                                     |..              |
        Index 1, Reset cross-stream True, Last False
               0 | 00C8                                     |..              |
        Index 1, Reset cross-stream True, Last True
               0 | 00C9                                     |..              |
        Index 2, Reset cross-stream False, Last False
               0 | FF38                                     |.8              |
        Index 2, Reset cross-stream False, Last True
               0 | FF39                                     |.9              |
        Index 2, Reset cross-stream True, Last False
               0 | 7F38                                     |.8              |
        Index 2, Reset cross-stream True, Last True
               0 | 7F39                                     |.9              |
        Index 3, Reset cross-stream True, Last False
               0 | 8096                                     |..              |
        Index 3, Reset cross-stream True, Last True
               0 | 8097                                     |..              |
        Index 4, Reset cross-stream True, Last False
               0 | FF6A                                     |.j              |
        Index 4, Reset cross-stream True, Last True
               0 | FF6B                                     |.k              |
        Index 5, Reset cross-stream True, Last False
               0 | 8000                                     |..              |
        Index 5, Reset cross-stream True, Last True
               0 | 8001                                     |..              |
        
        >>> h(n.binaryString(isCrossStream=False, isLast=False))
        Traceback (most recent call last):
          ...
        ValueError: resetCrossStream should only be True for cross-stream kerning!
        """
        
        n = int(self)
        
        if n < 0:
            n += 0x10000
        
        if kwArgs['isLast']:
            n |= 0x0001
        else:
            n &= 0xFFFE
        
        if kwArgs['isCrossStream']:
            if self.resetCrossStream:
                n |= 0x8000
            else:
                n &= 0x7FFF
        
        elif self.resetCrossStream:
            raise ValueError(
              "resetCrossStream should only be True for cross-stream kerning!")
        
        w.add("H", n)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Value from the specified walker, doing source
        validation.
        """
        
        logger = kwArgs.get('logger', logging.getLogger())
        logger = logger.getChild('value')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        n = w.unpack("H")
        
        if n & 0x0001:
            last = True
            n &= 0xFFFE
        else:
            last = False
        
        kwArgs.get('wasLast', [])[:] = [last]
        
        if kwArgs['isCrossStream']:
            
            # The top bit is reserved for the reset value, so for this case
            # there are only 15 significant bits (well, 14 since the 0x0001
            # bit is already cleared).
            
            rcs = bool(n & 0x8000)
            n &= 0x7FFF
            
            if n >= 0x4000:
                n -= 0x8000  # convert to 15-bit signed
        
        else:
            rcs = False
            
            if n >= 0x8000:
                n -= 0x10000  # convert to 16-bit signed
        
        return cls(n, resetCrossStream=rcs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Value from the specified walker. There are
        two keyword arguments:
        
            isCrossStream   If True, this is the cross-stream kerning case, so
                            a 0x8000 bit on means the resetCrossStream
                            attribute will be set True. If False, the 0x8000
                            bit contributes to the value, as usual
            
            wasLast         The caller may pass this in with an empty list as a
                            value. On return, the list will have one element:
                            True if this Value had the 0x0001 bit set and
                            False otherwise. This information is used by the
                            ActionList.fromwalker() method.
        
        >>> WL = []
        >>> for i, n in enumerate(_testingValues):
        ...     for ics in ((True,) if n.resetCrossStream else (False, True)):
        ...         for il in (False, True):
        ...             s = n.binaryString(isCrossStream=ics, isLast=il)
        ...             nNew = Value.frombytes(
        ...               s,
        ...               isCrossStream = ics,
        ...               wasLast = WL)
        ...             if nNew != n:
        ...                 print("Failure 1")
        ...             if WL[0] != il:
        ...                 print("Failure 2")
        """
        
        n = w.unpack("H")
        
        if n & 0x0001:
            last = True
            n &= 0xFFFE
        else:
            last = False
        
        kwArgs.get('wasLast', [])[:] = [last]
        
        if kwArgs['isCrossStream']:
            
            # The top bit is reserved for the reset value, so for this case
            # there are only 15 significant bits (well, 14 since the 0x0001
            # bit is already cleared).
            
            rcs = bool(n & 0x8000)
            n &= 0x7FFF
            
            if n >= 0x4000:
                n -= 0x8000  # convert to 15-bit signed
        
        else:
            rcs = False
            
            if n >= 0x8000:
                n -= 0x10000  # convert to 16-bit signed
        
        return cls(n, resetCrossStream=rcs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Value(0),
        Value(200),
        Value(-200),
        Value(150, resetCrossStream=True),
        Value(-150, resetCrossStream=True),
        Value(0, resetCrossStream=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
