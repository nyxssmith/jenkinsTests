#
# axis_info.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
AxisInfo class needed for support of 'fvar' tables.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.fvar import axial_coordinate
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    v = [float(obj.minValue), float(obj.defaultValue), float(obj.maxValue)]
    
    if v != sorted(v):
        logger.error((
          'Vxxxx',
          (v,),
          "The [min, default, max] values of %s are not in order."))
        
        return False
    
    if obj.flags:
        logger.warning((
          'Vxxxx',
          (obj.flags,),
          "The flags field (%d) should be zero."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class AxisInfo(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing VariationAxis entries in an fvar table.
    
    >>> AC = axial_coordinate.AxialCoordinate
    >>> ai = AxisInfo(AC(0.5), AC(1.0), AC(2.0), 0, 256)
    >>> e = utilities.fakeEditor(1000, name=True)
    >>> ai.pprint(editor=e)
    Minimum style coordinate: 0.5
    Default style coordinate: 1.0
    Maximum style coordinate: 2.0
    Designation in the 'name' table: 256 ('String 1')
    
    >>> ai = AxisInfo(AC(0.3333333), AC(1.0), AC(2.9999999), 0, 256)
    >>> ai.pprint(editor=e)
    Minimum style coordinate: 0.333
    Default style coordinate: 1.0
    Maximum style coordinate: 3.0
    Designation in the 'name' table: 256 ('String 1')
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        minValue = dict(
            attr_label = 'Minimum style coordinate',
            attr_initfunc = (lambda: -1.0),
            attr_validatefunc = valassist.isNumber_fixed),
        
        defaultValue = dict(
            attr_label = 'Default style coordinate',
            attr_initfunc = (lambda: 0.0),
            attr_validatefunc = valassist.isNumber_fixed),
        
        maxValue = dict(
            attr_label = 'Maximum style coordinate',
            attr_initfunc = (lambda: 1.0),
            attr_validatefunc = valassist.isNumber_fixed),
        
        flags = dict(
            attr_label = 'Flags',
            attr_initfunc = (lambda: 0),
            attr_showonlyiftrue = True,
            attr_validatefunc = valassist.isFormat_H),
        
        nameID = dict(
            attr_label = "Designation in the 'name' table",
            attr_renumbernamesdirect = True))

    attrSorted = ('minValue', 'defaultValue', 'maxValue', 'flags', 'nameID')

    #
    # Methods
    #

    # noinspection PyUnusedLocal
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the object to the specified writer.
        
        >>> AC = axial_coordinate.AxialCoordinate
        >>> ai = AxisInfo(AC(0.5), AC(1.0), AC(2.0), 0, 256)
        >>> utilities.hexdump(ai.binaryString())
               0 | 0000 8000 0001 0000  0002 0000 0000 0100 |................|
        """
        
        self.minValue.buildBinary(w, **kwArgs)
        self.defaultValue.buildBinary(w, **kwArgs)
        self.maxValue.buildBinary(w, **kwArgs)
        w.add('H', self.flags)
        w.add('H', self.nameID)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker,
        doing source validation.
        
        >>> bs = bytes.fromhex(
        ...   "00 00 80 00 00 01 00 00 00 02 00 00 00 00 01 00")
        >>> ai = AxisInfo.fromvalidatedbytes(bs)
        AxisInfo - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 12 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        >>> ai.pprint()
        Minimum style coordinate: 0.5
        Default style coordinate: 1.0
        Maximum style coordinate: 2.0
        Designation in the 'name' table: 256
        
        >>> bs = bytes.fromhex(
        ...   "00 00 80 00 00 01 00 00 00 02 00 00 00 00 00 FF")
        >>> ai = AxisInfo.fromvalidatedbytes(bs)
        AxisInfo - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 12 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        AxisInfo - ERROR - nameID=255 is not > 255 and < 32768
        
        >>> AxisInfo.fromvalidatedbytes(bs[:-1])
        AxisInfo - DEBUG - Walker has 15 remaining bytes.
        AxisInfo - ERROR - Insufficient bytes (15) for AxisInfo (minimum 16)
        
        >>> bs = bytes.fromhex(
        ...   "00 00 80 00 00 02 00 00 00 01 00 00 00 00 01 00")
        >>> AxisInfo.fromvalidatedbytes(bs)
        AxisInfo - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 12 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        AxisInfo - ERROR - The [min, default, max] values of [0.5, 2.0, 1.0] are not in order.
        
        >>> bs = bytes.fromhex(
        ...   "00 00 80 00 00 01 00 00 00 02 00 00 00 08 01 00")
        >>> ai = AxisInfo.fromvalidatedbytes(bs)
        AxisInfo - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 16 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 12 remaining bytes.
        AxisInfo.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        AxisInfo - WARNING - The flags value is 8, but should be zero.
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('AxisInfo')
        else:
            logger = utilities.makeDoctestLogger('AxisInfo')

        remaining_length = w.length()
        
        logger.debug((
          'V0001',
          (remaining_length,),
          "Walker has %d remaining bytes."))

        needed_bytes = 16  # already unpacked 4 bytes for tag
        
        if remaining_length < needed_bytes:
            logger.error((
              'V0004',
              (remaining_length, needed_bytes),
              "Insufficient bytes (%d) for AxisInfo (minimum %d)"))
            
            return None

        r = cls()
        fvw = axial_coordinate.AxialCoordinate.fromvalidatedwalker
        r.minValue = fvw(w, logger=logger, **kwArgs)
        r.defaultValue = fvw(w, logger=logger, **kwArgs)
        r.maxValue = fvw(w, logger=logger, **kwArgs)
        r.flags, r.nameID = w.unpack('2H')
        v = [float(r.minValue), float(r.defaultValue), float(r.maxValue)]
        
        if v != sorted(v):
            logger.error((
              'Vxxxx',
              (v,),
              "The [min, default, max] values of %s are not in order."))
            
            return None

        if not (255 < r.nameID < 32768):
            logger.error((
              'Vxxxx',
              (r.nameID,),
              "nameID=%d is not > 255 and < 32768"))
            
            return None
        
        if r.flags:
            logger.warning((
              'Vxxxx',
              (r.flags,),
              "The flags value is %d, but should be zero."))
        
        return r

    # noinspection PyUnusedLocal
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker.
        
        >>> bs = bytes.fromhex(
        ...   "00 00 80 00 00 01 00 00 00 02 00 00 00 00 01 00")
        >>> ai = AxisInfo.frombytes(bs)
        >>> ai.pprint()
        Minimum style coordinate: 0.5
        Default style coordinate: 1.0
        Maximum style coordinate: 2.0
        Designation in the 'name' table: 256
        """
        
        r = cls()
        fw = axial_coordinate.AxialCoordinate.fromwalker
        r.minValue = fw(w, **kwArgs)
        r.defaultValue = fw(w, **kwArgs)
        r.maxValue = fw(w, **kwArgs)
        r.flags, r.nameID = w.unpack('2H')
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    if __debug__:
        _test()

