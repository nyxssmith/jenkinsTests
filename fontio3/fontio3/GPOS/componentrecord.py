#
# componentrecord.py -- support for OpenType GPOS type 5 ComponentRecords
#
# Copyright © 2009-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType ComponentRecord objects (used in Mark-to-Ligature GPOS
lookups).
"""

# Other imports
from fontio3.GPOS import baserecord

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not any(obj):
        logger.warning((
          'V0344',
          (),
          "All the anchors in the ComponentRecord are empty, so the "
          "ComponentRecord has no effect and may be removed."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ComponentRecord(baserecord.BaseRecord):
    """
    Objects representing single component attachment records. These are
    structurally identical to BaseRecords, but are subclassed here in order to
    allow for correct labeling in the validating code.
    
    >>> _testingValues[0].pprint()
    Class 0:
      (no data)
    Class 1:
      x-coordinate: -40
      y-coordinate: 18
    Class 2:
      (no data)
    Class 3:
      x-coordinate: -40
      y-coordinate: 18
      Contour point index: 6
      Glyph index: 40
    
    >>> cr1 = _testingValues[0]
    >>> wTest = writer.LinkedWriter()
    >>> wTest.stakeCurrentWithValue("test stake")
    >>> cr1.buildBinary(wTest, posBase="test stake")
    >>> s = wTest.binaryString()
    >>> logger = utilities.makeDoctestLogger("componentrecord_test")
    >>> fvb = ComponentRecord.fromvalidatedbytes
    >>> obj = fvb(s, logger=logger, classCount=4, glyphIndex=40)
    componentrecord_test.componentrecord - DEBUG - Walker has 22 bytes remaining.
    componentrecord_test.componentrecord.[1].anchor_coord - DEBUG - Walker has 14 remaining bytes.
    componentrecord_test.componentrecord.[3].anchor_point - DEBUG - Walker has 8 remaining bytes.
    
    >>> logger = utilities.makeDoctestLogger("ivtest")
    >>> e = _fakeEditor()
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    ivtest.[3] - WARNING - Point 6 in glyph 40 has coordinates (950, 750), but the Anchor data in this object are (-40, 18).
    True
    
    >>> _testingValues[5].isValid(logger=logger, editor=e)
    ivtest - WARNING - All the anchors in the ComponentRecord are empty, so the ComponentRecord has no effect and may be removed.
    True
    """
    
    seqSpec = dict(
      seq_validatefunc_partial = _validate)
    
    _childLogName = "componentrecord"

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.GPOS import anchor_coord, anchor_device, anchor_point
    from fontio3.utilities import writer
    
    def _fakeEditor():
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(0x10000)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        return e
    
    ac = anchor_coord._testingValues
    ad = anchor_device._testingValues
    ap = anchor_point._testingValues
    
    _testingValues = (
        ComponentRecord([None, ac[0], None, ap[0]]), # point on glyph 40
        ComponentRecord([ad[0], None, None, ac[1]]),
        ComponentRecord([ac[2], ad[1], ac[3], ap[1]]), # point on glyph 99
        ComponentRecord([ad[2], ad[2], None, None]),
        ComponentRecord([ap[2], None, ap[3], ap[3]]), # points on glyph 16
        ComponentRecord([None, None, None, None]))
    
    del ac, ad, ap

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
