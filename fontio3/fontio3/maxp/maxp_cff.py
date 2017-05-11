#
# maxp_cff.py
#
# Copyright © 2004-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF 'maxp' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    editor = kwArgs['editor']
    logger = kwArgs['logger']
    
    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'maxp' table because the Editor is misisng."))
        
        return False
    
    if editor.reallyHas(b'glyf'):
        logger.error((
          'E1904',
          (),
          "Font has version 0.5 'maxp' table, "
          "but a 'glyf' table is present."))
        
        return False
    
    if not editor.reallyHas(b'CFF '):
        logger.error((
          'E1905',
          (),
          "Font has version 0.5 'maxp' table, "
          "but no 'CFF ' table is present."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Maxp_CFF(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire 'maxp' tables for CFF fonts. These are simple
    objects with a single attribute: numGlyphs.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        numGlyphs = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Number of glyphs"))
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Maxp_CFF object to the specified
        LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 0000 5000 0000                           |..P...          |
        
        >>> h(_testingValues[1].binaryString())
               0 | 0000 5000 0258                           |..P..X          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x5000)
        w.add("H", self.numGlyphs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Maxp_CFF object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Maxp_CFF.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.maxp_cff - DEBUG - Walker has 6 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:1], logger=logger)
        fvw.maxp_cff - DEBUG - Walker has 1 remaining bytes.
        fvw.maxp_cff - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("maxp_cff")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, numGlyphs = w.unpack("LH")
        
        if version != 0x5000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00005000, but got 0x%08X."))
            
            return None
        
        return cls(numGlyphs=numGlyphs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Maxp_CFF object from the data in the specified walker.
        
        >>> fb = Maxp_CFF.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        version, numGlyphs = w.unpack("LH")
        assert version == 0x5000
        return cls(numGlyphs=numGlyphs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Maxp_CFF(),
        Maxp_CFF(numGlyphs=600))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
