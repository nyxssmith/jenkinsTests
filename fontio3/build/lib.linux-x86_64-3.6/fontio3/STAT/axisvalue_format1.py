#
# axisvalue_format1.py
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
    """
    isValid() validation for AxisValueTable format 1
    
    requires kwArgs 'editor' and 'logger'
    """
    editor = kwArgs['editor']
    logger = kwArgs['logger']
    namestr=editor.name.getNameFromID(d.nameID, None)

    isOK = True

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
    Value Table information in format 1.

    >>> e = utilities.fakeEditor(1000, name=True)
    >>> logger = utilities.makeDoctestLogger('test')
    >>> obj = AxisValue(nameID=256, value=6.21)
    >>> obj.isValid(editor=e, logger=logger)
    True
    >>> obj.nameID=65534
    >>> obj.isValid(editor=e, logger=logger)
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

        value = dict(
            attr_label = "Value",
            attr_initfunc = axial_coordinate.AxialCoordinate,
            attr_validatefunc = valassist.isNumber_fixed))

    attrSorted = ('flags', 'nameID', 'value')

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the STAT to the specified walker.

        requires kwArg 'axisIndex', referring to an axis in the STAT table's
        AxisRecord array.

        >>> v = axial_coordinate.AxialCoordinate(1234.56)
        >>> flags = axisvalueflags.AxisValueFlags.fromnumber(1)
        >>> obj = AxisValue(flags=flags, nameID=987, value=v)
        >>> b = obj.binaryString(axisIndex=7)
        >>> utilities.hexdump(b)
               0 | 0001 0007 0001 03DB  04D2 8F5C           |...........\    |
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("H", 1)  # format
        w.add("H", kwArgs['axisIndex'])
        self.flags.buildBinary(w, **kwArgs)
        w.add("H", self.nameID)
        self.value.buildBinary(w, **kwArgs)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new AxisValue (format 1).
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = ("00 01 00 02 00 02 01 01 01 02 03 04")
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValue.fromvalidatedbytes(b, logger=logger)
        test.axisvalue_format1 - DEBUG - Walker has 12 remaining bytes.
        test.axisvalue_format1.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        >>> s = ("00 02 00 02 00 02 01 01 01 02 03 04")
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValue.fromvalidatedbytes(b, logger=logger)
        test.axisvalue_format1 - DEBUG - Walker has 12 remaining bytes.
        test.axisvalue_format1 - ERROR - Expected format 1, got 2
        >>> obj = AxisValue.fromvalidatedbytes(b'xyz', logger=logger)
        test.axisvalue_format1 - DEBUG - Walker has 3 remaining bytes.
        test.axisvalue_format1 - ERROR - Insufficient bytes
        """

        logger = kwArgs.pop('logger', None)
        axisTag = kwArgs.get('axisTag')

        if logger is None:
            logger = logging.getLogger().getChild('axisvalue_format1')
        else:
            logger = logger.getChild('axisvalue_format1')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None

        r = cls()

        format, axisIndex = w.unpack("2H")

        if format != 1:
            logger.error((
              'V1090',
              (format,),
              "Expected format 1, got %d"))

            return None

        r._axisIndex = axisIndex
        fvw = axisvalueflags.AxisValueFlags.fromvalidatedwalker
        r.flags = fvw(w)
        r.nameID = w.unpack("H")
        fvw = axial_coordinate.AxialCoordinate.fromvalidatedwalker
        r.value = fvw(w, logger=logger)

        return r


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxisValue (format 1) object from the
        specified walker.

        >>> s = ("00 01 00 03 00 03 02 11 12 34 56 78")
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValue.frombytes(b)
        >>> obj.pprint()
        Flags:
          Older Sibling Font Attribute: True
          Elidable Axis Value Name: True
        Designation in the 'name' table: 529
        Value: 4660.338
        >>> obj._axisIndex == 3
        True
        """

        r = cls()

        format, axisIndex = w.unpack("2H")
        r._axisIndex = axisIndex
        fw = axisvalueflags.AxisValueFlags.fromwalker
        r.flags = fw(w)
        r.nameID = w.unpack("H")
        fw = axial_coordinate.AxialCoordinate.fromwalker
        r.value = fw(w)

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
