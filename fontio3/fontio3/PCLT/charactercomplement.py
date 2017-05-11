#
# charactercomplement.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for character complement information, used in PCLT tables.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class CharacterComplement(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing PCLT character complements. These are masks with the
    following fields:
    
        unicodeOrder
        codePageExtensions
        postscriptExtensions
        macintoshExtensions
        pclExtensions
        accentExtensions
        desktopPublishingExtensions
        latin5Extensions
        latin2Extensions
        latin1Extensions
        ascii
    
    >>> obj = _testingValues[1]
    >>> _testingValues[1].pprint(annotateBits=True)
    ASCII (supports several standard interpretations) (bit 31)
    Unicode order (bit 0)
    
    >>> utilities.hexdump(_testingValues[1].binaryString())
           0 | FFFF FFFF 7FFF FFFE                      |........        |
    
    >>> _testingValues[2].pprint()
    ASCII (supports several standard interpretations)
    Desktop Publishing extensions
    Latin 1 extensions
    Macintosh extensions
    Unicode order
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> fvn = CharacterComplement.fromvalidatednumber
    >>> obj = fvn(0xEFFFFFFF7FFFFFFE, logger=logger)
    val.char complement - WARNING - All reserved bits should be set to 1, but some are 0.
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 8
    
    maskControls = dict(
        fillmissingwithone = True,
        loggername = "char complement")
    
    maskSpec = dict(
        unicodeOrder = dict(
            mask_isantibool = True,
            mask_label = "Unicode order",
            mask_rightmostbitindex = 0,
            mask_showonlyiftrue = True),
        
        codePageExtensions = dict(
            mask_isantibool = True,
            mask_label = "Code Page extensions",
            mask_rightmostbitindex = 22,
            mask_showonlyiftrue = True),
        
        postscriptExtensions = dict(
            mask_isantibool = True,
            mask_label = "PostScript extensions",
            mask_rightmostbitindex = 23,
            mask_showonlyiftrue = True),
        
        macintoshExtensions = dict(
            mask_isantibool = True,
            mask_label = "Macintosh extensions",
            mask_rightmostbitindex = 24,
            mask_showonlyiftrue = True),
        
        pclExtensions = dict(
            mask_isantibool = True,
            mask_label = "PCL extensions",
            mask_rightmostbitindex = 25,
            mask_showonlyiftrue = True),
        
        accentExtensions = dict(
            mask_isantibool = True,
            mask_label = "Accent extensions (East and West Europe)",
            mask_rightmostbitindex = 26,
            mask_showonlyiftrue = True),
        
        desktopPublishingExtensions = dict(
            mask_isantibool = True,
            mask_label = "Desktop Publishing extensions",
            mask_rightmostbitindex = 27,
            mask_showonlyiftrue = True),
        
        latin5Extensions = dict(
            mask_isantibool = True,
            mask_label = "Latin 5 extensions",
            mask_rightmostbitindex = 28,
            mask_showonlyiftrue = True),
        
        latin2Extensions = dict(
            mask_isantibool = True,
            mask_label = "Latin 2 extensions",
            mask_rightmostbitindex = 29,
            mask_showonlyiftrue = True),
        
        latin1Extensions = dict(
            mask_isantibool = True,
            mask_label = "Latin 1 extensions",
            mask_rightmostbitindex = 30,
            mask_showonlyiftrue = True),
        
        ascii = dict(
            mask_isantibool = True,
            mask_label = "ASCII (supports several standard interpretations)",
            mask_rightmostbitindex = 31,
            mask_showonlyiftrue = True))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        CharacterComplement(),
        
        CharacterComplement(
          ascii = True,
          unicodeOrder = True),
        
        CharacterComplement(
          ascii = True,
          desktopPublishingExtensions = True,
          latin1Extensions = True,
          macintoshExtensions = True,
          unicodeOrder = True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
