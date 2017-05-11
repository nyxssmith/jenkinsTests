#
# noncontextual.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 4 (noncontextual, or swash) 'mort' subtables.
"""

# Other imports
from fontio3.utilities import lookup

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_mask(p, value, label, **kwArgs):
    s = "%X" % (value,)
    extra = len(s) % 8
    
    if extra:
        s = "0" * (8 - extra) + s
    
    p.simple(s, label=label, **kwArgs)

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.warning((
          'V0667',
          (),
          "Swash table is empty and will have no effect."))
    
    idempotents = set(k for k, v in obj.items() if k == v)
    
    if idempotents:
        logger.warning((
          'V0668',
          (sorted(idempotents),),
          "The following glyphs map to themselves: %s"))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Noncontextual(lookup.Lookup_OutGlyph):
    """
    Objects representing format 4 (noncontextual, or swash) 'mort' subtables.
    These are dicts mapping input glyphs to output glyphs. There are two
    attributes:
    
        coverage        A Coverage object (q.v.)
        
        maskValue       The arbitrarily long integer value with the subFeature
                        mask bits for this subtable.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz16: afii60002
    xyz17: afii60003
    Mask value: 08000000
    Coverage:
      Subtable kind: 4
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    xyz23: xyz41
    xyz26: xyz20
    xyz81: U+0163
    Mask value: 0004000000000000
    Coverage:
      Subtable kind: 4
    
    >>> logger = utilities.makeDoctestLogger("swash")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    swash - WARNING - Swash table is empty and will have no effect.
    True
    
    >>> obj = _testingValues[1].__deepcopy__()
    >>> obj.update({24: 24, 19: 19, 80: 80})
    >>> obj.isValid(logger=logger, editor=e)
    swash - WARNING - The following glyphs map to themselves: [19, 24, 80]
    True
    
    >>> s = _testingValues[2].binaryString()
    >>> fvb = Noncontextual.fromvalidatedbytes
    >>> d = {
    ...   'logger': logger,
    ...   'coverage': _testingValues[2].coverage,
    ...   'maskValue': _testingValues[2].maskValue}
    >>> obj = fvb(s, **d)
    swash.lookup_aat - DEBUG - Walker has 28 remaining bytes.
    swash.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
    >>> obj == _testingValues[2]
    True
    
    >>> fvb(s[:3], **d)
    swash.lookup_aat - DEBUG - Walker has 3 remaining bytes.
    swash.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 1 remaining bytes.
    swash.lookup_aat.binsearch.binsrch header - ERROR - Insufficient bytes.
    
    >>> fvb(s[:13], **d)
    swash.lookup_aat - DEBUG - Walker has 13 remaining bytes.
    swash.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 11 remaining bytes.
    swash.lookup_aat - ERROR - The data for the format 6 Lookup are missing or incomplete.
    
    >>> utilities.hexdump(_testingValues[1].binaryString())
           0 | 0008 000F 0002 0061  0062                |.......a.b      |
    
    >>> utilities.hexdump(_testingValues[2].binaryString())
           0 | 0006 0004 0003 0008  0001 0004 0016 0028 |...............(|
          10 | 0019 0013 0050 0063  FFFF FFFF           |.....P.c....    |
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(  # these are added to Lookup_OutGlyph, remember...
        map_maxcontextfunc = (lambda obj: 2),
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        maskValue = dict(
            attr_ignoreforbool = True,
            attr_label = "Mask value",
            attr_pprintfunc = _pprint_mask),
        
        coverage = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_label = "Coverage"))
    
    attrSorted = ('maskValue', 'coverage')
    
    kind = 4  # class constant

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.mort import coverage
    from fontio3.utilities import namer
    
    _cov = coverage.Coverage(kind=4)
    
    _testingValues = (
        Noncontextual(),
        Noncontextual({15: 97, 16: 98}, coverage=_cov, maskValue=0x08000000),
        
        Noncontextual(
          {22: 40, 25: 19, 80: 99},
          coverage = _cov,
          maskValue = 0x0004000000000000))
    
    del _cov

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
