#
# axial_coordinates.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for tuples identifying a particular coordinate in the space defined by
all the variation axes present in a font.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import seqmeta
from fontio3.gvar.axial_coordinate import AxialCoordinate as AC
    
# -----------------------------------------------------------------------------

#
# Classes
#

class AxialCoordinates(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    These are tuples of AxialCoordinate objects. There is one attribute,
    axisOrder, for a tuple of axis tags. This is used in the custom __str__()
    method.
    """
    
    seqSpec = dict(
        item_followsprotocol = True,
        seq_asimmutablefunc = tuple)
    
    attrSpec = dict(
        axisOrder = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = tuple))
    
    #
    # Methods
    #
    
    def __hash__(self):
        """
        Since AxialCoordinates objects are used primarily as keys in dicts,
        we need to make sure the hash function only pays attention to the
        numeric values, and not the axisOrder. (Honestly, it's somewhat of a
        weakness in fontio3/3 that this has to be taken into account...)
        
        >>> ao = ('wght', 'wdth')
        >>> obj = AxialCoordinates((AC(1.0/3), AC(-0.25)), axisOrder=ao)
        >>> hash(obj) == hash((1.0/3, -0.25))
        True
        >>> hash(obj.asImmutable()) == hash((1.0/3, -0.25))
        True
        """
        
        return hash(tuple(self))
    
    def __new__(cls, iterable, **kwArgs):
        """
        Creates a new AxialCoordinates object. Note that there must be an
        axisOrder keyword provided.
        
        >>> ao = ('wght', 'wdth')
        >>> obj = AxialCoordinates((AC(1.0/3), AC(-0.25)), axisOrder=ao)
        >>> print(obj)
        (wght 0.333, wdth -0.25)
        """
        
        r = tuple.__new__(cls, iterable)
        r.axisOrder = tuple(kwArgs['axisOrder'])
        return r
    
    def __str__(self):
        """
        Returns a string representation of the AxialCoordinates object.
        
        >>> ao = ('wght', 'wdth')
        >>> obj = AxialCoordinates((AC(1.0/3), AC(-0.25)), axisOrder=ao)
        >>> print(obj)
        (wght 0.333, wdth -0.25)
        """
        
        it = list(zip(self.axisOrder, self))
        sv = ["%4s %s" % (axis, value) for axis, value in it]
        return "(%s)" % (', '.join(sv),)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for the AxialCoordinates object to the
        specified writer.
        
        >>> ao = ('wght', 'wdth')
        >>> obj = AxialCoordinates((AC(1.0/3), AC(-0.25)), axisOrder=ao)
        >>> utilities.hexdump(obj.binaryString())
               0 | 1555 F000                                |.U..            |
        """
        
        for obj in self:
            obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromlac(cls, lac, **kwArgs):
        """
        Given a living_variations-style LivingAxialCoordinate, create and
        return an AxialCoordinates object. The 'axisOrder' keyword argument is
        required.
        
        >>> lacObj = _makeLAC({'wght': -0.75, 'wdth': 0.5})
        >>> lacObj.pprint()
        Member:
          (wdth, 0.5)
        Member:
          (wght, -0.75)
        >>> ao = ('wght', 'wdth')
        >>> ac = AxialCoordinates.fromlac(lacObj, axisOrder=ao)
        >>> print(ac)
        (wght -0.75, wdth 0.5)
        """
        
        ao = kwArgs['axisOrder']
        t = lac.asCanonicalTuple(ao)
        return cls((AC(x) for x in t), axisOrder=ao)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxialCoordinates object from the specified
        walker, doing validation. The caller must provide an 'axisOrder' kwArg.
        
        >>> ao = ('wght', 'wdth')
        >>> obj = AxialCoordinates((AC(1.5), AC(-0.25)), axisOrder=ao)
        >>> bs = obj.binaryString()
        >>> fvb = AxialCoordinates.fromvalidatedbytes
        >>> obj2 = fvb(bs, axisOrder=ao)
        coords - DEBUG - Walker has 4 remaining bytes.
        coords.wght.coord - DEBUG - Walker has 4 remaining bytes.
        coords.wght.coord - DEBUG - Coordinate value is 24576
        coords.wdth.coord - DEBUG - Walker has 2 remaining bytes.
        coords.wdth.coord - DEBUG - Coordinate value is -4096
        coords - DEBUG - Coordinate is (wght 1.5, wdth -0.25)
        
        >>> obj2 == obj
        True
        
        >>> fvb(bs[:-1], axisOrder=ao)
        coords - DEBUG - Walker has 3 remaining bytes.
        coords.wght.coord - DEBUG - Walker has 3 remaining bytes.
        coords.wght.coord - DEBUG - Coordinate value is 24576
        coords.wdth.coord - DEBUG - Walker has 1 remaining bytes.
        coords.wdth.coord - ERROR - Insufficient bytes.
        
        Note that validation here catches cases where one or more axis tags are
        duplicated:
        
        >>> aoBad = ('wght', 'wght')
        >>> fvb(bs, axisOrder=aoBad)
        coords - DEBUG - Walker has 4 remaining bytes.
        coords - ERROR - There are duplicate axis tags
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('coords')
        else:
            logger = utilities.makeDoctestLogger('coords')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        ao = kwArgs['axisOrder']  # the absence is a code error, not a font one
        
        if len(ao) != len(set(ao)):
            logger.error((
              'V1034',
              (),
              "There are duplicate axis tags"))
            
            return None
        
        v = []
        fvw = AC.fromvalidatedwalker
        
        for axisTag in ao:
            subLogger = logger.getChild(axisTag)
            obj = fvw(w, logger=subLogger)
            
            if obj is None:
                return None
            
            v.append(obj)
        
        r = cls(v, axisOrder=ao)
        
        logger.debug((
          'Vxxxx',
          (r,),
          "Coordinate is %s"))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxialCoordinates object from the specified
        walker. The caller must provide an 'axisOrder' kwArg.
        
        >>> ao = ('wght', 'wdth')
        >>> obj = AxialCoordinates((AC(1.5), AC(-0.25)), axisOrder=ao)
        >>> bs = obj.binaryString()
        >>> obj2 = AxialCoordinates.frombytes(bs, axisOrder=ao)
        >>> obj == obj2
        True
        """
        
        ao = kwArgs['axisOrder']
        fw = AC.fromwalker
        v = [fw(w, **kwArgs) for axis in ao]
        return cls(v, axisOrder=ao)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _makeLAC(d):
        from fontio3.opentype import living_variations
        
        return living_variations.LivingAxialCoordinate.fromdict(d)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

