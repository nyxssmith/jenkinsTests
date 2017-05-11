#
# pair.py
#
# Copyright © 2007-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 2 (Pair Adjustment) subtables for a GPOS table.
"""

# System imports
import logging

# Other imports
from fontio3.GPOS import pairclasses, pairglyphs

# -----------------------------------------------------------------------------

#
# Factory function
#

def Pair(w, **kwArgs):
    """
    Factory function for creating either PairClasses or PairGlyphs objects from
    a walker whose format is not known in advance.
    
    >>> w = walkerbit.StringWalker(_testingValues[0].binaryString())
    >>> _testingValues[0] == Pair(w)
    True
    
    >>> w = walkerbit.StringWalker(_testingValues[1].binaryString())
    >>> _testingValues[1] == Pair(w)
    True
    """
    
    format = w.unpack("H", advance=False)
    
    if format == 1:
        return pairglyphs.PairGlyphs.fromwalker(w, **kwArgs)
    elif format == 2:
        return pairclasses.PairClasses.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown Pair format: %d" % (format,))

def Pair_fromValidatedFontWorkerSource(fws, **kwArgs):
    """
    Factory function for creating either PairClasses or PairGlyphs objects from
    a FontWorkerSource whose format is not known in advance, with source
    validation.
    
    >>> logger = utilities.makeDoctestLogger("FW_test")
    >>> p3 = Pair_fromValidatedFontWorkerSource(_test_FW_fws3, namer=_test_FW_namer, logger=logger)
    FW_test.pair - WARNING - line 2 -- unexpected token: foo
    FW_test.pair.pairglyphs - WARNING - line 2 -- unexpected token: foo
    FW_test.pair.pairglyphs - WARNING - line 5 -- unexpected token: bar
    >>> p3.pprint()
    Key((1, 2)):
      First adjustment:
        FUnit adjustment to origin's x-coordinate: -123
    Key((3, 4)):
      Second adjustment:
        FUnit adjustment to origin's x-coordinate: -456
    Key((5, 6)):
      First adjustment:
        FUnit adjustment to horizontal advance: 789
    Key((7, 8)):
      Second adjustment:
        FUnit adjustment to horizontal advance: 987
    """
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("pair")

    terminalStrings = ('subtable end', 'lookup end')
    startingLineNumber = fws.lineNumber
    for line in fws:
        if line in terminalStrings:
            break

        if len(line) > 0:
            tokens = [x.strip() for x in line.split('\t')]
            if tokens[0].lower() in ['firstclass definition begin',
                             'secondclass definition begin']:
                fws.goto(startingLineNumber + 1)

                return pairclasses.PairClasses.fromValidatedFontWorkerSource(
                    fws, logger=logger, **kwArgs)

            elif tokens[0].lower() in ['left x advance', 'left x placement',
                               'left y advance', 'left y placement',
                               'right x advance', 'right x placement',
                               'right y advance', 'right y placement']:
                fws.goto(startingLineNumber + 1)

                return pairglyphs.PairGlyphs.fromValidatedFontWorkerSource(
                    fws, logger=logger, **kwArgs)

            else:
                logger.warning((
                    'V0960',
                    (fws.lineNumber, tokens[0]),
                    'line %d -- unexpected token: %s'))

    logger.warning(('V0961',
        (fws.lineNumber,),
        'line %d -- reached end of lookup unexpectedly'))

    return None


def Pair_validated(w, **kwArgs):
    """
    Factory function for creating either PairClasses or PairGlyphs objects from
    a walker, with source validation.
    
    >>> logger = utilities.makeDoctestLogger("test")
    >>> w = walkerbit.StringWalker(_testingValues[0].binaryString())
    >>> _testingValues[0] == Pair_validated(w, logger=logger)
    test.pair - DEBUG - Walker has 82 remaining bytes.
    test.pair.pairglyphs - DEBUG - Walker has 82 remaining bytes.
    test.pair.pairglyphs.coverage - DEBUG - Walker has 68 remaining bytes.
    test.pair.pairglyphs.coverage - DEBUG - Format is 1, count is 2
    test.pair.pairglyphs.coverage - DEBUG - Raw data are [8, 10]
    test.pair.pairglyphs.second glyph 15.pairvalues - DEBUG - Walker has 56 remaining bytes.
    test.pair.pairglyphs.second glyph 15.pairvalues.value - DEBUG - Walker has 56 remaining bytes.
    test.pair.pairglyphs.second glyph 15.pairvalues.value - DEBUG - Walker has 52 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues - DEBUG - Walker has 44 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 44 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
    test.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 40 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues - DEBUG - Walker has 30 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 30 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
    test.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 26 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - Walker has 8 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - StartSize=12, endSize=18, format=1
    test.pair.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - Data are (35844,)
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - Walker has 20 remaining bytes.
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - StartSize=12, endSize=20, format=2
    test.pair.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - Data are (48624, 32, 12288)
    True
    
    >>> w = walkerbit.StringWalker(_testingValues[1].binaryString())
    >>> _testingValues[1] == Pair_validated(w, logger=logger)
    test.pair - DEBUG - Walker has 140 remaining bytes.
    test.pair.pairclasses - DEBUG - Walker has 140 remaining bytes.
    test.pair.pairclasses.coverage - DEBUG - Walker has 64 remaining bytes.
    test.pair.pairclasses.coverage - DEBUG - Format is 1, count is 4
    test.pair.pairclasses.coverage - DEBUG - Raw data are [5, 6, 7, 15]
    test.pair.pairclasses.first.classDef - DEBUG - Walker has 52 remaining bytes.
    test.pair.pairclasses.first.classDef - DEBUG - ClassDef is format 2.
    test.pair.pairclasses.first.classDef - DEBUG - Count is 3
    test.pair.pairclasses.first.classDef - DEBUG - Raw data are [(5, 6, 1), (7, 7, 2), (15, 15, 1)]
    test.pair.pairclasses.second.classDef - DEBUG - Walker has 30 remaining bytes.
    test.pair.pairclasses.second.classDef - DEBUG - ClassDef is format 2.
    test.pair.pairclasses.second.classDef - DEBUG - Count is 1
    test.pair.pairclasses.second.classDef - DEBUG - Raw data are [(20, 22, 1)]
    test.pair.pairclasses.class (0,0).pairvalues - DEBUG - Walker has 124 remaining bytes.
    test.pair.pairclasses.class (0,0).pairvalues.value - DEBUG - Walker has 124 remaining bytes.
    test.pair.pairclasses.class (0,0).pairvalues.value - DEBUG - Walker has 120 remaining bytes.
    test.pair.pairclasses.class (0,1).pairvalues - DEBUG - Walker has 114 remaining bytes.
    test.pair.pairclasses.class (0,1).pairvalues.value - DEBUG - Walker has 114 remaining bytes.
    test.pair.pairclasses.class (0,1).pairvalues.value - DEBUG - Walker has 110 remaining bytes.
    test.pair.pairclasses.class (1,0).pairvalues - DEBUG - Walker has 104 remaining bytes.
    test.pair.pairclasses.class (1,0).pairvalues.value - DEBUG - Walker has 104 remaining bytes.
    test.pair.pairclasses.class (1,0).pairvalues.value - DEBUG - Walker has 100 remaining bytes.
    test.pair.pairclasses.class (1,1).pairvalues - DEBUG - Walker has 94 remaining bytes.
    test.pair.pairclasses.class (1,1).pairvalues.value - DEBUG - Walker has 94 remaining bytes.
    test.pair.pairclasses.class (1,1).pairvalues.value - DEBUG - Walker has 90 remaining bytes.
    test.pair.pairclasses.class (2,0).pairvalues - DEBUG - Walker has 84 remaining bytes.
    test.pair.pairclasses.class (2,0).pairvalues.value - DEBUG - Walker has 84 remaining bytes.
    test.pair.pairclasses.class (2,0).pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
    test.pair.pairclasses.class (2,0).pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
    test.pair.pairclasses.class (2,0).pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
    test.pair.pairclasses.class (2,0).pairvalues.value - DEBUG - Walker has 80 remaining bytes.
    test.pair.pairclasses.class (2,1).pairvalues - DEBUG - Walker has 74 remaining bytes.
    test.pair.pairclasses.class (2,1).pairvalues.value - DEBUG - Walker has 74 remaining bytes.
    test.pair.pairclasses.class (2,1).pairvalues.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
    test.pair.pairclasses.class (2,1).pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
    test.pair.pairclasses.class (2,1).pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
    test.pair.pairclasses.class (2,1).pairvalues.value - DEBUG - Walker has 70 remaining bytes.
    test.pair.pairclasses.class (2,1).pairvalues.value.xPlaDevice.device - DEBUG - Walker has 8 remaining bytes.
    test.pair.pairclasses.class (2,1).pairvalues.value.xPlaDevice.device - DEBUG - StartSize=12, endSize=18, format=1
    test.pair.pairclasses.class (2,1).pairvalues.value.xPlaDevice.device - DEBUG - Data are (35844,)
    test.pair.pairclasses.class (2,1).pairvalues.value.yPlaDevice.device - DEBUG - Walker has 20 remaining bytes.
    test.pair.pairclasses.class (2,1).pairvalues.value.yPlaDevice.device - DEBUG - StartSize=12, endSize=20, format=2
    test.pair.pairclasses.class (2,1).pairvalues.value.yPlaDevice.device - DEBUG - Data are (48624, 32, 12288)
    test.pair.pairclasses - INFO - The following glyphs appear in non-first ClassDefs only, and are not in the Coverage: [20, 21, 22]
    test.pair.pairclasses - INFO - The following glyphs appear in the Coverage and in only the first ClassDef: [5, 6, 7, 15]
    True
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("pair")
    
    logger.debug((
      'V0001',
      (w.length(),),
      "Walker has %d remaining bytes."))
    
    if w.length() < 2:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    format = w.unpack("H", advance=False)
    
    if format not in {1, 2}:
        logger.error((
          'E4108',
          (format,),
          "The format %d is not valid; should be 1 or 2."))
        
        return None
    
    if format == 1:
        return pairglyphs.PairGlyphs.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
    
    return pairclasses.PairClasses.fromvalidatedwalker(
      w,
      logger = logger,
      **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer, walkerbit
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    _testingValues = (
        pairglyphs._testingValues[0],
        pairclasses._testingValues[0])

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'B': 2,
        'C': 3,
        'D': 4,
        'E': 5,
        'F': 6,
        'G': 7,
        'H': 8
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws1 = FontWorkerSource(StringIO(
        """
        left x placement	A	B	-123
        right x placement	C	D	-456
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        firstclass definition begin
        A	1
        B	2
        class definition end
        
        secondclass definition begin
        C	1
        D	2
        class definition end
        
        left x placement	1	2	-123
        right x placement	2	1	-456
        lookup end
        """))
    

    _test_FW_fws3 = FontWorkerSource(StringIO(
        """
        foo
        left x placement	A	B	-123
        right x placement	C	D	-456
        bar
        left x advance	E	F	789
        right x advance	G	H	987
        lookup end
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
