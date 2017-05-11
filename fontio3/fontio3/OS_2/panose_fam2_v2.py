#
# panose_fam2_v2.py
#
# Copyright © 2004-2014, 2016, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for representations of PANOSE data for OS/2 tables version 2 and
up, specifically for family 2 (Latin Text).
"""

# Other imports
from fontio3.fontdata import maskmeta
from fontio3.utilities import convertertoken
from fontio3.utilities import walker

# -----------------------------------------------------------------------------

#
# Private functions
#

def _asV0(obj, **kwArgs):
    """
    Convert obj to v0 Panose_fam2
    
    >>> p2 = Panose_fam2.fromnumber(0x02010203040506070801)
    >>> p2.stroke
    'Gradual/Vertical'
    >>> _asV0(p2).stroke
    'Gradual/Vertical'
    """
    
    from fontio3.OS_2 import panose
    
    bs = obj.binaryString()
    svmap = {0:0, 1:1, 2:1, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:8}
    sv = bs[5] # re-map stroke variation to new value
    svn = svmap.get(sv, 0)
    bn = bytes(bs[0:5] + bytes([svn]) + bs[6:])
    w = walker.StringWalker(bn)
    return panose.Panose(w, os2panver=0)

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

class Panose_fam2(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing PANOSE specifications.
    
    >>> Panose_fam2.fromnumber(0x02030205020303030405).pprint()
    Family Type: Latin Text
    Serif Type: Obtuse Cove
    Weight: Very Light
    Proportion: Extended
    Contrast: None
    Stroke Variation: Gradual/Diagonal
    Arm Style: Straight Arms/Wedge
    Letterform: Normal/Weighted
    Midline: Standard/Serifed
    x-Height: Ducking/Small
    
    # Note, this no longer results in a UserWarning. Use .fromvalidatednumber instead.
    >>> Panose_fam2.fromnumber(0xFF000000000000000000).pprint()
    Family Type: Latin Text
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
    >>> l = utilities.makeDoctestLogger("Panose_fam2")
    >>> Panose_fam2.fromvalidatednumber(0x02FF0101010101AB0101, logger=l).pprint()
    Panose_fam2.PANOSE.form - ERROR - Value 171 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam2.PANOSE.serif - ERROR - Value 255 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Family Type: Latin Text
    Serif Type: Any
    Weight: No Fit
    Proportion: No Fit
    Contrast: No Fit
    Stroke Variation: No Fit
    Arm Style: No Fit
    Letterform: Any
    Midline: No Fit
    x-Height: No Fit
    """
    
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
            mask_constantvalue = 2,
            mask_label = "Family Type: Latin Text",
            mask_rightmostbitindex = 72),
        
        serif = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Cove",
              "Obtuse Cove",
              "Square Cove",
              "Obtuse Square Cove",
              "Square",
              "Thin",
              "Oval",
              "Exaggerated",
              "Triangle",
              "Normal Sans",
              "Obtuse Sans",
              "Perpendicular Sans",
              "Flared",
              "Rounded"),
            mask_isenum = True,
            mask_label = "Serif Type",
            mask_rightmostbitindex = 64,
            mask_validatecode_badenumvalue = "E2109"),
        
        weight = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Very Light",
              "Light",
              "Thin",
              "Book",
              "Medium",
              "Demi",
              "Bold",
              "Heavy",
              "Black",
              "Extra Black"),
            mask_isenum = True,
            mask_label = "Weight",
            mask_rightmostbitindex = 56,
            mask_validatecode_badenumvalue = "E2111"),
        
        proportion = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Old Style",
              "Modern",
              "Even Width",
              "Extended",
              "Condensed",
              "Very Extended",
              "Very Condensed",
              "Monospaced"),
            mask_isenum = True,
            mask_label = "Proportion",
            mask_rightmostbitindex = 48,
            mask_validatecode_badenumvalue = "E2108"),
        
        contrast = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "None",
              "Very Low",
              "Low",
              "Medium Low",
              "Medium",
              "Medium High",
              "High",
              "Very High"),
            mask_isenum = True,
            mask_label = "Contrast",
            mask_rightmostbitindex = 40,
            mask_validatecode_badenumvalue = "E2104"),
        
        stroke = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "No Variation",
              "Gradual/Diagonal",
              "Gradual/Transitional",
              "Gradual/Vertical",
              "Gradual/Horizontal",
              "Rapid/Vertical",
              "Rapid/Horizontal",
              "Instant/Vertical",
              "Instant/Horizontal"),
            mask_isenum = True,
            mask_label = "Stroke Variation",
            mask_rightmostbitindex = 32,
            mask_validatecode_badenumvalue = "E2110"),
        
        arm = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Straight Arms/Horizontal",
              "Straight Arms/Wedge",
              "Straight Arms/Vertical",
              "Straight Arms/Single Serif",
              "Straight Arms/Double Serif",
              "Non-straight/Horizontal",
              "Non-straight/Wedge",
              "Non-straight/Vertical",
              "Non-straight/Single Serif",
              "Non-straight/Double Serif"),
            mask_isenum = True,
            mask_label = "Arm Style",
            mask_rightmostbitindex = 24,
            mask_validatecode_badenumvalue = "E2103"),
        
        form = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Normal/Contact",
              "Normal/Weighted",
              "Normal/Boxed",
              "Normal/Flattened",
              "Normal/Rounded",
              "Normal/Off Center",
              "Normal/Square",
              "Oblique/Contact",
              "Oblique/Weighted",
              "Oblique/Boxed",
              "Oblique/Flattened",
              "Oblique/Rounded",
              "Oblique/Off Center",
              "Oblique/Square"),
            mask_isenum = True,
            mask_label = "Letterform",
            mask_rightmostbitindex = 16,
            mask_validatecode_badenumvalue = "E2106"),
        
        midline = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Standard/Trimmed",
              "Standard/Pointed",
              "Standard/Serifed",
              "High/Trimmed",
              "High/Pointed",
              "High/Serifed",
              "Constant/Trimmed",
              "Constant/Pointed",
              "Constant/Serifed",
              "Low/Trimmed",
              "Low/Pointed",
              "Low/Serifed"),
            mask_isenum = True,
            mask_label = "Midline",
            mask_rightmostbitindex = 8,
            mask_validatecode_badenumvalue = "E2107"),
        
        xHeight = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Constant/Small",
              "Constant/Standard",
              "Constant/Large",
              "Ducking/Small",
              "Ducking/Standard",
              "Ducking/Large"),
            mask_isenum = True,
            mask_label = "x-Height",
            mask_rightmostbitindex = 0,
            mask_validatecode_badenumvalue = "E2112"))

    def converted(self, **kwArgs):
        """
        Implementation of protocol 'converted' method.
        """
        if kwArgs.get('returnTokens', False):
            CT = convertertoken.ConverterToken
            return [CT('To Panose for OS/2 v1 or older', _asV0)]
            
        ctk = kwArgs.get('useToken', None)
        if ctk:
            return ctk.func(self)


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

