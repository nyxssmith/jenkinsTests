#
# common.py
#
# Copyright © 2005-2014 Monotype Imaging Inc. All Rights Reserved.
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
    0x02: "SPVTCA[y]",
    0x03: "SPVTCA[x]",
    0x04: "SFVTCA[y]",
    0x05: "SFVTCA[x]",
    0x06: "SPVTL[parallel]",
    0x07: "SPVTL[perpendicular]",
    0x08: "SFVTL[parallel]",
    0x09: "SFVTL[perpendicular]",
    0x0A: "SPVFS",
    0x0B: "SFVFS",
    0x0C: "GPV",
    0x0D: "GFV",
    0x0E: "SFVTPV",
    0x0F: "ISECT",
    0x10: "SRP0",
    0x11: "SRP1",
    0x12: "SRP2",
    0x13: "SZP0",
    0x14: "SZP1",
    0x15: "SZP2",
    0x16: "SZPS",
    0x17: "SLOOP",
    0x18: "RTG",
    0x19: "RTHG",
    0x1A: "SMD",
    0x1B: "ELSE",
    0x1C: "JMPR",
    0x1D: "SCVTCI",
    0x1E: "SSWCI",
    0x1F: "SSW",
    0x20: "DUP",
    0x21: "POP",
    0x22: "CLEAR",
    0x23: "SWAP",
    0x24: "DEPTH",
    0x25: "CINDEX",
    0x26: "MINDEX",
    0x27: "ALIGNPTS",
    0x28: "RAW",
    0x29: "UTP",
    0x2A: "LOOPCALL",
    0x2B: "CALL",
    0x2C: "FDEF",
    0x2D: "ENDF",
    0x2E: "MDAP[noRound]",
    0x2F: "MDAP[round]",
    0x30: "IUP[y]",
    0x31: "IUP[x]",
    0x32: "SHP[RP2]",
    0x33: "SHP[RP1]",
    0x34: "SHC[RP2]",
    0x35: "SHC[RP1]",
    0x36: "SHZ[RP2]",
    0x37: "SHZ[RP1]",
    0x38: "SHPIX",
    0x39: "IP",
    0x3A: "MSIRP[noSetRP0]",
    0x3B: "MSIRP[setRP0]",
    0x3C: "ALIGNRP",
    0x3D: "RTDG",
    0x3E: "MIAP[noRound]",
    0x3F: "MIAP[round]",
    0x40: "NPUSHB",
    0x41: "NPUSHW",
    0x42: "WS",
    0x43: "RS",
    0x44: "WCVTP",
    0x45: "RCVT",
    0x46: "GC[current]",
    0x47: "GC[original]",
    0x48: "SCFS",
    0x49: "MD[gridfitted]",
    0x4A: "MD[original]",
    0x4B: "MPPEM",
    0x4C: "MPS",
    0x4D: "FLIPON",
    0x4E: "FLIPOFF",
    0x4F: "DEBUG",
    0x50: "LT",
    0x51: "LTEQ",
    0x52: "GT",
    0x53: "GTEQ",
    0x54: "EQ",
    0x55: "NEQ",
    0x56: "ODD",
    0x57: "EVEN",
    0x58: "IF",
    0x59: "EIF",
    0x5A: "AND",
    0x5B: "OR",
    0x5C: "NOT",
    0x5D: "DELTAP1",
    0x5E: "SDB",
    0x5F: "SDS",
    0x60: "ADD",
    0x61: "SUB",
    0x62: "DIV",
    0x63: "MUL",
    0x64: "ABS",
    0x65: "NEG",
    0x66: "FLOOR",
    0x67: "CEILING",
    0x68: "ROUND[gray]",
    0x69: "ROUND[black]",
    0x6A: "ROUND[white]",
    0x6C: "NROUND[gray]",
    0x6D: "NROUND[black]",
    0x6E: "NROUND[white]",
    0x70: "WCVTF",
    0x71: "DELTAP2",
    0x72: "DELTAP3",
    0x73: "DELTAC1",
    0x74: "DELTAC2",
    0x75: "DELTAC3",
    0x76: "SROUND",
    0x77: "S45ROUND",
    0x78: "JROT",
    0x79: "JROF",
    0x7A: "ROFF",
    0x7C: "RUTG",
    0x7D: "RDTG",
    0x7E: "SANGW",
    0x7F: "AA",
    0x80: "FLIPPT",
    0x81: "FLIPRGON",
    0x82: "FLIPRGOFF",
    0x85: "SCANCTRL",
    0x86: "SDPVTL[parallel]",
    0x87: "SDPVTL[perpendicular]",
    0x88: "GETINFO",
    0x89: "IDEF",
    0x8A: "ROLL",
    0x8B: "MAX",
    0x8C: "MIN",
    0x8D: "SCANTYPE",
    0x8E: "INSTCTRL",
    0x8F: "ADJUST[0]",
    0x90: "ADJUST[1]",
    0xA2: "MAZDELTA1",
    0xA3: "MAZDELTA2",
    0xA4: "MAZDELTA3",
    0xA5: "MAZMODE",
    0xA6: "MAZSTROKE",
    0xA7: "DELTAK1",
    0xA8: "DELTAK2",
    0xA9: "DELTAK3",
    0xAA: "DELTAL1",
    0xAB: "DELTAL2",
    0xAC: "DELTAL3",
    0xAD: "DELTAS1",
    0xAE: "DELTAS2",
    0xAF: "DELTAS3",
    0xB0: "PUSHB[1]",
    0xB1: "PUSHB[2]",
    0xB2: "PUSHB[3]",
    0xB3: "PUSHB[4]",
    0xB4: "PUSHB[5]",
    0xB5: "PUSHB[6]",
    0xB6: "PUSHB[7]",
    0xB7: "PUSHB[8]",
    0xB8: "PUSHW[1]",
    0xB9: "PUSHW[2]",
    0xBA: "PUSHW[3]",
    0xBB: "PUSHW[4]",
    0xBC: "PUSHW[5]",
    0xBD: "PUSHW[6]",
    0xBE: "PUSHW[7]",
    0xBF: "PUSHW[8]",
    0xC0: "MDRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, gray]",
    0xC1: "MDRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, black]",
    0xC2: "MDRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, white]",
    0xC4: "MDRP[noSetRP0, noRespectMinimumDistance, roundDistance, gray]",
    0xC5: "MDRP[noSetRP0, noRespectMinimumDistance, roundDistance, black]",
    0xC6: "MDRP[noSetRP0, noRespectMinimumDistance, roundDistance, white]",
    0xC8: "MDRP[noSetRP0, respectMinimumDistance, noRoundDistance, gray]",
    0xC9: "MDRP[noSetRP0, respectMinimumDistance, noRoundDistance, black]",
    0xCA: "MDRP[noSetRP0, respectMinimumDistance, noRoundDistance, white]",
    0xCC: "MDRP[noSetRP0, respectMinimumDistance, roundDistance, gray]",
    0xCD: "MDRP[noSetRP0, respectMinimumDistance, roundDistance, black]",
    0xCE: "MDRP[noSetRP0, respectMinimumDistance, roundDistance, white]",
    0xD0: "MDRP[setRP0, noRespectMinimumDistance, noRoundDistance, gray]",
    0xD1: "MDRP[setRP0, noRespectMinimumDistance, noRoundDistance, black]",
    0xD2: "MDRP[setRP0, noRespectMinimumDistance, noRoundDistance, white]",
    0xD4: "MDRP[setRP0, noRespectMinimumDistance, roundDistance, gray]",
    0xD5: "MDRP[setRP0, noRespectMinimumDistance, roundDistance, black]",
    0xD6: "MDRP[setRP0, noRespectMinimumDistance, roundDistance, white]",
    0xD8: "MDRP[setRP0, respectMinimumDistance, noRoundDistance, gray]",
    0xD9: "MDRP[setRP0, respectMinimumDistance, noRoundDistance, black]",
    0xDA: "MDRP[setRP0, respectMinimumDistance, noRoundDistance, white]",
    0xDC: "MDRP[setRP0, respectMinimumDistance, roundDistance, black]",
    0xDD: "MDRP[setRP0, respectMinimumDistance, roundDistance, gray]",
    0xDE: "MDRP[setRP0, respectMinimumDistance, roundDistance, white]",
    0xE0: "MIRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, gray]",
    0xE1: "MIRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, black]",
    0xE2: "MIRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, white]",
    0xE4: "MIRP[noSetRP0, noRespectMinimumDistance, roundDistance, gray]",
    0xE5: "MIRP[noSetRP0, noRespectMinimumDistance, roundDistance, black]",
    0xE6: "MIRP[noSetRP0, noRespectMinimumDistance, roundDistance, white]",
    0xE8: "MIRP[noSetRP0, respectMinimumDistance, noRoundDistance, gray]",
    0xE9: "MIRP[noSetRP0, respectMinimumDistance, noRoundDistance, black]",
    0xEA: "MIRP[noSetRP0, respectMinimumDistance, noRoundDistance, white]",
    0xEC: "MIRP[noSetRP0, respectMinimumDistance, roundDistance, gray]",
    0xED: "MIRP[noSetRP0, respectMinimumDistance, roundDistance, black]",
    0xEE: "MIRP[noSetRP0, respectMinimumDistance, roundDistance, white]",
    0xF0: "MIRP[setRP0, noRespectMinimumDistance, noRoundDistance, gray]",
    0xF1: "MIRP[setRP0, noRespectMinimumDistance, noRoundDistance, black]",
    0xF2: "MIRP[setRP0, noRespectMinimumDistance, noRoundDistance, white]",
    0xF4: "MIRP[setRP0, noRespectMinimumDistance, roundDistance, gray]",
    0xF5: "MIRP[setRP0, noRespectMinimumDistance, roundDistance, black]",
    0xF6: "MIRP[setRP0, noRespectMinimumDistance, roundDistance, white]",
    0xF8: "MIRP[setRP0, respectMinimumDistance, noRoundDistance, gray]",
    0xF9: "MIRP[setRP0, respectMinimumDistance, noRoundDistance, black]",
    0xFA: "MIRP[setRP0, respectMinimumDistance, noRoundDistance, white]",
    0xFC: "MIRP[setRP0, respectMinimumDistance, roundDistance, black]",
    0xFD: "MIRP[setRP0, respectMinimumDistance, roundDistance, gray]",
    0xFE: "MIRP[setRP0, respectMinimumDistance, roundDistance, white]"
    }

opcodeToNameMap = dict.fromkeys(range(256), 'INVALID')
opcodeToNameMap.update(rawOpcodeToNameMap)

# we don't preserve the "INVALID" entries in the following reverse map
nameToOpcodeMap = {v: k for k, v in rawOpcodeToNameMap.items()}

deltaOpcodesList = frozenset([
  nameToOpcodeMap["DELTAC1"],
  nameToOpcodeMap["DELTAC2"],
  nameToOpcodeMap["DELTAC3"],
  nameToOpcodeMap["DELTAK1"],
  nameToOpcodeMap["DELTAK2"],
  nameToOpcodeMap["DELTAK3"],
  nameToOpcodeMap["DELTAL1"],
  nameToOpcodeMap["DELTAL2"],
  nameToOpcodeMap["DELTAL3"],
  nameToOpcodeMap["DELTAP1"],
  nameToOpcodeMap["DELTAP2"],
  nameToOpcodeMap["DELTAP3"],
  nameToOpcodeMap["DELTAS1"],
  nameToOpcodeMap["DELTAS2"],
  nameToOpcodeMap["DELTAS3"]])

doNotProceedPC = 0xFFFFFFFF

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
