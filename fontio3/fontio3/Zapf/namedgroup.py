#
# namedgroup.py
#
# Copyright © 2010-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sets of glyph indices with an optional name.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import setmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_nameIndex(p, obj, label, **kwArgs):
    nameObj = kwArgs.get('nameTableObj')
    
    if nameObj is None:
        p.simple(obj, label=label)
    
    else:
        availKeys = {k for k in nameObj if k[-1] == obj}
        
        if not availKeys:
            p.simple(obj, label=label)
        
        else:
            if len(availKeys) == 1:
                k = availKeys.pop()
            else:
                k = sorted(availKeys)[0]
            
            s = "%s: %d ('%s')" % (label, obj, nameObj[k])
            p(s)

def _validate_nameIndex(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if obj is None:
        return True

    if (editor is None) or (not editor.reallyHas(b'name')):
        logger.error((
          'V0553',
          (),
          "Unable to validate nameIndex because the Editor and/or "
          "'name' table are missing or empty."))
        
        return False
    
    if not valassist.isFormat_H(obj, logger=logger, label="name index"):
        return False
    
    if not {k for k in editor.name if k[-1] == obj}:
        logger.error((
          'V0753',
          (obj,),
          "The index %d does not appear in the 'name' table."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class NamedGroup(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing 'Zapf' table NamedGroups. These are frozensets of
    glyph indices with the following attributes:
        
        isSubdivision   If True, this NamedGroup is a subdivision of a larger
                        grouping. This bit is set in the GroupInfo flags.
                        Default is False.
        
        nameIndex       An index into the 'name' table for the name associated
                        with this group or subgroup. Default is None.
    
    >>> fakeNameTable = {(1,0,0,290): "Ampersands"}
    >>> nm = namer.testingNamer()
    >>> nm.annotate = True
    >>> _testingValues[0].pprint(nameTableObj=fakeNameTable, namer=nm)
    xyz3 (glyph 2)
    xyz20 (glyph 19)
    afii60002 (glyph 97)
    Group name: 290 ('Ampersands')
    Group is a subdivision: True
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> _testingValues[0].isValid(logger=logger, editor=_fakeEditor(290))
    True
    
    >>> _testingValues[0].isValid(logger=logger, editor=_fakeEditor(200))
    val.nameIndex - ERROR - The index 290 does not appear in the 'name' table.
    False
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        set_showpresorted = True)
    
    attrSpec = dict(
        nameIndex = dict(
            attr_ignoreforbool = True,
            attr_label = "Group name",
            attr_pprintfunc = _pprint_nameIndex,
            attr_showonlyiffunc = (lambda n: n is not None),
            attr_validatefunc = _validate_nameIndex),
        
        isSubdivision = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: False),
            attr_label = "Group is a subdivision",
            attr_showonlyiftrue = True))
    
    attrSorted = ('nameIndex', 'isSubdivision')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the NamedGroup to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0122 0003 0002 0013  0061                |.".......a      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0003 0002 0013  0061                |.........a      |
        """
        
        w.add("H", self.nameIndex or 0)
        count = len(self)
        w.add("H", count)
        
        if count:
            w.addGroup("H", sorted(self))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new NamedGroup object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = NamedGroup.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.namedgroup - DEBUG - Walker has 10 remaining bytes.
        
        >>> obj = fvb(s[:-1], logger=logger)
        fvw.namedgroup - DEBUG - Walker has 9 remaining bytes.
        fvw.namedgroup - ERROR - The named groups are missing or incomplete.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("namedgroup")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        nameIndex, count = w.unpack("2H")
        
        if w.length() < 2 * count:
            logger.error((
              'V0754',
              (),
              "The named groups are missing or incomplete."))
            
            return None
        
        return cls(w.group("H", count), nameIndex=(nameIndex or None))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new NamedGroup object from the specified walker.
        
        >>> obj = _testingValues[0].__copy__()
        >>> obj.isSubdivision = False  # only handled at GroupInfo level
        >>> obj == NamedGroup.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[1]
        >>> obj == NamedGroup.frombytes(obj.binaryString())
        True
        """
        
        nameIndex = w.unpack("H") or None
        return cls(w.group("H", w.unpack("H")), nameIndex=nameIndex)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    def _fakeEditor(nameIndex):
        from fontio3.name import name
        
        e = utilities.fakeEditor(0x10000)
        e.name = name.Name({(1, 0, 0, nameIndex): "a name"})
        return e
    
    _testingValues = (
        NamedGroup({97, 2, 19}, nameIndex=290, isSubdivision=True),
        NamedGroup({97, 2, 19}),
        NamedGroup({}, nameIndex=289),
        NamedGroup({41, 42}, nameIndex=291, isSubdivision=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
