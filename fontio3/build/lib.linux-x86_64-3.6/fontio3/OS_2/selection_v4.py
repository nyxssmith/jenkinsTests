#
# selection_v4.py
#
# Copyright © 2010-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the font selection flags in a Version 4 OS/2 table.
"""

# System imports
import collections

# Other imports
from fontio3.fontdata import maskmeta
from fontio3.OS_2 import selection_v0

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
    Use Typographic Metrics
    Has weight/width/slope names
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
      'regular', 'useTypoMetrics', 'wws', 'oblique')
    
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
            mask_showonlyiftrue = True),
        
        useTypoMetrics = dict(
            mask_isbool = True,
            mask_label = "Use Typographic Metrics",
            mask_rightmostbitindex = 7,
            mask_showonlyiftrue = True),
        
        wws = dict(
            mask_isbool = True,
            mask_label = "Has weight/width/slope names",
            mask_rightmostbitindex = 8,
            mask_showonlyiftrue = True),
        
        oblique = dict(
            mask_isbool = True,
            mask_label = "Oblique",
            mask_rightmostbitindex = 9,
            mask_showonlyiftrue = True))
    
    #
    # Class methods
    #
    
    @classmethod
    def fromversion0(cls, v0Obj, **kwArgs):
        """
        Returns a new version 4 Selection object from the specified
        version 0 Selection object. There is one keyword argument:
        
            deferRecalculation  If True (the default), the fields will be
                                copied but no recalculation is done. The client
                                should do a recalculation, in this case. If
                                False, a recalculated() object will be
                                returned; in this case, the client should be
                                sure to pass in the needed keyword arguments
                                (usually editor and unicodeSpan, and perhaps
                                base1252 and threshold as well).
        """
        
        r = cls(
          italic = v0Obj.italic,
          underscore = v0Obj.underscore,
          negative = v0Obj.negative,
          outlined = v0Obj.outlined,
          strikeout = v0Obj.strikeout,
          bold = v0Obj.bold,
          regular = v0Obj.regular)
        
        if kwArgs.get('deferRecalculation', True):
            return r
        
        return r.recalculated(**kwArgs)
    
    #
    # Public methods
    #
    
    def asVersion0(self, **kwArgs):
        """
        Returns a version 0 Selection object from the data in self. There
        is one keyword argument:
        
            deferRecalculation  If True (the default), the fields will be
                                copied but no recalculation is done. The client
                                should do a recalculation, in this case. If
                                False, a recalculated() object will be
                                returned; in this case, the client should be
                                sure to pass in the needed keyword arguments
                                (usually editor and unicodeSpan, and perhaps
                                base1252 and threshold as well).
        """
        
        r = selection_v0.Selection(
          italic = self.italic,
          underscore = self.underscore,
          negative = self.negative,
          outlined = self.outlined,
          strikeout = self.strikeout,
          bold = self.bold,
          regular = self.regular)
        
        if kwArgs.get('deferRecalculation', True):
            return r
        
        return r.recalculated(**kwArgs)

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
