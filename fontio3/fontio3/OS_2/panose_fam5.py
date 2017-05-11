#
# panose_fam5.py
#
# Copyright © 2004-2014, 2016, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for representations of PANOSE data for OS/2 tables family 5 (Latin Pictorial).
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
    
    if not symMap:
        logger.error((
          'E2140',
          (),
          "Non-symbol font must not have PANOSE family of 'Pictorial'"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Panose_fam5(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing PANOSE specifications.
    
    >>> Panose_fam5.fromnumber(0x05020102010303030405).pprint()
    Family Type: Latin Pictorial
    Kind: Montages
    Weight: No Fit
    Spacing: Proportional Spaced
    Aspect Ratio & Contrast: No Fit
    Aspect ratio of character 94: Exceptionally Wide
    Aspect ratio of character 119: Exceptionally Wide
    Aspect ratio of character 157: Exceptionally Wide
    Aspect ratio of character 163: Super Wide
    Aspect ratio of character 211: Very Wide
    
    # Note: this no longer results in a UserWarning. Use .fromvalidatednumber instead.
    >>> p = Panose_fam5.fromnumber(0x05000000000000000000).pprint()
    Family Type: Latin Pictorial
    Kind: Any
    Weight: No Fit
    Spacing: Any
    Aspect Ratio & Contrast: No Fit
    Aspect ratio of character 94: Any
    Aspect ratio of character 119: Any
    Aspect ratio of character 157: Any
    Aspect ratio of character 163: Any
    Aspect ratio of character 211: Any
    
    >>> from fontio3 import utilities
    >>> l = utilities.makeDoctestLogger("Panose_fam5")
    >>> Panose_fam5.fromvalidatednumber(0x05000000000000000000, logger=l)
    Panose_fam5.PANOSE.aspectRatioAndContrast - ERROR - Field 'aspectRatioAndContrast' should have a constant value of 1, but instead has a value of 0
    Panose_fam5.PANOSE.weight - ERROR - Field 'weight' should have a constant value of 1, but instead has a value of 0
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
      'kind',
      'weight',
      'spacing',
      'aspectRatioAndContrast',
      'char94AspectRatio',
      'char119AspectRatio',
      'char157AspectRatio',
      'char163AspectRatio',
      'char211AspectRatio')
    
    maskSpec = dict(
        family = dict(
            mask_bitcount = 8,
            mask_constantvalue = 5,
            mask_label = "Family Type: Latin Pictorial",
            mask_rightmostbitindex = 72),
        
        kind = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "Montages",
              "Pictures",
              "Shapes",
              "Scientific",
              "Music",
              "Expert",
              "Patterns",
              "Borders",
              "Icons",
              "Logos",
              "Industry-specific"),
            mask_isenum = True,
            mask_label = "Kind",
            mask_rightmostbitindex = 64),
        
        weight = dict(
            mask_bitcount = 8,
            mask_constantvalue = 1,
            mask_label = "Weight: No Fit",
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
        
        aspectRatioAndContrast = dict(
            mask_bitcount = 8,
            mask_constantvalue = 1,
            mask_label = "Aspect Ratio & Contrast: No Fit",
            mask_rightmostbitindex = 40),
        
        char94AspectRatio = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "No Width",
              "Exceptionally Wide",
              "Super Wide",
              "Very Wide",
              "Wide",
              "Normal",
              "Narrow",
              "Very Narrow"),
            mask_isenum = True,
            mask_label = "Aspect ratio of character 94",
            mask_rightmostbitindex = 32),
        
        char119AspectRatio = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "No Width",
              "Exceptionally Wide",
              "Super Wide",
              "Very Wide",
              "Wide",
              "Normal",
              "Narrow",
              "Very Narrow"),
            mask_isenum = True,
            mask_label = "Aspect ratio of character 119",
            mask_rightmostbitindex = 24),
        
        char157AspectRatio = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "No Width",
              "Exceptionally Wide",
              "Super Wide",
              "Very Wide",
              "Wide",
              "Normal",
              "Narrow",
              "Very Narrow"),
            mask_isenum = True,
            mask_label = "Aspect ratio of character 157",
            mask_rightmostbitindex = 16),
        
        char163AspectRatio = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "No Width",
              "Exceptionally Wide",
              "Super Wide",
              "Very Wide",
              "Wide",
              "Normal",
              "Narrow",
              "Very Narrow"),
            mask_isenum = True,
            mask_label = "Aspect ratio of character 163",
            mask_rightmostbitindex = 8),
        
        char211AspectRatio = dict(
            mask_bitcount = 8,
            mask_enumstrings = (
              "Any",
              "No Fit",
              "No Width",
              "Exceptionally Wide",
              "Super Wide",
              "Very Wide",
              "Wide",
              "Normal",
              "Narrow",
              "Very Narrow"),
            mask_isenum = True,
            mask_label = "Aspect ratio of character 211",
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
