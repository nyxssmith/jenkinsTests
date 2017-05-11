#
# valassist.py -- functions to assist validation
#
# Copyright © 2012, 2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Functions for checking various kinds of numeric (and other) validity.
"""

# System imports
import numbers

# -----------------------------------------------------------------------------

#
# Public functions
#

def isFormat_B(obj, **kwArgs):
    """
    Convenience wrapper function for isNumber_integer_unsigned with numBits set
    to 8.
    >>> a = 32
    >>> w = writer.LinkedWriter()
    >>> myStake = w.getNewStake()
    >>> logger = utilities.makeDoctestLogger("fw")
    >>> isFormat_B(a, logger=logger)
    True
    """
    
    return isNumber_integer_unsigned(obj, numBits=8, **kwArgs)

def isFormat_b(obj, **kwArgs):
    """
    Convenience wrapper function for isNumber_integer_signed with numBits set
    to 8.
    >>> a = -32
    >>> w = writer.LinkedWriter()
    >>> myStake = w.getNewStake()
    >>> logger = utilities.makeDoctestLogger("fw")
    >>> isFormat_b(a, logger=logger)
    True
    """
    
    return isNumber_integer_signed(obj, numBits=8, **kwArgs)

def isFormat_H(obj, **kwArgs):
    """
    Convenience wrapper function for isNumber_integer_unsigned with numBits set
    to 16.
    >>> a = 0xA2
    >>> w = writer.LinkedWriter()
    >>> myStake = w.getNewStake()
    >>> logger = utilities.makeDoctestLogger("fw")
    >>> isFormat_H(a, logger=logger)
    True
    """
    
    return isNumber_integer_unsigned(obj, numBits=16, **kwArgs)

def isFormat_h(obj, **kwArgs):
    """
    Convenience wrapper function for isNumber_integer_signed with numBits set
    to 16.
    >>> a = 0xA2
    >>> w = writer.LinkedWriter()
    >>> myStake = w.getNewStake()
    >>> logger = utilities.makeDoctestLogger("fw")
    >>> isFormat_h(a, logger=logger)
    True
    """
    
    return isNumber_integer_signed(obj, numBits=16, **kwArgs)

def isFormat_L(obj, **kwArgs):
    """
    Convenience wrapper function for isNumber_integer_unsigned with numBits set
    to 32.
    >>> a = (65535*2)+2
    >>> w = writer.LinkedWriter()
    >>> myStake = w.getNewStake()
    >>> logger = utilities.makeDoctestLogger("fw")
    >>> isFormat_L(a, logger=logger)
    True
    """
    
    return isNumber_integer_unsigned(obj, numBits=32, **kwArgs)

def isFormat_l(obj, **kwArgs):
    """
    Convenience wrapper function for isNumber_integer_signed with numBits set
    to 32.
    >>> a = (65535*-2)-20
    >>> w = writer.LinkedWriter()
    >>> myStake = w.getNewStake()
    >>> logger = utilities.makeDoctestLogger("fw")
    >>> isFormat_l(a, logger=logger)
    True
    """
    
    return isNumber_integer_signed(obj, numBits=32, **kwArgs)

def isNumber(obj, **kwArgs):
    """
    Returns True if obj is a number (float or integer, but not complex), and
    False otherwise. The following keyword arguments are supported:
    
        allowNone   A Boolean which, if False (the default), will cause an
                    error to be logged if obj is None.
        
        label       A string that can be used to identify what is being
                    commented about with more specificity. The default is the
                    string "value".
        
        logger      A logger to which messages will be posted. This is
                    required.
    
    >>> logger = utilities.makeDoctestLogger("isnum")
    >>> isNumber(25.75, logger=logger)
    True
    
    >>> isNumber("xy", logger=logger)
    isnum - ERROR - The value 'xy' is not a real number.
    False
    
    >>> isNumber(1-3j, logger=logger, label="glyph index")
    isnum - ERROR - The glyph index (1-3j) is not a real number.
    False
    
    >>> isNumber(None, logger=logger)
    isnum - ERROR - The value None is not a real number.
    False
    
    >>> isNumber(None, logger=logger, allowNone=True)
    True
    """
    
    if obj is None and kwArgs.get('allowNone', False):
        return True
    
    try:
        float(obj)
        r = True
    
    except:
        kwArgs['logger'].error((
          'G0009',
          (kwArgs.get('label', 'value'), obj),
          "The %s %r is not a real number."))
        
        r = False
    
    return r

def isNumber_integer(obj, **kwArgs):
    """
    Returns True if obj is an integer (no size restrictions), and False
    otherwise. The following keyword arguments are supported:
    
        allowNone   A Boolean which, if False (the default), will cause an
                    error to be logged if obj is None.
        
        label       A string that can be used to identify what is being
                    commented about with more specificity. The default is the
                    string "value".
        
        logger      A logger to which messages will be posted. This is
                    required.
    
    >>> logger = utilities.makeDoctestLogger("isnum_int")
    >>> isNumber_integer(14, logger=logger)
    True
    
    >>> isNumber_integer(14.0, logger=logger)
    True
    
    >>> isNumber_integer(14.5, logger=logger)
    isnum_int - ERROR - The value 14.5 is not an integer.
    False
    
    >>> isNumber_integer('x', logger=logger, label="CVT index")
    isnum_int - ERROR - The CVT index 'x' is not a real number.
    False
    
    >>> a = None
    >>> logger = utilities.makeDoctestLogger("fw")
    >>> isNumber_integer(a, logger=logger , allowNone=True)
    True
    """
    
    if obj is None and kwArgs.get('allowNone', False):
        return True
    
    if not isNumber(obj, **kwArgs):
        return False
    
    # We do the following test, and not an isinstance(obj, numbers.Integral)
    # test, because we're really concerned with the contents. In Python,
    # 14 == 14.0, so both forms should be allowed.
    #
    # Note the explicit float cast in the following test. That is there because
    # metaclass-based types with attributes were failing the simpler "obj !=
    # int(obj)" test, and for Value-derived classes that's not acceptable.
    
    if float(obj) != int(obj):
        kwArgs['logger'].error((
          'G0024',
          (kwArgs.get('label', 'value'), obj),
          "The %s %r is not an integer."))
        
        return False
    
    return True

def isNumber_integer_signed(obj, **kwArgs):
    """
    Returns True if obj is an integer whose signed representation fits within a
    specified number of bits, and False otherwise. The following keyword
    arguments are supported:
    
        allowNone   A Boolean which, if False (the default), will cause an
                    error to be logged if obj is None.
        
        label       A string that can be used to identify what is being
                    commented about with more specificity. The default is the
                    string "signed value".
        
        logger      A logger to which messages will be posted. This is
                    required.
        
        numBits     The number of bits into which the signed value will be
                    fitted. There is no default; this must be specified.
    
    >>> logger = utilities.makeDoctestLogger("isnum_intsigned")
    >>> isNumber_integer_signed(1000, logger=logger, numBits=16)
    True
    
    >>> isNumber_integer_signed(1000, logger=logger, numBits=8)
    isnum_intsigned - ERROR - The signed value 1000 does not fit in 8 bits.
    False
    
    >>> isNumber_integer_signed(-128, logger=logger, numBits=8)
    True
    
    >>> isNumber_integer_signed(-129, logger=logger, numBits=8, label="kerning value")
    isnum_intsigned - ERROR - The kerning value -129 does not fit in 8 bits.
    False
    
    >>> isNumber_integer_signed('x', logger=logger, numBits=8)
    isnum_intsigned - ERROR - The value 'x' is not a real number.
    False
        
    >>> nNone = None
    >>> isNumber_integer_signed(nNone, logger=logger, numBits=8, allowNone=True )
    True
    """
    
    if obj is None and kwArgs.get('allowNone', False):
        return True
    
    if not isNumber_integer(obj, **kwArgs):
        return False
    
    logger = kwArgs['logger']
    numBits = kwArgs['numBits']
    base = 2 ** (numBits - 1)
    
    if (obj < -base) or (obj >= base):
        logger.error((
          'G0010',
          (kwArgs.get('label', 'signed value'), obj, numBits),
          "The %s %d does not fit in %d bits."))
        
        return False
    
    return True

def isNumber_integer_unsigned(obj, **kwArgs):
    """
    Returns True if obj is an integer whose unsigned representation fits within
    a specified number of bits, and False otherwise. The following keyword
    arguments are supported:
    
        allowNone   A Boolean which, if False (the default), will cause an
                    error to be logged if obj is None.
        
        label       A string that can be used to identify what is being
                    commented about with more specificity. The default is the
                    string "unsigned value" if obj is non-negative, and
                    "negative value" otherwise.
        
        logger      A logger to which messages will be posted. This is
                    required.
        
        numBits     The number of bits into which the unsigned value will be
                    fitted. There is no default; this must be specified.
    
    >>> logger = utilities.makeDoctestLogger("isnum_intunsigned")
    >>> isNumber_integer_unsigned(200, logger=logger, numBits=8)
    True
    
    >>> isNumber_integer_unsigned(256, logger=logger, numBits=8)
    isnum_intunsigned - ERROR - The unsigned value 256 does not fit in 8 bits.
    False
    
    >>> isNumber_integer_unsigned(-1, logger=logger, numBits=8, label="glyph index")
    isnum_intunsigned - ERROR - The glyph index -1 cannot be used in an unsigned field.
    False
    
    >>> isNumber_integer_unsigned('x', logger=logger, numBits=8, label="storage index")
    isnum_intunsigned - ERROR - The storage index 'x' is not a real number.
    False
    
    >>> nNone = None
    >>> isNumber_integer_unsigned(nNone, logger=logger, numBits=8, allowNone=True )
    True
    """
    
    if obj is None and kwArgs.get('allowNone', False):
        return True
    
    logger = kwArgs['logger']
    numBits = kwArgs['numBits']
    
    if not isNumber_integer(obj, **kwArgs):
        return False
    
    if obj < 0:
        logger.error((
          'G0034',
          (kwArgs.get('label', 'negative value'), obj),
          "The %s %d cannot be used in an unsigned field."))
        
        return False
    
    if obj >= (2 ** numBits):
        logger.error((
          'G0011',
          (kwArgs.get('label', 'unsigned value'), obj, numBits),
          "The %s %d does not fit in %d bits."))
        
        return False
    
    return True

def isNumber_fixed(obj, **kwArgs):
    """
    Returns True if obj is a numeric value that can be expressed as a Fixed
    value (for instance, in a signed 32-bit field as a 16.16 value), or False
    otherwise. The following keyword arguments are supported:
    
        allowNone           A Boolean which, if False (the default), will cause
                            an error to be logged if obj is None.
        
        characteristic      Default is 16. This is the number of significant
                            bits before the binary point (including the sign
                            bit, if the signed flag is True).
        
        label               A string that can be used to identify what is being
                            commented about with more specificity. The default
                            is the string "value".
    
        logger              A logger to which messages will be posted. This is
                            required.
        
        numBits             Default is 32. This is the total number of bits the
                            value is to occupy.
        
        signed              Default is True. Controls whether the value is
                            signed or unsigned.
        
        truncationError     Default is False. If True, and if any nonzero bits
                            would be lost by the conversion to 16.16, an error
                            will be logged.
    
        truncationWarning   Default is False. If True, and if any nonzero bits
                            would be lost by the conversion to 16.16, a warning
                            will be logged.
    
    >>> logger = utilities.makeDoctestLogger("isnum_fixed")
    >>> isNumber_fixed(-1.5, logger=logger)
    True
    
    >>> isNumber_fixed(40000.5, logger=logger, label="kerning distance")
    isnum_fixed - ERROR - The kerning distance 40000.5 cannot be represented in signed (16.16) format.
    False
    
    >>> isNumber_fixed(40000.5, logger=logger, label="kerning distance", signed=False)
    True
    
    >>> isNumber_fixed(140000.5, logger=logger, label="kerning distance", signed=False)
    isnum_fixed - ERROR - The kerning distance 140000.5 cannot be represented in unsigned (16.16) format.
    False
    
    >>> isNumber_fixed(11 / 10, logger=logger)
    True
    
    >>> isNumber_fixed(11 / 10, logger=logger, truncationWarning=True)
    isnum_fixed - WARNING - The conversion of value 1.1 to signed (16.16) format lost some low-significance bits.
    True
    
    >>> isNumber_fixed(11 / 10, logger=logger, truncationError=True)
    isnum_fixed - ERROR - The conversion of value 1.1 to signed (16.16) format lost some low-significance bits.
    False
    
    >>> isNumber_fixed(0.75, logger=logger, numBits=16, characteristic=2)
    True
    
    >>> isNumber_fixed(2.75, logger=logger, numBits=16, characteristic=2)
    isnum_fixed - ERROR - The value 2.75 cannot be represented in signed (2.14) format.
    False
    
    >>> nNone = None
    >>> isNumber_fixed(nNone, logger=logger, numBits=16, allowNone=True )
    True
    
    >>> isNumber_fixed("xy", logger=logger, numBits=16, allowNone=True )
    isnum_fixed - ERROR - The value 'xy' is not a real number.
    False
    """
    
    if obj is None and kwArgs.get('allowNone', False):
        return True
    
    if not isNumber(obj, **kwArgs):
        return False
    
    logger = kwArgs['logger']
    numBits = kwArgs.get('numBits', 32)
    characteristic = kwArgs.get('characteristic', 16)
    shiftCount = numBits - characteristic
    shift = 2 ** shiftCount
    n = int(round(obj * shift))
    s = kwArgs.get('label', 'value')
    signed = kwArgs.get('signed', True)
    
    doc = "%ssigned (%d.%d) format" % (
      ("" if signed else "un"),
      characteristic,
      shiftCount)
    
    if signed:
        lowerLimit = -(2 ** (numBits - 1))
        upperLimit = -lowerLimit
    else:
        lowerLimit = 0
        upperLimit = 2 ** numBits
    
    if (n < lowerLimit) or (n >= upperLimit):
        logger.error((
          'G0031',
          (s, obj, doc),
          "The %s %r cannot be represented in %s."))
        
        return False
    
    if (n / shift) != obj:
        if kwArgs.get('truncationError', False):
            logger.error((
              'G0032',
              (s, obj, doc),
              "The conversion of %s %r to %s lost some "
              "low-significance bits."))
            
            return False
        
        elif kwArgs.get('truncationWarning', False):
            logger.warning((
              'G0033',
              (s, obj, doc),
              "The conversion of %s %r to %s lost some "
              "low-significance bits."))
    
    return True

def isPointIndex(obj, **kwArgs):
    """
    Returns True if obj is a valid point index for a specified glyph, or False
    otherwise. The following keyword arguments are supported:
    
        allowNone           A Boolean which, if False (the default), will cause
                            an error to be logged if obj is None.
        
        editor              An Editor that should contain a 'glyf' table (or,
                            eventually, a 'CFF ' table).
        
        glyphIndex          The glyph index containing the specified point.
        
        label               A string that can be used to identify what is being
                            commented about with more specificity. The default
                            is the string "point index".
    
        logger              A logger to which messages will be posted. This is
                            required.
    
    >>> logger = utilities.makeDoctestLogger("ispointindex")
    >>> e = _fakeEditor()
    >>> isPointIndex(5, logger=logger, editor=e, glyphIndex=40)
    True
    
    >>> isPointIndex(15, logger=logger, editor=e, glyphIndex=40)
    ispointindex - ERROR - Glyph 40 only contains 8 points; point index 15 is out of range.
    False
    """
    
    if obj is None and kwArgs.get('allowNone', False):
        return True
    
    if not isFormat_H(obj, **kwArgs):
        return False
    
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    glyphIndex = kwArgs.get('glyphIndex', None)
    label = kwArgs.get('label', 'point index')
    
    if glyphIndex is None:
        logger.warning((
          'G0039',
          (label,),
          "Unable to validate %s because no glyph index was specified."))
        
        return True
    
    if editor is None:
        logger.warning((
          'G0039',
          (label,),
          "Unable to validate %s because no editor is present."))
        
        return True
    
    if editor.reallyHas(b'glyf'):
        glyfTable = editor.glyf
        
        if glyphIndex not in glyfTable:
            logger.error((
              'G0040',
              (glyphIndex,),
              "The glyph index %d does not exist in the 'glyf' table."))
            
            return False
        
        try:
            count = glyfTable[glyphIndex].pointCount(editor=editor)
        except:
            count = None
        
        if count is None:
            logger.error((
              'G0040',
              (glyphIndex,),
              "The glyph index %d refers to components that do not exist."))
            
            return False
        
        if obj >= count:
            logger.error((
              'V0320',
              (glyphIndex, count, label, obj),
              "Glyph %d only contains %d points; %s %d is out of range."))
            
            return False
    
    # elif editor.reallyHas(b'CFF '):
    
    else:
        logger.error((
          'G0039',
          (),
          "Unable to validate because neither a 'glyf' nor a 'CFF ' table "
          "is present."))
        
        return False
    
    return True

def isString(obj, **kwArgs):
    """
    Returns True if obj is a string (possibly meeting size limits), and
    False otherwise. Note that the string must be Unicode, in both fontio2 and
    fontio3, for the purposes of this method.
    
    The following keyword arguments are supported:
    
        allowNone   A Boolean which, if False (the default), will cause an
                    error to be logged if obj is None.
        
        label       A string that can be used to identify what is being
                    commented about with more specificity. The default is the
                    string "value".
        
        logger      A logger to which messages will be posted. This is
                    required.
        
        maxSize     The maximum length of the string, or None if none.
        
        minSize     The minimum length of the string, or None if none.
    
    >>> logger = utilities.makeDoctestLogger("isstr")
    >>> isString("fred", logger=logger)
    True
    
    >>> isString(3.25, logger=logger)
    isstr - ERROR - The value 3.25 is not a Unicode string.
    False
    
    >>> isString(b'fred', logger=logger)
    isstr - ERROR - The value b'fred' is not a Unicode string.
    False
    
    >>> isString("fred", label="tag", maxSize=5, minSize=3, logger=logger)
    True
    
    >>> isString("fred", label="tag", maxSize=5, minSize=5, logger=logger)
    isstr - ERROR - The tag 'fred' does not have the required length of 5.
    False
    
    >>> isString("fred", label="tag", maxSize=2, logger=logger)
    isstr - ERROR - The tag 'fred' exceeds the maximum length of 2.
    False
    
    >>> isString("fred", label="tag", minSize=8, logger=logger)
    isstr - ERROR - The tag 'fred' is smaller than the minimum length of 8.
    False
    
    >>> isString(None, logger=logger)
    isstr - ERROR - The value None is not a Unicode string.
    False
    
    >>> isString(None, allowNone=True, logger=logger)
    True
    """
    
    if obj is None and kwArgs.get('allowNone', False):
        return True
    
    logger = kwArgs['logger']
    label = kwArgs.get('label', 'value')
    
    if not isinstance(obj, str):
        logger.error((
          'G0035',
          (label, obj),
          "The %s %r is not a Unicode string."))
        
        return False
    
    maxSize = kwArgs.get('maxSize', None)
    minSize = kwArgs.get('minSize', None)
    
    if (maxSize is not None) and (minSize is not None) and (maxSize == minSize):
        tooBig = tooSmall = len(obj) != maxSize
    
    else:
        tooBig = (maxSize is not None) and (len(obj) > maxSize)
        tooSmall = (minSize is not None) and (len(obj) < minSize)
    
    if tooBig and tooSmall:  # hack for size not specified value
        logger.error((
          'G0036',
          (label, obj, maxSize),
          "The %s %r does not have the required length of %d."))
        
        return False
    
    elif tooBig:
        logger.error((
          'G0037',
          (label, obj, maxSize),
          "The %s %r exceeds the maximum length of %d."))
        
        return False
    
    elif tooSmall:
        logger.error((
          'G0038',
          (label, obj, minSize),
          "The %s %r is smaller than the minimum length of %d."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import writer
    
    def _fakeEditor():
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(0x10000)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        return e

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
