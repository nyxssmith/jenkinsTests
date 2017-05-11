#
# postcomp_action_single.py
#
# Copyright © 2012-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a single postcompensation action.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

from fontio3.just import (
  postcomp_conditionaladd,
  postcomp_decomposition,
  postcomp_ductile,
  postcomp_repeatedadd,
  postcomp_stretch,
  postcomp_unconditionaladd)

# -----------------------------------------------------------------------------

#
# Private constants
#

_makers = {
  0: postcomp_decomposition.Postcomp_Decomposition,
  1: postcomp_unconditionaladd.Postcomp_UnconditionalAdd,
  2: postcomp_conditionaladd.Postcomp_ConditionalAdd,
  3: postcomp_stretch.Postcomp_Stretch,
  4: postcomp_ductile.Postcomp_Ductile,
  5: postcomp_repeatedadd.Postcomp_RepeatedAdd}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_class(obj, **kwArgs):
    logger = kwArgs['logger']
    
    try: n = int(obj)
    except: n = None
    
    if n is None or n != obj:
        logger.error((
          'G0024',
          (n,),
          "The justification class value %r is not an integer."))
        
        return False
    
    if n < 0 or n > 127:
        logger.error((
          'V0741',
          (n,),
          "The justification class value of %d is out of range. It must "
          "be between 0 and 127 inclusive."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Postcomp_Action_Single(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single postcomp action. These are records in the
    Postcomp_Action object. The following attributes are defined:
    
        action          The action object. This will be an object of one of the
                        concrete types, like Postcomp_UnconditionalAdd or
                        Postcomp_Ductile.
        
        actionClass     A 7-bit value with the justification class value
                        associated with this action.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Specific action:
      Lower trigger for decomposition: 0.75
      Upper trigger for decomposition: 1.75
      Order (lower=earlier): 2
      Decomposed glyphs:
        0: xyz44
        1: xyz42
        2: afii60002
    Justification class: 1
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Specific action:
      Glyph to be added: xyz40
    Justification class: 0
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    Specific action:
      Trigger threshold: 1.0
      Glyph to be substituted: xyz49
    Justification class: 2
    
    >>> _testingValues[3].pprint(namer=namer.testingNamer())
    Specific action:
      Stretch glyph
    Justification class: 1
    
    >>> _testingValues[4].pprint(namer=namer.testingNamer())
    Specific action:
      Ductility axis: 'duct'
      Lower limit for ductility: 1.0
      Default value: 1.0
      Upper limit for ductility: 2.0
    Justification class: 4
    
    >>> _testingValues[5].pprint(namer=namer.testingNamer())
    Specific action:
      Glyph to be repeatedly added: xyz40
    Justification class: 0
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        actionClass = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Justification class",
            attr_validatefunc = _validate_class),
        
        action = dict(
            attr_followsprotocol = True,
            attr_label = "Specific action"))
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_Action_Single from the specified
        walker, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("pas_fvw")
        >>> fvb = Postcomp_Action_Single.fromvalidatedbytes
        
        >>> s = _testingValues[0].binaryString()
        >>> obj = fvb(s, logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 28 remaining bytes.
        pas_fvw.postcomp_action_single.postcomp_decomposition - DEBUG - Walker has 20 remaining bytes.
        pas_fvw.postcomp_action_single.postcomp_decomposition.glyphtuple - DEBUG - Walker has 10 bytes remaining.
        pas_fvw.postcomp_action_single.postcomp_decomposition.glyphtuple - DEBUG - Count is 3
        pas_fvw.postcomp_action_single.postcomp_decomposition.glyphtuple - DEBUG - Data are (43, 41, 97)
        
        >>> fvb(s[:6], logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 6 remaining bytes.
        pas_fvw.postcomp_action_single - ERROR - Insufficient bytes.
        
        >>> s = _testingValues[1].binaryString()
        >>> obj = fvb(s, logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 12 remaining bytes.
        pas_fvw.postcomp_action_single.postcomp_unconditionaladd - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:6], logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 6 remaining bytes.
        pas_fvw.postcomp_action_single - ERROR - Insufficient bytes.
        
        >>> s = _testingValues[2].binaryString()
        >>> obj = fvb(s, logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 16 remaining bytes.
        pas_fvw.postcomp_action_single.postcomp_conditionaladd - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:6], logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 6 remaining bytes.
        pas_fvw.postcomp_action_single - ERROR - Insufficient bytes.
        
        >>> s = _testingValues[3].binaryString()
        >>> obj = fvb(s, logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:6], logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 6 remaining bytes.
        pas_fvw.postcomp_action_single - ERROR - Insufficient bytes.
        
        >>> s = _testingValues[4].binaryString()
        >>> obj = fvb(s, logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 24 remaining bytes.
        pas_fvw.postcomp_action_single.postcomp_ductile - DEBUG - Walker has 16 remaining bytes.
        
        >>> fvb(s[:6], logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 6 remaining bytes.
        pas_fvw.postcomp_action_single - ERROR - Insufficient bytes.
        
        >>> s = _testingValues[5].binaryString()
        >>> obj = fvb(s, logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 12 remaining bytes.
        pas_fvw.postcomp_action_single.postcomp_repeatedadd - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:6], logger=logger)
        pas_fvw.postcomp_action_single - DEBUG - Walker has 6 remaining bytes.
        pas_fvw.postcomp_action_single - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("postcomp_action_single")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        aClass, aKind, aLength = w.unpack("2HL")
        
        if aClass >= 128:
            logger.error((
              'V0741',
              (aClass,),
              "The justification class value of %d is out of range. It must "
              "be between 0 and 127 inclusive."))
            
            return None
        
        if aKind not in _makers:
            logger.error((
              'V0742',
              (aKind,),
              "The postcomp action kind %d is unknown."))
            
            return None
        
        wSub = w.subWalker(0, relative=True, newLimit=aLength-8)
        obj = _makers[aKind].fromvalidatedwalker(w, logger=logger, **kwArgs)
        
        if obj is None:
            return None
        
        return cls(actionClass=aClass, action=obj)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Postcomp_Action_Single from the specified
        walker.
        
        >>> fb = Postcomp_Action_Single.frombytes
        >>> for i in range(6):
        ...   obj = _testingValues[i]
        ...   print(obj == fb(obj.binaryString()))
        True
        True
        True
        True
        True
        True
        """
        
        aClass, aKind, aLength = w.unpack("2HL")
        wSub = w.subWalker(0, relative=True, newLimit=aLength-8)
        obj = _makers[aKind].fromwalker(w, **kwArgs)
        return cls(actionClass=aClass, action=obj)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Postcomp_Action_Single object to the
        specified writer.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0000 0000 001C  0000 C000 0001 C000 |................|
              10 | 0002 0003 002B 0029  0061 0000           |.....+.).a..    |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0001 0000 000C  0027 0000           |.........'..    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0002 0002 0000 0010  0001 0000 FFFF 0030 |...............0|
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0001 0003 0000 0008                      |........        |
        
        >>> utilities.hexdump(_testingValues[4].binaryString())
               0 | 0004 0004 0000 0018  6475 6374 0001 0000 |........duct....|
              10 | 0001 0000 0002 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[5].binaryString())
               0 | 0000 0005 0000 000C  0000 0027           |...........'    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2H", self.actionClass, self.action.kind)
        finalStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, finalStake)
        self.action.buildBinary(w, **kwArgs)
        w.alignToByteMultiple(4)
        w.stakeCurrentWithValue(finalStake)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        Postcomp_Action_Single(
          actionClass = 1,
          action = postcomp_decomposition._testingValues[1]),       # kind 0
        
        Postcomp_Action_Single(
          actionClass = 0,
          action = postcomp_unconditionaladd._testingValues[1]),    # kind 1
        
        Postcomp_Action_Single(
          actionClass = 2,
          action = postcomp_conditionaladd._testingValues[1]),      # kind 2
        
        Postcomp_Action_Single(
          actionClass = 1,
          action = postcomp_stretch._testingValues[0]),             # kind 3
        
        Postcomp_Action_Single(
          actionClass = 4,
          action = postcomp_ductile._testingValues[1]),             # kind 4
        
        Postcomp_Action_Single(
          actionClass = 0,
          action = postcomp_repeatedadd._testingValues[1]))         # kind 5

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
