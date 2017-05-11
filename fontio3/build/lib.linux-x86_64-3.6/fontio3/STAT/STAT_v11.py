#
# STAT_v11.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the STAT table.
"""

# System imports
import logging
import re

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.opentype import version as otversion
from fontio3.STAT import axisrecord
from fontio3.STAT import axisvalues
from fontio3.utilities import inRangeForAxis, isValidAxisTag

# -----------------------------------------------------------------------------

#
# Private constants
#

_v1_1_DESIGN_AXIS_SIZE = 8

_axisValueAttrs = ('value', 'linkedValue', 'nominalValue',
                   'rangeMinValue', 'rangeMaxValue')

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(d, **kwArgs):
    """
    Full validation of the STAT table and all subtables.
    """
    logger = kwArgs.pop('logger')

    isOK = True

    for tag, axisRec in sorted(d.items()):

        if isValidAxisTag(tag, registeredOnly=True):
            logger.info((
              'V1091',
              (tag,),
              "'%s' is a registered axis tag."))

        elif isValidAxisTag(tag, minimallyValid=True):
            logger.warning((
              'Vxxxx',
              (tag,),
              "'%s' is not a registered axis tag."))

        else:
            logger.error((
              'V1079',
              (tag,),
              "'%s' is neither a registered axis tag "
              "nor a valid private tag."))

            isOK = False

        # check values against spec requirements.
        for avi, axisVal in enumerate(axisRec.axisValues):

            for attr in _axisValueAttrs:
                v = getattr(axisVal, attr, None)

                if v is not None:

                    if inRangeForAxis(v, tag):
                        logger.info((
                          'V1080',
                          (attr, v, tag),
                          "%s %s is in range for axis '%s'"))
                    else:
                        logger.error((
                          'V1081',
                          (attr, v, tag),
                          "%s %s is out of range for axis '%s'"))
                          
                        isOK = False

    # check that elidedFallbackNameID is present in the 'name' table
    editor = kwArgs['editor']
    if editor.reallyHas(b'name'):
        nameTbl = editor.name
        efnid = d.elidedFallbackNameID
        efname = nameTbl.getNameFromID(efnid, None)
        if efname is None:
            logger.error((
              'V1104',
              (efnid,),
              "The elidedFallbackNameID %d is not present in the 'name' table."))
        else:
            logger.info((
              'V1104',
              (efnid, efname),
              "The elidedFallbackNameID is %d ('%s')"))

    else:
        logger.error((
          'Vxxxx',
          (),
          "The STAT table contents cannot be verified against the 'name' "
          "table because the name table is missing or damaged"))
        isOK = False

    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class STAT(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire STAT tables. These are dicts whose keys are
    axis tags and values are AxisRecords.

    >>> flags = axisvalueflags.AxisValueFlags()
    >>> AV1 = axisvalue_format1.AxisValue
    >>> AC = axial_coordinate.AxialCoordinate
    >>> av1 = AV1(value=AC(-34), nameID=2353, flags=flags)
    >>> avs = axisvalues.AxisValues([av1])
    >>> ar = axisrecord.AxisRecord(nameID=0x123, ordering=90, axisValues=avs)
    >>> obj = STAT({'wght': ar})
    >>> obj.pprint()
    'wght':
      Designation in the 'name' table: 291
      Ordering: 90
      Axis Values:
        0:
          Flags:
            Older Sibling Font Attribute: False
            Elidable Axis Value Name: False
          Designation in the 'name' table: 2353
          Value: -34.0
    Version:
      Major version: 1
      Minor version: 1
    ElidedFallbackNameID: 2
   
    >>> logger=utilities.makeDoctestLogger("test")
    >>> ed = utilities.fakeEditor(100, name=True)
    >>> obj.isValid(logger=logger, editor=ed)
    test - INFO - 'wght' is a registered axis tag.
    test - ERROR - value -34.0 is out of range for axis 'wght'
    test - INFO - The elidedFallbackNameID is 2 ('Regular')
    test.[wght] - ERROR - AxisRecord nameID 291 not found in the font's 'name' table.
    test.[wght].axisValues.[0] - ERROR - NameID 2353 not found in the font's 'name' table.
    test.[wght].nameID - ERROR - Name table index 291 not present in 'name' table.
    False

    >>> obj = STAT({'0Xft': ar}, elidedFallbackNameID=666)
    >>> logger.logger.setLevel("WARNING")
    >>> obj.isValid(editor=ed, logger=logger)
    test - ERROR - '0Xft' is neither a registered axis tag nor a valid private tag.
    test - ERROR - The elidedFallbackNameID 666 is not present in the 'name' table.
    test.[0Xft] - ERROR - AxisRecord nameID 291 not found in the font's 'name' table.
    test.[0Xft].axisValues.[0] - ERROR - NameID 2353 not found in the font's 'name' table.
    test.[0Xft].nameID - ERROR - Name table index 291 not present in 'name' table.
    False
    """

    #
    # Class definition variables
    #

    mapSpec = dict(
        item_ensurekeytype = str,
        item_followsprotocol = True,
        item_keyfollowsprotocol = True,
        item_pprintlabelpresort = True,
        map_validatefunc_partial = _validate)

    attrSpec = dict(
        version = dict(
            attr_followsprotocol = True,
            attr_initfunc = lambda: otversion.Version(minor=1),
            attr_label = 'Version'),
            
        elidedFallbackNameID = dict(
            attr_initfunc = lambda: 2,
            attr_label = 'ElidedFallbackNameID'))

    attrSorted = ('version', 'elidedFallbackNameID')

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the STAT to the specified walker.

        >>> obj = _testingValues[1]
        >>> s = obj.binaryString()
        >>> utilities.hexdump(s)
               0 | 0001 0001 0008 0002  0000 0014 0002 0000 |................|
              10 | 0024 0002 7465 7374  0123 0001 7767 6874 |.$..test.#..wght|
              20 | 0100 0000 0004 0010  0001 0000 0000 0931 |...............1|
              30 | FFDE 0000 0001 0001  0000 0931 FFDE 0000 |...........1....|
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        stake_tableStart = w.stakeCurrent()

        self.version.buildBinary(w)
        w.add("H", _v1_1_DESIGN_AXIS_SIZE)
        w.add("H", len(self))
        w.add("L", 20)  # size of header
        axisValueCount = sum([len(ar.axisValues) for ar in self.values()])
        w.add("H", axisValueCount)

        if axisValueCount:
            stake_endOfAxisRecords = w.getNewStake()
            w.addUnresolvedOffset("L", stake_tableStart, stake_endOfAxisRecords)
        else:
            w.add("L", 0)

        w.add("H", self.elidedFallbackNameID)

        allAxisValues = list()
        for i, (tag, ar) in enumerate(sorted(self.items())):
            ar.buildBinary(w, axisTag=tag, **kwArgs)
            for av in ar.axisValues:
                allAxisValues.append((i, av))

        if axisValueCount:
            w.stakeCurrentWithValue(stake_endOfAxisRecords)
        else:
            return  # end of table

        stake_AVOArrayStart = w.stakeCurrent()
        stakedict_AVOs = {}
        for i in range(len(allAxisValues)):
            stakedict_AVOs[i] = w.getNewStake()
            w.addUnresolvedOffset("H", stake_AVOArrayStart, stakedict_AVOs[i])

        aai = 0
        for ai, av in allAxisValues:
            w.stakeCurrentWithValue(stakedict_AVOs[aai])
            av.buildBinary(w, axisIndex=ai)
            aai += 1


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new STAT. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).

        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = ("00 01 00 01 00 08 00 01 00 00 00 14 00 01 00 00 "
        ...      "00 1C 00 02 74 65 73 74 01 23 00 01 00 02 00 01 "
        ...      "00 00 00 00 09 31 00 02 4C CD")
        >>> b = utilities.fromhex(s)
        >>> obj = STAT.fromvalidatedbytes(b, logger=logger)
        test.STAT - DEBUG - Walker has 42 remaining bytes.
        test.STAT.version - DEBUG - Walker has 42 remaining bytes.
        test.STAT - INFO - Version is 1.1
        test.STAT - INFO - 1 design axis
        test.STAT - INFO - Elided Fallback Name ID is 2
        test.STAT.axisrecord - DEBUG - Walker has 22 remaining bytes.
        test.STAT.axisvalues - DEBUG - Walker has 12 remaining bytes.
        test.STAT.axisvalues.axisvalue_format1 - DEBUG - Walker has 12 remaining bytes.
        test.STAT.axisvalues.axisvalue_format1.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.

        >>> obj.binaryString() == b
        True

        >>> obj = STAT.fromvalidatedbytes(b'XYZ', logger=logger)
        test.STAT - DEBUG - Walker has 3 remaining bytes.
        test.STAT - ERROR - Insufficient bytes

        >>> s = ("00 01 00 15 00 08 00 01 00 00 00 14 00 01 00 00 "
        ...      "00 1A 74 65 73 74 01 23 00 01 00 02 00 01 00 00 "
        ...      "00 00 09 31 00 02 4C CD")
        >>> b = utilities.fromhex(s)
        >>> obj = STAT.fromvalidatedbytes(b, logger=logger)
        test.STAT - DEBUG - Walker has 40 remaining bytes.
        test.STAT.version - DEBUG - Walker has 40 remaining bytes.
        test.STAT - ERROR - Expected version 1.1, but got Major version = 1, Minor version = 21 instead.

        >>> s = ("00 01 00 01 08 00 00 01 00 00 00 14 00 01 00 00 "
        ...      "00 1A 74 65 73 74 01 23 00 01 00 02 00 01 00 00 "
        ...      "00 00 09 31 00 02 4C CD")
        >>> b = utilities.fromhex(s)
        >>> obj = STAT.fromvalidatedbytes(b, logger=logger)
        test.STAT - DEBUG - Walker has 40 remaining bytes.
        test.STAT.version - DEBUG - Walker has 40 remaining bytes.
        test.STAT - INFO - Version is 1.1
        test.STAT - ERROR - Expected designAxisSize = 8 but got 2048 instead.

        >>> s = ("00 01 00 01 00 08 00 05 00 00 00 14 00 01 00 00 "
        ...      "00 1A 74 65 73 74 01 23 00 01 00 02 00 01 00 00 "
        ...      "00 00 09 31 00 02 4C CD")
        >>> b = utilities.fromhex(s)
        >>> obj = STAT.fromvalidatedbytes(b, logger=logger)
        test.STAT - DEBUG - Walker has 40 remaining bytes.
        test.STAT.version - DEBUG - Walker has 40 remaining bytes.
        test.STAT - INFO - Version is 1.1
        test.STAT - INFO - 5 design axes
        test.STAT - ERROR - Table is too short for the advertised number * size of design axes

        >>> s = ("00 01 00 01 00 08 00 01 00 00 00 14 00 00 00 00 "
        ...      "00 1C 00 02 74 65 73 74 01 23 00 01 00 02 00 01 "
        ...      "00 00 00 00 09 31 00 02 4C CD")
        >>> b = utilities.fromhex(s)
        >>> obj = STAT.fromvalidatedbytes(b, logger=logger)
        test.STAT - DEBUG - Walker has 42 remaining bytes.
        test.STAT.version - DEBUG - Walker has 42 remaining bytes.
        test.STAT - INFO - Version is 1.1
        test.STAT - INFO - 1 design axis
        test.STAT - WARNING - AxisValueTable count is zero
        test.STAT - INFO - Elided Fallback Name ID is 2
        test.STAT.axisrecord - DEBUG - Walker has 22 remaining bytes.
        test.STAT - WARNING - axisValueCount of zero with non-zero offsetToAxisValueOffsets

        >>> s = ("00 01 00 01 00 08 00 01 00 00 00 14 00 01 00 00 "
        ...      "00 1C 00 02 74 65 73 74 01 23 00 01 00 02 00 01 "
        ...      "02 00 00 00 09 31 00 02 4C CD")
        >>> b = utilities.fromhex(s)
        >>> obj = STAT.fromvalidatedbytes(b, logger=logger)
        test.STAT - DEBUG - Walker has 42 remaining bytes.
        test.STAT.version - DEBUG - Walker has 42 remaining bytes.
        test.STAT - INFO - Version is 1.1
        test.STAT - INFO - 1 design axis
        test.STAT - INFO - Elided Fallback Name ID is 2
        test.STAT.axisrecord - DEBUG - Walker has 22 remaining bytes.
        test.STAT.axisvalues - DEBUG - Walker has 12 remaining bytes.
        test.STAT.axisvalues.axisvalue_format1 - DEBUG - Walker has 12 remaining bytes.
        test.STAT.axisvalues.axisvalue_format1.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        test.STAT - ERROR - AxisValueTable[0] refers to out-of-range axis index 512
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('STAT')
        else:
            logger = logger.getChild('STAT')

        wholeTableLength = w.length()

        logger.debug((
          'V0001',
          (wholeTableLength,),
          "Walker has %d remaining bytes."))

        if wholeTableLength < 20:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None

        version = otversion.Version.fromvalidatedwalker(w, logger=logger)

        if version.major != 1 or version.minor != 1:
            logger.error((
              'V0002',
              (version,),
              "Expected version 1.1, but got %s instead."))

            return None

        else:
            logger.info((
              'V1076',
              (),
              "Version is 1.1"))

        designAxisSize, designAxisCount = w.unpack("2H")

        if designAxisSize != _v1_1_DESIGN_AXIS_SIZE:
            logger.error((
              'V1077',
              (designAxisSize,),
              "Expected designAxisSize = 8 but got %d instead."))

            return None

        logger.info((
          'Vxxxx',
          (designAxisCount, 'i' if designAxisCount==1 else 'e'),
          "%d design ax%ss"))

        offsetToDesignAxes = w.unpack("L")

        if designAxisSize * designAxisCount >= wholeTableLength:
            logger.error((
              'V0004',
              (),
              "Table is too short for the advertised number * size of design axes"))

            return None

        axisValueCount = w.unpack("H")
        
        if axisValueCount <= 0:
            logger.warning((
              'Vxxxx',
              (),
              "AxisValueTable count is zero"))

        offsetToAxisValueOffsets = w.unpack("L")

        if offsetToAxisValueOffsets > wholeTableLength:
            logger.error((
              'V0004',
              (offsetToAxisValueOffsets,),
              "Table is too short for offset to AxisValueOffsets %d"))

            return None

        if w.length() < 2:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes"))
            return None

        efnid = w.unpack("H")
        
        logger.info((
          'V1103',
          (efnid,),
          "Elided Fallback Name ID is %d"))

        r = cls(version=version, elidedFallbackNameID=efnid)

        w.setOffset(offsetToDesignAxes)
        axisrecords = w.group("4s2H", designAxisCount)  # pre-read to get tags
        w.setOffset(-(designAxisCount * _v1_1_DESIGN_AXIS_SIZE), relative=True)  # back up
        ARfvw = axisrecord.AxisRecord.fromvalidatedwalker
        origOrder = {}

        for i, (tag, nameID, ordering) in enumerate(axisrecords):
            tag_ascii = tag.decode('ascii')
            origOrder[i] = tag_ascii
            axisrec = ARfvw(w, logger=logger, **kwArgs)  # read validated
            r[tag_ascii] = axisrec

        if axisValueCount:
            # now process AxisValueTables and attach to our AxisRecords
            # according to their ._axisIndex
            AVRS = axisvalues.AxisValues
            w.setOffset(offsetToAxisValueOffsets)
            axisValueOffsets = w.group("H", axisValueCount)

            for oidx, o in enumerate(axisValueOffsets):
                w.setOffset(offsetToAxisValueOffsets + o)
                tmp = AVRS.fromvalidatedwalker(w, axisValueCount=1, logger=logger)
                if tmp and tmp[0] is not None:
                    axidx = tmp[0]._axisIndex
                    if axidx not in origOrder:
                        logger.error((
                          'V1078',
                          (oidx, axidx),
                          "AxisValueTable[%d] refers to out-of-range axis index %d"))
                    else:
                        axtag = origOrder.get(axidx)
                        r[axtag].axisValues.append(tmp[0])
        else:
            if offsetToAxisValueOffsets != 0:
                logger.warning((
                  'Vxxxx',
                  (),
                  "axisValueCount of zero with non-zero offsetToAxisValueOffsets"))

        return r


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new STAT object from the specified walker.

        >>> b = _testingValues[1].binaryString()
        >>> utilities.hexdump(b)
               0 | 0001 0001 0008 0002  0000 0014 0002 0000 |................|
              10 | 0024 0002 7465 7374  0123 0001 7767 6874 |.$..test.#..wght|
              20 | 0100 0000 0004 0010  0001 0000 0000 0931 |...............1|
              30 | FFDE 0000 0001 0001  0000 0931 FFDE 0000 |...........1....|
        >>> obj = STAT.frombytes(b)
        >>> obj == _testingValues[1]
        True
        """
        version = otversion.Version.fromwalker(w, **kwArgs)
        designAxisSize, designAxisCount = w.unpack("2H")
        offsetToDesignAxes = w.unpack("L")
        axisValueCount = w.unpack("H")
        offsetToAxisValueOffsets = w.unpack("L")
        efnid = w.unpack("H")

        r = cls(version=version, elidedFallbackNameID=efnid)

        w.setOffset(offsetToDesignAxes)
        axisrecords = w.group("4s2H", designAxisCount)
        w.setOffset(-(designAxisCount * _v1_1_DESIGN_AXIS_SIZE), relative=True)
        ARfw = axisrecord.AxisRecord.fromwalker
        origOrder = {}

        for i, (tag, nameID, ordering) in enumerate(axisrecords):
            tag_ascii = tag.decode('ascii')
            origOrder[i] = tag_ascii
            axisrec = ARfw(w, **kwArgs)
            r[tag_ascii] = axisrec

        if axisValueCount:
            # process AxisValueTables and attach to our AxisRecords by index
            AVRS = axisvalues.AxisValues
            w.setOffset(offsetToAxisValueOffsets)
            axisValueOffsets = w.group("H", axisValueCount)

            for o in axisValueOffsets:
                w.setOffset(offsetToAxisValueOffsets + o)
                tmp = AVRS.fromwalker(w, axisValueCount=1)
                if tmp and tmp[0] is not None:
                    axidx = tmp[0]._axisIndex
                    if axidx in origOrder:
                        axtag = origOrder.get(axidx)
                        r[axtag].axisValues.append(tmp[0])

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
    from fontio3.STAT import axisvalue_format2

    flags = axisvalueflags.AxisValueFlags()
    AV1 = axisvalue_format1.AxisValue
    AC = axial_coordinate.AxialCoordinate
    av1 = AV1(value=AC(-34), nameID=2353, flags=flags)
    avs = axisvalues.AxisValues([av1])
    ar = axisrecord.AxisRecord(nameID=0x123, ordering=1, axisValues=avs)
    ar2 = axisrecord.AxisRecord(nameID=0x100, ordering=0, axisValues=avs)

    _testingValues = (
        STAT(),
        STAT({'test': ar, 'wght': ar2}))


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
