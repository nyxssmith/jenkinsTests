#
# postcomp_unconditionaladd.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for action type 1 (unconditional add) in a 'just' postcompensation
table.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.opentype import glyphtuple

# -----------------------------------------------------------------------------

#
# Classes
#

class Postcomp_UnconditionalAdd(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing unconditional add actions. These are simple
    collections of the following attributes:
    
        addGlyph        A glyph to be added if the distance factor is growing.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Glyph to be added: xyz40
    
    >>> logger = utilities.makeDoctestLogger("pc_uncond_val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    pc_uncond_val.addGlyph - ERROR - The glyph index 'x' is not a real number.
    False
    
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    pc_uncond_val.addGlyph - ERROR - Glyph index 8192 too large.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        addGlyph = dict(
            attr_label = "Glyph to be added",
            attr_renumberdirect = True,
            attr_usenamerforstr = True))
    
    kind = 1  # Class constant for this action kind
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_UnconditionalAdd object from the
        specified walker, doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Postcomp_UnconditionalAdd.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("pc_uncond_fvw")
        >>> obj = fvb(s, logger=logger)
        pc_uncond_fvw.postcomp_unconditionaladd - DEBUG - Walker has 2 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        pc_uncond_fvw.postcomp_unconditionaladd - DEBUG - Walker has 1 remaining bytes.
        pc_uncond_fvw.postcomp_unconditionaladd - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("postcomp_unconditionaladd")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(w.unpack("H"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_UnconditionalAdd object from the
        specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Postcomp_UnconditionalAdd.frombytes(obj.binaryString())
        True
        """
        
        return cls(w.unpack("H"))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Postcomp_UnconditionalAdd object to the
        specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0027                                     |.'              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", self.addGlyph)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        Postcomp_UnconditionalAdd(),
        Postcomp_UnconditionalAdd(39),
        
        # the following are bad (for validation testing)
        
        Postcomp_UnconditionalAdd('x'),
        Postcomp_UnconditionalAdd(0x2000))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
