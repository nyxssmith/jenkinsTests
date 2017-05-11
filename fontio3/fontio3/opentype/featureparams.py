#
# featureparams.py
#
# Copyright © 2007-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Put any classes defining feature params (for GPOS or GSUB tables) here.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta, setmeta, simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pf(p, n):
    if n < 0x10000:
        p("U+%04X" % (n,))
    else:
        p("U+%06X" % (n,))

def _validate_GPOS_size(obj, **kwArgs):
    logger = kwArgs['logger']
    r = endTestOK = True
    
    # Check the validity of the numeric values
    f = valassist.isNumber_integer_unsigned
    
    if not f(obj.designSize, numBits=16, label="design size", **kwArgs):
        r = False
    
    if not f(obj.smallRangeEnd, numBits=16, label="small end", **kwArgs):
        r = endTestOK = False
    
    if not f(obj.largeRangeEnd, numBits=16, label="large end", **kwArgs):
        r = endTestOK = False
    
    # Check the ordering of the small and large range ends
    
    if endTestOK and (obj.smallRangeEnd > obj.largeRangeEnd):
        logger.error((
          'V0315',
          (obj.smallRangeEnd, obj.largeRangeEnd),
          "The smallRangeEnd (%s) is greater than the largeRangeEnd (%s)."))
        
        r = False
    
    return r

def _validate_GSUB_ssxx(obj, **kwArgs):
    logger = kwArgs['logger']
    f = valassist.isNumber_integer_unsigned
    
    if obj.version != 0:
        logger.error((
          'Vxxxx',
          (obj.version,),
          "Version must be zero, but is %d."))
        
        return False
    
    return True

def _validate_nameList(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if len(obj) > 1:
        if list(obj) != list(range(min(obj), min(obj) + len(obj))):
            logger.error((
              'Vxxxx',
              (list(obj),),
              "The FeatureParam_GSUB_cvxx_NameList must be monotonic "
              "but the data %s are not."))
            
            return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureParam_GPOS_size(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing FeatureParams for 'size' GPOS features. These are
    simple collections of the following 5 attributes (for details on how these
    are used in living fonts, see the OpenType Layout tag registry):
    
        designSize
        subFamily
        nameTableIndex
        smallRangeEnd
        largeRangeEnd
    
    >>> _testingValues[0].pprint()
    Design size in decipoints: 60
    Subfamily value: 0
    
    >>> e = _fakeEditor(300)
    >>> _testingValues[1].pprint(editor=e)
    Design size in decipoints: 80
    Subfamily value: 4
    Name table index of common subfamily: 300 ('Test string')
    Small end of usage range in decipoints: 80
    Large end of usage range in decipoints: 120
    
    >>> logger = utilities.makeDoctestLogger("test")
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    test - ERROR - The smallRangeEnd (180) is greater than the largeRangeEnd (120).
    test.nameTableIndex - ERROR - Name table index 250 not present in 'name' table.
    False
    
    >>> _testingValues["bad 1"].isValid(logger=logger, editor=e)
    test - ERROR - The design size 12.5 is not an integer.
    test - ERROR - The small end -19 cannot be used in an unsigned field.
    test - ERROR - The large end 'pookie' is not a real number.
    False
    
    >>> e2 = utilities.fakeEditor(0x10000)  # no name table
    >>> _testingValues[0].isValid(logger=logger, editor=e2)
    test.nameTableIndex - ERROR - Name table index 0 not present in 'name' table.
    False
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate_GPOS_size)
    
    attrSpec = dict(
        designSize = dict(
            attr_initfunc = (lambda: 90),
            attr_label = "Design size in decipoints"),
        
        subFamily = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Subfamily value"),
        
        nameTableIndex = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Name table index of common subfamily",
            attr_renumbernamesdirect = True,
            attr_showonlyiftrue = True),
        
        smallRangeEnd = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Small end of usage range in decipoints",
            attr_showonlyiftrue = True),
        
        largeRangeEnd = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Large end of usage range in decipoints",
            attr_showonlyiftrue = True))
    
    attrSorted = (
      'designSize',
      'subFamily',
      'nameTableIndex',
      'smallRangeEnd',
      'largeRangeEnd')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 003C 0000 0000 0000  0000                |.<........      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0050 0004 012C 0050  0078                |.P...,.P.x      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        d = self.__dict__
        w.add("5H", *[d[k] for k in self._ATTRSORT])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new FeatureParam_GPOS_size (like fromwalker), but performs
        validation on the input data.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = FeatureParam_GPOS_size.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.featureparams_GPOS_size - DEBUG - Walker has 10 remaining bytes.
        fvw.featureparams_GPOS_size - DEBUG - Data are (80, 4, 300, 80, 120)
        
        >>> obj.pprint()
        Design size in decipoints: 80
        Subfamily value: 4
        Name table index of common subfamily: 300
        Small end of usage range in decipoints: 80
        Large end of usage range in decipoints: 120
        
        >>> fvb(s[:5], logger=logger)
        fvw.featureparams_GPOS_size - DEBUG - Walker has 5 remaining bytes.
        fvw.featureparams_GPOS_size - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('featureparams_GPOS_size')
        else:
            logger = logger.getChild('featureparams_GPOS_size')
        
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength < 10:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))
            
            return None
        
        t = w.group("H", 5)
        logger.debug(('Vxxxx', (t,), "Data are %s"))
        return cls(*t)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureParam_GPOS_size object from the
        specified walker.
        
        >>> all(
        ...   obj == FeatureParam_GPOS_size.frombytes(obj.binaryString())
        ...   for obj in (_testingValues[0], _testingValues[1]))
        True
        """
        
        return cls(*w.group("H", 5))

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class FeatureParam_GSUB_cvxx_NameList(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Sequences of 'name' table indices. Note these must be monotonic!
    """
    
    seqSpec = dict(
        item_renumbernamesdirect = True,
        seq_validatefunc_partial = _validate_nameList)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureParam_GSUB_cvxx_NameList object to
        the specified writer. Note that these data are really inline to the
        parent object, so no stake is needed or used here.
        """
        
        w.add("2H", len(self), min(self))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureParam_GSUB_cvxx_NameList object from
        the specified walker.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('NameList')
        else:
            logger = logger.getChild('NameList')
        
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength < 4:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))
            
            return None
        
        count, first = w.unpack("2H")
        v = list(range(first, first + count))
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureParam_GSUB_cvxx_NameList object from
        the specified walker.
        """
        
        count, first = w.unpack("2H")
        return cls(range(first, first + count))

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class FeatureParam_GSUB_cvxx(set, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing FeatureParams for 'cv01' through 'cv99' GSUB features.
    These are sets of Unicode values for which the associated feature provides
    variants. Additionally, the following attributes are supported:
    
    sampleTextName      A 'name' table ID for sample text that demonstrates
                        this feature.
    
    uiItemNames         A FeatureParam_GSUB_cvxx_NameList object.
    
    uiLabelName         A 'name' table ID for a label for the overall effect.
    
    uiTooltipTextName   A 'name' table ID for the tooltip text.
    """
    
    setSpec = dict(
        item_pprintfunc = _pf,
        set_showpresorted = True)
    
    attrSpec = dict(
        sampleTextName = dict(
            attr_renumbernamesdirect = True,
            attr_showonlyiftrue = True),
        
        uiItemNames = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue = True),
        
        uiLabelName = dict(
            attr_renumbernamesdirect = True,
            attr_showonlyiftrue = True),
        
        uiTooltipTextName = dict(
            attr_renumbernamesdirect = True,
            attr_showonlyiftrue = True))
    
    attrSorted = (
      'uiLabelName',
      'uiTooltipTextName',
      'sampleTextName',
      'uiItemNames')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureParam_GSUB_cvxx object to the
        specified writer.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 0)  # format
        w.add("H", self.uiLabelName or 0)
        w.add("H", self.uiTooltipTextName or 0)
        w.add("H", self.sampleTextName or 0)
        self.uiItemNames.buildBinary(w, **kwArgs)  # no stake needed
        w.add("H", len(self))
        w.addGroup("T", sorted(self))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureParam_GSUB_cvxx object from the
        specified walker.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('FeatureParam_GSUB_cvxx')
        else:
            logger = logger.getChild('FeatureParam_GSUB_cvxx')
        
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength < 8:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))
            
            return None
        
        t = w.group("H", 4)
        
        if t[0] != 0:
            logger.error((
              'Vxxxx',
              (t[0],),
              "Unknown FeatureParam_GSUB_cvxx format: %d"))
            
            return None
        
        names = FeatureParam_GSUB_cvxx_NameList.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if names is None:
            return None
        
        if w.length() < 2:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))
            
            return None
        
        count = w.unpack("H")
        
        if w.length() < 2 * count:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))
            
            return None
        
        if count:
            s = w.group("H", count)
        else:
            s = set()
        
        return cls(
          s,
          uiLabelName = t[1],
          uiTooltipTextName = t[2],
          sampleTextName = t[3],
          uiItemNames = names)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureParam_GSUB_cvxx object from the
        specified walker.
        """
        
        t = w.group("H", 4)
        
        if t[0] != 0:
            raise ValueError("Unknown FeatureParam_GSUB_cvxx format %d" % (t[0],))
        
        names = FeatureParam_GSUB_cvxx_NameList.fromwalker(w, **kwArgs)
        count = w.unpack("H")
        
        if count:
            s = w.group("H", count)
        else:
            s = set()
        
        return cls(
          s,
          uiLabelName = t[1],
          uiTooltipTextName = t[2],
          sampleTextName = t[3],
          uiItemNames = names)

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class FeatureParam_GSUB_ssxx(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing FeatureParams for 'ss01' through 'ss20' GSUB features.
    These are simple objects with the following attributes:
    
        version
        nameTableIndex
    
    >>> e = _fakeEditor(300)
    >>> _testingValues[3].pprint(editor=e)
    Version: 0
    Name table index of UI name: 300 ('Test string')
    
    >>> logger = utilities.makeDoctestLogger("test_GSUB")
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues["bad 2"].isValid(logger=logger, editor=e)
    test_GSUB - ERROR - Version must be zero, but is 1.
    test_GSUB.nameTableIndex - ERROR - Name table index 500 not present in 'name' table.
    False
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate_GSUB_ssxx)
    
    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Version"),
        
        nameTableIndex = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Name table index of UI name",
            attr_renumbernamesdirect = True,
            attr_showonlyiftrue = True))
    
    attrSorted = ('version', 'nameTableIndex')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0000 012C                                |...,            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2H", self.version, self.nameTableIndex)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureParam_GSUB_ssxx object from the
        specified walker, doing source validation.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('featureparams_GSUB_ssxx')
        else:
            logger = logger.getChild('featureparams_GSUB_ssxx')
        
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        t = w.group("H", 2)
        logger.debug(('Vxxxx', (t,), "Data are %s"))
        
        if t[0] != 0:
            logger.error(('Vxxxx', (t[0],), "Expected version 0 but got %d."))
            return None
        
        return cls(*t)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureParam_GSUB_ssxx object from the
        specified walker.
        """
        
        return cls(*w.group("H", 2))

# -----------------------------------------------------------------------------

#
# Dispatch constants
#

dispatchTableGPOS = {
  b'size': FeatureParam_GPOS_size.fromwalker}

dispatchTableGPOS_validated = {
  b'size': FeatureParam_GPOS_size.fromvalidatedwalker}

dispatchTableGSUB = {
  b'ss%02d' % (i,): FeatureParam_GSUB_ssxx.fromwalker
  for i in range(1, 21)}

dispatchTableGSUB.update({
  b'cv%02d' % (i,): FeatureParam_GSUB_cvxx.fromwalker
  for i in range(1, 100)})
  
dispatchTableGSUB_validated = {
  b'ss%02d' % (i,): FeatureParam_GSUB_ssxx.fromvalidatedwalker
  for i in range(1, 21)}

dispatchTableGSUB_validated.update({
  b'cv%02d' % (i,): FeatureParam_GSUB_cvxx.fromvalidatedwalker
  for i in range(1, 100)})
  
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _fakeEditor(nameTableIndex):
        from fontio3 import name
        
        e = utilities.fakeEditor(0x10000)
        e.name = name.name.Name()
        e.name[(3, 1, 1033, nameTableIndex)] = "Test string"
        return e
    
    _testingValues = {
        0: FeatureParam_GPOS_size(60, 0, 0, 0, 0),
        1: FeatureParam_GPOS_size(80, 4, 300, 80, 120),
        2: FeatureParam_GPOS_size(80, 4, 250, 180, 120),
        3: FeatureParam_GSUB_ssxx(0, 300),
        
        # bad values start here
        
        "bad 1": FeatureParam_GPOS_size(12.5, 4, 300, -19, 'pookie'),
        "bad 2": FeatureParam_GSUB_ssxx(1, 500)}

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
