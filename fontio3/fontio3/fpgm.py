#
# fpgm.py
#
# Copyright © 2004-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType "fpgm' tables.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.hints import common, hints_tt, opcode_tt

# -----------------------------------------------------------------------------

#
# Constants
#

_fdef44_bad = bytes.fromhex(
  "20 B0 03 25 45 50 58 8A "
  "20 45 8A 8B 44 21 1B 21 "
  "45 44 59")

_fdef44_good = bytes.fromhex(
  "21 21 0C 64 23 64 8B B8 "
  "40 00 62")

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if obj and (44 in obj) and (obj[44].binaryString() == _fdef44_bad):
        logger.warning((
          'Vxxxx',
          (),
          "FDEF 44 in this fpgm is the incorrect one. Please fix it."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Fpgm(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'fpgm' tables. These are dicts whose keys are
    FDEF numbers and whose values are hints_tt.Hints objects.
    
    >>> _testingValues[1].pprint()
    Function #2:
      0000 (0x000000): PUSH
                         (1, 2, 3)
      0001 (0x000004): LT
    Function #25:
      0000 (0x000000): SVTCA[y]
      0001 (0x000001): SVTCA[x]
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Function #%d" % (i,)),
        item_pprintlabelpresort = True,
        item_renumberfdefsdirectkeys = True,
        map_validatefunc = _validate)
    
    #
    # Methods
    #
    
    @staticmethod
    def _split(h, **kwArgs):
        """
        Given a Hints object representing the entire 'fpgm' table, this method
        breaks it up into separate FDEFs and IDEFs. If a logger is specified in
        the keyword arguments, it will be used to post errors and warnings;
        otherwise, ValueErrors will be raised.
        """
        
        specialStack = []
        startIndex = -1
        dOutput = {}
        dIDEF = kwArgs.get('dIDEF', {})
        op_ENDF = common.nameToOpcodeMap["ENDF"]
        op_FDEF = common.nameToOpcodeMap["FDEF"]
        op_IDEF = common.nameToOpcodeMap["IDEF"]
        logger = kwArgs.get('logger', None)
        rawMap = set(common.rawOpcodeToNameMap)
        rawMap -= set(range(0xA2, 0xB0))
        
        for i, opcodeObj in enumerate(h):
            if startIndex == -1:  # not in definition yet, so pushes are live
                if opcodeObj.isPush():
                    specialStack.extend(opcodeObj.data)
                
                else:
                    op = opcodeObj.opcode
                    
                    if op == op_FDEF or op == op_IDEF:
                        dIndex = specialStack.pop()
                        startIndex = i
                        isIDEFCase = (op == op_IDEF)
                        
                        if isIDEFCase:
                            if not (0 <= dIndex < 256):
                                logger.error((
                                  'E6025',
                                  (dIndex,),
                                  "Cannot define opcode %d; not 0-255."))
                                
                                return {}
                            
                            if dIndex in rawMap:
                                logger.error((
                                  'E6026',
                                  (dIndex,),
                                  "Cannot redefine built-in opcode 0x%02X."))
                                
                                return {}
                    
                    elif op == op_ENDF:
                        if logger is None:
                            raise ValueError(
                              "ENDF appeared without FDEF or IDEF!")
                        
                        else:
                            logger.error((
                              'V0173',
                              (),
                              "ENDF appeared without FDEF or IDEF."))
                            
                            return None
            
            elif not opcodeObj.isPush():
                op = opcodeObj.opcode
                
                if op == op_ENDF:
                    if isIDEFCase:
                        info = "IDEF %d" % (dIndex,)
                        
                        dIDEF[dIndex] = hints_tt.Hints(
                          h[startIndex+1:i],
                          infoString=info,
                          isFDEF=False)
                        
                        if logger is not None:
                            logger.warning((
                              'V0174',
                              (info,),
                              "%s encountered; note that IDEFs "
                              "are deprecated."))
                    
                    else:
                        info = "FDEF %d" % (dIndex,)
                        
                        dOutput[dIndex] = hints_tt.Hints(
                          h[startIndex+1:i],
                          infoString=info,
                          isFDEF=True)
                    
                    startIndex = -1
                
                elif op == op_FDEF:
                    if logger is None:
                        raise ValueError("Nested FDEFs not allowed!")
                    
                    else:
                        logger.error((
                          'V0175',
                          (),
                          "Nested FDEFs are not permitted."))
                        
                        return None
                
                elif op == op_IDEF:
                    if logger is None:
                        raise ValueError("Nested IDEFs not allowed!")
                    
                    else:
                        logger.error((
                          'V0176',
                          (),
                          "Nested IDEFs are not permitted."))
                        
                        return None
        
        if startIndex != -1: # allow for unclosed final FDEF or IDEF
            if isIDEFCase:
                info = "IDEF %d" % (dIndex,)
                
                dIDEF[dIndex] = hints_tt.Hints(
                  h[startIndex+1:-1],
                  infoString=info,
                  isFDEF=False)
                
                if logger is not None:
                    logger.warning((
                      'V0177',
                      (info,),
                      "%s was not explicitly closed with an ENDF."))
            
            else:
                info = "FDEF %d" % (dIndex,)
                
                dOutput[dIndex] = hints_tt.Hints(
                  h[startIndex+1:-1],
                  infoString=info,
                  isFDEF=True)
                
                if logger is not None:
                    logger.warning((
                      'V0178',
                      (info,),
                      "%s was not explicitly closed with an ENDF."))
        
        return dOutput
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for the Fpgm object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | B119 022C B201 0203  502D 2C00 012D      |...,....P-,..-  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        keysObj = opcode_tt.Opcode_push(sorted(self, reverse=True))
        w.addString(keysObj.binaryString())
        op_ENDF = common.nameToOpcodeMap["ENDF"]
        op_FDEF = common.nameToOpcodeMap["FDEF"]
        
        for key in sorted(self):
            w.add("B", op_FDEF)
            w.addString(self[key].binaryString())
            w.add("B", op_ENDF)
    
    def fix44(self):
        """
        If FDEF 44 in self is the corrupted one, this method replaces it with
        the corrected one. If this substitution actually happened, True is
        returned; otherwise False is returned.
        """
        
        if (44 in self) and (self[44].binaryString() == _fdef44_bad):
            self[44] = hints_tt.Hints.frombytes(
              _fdef44_good,
              infoString = self[44].infoString)
            
            return True
        
        return False
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Fpsm. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> Fpgm.fromvalidatedbytes(s, logger=logger).pprint()
        test.fpgm - DEBUG - Walker has 14 remaining bytes.
        Function #2:
          0000 (0x000000): PUSH
                             (1, 2, 3)
          0001 (0x000004): LT
        Function #25:
          0000 (0x000000): SVTCA[y]
          0001 (0x000001): SVTCA[x]
        
        >>> obj = Fpgm.fromvalidatedbytes(s[:-1], logger=logger)
        test.fpgm - DEBUG - Walker has 13 remaining bytes.
        test.fpgm - WARNING - FDEF 25 was not explicitly closed with an ENDF.
        
        >>> s2 = utilities.fromhex("B0 01 2C 2C")
        >>> Fpgm.fromvalidatedbytes(s2, logger=logger)
        test.fpgm - DEBUG - Walker has 4 remaining bytes.
        test.fpgm - ERROR - Nested FDEFs are not permitted.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('fpgm')
        else:
            logger = logger.getChild('fpgm')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        r = cls()
        h = hints_tt.Hints.fromwalker(w, **kwArgs)
        d = cls._split(h, logger=logger, **kwArgs)
        
        if d is None:
            return None
        
        r.update(d)
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Fpgm object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Fpgm.frombytes(obj.binaryString())
        True
        """
        
        r = cls()
        h = hints_tt.Hints.fromwalker(w, **kwArgs)
        r.update(cls._split(h, **kwArgs))
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    s = utilities.fromhex("B1 19 02 2C B2 01 02 03 50 2D 2C 00 01 2D")
    
    _testingValues = (
        Fpgm(),
        Fpgm.frombytes(s))
    
    del s

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
