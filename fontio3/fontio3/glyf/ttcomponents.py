#
# ttcomponents.py
#
# Copyright © 2009-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a sequence of components for a composite TrueType glyph.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.glyf import ttcomponent

# -----------------------------------------------------------------------------

#
# Classes
#

class TTComponents(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing all the components of a composite glyph (though not
    the hints, which are handled at a higher level).
    
    >>> _testingValues[1].pprint()
    Component 1:
      Component glyph: 100
      Transformation matrix: [[1.25, 0.75, 0.0], [0.0, 1.5, 0.0], [300.0, 0.0, 1.0]]
      This component's metrics will be used: True
    Component 2:
      Component glyph: 80
      Transformation matrix: Shift Y by -40
      Round to grid: True
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Component %d" % (i + 1,)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the TTComponents object to the specified
        writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString(hasHints=False))
               0 | 12A3 0064 012C 0000  5000 3000 0000 6000 |...d.,..P.0...`.|
              10 | 0006 0050 00D8                           |...P..          |
        """
        
        hasHints = kwArgs.pop('hasHints')
        kwArgs.pop('moreComponents', None)
        
        for i, obj in enumerate(self):
            lastComponent = i == (len(self) - 1)
            
            obj.buildBinary(
              w,
              moreComponents = (not lastComponent),
              hasHints = (hasHints if lastComponent else False),
              **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new TTComponents. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString(hasHints=False)
        >>> ci = {'hasHints': False}
        >>> fvb = TTComponents.fromvalidatedbytes
        >>> fvb(s, logger=logger, componentInfo=ci).pprint()
        test.ttcomponents - DEBUG - Walker has 22 remaining bytes.
        test.ttcomponents.[0].ttcomponent - DEBUG - Walker has 22 remaining bytes.
        test.ttcomponents.[1].ttcomponent - DEBUG - Walker has 6 remaining bytes.
        Component 1:
          Component glyph: 100
          Transformation matrix: [[1.25, 0.75, 0.0], [0.0, 1.5, 0.0], [300, 0, 1]]
          This component's metrics will be used: True
        Component 2:
          Component glyph: 80
          Transformation matrix: Shift Y by -40.0
          Round to grid: True
        
        >>> obj = fvb(s[:2], logger=logger, componentInfo=ci)
        test.ttcomponents - DEBUG - Walker has 2 remaining bytes.
        test.ttcomponents.[0].ttcomponent - DEBUG - Walker has 2 remaining bytes.
        test.ttcomponents.[0].ttcomponent - ERROR - Insufficient bytes for component glyph index
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ttcomponents')
        else:
            logger = logger.getChild('ttcomponents')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        r = cls()
        func = ttcomponent.TTComponent.fromvalidatedwalker
        ci = kwArgs['componentInfo']
        anyHints = False
        
        while True:
            subLogger = logger.getChild("[%d]" % (len(r),))
            obj = func(w, logger=subLogger, **kwArgs)
            
            if obj is None:
                return None
            
            r.append(obj)
            anyHints = anyHints or ci['hasHints']
            
            if not ci['moreComponents']:
                break
        
        ci['hasHints'] = anyHints
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TTComponents object from the specified
        walker.
        
        >>> _testingValues[1] == TTComponents.frombytes(
        ...   _testingValues[1].binaryString(hasHints=False),
        ...   componentInfo={'hasHints':False})
        True
        """
        
        r = cls()
        func = ttcomponent.TTComponent.fromwalker
        ci = kwArgs['componentInfo']
        anyHints = False
        
        while True:
            r.append(func(w, **kwArgs))
            anyHints = anyHints or ci['hasHints']
            
            if not ci['moreComponents']:
                break
        
        ci['hasHints'] = anyHints
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    ctv = ttcomponent._testingValues
    
    _testingValues = (
        TTComponents(),
        TTComponents([ctv[2], ctv[1]]),     # glyphs 100, 80
        TTComponents([ctv[3]]),             # glyph 901
        TTComponents([ctv[4], ctv[5]]),     # glyphs 902, 903
        TTComponents([ctv[6]]),             # glyph 904
        TTComponents([ctv[7]]))             # glyph 905
    
    del ctv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
