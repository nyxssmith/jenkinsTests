#
# postcomp_repeatedadd.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for action type 5 (repeated add) in a 'just' postcompensation
table.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_flags(obj, **kwArgs):
    if not valassist.isNumber(obj, **kwArgs):
        return False
    
    if obj:
        kwArgs['logger'].error((
          'V0740',
          (obj,),
          "Flags value should be zero, but is %d."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

class Postcomp_RepeatedAdd(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing repeated add actions. These are simple
    collections of the following attributes:
    
        addGlyph        A glyph to be added repeatedly if the distance factor
                        is growing.
        
        flags           Reserved; set to zero.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Glyph to be repeatedly added: xyz40
    
    >>> logger = utilities.makeDoctestLogger("pc_repeat_val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    pc_repeat_val.addGlyph - ERROR - The glyph index 'x' is not a real number.
    pc_repeat_val.flags - ERROR - Flags value should be zero, but is 25.
    False
    
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    pc_repeat_val.addGlyph - ERROR - Glyph index 8192 too large.
    pc_repeat_val.flags - ERROR - The value 'aardvark' is not a real number.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        addGlyph = dict(
            attr_label = "Glyph to be repeatedly added",
            attr_renumberdirect = True,
            attr_usenamerforstr = True),
        
        flags = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Flags",
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate_flags))
    
    attrSorted = ('flags', 'addGlyph')
    
    kind = 5  # Class constant for this action kind
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_RepeatedAdd object from the
        specified walker, doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Postcomp_RepeatedAdd.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("pc_repeat_fvw")
        >>> obj = fvb(s, logger=logger)
        pc_repeat_fvw.postcomp_repeatedadd - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        pc_repeat_fvw.postcomp_repeatedadd - DEBUG - Walker has 1 remaining bytes.
        pc_repeat_fvw.postcomp_repeatedadd - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("postcomp_repeatedadd")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(*w.unpack("2H"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_RepeatedAdd object from the
        specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Postcomp_RepeatedAdd.frombytes(obj.binaryString())
        True
        """
        
        return cls(*w.unpack("2H"))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Postcomp_RepeatedAdd object to the
        specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0027                                |...'            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2H", self.flags, self.addGlyph)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        Postcomp_RepeatedAdd(),
        Postcomp_RepeatedAdd(0, 39),
        
        # the following are bad (for validation testing)
        
        Postcomp_RepeatedAdd(25, 'x'),
        Postcomp_RepeatedAdd('aardvark', 0x2000))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
