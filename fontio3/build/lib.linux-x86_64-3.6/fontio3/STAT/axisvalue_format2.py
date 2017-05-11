#
# axisvalue_format2.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for AxisValues within the STAT table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.STAT import axial_coordinate, axisvalueflags
from fontio3.utilities import valassist


# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(d, **kwArgs):
    editor = kwArgs['editor']
    logger = kwArgs['logger']
    namestr=editor.name.getNameFromID(d.nameID, None)

    isOK = True

    if not d.rangeMinValue < d.rangeMaxValue:
        logger.warning((
          'V1088',
          (d.rangeMinValue, d.rangeMaxValue),
          "Range minimum %s is not less than range maximum %s"))

        isOK = False

    if not d.rangeMinValue <= d.nominalValue <= d.rangeMaxValue:
        logger.warning((
          'V1089',
          (d.rangeMinValue, d.nominalValue, d.rangeMaxValue),
          "Nominal value %s is not between range minimum %s and range maximum %s"))

        isOK = False

    if namestr is None:
        logger.error((
          'V1086',
          (d.nameID,),
          "NameID %d not found in the font's 'name' table."))

        isOK = False

    if not 255 < d.nameID < 32768:
        logger.error((
          'V1087',
          (d.nameID,),
          "NameID %d is not between 255 and 32768."))

        isOK = False

    return isOK


# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class AxisValue(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing AxisValues. These are simple objects that contain Axis
    Value Table information in format 2.

    >>> e = utilities.fakeEditor(1000, name=True)
    >>> logger = utilities.makeDoctestLogger('test')
    >>> mx = axial_coordinate.AxialCoordinate(5)
    >>> obj = AxisValue(nameID=256, rangeMaxValue=mx)
    >>> obj.isValid(editor=e, logger=logger)
    True
    >>> obj.nameID = 65534
    >>> obj.rangeMinValue = 1000
    >>> obj.nominalValue = 1
    >>> obj.isValid(editor=e, logger=logger)
    test - WARNING - Range minimum 1000 is not less than range maximum 5.0
    test - WARNING - Nominal value 1000 is not between range minimum 1 and range maximum 5.0
    test - ERROR - NameID 65534 not found in the font's 'name' table.
    test - ERROR - NameID 65534 is not between 255 and 32768.
    False
    """

    #
    # Class definition variables
    #

    objSpec = dict(
        obj_validatefunc_partial = _validate)

    attrSpec = dict(
        flags = dict(
            attr_label = "Flags",
            attr_renumbernamesdirect = True,
            attr_followsprotocol = True,
            attr_initfunc = axisvalueflags.AxisValueFlags),

        nameID = dict(
            attr_label = "Designation in the 'name' table",
            attr_initfunc = (lambda: 0),
            attr_validatefunc = valassist.isFormat_H),

        nominalValue = dict(
            attr_label = "Nominal value",
            attr_initfunc = axial_coordinate.AxialCoordinate,
            attr_validatefunc = valassist.isNumber_fixed),

        rangeMinValue = dict(
            attr_label = "Range Minimum Value",
            attr_initfunc = axial_coordinate.AxialCoordinate,
            attr_validatefunc = valassist.isNumber_fixed),

        rangeMaxValue = dict(
            attr_label = "Range Maximum Value",
            attr_initfunc = axial_coordinate.AxialCoordinate,
            attr_validatefunc = valassist.isNumber_fixed))

    attrSorted = ('flags', 'nameID', 'nominalValue', 'rangeMinValue', 'rangeMaxValue')

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the STAT to the specified walker.

        requires kwArg 'axisIndex', referring to an axis in the STAT table's
        AxisRecord array.

        >>> nm = axial_coordinate.AxialCoordinate(1234.56)
        >>> mn = axial_coordinate.AxialCoordinate(0.0)
        >>> mx = axial_coordinate.AxialCoordinate(9876.54)
        >>> flags = axisvalueflags.AxisValueFlags.fromnumber(2)
        >>> obj = AxisValue(flags=flags, nameID=987, nominalValue=nm,
        ...     rangeMinValue=mn, rangeMaxValue=mx)
        >>> b = obj.binaryString(axisIndex=6)
        >>> utilities.hexdump(b)
               0 | 0002 0006 0002 03DB  04D2 8F5C 0000 0000 |...........\....|
              10 | 2694 8A3D                                |&..=            |
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("H", 2)  # format
        w.add("H", kwArgs['axisIndex'])
        self.flags.buildBinary(w, **kwArgs)
        w.add("H", self.nameID)
        self.nominalValue.buildBinary(w, **kwArgs)
        self.rangeMinValue.buildBinary(w, **kwArgs)
        self.rangeMaxValue.buildBinary(w, **kwArgs)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new AxisValue (format 1).
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = ("00 02 00 02 00 02 01 00 00 12 34 56 00 00 12 34 "
        ...      "12 34 56 78")
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValue.fromvalidatedbytes(b, logger=logger)
        test.axisvalue_format2 - DEBUG - Walker has 20 remaining bytes.
        test.axisvalue_format2.AxialCoordinate - DEBUG - Walker has 12 remaining bytes.
        test.axisvalue_format2.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        test.axisvalue_format2.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        >>> s = ("00 02 00 02 00 02 01 00 12 34 56 78 00 00 34 56 "
        ...      "00 00 23 45")
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValue.fromvalidatedbytes(b, logger=logger)
        test.axisvalue_format2 - DEBUG - Walker has 20 remaining bytes.
        test.axisvalue_format2.AxialCoordinate - DEBUG - Walker has 12 remaining bytes.
        test.axisvalue_format2.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        test.axisvalue_format2.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.

        >>> s = ("00 0F 00 02 00 02 01 00 12 34 56 78 00 00 34 56 "
        ...      "00 00 23 45")
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValue.fromvalidatedbytes(b, logger=logger)
        test.axisvalue_format2 - DEBUG - Walker has 20 remaining bytes.
        test.axisvalue_format2 - ERROR - Expected format 2, got 15
        
        >>> obj = AxisValue.fromvalidatedbytes(b'xyz', logger=logger)
        test.axisvalue_format2 - DEBUG - Walker has 3 remaining bytes.
        test.axisvalue_format2 - ERROR - Insufficient bytes
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('axisvalue_format2')
        else:
            logger = logger.getChild('axisvalue_format2')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 20:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None

        r = cls()

        format, axisIndex = w.unpack("2H")

        if format != 2:
            logger.error((
              'V1090',
              (format,),
              "Expected format 2, got %d"))

            return None

        r._axisIndex = axisIndex
        fvw = axisvalueflags.AxisValueFlags.fromvalidatedwalker
        r.flags = fvw(w)
        r.nameID = w.unpack("H")
        fvw = axial_coordinate.AxialCoordinate.fromvalidatedwalker
        r.nominalValue = fvw(w, logger=logger)
        r.rangeMinValue = fvw(w, logger=logger)
        r.rangeMaxValue = fvw(w, logger=logger)

        return r


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxisValue (format 2) object from the
        specified walker.

        >>> s = ("00 02 00 09 00 02 01 00 00 12 34 56 00 00 12 34 "
        ...      "12 34 56 78")
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValue.frombytes(b)
        >>> obj.pprint()
        Flags:
          Older Sibling Font Attribute: False
          Elidable Axis Value Name: True
        Designation in the 'name' table: 256
        Nominal value: 18.204
        Range Minimum Value: 0.071
        Range Maximum Value: 4660.338
        >>> obj._axisIndex == 9
        True
        """

        r = cls()

        format, axisIndex = w.unpack("2H")
        r._axisIndex = axisIndex
        fw = axisvalueflags.AxisValueFlags.fromwalker
        r.flags = fw(w)
        r.nameID = w.unpack("H")
        fw = axial_coordinate.AxialCoordinate.fromwalker
        r.nominalValue = fw(w)
        r.rangeMinValue = fw(w)
        r.rangeMaxValue = fw(w)

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

if __name__ == "__main__":
    if __debug__:
        _test()
