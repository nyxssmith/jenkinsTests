#
# axisdict.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'avar'-specified maps for a single axis. The top-level Avar dict
is a collection of these.
"""

# System imports
import functools

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(obj, **kwArgs):
    """
    Do extensive reality checking on the dict values.
    
    >>> logger = utilities.makeDoctestLogger("_val")
    >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
    >>> obj.isValid(logger=logger)
    True
    
    >>> obj = AxisDict({})
    >>> obj.isValid(logger=logger)
    _val - ERROR - An AxisDict must contain keys for -1.0, 0, and 1.0; this dict is missing one or more of these values.
    False
    
    >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 0.50000000001: 0.3, 1.0: 1.0})
    >>> obj.isValid(logger=logger)
    _val - ERROR - Some keys in the AxisDict are too close together and will end up with the same shortFrac representation.
    False
    
    >>> obj = AxisDict({-1.5: -1.5, -1.0: -1.0, 0.0: 0.0, 1.0: 1.0})
    >>> obj.isValid(logger=logger)
    _val - ERROR - The smallest key in the AxisDict is less than -1.0
    _val - ERROR - The smallest value in the AxisDict is less than -1.0
    False
    
    >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 1.0: 1.0, 1.5: 1.5})
    >>> obj.isValid(logger=logger)
    _val - ERROR - The largest key in the AxisDict is greater than +1.0
    _val - ERROR - The largest value in the AxisDict is greater than +1.0
    False
    
    >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.1, 1.0: 1.0})
    >>> obj.isValid(logger=logger)
    _val - ERROR - One or more of the fixed values (-1.0, 0.0, +1.0) do not map to themselves.
    False
    
    >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 0.25: 0.5, 0.5: 0.25, 1.0: 1.0})
    >>> obj.isValid(logger=logger)
    _val - ERROR - The values in the AxisDict are out of order with respect to the keys.
    False
    
    >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 0.25: 0.5, 0.5: 0.5, 1.0: 1.0})
    >>> obj.isValid(logger=logger)
    _val - ERROR - There are duplicates in the AxisDict values.
    False
    """
    
    r = True
    logger = kwArgs['logger']
    rawSort = sorted(obj)
    allKeys = [int(round(n * 16384)) for n in rawSort]
    allKeysSet = set(allKeys)
    
    if (len(obj) < 3) or ({-16384, 0, 16384} - allKeysSet):
        logger.error((
          'Vxxxx',
          (),
          "An AxisDict must contain keys for -1.0, 0, and 1.0; this "
          "dict is missing one or more of these values."))
        
        r = False
    
    if len(allKeysSet) != len(obj):
        logger.error((
          'Vxxxx',
          (),
          "Some keys in the AxisDict are too close together and will end "
          "up with the same shortFrac representation."))
        
        r = False
    
    if rawSort and (rawSort[0] < -1.0):
        logger.error((
          'Vxxxx',
          (),
          "The smallest key in the AxisDict is less than -1.0"))
        
        r = False
    
    if rawSort and (rawSort[-1] > 1.0):
        logger.error((
          'Vxxxx',
          (),
          "The largest key in the AxisDict is greater than +1.0"))
        
        r = False
    
    if not all(obj[n] == n for n in [-1.0, 0.0, 1.0] if n in obj):
        logger.error((
          'Vxxxx',
          (),
          "One or more of the fixed values (-1.0, 0.0, +1.0) do not map to "
          "themselves."))
        
        r = False
    
    rawValues = [obj[n] for n in rawSort]
    rawValuesSorted = sorted(rawValues)
    
    if rawValues != rawValuesSorted:
        logger.error((
          'Vxxxx',
          (),
          "The values in the AxisDict are out of order with respect "
          "to the keys."))
        
        r = False
    
    if rawValuesSorted and (rawValuesSorted[0] < -1.0):
        logger.error((
          'Vxxxx',
          (),
          "The smallest value in the AxisDict is less than -1.0"))
        
        r = False
    
    if rawValuesSorted and (rawValuesSorted[-1] > 1.0):
        logger.error((
          'Vxxxx',
          (),
          "The largest value in the AxisDict is greater than +1.0"))
        
        r = False
    
    if len(rawValues) != len(set(rawValues)):
        logger.error((
          'Vxxxx',
          (),
          "There are duplicates in the AxisDict values."))
        
        r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

class AxisDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing the normalized transformation for a single axis. These
    are dicts mapping normalized input coordinates to normalized output
    coordinates.
    
    >>> AxisDict({-1.0: -1.0, -0.75: -0.25, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0}).pprint()
    -1.0: -1.0
    -0.75: -0.25
    0.0: 0.0
    0.5: 0.25
    1.0: 1.0
    """
    
    mapSpec = dict(
        item_pprintlabelpresort = True,
        
        item_validatefunc_partial = functools.partial(
          valassist.isNumber_fixed,
          characteristic = 2,
          numBits = 16),
        
        item_validatefunckeys_partial = functools.partial(
          valassist.isNumber_fixed,
          characteristic = 2,
          numBits = 16),
        
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the AxisDict to the specified walker.
        
        >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
        >>> utilities.hexdump(obj.binaryString())
               0 | 0004 C000 C000 0000  0000 2000 1000 4000 |.......... ...@.|
              10 | 4000                                     |@.              |
        """
        
        w.add("H", len(self))
        
        for fromCoord in sorted(self):
            toCoord = self[fromCoord]
            
            w.add(
              "2h",
              int(round(fromCoord * 16384)),
              int(round(toCoord * 16384)))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxisDict from the data in the specified
        walker, doing validation.
        
        >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
        >>> bs = obj.binaryString()
        >>> obj2 = AxisDict.fromvalidatedbytes(bs)
        axisdict - DEBUG - Walker has 18 remaining bytes.
        >>> obj == obj2
        True
        
        >>> AxisDict.fromvalidatedbytes(bs[:-1])
        axisdict - DEBUG - Walker has 17 remaining bytes.
        axisdict - ERROR - Insufficient bytes.
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('axisdict')
        else:
            logger = utilities.makeDoctestLogger('axisdict')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        
        if w.length() < 4 * count:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        pairs = w.group("2h", count)
        r = cls()
        
        for fromCoord, toCoord in pairs:
            r[fromCoord / 16384] = toCoord / 16384
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxisDict from the data in the specified
        walker.
        
        >>> obj = AxisDict({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
        >>> bs = obj.binaryString()
        >>> obj2 = AxisDict.frombytes(bs)
        >>> obj == obj2
        True
        """
        
        count = w.unpack("H")
        pairs = w.group("2h", count)
        r = cls()
        
        for fromCoord, toCoord in pairs:
            r[fromCoord / 16384] = toCoord / 16384
        
        return r

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

