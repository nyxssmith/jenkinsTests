#
# lookupflag.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the LookupFlag mask.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class LookupFlag(object, metaclass=maskmeta.FontDataMetaclass):
    """
    The flags associated with a single Lookup.
    
    >>> _testingValues[0].pprint()
    Right-to-left for Cursive: False
    Ignore base glyphs: False
    Ignore ligatures: False
    Ignore marks: False
    
    >>> _testingValues[1].pprint()
    Right-to-left for Cursive: True
    Ignore base glyphs: False
    Ignore ligatures: False
    Ignore marks: False
    
    >>> _testingValues[2].pprint()
    Right-to-left for Cursive: False
    Ignore base glyphs: False
    Ignore ligatures: False
    Ignore marks: False
    A mark filter is present
    
    >>> _testingValues[3].pprint()
    Right-to-left for Cursive: False
    Ignore base glyphs: False
    Ignore ligatures: True
    Ignore marks: False
    Mark attachment type: 3
    
    >>> utilities.hexdump(_testingValues[3].binaryString())
           0 | 0304                                     |..              |
    
    >>> logger = utilities.makeDoctestLogger("lookupflag_ivtest")
    >>> obj = LookupFlag.fromvalidatednumber(0x00E0, logger=logger)
    lookupflag_ivtest.genericmask - WARNING - All reserved bits should be set to 0, but some are 1.
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        validatecode_notsettozero = 'V0349')
    
    maskSorted = (
      'rightToLeft',
      'ignoreBaseGlyphs',
      'ignoreLigatures',
      'ignoreMarks',
      'useMarkFilteringSet',
      'markAttachmentType')
    
    maskSpec = dict(
        rightToLeft = dict(
            mask_isbool = True,
            mask_label = "Right-to-left for Cursive",
            mask_rightmostbitindex = 0),
        
        ignoreBaseGlyphs = dict(
            mask_isbool = True,
            mask_label = "Ignore base glyphs",
            mask_rightmostbitindex = 1),
        
        ignoreLigatures = dict(
            mask_isbool = True,
            mask_label = "Ignore ligatures",
            mask_rightmostbitindex = 2),
        
        ignoreMarks = dict(
            mask_isbool = True,
            mask_label = "Ignore marks",
            mask_rightmostbitindex = 3),
        
        useMarkFilteringSet = dict(
            mask_isbool = True,
            mask_label = "A mark filter is present",
            mask_rightmostbitindex = 4,
            mask_showonlyiftrue = True),
        
        markAttachmentType = dict(
            mask_bitcount = 8,
            mask_label = "Mark attachment type",
            mask_rightmostbitindex = 8,
            mask_showonlyiftrue = True))

    #
    # Methods
    #
    
    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write flags to stream 's' in Font Worker source format.
        
        >>> import io
        >>> s = io.StringIO()
        >>> f = LookupFlag(
        ...   ignoreMarks = True,
        ...   markAttachmentType = 2,
        ...   useMarkFilteringSet = True)
        >>> f.writeFontWorkerSource(s, markglyphsetindex=3)
        >>> print(s.getvalue().replace("\\t", ": "), end='')
        RightToLeft: no
        IgnoreBaseGlyphs: no
        IgnoreLigatures: no
        IgnoreMarks: yes
        MarkFilterType: 3
        <BLANKLINE>
        """
        
        s.write("RightToLeft\t%s\n" % ("yes" if self.rightToLeft else "no",))
        s.write("IgnoreBaseGlyphs\t%s\n" % ("yes" if self.ignoreBaseGlyphs else "no",))
        s.write("IgnoreLigatures\t%s\n" % ("yes" if self.ignoreLigatures else "no",))
        s.write("IgnoreMarks\t%s\n" % ("yes" if self.ignoreMarks else "no",))
        
        if self.useMarkFilteringSet:
            mfi = kwArgs.get('markglyphsetindex')
            s.write("MarkFilterType\t%d\n" % (mfi,))
        
        elif self.markAttachmentType:
            # note it is one or the other with MarkFilteringSet preferred.
            s.write("MarkAttachmentType\t%d\n" % (self.markAttachmentType,))

        s.write("\n")

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        LookupFlag(),
        LookupFlag(rightToLeft=True),
        LookupFlag(useMarkFilteringSet=True),
        LookupFlag(ignoreLigatures=True, markAttachmentType=3))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
