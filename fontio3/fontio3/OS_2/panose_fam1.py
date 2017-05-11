#
# panose_fam1.py
#
# Copyright © 2004-2014, 2016, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for representations of PANOSE data for OS/2 tables family 1 (No Fit).
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate PANOSE value because the Editor and/or "
          "Cmap are missing or empty."))
        
        return False
    
    symMap = editor.cmap.getSymbolMap()
    
    if obj.binaryString() == (b'\x00' * 10):
        logger.warning((
          'W2105',
          (),
          "PANOSE values are all zero; font mapping may not work."))
    
    if symMap:
        logger.error((
          'E2139',
          (),
          "Symbol font must have PANOSE family of 'Pictorial'"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Panose_fam1(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing PANOSE specifications.
    
    >>> Panose_fam1().pprint()
    Family Type: No Fit
    Serif Type: Any
    Weight: Any
    Proportion: Any
    Contrast: Any
    Stroke Variation: Any
    Arm Style: Any
    Letterform: Any
    Midline: Any
    x-Height: Any
    
    # Note, this no longer results in a UserWarning. Use .fromvalidatednumber() instead.
    >>> Panose_fam1.fromnumber(0xFF000000000000000000).pprint()
    Family Type: No Fit
    Serif Type: Any
    Weight: Any
    Proportion: Any
    Contrast: Any
    Stroke Variation: Any
    Arm Style: Any
    Letterform: Any
    Midline: Any
    x-Height: Any
    
    >>> from fontio3 import utilities
    >>> l = utilities.makeDoctestLogger("Panose_fam1")
    >>> Panose_fam1.fromvalidatednumber(0x01FF0102030405060708, logger=l).pprint()
    Panose_fam1.PANOSE.arm - ERROR - Value 5 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.contrast - ERROR - Value 3 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.form - ERROR - Value 6 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.midline - ERROR - Value 7 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.proportion - ERROR - Value 2 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.serif - ERROR - Value 255 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.stroke - ERROR - Value 4 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.xHeight - ERROR - Value 8 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Family Type: No Fit
    Serif Type: Any
    Weight: No Fit
    Proportion: Any
    Contrast: Any
    Stroke Variation: Any
    Arm Style: Any
    Letterform: Any
    Midline: Any
    x-Height: Any
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 10
    
    maskControls = dict(
        loggername = "PANOSE",
        validatefunc_partial = _validate)
    
    maskSorted = (
      'family',
      'serif',
      'weight',
      'proportion',
      'contrast',
      'stroke',
      'arm',
      'form',
      'midline',
      'xHeight')
    
    maskSpec = dict(
        family = dict(
            mask_bitcount = 8,
            mask_constantvalue = 1,
            mask_label = "Family Type: No Fit",
            mask_rightmostbitindex = 72),
        
        serif = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Serif Type",
            mask_rightmostbitindex = 64,
            mask_validatecode_badenumvalue = "E2109"),
        
        weight = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Weight",
            mask_rightmostbitindex = 56,
            mask_validatecode_badenumvalue = "E2111"),
        
        proportion = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Proportion",
            mask_rightmostbitindex = 48,
            mask_validatecode_badenumvalue = "E2108"),
        
        contrast = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Contrast",
            mask_rightmostbitindex = 40,
            mask_validatecode_badenumvalue = "E2104"),
        
        stroke = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Stroke Variation",
            mask_rightmostbitindex = 32,
            mask_validatecode_badenumvalue = "E2110"),
        
        arm = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Arm Style",
            mask_rightmostbitindex = 24,
            mask_validatecode_badenumvalue = "E2103"),
        
        form = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Letterform",
            mask_rightmostbitindex = 16,
            mask_validatecode_badenumvalue = "E2106"),
        
        midline = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "Midline",
            mask_rightmostbitindex = 8,
            mask_validatecode_badenumvalue = "E2107"),
        
        xHeight = dict(
            mask_bitcount = 8,
            mask_enumstrings = ("Any", "No Fit"),
            mask_isenum = True,
            mask_label = "x-Height",
            mask_rightmostbitindex = 0,
            mask_validatecode_badenumvalue = "E2112"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    import warnings
    warnings.simplefilter('error')
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
