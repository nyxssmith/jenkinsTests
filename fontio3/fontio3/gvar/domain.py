#
# domain.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for domains, as used in the intermediate_tuple case.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Domain(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Simple collections of two attributes, edge1 and edge2, both of which are
    AxialCoordinates objects.
    """
    
    attrSpec = dict(
        edge1 = dict(
            attr_followsprotocol = True),
        
        edge2 = dict(
            attr_followsprotocol = True))

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

