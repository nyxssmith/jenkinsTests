#
# hint_eif.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the EIF opcode.
"""

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_EIF(self, **kwArgs):
    """
    EIF: End IF, opcode 0x59.
    
    Because of the way _hint_IF works, a free-standing EIF should never be
    encountered "in the wild." If one is, an error is posted to the logger.
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    
    logger.error((
      'E6007',
      (self.ultParent.infoString, state.pc + self.ultDelta),
      "EIF opcode found alone in %s (PC %d)."))
    
    state._validationFailed = True
    state.assign('pc', state.pc + 1)

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
