#
# groupinfo.py
#
# Copyright © 2010-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for GroupInfo structures in 'Zapf' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.Zapf import namedgroup

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    if len(obj) > 1:
        if not all(len(x) for x in obj[1:]):
            kwArgs['logger'].error((
              'V0756',
              (),
              "There is a zero-length NamedGroup in some position other "
              "than first in the array."))
            
            return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GroupInfo(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing single GroupInfo structures in a 'Zapf' table. These
    are tuples of NamedGroup objects.
    
    >>> nm = namer.testingNamer()
    >>> nm.annotate = True
    >>> n = {
    ...   (1, 0, 0, 289): "Ampersands",
    ...   (1, 0, 0, 290): "Classic",
    ...   (1, 0, 0, 291): "Modern"}
    >>> _testingValues[1].pprint(namer=nm, nameTableObj=n)
    NamedGroup #1:
      xyz3 (glyph 2)
      xyz20 (glyph 19)
      afii60002 (glyph 97)
    
    >>> _testingValues[2].pprint(namer=nm, nameTableObj=n)
    NamedGroup #1:
      Group name: 289 ('Ampersands')
    NamedGroup #2:
      xyz3 (glyph 2)
      xyz20 (glyph 19)
      afii60002 (glyph 97)
      Group name: 290 ('Classic')
      Group is a subdivision: True
    NamedGroup #3:
      xyz42 (glyph 41)
      xyz43 (glyph 42)
      Group name: 291 ('Modern')
      Group is a subdivision: True
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = _fakeEditor([289, 290, 291])
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    val - ERROR - There is a zero-length NamedGroup in some position other than first in the array.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "NamedGroup #%d" % (i + 1,)),
        seq_compactremovesfalses = True,
        seq_validatefunc_partial = _validate)

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GroupInfo object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 0003 0002  0013 0061           |...........a    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 8003 0000 0121 0000  8000 0122 0003 0002 |.....!....."....|
              10 | 0013 0061 8000 0123  0002 0029 002A      |...a...#...).*  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        needFlag = any(obj.isSubdivision for obj in self)
        w.add("H", len(self) + (0x8000 if needFlag else 0))
        
        for obj in self:
            if needFlag:
                w.add("H", (0x8000 if obj.isSubdivision else 0))
            
            obj.buildBinary(w)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GroupInfo object from the data in the
        specified walker.
        
        >>> s = _testingValues[2].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = GroupInfo.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.groupinfo - DEBUG - Walker has 30 remaining bytes.
        fvw.groupinfo.group 0.namedgroup - DEBUG - Walker has 26 remaining bytes.
        fvw.groupinfo.group 1.namedgroup - DEBUG - Walker has 20 remaining bytes.
        fvw.groupinfo.group 2.namedgroup - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        fvw.groupinfo - DEBUG - Walker has 1 remaining bytes.
        fvw.groupinfo - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        fvw.groupinfo - DEBUG - Walker has 29 remaining bytes.
        fvw.groupinfo.group 0.namedgroup - DEBUG - Walker has 25 remaining bytes.
        fvw.groupinfo.group 1.namedgroup - DEBUG - Walker has 19 remaining bytes.
        fvw.groupinfo.group 2.namedgroup - DEBUG - Walker has 7 remaining bytes.
        fvw.groupinfo.group 2.namedgroup - ERROR - The named groups are missing or incomplete.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("groupinfo")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        numGroups = w.unpack("H")
        
        if numGroups & 0x4000:
            logger.error((
              'V0002',
              (),
              "A GroupInfoGroup was encountered instead of a GroupInfo."))
            
            return False
        
        hasFlagWord = bool(numGroups & 0x8000)
        numGroups &= 0x3FFF
        v = []
        fvw = namedgroup.NamedGroup.fromvalidatedwalker
        
        for i in range(numGroups):
            itemLogger = logger.getChild("group %d" % (i,))
            
            if hasFlagWord:
                if w.length() < 2:
                    itemLogger.error((
                      'V0755',
                      (),
                      "The group flags are missing or incomplete."))
                    
                    return None
                
                flags = w.unpack("H")
            
            else:
                flags = 0
            
            ng = fvw(w, logger=itemLogger, **kwArgs)
            
            if ng is None:
                return None
            
            if len(ng) == 0 and i > 0:
                logger.error((
                  'V0756',
                  (),
                  "There is a zero-length NamedGroup in some position other "
                  "than first in the array."))
                
                return None
            
            if flags & 0x8000:
                ng.isSubdivision = True
            
            if len(ng) or (ng.nameIndex is not None):
                v.append(ng)
            
            if flags & 0x4000:
                w.align(4)
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GroupInfo object from the data in the
        specified walker.
        
        >>> for i in range(1, 3):
        ...   obj = _testingValues[i]
        ...   print(obj == GroupInfo.frombytes(obj.binaryString()))
        True
        True
        """
        
        numGroups = w.unpack("H")
        
        if numGroups & 0x4000:
            raise ValueError(
              "GroupInfoGroup walker passed to GroupInfo.fromwalker!")
        
        hasFlagWord = bool(numGroups & 0x8000)
        numGroups &= 0x3FFF
        v = []
        
        for i in range(numGroups):
            flags = (w.unpack("H") if hasFlagWord else 0)
            ng = namedgroup.NamedGroup.fromwalker(w)
            
            if len(ng) == 0 and i > 0:
                raise ValueError(
                  "Cannot have zero-length NamedGroup after first!")
            
            if flags & 0x8000:
                ng.isSubdivision = True
            
            if len(ng) or (ng.nameIndex is not None):
                v.append(ng)
            
            if flags & 0x4000:
                w.align(4)
        
        return cls(v)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    def _fakeEditor(nameIndices):
        from fontio3.name import name
        
        e = utilities.fakeEditor(0x10000)
        e.name = name.Name()
        
        for n in nameIndices:
            e.name[(1, 0, 0, n)] = "a name"
        
        return e
    
    _ngv = namedgroup._testingValues
    
    _testingValues = (
        GroupInfo(),
        GroupInfo([_ngv[1]]),
        GroupInfo([_ngv[2], _ngv[0], _ngv[3]]),
        
        # bad entries start here
        
        GroupInfo([_ngv[0], _ngv[2], _ngv[3]]))
    
    del _ngv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
