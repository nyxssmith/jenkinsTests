#
# VORG.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'VORG' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class VORG(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing 'VORG' tables. These are dicts mapping glyph indices
    to vertOriginY values.
    
    >>> _testingValues[1].pprint()
    0: 100
    1: 200
    2: 300
    default Y origin: 50

    >>> logger = utilities.makeDoctestLogger("VORG")
    >>> _testingValues[1].isValid(logger=logger)
    True
    """
    
    #
    # Class definition variables
    #

    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_subloggernamefunc = (lambda i: "glyph %d" % (i,)),
        item_usenamerforstr = True)

    attrSpec = dict(
        defaultOrigin = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda:0),
            attr_label = "default Y origin"))
        
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the VORG object to the specified LinkedWriter.

        >>> h = utilities.hexdumpString
        >>> print(h(_testingValues[1].binaryString()), end='')
               0 |0001 0000 0032 0003  0000 0064 0001 00C8 |.....2.....d....|
              10 |0002 012C                                |...,            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("HH", 1, 0) # major & minor version
        w.add("h", self.defaultOrigin)
        w.add("H", len(self)) # numVertOriginYMetrics
        
        for g,v in self.items():
            w.add("Hh", g, v)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new VORG object. However, it
        also does validation on the binary data being unpacked.
        
        The following keyword arguments are supported:
        
            logger              A logger to which observations will be posted.
                                If not specified, the default system logger
                                will be used.

        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = _testingValues[1].binaryString()
        >>> obj = VORG.fromvalidatedbytes(s, logger=logger)
        test.VORG - DEBUG - Walker has 20 remaining bytes.
        
        >>> VORG.fromvalidatedbytes(s, logger=logger)
        test.VORG - DEBUG - Walker has 20 remaining bytes.
        VORG({0: 100, 1: 200, 2: 300}, defaultOrigin=50)
        
        >>> VORG.fromvalidatedbytes(s[:-1], logger=logger)
        test.VORG - DEBUG - Walker has 19 remaining bytes.
        test.VORG - ERROR - Insufficient bytes (11) for 3 glyphs.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('VORG')
        else:
            logger = logger.getChild('VORG')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes (8 minimum required for VORG)."))
            
            return None
    
        major, minor, default, num = w.unpack("HHhH")

        if w.length() < (num * 4):
            logger.error((
              'V0004',
              (w.length(), num,),
              "Insufficient bytes (%d) for %d glyphs."))

            return None

        orgs = w.group("Hh", num)
        r = cls({k:v for k,v in orgs}, defaultOrigin=default)

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new VORG object using the specified walker.

        >>> s = _testingValues[1].binaryString()
        >>> _testingValues[1] == VORG.frombytes(s)
        True
        """
        
        major, minor, default, num = w.unpack("HHhH")

        orgs = w.group("Hh", num)
        r = cls({k:v for k,v in orgs}, defaultOrigin=default)

        return r
    

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        VORG(),
                  
        VORG({
          0: 100,
          1: 200,
          2: 300},
          defaultOrigin = 50))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
