#
# featureinfo_context.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'Zapf' FeatureInfo contexts.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Context(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing the context specified in a 'Zapf' table's FeatureInfo
    object. These are masklike 16-bit values.
    
    >>> _testingValues[0].pprint(label="Glyph context")
    Glyph context: None
    
    >>> _testingValues[1].pprint(label="Glyph context")
    Glyph context: line-initial, word-initial
    
    >>> utilities.hexdump(_testingValues[1].binaryString())
           0 | 0009                                     |..              |
    
    >>> _testingValues[1] == Context.frombytes(_testingValues[1].binaryString())
    True
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        combinedstringfunc = (lambda sv: (', '.join(sv) if sv else "None")))
    
    maskSorted = (
      'lineInitial', 'lineMedial', 'lineFinal', 'wordInitial', 'wordMedial',
      'wordFinal', 'autoFracNumerator', 'autoFracDenominator')
    
    maskSpec = dict(
        lineInitial = dict(
            mask_isbool = True,
            mask_label = "line-initial",
            mask_rightmostbitindex = 0),
        
        lineMedial = dict(
            mask_isbool = True,
            mask_label = "line-medial",
            mask_rightmostbitindex = 1),
        
        lineFinal = dict(
            mask_isbool = True,
            mask_label = "line-final",
            mask_rightmostbitindex = 2),
        
        wordInitial = dict(
            mask_isbool = True,
            mask_label = "word-initial",
            mask_rightmostbitindex = 3),
        
        wordMedial = dict(
            mask_isbool = True,
            mask_label = "word-medial",
            mask_rightmostbitindex = 4),
        
        wordFinal = dict(
            mask_isbool = True,
            mask_label = "word-final",
            mask_rightmostbitindex = 5),
        
        autoFracNumerator = dict(
            mask_isbool = True,
            mask_label = "auto-fraction numerator",
            mask_rightmostbitindex = 6),
        
        autoFracDenominator = dict(
            mask_isbool = True,
            mask_label = "auto-fraction denominator",
            mask_rightmostbitindex = 7))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Context.fromnumber(0),
        Context.fromnumber(0x0009))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
