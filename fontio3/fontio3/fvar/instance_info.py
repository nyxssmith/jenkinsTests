#
# instance_info.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
InstanceInfo class needed for support of 'fvar' tables.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.fvar import axial_coordinate

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate_flags(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if obj != 0:
        logger.error((
          'Vxxxx',
          (obj,),
          "The flags value should be zero, but is %s"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class InstanceInfo(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing Instances entries in an fvar table.
    
    >>> AC = axial_coordinate.AxialCoordinate
    >>> ii = InstanceInfo({'wdth': AC(0.5), 'wght': AC(1.0)})
    >>> ii.pprint()
    'wdth': 0.5
    'wght': 1.0
    
    >>> ii = InstanceInfo({'wdth': AC(0.3333333), 'wght': AC(0.9999999)})
    >>> ii.pprint()
    'wdth': 0.333
    'wght': 1.0
    
    Note that as of OpenType 1.8 a new field is allowed, the psNameID:
    
    >>> e = utilities.fakeEditor(1000, name=True)
    >>> ii.psNameID = 256
    >>> ii.pprint(editor=e)
    'wdth': 0.333
    'wght': 1.0
    Postscript name ID: 256 ('String 1')
    """

    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintdeep = False)

    attrSpec = dict(
        flags = dict(
            attr_label = "Flags",
            attr_initfunc = (lambda: 0),
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate_flags),
        
        psNameID = dict(
            attr_label = "Postscript name ID",
            attr_renumbernamesdirect = True,
            attr_showonlyiftrue = True))

    attrSorted = ('flags', 'psNameID')

    #
    # Methods
    #

    # noinspection PyUnusedLocal
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the object to the specified writer. The
        following keyword arguments are supported:
        
            axisOrder   A required sequence of axis tag strings.
            
            hasPSName   A Boolean (default False) indicating this is OT 1.8
                        or later.
        
        >>> AC = axial_coordinate.AxialCoordinate
        >>> ii = InstanceInfo({'wdth': AC(0.5), 'wght': AC(1.0)})
        >>> axisOrder=('wdth', 'wght')
        >>> dKW = {'axisOrder': axisOrder}
        >>> utilities.hexdump(ii.binaryString(**dKW))
               0 | 0000 0000 8000 0001  0000                |..........      |
        
        >>> ii.psNameID = 768
        >>> dKW['hasPSName'] = True
        >>> utilities.hexdump(ii.binaryString(**dKW))
               0 | 0000 0000 8000 0001  0000 0300           |............    |
        """

        axisOrder = kwArgs['axisOrder']
        w.add('H', self.flags)
        
        for axisTag in axisOrder:
            self[axisTag].buildBinary(w, **kwArgs)
        
        if kwArgs.get('hasPSName', False):
            w.add("H", self.psNameID or 0)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker, doing
        source validation. The following keyword arguments are supported:
        
            axisOrder   A required sequence of axis tag strings.
            
            editor      An Editor-class object, required if hasPSName is True,
                        and not required otherwise.
            
            hasPSName   A Boolean (default False) indicating this is OT 1.8
            
            logger      A logger (default is a standard doctest logger) to
                        which messages will be logged.
        
        >>> e = utilities.fakeEditor(1000, name=True)
        >>> bs = bytes.fromhex("00000000800000010000")
        >>> axisOrder = ('wdth', 'wght')
        >>> ii = InstanceInfo.fromvalidatedbytes(
        ...   bs,
        ...   axisOrder = axisOrder,
        ...   editor = e)
        InstanceInfo - DEBUG - Walker has 10 remaining bytes.
        InstanceInfo.AxialCoordinate - DEBUG - Walker has 8 remaining bytes.
        InstanceInfo.AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        >>> ii.pprint()
        'wdth': 0.5
        'wght': 1.0
        
        >>> ii2 = InstanceInfo.fromvalidatedbytes(bs[:-1], axisOrder=axisOrder)
        InstanceInfo - DEBUG - Walker has 9 remaining bytes.
        InstanceInfo - ERROR - Insufficient bytes (9) for InstanceInfo (minimum 10)
        
        >>> bs = bytes.fromhex("000000008000000100000100")
        >>> ii = InstanceInfo.fromvalidatedbytes(
        ...   bs,
        ...   axisOrder = axisOrder,
        ...   hasPSName = True,
        ...   editor = e)
        InstanceInfo - DEBUG - Walker has 12 remaining bytes.
        InstanceInfo.AxialCoordinate - DEBUG - Walker has 10 remaining bytes.
        InstanceInfo.AxialCoordinate - DEBUG - Walker has 6 remaining bytes.
        >>> ii.pprint(editor=e)
        'wdth': 0.5
        'wght': 1.0
        Postscript name ID: 256 ('String 1')
        
        >>> bs = bytes.fromhex("000000008000000100000180")
        >>> InstanceInfo.fromvalidatedbytes(
        ...   bs,
        ...   axisOrder = axisOrder,
        ...   hasPSName = True,
        ...   editor = e)
        InstanceInfo - DEBUG - Walker has 12 remaining bytes.
        InstanceInfo.AxialCoordinate - DEBUG - Walker has 10 remaining bytes.
        InstanceInfo.AxialCoordinate - DEBUG - Walker has 6 remaining bytes.
        InstanceInfo - ERROR - The postscriptNameID is given as 384, but that name does not appear in the font's 'name' table.
        """

        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('InstanceInfo')
        else:
            logger = utilities.makeDoctestLogger('InstanceInfo')

        remaining_length = w.length()
        
        logger.debug((
          'V0001',
          (remaining_length,),
          "Walker has %d remaining bytes."))

        axisOrder = kwArgs['axisOrder']
        hasPSName = kwArgs.get('hasPSName', False)
        count = len(axisOrder)
        bytes_needed = 2 + 4 * count  # already unpacked 2 bytes for nameID
        
        if hasPSName:
            bytes_needed += 2
        
        if remaining_length < bytes_needed:
            logger.error((
              'V0004',
              (remaining_length, bytes_needed),
              "Insufficient bytes (%d) for InstanceInfo (minimum %d)"))
            
            return None

        # noinspection PyCallingNonCallable
        r = cls()
        r.flags = w.unpack("H")
        fvw = axial_coordinate.AxialCoordinate.fromvalidatedwalker
        
        for axisTag in axisOrder:
            ac = fvw(w, logger=logger, **kwArgs)
            
            if ac is None:
                return None
            
            r[axisTag] = ac
        
        if hasPSName:
            e = kwArgs['editor']
        
            if e.reallyHas(b'name'):
                nameTable = e.name
        
            else:
                logger.error(('Vxxxx', (), "Font has no 'name' table."))
                return None
            
            r.psNameID = w.unpack("H")
            
            if not nameTable.hasNameID(r.psNameID):
                logger.error((
                  'Vxxxx',
                  (r.psNameID,),
                  "The postscriptNameID is given as %d, but that name "
                  "does not appear in the font's 'name' table."))
                
                return None
        
        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new object from the specified walker. The
        following keyword arguments are supported:
        
            axisOrder   A required sequence of axis tag strings.
            
            hasPSName   A Boolean (default False) indicating this is OT 1.8
        
        >>> bs = bytes.fromhex("00000000800000010000")
        >>> axisOrder = ('wdth', 'wght')
        >>> ii = InstanceInfo.frombytes(bs, axisOrder=axisOrder)
        >>> ii.pprint()
        'wdth': 0.5
        'wght': 1.0
        
        >>> bs = bytes.fromhex("000000008000000100000100")
        >>> axisOrder = ('wdth', 'wght')
        >>> ii = InstanceInfo.frombytes(bs, axisOrder=axisOrder, hasPSName=True)
        >>> e = utilities.fakeEditor(1000, name=True)
        >>> ii.pprint(editor=e)
        'wdth': 0.5
        'wght': 1.0
        Postscript name ID: 256 ('String 1')
        """

        axisOrder = kwArgs['axisOrder']
        # noinspection PyCallingNonCallable
        r = cls()
        r.flags = w.unpack("H")
        fw = axial_coordinate.AxialCoordinate.fromwalker
        
        for axisTag in axisOrder:
            r[axisTag] = fw(w, **kwArgs)
        
        if kwArgs.get('hasPSName', False):
            r.psNameID = w.unpack("H")
        
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

