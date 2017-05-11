#
# pslookuprecord.py
#
# Copyright © 2009-2010, 2012-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Objects representing single effects for contextual lookups (both GPOS and
GSUB).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _specialValidate(obj, **kwArgs):
    """
    This method does the normal deep validation, but with a catch: if the
    suppressDeepValidation keyword argument is present and True, then the deep
    validation is not performed.
    
    This is necessary because deeply nested fonts can take a very long time to
    validate, so it's better for the high-level objects (GSUB and GPOS) to
    gather all Lookup objects separately, and validate them seriatim. Since
    this gathering will also gather the contained lookups in the PSLookupRecord
    (or derivative) classes, their validation will still be done -- just not
    recursively.
    """
    
    if kwArgs.get('suppressDeepValidation', False):
        return True
    
    return obj.isValid(**kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PSLookupRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects containing information on single effects performed by a GPOS
    table's contextual or chained-contextual lookups. These are simple objects
    with two attributes:
    
        sequenceIndex   The relative glyph position (not glyph index per se,
                        but rather where the glyph index is) at which the
                        effect will be applied.
        
        lookup          The Lookup object with the effect to be applied.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Sequence index: 2
    Lookup:
      Subtable 0 (Single positioning table):
        xyz11:
          FUnit adjustment to origin's x-coordinate: -10
      Lookup flags:
        Right-to-left for Cursive: False
        Ignore base glyphs: False
        Ignore ligatures: False
        Ignore marks: False
        Mark attachment type: 4
      Sequence order (lower happens first): 0
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        sequenceIndex = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Sequence index",
            attr_validatefunc = valassist.isFormat_H),
        
        lookup = dict(
            attr_enablecyclechecktag = 'lookup',
            attr_followsprotocol = True,
            attr_islookup = True,
            attr_label = "Lookup",
            attr_validatefunc = _specialValidate))
    
    attrSorted = ('sequenceIndex', 'lookup')
    
    #
    # Methods
    #
    
    def _fixup(self, obj):
        self.lookup = obj
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. An unresolved
        lookup list index is added, so the caller (or somewhere higher) is
        responsible for adding an index map to the writer with the tag
        "lookupList" before the writer's binaryString() method is called.
        
        >>> w = writer.LinkedWriter()
        >>> v = _testingValues
        >>> v[0].buildBinary(w, forGPOS=True)
        >>> v[1].buildBinary(w, forGPOS=True)
        >>> v[2].buildBinary(w, forGPOS=True)
        >>> w.addIndexMap(
        ...   "lookupList_GPOS",
        ...   { v[0].lookup.asImmutable(): 10,
        ...     v[1].lookup.asImmutable(): 11,
        ...     v[2].lookup.asImmutable(): 5})
        >>> utilities.hexdump(w.binaryString())
               0 | 0002 000A 0000 000B  0001 0005           |............    |
        """
        
        w.add("H", self.sequenceIndex)
        s = ("lookupList_GPOS" if kwArgs['forGPOS'] else "lookupList_GSUB")
        w.addUnresolvedIndex("H", s, self.lookup.asImmutable())
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSLookupRecord object from the specified
        walker, doing source validation.
        
        >>> s = utilities.fromhex("00 01")
        >>> logger = utilities.makeDoctestLogger("pslookuprecord_test")
        >>> fvb = PSLookupRecord.fromvalidatedbytes
        >>> FL = []
        >>> fvb(s, logger=logger, fixupList=FL)
        pslookuprecord_test.pslookuprecord - DEBUG - Walker has 2 remaining bytes.
        pslookuprecord_test.pslookuprecord - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pslookuprecord")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        assert 'fixupList' in kwArgs
        seq, listIndex = w.unpack("2H")
        logger.debug(('Vxxxx', (seq,), "Sequence index is %d"))
        logger.debug(('Vxxxx', (listIndex,), "Lookup index is %d"))
        r = cls(sequenceIndex=seq)  # lookup will be set later via _fixup
        
        # In the following line, note that r._fixup is a bound method
        
        kwArgs['fixupList'].append((listIndex, r._fixup))
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSLookupRecord from the specified walker.
        There is one required keyword argument:
        
            fixupList   A list, to which a pair (lookupListIndex, fixupFunc)
                        will be appended. The actual lookup won't be set
                        in the PSLookupRecord until this call is made. The
                        call takes one argument, the Lookup being set into
                        it.
        
        >>> FL = []
        >>> s = utilities.fromhex("00 02 00 0A")
        >>> obj = PSLookupRecord.frombytes(s, fixupList=FL)
        >>> obj.lookup is None
        True
        >>> FL[0][0]
        10
        >>> FL[0][1](_testingValues[0].lookup)
        >>> obj.pprint(namer=namer.testingNamer())
        Sequence index: 2
        Lookup:
          Subtable 0 (Single positioning table):
            xyz11:
              FUnit adjustment to origin's x-coordinate: -10
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
            Mark attachment type: 4
          Sequence order (lower happens first): 0
        """
        
        seq, listIndex = w.unpack("2H")
        r = cls(sequenceIndex=seq)  # lookup will be set later via _fixup
        
        # In the following line, note that r._fixup is a bound method
        
        kwArgs['fixupList'].append((listIndex, r._fixup))
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.opentype import lookup
    from fontio3.utilities import namer, writer
    
    ltv = lookup._testingValues
    
    _testingValues = (
        PSLookupRecord(2, ltv[0]),
        PSLookupRecord(0, ltv[1]),
        PSLookupRecord(1, ltv[2]),
        PSLookupRecord(0, ltv[4]),
        PSLookupRecord(1, ltv[5]))
    
    del ltv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
