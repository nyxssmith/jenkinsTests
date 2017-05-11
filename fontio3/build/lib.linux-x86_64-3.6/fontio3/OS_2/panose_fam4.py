#
# panose_fam4.py
#
# Copyright © 2004-2014, 2016, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for representations of PANOSE data for OS/2 tables family 4 (Latin Decorative).
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

class Panose_fam4(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing PANOSE specifications.
    
    >>> Panose_fam4.fromnumber(0x04030202050303030405).pprint()
    Family Type: Latin Decorative
    Class: Non-standard Topology
    Weight: Very Light
    Aspect: Super Condensed
    Contrast: Medium Low
    Serif Variant: Obtuse Cove
    Treatment: White / No Fill
    Lining: Inline
    Topology: Multiple Segment
    Range of Characters: Small Caps

    # Note: this no longer results in a UserWarning. Use .fromvalidatednumber instead.
    >>> Panose_fam4.fromnumber(0xFF000000000000000000).pprint()
    Family Type: Latin Decorative
    Class: Any
    Weight: Any
    Aspect: Any
    Contrast: Any
    Serif Variant: Any
    Treatment: Any
    Lining: Any
    Topology: Any
    Range of Characters: Any

    >>> from fontio3 import utilities
    >>> l = utilities.makeDoctestLogger("Panose_fam1")
    >>> Panose_fam4.fromvalidatednumber(0x04FF0102030405060708, logger=l).pprint()
    Panose_fam1.PANOSE.class_ - ERROR - Value 255 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Panose_fam1.PANOSE.rangeOfCharacters - ERROR - Value 8 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    Family Type: Latin Decorative
    Class: Any
    Weight: No Fit
    Aspect: Super Condensed
    Contrast: Very Low
    Serif Variant: Square Cove
    Treatment: Complex Fill
    Lining: Shadow
    Topology: Diverse Arms
    Range of Characters: Any
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
      'class_',
      'weight',
      'aspect',
      'contrast',
      'serifVariant',
      'treatment',
      'lining',
      'topology',
      'rangeOfCharacters')
    
    maskSpec = dict(
        family = dict(
            mask_bitcount = 8,
            mask_constantvalue = 4,
            mask_label = "Family Type: Latin Decorative",
            mask_rightmostbitindex = 72),
        
        class_ = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Derivative",
              "Non-standard Topology",
              "Non-standard Elements",
              "Non-standard Aspect",
              "Initials",
              "Cartoon",
              "Picture Stems",
              "Ornamented",
              "Text and Background",
              "Collage",
              "Montage"),
            mask_isenum = True,
            mask_label = "Class",
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
              "Extra Black"),
            mask_isenum = True,
            mask_label = "Weight",
            mask_rightmostbitindex = 56),
        
        aspect = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Super Condensed",
              "Very Condensed",
              "Condensed",
              "Normal",
              "Extended",
              "Very Extended",
              "Super Extended",
              "Monospaced"),
            mask_isenum = True,
            mask_label = "Aspect",
            mask_rightmostbitindex = 48),
        
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
              "Very High",
              "Horizontal Low",
              "Horizontal Medium",
              "Horizontal High",
              "Broken"),
            mask_isenum = True,
            mask_label = "Contrast",
            mask_rightmostbitindex = 40),
        
        serifVariant = dict(
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
              "Rounded",
              "Script"),
            mask_isenum = True,
            mask_label = "Serif Variant",
            mask_rightmostbitindex = 32),
        
        treatment = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "None - Standard Solid Fill",
              "White / No Fill",
              "Patterned Fill",
              "Complex Fill",
              "Shaped Fill",
              "Drawn / Distressed"),
            mask_isenum = True,
            mask_label = "Treatment",
            mask_rightmostbitindex = 24),
        
        lining = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "None",
              "Inline",
              "Outline",
              "Engraved (Multiple Lines)",
              "Shadow",
              "Relief",
              "Backdrop"),
            mask_isenum = True,
            mask_label = "Lining",
            mask_rightmostbitindex = 16),
        
        topology = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Standard",
              "Square",
              "Multiple Segment",
              "Deco (E,M,S) Waco midlines",
              "Uneven Weighting",
              "Diverse Arms",
              "Diverse Forms",
              "Lombardic Forms",
              "Upper Case in Lower Case",
              "Implied Topology",
              "Horseshoe E and A",
              "Cursive",
              "Blackletter",
              "Swash Variance"),
            mask_isenum = True,
            mask_label = "Topology",
            mask_rightmostbitindex = 8),
        
        rangeOfCharacters = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Extended Collection",
              "Literals",
              "No Lower Case",
              "Small Caps"),
            mask_isenum = True,
            mask_label = "Range of Characters",
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
