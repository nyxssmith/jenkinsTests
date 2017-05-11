#
# panose_fam3.py
#
# Copyright © 2004-2014, 2016, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for representations of PANOSE data for OS/2 tables family 3 (Latin Hand Written).
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

class Panose_fam3(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing PANOSE specifications.
    
    >>> Panose_fam3.fromnumber(0x03030202050303030405).pprint()
    Family Type: Latin Hand Written
    Tool Kind: Pressure Point
    Weight: Very Light
    Spacing: Proportional Spaced
    Aspect Ratio: Expanded
    Contrast: Very Low
    Topology: Roman Trailing
    Form: Upright / Some Wrapping
    Finials: None / Open loops
    X-Ascent: High

    # Note: this no longer results in a UserWarning. Use .fromvalidatednumber instead.
    >>> Panose_fam3.fromnumber(0xFF000000000000000000).pprint()
    Family Type: Latin Hand Written
    Tool Kind: Any
    Weight: Any
    Spacing: Any
    Aspect Ratio: Any
    Contrast: Any
    Topology: Any
    Form: Any
    Finials: Any
    X-Ascent: Any
    
    >>> from fontio3 import utilities
    >>> l = utilities.makeDoctestLogger("Panose_fam3")
    >>> Panose_fam3.fromvalidatednumber(0x03FF0102030405060708, logger=l).pprint()
    Panose_fam3.PANOSE.tool - ERROR - Value 255 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam3.PANOSE.xAscent - ERROR - Value 8 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Family Type: Latin Hand Written
    Tool Kind: Any
    Weight: No Fit
    Spacing: Proportional Spaced
    Aspect Ratio: Condensed
    Contrast: Low
    Topology: Cursive Disconnected
    Form: Oblique / No Wrapping
    Finials: Sharp / Open loops
    X-Ascent: Any
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
      'tool',
      'weight',
      'spacing',
      'aspectRatio',
      'contrast',
      'topology',
      'form',
      'finials',
      'xAscent')
    
    maskSpec = dict(
        family = dict(
            mask_bitcount = 8,
            mask_constantvalue = 3,
            mask_label = "Family Type: Latin Hand Written",
            mask_rightmostbitindex = 72),
        
        tool = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Flat Nib",
              "Pressure Point",
              "Engraved",
              "Ball (Round Cap)",
              "Brush",
              "Rough",
              "Felt Pen/Brush Tip",
              "Wild Brush - Drips a lot"),
            mask_isenum = True,
            mask_label = "Tool Kind",
            mask_rightmostbitindex = 64),
        
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
              "Extra Black (Nord)"),
            mask_isenum = True,
            mask_label = "Weight",
            mask_rightmostbitindex = 56),
        
        spacing = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Proportional Spaced",
              "Monospaced"),
            mask_isenum = True,
            mask_label = "Spacing",
            mask_rightmostbitindex = 48),
        
        aspectRatio = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Very Condensed",
              "Condensed",
              "Normal",
              "Expanded",
              "Very Expanded"),
            mask_isenum = True,
            mask_label = "Aspect Ratio",
            mask_rightmostbitindex = 40),
        
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
            mask_rightmostbitindex = 32),
        
        topology = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Roman Disconnected",
              "Roman Trailing",
              "Roman Connected",
              "Cursive Disconnected",
              "Cursive Trailing",
              "Cursive Connected",
              "Blackletter Disconnected",
              "Blackletter Trailing",
              "Blackletter Connected"),
            mask_isenum = True,
            mask_label = "Topology",
            mask_rightmostbitindex = 24),
        
        form = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Upright / No Wrapping",
              "Upright / Some Wrapping",
              "Upright / More Wrapping",
              "Upright / Extreme Wrapping",
              "Oblique / No Wrapping",
              "Oblique / Some Wrapping",
              "Oblique / More Wrapping",
              "Oblique / Extreme Wrapping",
              "Exaggerated / No Wrapping",
              "Exaggerated / Some Wrapping",
              "Exaggerated / More Wrapping",
              "Exaggerated / Extreme Wrapping"),
            mask_isenum = True,
            mask_label = "Form",
            mask_rightmostbitindex = 16),
        
        finials = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "None / No loops",
              "None / Closed loops",
              "None / Open loops",
              "Sharp / No loops",
              "Sharp / Closed loops",
              "Sharp / Open loops",
              "Tapered / No loops",
              "Tapered / Closed loops",
              "Tapered / Open loops",
              "Round / No loops",
              "Round / Closed loops",
              "Round / Open loops"),
            mask_isenum = True,
            mask_label = "Finials",
            mask_rightmostbitindex = 8),
        
        xAscent = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Very Low",
              "Low",
              "Medium",
              "High",
              "Very High"),
            mask_isenum = True,
            mask_label = "X-Ascent",
            mask_rightmostbitindex = 0))

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
