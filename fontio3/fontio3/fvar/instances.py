#
# instances.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Instances class needed for support of 'fvar' tables.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.fvar import instance_info

# -----------------------------------------------------------------------------

#
# Classes
#

class Instances(dict, metaclass=mapmeta.FontDataMetaclass):

    #
    # Class definition variables
    #

    mapSpec = dict(
        item_followsprotocol = True,
        item_renumbernamesdirectkeys = True)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the object to the specified writer.
        
        >>> AC = axial_coordinate.AxialCoordinate
        >>> II = instance_info.InstanceInfo
        >>> ii1 = II({'wdth': AC(3.2), 'wght': AC(1.0)})
        >>> ii2 = II({'wdth': AC(1.0), 'wght': AC(1.3)})
        >>> ii3 = II({'wdth': AC(1.0), 'wght': AC(0.62)})
        >>> i = Instances([(289, ii1), (293, ii2), (295, ii3)])
        >>> axisOrder = ['wdth', 'wght']
        >>> utilities.hexdump(i.binaryString(axisOrder=axisOrder))
               0 | 0121 0000 0003 3333  0001 0000 0125 0000 |.!....33.....%..|
              10 | 0001 0000 0001 4CCD  0127 0000 0001 0000 |......L..'......|
              20 | 0000 9EB8                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        for nameID in sorted(self):
            w.add('H', nameID)
            self[nameID].buildBinary(w, **kwArgs)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Fvar object from the specified walker,
        doing source validation.
        
        >>> bs = bytes.fromhex(
        ...   "012100000003333300010000012500000001000000014ccc012700000001"
        ...   "000000009eb7")
        >>> axisOrder = ['wdth', 'wght']
        >>> dExtras = {289: "Heavy", 293: "Medium", 295: "Light"}
        >>> e = utilities.fakeEditor(1000, name_extras=dExtras)
        >>> i = Instances.fromvalidatedbytes(
        ...   bs,
        ...   axisOrder = axisOrder,
        ...   instanceCount = 3,
        ...   editor = e)
        Instances - DEBUG - Walker has 36 remaining bytes.
        Instances.[0].InstanceInfo - DEBUG - Walker has 34 remaining bytes.
        Instances.[0].InstanceInfo.AxialCoordinate - DEBUG - Walker has 32 remaining bytes.
        Instances.[0].InstanceInfo.AxialCoordinate - DEBUG - Walker has 28 remaining bytes.
        Instances.[1].InstanceInfo - DEBUG - Walker has 22 remaining bytes.
        Instances.[1].InstanceInfo.AxialCoordinate - DEBUG - Walker has 20 remaining bytes.
        Instances.[1].InstanceInfo.AxialCoordinate - DEBUG - Walker has 16 remaining bytes.
        Instances.[2].InstanceInfo - DEBUG - Walker has 10 remaining bytes.
        Instances.[2].InstanceInfo.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        Instances.[2].InstanceInfo.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        >>> i.pprint()
        289:
          'wdth': 3.2
          'wght': 1.0
        293:
          'wdth': 1.0
          'wght': 1.3
        295:
          'wdth': 1.0
          'wght': 0.62
        
        >>> Instances.fromvalidatedbytes(
        ...   bs[:-1],
        ...   axisOrder = axisOrder,
        ...   instanceCount = 3,
        ...   editor = e)
        Instances - DEBUG - Walker has 35 remaining bytes.
        Instances - ERROR - Insufficient bytes (35) for Instances (minimum 36)
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('Instances')
        else:
            logger = utilities.makeDoctestLogger('Instances')

        remaining_length = w.length()
        
        logger.debug((
          'V0001',
          (remaining_length,),
          "Walker has %d remaining bytes."))

        axisOrder = kwArgs['axisOrder']
        axisCount = len(axisOrder)
        hasPSName = kwArgs.get('hasPSName', False)
        instCount = kwArgs['instanceCount']
        bytes_needed = ((6 if hasPSName else 4) + 4 * axisCount) * instCount
        
        if remaining_length < bytes_needed:
            logger.error((
              'V0004',
              (remaining_length, bytes_needed),
              "Insufficient bytes (%d) for Instances (minimum %d)"))
            
            return None
        
        e = kwArgs['editor']
    
        if e.reallyHas(b'name'):
            nameTable = e.name
    
        else:
            logger.error(('Vxxxx', (), "Font has no 'name' table."))
            return None
        
        # noinspection PyCallingNonCallable
        r = cls()
        fvw = instance_info.InstanceInfo.fromvalidatedwalker
        
        for i in range(instCount):
            nameID = w.unpack("H")
            
            if not nameTable.hasNameID(nameID):
                logger.error((
                  'Vxxxx',
                  (nameID,),
                  "The nameID %d does not appear in the font's 'name' table."))
                
                return None
            
            subLogger = logger.getChild("[%d]" % (i,))
            instanceInfo = fvw(w, logger=subLogger, **kwArgs)
            
            if instanceInfo is None:
                return None
            
            r[nameID] = instanceInfo
        
        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker. The
        following keyword arguments are used:
        
            axisOrder       A required sequence with 4-byte strings
                            representing the axes. Note that this field is not
                            directly used in this method, but rather in the
                            InstanceInfo constructor.
            
            hasPSName       A required Boolean indicating whether the
                            InstanceRecord has the postscriptNameID field. Note
                            that this field is not directly used in this
                            method, but rather in the InstanceInfo constructor.
            
            instanceCount   The number of instances. This is required.
        
        >>> bs = bytes.fromhex(
        ...   "012100000003333300010000012500000001000000014ccc012700000001"
        ...   "000000009eb7")
        >>> axisOrder = ['wdth', 'wght']
        >>> dExtras = {289: "Heavy", 293: "Medium", 295: "Light"}
        >>> e = utilities.fakeEditor(1000, name_extras=dExtras)
        >>> i = Instances.frombytes(bs, axisOrder=axisOrder, instanceCount=3)
        >>> i.pprint(editor=e)
        289 ('Heavy'):
          'wdth': 3.2
          'wght': 1.0
        293 ('Medium'):
          'wdth': 1.0
          'wght': 1.3
        295 ('Light'):
          'wdth': 1.0
          'wght': 0.62
        """
        
        # noinspection PyCallingNonCallable
        r = cls()
        instanceCount = kwArgs.pop('instanceCount')
        fw = instance_info.InstanceInfo.fromwalker
        
        while instanceCount:
            nameID = w.unpack("H")
            instanceInfo = fw(w, **kwArgs)
            r[nameID] = instanceInfo
            instanceCount -= 1
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.fvar import axial_coordinate

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    if __debug__:
        _test()

