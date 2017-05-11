#
# coverage.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for coverage values associated with 'mort' subtables.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if obj.always and obj.vertical:
        logger.warning((
          'V0698',
          (),
          "The Coverage has both the 'always' and 'vertical' bits set. "
          "The 'always' bit includes the vertical orientation, so the "
          "vertical bit is redundant here."))
    
    if obj.reverse and (obj.always or obj.vertical):
        logger.warning((
          'V0699',
          (),
          "The 'reverse' bit is set in addition to the 'always' and/or "
          "'vertical' bits. This is an unusual combination."))
    
    return True

def _validate_kind(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if obj not in {0, 1, 2, 4, 5}:
        logger.error((
          'V0697',
          (obj,),
          "The kind value %d is not a valid subtable kind."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Coverage(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing coverage values for 'mort' subtables. These are mask
    values with the following fields:
    
        always      A Boolean specifying whether this subtable should always be
                    processed, irrespective of horizontal/vertical orientation.
                    Default is False.
        
        kind        A numeric value determining the kind of subtable.
        
        reverse     A Boolean specifying whether this subtable should be
                    processed in reverse order (i.e. starting at the semantic
                    end of the run/line of text). Default is False.
        
        vertical    A Boolean specifying whether this subtable should only be
                    applied for vertical runs of text. Default is False.
    
    >>> _testingValues[1].pprint()
    Vertical text
    Subtable kind: 4
    
    >>> logger = utilities.makeDoctestLogger("coverage_test")
    >>> e = utilities.fakeEditor(0x10000)
    >>> d = {'logger': logger, 'editor': e}
    >>> Coverage(kind=7).isValid(**d)
    coverage_test.kind - ERROR - The kind value 7 is not a valid subtable kind.
    False
    
    >>> Coverage(always=True, vertical=True).isValid(**d)
    coverage_test - WARNING - The Coverage has both the 'always' and 'vertical' bits set. The 'always' bit includes the vertical orientation, so the vertical bit is redundant here.
    True
    
    >>> Coverage(reverse=True, vertical=True).isValid(**d)
    coverage_test - WARNING - The 'reverse' bit is set in addition to the 'always' and/or 'vertical' bits. This is an unusual combination.
    True
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        validatefunc_partial = _validate)
    
    maskSpec = dict(
        vertical = dict(
            mask_isbool = True,
            mask_label = "Vertical text",
            mask_rightmostbitindex = 15,
            mask_showonlyiftrue = True),
        
        reverse = dict(
            mask_isbool = True,
            mask_label = "Process reversed",
            mask_rightmostbitindex = 14,
            mask_showonlyiftrue = True),
        
        always = dict(
            mask_isbool = True,
            mask_label = "Process in both orientations",
            mask_rightmostbitindex = 13,
            mask_showonlyiftrue = True),
        
        kind = dict(
            mask_bitcount = 3,
            mask_label = "Subtable kind",
            mask_rightmostbitindex = 0,
            mask_validatefunc = _validate_kind))
    
    maskSorted = ('vertical', 'reverse', 'always', 'kind')

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Coverage(),
        Coverage(vertical=True, kind=4))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
