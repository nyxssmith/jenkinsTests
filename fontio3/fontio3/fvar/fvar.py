#
# fvar.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for AAT (and GX (and now OpenType)) 'fvar' tables.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.fvar import axis_info, instances
from fontio3.opentype import version as otversion
from fontio3.utilities import inRangeForAxis, isValidAxisTag

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(d, **kwArgs):
    editor = kwArgs['editor']
    logger = kwArgs['logger']
    isOK = True
    
    # axis infos
    for tag, axisInfo in sorted(d.items()):

        if isValidAxisTag(tag, registeredOnly=True):
            logger.info((
              'Vxxxx',
              (tag,),
              "'%s' is a registered axis tag."))

        elif not isValidAxisTag(tag):
            logger.error((
              'V1079',
              (tag,),
              "'%s' is neither a registered axis tag "
              "nor a valid private tag."))

            isOK = False

        # check values against spec requirements
        for attr in ('minValue', 'defaultValue', 'maxValue'):
            v = getattr(axisInfo, attr)
            if inRangeForAxis(v, tag):
                logger.info((
                  'V1080',
                  (attr, v, tag),
                  "%s %s is in range for '%s' axis"))

            else:
                logger.error((
                  'V1081',
                  (attr, v, tag),
                  "%s %s is out of range for '%s' axis"))
                  
                isOK = False

        # special check for 'wdth' axis
        if tag == 'wdth':
            if axisInfo.maxValue <= 10:
                logger.warning((
                  'Vxxxx',
                  (),
                  "Width ('wdth') axis appears to use OS/2 logarithmic (1..10) "
                  "scale instead of expected percentage-of-normal scale."))
                # not an error, though...

    # instances
    if not d.instances:
        logger.warning((
          'Vxxxx',
          (),
          "No named instances defined. Font may "
          "not work correctly in some applications."))
        # also not an error...

    for axk, instance in sorted(d.instances.items()):
        instname = editor.name.getNameFromID(axk, None)
        
        if instname is None:
            logger.error((
              'Vxxxx',
              (axk,),
              "Name ID %d for instance not found in name table."))

            isOK = False
        
        for axtag, acv in instance.items():
            axinfo = d[axtag]
            if not (axinfo.minValue <= acv <= axinfo.maxValue):
                logger.error((
                  'Vxxxx',
                  (instname, acv, axtag, axinfo.minValue, axinfo.maxValue),
                  "Instance '%s' value %s is out-of-range for %s axis (%s, %s)"))

                isOK = False

    return isOK


def _validate_axisOrder(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.error((
          'Vxxxx',
          (),
          "No axes defined!"))
        
        return False
    
    if not all(isinstance(x, str) and len(x) == 4 for x in obj):
        logger.error((
          'Vxxxx',
          (obj,),
          "One or more axis values in the axisOrder list %s are either "
          "not strings, or are not exactly 4 bytes long."))
        
        return False
    
    # Since 'fvar' is the pivotal table for defining the axes, we don't do
    # checks of other tables; instead, those tables will check against our
    # axisOrder list for consistency.
    
    return True


# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Fvar(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'fvar' tables. These are dicts whose keys are
    axis tag strings (not bytes), and whose values are AxisInfo objects. There
    are attributes containing the axial order and any instances, as well.

    >>> obj = Fvar()
    >>> ed = utilities.fakeEditor(5, name=True)
    >>> AC = axial_coordinate.AxialCoordinate
    >>> logger = utilities.makeDoctestLogger("test")
    >>> obj.isValid(editor=ed, logger=logger)
    test - WARNING - No named instances defined. Font may not work correctly in some applications.
    True

    >>> ai = axis_info.AxisInfo(maxValue=AC(0), minValue=AC(1), defaultValue=AC(0.5))
    >>> obj['wdth'] = ai
    >>> logger.logger.setLevel("WARNING")
    >>> obj.isValid(editor=ed, logger=logger)
    test - ERROR - maxValue 0.0 is out of range for 'wdth' axis
    test - WARNING - Width ('wdth') axis appears to use OS/2 logarithmic (1..10) scale instead of expected percentage-of-normal scale.
    test - WARNING - No named instances defined. Font may not work correctly in some applications.
    test.['wdth'] - ERROR - The [min, default, max] values of [1.0, 0.5, 0.0] are not in order.
    False

    >>> logger.logger.setLevel("ERROR")
    >>> ai = axis_info.AxisInfo(maxValue=AC(200), minValue=AC(50), defaultValue=AC(100))
    >>> obj['wdth'] = ai
    >>> ii = instance_info.InstanceInfo({'wdth': AC(900)})
    >>> i = instances.Instances([(289, ii), ])
    >>> obj.instances=i
    >>> obj.isValid(editor=ed, logger=logger)
    test - ERROR - Name ID 289 for instance not found in name table.
    test - ERROR - Instance 'None' value 900.0 is out-of-range for wdth axis (50.0, 200.0)
    test.instances.[289] - ERROR - Name table index 289 not present in 'name' table.
    False

    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        map_validatefunc_partial = _validate)

    attrSpec = dict(
        version = dict(
            attr_followsprotocol = True,
            attr_initfunc = otversion.Version,
            attr_label = 'Version'),
        
        instances = dict(
            attr_followsprotocol = True,
            attr_initfunc = instances.Instances,
            attr_label = 'Instances'),
        
        axisOrder = dict(
            attr_label = 'Axis Order',
            attr_validatefunc = _validate_axisOrder))

    attrSorted = ('version', 'instances')

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the object to the specified writer.
        
        >>> axisOrder = ['wdth', 'wght']
        >>> AC = axial_coordinate.AxialCoordinate
        >>> AI = axis_info.AxisInfo
        >>> ai1 = AI(AC(0.48), AC(1.0), AC(3.2), 0, 257)
        >>> ai2 = AI(AC(0.62), AC(1.0), AC(1.3), 0, 258)
        >>> k = {'flags': 0, 'axisOrder': axisOrder}
        >>> II = instance_info.InstanceInfo
        >>> ii1 = II({'wdth': AC(3.2), 'wght': AC(1.0)}, **k)
        >>> ii2 = II({'wdth': AC(1.0), 'wght': AC(1.3)}, **k)
        >>> ii3 = II({'wdth': AC(1.0), 'wght': AC(0.62)}, **k)
        >>> i = instances.Instances([(289, ii1), (293, ii2), (295, ii3)])
        >>> f = Fvar({'wght': ai1, 'wdth': ai2}, instances=i, axisOrder=axisOrder)
        >>> utilities.hexdump(f.binaryString())
               0 | 0001 0000 0010 0002  0002 0014 0003 000C |................|
              10 | 7764 7468 0000 9EB8  0001 0000 0001 4CCD |wdth..........L.|
              20 | 0000 0102 7767 6874  0000 7AE1 0001 0000 |....wght..z.....|
              30 | 0003 3333 0000 0101  0121 0000 0003 3333 |..33.....!....33|
              40 | 0001 0000 0125 0000  0001 0000 0001 4CCD |.....%........L.|
              50 | 0127 0000 0001 0000  0000 9EB8           |.'..........    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        offsetToData = 0x10
        countSizePairs = 2
        axisCount = len(self)
        axisSize = 20
        instanceCount = len(self.instances)
        instanceSize = 4 + 4 * axisCount
        self.version.buildBinary(w)
        w.add('H', offsetToData)
        w.add('H', countSizePairs)
        w.add('H', axisCount)
        w.add('H', axisSize)
        w.add('H', instanceCount)
        w.add('H', instanceSize)
        
        for axisTag in self.axisOrder:
            w.add('4s', axisTag.encode('ascii'))
            axisInfo = self[axisTag]
            axisInfo.buildBinary(w, **kwArgs)
        
        self.instances.buildBinary(w, axisOrder=self.axisOrder, **kwArgs)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Fvar object from the specified walker,
        doing source validation.
        
        >>> dExtras = {289: "Heavy", 293: "Medium", 295: "Light", 258: "Width", 257: "Weight"}
        >>> e = utilities.fakeEditor(1000, name_extras=dExtras)
        >>> f = Fvar.fromvalidatedbytes(_test_str, editor=e)
        fvar.version - DEBUG - Walker has 92 remaining bytes.
        fvar.AxisInfo - DEBUG - Walker has 72 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 72 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 68 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 64 remaining bytes.
        fvar.AxisInfo - DEBUG - Walker has 52 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 52 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 48 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 44 remaining bytes.
        fvar.Instances - DEBUG - Walker has 36 remaining bytes.
        fvar.Instances.[0].InstanceInfo - DEBUG - Walker has 34 remaining bytes.
        fvar.Instances.[0].InstanceInfo.AxialCoordinate - DEBUG - Walker has 32 remaining bytes.
        fvar.Instances.[0].InstanceInfo.AxialCoordinate - DEBUG - Walker has 28 remaining bytes.
        fvar.Instances.[1].InstanceInfo - DEBUG - Walker has 22 remaining bytes.
        fvar.Instances.[1].InstanceInfo.AxialCoordinate - DEBUG - Walker has 20 remaining bytes.
        fvar.Instances.[1].InstanceInfo.AxialCoordinate - DEBUG - Walker has 16 remaining bytes.
        fvar.Instances.[2].InstanceInfo - DEBUG - Walker has 10 remaining bytes.
        fvar.Instances.[2].InstanceInfo.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        fvar.Instances.[2].InstanceInfo.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        >>> f.pprint(editor=e)
        'wdth':
          Minimum style coordinate: 0.62
          Default style coordinate: 1.0
          Maximum style coordinate: 1.3
          Designation in the 'name' table: 258 ('Width')
        'wght':
          Minimum style coordinate: 0.48
          Default style coordinate: 1.0
          Maximum style coordinate: 3.2
          Designation in the 'name' table: 257 ('Weight')
        Version:
          Major version: 1
          Minor version: 0
        Instances:
          289 ('Heavy'):
            'wdth': 1.0
            'wght': 3.2
          293 ('Medium'):
            'wdth': 1.3
            'wght': 1.0
          295 ('Light'):
            'wdth': 0.62
            'wght': 1.0
        
        >>> f2 = Fvar.fromvalidatedbytes(_test_str[:-41], editor=e)
        fvar.version - DEBUG - Walker has 51 remaining bytes.
        fvar.AxisInfo - DEBUG - Walker has 31 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 31 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 27 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 23 remaining bytes.
        fvar.AxisInfo - DEBUG - Walker has 11 remaining bytes.
        fvar.AxisInfo - ERROR - Insufficient bytes (11) for AxisInfo (minimum 16)
        
        >>> f3 = Fvar.fromvalidatedbytes(_test_str[:-11], editor=e)
        fvar.version - DEBUG - Walker has 81 remaining bytes.
        fvar.AxisInfo - DEBUG - Walker has 61 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 61 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 57 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 53 remaining bytes.
        fvar.AxisInfo - DEBUG - Walker has 41 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 41 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 37 remaining bytes.
        fvar.AxisInfo.AxialCoordinate - DEBUG - Walker has 33 remaining bytes.
        fvar.Instances - DEBUG - Walker has 25 remaining bytes.
        fvar.Instances - ERROR - Insufficient bytes (25) for Instances (minimum 36)
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('fvar')
        else:
            logger = utilities.makeDoctestLogger('fvar')

        #remaining_length = w.length()
        version = otversion.Version.fromvalidatedwalker(w, logger=logger)
        
        if version is None:
            return None
        
        if (version.major != 1) or (version.minor != 0):
            logger.error((
              'V0002',
              (version,),
              "Was expecting version 1.0, but got %f instead."))
            
            return None

        # noinspection PyCallingNonCallable
        r = cls()
        r.version = version
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        t = w.unpack("6H")
        offsetToData, countSizePairs, axisCount = t[0:3]
        axisSize, instanceCount, instanceSize = t[3:6]
        
        if countSizePairs != 2:
            logger.error((
              'V1022',
              (countSizePairs,),
              "Unexpected value for countSizePairs: %d (expected 2)"))
            
            return None
        
        if axisSize != 20:
            logger.error((
              'V1023',
              (axisSize,),
              "Unexpected value for axisSize: %d (expected 20)"))
            
            return None
        
        expected_withpsname = (axisCount * 4) + 6
        expected_nopsname = (axisCount * 4) + 4
                
        if instanceSize not in (expected_withpsname, expected_nopsname):
            logger.error((
              'V1024',
              (axisSize, expected_withpsname, expected_nopsname),
              "Unexpected value for instanceSize: %d (expected either %d or %d)"))
            
            return None

        count = axisCount
        r.axisOrder = []
        fvw = axis_info.AxisInfo.fromvalidatedwalker
        
        while count:
            axisTag = str(w.unpack('4s'), 'ascii')
            r.axisOrder.append(axisTag)
            axisInfo = fvw(w, logger=logger, **kwArgs)
            
            if axisInfo is None:
                return None
            
            r[axisTag] = axisInfo
            count -= 1

        r.instances = instances.Instances.fromvalidatedwalker(
          w,
          axisOrder = r.axisOrder,
          instanceCount = instanceCount,
          hasPSName = instanceSize==expected_withpsname,
          logger = logger,
          **kwArgs)
       
        if r.instances is None:
            return None

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Fvar object from the specified walker.
        
        >>> dExtras = {289: "Heavy", 293: "Medium", 295: "Light", 258: "Width", 257: "Weight"}
        >>> e = utilities.fakeEditor(1000, name_extras=dExtras)
        >>> f = Fvar.frombytes(_test_str, editor=e)
        >>> f.pprint(editor=e)
        'wdth':
          Minimum style coordinate: 0.62
          Default style coordinate: 1.0
          Maximum style coordinate: 1.3
          Designation in the 'name' table: 258 ('Width')
        'wght':
          Minimum style coordinate: 0.48
          Default style coordinate: 1.0
          Maximum style coordinate: 3.2
          Designation in the 'name' table: 257 ('Weight')
        Version:
          Major version: 1
          Minor version: 0
        Instances:
          289 ('Heavy'):
            'wdth': 1.0
            'wght': 3.2
          293 ('Medium'):
            'wdth': 1.3
            'wght': 1.0
          295 ('Light'):
            'wdth': 0.62
            'wght': 1.0
        """
        
        version = otversion.Version.fromwalker(w)
        
        if (version.major != 1) or (version.minor != 0):
            raise ValueError("Unknown 'fvar' version: %f" % (version,))

        # noinspection PyCallingNonCallable
        r = cls()
        r.version = version
        offsetToAxesArray, countSizePairs = w.unpack("2H")
        
        # If the version bumps and countSizePairs increases, change the
        # following test and error.
        
        if countSizePairs != 2:
            s = "The countSizePairs value %d is incorrect; it should be 2."
            raise ValueError(s % (countSizePairs,))
        
        t = w.group("2H", countSizePairs)
        axisCount, axisSize = t[0]
        instanceCount, instanceSize = t[1]
        wSub = w.subWalker(offsetToAxesArray)
        ao = []
        count = axisCount
        fw = axis_info.AxisInfo.fromwalker
        
        while count:
            axisTag = str(wSub.unpack('4s'), 'ascii')
            ao.append(axisTag)
            r[axisTag] = fw(wSub)
            count -= 1
        
        r.axisOrder = tuple(ao)
        hasPSName = (instanceSize == ((len(ao) * 4) + 6))

        r.instances = instances.Instances.fromwalker(
          wSub,
          axisOrder = r.axisOrder,
          instanceCount = instanceCount,
          hasPSName = hasPSName,
          **kwArgs)

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities.walker import StringWalker
    from fontio3.fvar import axial_coordinate, instance_info, instances

    _test_str = bytes([
      0x00, 0x01, 0x00, 0x00, 0x00, 0x10, 0x00, 0x02, 0x00, 0x02, 0x00, 0x14,
      0x00, 0x03, 0x00, 0x0C, 0x77, 0x67, 0x68, 0x74, 0x00, 0x00, 0x7A, 0xE1,
      0x00, 0x01, 0x00, 0x00, 0x00, 0x03, 0x33, 0x33, 0x00, 0x00, 0x01, 0x01,
      0x77, 0x64, 0x74, 0x68, 0x00, 0x00, 0x9E, 0xB8, 0x00, 0x01, 0x00, 0x00,
      0x00, 0x01, 0x4C, 0xCD, 0x00, 0x00, 0x01, 0x02, 0x01, 0x21, 0x00, 0x00,
      0x00, 0x03, 0x33, 0x33, 0x00, 0x01, 0x00, 0x00, 0x01, 0x25, 0x00, 0x00,
      0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x4C, 0xCD, 0x01, 0x27, 0x00, 0x00,
      0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x9E, 0xB8])

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
