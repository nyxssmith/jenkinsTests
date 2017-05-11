#
# axisrecord.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
AxisRecord class needed for support of 'STAT' tables.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.STAT import axisvalues
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(d, **kwArgs):
    """
    isValid() validation for AxisRecords
    """
    editor = kwArgs['editor']
    logger = kwArgs['logger']
    namestr=editor.name.getNameFromID(d.nameID, None)

    isOK = True

    if namestr is None:
        logger.error((
          'V1083',
          (d.nameID,),
          "AxisRecord nameID %d not found in the font's 'name' table."))

        isOK = False

    if not 255 < d.nameID < 32768:
        logger.error((
          'V1084',
          (d.nameID,),
          "AxisRecord nameID %d is not between 255 and 32768."))

        isOK = False

    return isOK


# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class AxisRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing Axis Record entries in a STAT table.

    >>> AC = axial_coordinate.AxialCoordinate
    >>> AVF = axisvalueflags.AxisValueFlags
    >>> flags = AVF(olderSiblingAttribute=True)
    >>> av1 = axisvalue_format1.AxisValue(nameID=267, value=0.12, flags=flags)
    >>> av2 = axisvalue_format3.AxisValue(nameID=51234, value=0.5, linkedValue=700, flags=flags)
    >>> avs = axisvalues.AxisValues([av1, av2])
    >>> ar = AxisRecord(nameID=259, ordering=0, axisValues=avs)
    >>> ar.pprint()
    Designation in the 'name' table: 259
    Ordering: 0
    Axis Values:
      0:
        Flags:
          Older Sibling Font Attribute: False
          Elidable Axis Value Name: False
        Designation in the 'name' table: 267
        Value: 0.12
      1:
        Flags:
          Older Sibling Font Attribute: False
          Elidable Axis Value Name: False
        Designation in the 'name' table: 51234
        Value: 0.5
        Linked Value: 700

    >>> ed = utilities.fakeEditor(100, name=True)
    >>> logger = utilities.makeDoctestLogger("test", level="WARNING")
    >>> ar.isValid(editor=ed, logger=logger)
    test - ERROR - AxisRecord nameID 259 not found in the font's 'name' table.
    test.axisValues.[0] - ERROR - NameID 267 not found in the font's 'name' table.
    test.axisValues.[1] - ERROR - NameID 51234 not found in the font's 'name' table.
    test.axisValues.[1] - ERROR - NameID 51234 is not between 255 and 32768.
    test.nameID - ERROR - Name table index 259 not present in 'name' table.
    False
    """

    #
    # Class definition variables
    #

    objSpec = dict(
        obj_validatefunc_partial = _validate)

    attrSpec = dict(
        nameID = dict(
            attr_label = "Designation in the 'name' table",
            attr_initfunc = (lambda: 0),
            attr_renumbernamesdirect = True),

        ordering = dict(
            attr_label = "Ordering",
            attr_initfunc = (lambda: 0)),

        axisValues = dict(
            attr_label = "Axis Values",
            attr_followsprotocol = True,
            attr_initfunc = axisvalues.AxisValues))

    attrSorted = ('nameID', 'ordering', 'axisValues')

    #
    # Methods
    #

    # noinspection PyUnusedLocal
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the object to the specified writer.

        >>> s = "41 42 43 44 01 7F 00 01"
        >>> b = utilities.fromhex(s)
        >>> obj = AxisRecord.frombytes(b)
        >>> utilities.hexdump(obj.binaryString(axisTag='test'))
               0 | 7465 7374 017F 0001                      |test....        |
        """

        safe_tag = (kwArgs['axisTag'] + "    ")[0:4].encode('ascii')

        w.addString(safe_tag)
        w.add('H', self.nameID)
        w.add('H', self.ordering)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxisRecord object from the specified walker,
        doing source validation.

        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = "41 42 43 44 01 7F 00 01"
        >>> b = utilities.fromhex(s)
        >>> obj = AxisRecord.fromvalidatedbytes(b, logger=logger)
        test.axisrecord - DEBUG - Walker has 8 remaining bytes.
        >>> obj.nameID == 383
        True
        >>> obj.ordering == 1
        True

        >>> s = "95 42 43 44 01 7F 00 01"
        >>> b = utilities.fromhex(s)
        >>> obj = AxisRecord.fromvalidatedbytes(b, logger=logger)
        test.axisrecord - DEBUG - Walker has 8 remaining bytes.
        test.axisrecord - ERROR - Axis tag contains non-ASCII characters

        >>> obj = AxisRecord.fromvalidatedbytes(b'XYZ', logger=logger)
        test.axisrecord - DEBUG - Walker has 3 remaining bytes.
        test.axisrecord - ERROR - Insufficient bytes to read AxisRecord
        """

        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('axisrecord')
        else:
            logger = utilities.makeDoctestLogger('axisrecord')

        remaining_length = w.length()

        logger.debug((
          'V0001',
          (remaining_length,),
          "Walker has %d remaining bytes."))

        if remaining_length < 8:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes to read AxisRecord"))

            return None

        axisTag, nameID, ordering = w.unpack("4s2H")

        try:
            axisTag_ascii = axisTag.decode('ascii')
        except UnicodeDecodeError:
            logger.error((
              'V1085',
              (),
              "Axis tag contains non-ASCII characters"))

            return None

        r = cls(nameID=nameID, ordering=ordering)
        r._axisTag = axisTag_ascii

        return r


    # noinspection PyUnusedLocal
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker.

        >>> s = "41 42 43 44 01 7F 00 01"
        >>> b = utilities.fromhex(s)
        >>> obj = AxisRecord.frombytes(b)
        >>> obj.nameID == 383
        True
        >>> obj.ordering == 1
        True
        """

        axisTag, nameID, ordering = w.unpack("4s2H")
        r = cls(nameID=nameID, ordering=ordering)
        r._axisTag = axisTag.decode('ascii')

        return r


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.STAT import axial_coordinate
    from fontio3.STAT import axisvalueflags
    from fontio3.STAT import axisvalue_format1
    from fontio3.STAT import axisvalue_format3

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    if __debug__:
        _test()

