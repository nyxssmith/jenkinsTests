#
# postcomp_conditionaladd.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for action type 2 (conditionial add) in a 'just' postcompensation
table.
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
# Classes
#

class Postcomp_ConditionalAdd(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing conditional add actions. These are simple collections
    of the following attributes:
    
        addGlyph        A glyph to be added if the distance factor is growing,
                        or None if no extra glyph is to be added.
        
        substGlyph      A glyph to be put in place of the current glyph if the
                        growth factor equals or exceeds the substThreshold
                        value.
        
        substThreshold  A floating-point value representing the growth value
                        at which the substitution (and possible add) will
                        occur.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Trigger threshold: 1.0
    Glyph to be substituted: xyz49
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    Trigger threshold: 0.875
    Glyph to be added: afii60002
    Glyph to be substituted: xyz45
    
    >>> logger = utilities.makeDoctestLogger("pc_cond_val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    pc_cond_val.addGlyph - ERROR - The glyph index 'x' is not a real number.
    pc_cond_val.substGlyph - ERROR - The glyph index 103.25 is not an integer.
    pc_cond_val.substThreshold - ERROR - The value 40000 cannot be represented in signed (16.16) format.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        addGlyph = dict(
            attr_label = "Glyph to be added",
            attr_renumberdirect = True,
            attr_showonlyiffunc = (lambda x: x is not None),
            attr_usenamerforstr = True),
        
        substGlyph = dict(
            attr_label = "Glyph to be substituted",
            attr_renumberdirect = True,
            attr_usenamerforstr = True),
        
        substThreshold = dict(
            attr_initfunc = (lambda: 0.0),
            attr_label = "Trigger threshold",
            attr_validatefunc = valassist.isNumber_fixed))
    
    attrSorted = ('substThreshold', 'addGlyph', 'substGlyph')
    
    kind = 2  # Class constant for this action kind
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_ConditionalAdd object from the
        specified walker, doing source validation.
        
        >>> s = _testingValues[2].binaryString()
        >>> fvb = Postcomp_ConditionalAdd.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("pc_cond_fvw")
        >>> obj = fvb(s, logger=logger)
        pc_cond_fvw.postcomp_conditionaladd - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        pc_cond_fvw.postcomp_conditionaladd - DEBUG - Walker has 1 remaining bytes.
        pc_cond_fvw.postcomp_conditionaladd - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("postcomp_conditionaladd")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        threshold, addGlyph, substGlyph = w.unpack("l2H")
        
        return cls(
          substThreshold = threshold / 65536,
          addGlyph = (None if addGlyph == 0xFFFF else addGlyph),
          substGlyph = substGlyph)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_ConditionalAdd object from the
        specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Postcomp_ConditionalAdd.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == Postcomp_ConditionalAdd.frombytes(obj.binaryString())
        True
        """
        
        threshold, addGlyph, substGlyph = w.unpack("l2H")
        
        return cls(
          substThreshold = threshold / 65536,
          addGlyph = (None if addGlyph == 0xFFFF else addGlyph),
          substGlyph = substGlyph)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Postcomp_ConditionalAdd object to the
        specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 FFFF 0030                      |.......0        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0000 E000 0061 002C                      |.....a.,        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("l", int(round(self.substThreshold * 65536)))
        w.add("H", (0xFFFF if self.addGlyph is None else self.addGlyph))
        w.add("H", self.substGlyph)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        Postcomp_ConditionalAdd(),
        Postcomp_ConditionalAdd(1.0, None, 48),
        Postcomp_ConditionalAdd(0.875, 97, 44),
        
        # the following are bad (for validation testing)
        
        Postcomp_ConditionalAdd(40000, 'x', 103.25))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
