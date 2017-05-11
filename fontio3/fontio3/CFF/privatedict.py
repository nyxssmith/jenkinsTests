#
# privatedict.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF font Private DICT information.
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

class PrivateDict(object, metaclass=deferreddictmeta.FontDataMetaclass):
    """
    Objects containing CFF Private DICT data. Since the contents can
    vary per-font, it is set up as a deferreddict to allow simple
    building and access.
    
    There is one attribute, 'index', which is used to track the multiple
    Private DICTs that can be present in CID fonts.
    """
    
    deferredDictSpec = dict(
        item_strusesrepr = False)
        
    attrSpec = dict(
        index = dict(
          attr_initfunc=lambda:0))
    
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

