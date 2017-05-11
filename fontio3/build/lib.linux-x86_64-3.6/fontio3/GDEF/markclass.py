#
# markclass.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to mark classes.
"""

# Other imports
from fontio3.opentype import classdef
from fontio3.utilities import span

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, obj, **kwArgs):
    if not obj:
        p.simple("No mark classes are defined.", **kwArgs)
        return
    
    nm = kwArgs.get('namer', obj.getNamer())
    
    for i in sorted(set(obj.values())):
        if not i:
            continue
        
        s = {gi for gi, c in obj.items() if c == i}
        
        if not s:
            continue
        
        s = span.Span(s)
        
        if nm is not None:
            sv = []
            nf = nm.bestNameForGlyphIndex
            
            for first, last in s:
                if first == last:
                    sv.append(nf(first))
                else:
                    sv.append("%s - %s" % (nf(first), nf(last)))
            
            p.simple(
              ', '.join(sv),
              label = "Mark class %d" % (i,),
              multilineExtraIndent = 0)
        
        else:
            p.simple(
              str(s),
              label = "Mark class %d" % (i,),
              multilineExtraIndent = 0)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class MarkClassTable(classdef.ClassDef):
    """
    Objects identifying mark classes. These are simple ClassDefTables with a
    slightly different item_pprintfunc.
    
    >>> c = _testingValues[1]
    >>> c.pprint()
    Mark class 1: 7
    Mark class 2: 4-6, 10-11, 15
    
    >>> c.pprint(namer=namer.testingNamer())
    Mark class 1: xyz8
    Mark class 2: xyz5 - xyz7, xyz11 - xyz12, xyz16
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        map_pprintfunc = _pprint)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        MarkClassTable(),
        MarkClassTable({4: 2, 5: 2, 6: 2, 7: 1, 10: 2, 11: 2, 15: 2}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
