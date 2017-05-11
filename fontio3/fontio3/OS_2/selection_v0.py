#
# selection_v0.py
#
# Copyright © 2010-2012, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the font selection flags in a Version 0 OS/2 table.
"""

# System imports
import collections

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'name')):
        logger.error((
          'V0553',
          (),
          "Unable to validate fsSelection because the Editor and/or "
          "Name object are missing or empty."))
        
        return False
    
    d = editor.name.subFamilyNameToBits()
    r = True
    
    if (
      obj.italic != d['italic'] or
      obj.bold != d['bold'] or
      obj.underscore != d['underscore'] or
      obj.outlined != d['outline'] or
      obj.strikeout != d['strikeout'] or
      obj.negative != d['negative']):
      
        logger.error((
          "E2100",
          (),
          "The fsSelection doesn't match the subfamily 'name' entry"))
        
        r = False
    
    if obj.regular and obj.bold:
        logger.error((
          'E2114',
          (),
          "The fsSelection specifies both regular and bold"))
        
        r = False
    
    if obj.regular and obj.italic:
        logger.error((
          'E2115',
          (),
          "The fsSelection specifies both regular and italic"))
        
        r = False
    
    return r

def _validate_bold(flag, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate fsSelection bold bit because Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if flag != editor.head.macStyle.bold:
        logger.error((
          'E2143',
          (),
          "Bold bit in fsSelection doesn't match head macStyle"))
        
        return False
    
    return True

def _validate_italic(flag, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate fsSelection bold bit because Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if flag != editor.head.macStyle.italic:
        logger.error((
          'E2144',
          (),
          "Italic bit in fsSelection doesn't match head macStyle"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Selection(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing fsSelection values in an OS/2 table.
    
    >>> Selection.fromnumber(0).pprint()
    >>> Selection.fromnumber(0x01C0).pprint()
    Regular
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        loggername = "fsselection",
        validate_notsettozero_iserror = True,
        validatecode_notsettozero = "E2101",
        validatefunc_partial = _validate)
    
    maskSorted = (
      'italic', 'underscore', 'negative', 'outlined', 'strikeout', 'bold',
      'regular')
    
    maskSpec = dict(
        italic = dict(
            mask_isbool = True,
            mask_label = "Italic",
            mask_rightmostbitindex = 0,
            mask_showonlyiftrue = True,
            mask_validatefunc = _validate_italic),
        
        underscore = dict(
            mask_isbool = True,
            mask_label = "Underscore",
            mask_rightmostbitindex = 1,
            mask_showonlyiftrue = True),
        
        negative = dict(
            mask_isbool = True,
            mask_label = "Negative",
            mask_rightmostbitindex = 2,
            mask_showonlyiftrue = True),
        
        outlined = dict(
            mask_isbool = True,
            mask_label = "Outlined",
            mask_rightmostbitindex = 3,
            mask_showonlyiftrue = True),
        
        strikeout = dict(
            mask_isbool = True,
            mask_label = "Strikeout",
            mask_rightmostbitindex = 4,
            mask_showonlyiftrue = True),
        
        bold = dict(
            mask_isbool = True,
            mask_label = "Bold",
            mask_rightmostbitindex = 5,
            mask_showonlyiftrue = True,
            mask_validatefunc = _validate_bold),
        
        regular = dict(
            mask_isbool = True,
            mask_label = "Regular",
            mask_rightmostbitindex = 6,
            mask_showonlyiftrue = True))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
