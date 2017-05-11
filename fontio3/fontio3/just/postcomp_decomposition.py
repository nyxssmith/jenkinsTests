#
# postcomp_decomposition.py
#
# Copyright © 2012-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for action type 0 (decomposition) in a 'just' postcompensation table.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.opentype import glyphtuple
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj.glyphs:
        logger.warning((
          'V0733',
          (),
          "The list of decomposed glyphs is empty."))
    
    try:
        float(obj.lowerLimit)
        float(obj.upperLimit)
    
    except:
        return True  # metaclass validation will report the error(s)
    
    if obj.lowerLimit > obj.upperLimit:
        logger.error((
          'V0734',
          (obj.lowerLimit, obj.upperLimit),
          "The lower limit %s is greater than the upper limit %s."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Postcomp_Decomposition(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing decomposition actions. These are simple collections of
    the following attributes:
    
        glyphs          A GlyphTuple_Output with the decomposed glyphs.
        
        lowerLimit      A floating-point value. If the distance factor is less
                        than this value, the ligature will be decomposed.
        
        order           Numerical order in which this ligature will be
                        decomposed.
        
        upperLimit      A floating-point value. If the distance factor is
                        greater than this value, the ligature will be
                        decomposed.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Lower trigger for decomposition: 0.75
    Upper trigger for decomposition: 1.75
    Order (lower=earlier): 2
    Decomposed glyphs:
      0: xyz44
      1: xyz42
      2: afii60002
    
    >>> logger = utilities.makeDoctestLogger("pc_decomp_val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    pc_decomp_val.glyphs.[2] - ERROR - The glyph index 'x' is not a real number.
    False
    
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    pc_decomp_val - WARNING - The list of decomposed glyphs is empty.
    pc_decomp_val.lowerLimit - ERROR - The value -40000 cannot be represented in signed (16.16) format.
    False
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    pc_decomp_val - WARNING - The list of decomposed glyphs is empty.
    pc_decomp_val - ERROR - The lower limit 1.5 is greater than the upper limit 0.75.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        glyphs = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphtuple.GlyphTuple_Output,
            attr_label = "Decomposed glyphs"),
        
        lowerLimit = dict(
            attr_initfunc = (lambda: 0.0),
            attr_label = "Lower trigger for decomposition",
            attr_validatefunc = valassist.isNumber_fixed),
        
        order = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Order (lower=earlier)"),
        
        upperLimit = dict(
            attr_initfunc = (lambda: 0.0),
            attr_label = "Upper trigger for decomposition",
            attr_validatefunc = valassist.isNumber_fixed))
    
    attrSorted = ('lowerLimit', 'upperLimit', 'order', 'glyphs')
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    kind = 0  # Class constant for this action kind
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_Decomposition object from the
        specified walker, doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Postcomp_Decomposition.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("pc_decomp_fvw")
        >>> obj = fvb(s, logger=logger)
        pc_decomp_fvw.postcomp_decomposition - DEBUG - Walker has 18 remaining bytes.
        pc_decomp_fvw.postcomp_decomposition.glyphtuple - DEBUG - Walker has 8 bytes remaining.
        pc_decomp_fvw.postcomp_decomposition.glyphtuple - DEBUG - Count is 3
        pc_decomp_fvw.postcomp_decomposition.glyphtuple - DEBUG - Data are (43, 41, 97)
        
        >>> fvb(s[:3], logger=logger)
        pc_decomp_fvw.postcomp_decomposition - DEBUG - Walker has 3 remaining bytes.
        pc_decomp_fvw.postcomp_decomposition - ERROR - Insufficient bytes.
        
        >>> fvb(s[:13], logger=logger)
        pc_decomp_fvw.postcomp_decomposition - DEBUG - Walker has 13 remaining bytes.
        pc_decomp_fvw.postcomp_decomposition.glyphtuple - DEBUG - Walker has 3 bytes remaining.
        pc_decomp_fvw.postcomp_decomposition.glyphtuple - DEBUG - Count is 3
        pc_decomp_fvw.postcomp_decomposition.glyphtuple - ERROR - The glyph sequence is missing or incomplete.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("postcomp_decomposition")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 10:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        lo, hi, order = w.unpack("2lH")
        kwArgs.pop('countFirst', None)
        
        glyphs = glyphtuple.GlyphTuple_Output.fromvalidatedwalker(
          w,
          countFirst = True,
          logger = logger,
          **kwArgs)
        
        if glyphs is None:
            return None
        
        return cls(
          glyphs = glyphs,
          lowerLimit = lo / 65536,
          order = order,
          upperLimit = hi / 65536)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_Decomposition object from the
        specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Postcomp_Decomposition.frombytes(obj.binaryString())
        True
        """
        
        lo, hi, order = w.unpack("2lH")
        kwArgs.pop('countFirst', None)
        
        glyphs = glyphtuple.GlyphTuple_Output.fromwalker(
          w,
          countFirst = True,
          **kwArgs)
        
        return cls(
          glyphs = glyphs,
          lowerLimit = lo / 65536,
          order = order,
          upperLimit = hi / 65536)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Postcomp_Decomposition object to the
        specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 C000 0001 C000  0002 0003 002B 0029 |.............+.)|
              10 | 0061                                     |.a              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("l", int(round(self.lowerLimit * 65536)))
        w.add("l", int(round(self.upperLimit * 65536)))
        w.add("H", self.order)
        self.glyphs.buildBinary(w, countFirst=True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        Postcomp_Decomposition(),
        
        Postcomp_Decomposition(
          glyphs = glyphtuple.GlyphTuple_Output([43, 41, 97]),
          lowerLimit = 0.75,
          order = 2,
          upperLimit = 1.75),
        
        # the following are bad (for validation testing)
        
        Postcomp_Decomposition(
          glyphs = glyphtuple.GlyphTuple_Output([12, 29, 'x'])),
        
        Postcomp_Decomposition(
          order = 'x',
          lowerLimit = -40000),
        
        Postcomp_Decomposition(
          lowerLimit = 1.5,
          upperLimit = 0.75))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
