#
# axisvalues.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sequences of AxisValues as found in the STAT table.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.STAT import axisvalue_format1
from fontio3.STAT import axisvalue_format2
from fontio3.STAT import axisvalue_format3

# -----------------------------------------------------------------------------

#
# Private Constatns
#

_avmakers = {
  1: axisvalue_format1.AxisValue.fromwalker,
  2: axisvalue_format2.AxisValue.fromwalker,
  3: axisvalue_format3.AxisValue.fromwalker}

_avvalidatedmakers = {
  1: axisvalue_format1.AxisValue.fromvalidatedwalker,
  2: axisvalue_format2.AxisValue.fromvalidatedwalker,
  3: axisvalue_format3.AxisValue.fromvalidatedwalker}

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class AxisValues(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing sequences of AxisValue entries in a STAT table.

    >>> av1 = axisvalue_format1.AxisValue(nameID=555, value=1.1)
    >>> obj = AxisValues([av1])
    >>> obj.pprint()
    0:
      Flags:
        Older Sibling Font Attribute: False
        Elidable Axis Value Name: False
      Designation in the 'name' table: 555
      Value: 1.1
    """

    #
    # Class definition variables
    #

    seqSpec = dict(
        item_followsprotocol = True)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the object to the specified writer.
        
        >>> AC = axial_coordinate.AxialCoordinate
        >>> av1 = axisvalue_format1.AxisValue(nameID=555, value=AC(1.1))
        >>> avs = AxisValues([av1])
        >>> utilities.hexdump(avs.binaryString(axisIndex=4))
               0 | 0001 0004 0000 022B  0001 199A           |.......+....    |
        """
        for obj in self:
            obj.buildBinary(w, **kwArgs)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker,
        doing source validation.

        requires kwArg 'axisValueCount'

        >>> s = "00 01 00 04 00 00 02 2B 00 01 19 9A"
        >>> b = utilities.fromhex(s)
        >>> logger = utilities.makeDoctestLogger('test')
        >>> obj = AxisValues.fromvalidatedbytes(b, logger=logger, axisValueCount=1)
        test.axisvalues - DEBUG - Walker has 12 remaining bytes.
        test.axisvalues.axisvalue_format1 - DEBUG - Walker has 12 remaining bytes.
        test.axisvalues.axisvalue_format1.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.

        >>> s = "00 21 00 04 00 00 02 2B 00 01 19 9A"
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValues.fromvalidatedbytes(b, logger=logger, axisValueCount=1)
        test.axisvalues - DEBUG - Walker has 12 remaining bytes.
        test.axisvalues - ERROR - Unknown AxisValueTable format 33
        """

        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('axisvalues')
        else:
            logger = utilities.makeDoctestLogger('axisvalues')

        axisValueCount = kwArgs['axisValueCount']

        remaining_length = w.length()

        logger.debug((
          'V0001',
          (remaining_length,),
          "Walker has %d remaining bytes."))

        r = cls()

        for avi in range(axisValueCount):
            format = w.unpack("H", advance=False)  # sniff format for maker
            fvw = _avvalidatedmakers.get(format)
            if fvw is None:
                logger.error((
                  'V1082',
                  (format,),
                  "Unknown AxisValueTable format %d"))

                return None

            else:
                r.append(fvw(w, logger=logger))

        return r

    # noinspection PyUnusedLocal
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker.

        requires kwArg 'axisValueCount'

        >>> s = "00 01 00 04 00 00 02 2B 00 01 19 9A"
        >>> b = utilities.fromhex(s)
        >>> obj = AxisValues.frombytes(b, axisValueCount=1)
        """

        r = cls()

        axisValueCount = kwArgs['axisValueCount']

        for avi in range(axisValueCount):
            format = w.unpack("H", advance=False)  # sniff format for maker
            fw = _avmakers.get(format, None)
            if fw is not None:  # only add if we know the format
                r.append(fw(w, **kwArgs))

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.STAT import axial_coordinate, axisvalue_format1

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    if __debug__:
        _test()

