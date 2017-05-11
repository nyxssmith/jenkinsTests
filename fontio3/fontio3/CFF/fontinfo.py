#
# fontinfo.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF font non-glyph information.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import deferreddictmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FontInfo(object, metaclass=deferreddictmeta.FontDataMetaclass):
    """
    Objects containing CFF Font information and metadata. This is an
    abstraction of various properties scattered about the CFF table, and
    does not strictly follow the CFF data structures.
    """
    
    deferredDictSpec = dict(
        item_strusesrepr = False)
        
    attrSpec = dict(
        fontname = dict(
          attr_label = "Font Name",
          attr_initfunc = lambda: "NoName",
          ),
        isCID = dict(
          attr_label = "Font is CID-keyed",
          attr_initfunc = lambda: False,
          ),
        )
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

