#
# kernset.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 2 (Pair Adjustment) subtables for a GPOS table with specific
combination of 2 subtables: one PairGlyphs which are exceptions to the second
subtable, a PairClasses. 'kernset' is not an actual OpenType LookupType; it is
a FontWorker-specific scheme for describing this specific combination of
subtables. Hence there are only FontWorker-related methods here.
"""

# System imports
import logging

# Other imports
from fontio3.GPOS import pairclasses, pairglyphs

# -----------------------------------------------------------------------------

#
# Factory function
#

def Kernset_fromValidatedFontWorkerSource(fws, **kwArgs):
    """
    Factory function for creating a Kernset, which is a combined lookup
    consisting of one PairGlyphs object + one PairClasses object from a
    FontWorkerSource, with source validation.
    
    >>> logger = utilities.makeDoctestLogger("FW_test")
    >>> ks = Kernset_fromValidatedFontWorkerSource(_test_FW_fws1, namer=_test_FW_namer, logger=logger)
    >>> ks[0].pprint()
    Key((3, 5)):
      First adjustment:
        FUnit adjustment to horizontal advance: 123
    >>> ks[1].pprint()
    (First class 1, Second class 1):
      First adjustment:
        FUnit adjustment to horizontal advance: -50
    Class definition table for first glyph:
      1: 1
      2: 1
      3: 1
    Class definition table for second glyph:
      4: 1
      5: 1
      6: 1
    """
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("kernset")

    terminalString = 'lookup end' # note, ignore explicit 'subtable end'

    ksglyphs = pairglyphs.PairGlyphs.fromValidatedFontWorkerSource(
        fws, logger=logger, iskernset=True, **kwArgs)

    fws.lineNumber -= 1

    ksclasses = pairclasses.PairClasses.fromValidatedFontWorkerSource(
        fws, logger=logger, iskernset=True, **kwArgs)

    fws.lineNumber -= 1

    for line in fws:
        if line.lower().strip() == terminalString:
            if ksglyphs and ksclasses:
                return ksglyphs, ksclasses
            else:
                logger.error((
                    'Vxxxx',
                    (),
                    "Must define both pair glyphs and pair classes for kernset."))
                return tuple()

    logger.warning(('V0961',
        (fws.lineNumber,),
        'line %d -- reached end of lookup unexpectedly'))

    return None



# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'Adieresis': 2,
        'Aacute': 3,
        'O': 4,
        'Oslash': 5,
        'Odieresis': 6,
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws1 = FontWorkerSource(StringIO(
        """
        left x advance	Aacute	Oslash	123

        firstclass definition begin
        A	1
        Adieresis	1
        Aacute	1
        class definition end

        secondclass definition begin
        O	1
        Oslash	1
        Odieresis	1
        class definition end

        left x advance	1	1	-50

        lookup end
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

