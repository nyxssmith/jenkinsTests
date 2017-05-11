#
# TSI5.py
#
# Copyright © 2012-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Functions and classes for displaying and editing data from the 'TSI5' table.
"""

# System imports
import logging
import operator
import re

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_fixedGroupNames = (
  "AnyGroup",
  "Other",
  "UpperCase",
  "LowerCase",
  "Figure",
  "Reserved1",
  "Reserved2",
  "Reserved3")

# -----------------------------------------------------------------------------

#
# Private functions
#

def _getGroupNames(tsiDatTbl):
    """
    Return glyph group strings for TSI5 glyph classes, *including* the 8
    predefined names, plus any additional names defined in a TSIDat.cvt string
    (typically: TSI1). These strings are the values stored in the map.
    """
    
    if tsiDatTbl is not None:
        cvttxt = tsiDatTbl.cvt or ""
        
        pat = re.compile(
          '^\s*GROUP\s+(\w+)(\s+\x22.+\x22.*)?$',
          flags = re.MULTILINE)
        
        customgroups = [g[0] for g in pat.findall(cvttxt)]
        return list(_fixedGroupNames) + customgroups

    return list(_fixedGroupNames)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TSI5(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects mapping glyphIDs to VTT Glyph Group names.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True)
        
    attrSpec = dict(
        groupnames = dict(
          attr_initfunc = (lambda: list(_fixedGroupNames))))

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Hhea object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0008 0002 0003                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()

        d = {s: i for i, s in enumerate(self.groupnames)}

        for i in sorted(self):
            g = d.get(self[i], 0)
            w.add("H", g)
    
    @classmethod
    def fromValidatedFontChefSource(cls, s, **kwArgs):
        """
        Builds a TSI5 table from Font Chef source (stream-like object 's').
        The following kwArgs are required:

            dataTable   TSIDat object containing Control Program text defining
                        Group names.

            logger      A logger for posting errors

            namer       for converting glyphname strings into glyph ids
            
        >>> t = _testingValues[1]
        >>> s = io.StringIO()
        >>> l = utilities.makeDoctestLogger('fromValidatedFontChefSource')
        >>> t.writeFontChefSource(s)
        >>> ignore = s.seek(0)
        >>> f = TSI5.fromValidatedFontChefSource
        >>> obj = f(s, namer=_testingNamer, logger=l, dataTable=_testingDatTbl)
        >>> obj[1] == 'TestGroup1'
        True
        """
        
        namer = kwArgs.get('namer')
        tsidat = kwArgs.get('dataTable')
        logger = kwArgs.get('logger')
        groups = _getGroupNames(tsidat)
        d = {}
        hdr = s.readline().strip() # first line
        
        if hdr.lower() == 'font chef table tsi5':
            for line in s.readlines():
                tokens = line.split() # any whitespace
                
                if len(tokens) == 2:
                    gname = tokens[0]
                    ggroup = tokens[1]
                    gid = namer.glyphIndexFromString(gname)
                    
                    if gid is not None:
                        if ggroup in groups:
                            d[gid] = ggroup
                        
                        else:
                            logger.error((
                              'Vxxxx',
                              (ggroup, gname),
                              "Group '%s' for glyph %s' not in Group List."))
                    
                    else:
                        logger.warning((
                          'Vxxxx',
                          (gname,),
                          "Glyph '%s' not found."))
        
        else:
            logger.error((
              'Vxxxx',
              (),
              "Not a valid Font Chef TSI5 dump."))
        
        return cls(d, groupnames=groups)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker, but with validation.
        
        The following keyword arguments are supported:
        
            fontGlyphCount      The glyph count from the 'maxp' table.
                                This is required.

            dataTable           A TSIDat object (typically TSI1). This
                                is optional, but if not included, only
                                default glyphnames will be used, and any
                                custom names defined in a Control Program
                                will be ignored.
            
            logger              A logger to which notices will be posted. This
                                is optional; the default logger will be used if
                                this is not provided.
                                
        >>> fvb=TSI5.fromvalidatedbytes
        >>> l=utilities.makeDoctestLogger("test")
        >>> s = utilities.fromhex("00 01 00 02 00 08 00 09 00 FF")
        >>> obj= fvb(s, fontGlyphCount=5, logger=l, dataTable=_testingDatTbl)
        test.TSI5 - DEBUG - Walker has 10 remaining bytes.
        test.TSI5 - INFO - There are 5 entries.
        test.TSI5 - ERROR - Group index 255 for glyph 4 is beyond the range of defined glyph groups.
        >>> obj[2], obj[3]
        ('TestGroup1', 'TestGroup2')
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('TSI5')
        else:
            logger = logger.getChild('TSI5')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        fontGlyphCount = utilities.getFontGlyphCount(**kwArgs)
        count = int(w.length()/2)
        
        if count != fontGlyphCount:
            logger.warning((
              'V0482',
              (),
              "Length of the table is not consistent with "
              "font's glyph count."))
        
        else:
            logger.info(('V0483', (count,), "There are %d entries."))
        
        dataTable = kwArgs.pop('dataTable', None)
        groups = _getGroupNames(dataTable)
        d = {}
        
        if count:
            gc = w.group("H", count)
            
            for k,v in enumerate(gc):
                if v < len(groups):
                    d[k] = groups[v]
                
                else:
                    logger.error((
                      'Vxxxx',
                      (v,k),
                      "Group index %d for glyph %d is beyond the range "
                      "of defined glyph groups."))
                    
                    d[k] = groups[0]
        
        return cls(d, groupnames=groups)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new TSI5 map of glyphID to VTT Group Name. If the optional
        'dataTable' keyword is supplied, custom-defined group names (from a VTT
        Control Table, typically stored in the TSI1.cvt attribute) will be
        built from that, otherwise ignored.

        The following keyword arguments are supported:
        
            dataTable       A TSIDat object (typically TSI1). This is optional,
                            but if not included, only default glyphnames will
                            be used, and any custom names defined in a Control
                            Program will be ignored.

        >>> fb=TSI5.frombytes
        >>> s = utilities.fromhex("00 08 00 07 00 05 00 99")
        >>> obj= fb(s, fontGlyphCount=4, dataTable=_testingDatTbl)
        >>> [obj[i] for i in range(len(obj))]
        ['TestGroup1', 'Reserved3', 'Reserved1', 'AnyGroup']
        >>> s = utilities.fromhex("00 03 00 03 00 04 00 04")
        >>> obj = fb(s)
        >>> obj[1], obj[2]
        ('LowerCase', 'Figure')
        """
        
        count = int(w.length() / 2)
        dataTable = kwArgs.pop('dataTable', None)
        groups = _getGroupNames(dataTable)
        d = {}
        
        if count:
            gc = w.group("H", count)
            
            for k,v in enumerate(gc):
                if v < len(groups):
                    d[k] = groups[v]
                else:
                    d[k] = groups[0]

        return cls(d, groupnames=groups)


    def writeFontChefSource(self, s, **kwArgs):
        """
        Writes the TSI5 data to stream-like object 's' in Font Chef format.
        Uses optional supplied 'namer' to name glyphs; otherwise, uses Font
        Chef glyph ID notation ('\#N' where N is the glyph index as integer).
        
        >>> s = io.StringIO()
        >>> _testingValues[1].writeFontChefSource(s)
        >>> utilities.hexdump(s.getvalue().encode('ascii'))
               0 | 466F 6E74 2043 6865  6620 5461 626C 6520 |Font Chef Table |
              10 | 5453 4935 0A0A 5C23  3009 416E 7947 726F |TSI5..\#0.AnyGro|
              20 | 7570 0A5C 2331 0954  6573 7447 726F 7570 |up.\#1.TestGroup|
              30 | 310A 5C23 3209 5570  7065 7243 6173 650A |1.\#2.UpperCase.|
              40 | 5C23 3309 4C6F 7765  7243 6173 650A      |\#3.LowerCase.  |
        """
        
        namer = kwArgs.get('namer')
        
        if namer:
            bnfgi = namer.bestNameForGlyphIndex
        else:
            bnfgi = lambda x: "\#%d" % (x,)

        s.write("Font Chef Table TSI5\n\n")
        
        for gid, grp in sorted(self.items()):
            s.write("%s\t%s\n" % (bnfgi(gid), grp))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import io
    from collections import namedtuple
    from fontio3.TSI.TSIDat import TSIDat

    _testingDatTbl = TSIDat()
    _testingDatTbl.cvt = (
      'GROUP TestGroup1 "ABCDEFG"\n/* GROUP NullGroup1 "foo" */\n'
      'GROUP TestGroup2 "xyz"\n')
    
    _testingValues = (
        TSI5(),
        
        TSI5(
          {0:"AnyGroup", 1:"TestGroup1", 2:"UpperCase", 3:"LowerCase"},
          groupnames = list(_fixedGroupNames) + ['TestGroup1']))

    _testingNamer = namedtuple('namer', 'glyphIndexFromString')
    _testingNamer.glyphIndexFromString = staticmethod(
        lambda x: int(x.replace('\\#', '')))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
