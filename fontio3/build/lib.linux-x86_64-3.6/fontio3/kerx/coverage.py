#
# coverage.py
#
# Copyright © 2011-2012, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for coverage fields for 'kerx' tables.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Coverage(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing coverage flags for 'kerx' tables. These are masks with
    three single-bit fields:
    
        crossStream     If True, the subtable's distances are used to express
                        cross-stream shifts (that is, vertical shifts for
                        horizontal text, and horizontal shifts for vertical
                        text). Default is False.
        
        variation       If True, the subtable includes variation kerning tuple
                        values. This is only used for Apple TrueType variation
                        fonts, and is very rare. Default is False.
        
        vertical        If True, this subtable is intended to be used for
                        vertical text. Default is False.
        
        reverse         If True, the glyph array should be processed in
                        last-to-first order. If False, processing should be
                        first-to-last. Default is False.
    
    Note that the subtable format is not included here; the Kerx object deals
    with that.
    
    >>> _testingValues[0].pprint()
    Horizontal
    With-stream
    No variation kerning
    Process forward
    
    >>> print(_testingValues[1])
    Vertical, With-stream, Variation kerning, Process reverse
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 3
    
    maskSpec = dict(
        vertical = dict(
            mask_boolstrings = ("Horizontal", "Vertical"),
            mask_isbool = True,
            mask_label = "Vertical text",
            mask_rightmostbitindex = 23),
        
        crossStream = dict(
            mask_boolstrings = ("With-stream", "Cross-stream"),
            mask_isbool = True,
            mask_label = "Cross-stream",
            mask_rightmostbitindex = 22),
        
        variation = dict(
            mask_boolstrings = ("No variation kerning", "Variation kerning"),
            mask_isbool = True,
            mask_label = "Variation kerning is present",
            mask_rightmostbitindex = 21,
            mask_showonlyiftrue = True),
        
        reverse = dict(
            mask_boolstrings = ("Process forward", "Process reverse"),
            mask_isbool = True,
            mask_label = "Processing direction",
            mask_rightmostbitindex = 20,
            mask_showonlyiftrue = True))
    
    maskSorted = ('vertical', 'crossStream', 'variation', 'reverse')
    
    #
    # Class methods
    #
    
    @classmethod
    def fromkern_coverage(cls, kernCoverage, **kwArgs):
        """
        Creates and returns a new Coverage object based on the data in the
        'kern' coverage object passed in (which may be format 0 or format 1).
        
        >>> tv0, tv1 = _kc()
        >>> Coverage.fromkern_coverage(tv0[1]).pprint()
        Horizontal
        Cross-stream
        No variation kerning
        Process forward
        
        >>> Coverage.fromkern_coverage(tv1[1]).pprint()
        Vertical
        With-stream
        Variation kerning
        Process forward
        """
        
        if kernCoverage.format == 0:
            r = cls(
              vertical = kernCoverage.vertical,
              crossStream = kernCoverage.crossStream,
              variation = False,
              reverse = False)
        
        elif kernCoverage.format == 1:
            r = cls(
              vertical = kernCoverage.vertical,
              crossStream = kernCoverage.crossStream,
              variation = kernCoverage.variation,
              reverse = False)
        
        else:
            raise ValueError("Unknown Coverage type!")
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _kc():
        from fontio3.kern import coverage_v0, coverage_v1
        
        return (coverage_v0._testingValues, coverage_v1._testingValues)
    
    _testingValues = (
        Coverage(),
        Coverage(vertical=True, variation=True, reverse=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
