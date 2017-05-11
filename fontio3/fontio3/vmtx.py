#
# vmtx.py
#
# Copyright © 2004-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType 'vmtx' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta, simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if abs(obj.sidebearing) > obj.advance:
        logger.warning((
          'V0265',
          (obj.sidebearing, obj.advance),
          "The sidebearing %d is greater than the advance %d."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class MtxEntry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single values in a Vmtx dict. These are simple
    objects with two attributes: advance and sidebearing.

    There are no fromwalker() or buildBinary() methods here; it's handled at
    the higher level.
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        advance = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Advance height",
            attr_scaledirect = True,
            attr_representsy = True),
        
        sidebearing = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Top sidebearing",
            attr_scaledirect = True,
            attr_representsy = True))

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class Vmtx(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing 'vmtx' tables. These are dicts mapping glyph indices
    to MtxEntry objects.
    
    >>> _testingValues[1].pprint()
    0:
      Advance height: 1024
      Top sidebearing: 50
    1:
      Advance height: 1700
      Top sidebearing: 60
    2:
      Advance height: 1700
      Top sidebearing: -50
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    xyz1:
      Advance height: 1700
      Top sidebearing: 50
    xyz2:
      Advance height: 1700
      Top sidebearing: 60
    xyz3:
      Advance height: 1700
      Top sidebearing: -50
    
    >>> logger = utilities.makeDoctestLogger("toptest")
    >>> _testingValues[3].isValid(logger=logger)
    toptest.glyph 2 - WARNING - The sidebearing 900 is greater than the advance 300.
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_subloggernamefunc = (lambda i: "glyph %d" % (i,)),
        item_usenamerforstr = True)
    
    #
    # Methods
    #
    
    def _keysAreDense(self):
        """
        Returns True if sorted(self) == list(range(len(self))).
        """
        
        return all(i in self for i in range(len(self)))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Vmtx object to the specified LinkedWriter.
        There is one optional keyword argument:
        
            okToCompact     If True, the metrics will be analyzed for monospace
                            runs. If False (the default) all glyphs will get
                            full metrics added, both advance and sidebearing.
        
        >>> utilities.hexdump(_testingValues[1].binaryString(okToCompact=False))
               0 | 0400 0032 06A4 003C  06A4 FFCE           |...2...<....    |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0400 0032 06A4 003C  FFCE                |...2...<..      |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(okToCompact=False))
               0 | 06A4 0032 06A4 003C  06A4 FFCE           |...2...<....    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 06A4 0032 003C FFCE                      |...2.<..        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        okToCompact = kwArgs.get('okToCompact', True)  # w00t!
        longCount = self.getLongMetricsCount(okToCompact)  # does a density check
        shortCount = len(self) - longCount
        
        for i in range(longCount):
            obj = self[i]
            w.add("Hh", obj.advance, obj.sidebearing)
        
        for i in range(shortCount):
            obj = self[i + longCount]
            w.add("h", obj.sidebearing)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Vmtx object. However, it
        also does validation on the binary data being unpacked.
        
        The following keyword arguments are supported:
        
            fontGlyphCount      The number of glyphs (from maxp). This is
                                required. Note this differs from the non-
                                validating method, which does not require this
                                keyword argument.
            
            logger              A logger to which observations will be posted.
                                If not specified, the default system logger
                                will be used.
            
            numLongMetrics      Number of long metrics (contained in the Hhea
                                object). This is required.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = _testingValues[1].binaryString(okToCompact=True)
        >>> d = {'fontGlyphCount': 3, 'numLongMetrics': 2, 'logger': logger}
        >>> obj = Vmtx.fromvalidatedbytes(s, **d)
        test.vmtx - DEBUG - Walker has 10 remaining bytes.
        
        >>> Vmtx.fromvalidatedbytes(s[:-1], **d)
        test.vmtx - DEBUG - Walker has 9 remaining bytes.
        test.vmtx - ERROR - The table is not long enough for the specified number of long and short metrics records.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('vmtx')
        else:
            logger = logger.getChild('vmtx')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        longCount = kwArgs['numLongMetrics']
        fontGlyphCount = kwArgs['fontGlyphCount']
        shortCount = fontGlyphCount - longCount
        
        if longCount > fontGlyphCount:
            logger.error((
              'V0263',
              (),
              "The number of long metrics exceeds the font's glyph count."))
            
            return None
        
        if longCount == 0:
            logger.error((
              'V0264',
              (),
              "There must always be at least one long metrics record, "
              "but the font's count of long metrics is zero."))
            
            return None
        
        if w.length() < (4 * longCount + 2 * shortCount):
            logger.error((
              'E2700',
              (),
              "The table is not long enough for the specified number of "
              "long and short metrics records."))
            
            return None
        
        longList = w.group("Hh", longCount)
        shortList = w.group("h", shortCount)
        r = cls()
        
        for i, t in enumerate(longList):
            r[i] = MtxEntry(*t)
        
        if shortList is not None:
            commonAdvance = r[longCount - 1].advance
            
            for i, sb in enumerate(shortList):
                r[i + longCount] = MtxEntry(commonAdvance, sb)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Vmtx object using the specified walker. There is one
        require keyword argument:
        
            numLongMetrics      The number of full (advance, sidebearing) pairs
                                present in the data. If there is any left-over
                                content after these are processed, that content
                                is treated as sidebearing-only metrics.
        
        >>> s = _testingValues[1].binaryString(okToCompact=False)
        >>> _testingValues[1] == Vmtx.frombytes(s, numLongMetrics=3)
        True
        
        >>> s = _testingValues[1].binaryString()
        >>> _testingValues[1] == Vmtx.frombytes(s, numLongMetrics=2)
        True
        
        >>> s = _testingValues[2].binaryString(okToCompact=False)
        >>> _testingValues[2] == Vmtx.frombytes(s, numLongMetrics=3)
        True
        
        >>> s = _testingValues[2].binaryString()
        >>> _testingValues[2] == Vmtx.frombytes(s, numLongMetrics=1)
        True
        """
        
        longCount = kwArgs['numLongMetrics']
        longList = w.group("Hh", longCount)
        shortList = (w.unpackRest("h") if w.stillGoing() else None)
        r = cls()
        
        for i, t in enumerate(longList):
            r[i] = MtxEntry(*t)
        
        if shortList is not None:
            commonAdvance = r[longCount - 1].advance
            
            for i, sb in enumerate(shortList):
                r[i + longCount] = MtxEntry(commonAdvance, sb)
        
        return r
    
    def getLongMetricsCount(self, okToCompact):
        """
        Returns the number of long metrics present, given the specified
        okToCompact permission.
        
        >>> _testingValues[1].getLongMetricsCount(False)
        3
        
        >>> _testingValues[1].getLongMetricsCount(True)
        2
        
        >>> _testingValues[2].getLongMetricsCount(False)
        3
        
        >>> _testingValues[2].getLongMetricsCount(True)
        1
        """
        
        if not self:
            return 0
        
        if not self._keysAreDense():
            raise ValueError("There are key gaps in the metrics dict!")
        
        if not okToCompact:
            return len(self)
        
        shortCount = 0
        testAdvance = self[len(self) - 1].advance
        
        for i in range(len(self) - 2, -1, -1):
            if self[i].advance != testAdvance:
                break
            
            shortCount += 1
        
        return len(self) - shortCount

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        Vmtx(),
        
        Vmtx({
          0: MtxEntry(1024, 50),
          1: MtxEntry(1700, 60),
          2: MtxEntry(1700, -50)}),
        
        Vmtx({
          0: MtxEntry(1700, 50),
          1: MtxEntry(1700, 60),
          2: MtxEntry(1700, -50)}),
        
        Vmtx({
          0: MtxEntry(1700, 50),
          1: MtxEntry(1700, 60),
          2: MtxEntry(300, 900)}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
