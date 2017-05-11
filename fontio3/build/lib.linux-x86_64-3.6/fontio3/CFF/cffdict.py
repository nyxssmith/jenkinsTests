#
# cffdict.py
#
# Copyright © 2012-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Generic support for CFF DICT structures.
"""

# Other imports
from fontio3.fontmath import rectangle
from fontio3 import utilitiesbackend

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(d, **kwArgs):
        return True

def _packCFFNumber(n):
    """
    Converts a number to a bytestring, formatted for writing in a CFF DICT. This
    function is passed in for LinkedWriter.addUnresolvedOffset for offset
    operators such as 'Encoding', 'charset', 'charStrings', and 'Private'. The
    function will expand to the CFF Dict-specific byte encoding and length.
    
    Note that in CFF DICTs, following the PostScript model, operands
    (values) precede operators (keys).
    """

    if -107 <= n <= 107:
        return utilitiesbackend.utPack('B', n + 139)
    elif 108 <= n <= 1131:
        return utilitiesbackend.utPack('H', n + 0xF694)    
    elif -1131 <= n <= -108:
        return utilitiesbackend.utPack('H', 0xFA94 - n)
    elif -32768 <= n <= 32767:
        return utilitiesbackend.utPack('Bh', 28, n)
    else:
        return utilitiesbackend.utPack('Bl', 29, n)

def _writeCffInteger(n, w):
    """
    Writes integer 'n' to LinkedWriter 'w' using CFF DICT Operator
    Encoding scheme for integer values.
    """
    if -107 <= n <= 107:
        w.add("B", n + 139)
        
    elif 108 <= n <= 1131:
        w.add("H", n + 0xF694)

    elif -1131 <= n <= -108:
        w.add("H", 0xFA94 - n)

    elif -32768 <= n <= 32767:
        w.add("Bh", 28, n)

    else:
        w.add("Bl", 29, n)

        
# -----------------------------------------------------------------------------

#
# Constants
#

_fpnybbles = [
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', 'E', 'E-', '', '-']
  
_reservedOperands = (22, 23, 24, 25, 26, 27, 31, 255)
    
# -----------------------------------------------------------------------------

#
# Public Functions
#

if 0:
    def __________________(): pass


def fromwalker(w, **kwArgs):
    """
    This method reads a CFF DICT structure from the supplied Walker. The
    result is returned as (operatorToOperandDict, keyOrderTuple). The
    keyOrderTuple can be used to maintain the original order of the
    keys when rebuilding/editing, etc.
    
    NOTE that this only reads and returns the "raw" operators/operands.
    There is basic data-structure validation available. The calling
    class is responsible for processing, content validation, etc.
    
    The following kwArgs are supported:
        'doValidation'      Perform validation checking of the data structures.
                            If this evaluates to True, a Logger must also be 
                            supplied with kwArg 'logger'.
                            
        'logger'            A logger to handle messages generated during validation.
                            This is *required* if 'doValidation' evaluates to True.
                            
    >>> data = _testingData[0]
    >>> w = walker.StringWalker(data)
    >>> d,t = fromwalker(w)
    >>> d
    {0: [0], 2: [300], (12, 0): [1]}
    >>> t
    [0, 2, (12, 0)]
    >>> data = _testingData[1]
    >>> w = walker.StringWalker(data)
    >>> logger = utilities.makeDoctestLogger("test")
    >>> fromwalker(w, doValidation=True, logger=logger)
    test.DICT - DEBUG - Walker has 8 remaining bytes.
    test.DICT - ERROR - Reserved value 22 in DICT operand
    ({0: [500]}, [0])
    """
    
    doValidation = kwArgs.get('doValidation', False)
    if doValidation:
        logger = kwArgs.get('logger')
        logger = logger.getChild('DICT')

    if doValidation:
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
    
    d = {}
    keyorder = []

    while w.stillGoing():
        operands = []
        
        while w.stillGoing():
            b0 = w.unpack("B")
            remLen = w.remainingLength()
            
            if b0 < 22:
                break # operator

            elif b0 in _reservedOperands:
                if doValidation:
                    logger.error((
                      "V0847",
                      (b0,),
                      "Reserved value %d in DICT operand"))
                return d,keyorder

            elif 32 <= b0 <= 246: # one-byte number
                operands.append(b0 - 139)

            elif b0 == 30: # floating-point
                sv = []
                
                while True:
                    if w.atEnd():
                        if doValidation:
                            logger.error((
                              "V0848",
                              (),
                              "DICT data too short for operand."))
                        return d,keyorder

                    b = w.unpack("B")
                    n = b >> 4
                    
                    if n == 15:
                        break
                    elif n == 13:
                        if doValidation:
                            logger.error((
                              "V0847",
                              (n,),
                              "Reserved value %d in DICT operand"))
                        return d,keyorder
                    else:
                        sv.append(_fpnybbles[n])
                        
                    n = b & 15
                    
                    if n == 15:
                        break
                    elif n == 13:
                        if doValidation:
                            logger.error((
                              "V0847",
                              (n,),
                              "Reserved value %d in DICT operand"))
                        return d,keyorder
                    else:
                        sv.append(_fpnybbles[n])

                operands.append(float(''.join(sv)))
            
            elif 247 <= b0 <= 254: # two-byte number
                if remLen < 1:
                    if doValidation:
                        logger.error((
                          "V0848",
                          (),
                          "DICT data too short for operand."))
                    return d,keyorder
                
                b1 = w.unpack("B")
                
                if b0 < 251:
                    operands.append((b0 - 247) * 256 + b1 + 108)
                else:
                    operands.append((251 - b0) * 256 - b1 - 108)
                    
            elif b0 == 28: # three-byte number
                if remLen < 2:
                    if doValidation:
                        logger.error((
                          "V0848",
                          (),
                          "DICT data too short for operand."))
                    return d,keyorder
                
                operands.append(w.unpack("h"))
                
            else: # four-byte number
                if remLen < 4:
                    if doValidation:
                        logger.error((
                          "V0848",
                          (),
                          "DICT data too short for operand."))
                    return d,keyorder

                operands.append(w.unpack("l"))

            if len(operands) > 48:
                if doValidation:
                    logger.error((
                      'V0844',
                      (),
                      "Number of DICT operands exceeds limit of 48."))
                
        else:
            if doValidation:
                logger.error((
                  "V0849",
                  (),
                  "DICT operands not followed by operator."))
            return d,keyorder
            
        if b0 == 12: # extension operator
            if w.atEnd():
                if doValidation:
                    logger.error((
                      "V0848",
                      (),
                      "DICT data too short for operand."))
                return d,keyorder
                
            key = (12, w.unpack("B"))
        
        else:
            key = b0
            
        keyorder.append(key)
        d[key] = operands

    return d, keyorder
    

def buildBinary(d, w, **kwArgs):
    """
    Adds the binary data for the CFF DICT object to the specified
    LinkedWriter. d should be supplied as 'raw'
    operators/operands. The 'originalOrder' kwArg may be supplied to
    indicate the ordering of keys. Otherwise they will be in numerically
    sorted order.
    
    NOTE: for operators that specify offsets, a temporary value of 0 is
    written, regardless of the value supplied in d. When writing
    dictionaries with these keys, it is essential to supply stakeValues
    containing a key for 'cffstart'. New stakes for the various keys
    will be added, and you should call stakeCurrentWithValue in the
    appropriate locations prior to attempting to fully resolve the
    binary string of the writer.

    >>> d = {0: [0], 2: [300], (12, 0): [1]}
    >>> wr = writer.LinkedWriter()
    >>> buildBinary(d, wr)
    >>> print(utilities.hexdumpString(wr.binaryString()), end='')
           0 |8B00 F7C0 028C 0C00                      |........        |
    >>> namedStakes = {'cffstart': 0}
    >>> d = {0: [0], 15: 5}
    >>> wr = writer.LinkedWriter()
    >>> wr.stakeCurrentWithValue(namedStakes['cffstart'])
    >>> buildBinary(d, wr, stakeValues=namedStakes)
    >>> wr.addString(b"----------")
    >>> wr.stakeCurrentWithValue(namedStakes['charset'])
    >>> print(utilities.hexdumpString(wr.binaryString()), end='')
           0 |8B00 990F 2D2D 2D2D  2D2D 2D2D 2D2D      |....----------  |
    """

    stakeValues = kwArgs.get('stakeValues', None)
    originalOrder = kwArgs.get('originalOrder', None)
    if originalOrder is not None:
        od = {v:i for i,v in enumerate(originalOrder)}
        opSort = sorted(d, key = lambda x: od.get(x,x) if isinstance(od.get(x,x),tuple) else (od.get(x,x),))
    else:
        opSort = sorted(d, key=(lambda x: x if isinstance(x, tuple) else (x,)))

    for op in opSort:
        if op == (12, 14):
            forcebold = d[op]
            if forcebold:
                _writeCffInteger(1, w)
            
        elif op == (12, 36):
            stakeValues['fdarray'] = w.getNewStake()
            w.addUnresolvedOffset(
              _packCFFNumber,
              stakeValues['cffstart'],
              stakeValues['fdarray'])
    
        elif op == (12, 37):
            stakeValues['fdselect'] = w.getNewStake()
            w.addUnresolvedOffset(
              _packCFFNumber,
              stakeValues['cffstart'],
              stakeValues['fdselect'])
    
        elif op == 15:
            # if 1 or 2, store directly; otherwise stake for offset
            cs = d[op]
            if cs in (1,2):
                _writeCffInteger(cs, w)
            else:
                stakeValues['charset'] = w.getNewStake()
                w.addUnresolvedOffset(
                  _packCFFNumber,
                  stakeValues['cffstart'],
                  stakeValues['charset'])
              
        elif op == 16:
            # if 1, store directly; otherwise stake for offset
            enc = d[op]
            if enc == 1:
                _writeCffInteger(enc, w)
            else:
                stakeValues['encoding'] = w.getNewStake()
                w.addUnresolvedOffset(
                  _packCFFNumber,
                  stakeValues['cffstart'],
                  stakeValues['encoding'])
              
        elif op == 17:
            stakeValues['charstrings'] = w.getNewStake()
            w.addUnresolvedOffset(
              _packCFFNumber,
              stakeValues['cffstart'],
              stakeValues['charstrings'])
              
        elif op == 18:
            if 'fdindex' in kwArgs:
                pdidx = kwArgs.get('fdindex')
                stakestarttag = 'privatestart%d' % (pdidx,)
                stakeendtag = 'privateend%d' % (pdidx,)
            else:
                stakestarttag = 'privatestart'
                stakeendtag = 'privateend'

            stakeValues[stakestarttag] = w.getNewStake()
            stakeValues[stakeendtag] = w.getNewStake()
            w.addUnresolvedOffset(
              _packCFFNumber,
              stakeValues[stakestarttag],
              stakeValues[stakeendtag])
            w.addUnresolvedOffset(
              _packCFFNumber,
              stakeValues['cffstart'],
              stakeValues[stakestarttag])
        
        elif op == 19:
            if 'privateindex' in kwArgs:
                lsindex = kwArgs.get('privateindex')
                stakefromtag = 'privatestart%d' % (lsindex,)
                staketotag = 'lsrstart%d' % (lsindex,)
                stakeValues[staketotag] = w.getNewStake()
            else:
                stakefromtag = 'privatestart'
                staketotag = 'privateend'

            w.addUnresolvedOffset(
              _packCFFNumber,
              stakeValues[stakefromtag],
              stakeValues[staketotag])

        else:
            for operand in d[op]:
                if isinstance(operand, float):
                    s = str(operand).lstrip('0') # strip leading zero(es)
                    nybs = [1, 14]
                    i = 0
                    
                    while i < len(s):
                        c = s[i]
                        
                        if '0' <= c <= '9':
                            nybs.append(int(c))
                        
                        elif c == '.':
                            nybs.append(10)
                        
                        elif c == '-':
                            nybs.append(14)
                        
                        elif c == 'E':
                            if (i < (len(s) - 1)) and (s[i+1] == '-'):
                                nybs.append(12)
                                i += 1
                            
                            else:
                                nybs.append(11)

                        i += 1
                    
                    if len(nybs) % 2: nybs.append(15)
                    else: nybs.extend([15, 15])
                    for i in range(0, len(nybs), 2):
                        n = nybs[i] * 16 + nybs[i+1]
                        w.add("B", n)
                
                else: # integer
                    _writeCffInteger(operand, w)

        if isinstance(op, tuple):
            w.add("BB", *op)
        else:
            w.add("B", op)
            
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walker, writer
    
    _testingData = (
        utilities.fromhex("8B 00 F7 C0 02 8C 0C 00"),
        utilities.fromhex("F8 88 00 8B 16 8B 0C 00")
        )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

