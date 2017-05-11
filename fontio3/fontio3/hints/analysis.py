#
# analysis.py
#
# Copyright © 2007-2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Classes and functions used to analyze streams of hints.
"""

# Other imports
from fontio3 import utilities
from fontio3.hints import common, hints_tt

# -----------------------------------------------------------------------------

#
# Constants
#

nameToOpcodeMap = common.nameToOpcodeMap

op_FDEF = nameToOpcodeMap["FDEF"]
op_ENDF = nameToOpcodeMap["ENDF"]
op_IDEF = nameToOpcodeMap["IDEF"]

Hints = hints_tt.Hints

# -----------------------------------------------------------------------------

#
# Classes
#

class Analysis(object):
    """
    Singleton object supporting analysis of the FDEFs and IDEFs in the 'fpgm'
    table of a TrueType font.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, hintsObj):
        self.hintsObj = hintsObj
    
    #
    # Public methods
    #
    
    def splitFDEFs(self, **kwArgs):
        """
        Returns a dictionary whose keys are FDEF numbers and whose values are
        Hints-class objects (subsets of the original hint stream). A ValueError
        is raised if FDEFs and ENDFs are not balanced.
        
        There is one optional keyword argument:
        
            dIDEF   An empty dictionary which will be filled with entries whose
                    keys are IDEF opcode numbers and whose values are Hints
                    objects associated with the IDEF. A client can use this,
                    for example, to remap IDEFs into their component hints.
        
        >>> s = utilities.fromhex("B1 01 00 2C 21 2D 2C B0 44 4B 2D")
        >>> h = Hints.frombytes(s)
        >>> r = Analysis(h).splitFDEFs()
        >>> for n in sorted(r): print(n, str(r[n]))
        0 [POP]
        1 [PUSH [68], MPPEM]
        
        >>> s = utilities.fromhex("2D")
        >>> h = Hints.frombytes(s)
        >>> Analysis(h).splitFDEFs()
        Traceback (most recent call last):
          ...
        ValueError: ENDF appeared without FDEF or IDEF!
        
        >>> s = utilities.fromhex("B1 01 00 2C 2C")
        >>> h = Hints.frombytes(s)
        >>> Analysis(h).splitFDEFs()
        Traceback (most recent call last):
          ...
        ValueError: Nested FDEFs not allowed!
        
        >>> s = utilities.fromhex("B0 93 89 01 88 2D")
        >>> h = Hints.frombytes(s)
        >>> dIDEF = {}
        >>> Analysis(h).splitFDEFs(dIDEF=dIDEF)
        {}
        >>> for n in sorted(dIDEF): print(n, str(dIDEF[n]))
        147 [SVTCA[x], GETINFO]
        """
        
        specialStack = []
        startIndex = -1
        dOutput = {}
        dIDEF = kwArgs.get('dIDEF', {})
        
        for i, opcodeObj in enumerate(self.hintsObj):
            if startIndex == -1:  # not in definition yet, so pushes are live
                if opcodeObj.isPush():
                    specialStack.extend(opcodeObj.data)
                
                else:
                    op = opcodeObj.opcode
                    
                    if op == op_FDEF or op == op_IDEF:
                        dIndex = specialStack.pop()
                        startIndex = i
                        isIDEFCase = (op == op_IDEF)
                    
                    elif op == op_ENDF:
                        raise ValueError("ENDF appeared without FDEF or IDEF!")
            
            elif not opcodeObj.isPush():
                op = opcodeObj.opcode
                
                if op == op_ENDF:
                    if isIDEFCase:
                        info = "IDEF %d" % (dIndex,)
                        
                        dIDEF[dIndex] = Hints(
                          self.hintsObj[startIndex+1:i],
                          infoString=info,
                          isFDEF=False)
                    
                    else:
                        info = "FDEF %d" % (dIndex,)
                        
                        dOutput[dIndex] = Hints(
                          self.hintsObj[startIndex+1:i],
                          infoString=info,
                          isFDEF=True)
                    
                    startIndex = -1
                
                elif op == op_FDEF:
                    raise ValueError("Nested FDEFs not allowed!")
                
                elif op == op_IDEF:
                    raise ValueError("Nested IDEFs not allowed!")
        
        if startIndex != -1: # allow for unclosed final FDEF or IDEF
            if isIDEFCase:
                info = "IDEF %d" % (dIndex,)
                
                dIDEF[dIndex] = Hints(
                  self.hintsObj[startIndex+1:-1],
                  infoString=info,
                  isFDEF=False)
            
            else:
                info = "FDEF %d" % (dIndex,)
                
                dOutput[dIndex] = Hints(
                  self.hintsObj[startIndex+1:-1],
                  infoString=info,
                  isFDEF=True)
        
        return dOutput

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

