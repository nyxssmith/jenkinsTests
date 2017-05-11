#
# convertertoken.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
ConverterTokens for converting among objects of different types.
"""

# -----------------------------------------------------------------------------

#
# Classes
#

class ConverterToken(object):
    """
    A ConverterToken is an object that contains a description of a
    converter and the method for performing the conversion.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, description, func, **kwArgs):
        """
        Initializes the object.
        
        >>> t = ConverterToken("test", lambda x:x)
        >>> t.description
        'test'
        >>> t.func(5)
        5
        """
        
        self.description = description
        self.func = func

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
    _test()

