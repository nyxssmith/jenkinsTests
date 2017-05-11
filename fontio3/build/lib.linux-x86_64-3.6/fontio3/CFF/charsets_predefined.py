#
# charsets_predefined.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for predefined CFF Charsets.
"""

# System imports
import logging

# Other imports
from fontio3.CFF.cffutils import stdStrings
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Predefined(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing Predefined charsets.
    """
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        map_compactremovesfalses = True,
        item_pprintlabelpresort = True)
    
    
    #
    # Initialization and class methods
    #
    
    @classmethod
    def fromvalidatednumber(cls, n, **kwArgs):
        """
        Like fromwalker(), this method returns a new Predefined Charset.
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> obj = Predefined.fromvalidatednumber(0, logger=logger)
        test.predefined - INFO - ISOAdobe charset
        >>> obj[9]
        'parenleft'
        >>> obj = Predefined.fromvalidatednumber(1, logger=logger)
        test.predefined - INFO - Expert charset
        >>> obj[22]
        'sixoldstyle'
        >>> obj = Predefined.fromvalidatednumber(2, logger=logger)
        test.predefined - INFO - Expert Subset charset
        >>> obj[5]
        'parenrightsuperior'
        >>> obj = Predefined.fromvalidatednumber(99, logger=logger)
        test.predefined - ERROR - Unknown predefined charset designator 99
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('predefined')
        else:
            logger = logger.getChild('predefined')
        
        if n < 0 or n > 2:
            logger.error(('xxxxx', (n,), "Unknown predefined charset designator %d"))
            return cls({})

        if n == 0:
            logger.info(('xxxxx', (), "ISOAdobe charset"))
            charmap = {i:stdStrings[i] for i in range(1,229)}
            
        elif n == 1:
            logger.info(('xxxxx', (), "Expert charset"))
            charmap = {}
            i = 1
            ranges = ((1,1), (229,238), (13,15), (99,99), (239,248), (27,28), (249,266), 
                      (109,110), (267,318), (158,158), (155,155), (163,163), (319,326), 
                      (150,150), (164,164), (169,169), (327,378))
            for start, end in ranges:
                for c in range(start, end+1):
                    charmap[i] = stdStrings[c]
                    i += 1
                    
        elif n == 2:
            logger.info(('xxxxx', (), "Expert Subset charset"))
            charmap = {}
            i = 1
            ranges = ((1,1), (231,232), (235,238), (13,15), (99,99), (239,248), (27,28), 
                      (249,251), (253,266), (109,110), (267,270), (272,272), (300,302), 
                      (305,305), (314,315), (158,158), (155,155), (163,163), (320,326), 
                      (150,150), (164,164), (169,169), (327,346))
            for start, end in ranges:
                for c in range(start, end+1):
                    charmap[i] = stdStrings[c]
                    i += 1

        return cls(charmap)
    
    @classmethod
    def fromnumber(cls, n, **kwArgs):
        """
        Build a Format0 charset, mapping glyphID:glyphName from the specified Walker.
        
        >>> obj = Predefined.fromnumber(0)
        >>> obj[1]
        'space'
        >>> obj = Predefined.fromnumber(1)
        >>> obj[99]
        'Cedillasmall'
        >>> obj = Predefined.fromnumber(2)
        >>> obj[22]
        'colon'
        """
        
        if n == 0:
            # ISOAdobe: simply SIDs 1-228 in order:
            charmap = {i:stdStrings[i] for i in range(1,229)}
            
        elif n == 1:
            # Expert: ranges of SIDs:
            charmap = {}
            i = 1
            ranges = ((1,1), (229,238), (13,15), (99,99), (239,248), (27,28), (249,266), 
                      (109,110), (267,318), (158,158), (155,155), (163,163), (319,326), 
                      (150,150), (164,164), (169,169), (327,378))
            for start, end in ranges:
                for c in range(start, end+1):
                    charmap[i] = stdStrings[c]
                    i += 1
                    
        elif n == 2:
            # Expert subset
            charmap = {}
            i = 1
            ranges = ((1,1), (231,232), (235,238), (13,15), (99,99), (239,248), (27,28), 
                      (249,251), (253,266), (109,110), (267,270), (272,272), (300,302), 
                      (305,305), (314,315), (158,158), (155,155), (163,163), (320,326), 
                      (150,150), (164,164), (169,169), (327,346))
            for start, end in ranges:
                for c in range(start, end+1):
                    charmap[i] = stdStrings[c]
                    i += 1
        
        else:
            raise ValueError("Unknown predefined charset designator %d " % (n,))

        return cls(charmap)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format0 object to the specified
        LinkedWriter. If any keys or values do not fit in a single byte, a
        ValueError is raised.
        
        >>> 
        """

        pass
        
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (0, 1, 2, 5)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

