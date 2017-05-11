#
# hint_iup.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the IUP opcode.
"""

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_IUP(self, **kwArgs):
    """
    IUP: Interpolate untouched points, opcodes 0x30-0x31.
    
    Keyword argument inX determines the direction.
    
    (Doctests to be added...)
    """
    
    gs = self.state.graphicsState
    logger = self._getLogger(**kwArgs)
    
    if gs.zonePointer2 != 1:
        logger.error((
          'E6032',
          (self.ultParent.infoString, self.state.pc + self.ultDelta),
          "IUP opcode in %s (PC %d) has ZP2 set to something other than "
          "one. This opcode cannot move points in the twilight zone."))
        
        self.state._validationFailed = True
    
    self.state.assign('pc', self.state.pc + 1)

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
