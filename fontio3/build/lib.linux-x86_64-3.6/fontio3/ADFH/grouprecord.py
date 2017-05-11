#
# grouprecord.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ADFH 2.0 group records (BAZ).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate_numberOfYLines(obj, **kwArgs):
    kwArgs.pop('numBits', None)
    
    if not valassist.isNumber_integer_unsigned(obj, numBits=16, **kwArgs):
        return False
    
    if obj == 0 or obj > 500:
        kwArgs['logger'].warning((
          'V0595',
          (obj,),
          "The numberOfYLines value %s is zero or is unusually large."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GroupRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Simple objects with three attributes: firstCVT, numberOfYLines, and
    isRightToLeft. These are needed to do BAZ autohinting.
    
    >>> _testingValues[1].pprint()
    Index of first CVT value: 12
    Number of y-lines: 30
    Adjust strokes right-to-left: False
    
    >>> _testingValues[2].pprint()
    Index of first CVT value: 4
    Number of y-lines: 12
    Adjust strokes right-to-left: True
    
    >>> logger = utilities.makeDoctestLogger("grouprecord_test")
    >>> e = utilities.fakeEditor(0x10000)
    >>> e[b'cvt '] = [0, -10, 25, -19, 15, 23]
    >>> _testingValues[2].isValid(editor=e, logger=logger)
    True
    
    >>> _testingValues[1].isValid(editor=e, logger=logger)
    grouprecord_test.firstCVT - ERROR - CVT index 12 is not defined.
    False
    
    >>> obj = _testingValues[2].__copy__()
    >>> obj.numberOfYLines = "fred"
    >>> obj.isValid(editor=e, logger=logger)
    grouprecord_test.numberOfYLines - ERROR - The value 'fred' is not a real number.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        firstCVT = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Index of first CVT value",
            attr_renumbercvtsdirect = True),
        
        numberOfYLines = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Number of y-lines",
            attr_validatefunc = _validate_numberOfYLines),
        
        isRightToLeft = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Adjust strokes right-to-left"))
    
    attrSorted = ('firstCVT', 'numberOfYLines', 'isRightToLeft')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GroupRecord to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0000 0000 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000C 001E 0000 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0004 000C 0001 0000                      |........        |
        """
        
        w.add(
          "3Hxx",
          self.firstCVT,
          self.numberOfYLines,
          int(self.isRightToLeft))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a GroupRecord object from the specified walker,
        doing source validation.
        """
        
        logger = kwArgs.get('logger', logging.getLogger())
        logger = logger.getChild("grouprecord")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        cvtIndex, yLines, rightToLeft, unused = w.unpack("4H")
        
        if rightToLeft not in {0, 1}:
            logger.warning((
              'V0590',
              (rightToLeft,),
              "The rightToLeft value (%d) is neither one nor zero."))
        
        if unused:
            logger.warning((
              'V0591',
              (unused,),
              "The unused field has a nonzero value (%d)."))
        
        return cls(cvtIndex, yLines, bool(rightToLeft))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a GroupRecord from the specified walker.
        
        >>> fb = GroupRecord.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        c, y, r = w.unpack("3Hxx")
        return cls(c, y, bool(r))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        GroupRecord(),
        GroupRecord(firstCVT=12, numberOfYLines=30, isRightToLeft=False),
        GroupRecord(firstCVT=4, numberOfYLines=12, isRightToLeft=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
