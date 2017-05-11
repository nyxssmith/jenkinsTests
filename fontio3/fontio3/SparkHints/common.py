#
# common.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Common constants (like opcode names) used throughout the hints package.
"""

# -----------------------------------------------------------------------------

#
# Constants
#

rawOpcodeToNameMap = {
  0x00: "SVTCA[y]",
  0x01: "SVTCA[x]",
  0x5D: "DELTAP1",
  0x5E: "SDB",
  0x5F: "SDS",
  0x71: "DELTAP2",
  0x72: "DELTAP3",
  0x7F: "AA",
  0xA1: "DELTAG1",
  0xA2: "STROKEDELTA1",
  0xA3: "STROKEDELTA2",
  0xA4: "STROKEDELTA3",
  0xA5: "DELTAG2",
  0xA6: "DELTAG3",
  0xA7: "DELTAK1",
  0xA8: "DELTAK2",
  0xA9: "DELTAK3",
  0xAA: "DELTAL1",
  0xAB: "DELTAL2",
  0xAC: "DELTAL3",
  0xAD: "DELTAS1",
  0xAE: "DELTAS2",
  0xAF: "DELTAS3"}

opcodeToNameMap = dict.fromkeys(range(256), 'INVALID')
opcodeToNameMap.update(rawOpcodeToNameMap)

# we don't preserve the "INVALID" entries in the following reverse map
nameToOpcodeMap = {v: k for k, v in rawOpcodeToNameMap.items()}

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
    _test()

