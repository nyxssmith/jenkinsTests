#
# format4analyzer.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for analyzing the current and marked glyph sets associated with each
entry index in a format 4 'kerx' subtable.
"""

# Other imports
from fontio3 import utilities
from fontio3.statetables import stutils
from fontio3.utilities import lookup

# -----------------------------------------------------------------------------

#
# Constants
#

fixedClassNames = frozenset([
  "End of text",
  "Out of bounds",
  "Deleted glyph",
  "End of line"])

# -----------------------------------------------------------------------------

#
# Classes
#

class Analyzer:
    """
    """
    
    #
    # Methods
    #
    
    def __init__(self, f4Obj):
        """
        Initializes the object with the specified walker. Note the walker is
        not copied; rather, its reset() method is called before processing
        starts.
        """
        
        self.f4Obj = f4Obj
        self.analysis = None
    
    def _buildInputs(self):
        self.entryTable = {}  # immut(entryObj) -> entryObj
        
        for row in self.f4Obj.values():
            for entryObj in row.values():
                immut = entryObj.asImmutable()
                
                if immut not in self.entryTable:
                    self.entryTable[immut] = entryObj
        
        d = utilities.invertDictFull(self.f4Obj.classTable, asSets=True)
        
        self.classNameToGlyphs = {
          k: v
          for k, v in d.items()
          if k not in fixedClassNames}
        
        self.classNameToGlyphs["Deleted glyph"] = {0xFFFF}
        nonFixedClassNames = set(self.f4Obj["Start of text"]) - fixedClassNames
        self.emptyClassNames = nonFixedClassNames - set(self.classNameToGlyphs)
    
    def _doAnalysis(self):
        self._buildInputs()
        self.analysis = set()  # (stateName, className, markSet, currSet)
        self.entryImmutToMarkSets = {}  # immut(entry) -> set(glyphs)
        self.entryImmutToCurrSets = {}  # immut(entry) -> set(glyphs)
        self._fillStateRecs("Start of text", set())
        self._fillStateRecs("Start of line", set())
    
    def _fillStateRecs(self, stateName, markSet):
        thisState = self.f4Obj[stateName]
        newToDo = set()
        
        for className, entryObj in thisState.items():
            if className in self.emptyClassNames:
                continue
            
            entryImmut = entryObj.asImmutable()
            
            if className in fixedClassNames and className != "Deleted glyph":
                currSet = set()
            else:
                currSet = self.classNameToGlyphs[className]
            
            t = (
              stateName,
              className,
              frozenset(markSet),
              frozenset(currSet))
            
            if t not in self.analysis:
                newStateName = entryObj.newState
                mark = entryObj.mark
                actionObj = entryObj.action
                
                if actionObj is not None:
                    assert markSet
                    assert currSet
                    s = self.entryImmutToMarkSets.setdefault(entryImmut, set())
                    s.update(markSet)
                    s = self.entryImmutToCurrSets.setdefault(entryImmut, set())
                    s.update(currSet)
                
                if newStateName not in {"Start of text", "Start of line"}:
                    if mark:
                        
                        if (
                          (className == "Deleted glyph") and
                          (newStateName == stateName)):
                            
                            # If this case arises, the deleted glyph is being
                            # marked and then passed to this same state. This
                            # is a font bug; the mark bit should not be set in
                            # this case. This logic prevents the recursion from
                            # continuing down in this case.
                            
                            pass
                        
                        else:  # mark the current set
                            newToDo.add((newStateName, frozenset(currSet)))
                
                self.analysis.add(t)
        
        # now do the recursive calls back to this method
        for newStateName, newMarkSet in newToDo:
            self._fillStateRecs(newStateName, newMarkSet)
    
    def analyze(self, **kwArgs):
        """
        >>> m, c, et = Analyzer(_makef4()).analyze()
        >>> p = pp.PP()
        >>> for immut, gs in m.items():
        ...     et[immut].pprint()
        ...     print("maps to marked glyphs", gs)
        Go to state 'Start of text' after doing this alignment:
          Marked glyph's point: 8
          Current glyph's point: 16
        maps to marked glyphs {10, 11}
        
        >>> for immut, gs in c.items():
        ...     et[immut].pprint()
        ...     print("maps to current glyphs", gs)
        Go to state 'Start of text' after doing this alignment:
          Marked glyph's point: 8
          Current glyph's point: 16
        maps to current glyphs {20, 21, 22}
        """
        
        if self.analysis is None:
            if 'logger' in kwArgs:
                if not self._doAnalysis_validated(kwArgs['logger']):
                    self.entryImmutToMarkSets = None
                    self.entryImmutToCurrSets = None
            
            else:
                self._doAnalysis()
        
        return (
          self.entryImmutToMarkSets,
          self.entryImmutToCurrSets,
          self.entryTable)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import pp
    
    # We'll do a fairly simple example. Here, glyphs 10 and 11, control point
    # 8 connect with glyphs 20, 21, and 22, control point 16.
    
    def _makef4():
        from fontio3.kerx import format4
        
        sv = [
          "00 00 00 06",    # numClasses
          "00 00 00 14",    # offset to class table
          "00 00 00 34",    # offset to state array
          "00 00 00 58",    # offset to entry table
          "00 00 00 70",    # flags and offset to control point table
      
          # Class table starts here (offset = 0x0014 bytes)
          "00 02",                          # lookup format 2
          "00 06 00 02 00 0C 00 01 00 00",  # binary search header
          "00 0B 00 0A 00 04",              # segment 0 -> class 4
          "00 16 00 14 00 05",              # segment 1 -> class 5
          "FF FF FF FF FF FF",              # guardian
          "00 00",                          # padding to 32-bit alignment (needed?)
      
          # State array starts here (offset = 0x0034 bytes)
          "00 00 00 00 00 00 00 00 00 01 00 00",    # SOT
          "00 00 00 00 00 00 00 00 00 01 00 00",    # SOL
          "00 00 00 00 00 02 00 00 00 01 00 03",    # Saw first
      
          # Entry array starts here (offset = 0x0058 bytes)
          "00 00 00 00 FF FF",  # entry 0 - NOP
          "00 02 80 00 FF FF",  # entry 1 - mark and go to state "Saw first"
          "00 02 00 00 FF FF",  # entry 2 - go to state "Saw first"
          "00 00 00 00 00 00",  # entry 3 - do the attachment and go to state SOT
      
          # Control point array starts here (offset = 0x0070 bytes)
          "00 08 00 10"         # control point entry 0
          ]
    
        binData = utilities.fromhex(' '.join(sv))
        return format4.Format4.frombytes(binData)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
