#
# entryexit.py
#
# Copyright © 2007-2010, 2012, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for EntryExit objects, used in Cursive tables.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class EntryExit(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing the entry and exit anchors for a Cursive subtable
    entry. These are simple objects with two attributes: entry and exit.
    
    Note that EntryExit objects do not have fromwalker() or buildBinary()
    methods; these are handled at the Cursive level.
    
    >>> _testingValues[0].pprint()
    Exit anchor:
      x-coordinate: -40
      y-coordinate: 18
    
    >>> _testingValues[2].pprint()
    Entry anchor:
      x-coordinate: 10
      y-coordinate: 20
      Device for x:
        Tweak at 12 ppem: -2
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 1
    Exit anchor:
      x-coordinate: -40
      y-coordinate: 18
      Contour point index: 6
      Glyph index: 40
      
    >>> _testingValues[3].pprint()
    Entry anchor:
      x-coordinate: -25
      y-coordinate: 120
      Variation for y:
        A delta of 40 applies in region 'wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0)
    Exit anchor:
      x-coordinate: -40
      y-coordinate: 18
      Contour point index: 6
      Glyph index: 40
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        entry = dict(
            attr_followsprotocol = True,
            attr_label = "Entry anchor",
            attr_showonlyiftrue = True,
            attr_strneedsparens = True),
        
        exit = dict(
            attr_followsprotocol = True,
            attr_label = "Exit anchor",
            attr_showonlyiftrue = True,
            attr_strneedsparens = True))

    #
    # Methods
    #
    
    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write EntryExit as Font Worker-style source. The following kwArgs
        are required:
        'lbl'       a label to use for the entry/exit (usu. glyph name)
        'datatbl'   Glyf or CFF object to get point #s
        """

        lbl = kwArgs.get('lbl')
        map = kwArgs.get('map')

        for obj,typ in ((self.entry, 'entry'), (self.exit, 'exit')):
            if obj is not None:
                pt = map.get((obj.x,obj.y), None)
                pts = ("\t%d" % (pt,)) if pt else ""
                s.write("%s\t%s\t%d,%d%s\n" % (typ, lbl, obj.x, obj.y, pts))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.GPOS import anchor_coord, anchor_device, anchor_point, anchor_variation
    
    ac = anchor_coord._testingValues
    ad = anchor_device._testingValues
    ap = anchor_point._testingValues
    av = anchor_variation._testingValues
    
    _testingValues = (
      EntryExit(None, ac[0]),
      EntryExit(ac[0], None),
      EntryExit(ad[0], ap[0]),
      EntryExit(av[1], ap[0]))
    
    del ac, ad, ap

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
