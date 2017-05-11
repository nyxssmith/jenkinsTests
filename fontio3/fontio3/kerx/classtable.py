#
# classtable.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mappings from glyph to class for 'kerx' tables. The code here
includes optimization so the smallest possible lookup table format will be
chosen.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import lookup, valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pf(p, value, label, **kwArgs):
    if value != "Out of bounds":
        p.simple(value, label=label, **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ClassTable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing class mappings as used in format 1 'kerx' subtables.
    These are dicts mapping glyph indices to class name strings.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    afii60001: Vowel
    afii60002: Vowel
    afii60003: Consonant
    xyz91: Vowel
    xyz95: End of line
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintfunc = _pf,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        item_validatefunc = functools.partial(
          valassist.isString,
          label = "class name"))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ClassTable object to the specified writer.
        The following keyword arguments are used:
        
            classDict                   A dict mapping class name strings to
                                        their corresponding numeric indices.
                                        This is required.
        
            preferredIOLookupFormat     If you need the actual input glyph to
                                        output glyph lookup to be written in a
                                        specific format, use this keyword. The
                                        default (as usual for Lookup objects)
                                        is to use the smallest one possible.
                                        
                                        Note this keyword is usually specified
                                        in the perTableOptions dict passed into
                                        the Editor's writeFont() method.
            
            stakeValue                  A value which will stake the start of
                                        the newly-written data. This is
                                        optional.
        
        >>> cd = {s: i for i, s in enumerate(_testNames())}
        >>> h = utilities.hexdump
        >>> k = {'classDict': cd}
        >>> h(_testingValues[1].binaryString(**k))
               0 | 0008 005A 0009 0004  0001 0001 0001 0003 |...Z............|
              10 | 0001 0004 0004 0005                      |........        |
        
        >>> k['preferredIOLookupFormat'] = 2
        >>> h(_testingValues[1].binaryString(**k))
               0 | 0002 0006 0004 0018  0002 0000 005A 005A |.............Z.Z|
              10 | 0004 005E 005E 0003  0061 0060 0004 0062 |...^.^...a.`...b|
              20 | 0062 0005 FFFF FFFF  0001                |.b........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        cd = kwArgs['classDict']  # name -> class index
        d = {k: cd[s] for k, s in self.items() if s != "Out of bounds"}
        k = {'sentinelValue': 1}
        pref = kwArgs.get('preferredIOLookupFormat', None)
        
        if pref is not None:
            k['preferredFormat'] = pref
        
        w.addString(lookup.bestFromDict(d, **k))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassTable object from the specified walker,
        doing source validation. The following keyword arguments are used:
        
            classNames      A sequence whose indices are class index numbers
                            and whose values are the associated class name
                            strings. This is required.
            
            logger          A logger to which messages will be posted.
        
        >>> v = _testNames()
        >>> cd = {s: i for i, s in enumerate(v)}
        >>> s = _testingValues[1].binaryString(classDict=cd)
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = ClassTable.fromvalidatedbytes
        >>> obj = fvb(s, classNames=v, logger=logger)
        fvw - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:1], classNames=v, logger=logger)
        fvw - DEBUG - Walker has 1 remaining bytes.
        fvw.lookup_aat - DEBUG - Walker has 1 remaining bytes.
        fvw.lookup_aat - ERROR - Insufficient bytes.
        """
        
        classNames = kwArgs.pop('classNames')
        logger = kwArgs.pop('logger', logging.getLogger())
        logger.getChild("classtable")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        fvw = lookup.Lookup.fromvalidatedwalker
        sv = kwArgs.pop('sentinelValue', 1)
        lk = fvw(w, logger=logger, sentinelValue=sv, **kwArgs)
        
        if lk is None:
            return None
        
        r = cls()
        bads = set()
        
        for glyph, classIndex in lk.items():
            if classIndex >= len(classNames):
                bads.add(glyph)
            else:
                r[glyph] = classNames[classIndex]
        
        if bads:
            logger.error((
              'V0776',
              (sorted(bads),),
              "The following glyphs have bad class indices: %s"))
            
            return None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassTable object from the specified walker.
        The following keyword arguments are used:
        
            classNames      A sequence whose indices are class index numbers
                            and whose values are the associated class name
                            strings. This is required.
        
        >>> v = _testNames()
        >>> cd = {s: i for i, s in enumerate(v)}
        >>> obj = _testingValues[1]
        >>> bs = obj.binaryString(classDict=cd)
        >>> obj == ClassTable.frombytes(bs, classNames=v)
        True
        """
        
        classNames = kwArgs.pop('classNames')
        lk = lookup.Lookup.fromwalker(w, **kwArgs)
        return cls((g, classNames[x]) for g, x in lk.items())

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    def _testNames():
        return [
          "End of text",
          "Out of bounds",
          "Deleted glyph",
          "End of line",
          "Vowel",
          "Consonant"]
    
    v = _testNames()
    
    _testingValues = (
        ClassTable(),
        ClassTable({i+90: v[k] for i, k in enumerate([4,1,1,1,3,1,4,4,5])}))
    
    del v

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
