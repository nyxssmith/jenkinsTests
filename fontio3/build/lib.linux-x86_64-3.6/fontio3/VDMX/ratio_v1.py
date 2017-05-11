#
# ratio_v1.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Ratio objects for version 1 'VDMX' tables.
"""

# System imports
import fractions

# Other imports
from fontio3.fontdata import enummeta, simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprintFunc(p, obj, **kwArgs):
    if not (obj.xRatio or obj.yStartRatio or obj.yEndRatio):
        p.simple("All aspect ratios")
    
    else:
        f = fractions.Fraction(obj.xRatio, obj.yStartRatio)
        
        p.simple(
          "%d:%d" % (f.numerator, f.denominator),
          label = "Start ratio",
          **kwArgs)
        
        f = fractions.Fraction(obj.xRatio, obj.yEndRatio)
        
        p.simple(
          "%d:%d" % (f.numerator, f.denominator),
          label = "End ratio",
          **kwArgs)
    
    p.simple(obj.charSet, label="Char set", **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CharSet(int, metaclass=enummeta.FontDataMetaclass):
    """
    Objects representing a character set for a version 1 'VDMX' table. This is
    a value of zero or one; for version 1 'VDMX' tables, both zero and one mean
    there is no subset. A client adding new glyphs to an existing font should
    use zero; a client creating a new font ab initio should use one.
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_annotatevalue = True,
        
        enum_stringsdict = {
            0: "All glyphs",
            1: "All glyphs"},
            
        enum_validatecode_badenumvalue = 'V0266')

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class Ratio(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single ratio range. These are simple objects with
    the following attributes:
    
        charSet         A CharSet object.
        
        xRatio          An integer representing the normalized value of the
                        horizontal aspect-ratio component.
        
        yStartRatio     An integer representing the normalized value of one end
                        of the vertical aspect-ratio component. Note that since
                        this is the denominator, a larger value here represents
                        a smaller aspect ratio, and vice versa.
        
        yEndRatio       An integer representing the normalized value of the
                        other end of the vertical aspect-ratio component. Note
                        that since this is the denominator, a larger value here
                        represents a smaller aspect ratio, and vice versa.
    
    >>> _testingValues[0].pprint()
    All aspect ratios
    Char set: All glyphs (0)
    
    >>> _testingValues[1].pprint()
    Start ratio: 2:1
    End ratio: 1:1
    Char set: All glyphs (0)
    
    >>> _testingValues[2].pprint()
    Start ratio: 4:3
    End ratio: 1:1
    Char set: All glyphs (1)
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
       charSet = dict(
           attr_followsprotocol = True,
           attr_initfunc = CharSet,
           attr_label = "Character set"),
    
       xRatio = dict(
           attr_initfunc = (lambda: 0),
           attr_label = "Horizontal factor"),
    
       yStartRatio = dict(
           attr_initfunc = (lambda: 0),
           attr_label = "Vertical start factor"),
    
       yEndRatio = dict(
           attr_initfunc = (lambda: 0),
           attr_label = "Vertical end factor"))
    
    attrSorted = ('charSet', 'xRatio', 'yStartRatio', 'yEndRatio')
    
    objSpec = dict(
        obj_pprintfunc = _pprintFunc)
    
    ratioVersion = 1  # class constant
    
    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Ratio object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0102                                |....            |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0104 0304                                |....            |
        """
        
        w.add("4B", self.charSet, self.xRatio, self.yStartRatio, self.yEndRatio)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Ratio object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == Ratio.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[1]
        >>> obj == Ratio.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == Ratio.frombytes(obj.binaryString())
        True
        """
        
        cs, *t = w.unpack("4B")
        return cls(CharSet(cs), *t)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Ratio object from the specified walker.
        
        >>> logger = utilities.makeDoctestLogger('test')

        >>> _testingValues[1].isValid(logger=logger)
        True

        >>> _testingValues[3].isValid(logger=logger)
        test.charSet - ERROR - Value 27 is not a valid enum value.
        False
        """
        
        logger = kwArgs.pop('logger', None)
        if logger is None:
            logger = logging.getLogger().getChild('Ratio_v1')
        else:
            logger = logger.getChild('Ratio_v1')

        cs, *t = w.unpack("4B")
        return cls(CharSet(cs), *t)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Ratio(),
        Ratio(CharSet(0), 2, 1, 2),
        Ratio(CharSet(1), 4, 3, 4),
        Ratio(CharSet(27),3, 3, 3))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
