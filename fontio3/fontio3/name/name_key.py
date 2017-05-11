#
# name_key.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for keys of a Name object.
"""

# Other imports
from fontio3.fontdata import keymeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class Name_Key(tuple, metaclass=keymeta.FontDataMetaclass):
    """
    """
    
    #
    # Class definition variables
    #
    
    itemSpec = (
        dict(
            item_validatefunc_partial = valassist.isFormat_H),
        
        dict(
            item_validatefunc_partial = valassist.isFormat_H),
        
        dict(
            item_strusesrepr = True),
        
        dict(
            item_renumbernamesdirect = True))

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
