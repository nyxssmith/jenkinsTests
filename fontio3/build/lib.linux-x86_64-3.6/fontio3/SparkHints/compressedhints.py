#
# compressedhints.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

# System imports
import collections
import operator

# Other imports
from fontio3 import utilities
from fontio3.utilities import pp, writer

# NOTE: I have disabled doctests in this module until I figure out a way
# around the pprint module's use of unsorted iterators...

# -----------------------------------------------------------------------------

#
# Constants
#

DELTA_MAP = {
  'DELTAP': 8,
  'DELTAK': 9,
  'DELTAL': 10,
  'DELTAS': 11,
  'DELTAG': 12,
  'STROKEDELTA': 13}

DELTA_MAP_INV = {b: a for a, b in DELTA_MAP.items()}

GROUP_MASK_MAP = {  # map values == -1000 to True or False
  (False, False, True): ('mask', 2),
  (False, True, False): ('mask', 4),
  (True, False, False): ('mask', 1),
  (False, True, True): ('mask', 6),
  (True, True, False): ('mask', 5),
  (True, False, True): ('mask', 3)}

# HUFFMAN_OPCODES = {
#   0: ("\x00", 3),  # opcode  0, 000
#   1: ("\x40", 3),  # opcode  1, 010
#   2: ("\x20", 3),  # opcode  2, 001
#   3: ("\xE0", 4),  # opcode  3, 1110
#   4: ("\xA0", 3),  # opcode  4, 101
#   5: ("\x80", 3),  # opcode  5, 100
#   6: ("\xF8", 5),  # opcode  6, 11111
# # 7 is not coded  
#   8: ("\x60", 4),  # opcode  8, 0110
#   9: ("\xF4", 7),  # opcode  9, 1111010
#  10: ("\xF2", 7),  # opcode 10, 1111001
#  11: ("\xF6", 7),  # opcode 11, 1111011
#  12: ("\xF0", 7),  # opcode 12, 1111000
#  13: ("\xC0", 3),  # opcode 13, 110
#  14: ("\x70", 5),  # opcode 14, 01110
#  15: ("\x78", 5)}  # opcode 15, 01111
# 
# HUFFMAN_OPERANDS = {
#   (0, 1): ("\xC0", 2),  # operand (0, 1), 11
#   (0, 2): ("\x00", 1),  # operand (0, 2), 0
#   (0, 3): ("\x80", 2),  # operand (0, 3), 10
#   
#   (1, 1): ("\x90", 4),  # operand (1, 1), 1001
#   (1, 2): ("\xC0", 3),  # operand (1, 2), 110
#   (1, 3): ("\x88", 5),  # operand (1, 3), 10001
#   (1, 4): ("\x80", 5),  # operand (1, 4), 10000
#   (1, 5): ("\xE0", 3),  # operand (1, 5), 111
#   (1, 6): ("\xA0", 3),  # operand (1, 6), 101
#   (1, 7): ("\x00", 1),  # operand (1, 7), 0
#   
#   (2, 0): ("\x80", 2),  # operand (2, 0),  10
#   (2, 1): ("\x40", 2),  # operand (2, 1),  01
#   (2, 2): ("\xD0", 4),  # operand (2, 2),  1101
#   (2, 3): ("\xE0", 3),  # operand (2, 3),  111
#   (2, 4): ("\xC8", 5),  # operand (2, 4),  11001
#   (2, 5): ("\x00", 3),  # operand (2, 5),  000
#   (2, 6): ("\x28", 5),  # operand (2, 6),  00101
#   (2, 7): ("\x3C", 6),  # operand (2, 7),  001111
#   (2, 8): ("\x34", 6),  # operand (2, 8),  001101
#   (2, 9): ("\xC0", 5),  # operand (2, 9),  11000
#  (2, 10): ("\x20", 6),  # operand (2, 10), 001000
#  (2, 11): ("\x24", 6),  # operand (2, 11), 001001
#  (2, 12): ("\x32", 7),  # operand (2, 12), 0011001
#  (2, 13): ("\x38", 7),  # operand (2, 13), 0011100
#  (2, 14): ("\x30", 7),  # operand (2, 14), 0011000
#  (2, 15): ("\x3A", 7),  # operand (2, 15), 0011101
#   
#   (3, 0): ("\x60", 3),      # operand (3, 0),  011
#   (3, 1): ("\x00", 2),      # operand (3, 1),  00
#   (3, 2): ("\x40", 3),      # operand (3, 2),  010
#   (3, 3): ("\xC0", 2),      # operand (3, 3),  11
#   (3, 4): ("\x90", 5),      # operand (3, 4),  10010
#   (3, 5): ("\xA0", 3),      # operand (3, 5),  101
#   (3, 6): ("\x8C", 7),      # operand (3, 6),  1000110
#   (3, 7): ("\x88", 6),      # operand (3, 7),  100010
#   (3, 8): ("\x8E", 7),      # operand (3, 8),  1000111
#   (3, 9): ("\x98", 5),      # operand (3, 9),  10011
#  (3, 10): ("\x84", 8),      # operand (3, 10), 10000100
#  (3, 11): ("\x80", 6),      # operand (3, 11), 100000
#  (3, 12): ("\x85\x00", 9),  # operand (3, 12), 100001010
#  (3, 13): ("\x85\xC0", 10), # operand (3, 13), 1000010111
#  (3, 14): ("\x85\x80", 10), # operand (3, 14), 1000010110
#  (3, 15): ("\x86", 7),      # operand (3, 15), 1000011
# 
#   (4, 0): ("\xE0", 4),  # operand (4, 0),  1110
#   (4, 1): ("\xF0", 4),  # operand (4, 1),  1111
#   (4, 2): ("\xA0", 4),  # operand (4, 2),  1010
#   (4, 3): ("\xB0", 4),  # operand (4, 3),  1011
#   (4, 4): ("\x20", 4),  # operand (4, 4),  0010
#   (4, 5): ("\x80", 4),  # operand (4, 5),  1000
#   (4, 6): ("\x10", 4),  # operand (4, 6),  0001
#   (4, 7): ("\x30", 4),  # operand (4, 7),  0011
#   (4, 8): ("\xD8", 5),  # operand (4, 8),  11011
#   (4, 9): ("\x00", 4),  # operand (4, 9),  0000
#  (4, 10): ("\xD0", 5),  # operand (4, 10), 11010
#  (4, 11): ("\xC8", 5),  # operand (4, 11), 11001
#  (4, 12): ("\xC0", 5),  # operand (4, 12), 11000
#  (4, 13): ("\x98", 5),  # operand (4, 13), 10011
#  (4, 14): ("\x90", 5),  # operand (4, 14), 10010
#  (4, 15): ("\x40", 2),  # operand (4, 15), 01
# 
#   (5, 0): ("\xC0", 4),  # operand (5, 0),  1100
#   (5, 1): ("\xB4", 6),  # operand (5, 1),  101101
#   (5, 2): ("\x38", 5),  # operand (5, 2),  00111
#   (5, 3): ("\x20", 4),  # operand (5, 3),  0010
#   (5, 4): ("\xE0", 4),  # operand (5, 4),  1110
#   (5, 5): ("\x60", 3),  # operand (5, 5),  011
#   (5, 6): ("\x00", 3),  # operand (5, 6),  000
#   (5, 7): ("\xF0", 5),  # operand (5, 7),  11110
#   (5, 8): ("\xF8", 5),  # operand (5, 8),  11111
#   (5, 9): ("\x80", 3),  # operand (5, 9),  100
#  (5, 10): ("\x40", 3),  # operand (5, 10), 010
#  (5, 11): ("\xD0", 4),  # operand (5, 11), 1101
#  (5, 12): ("\xD8", 5),  # operand (5, 12), 10111
#  (5, 13): ("\x30", 5),  # operand (5, 13), 00110
#  (5, 14): ("\xB0", 6),  # operand (5, 14), 101100
#  (5, 15): ("\xA0", 4),  # operand (5, 15), 1010
# 
#   (6, 0): ("\x80", 3),      # operand (6, 0),  100
#   (6, 1): ("\x00", 1),      # operand (6, 1),  0
#   (6, 2): ("\xB2", 7),      # operand (6, 2),  1011001
#   (6, 3): ("\xB4", 6),      # operand (6, 3),  101101
#   (6, 4): ("\xB0\x00", 10), # operand (6, 4),  1011000000
#   (6, 5): ("\xB0\x40", 10), # operand (6, 5),  1011000001
#   (6, 6): ("\xB0\x80", 10), # operand (6, 6),  1011000010
#   (6, 7): ("\xB0\xC0", 10), # operand (6, 7),  1011000011
#   (6, 8): ("\xC0", 2),      # operand (6, 8),  11
#   (6, 9): ("\xB8", 6),      # operand (6, 9),  101110
#  (6, 10): ("\xA0", 4),      # operand (6, 10), 1010
#  (6, 11): ("\xBC", 5),      # operand (6, 11), 101111
#  (6, 12): ("\xB1", 8)}      # operand (6, 12), 10110001

HUFFMAN_FUSED = {
  (0, 1): ("\xB0", 6),       # 101100
  (0, 2): ("\xF8", 5),       # 11111
  (0, 3): ("\x6C", 6),       # 011011
  (1, 1): ("\xF4", 7),       # 1111010
  (1, 2): ("\x64", 6),       # 011001
  (1, 3): ("\xB8\x80", 9),   # 101110001
  (1, 4): ("\xF1\x20", 11),  # 11110001001
  (1, 5): ("\xBC", 6),       # 101111
  (1, 6): ("\x84", 6),       # 100001
  (1, 7): ("\x40", 5),       # 01000
  (2, 0): ("\xA0", 5),       # 10100
  (2, 1): ("\x38", 5),       # 00111
  (2, 2): ("\xB6", 7),       # 1011011
  (2, 3): ("\x00", 5),       # 00000
  (2, 4): ("\xB9", 8),       # 10111001
  (2, 5): ("\x08", 6),       # 000010
  (2, 6): ("\xE7\x80", 9),   # 111001111
  (2, 7): ("\xB8\x00", 9),   # 101110000
  (2, 8): ("\x17\x00", 9),   # 000101110
  (2, 9): ("\x96", 8),       # 10010110
 (2, 10): ("\xE6\x80", 10),  # 1110011010
 (2, 11): ("\xE6\xC0", 10),  # 1110011011
 (2, 12): ("\x16\x80", 10),  # 0001011010
 (2, 13): ("\x5C\x00", 10),  # 0101110000
 (2, 14): ("\x16\x00", 10),  # 0001011000
 (2, 15): ("\x5C\x40", 10),  # 0101110001
  (3, 0): ("\x92", 7),       # 1001001
  (3, 1): ("\x4C", 6),       # 010011
  (3, 2): ("\xEB", 8),       # 11101011
  (3, 3): ("\x18", 5),       # 00011
  (3, 4): ("\xE7\x00", 9),   # 111001110
  (3, 5): ("\x24", 6),       # 001001
  (3, 6): ("\xF1\x00", 11),  # 11110001000
  (3, 7): ("\x83\x80", 10),  # 1000001110
  (3, 8): ("\x83\xC0", 11),  # 10000011110
  (3, 9): ("\x82", 8),       # 10000010
 (3, 10): ("\x83\xE0", 12),  # 100000111110
 (3, 11): ("\x83\x00", 10),  # 1000001100
 (3, 12): ("\x83\xF8", 14),  # 10000011111110
 (3, 13): ("\x83\xFE", 15),  # 100000111111111
 (3, 14): ("\x83\xFC", 15),  # 100000111111110
 (3, 15): ("\x16\x40", 10),  # 0001011001
  (4, 0): ("\xEE", 7),       # 1110111
  (4, 1): ("\x2C", 6),       # 001011
  (4, 2): ("\xBA", 7),       # 1011101
  (4, 3): ("\xEC", 7),       # 1110110
  (4, 4): ("\x5E", 7),       # 0101111
  (4, 5): ("\x94", 7),       # 1001010
  (4, 6): ("\x4A", 7),       # 0100101
  (4, 7): ("\x80", 7),       # 1000000
  (4, 8): ("\x0C", 7),       # 0000110
  (4, 9): ("\x48", 7),       # 0100100
 (4, 10): ("\xF6", 8),       # 11110110
 (4, 11): ("\xF7", 8),       # 11110111
 (4, 12): ("\xF0", 8),       # 11110000
 (4, 13): ("\xEA", 8),       # 11101010
 (4, 14): ("\xE4", 8),       # 11100100
 (4, 15): ("\x88", 5),       # 10001
  (5, 0): ("\x52", 7),       # 0101001
  (5, 1): ("\x5C\x80", 9),   # 010111001
  (5, 2): ("\x5D", 8),       # 01011101
  (5, 3): ("\x14", 7),       # 0001010
  (5, 4): ("\xF2", 7),       # 1111001
  (5, 5): ("\x58", 6),       # 010110
  (5, 6): ("\x20", 6),       # 001000
  (5, 7): ("\x0E", 7),       # 0000111
  (5, 8): ("\x50", 7),       # 0101000
  (5, 9): ("\x60", 6),       # 011000
 (5, 10): ("\x68", 6),       # 011010
 (5, 11): ("\xE8", 7),       # 1110100
 (5, 12): ("\xE5", 8),       # 11100101
 (5, 13): ("\xF1\x80", 9),   # 111100011
 (5, 14): ("\xE6\x00", 9),   # 111001100
 (5, 15): ("\xB4", 7),       # 1011010
  (6, 0): ("\x10", 7),       # 0001000
  (6, 1): ("\x30", 5),       # 00110
  (6, 2): ("\x16\xC0", 10),  # 0001011011
  (6, 3): ("\x83\x40", 10),  # 1000001101
  (6, 8): ("\xE0", 6),       # 111000
  (6, 9): ("\x17\x80", 9),   # 000101111
 (6, 10): ("\x97", 8),       # 10010111
 (6, 11): ("\xF1\x40", 10),  # 1111000101
 (6, 12): ("\x83\xF0", 13),  # 1000001111110
       8: ("\x70", 4),       # 0111
       9: ("\x28", 6),       # 001010
      10: ("\x90", 7),       # 1001000
      11: ("\x54", 6),       # 010101
      12: ("\x12", 7),       # 0001001
      13: ("\xC0", 3),       # 110
      14: ("\x98", 5),       # 10011
      15: ("\xA8", 5)}       # 10101

MASK_NAMES = {
  0: "nothing",
  1: "ppem",
  2: "point index",
  3: "ppem and point index",
  4: "shift",
  5: "ppem and shift",
  6: "point index and shift",
  7: "ppem, point index, and shift"}

MISC_NAMES = {
  0: "Set to x-axis",
  1: "Set to y-axis",
  2: "Increment SDS by 1",
  3: "Decrement SDS by 1",
  4: "Increment SDB by 48",
  5: "Decrement SDB by 48",
  6: "Increment ppem by 32",
  7: "Increment ppem by 64",
  8: "Increment point by 32",
  9: "Increment point by 64",
 10: "Increment repeat by 16",
 11: "Increment repeat by 32",
 12: "Increment repeat by 64"}

# -----------------------------------------------------------------------------

#
# Functions
#

def deltaShiftCanRepresent(deltaShift, n):
    """
    Return True or False, depending on whether n is expressible in grains.
    
    ### deltaShiftCanRepresent(3, -0.375)
    True
    ### deltaShiftCanRepresent(3, -1.375)
    False
    ### deltaShiftCanRepresent(1, -0.375)
    False
    """
    
    steps = n * (2.0 ** deltaShift)
    
    if steps != int(steps):
        return False
    
    return abs(steps) <= 8

def opStr(seq, *args):
    """
    Returns a string describing the compressed instruction contained in
    one or two entries of args.
    
    ### print((opStr(12, 0, 1)))
    012  0 1   Reset ppem
    """
    
    fmtOperand = "%03d  %X %X   %s"
    fmtNoOperand = "%03d  %X     %s"
    op = args[0]
    
    if op == 0:
        arg = args[1]
        t = (seq, 0, arg, "Reset %s" % (MASK_NAMES[arg],))
        s = fmtOperand % t
    
    elif op == 1:
        arg = args[1]
        t = (seq, 1, arg, "Set auto-increment for %s" % (MASK_NAMES[arg],))
        s = fmtOperand % t
    
    elif op == 2:
        arg = args[1]
        t = (seq, 2, arg, "Set repeat to %d" % (arg + 1,))
        s = fmtOperand % t
    
    elif op == 3:
        arg = args[1]
        t = (seq, 3, arg, "Increment ppem by %d" % (arg + 1,))
        s = fmtOperand % t
    
    elif op == 4:
        arg = args[1]
        t = (seq, 4, arg, "Increment point by %d" % (arg + 1,))
        s = fmtOperand % t
    
    elif op == 5:
        arg = args[1]
        t = (seq, 5, arg, "Set shift to %d" % (arg,))
        s = fmtOperand % t
    
    elif op == 6:
        arg = args[1]
        t = (seq, 6, arg, MISC_NAMES[arg])
        s = fmtOperand % t
    
    # 7 is currently unused
    
    elif 8 <= op <= 13:
        s = fmtNoOperand % (seq, op, DELTA_MAP_INV[op])
    
    elif op == 14:
        s = fmtNoOperand % (seq, 14, "RTGAH")
    
    else:
        s = fmtNoOperand % (seq, 15, "End of hints")
    
    return s
    
def processOrientation_order(d, deltaShift, **kwArgs):
    """
    ### bs = utilities.fromhex(
    ...   '7F F9 00 41 A2 00 0E 01 '
    ...   '5A 00 A2 00 0E 01 59 7F '
    ...   '0B 01 5D 01 00 07 5B 5D '
    ...   '01 00 20 5A 5D 01 00 21 '
    ...   '5A 00 5D 01 00 20 58 5D '
    ...   '01 00 21 58 01 AA 00 13 '
    ...   '01 59 5D 01 00 08 5A 5D '
    ...   '01 00 0A 5A 5D 01 00 09 '
    ...   '59')
    ### h = hints.Hints.frombytes(bs)
    ### dPre, dPost = h.analyze()
    ### pprint.pprint(dPre)
    {False: {14: {0.375: {('STROKEDELTA', 14)}}},
     True: {14: {0.25: {('STROKEDELTA', 14)}}}}
    
    ### pprint.pprint(dPost)
    {False: {14: {0.25: {('DELTAP', 9), ('DELTAL', 19)},
                  0.375: {('DELTAP', 8),
                          ('DELTAP', 10),
                          ('DELTAP', 32),
                          ('DELTAP', 33)},
                  0.5: {('DELTAP', 7)}}},
     True: {14: {0.125: {('DELTAP', 33), ('DELTAP', 32)}}}}
    
    ### v = processOrientation_order(dPost[False], 3)
    ### for t in v:
    ...     print(t)
    ('mask', 2)
    (14, 0.25, 9, 'DELTAP')
    (14, 0.25, 19, 'DELTAL')
    ('mask', 2)
    (14, 0.375, 8, 'DELTAP')
    (14, 0.375, 10, 'DELTAP')
    (14, 0.375, 32, 'DELTAP')
    (14, 0.375, 33, 'DELTAP')
    ('mask', 7)
    (14, 0.5, 7, 'DELTAP')
    
    ### d = {13: {-0.125: {('DELTAP', 4)}, -1.25: {('DELTAP', 4)}}}
    ### v = processOrientation_order(d, 3)
    ### for t in v:
    ...     print(t)
    ('mask', 4)
    ('sds', 2)
    (13, -1.25, 4, 'DELTAP')
    ('sds', 3)
    (13, -0.125, 4, 'DELTAP')
    
    ### d = {13: {0.5: {('DELTAP', 4)}}, 70: {0.25: {('DELTAP', 12)}}}
    ### v = processOrientation_order(d, 3)
    ### for t in v:
    ...     print(t)
    ('mask', 7)
    (13, 0.5, 4, 'DELTAP')
    ('sdb', 57)
    (70, 0.25, 12, 'DELTAP')
    ('sdb', 9)
    """
    
    v = []
    
    for ppem, dPPEM in d.items():
        for shift, sShift in dPPEM.items():
            for t in sShift:
                v.append((ppem, shift, t[1], t[0]))
    
    rest = set(v)
    dDoubles = collections.defaultdict(set)
    dSingles = collections.defaultdict(set)
    
    for t in v:
        ppem, shift, point, hint = t
        dDoubles[(ppem, shift, -1000)].add(t)
        dDoubles[(ppem, -1000, point)].add(t)
        dDoubles[(-1000, shift, point)].add(t)
        dSingles[(ppem, -1000, -1000)].add(t)
        dSingles[(-1000, -1000, point)].add(t)
        dSingles[(-1000, shift, -1000)].add(t)
    
    groups = []
    
    while True:
        best = None

        for key, s in dDoubles.items():
            if len(s) < 2:
                continue
    
            if (best is None) or (len(s) > len(dDoubles[best])):
                best = key
        
        if best is None:
            break
        
        sCopy = set(dDoubles[best])
        groups.append((best, sCopy))
        rest -= sCopy
        
        for t in sCopy:
            for s in dDoubles.values():
                s.discard(t)
            
            for s in dSingles.values():
                s.discard(t)
    
    while True:
        best = None

        for key, s in dSingles.items():
            if len(s) < 2:
                continue
    
            if (best is None) or (len(s) > len(dSingles[best])):
                best = key
        
        if best is None:
            break
        
        sCopy = set(dSingles[best])
        groups.append((best, sCopy))
        rest -= sCopy
        
        for t in sCopy:
            for s in dSingles.values():
                s.discard(t)
    
    rWorking = []
    
    for key, s in sorted(groups, key=operator.itemgetter(0)):
        mk = tuple(x == -1000 for x in key)
        rWorking.append(GROUP_MASK_MAP[mk])
        
        for t in sorted(s):
            rWorking.append(t)
    
    if rest:
        rWorking.append(('mask', 7))
        rWorking.extend(sorted(rest))
    
    # As a final step, we walk through and make sure all the shift and ppem
    # values can be represented, adding 'sdb' and/or 'sds' records when a
    # change is needed.
    
    r = []
    sdb = 9
    
    for t in rWorking:
        if t[0] != 'mask':
            if not deltaShiftCanRepresent(deltaShift, t[1]):
                steps = t[1] * (2 ** deltaShift)
                
                while steps != int(steps):
                    deltaShift += 1
                    
                    if deltaShift > 6:
                        raise ValueError("Delta shift out of range!")
                    
                    steps *= 2
                
                # we now know steps is integer
                
                while abs(steps) > 8:
                    deltaShift -= 1
                    
                    if deltaShift < 0:
                        raise ValueError("Delta shift out of range!")
                    
                    steps /= 2.0
                    assert steps == int(steps)
                
                r.append(('sds', deltaShift))
            
            if t[0] < sdb:
                r.append(('sdb', 9))
                sdb = 9
            
            while t[0] >= (sdb + 48):
                r.append(('sdb', sdb + 48))
                sdb += 48
        
        r.append(t)
    
    if sdb != 9:
        r.append(('sdb', 9))
    
    return r

def setupBaseState_point(dPre, dPost, **kwArgs):
    """
    ### bs = utilities.fromhex(
    ...   '7F F9 00 41 A2 00 0E 01 '
    ...   '5A 00 A2 00 0E 01 59 7F '
    ...   '0B 01 5D 01 00 07 5B 5D '
    ...   '01 00 20 5A 5D 01 00 21 '
    ...   '5A 00 5D 01 00 20 58 5D '
    ...   '01 00 21 58 01 AA 00 13 '
    ...   '01 59 5D 01 00 08 5A 5D '
    ...   '01 00 0A 5A 5D 01 00 09 '
    ...   '59')
    ### h = hints.Hints.frombytes(bs)
    ### dPre, dPost = h.analyze()
    ### pprint.pprint(dPre)
    {False: {14: {0.375: {('STROKEDELTA', 14)}}},
     True: {14: {0.25: {('STROKEDELTA', 14)}}}}
    
    ### pprint.pprint(dPost)
    {False: {14: {0.25: {('DELTAP', 9), ('DELTAL', 19)},
                  0.375: {('DELTAP', 8),
                          ('DELTAP', 10),
                          ('DELTAP', 32),
                          ('DELTAP', 33)},
                  0.5: {('DELTAP', 7)}}},
     True: {14: {0.125: {('DELTAP', 33), ('DELTAP', 32)}}}}
    
    ### setupBaseState_point(dPre, dPost)
    7
    """
    
    allPoints = set()
    
    for d in (dPre, dPost):
        if not d:
            continue
        
        for dXY in d.values():
            for dPPEM in dXY.values():
                for s in dPPEM.values():
                    allPoints.update(t[1] for t in s if t[1] is not None)
    
    return (min(allPoints) if allPoints else 0)

def setupBaseState_ppem(dPre, dPost, **kwArgs):
    """
    ### bs = utilities.fromhex(
    ...   '7F F9 00 41 A2 00 0E 01 '
    ...   '5A 00 A2 00 0E 01 59 7F '
    ...   '0B 01 5D 01 00 07 5B 5D '
    ...   '01 00 20 5A 5D 01 00 21 '
    ...   '5A 00 5D 01 00 20 58 5D '
    ...   '01 00 21 58 01 AA 00 13 '
    ...   '01 59 5D 01 00 08 5A 5D '
    ...   '01 00 0A 5A 5D 01 00 09 '
    ...   '59')
    ### h = hints.Hints.frombytes(bs)
    ### dPre, dPost = h.analyze()
    ### pprint.pprint(dPre)
    {False: {14: {0.375: {('STROKEDELTA', 14)}}},
     True: {14: {0.25: {('STROKEDELTA', 14)}}}}
    
    ### pprint.pprint(dPost)
    {False: {14: {0.25: {('DELTAP', 9), ('DELTAL', 19)},
                  0.375: {('DELTAP', 8),
                          ('DELTAP', 10),
                          ('DELTAP', 32),
                          ('DELTAP', 33)},
                  0.5: {('DELTAP', 7)}}},
     True: {14: {0.125: {('DELTAP', 33), ('DELTAP', 32)}}}}
    
    ### setupBaseState_ppem(dPre, dPost)
    14
    """
    
    allPPEMs = set()
    
    for d in (dPre, dPost):
        if not d:
            continue
        
        for dXY in d.values():
            allPPEMs.update(dXY)
    
    return (min(allPPEMs) if allPPEMs else 9)

def setupBaseState_shift(dPre, dPost, **kwArgs):
    """
    ### bs = utilities.fromhex(
    ...   '7F F9 00 41 A2 00 0E 01 '
    ...   '5A 00 A2 00 0E 01 59 7F '
    ...   '0B 01 5D 01 00 07 5B 5D '
    ...   '01 00 20 5A 5D 01 00 21 '
    ...   '5A 00 5D 01 00 20 58 5D '
    ...   '01 00 21 58 01 AA 00 13 '
    ...   '01 59 5D 01 00 08 5A 5D '
    ...   '01 00 0A 5A 5D 01 00 09 '
    ...   '59')
    ### h = hints.Hints.frombytes(bs)
    ### dPre, dPost = h.analyze()
    ### pprint.pprint(dPre)
    {False: {14: {0.375: {('STROKEDELTA', 14)}}},
     True: {14: {0.25: {('STROKEDELTA', 14)}}}}
    
    ### pprint.pprint(dPost)
    {False: {14: {0.25: {('DELTAP', 9), ('DELTAL', 19)},
                  0.375: {('DELTAP', 8),
                          ('DELTAP', 10),
                          ('DELTAP', 32),
                          ('DELTAP', 33)},
                  0.5: {('DELTAP', 7)}}},
     True: {14: {0.125: {('DELTAP', 33), ('DELTAP', 32)}}}}
    
    ### setupBaseState_shift(dPre, dPost)
    (3, 0.125)
    """
    
    allShifts = set()
    
    for d in (dPre, dPost):
        if not d:  # also handles special case of dPre == None
            continue
        
        for dXY in d.values():
            for dPPEM in dXY.values():
                allShifts.update(dPPEM)
    
    # Find the finest fraction of a pixel needed.
    
    sds = 0
    n = min(allShifts)
    
    while sds < 7:
        if n == int(n):
            break
        
        sds += 1
        n *= 2
    
    if sds == 7:
        raise ValueError("Too fine a grain!")
    
    return sds, n / (2.0 ** sds)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CompressedHints(object):
    """
    Objects representing a compressed stream of hints. These do not start out
    Huffman-encoded; there is a method to support this.
    
    Mask values are 1=PPEM, 2=Point, 4=Shift
    
    0 m         Reset to bases 
    1 m         Set auto-increment on/off
    2 n         Set repeat to n + 1
    3 n         Increment PPEM by n + 1 (does not affect repeat)
    4 n         Increment Point by n + 1 (does not affect repeat)
    5 n         Set shift to n (does not affect repeat)
    6 n         Miscellaneous
                  0 = Set x
                  1 = Set y
                  2 = Increment SDS by 1
                  3 = Decrement SDS by 1
                  4 = Increment SDB by 48
                  5 = Decrement SDB by 48
                  6 = Increment ppem by 32
                  7 = Increment ppem by 64
                  8 = Increment point by 32
                  9 = Increment point by 64
    7           (currently unused)
    8           DELTAP (do auto-incrementing)
    9           DELTAK (do auto-incrementing)
    A           DELTAL (do auto-incrementing)
    B           DELTAS (do auto-incrementing)
    C           DELTAG (do auto-incrementing)
    D           STROKEDELTA (do auto-incrementing)
    E           RTGAH (this one does NOT do auto-incrementing)
    F           End of hints
    
    Before the actual nybble-stream starts, there is a prolog (note that 'n'
    here refers to a nybble, a 4-bit value):
    
    n           The SDS used to express the base shift (which follows)
    n           The base shift, in SDS units
    n           The base PPEM, as a delta from 9. If the base delta is 24 or
                higher, the F value here indicates one byte follows with the
                actual base PPEM.
    n n         The base point
    
    Here's an example. Suppose we have the following hints:
    
    STROKEDELTA: Point 14 -1@18
    STROKEDELTA: Point 5 -1@18
    STROKEDELTA: Point 4 -3/8@14
    RTGAH
    DELTAK: Point 27 -1@14, -1@18
    DELTAP: Point 26 5/8@14
    DELTAP: Point 21 1/4@14
    
    Here's a deconstruction of the compressed stream:
    
    3       SDS is 3 (2 ** -3, 1/8-pixel granularity)
    0       Base delta, in SDS units, is -1 pixel (-8/8)
    5       Base PPEM is 14
    0 4     Base point is 4
    
            (ppem = 14, shift = 0 (-8/8), point = 4, auto = 0b111, repeat = 1, X)
    5 5     Set shift to 5
            (ppem = 14, shift = 5 (-3/8), point = 4, auto = 0b111, repeat = 1, X)
    D       STROKEDELTA
            (ppem = 15, shift = 6 (-2/8), point = 5, auto = 0b111, repeat = 1, X)
    3 2     Increment ppem by 3
            (ppem = 18, shift = 6 (-2/8), point = 5, auto = 0b111, repeat = 1, X)
    0 4     Reset shift to base
            (ppem = 18, shift = 0 (-8/8), point = 5, auto = 0b111, repeat = 1, X)
    1 2     Set auto-increment to point only
            (ppem = 18, shift = 0 (-8/8), point = 5, auto = 0b010, repeat = 1, X)
    2 8     Set repeat to 9
            (ppem = 18, shift = 0 (-8/8), point = 5, auto = 0b010, repeat = 9, X)
    D       STROKEDELTA
            (ppem = 18, shift = 0 (-8/8), point = 14, auto = 0b010, repeat = 9, X)
    D       STROKEDELTA
            (ppem = 18, shift = 0 (-8/8), point = 23, auto = 0b010, repeat = 9, X)
    E       RTGAH
            (ppem = 18, shift = 0 (-8/8), point = 23, auto = 0b010, repeat = 9, X)
    0 7     Reset all to bases
            (ppem = 14, shift = 0 (-8/8), point = 4, auto = 0b010, repeat = 9, X)
    5 9     Set shift to 9
            (ppem = 14, shift = 9 (+2/8), point = 4, auto = 0b010, repeat = 9, X)
    7 0     Increment point by 16
            (ppem = 14, shift = 9 (+2/8), point = 20, auto = 0b010, repeat = 9, X)
    4 0     Increment point by 1
            (ppem = 14, shift = 9 (+2/8), point = 21, auto = 0b010, repeat = 9, X)
    2 4     Set repeat to 5
            (ppem = 14, shift = 9 (+2/8), point = 21, auto = 0b010, repeat = 5, X)
    8       DELTAP
            (ppem = 14, shift = 9 (+2/8), point = 26, auto = 0b010, repeat = 5, X)
    5 C     Set shift to 12
            (ppem = 14, shift = 12 (+5/8), point = 26, auto = 0b010, repeat = 5, X)
    2 0     Set repeat to 1
            (ppem = 14, shift = 12 (+5/8), point = 26, auto = 0b010, repeat = 1, X)
    8       DELTAP
            (ppem = 14, shift = 12 (+5/8), point = 27, auto = 0b010, repeat = 1, X)
    1 1     Set auto-increment to ppem only
            (ppem = 14, shift = 12 (+5/8), point = 27, auto = 0b001, repeat = 1, X)
    5 0     Set shift to 0
            (ppem = 14, shift = 0 (-8/8), point = 27, auto = 0b001, repeat = 1, X)
    2 3     Set repeat to 4
            (ppem = 14, shift = 0 (-8/8), point = 27, auto = 0b001, repeat = 4, X)
    9       DELTAK
            (ppem = 18, shift = 0 (-8/8), point = 27, auto = 0b001, repeat = 4, X)
    9       DELTAK
            (ppem = 22, shift = 0 (-8/8), point = 27, auto = 0b001, repeat = 4, X)
    F       End of hints
    """
    
    #
    # Methods
    #
    
    def __init__(self, dPre, dPost, **kwArgs):
        """
        Given a pair of dicts as produced by Hints.analyze(), initialize this
        compressed hints object.
        
        ### bs = utilities.fromhex(
        ...   '7F F9 00 26 A2 00 0E 01 '
        ...   '90 A2 00 05 01 90 A2 00 '
        ...   '04 01 55 7F 0B A7 01 00 '
        ...   '1B 02 90 50 5D 01 00 1A '
        ...   '5C 5D 01 00 15 59')
        ### h = hints.Hints.frombytes(bs)
        ### h.pprint()
        STROKEDELTA: Point 14 -1@18
        STROKEDELTA: Point 5 -1@18
        STROKEDELTA: Point 4 -3/8@14
        RTGAH
        DELTAK: Point 27 -1@14, -1@18
        DELTAP: Point 26 5/8@14
        DELTAP: Point 21 1/4@14
        isGray: True
        isOldStyle: True
        ### dPre, dPost = h.analyze()
        ### obj = CompressedHints(dPre, dPost, debug=False)        
        ### obj.pprint()
        Granularity is 0
        Base shift is -1.0
        Base PPEM is 14
        Base point is 4
        000  1 2   Set auto-increment for point index
        001  3 3   Increment ppem by 4
        002  4 0   Increment point by 1
        003  2 8   Set repeat to 9
        004  D     STROKEDELTA
        005  D     STROKEDELTA
        006  1 7   Set auto-increment for ppem, point index, and shift
        007  0 3   Reset ppem and point index
        008  5 5   Set shift to 5
        009  D     STROKEDELTA
        010  E     RTGAH
        011  1 1   Set auto-increment for ppem
        012  4 F   Increment point by 16
        013  4 6   Increment point by 7
        014  2 3   Set repeat to 4
        015  9     DELTAK
        016  9     DELTAK
        017  1 6   Set auto-increment for point index and shift
        018  0 3   Reset ppem and point index
        019  5 9   Set shift to 9
        020  4 F   Increment point by 16
        021  4 0   Increment point by 1
        022  2 2   Set repeat to 3
        023  8     DELTAP
        024  4 1   Increment point by 2
        025  8     DELTAP
        026  F     End of hints
        Total bytes = 25
        """
        
        if kwArgs.get('debug', False):
            import pdb; pdb.set_trace()
        
        self.isGray = kwArgs.get('isGray', False)
        self.initializeState()
        self.nybbles = []
        
        if dPre or dPost:
            self.setupBaseState(dPre, dPost, **kwArgs)
    
            if dPre is not None:
                self.processPhase(dPre, **kwArgs)
                self.nybbles.append(14)  # RTGAH
                self.resetState(7)
    
            self.processPhase(dPost, **kwArgs)
            self.nybbles.append(15)  # end of hints
        
        else:
            
            # There is a special case where the glyph only has a RTGAH. In
            # this case, we emit a bogus header and then the E and F nybbles.
            # Note that this will always be larger than the three bytes of the
            # push, 11, AA -- this means clients probably should use the
            # compressed hints for this special case!
            
            self.nybbles.extend([3, 0, 0, 0, 0, 14, 15])
    
#     def asHuffman(self):
#         """
#         Returns a string with the binary hints. These will include an initial
#         AA 246 or 247 (for B&W and GS, respectively), followed by a two-byte
#         length, and then the contents of the nybbles array.
#         
#         ### bs = utilities.fromhex(
#         ...   '7F F9 00 26 A2 00 0E 01 '
#         ...   '90 A2 00 05 01 90 A2 00 '
#         ...   '04 01 55 7F 0B A7 01 00 '
#         ...   '1B 02 90 50 5D 01 00 1A '
#         ...   '5C 5D 01 00 15 59')
#         ### h = hints.Hints.frombytes(bs)
#         ### c = CompressedHints.fromhints(h)
#         ### utilities.hexdump(c.asHuffman())
#                0 | 7FF7 001A 0750 45BB  BC4D D905 1E72 9AD1 |.....PE..M...r..|
#               10 | 3FD7 A545 256F 1D6B  ECF0                |?..E%o.k..      |
#         """
#         
#         w = writer.LinkedWriter()
#         stake = w.stakeCurrent()
#         endStake = w.getNewStake()
#         w.add("BB", 0x7F, (247 if self.isGray else 246))
#         w.addUnresolvedOffset("H", stake, endStake)
#         ny = self.nybbles
#         
#         if len(ny) > 2:
#             i = (7 if ny[2]==15 else 5)
#             w.addBitsGroup(ny[:i], 4, False)
#         
#             while i < len(ny):
#                 op = ny[i]
#                 w.addBits(*HUFFMAN_OPCODES[op])
#             
#                 if op < 7:
#                     w.addBits(*HUFFMAN_OPERANDS[(op, ny[i+1])])
#                     i += 1
#             
#                 i += 1
#         
#             w.alignToByteMultiple()
#         
#         w.stakeCurrentWithValue(endStake)
#         return w.binaryString()
    
    def asHuffman_fused(self, **kwArgs):
        """
        Returns a string with the binary hints. These will include an initial
        AA 244 or 245 (for B&W and GS, respectively), followed by a two-byte
        length, and then the contents of the nybbles array.
        
        ### bs = utilities.fromhex(
        ...   '7F F9 00 26 A2 00 0E 01 '
        ...   '90 A2 00 05 01 90 A2 00 '
        ...   '04 01 55 7F 0B A7 01 00 '
        ...   '1B 02 90 50 5D 01 00 1A '
        ...   '5C 5D 01 00 15 59')
        ### h = hints.Hints.frombytes(bs)
        ### c = CompressedHints.fromhints(h)
        ### utilities.hexdump(c.asHuffman_fused())
               0 | 7FF7 001A 0750 4647  845D B21B 5B63 0E12 |.....PFG.]..[c..|
              10 | 80A2 B06D 8C61 C2E5  BE00                |...m.a....      |
        """
        
        doPrint = kwArgs.get('doPrint', False)
        w = writer.LinkedWriter()
        stake = w.stakeCurrent()
        endStake = w.getNewStake()
        w.add("BB", 0x7F, (247 if self.isGray else 246))
        w.addUnresolvedOffset("H", stake, endStake)
        ny = self.nybbles
        
        if len(ny) > 2:
            i = (7 if ny[2]==15 else 5)
            w.addBitsGroup(ny[:i], 4, False)
        
            while i < len(ny):
                op = ny[i]
                key = (op if op > 7 else (op, ny[i + 1]))
                w.addBits(*HUFFMAN_FUSED[key])
            
                i += (1 + (op < 7))
        
            w.alignToByteMultiple()
        
        w.stakeCurrentWithValue(endStake)
        r = w.binaryString()
        
        if doPrint:
            utilities.hexdump(r)
        
        return r
    
    def asNonHuffman(self):
        """
        Returns a string with the binary hints. These will include an initial
        AA 246 or 247 (for B&W and GS, respectively), followed by a two-byte
        length, and then the contents of the nybbles array.
        
        Note that this is really for internal debugging; there is no
        corresponding decompressor for data in this format!
        
        ### bs = utilities.fromhex(
        ...   '7F F9 00 26 A2 00 0E 01 '
        ...   '90 A2 00 05 01 90 A2 00 '
        ...   '04 01 55 7F 0B A7 01 00 '
        ...   '1B 02 90 50 5D 01 00 1A '
        ...   '5C 5D 01 00 15 59')
        ### h = hints.Hints.frombytes(bs)
        ### c = CompressedHints.fromhints(h)
        ### utilities.hexdump(c.asNonHuffman())
               0 | 7FF7 001D 0750 4123  3402 8DD1 7035 5DE1 |.....PA#4...p5].|
              10 | 14F4 6239 9160 3594  F402 2841 8F        |..b9.`5...(A.   |
        """
        
        w = writer.LinkedWriter()
        stake = w.stakeCurrent()
        endStake = w.getNewStake()
        w.add("BB", 0x7F, (247 if self.isGray else 246))
        w.addUnresolvedOffset("H", stake, endStake)
        w.addBitsGroup(self.nybbles, 4, False)
        w.alignToByteMultiple()
        w.stakeCurrentWithValue(endStake)
        return w.binaryString()
    
    def dumpState(self, p):
        st = self.state
        p('inY is %s' % (bool(st['inY']),))
        p('shift is %s' % (st['shift'],))
        p('ppem is %s' % (st['ppem'],))
        p('point is %s' % (st['point'],))
        p('delta base is %s' % (st['deltaBase'],))
        p('delta shift is %s' % (st['deltaShift'],))
        p('repeat is %s' % (st['repeat'],))
        p('auto-increment mask is %s' % (MASK_NAMES[st['autoMask']],))
        p('base shift is %s' % (st['baseShift'],))
        p('base ppem is %s' % (st['basePPEM'],))
        p('base point is %s' % (st['basePoint'],))
    
    @classmethod
    def fromhints(cls, hintObj, **kwArgs):
        """
        Creates and returns a new CompressedHints object from the specified
        Hints object.
        """
        
        kwArgs.pop('isGray', False)
        dPre, dPost = hintObj.analyze()
        return cls(dPre, dPost, isGray=hintObj.isGray)
    
    def grainToShift(self, n):
        """
        Converts a grain value (in SDS-compatible form) into a floating-point
        shift value, using the current state's deltaShift setting.
        """
        
        steps = n - 8 + (n >= 8)
        return steps / (2.0 ** self.state['deltaShift'])
    
    def initializeState(self):
        self.state = {
          'inY': 0,
          'shift': 0,
          'ppem': 9,
          'point': 0,
          'deltaBase': 9,
          'deltaShift': 3,
          'repeat': 1,
          'autoMask': 7,
          'baseShift': None,
          'basePPEM': None,
          'basePoint': None}
    
    def pprint(self, **kwArgs):
        """
        Pretty-print the compressed hint stream.
        """
        
        if 'p' in kwArgs:
            p = kwArgs.pop('p')
        else:
            p = pp.PP(**kwArgs)
        
        ops = self.nybbles
        p("Granularity is %d" % (ops[0],))
        n = (ops[1] - 8 + (ops[1] >= 8)) / (2.0 ** ops[0])
        p("Base shift is %s" % (n,))
        
        if ops[2] == 15:
            p("Base PPEM is %d" % (16 * ops[3] + ops[4],))
            i = 7
        
        else:
            p("Base PPEM is %d" % (9 + ops[2],))
            i = 5
        
        p("Base point is %d" % (16 * ops[i - 2] + ops[i - 1],))
        seq = 0
        
        while True:
            p(opStr(seq, *ops[i:i+2]))
            op = ops[i]
            i += (1 + (op < 7))
            
            if op == 15:
                break
            
            seq += 1
        
        p("Total bytes = %d" % ((len(ops) + 1) // 2,))
    
    def processOrientation(self, d, **kwArgs):
        st = self.state
        ny = self.nybbles
        groupData = processOrientation_order(d, st['deltaShift'])
        
        for tThis, tNext in utilities.pairwise(groupData):
            if tThis[0] == 'mask':
                if st['autoMask'] != tThis[1]:
                    ny.extend([1, tThis[1]])
                    st['autoMask'] = tThis[1]
            
            elif tThis[0] == 'sds':
                newSDS = tThis[1]
                count = abs(newSDS - st['deltaShift'])
                
                if st['deltaShift'] < newSDS:
                    ny.extend([6, 2] * count)
                elif st['deltaShift'] > newSDS:
                    ny.extend([6, 3] * count)
                
                st['deltaShift'] = newSDS
            
            elif tThis[0] == 'sdb':
                newSDB = tThis[1]
                
                if newSDB < st['deltaBase']:
                    # note the following line requires a division __future__
                    # import for fontio3!
                    assert newSDB == 9
                    fSteps = (st['deltaBase'] - newSDB) / 48
                    nSteps = int(fSteps)
                    assert nSteps == fSteps
                    ny.extend([6, 5] * nSteps)
                    st['deltaBase'] = 9
                
                else:
                    assert newSDB > st['deltaBase']
                    fSteps = (newSDB - st['deltaBase']) / 48
                    nSteps = int(fSteps)
                    assert nSteps == fSteps
                    ny.extend([6, 4] * nSteps)
                    st['deltaBase'] = newSDB
            
            elif tNext[0] in {'mask', 'sds', 'sdb'}:
                self.processTuple(tThis, **kwArgs)
            
            else:
                self.processTuple(tThis, tNext, **kwArgs)
        
        tThis = groupData[-1]
        
        if tThis[0] == 'mask':
            if st['autoMask'] != tThis[1]:
                ny.extend([1, tThis[1]])
                st['autoMask'] = tThis[1]
        
        elif tThis[0] == 'sds':
            newSDS = tThis[1]
            count = abs(newSDS - st['deltaShift'])
            
            if st['deltaShift'] < newSDS:
                ny.extend([6, 2] * count)
            elif st['deltaShift'] > newSDS:
                ny.extend([6, 3] * count)
            
            st['deltaShift'] = newSDS
        
        elif tThis[0] == 'sdb':
            newSDB = tThis[1]
            
            if newSDB < st['deltaBase']:
                # note the following line requires a division __future__
                # import for fontio3!
                assert newSDB == 9
                fSteps = (st['deltaBase'] - newSDB) / 48
                nSteps = int(fSteps)
                assert nSteps == fSteps
                ny.extend([6, 5] * nSteps)
                st['deltaBase'] = 9
            
            else:
                assert newSDB > st['deltaBase']
                fSteps = (newSDB - st['deltaBase']) / 48
                nSteps = int(fSteps)
                assert nSteps == fSteps
                ny.extend([6, 4] * nSteps)
                st['deltaBase'] = newSDB
        
        else:
            self.processTuple(tThis, **kwArgs)
    
    def processPhase(self, d, **kwArgs):
        st = self.state
        ny = self.nybbles
        
        if False in d:
            if st['inY']:
                ny.extend([6, 0])
                st['inY'] = False
            
            self.resetState(7)
            self.processOrientation(d[False], **kwArgs)
        
        if True in d:
            if not st['inY']:
                ny.extend([6, 1])
                st['inY'] = True
            
            self.resetState(7)
            self.processOrientation(d[True], **kwArgs)
    
    def processTuple(self, tThis, tNext=None, **kwArgs):
        """
        Given a tuple of the form (ppem, shift, point, hintName) emit the state
        transitions necessary to implement it.
        """
        
        st = self.state
        ny = self.nybbles
        ppem, shift, point, hintName = tThis
        self.processTuple_low_checks(ppem, point, **kwArgs)
        self.processTuple_match_ppem(ppem, **kwArgs)
        self.processTuple_match_shift(shift, **kwArgs)
        self.processTuple_match_point(point, **kwArgs)
        
        if tNext is not None:
            self.processTuple_repeat(tThis, tNext, **kwArgs)
        
        # We're finally ready to emit the actual hint and auto-increment
        
        ny.append(DELTA_MAP[hintName])
        currMask = st['autoMask']
        rep = st['repeat']
        
        if currMask & 1:
            st['ppem'] += rep
        
        if currMask & 2:
            st['point'] += rep
        
        if currMask & 4:
            st['shift'] = self.grainToShift(self.shiftToGrain(st['shift']) + rep)
    
    def processTuple_repeat(self, tThis, tNext, **kwArgs):
        st = self.state
        ny = self.nybbles
        currMask = st['autoMask']
        assert currMask  # should never be zero
        f = self.shiftToGrain
        
        if currMask == 1:
            self.processTuple_repeat_sub(tThis[0], tNext[0], **kwArgs)
        
        elif currMask == 2:
            # Only do this for non-DELTAGs
            if (tThis[2] is not None) and (tNext[2] is not None):
                self.processTuple_repeat_sub(tThis[2], tNext[2], **kwArgs)
        
        elif currMask == 4:
            self.processTuple_repeat_sub(f(tThis[1]), f(tNext[1]), **kwArgs)
        
        elif currMask == 3:
            # Only do this for non-DELTAGs
            if (tThis[2] is not None) and (tNext[2] is not None):
                self.processTuple_repeat_sub2(
                  tThis[0], tNext[0], tThis[2], tNext[2], **kwArgs)
            
            else:
                self.processTuple_repeat_sub(tThis[0], tNext[0], **kwArgs)
        
        elif currMask == 5:
            self.processTuple_repeat_sub2(
              tThis[0], tNext[0], f(tThis[1]), f(tNext[1]), **kwArgs)
        
        elif currMask == 6:
            # Only do this for non-DELTAGs
            if (tThis[2] is not None) and (tNext[2] is not None):
                self.processTuple_repeat_sub2(
                  f(tThis[1]), f(tNext[1]), tThis[2], tNext[2], **kwArgs)
            
            else:
                self.processTuple_repeat_sub(f(tThis[1]), f(tNext[1]), **kwArgs)
        
        else:
            delta1 = tNext[0] - tThis[0]
            delta2 = f(tNext[1]) - f(tThis[1])
            
            if (tNext[2] is not None) and (tThis[2] is not None):
                delta3 = tNext[2] - tThis[2]
            else:
                delta3 = -1
            
            v = [n for n in (delta1, delta2, delta3) if n > 0]
            
            if v:
                delta = min(v)
                st['repeat'] = delta
                modulus = (delta - 1) % 16
                ny.extend([2, modulus])
                delta -= (modulus + 1)
            
                while delta > 0:
                    if delta >= 64:
                        ny.extend([6, 12])
                        delta -= 64
                
                    elif delta >= 32:
                        ny.extend([6, 11])
                        delta -= 32
                
                    else:
                        ny.extend([6, 10])
                        delta -= 16
    
    def processTuple_repeat_sub(self, valThis, valNext, **kwArgs):
        st = self.state
        ny = self.nybbles
        
        if valNext > valThis:
            delta = valNext - valThis
            st['repeat'] = delta
            modulus = (delta - 1) % 16
            ny.extend([2, modulus])
            delta -= (modulus + 1)
            
            while delta > 0:
                if delta >= 64:
                    ny.extend([6, 12])
                    delta -= 64
                
                elif delta >= 32:
                    ny.extend([6, 11])
                    delta -= 32
                
                else:
                    ny.extend([6, 10])
                    delta -= 16
    
    def processTuple_repeat_sub2(self, valThis1, valNext1, valThis2, valNext2, **kwArgs):
        st = self.state
        ny = self.nybbles
        delta1 = valNext1 - valThis1
        delta2 = valNext2 - valThis2
        
        if delta1 < 0:
            if delta2 < 0:
                return
            
            delta = delta2
        
        elif delta2 < 0:
            delta = delta1
        
        else:
            delta = min(delta1, delta2)
        
        st['repeat'] = delta
        modulus = (delta - 1) % 16
        ny.extend([2, modulus])
        delta -= (modulus + 1)
        
        while delta > 0:
            if delta >= 64:
                ny.extend([6, 12])
                delta -= 64
            
            elif delta >= 32:
                ny.extend([6, 11])
                delta -= 32
            
            else:
                ny.extend([6, 10])
                delta -= 16
    
    def processTuple_low_checks(self, ppem, point, **kwArgs):
        """
        If one or more of ppem or point are lower than the current state values
        then reset the current values. Note that shift is not handled this way
        since it gets set directly.
        """
        
        st = self.state
        m = 0
        
        if ppem < st['ppem']:
            m += 1
            st['ppem'] = st['basePPEM']
        
        if point < st['point']:
            m += 2
            st['point'] = st['basePoint']
        
        if m:
            self.nybbles.extend([0, m])
    
    def processTuple_match_point(self, point, **kwArgs):
        st = self.state
        ny = self.nybbles
        
        if (point == st['point']) or (point is None):
            return
        
        assert point >= st['point']  # done in processTuple_low_checks()
        neededDelta = point - st['point']
        
        while neededDelta:
            if neededDelta >= 64:
                ny.extend([6, 9])
                neededDelta -= 64
            
            elif neededDelta >= 32:
                ny.extend([6, 8])
                neededDelta -= 32
            
            elif neededDelta >= 16:
                ny.extend([4, 15])
                neededDelta -= 16
            
            else:
                ny.extend([4, neededDelta - 1])
                neededDelta = 0
        
        st['point'] = point
    
    def processTuple_match_ppem(self, ppem, **kwArgs):
        st = self.state
        ny = self.nybbles
        
        if ppem == st['ppem']:
            return
        
        assert ppem >= st['ppem']  # done in processTuple_low_checks()
        neededDelta = ppem - st['ppem']
        
        while neededDelta:
            if neededDelta >= 64:
#               ny.extend([6, 7])
                ny.extend([3, 15, 3, 15, 3, 15])
                neededDelta -= 64
            
            elif neededDelta >= 32:
#               ny.extend([6, 6])
                ny.extend([3, 15, 3, 15])
                neededDelta -= 32
            
            elif neededDelta >= 16:
                ny.extend([3, 15])
                neededDelta -= 16
            
            else:
                ny.extend([3, neededDelta - 1])
                neededDelta = 0
        
        st['ppem'] = ppem
    
    def processTuple_match_shift(self, shift, **kwArgs):
        st = self.state
        ny = self.nybbles
        
        if shift == st['shift']:
            return
        
        steps = shift * (2 ** st['deltaShift'])
        
        if steps == int(steps):
            while abs(steps) > 8:
                ny.extend([6, 3])
                st['deltaShift'] -= 1
                steps /= 2.0
                
                if (steps != int(steps)) or (st['deltaShift'] < 0):
                    raise ValueError("Cannot represent shift!")
        
        else:
            while steps != int(steps):
                ny.extend([6, 2])
                st['deltaShift'] += 1
                steps *= 2.0
                
                if st['deltaShift'] > 6:
                    raise ValueError("Cannot represent shift!")
        
        n = int(steps + 8 - (steps > 0))
        ny.extend([5, n])
        st['shift'] = shift
    
    def resetState(self, mask):
        """
        Reset the three key values to their bases, depending on mask.
        """
        
        st = self.state
        
        if mask & 1:
            st['ppem'] = st['basePPEM']
        
        if mask & 2:
            st['point'] = st['basePoint']
        
        if mask & 4:
            st['shift'] = st['baseShift']
    
    def run(self, **kwArgs):
        """
        Emulates running the compressed hints, creating a dPre and dPost which
        are returned. Keyword arguments allow print-tracing.
        
        ### bs = utilities.fromhex(
        ...   '7F F9 00 41 A2 00 0E 01 '
        ...   '5A 00 A2 00 0E 01 59 7F '
        ...   '0B 01 5D 01 00 07 5B 5D '
        ...   '01 00 20 5A 5D 01 00 21 '
        ...   '5A 00 5D 01 00 20 58 5D '
        ...   '01 00 21 58 01 AA 00 13 '
        ...   '01 59 5D 01 00 08 5A 5D '
        ...   '01 00 0A 5A 5D 01 00 09 '
        ...   '59')
        ### h = hints.Hints.frombytes(bs)
        ### dPre, dPost = h.analyze()
        ### pprint.pprint(dPre)
        {False: {14: {0.375: {('STROKEDELTA', 14)}}},
         True: {14: {0.25: {('STROKEDELTA', 14)}}}}
        
        ### pprint.pprint(dPost)
        {False: {14: {0.25: {('DELTAP', 9), ('DELTAL', 19)},
                      0.375: {('DELTAP', 8),
                              ('DELTAP', 10),
                              ('DELTAP', 32),
                              ('DELTAP', 33)},
                      0.5: {('DELTAP', 7)}}},
         True: {14: {0.125: {('DELTAP', 33), ('DELTAP', 32)}}}}
        
        ### obj = CompressedHints(dPre, dPost)
        ### dPre2, dPost2 = obj.run(doPrint=False)
        ### dPre == dPre2
        True
        ### dPost == dPost2
        True
        """
        
        self.initializeState()
        st = self.state
        ny = self.nybbles
        d = dPre = {}
        dPost = {}
        doPrint = kwArgs.get('doPrint', False)
        
        # Handle the prolog
        
        shift = (ny[1] - 8 + (ny[1] >= 8)) / (2.0 ** ny[0])
        st['baseShift'] = st['shift'] = shift
        
        if ny[2] == 15:
            ppem = (16 * ny[3] + ny[4])
            i = 7
        
        else:
            ppem = 9 + ny[2]
            i = 5
        
        st['basePPEM'] = st['ppem'] = ppem
        st['basePoint'] = st['point'] = (16 * ny[i - 2]) + ny[i - 1]
        
        if doPrint:
            if 'p' in kwArgs:
                p = kwArgs['p']
            else:
                p = pp.PP(**kwArgs)
            
            p2 = p.makeIndentedPP()
            self.dumpState(p2)
            seq = 0
        
        # Now loop through the opcodes
        
        while i < len(ny):
            if doPrint:
                p(opStr(seq, *ny[i:i+2]))
            
            op = ny[i]
            
            if op == 0:
                self.resetState(ny[i + 1])
            
            elif op == 1:
                st['autoMask'] = ny[i + 1]
            
            elif op == 2:
                st['repeat'] = ny[i + 1] + 1
            
            elif op == 3:
                st['ppem'] += (ny[i + 1] + 1)
            
            elif op == 4:
                st['point'] += (ny[i + 1] + 1)
            
            elif op == 5:
                st['shift'] = self.grainToShift(ny[i + 1])
            
            elif op == 6:
                arg = ny[i + 1]
                
                if arg == 0:
                    st['inY'] = False
                    self.resetState(7)
                
                elif arg == 1:
                    st['inY'] = True
                    self.resetState(7)
                
                elif arg == 2:
                    st['deltaShift'] += 1
                
                elif arg == 3:
                    st['deltaShift'] -= 1
                
                elif arg == 4:  # not used?
                    st['deltaBase'] += 48
                
                elif arg == 5:  # not used?
                    st['deltaBase'] -= 48
                
                elif arg == 6:
                    st['ppem'] += 32
                
                elif arg == 7:
                    st['ppem'] += 64
                
                elif arg == 8:
                    st['point'] += 32
                
                elif arg == 9:
                    st['point'] += 64
                
                elif arg == 10:
                    st['repeat'] += 16
                
                elif arg == 11:
                    st['repeat'] += 32
                
                else:
                    st['repeat'] += 64
            
            elif 8 <= op <= 13:
                dXY = d.setdefault(st['inY'], {})
                dPPEM = dXY.setdefault(st['ppem'], {})
                sShift = dPPEM.setdefault(st['shift'], set())
                t = (DELTA_MAP_INV[op], st['point'])
                sShift.add(t)
                
                if st['autoMask'] & 1:
                    st['ppem'] += st['repeat']
                
                if st['autoMask'] & 2:
                    st['point'] += st['repeat']
                
                if st['autoMask'] & 4:
                    n = self.shiftToGrain(st['shift'])
                    st['shift'] = self.grainToShift(n + 1)
            
            elif op == 14:
                d = dPost
                self.resetState(7)
            
            else:
                break
            
            if doPrint:
                self.dumpState(p2)
                seq += 1
            
            i += (2 if op < 7 else 1)
        
        return dPre, dPost
    
    def setupBaseState(self, dPre, dPost, **kwArgs):
        """
        Analyze the dicts in order to determine the prolog values.
        """
        
        st = self.state
        ny = self.nybbles
        baseGrain, baseShift = setupBaseState_shift(dPre, dPost, **kwArgs)
        
        # If baseShift cannot be represented as 1 to 8 signed SDS units, then
        # we need to handle things specially -- shouldn't happen very often.
        
        st['shift'] = st['baseShift'] = baseShift
        magnitude = int(baseShift * (2 ** baseGrain))
        ny.extend([baseGrain, magnitude + (8 - (magnitude > 0))])
        basePPEM = setupBaseState_ppem(dPre, dPost, **kwArgs)
        st['ppem'] = st['basePPEM'] = basePPEM
        
        if basePPEM < 24:
            if basePPEM < 9:
                raise ValueError("Base PPEM below 9!")
            
            ny.append(basePPEM - 9)
        
        else:
            a, b = divmod(basePPEM, 16)
            ny.extend([15, a, b])
        
        basePoint = setupBaseState_point(dPre, dPost, **kwArgs)
        st['point'] = st['basePoint'] = basePoint
        a, b = divmod(basePoint, 16)
        ny.extend([a, b])
    
    def shiftToGrain(self, n):
        """
        Convert a floating-point shift into a number of grains, based on the
        current settings in self.state['deltaShift']. Note that the value
        returned in in SDS format (i.e. 0 = -8); this way the zero shift is
        skipped automatically. To this end, this method may return values
        outside the 0..15 range! Since it's used to do delta calculations
        within the repeat-setting code, that's OK.
        """
        
        steps = n * (2 ** self.state['deltaShift'])
        return int(steps + 8 - (steps > 0))
    
    def statistics(self, **kwArgs):
        """
        Gather statistics on the opcodes and operands used, for analysis to
        determine optimal Huffman encoding, for instance. Returns two dicts:
        
            dOp     A dict mapping opcodes to counts of usage
            
            dArg    A dict mapping opcodes to subdicts, which in turn map
                    arguments to counts.
        
        These may also be passed in, for multi-glyph accumulation.
        """
        
        dOp = kwArgs.get('dOp', None)
        
        if dOp is None:
            dOp = collections.defaultdict(int)
        
        dArg = kwArgs.get('dArg', None)
        
        if dArg is None:
            f = lambda: collections.defaultdict(int)
            dArg = collections.defaultdict(f)
        
        ny = self.nybbles
        
        if ny:
            i = (7 if ny[2] == 15 else 5)
        
            while i < len(ny):
                op = ny[i]
                dOp[op] += 1
            
                if op < 7:  # it has an operand
                    dArg[op][ny[i + 1]] += 1
                    i += 1
                
                i += 1
        
        return dOp, dArg
    
    def statistics_fused(self, **kwArgs):
        """
        Gather statistics on the opcodes and operands used, for analysis to
        determine optimal Huffman encoding, for instance. Returns a dict
        mapping either single ints or pairs of ints to counts. The pairs are
        used for opcodes with arguments.
        
        The dict 'd' may also be passed in, for multi-glyph accumulation.
        
        ### bs = utilities.fromhex(
        ...   '7F F9 00 41 A2 00 0E 01 '
        ...   '5A 00 A2 00 0E 01 59 7F '
        ...   '0B 01 5D 01 00 07 5B 5D '
        ...   '01 00 20 5A 5D 01 00 21 '
        ...   '5A 00 5D 01 00 20 58 5D '
        ...   '01 00 21 58 01 AA 00 13 '
        ...   '01 59 5D 01 00 08 5A 5D '
        ...   '01 00 0A 5A 5D 01 00 09 '
        ...   '59')
        ### h = hints.Hints.frombytes(bs)
        ### obj = CompressedHints.fromhints(h)
        ### obj.pprint()
        Granularity is 3
        Base shift is 0.125
        Base PPEM is 14
        Base point is 7
        000  5 A   Set shift to 10
        001  4 6   Increment point by 7
        002  D     STROKEDELTA
        003  6 1   Set to y-axis
        004  5 9   Set shift to 9
        005  4 6   Increment point by 7
        006  D     STROKEDELTA
        007  E     RTGAH
        008  6 0   Set to x-axis
        009  1 2   Set auto-increment for point index
        010  5 9   Set shift to 9
        011  4 1   Increment point by 2
        012  2 9   Set repeat to 10
        013  8     DELTAP
        014  A     DELTAL
        015  0 2   Reset point index
        016  5 A   Set shift to 10
        017  4 0   Increment point by 1
        018  2 1   Set repeat to 2
        019  8     DELTAP
        020  2 5   Set repeat to 6
        021  6 A   Increment repeat by 16
        022  8     DELTAP
        023  2 0   Set repeat to 1
        024  8     DELTAP
        025  8     DELTAP
        026  1 7   Set auto-increment for ppem, point index, and shift
        027  0 2   Reset point index
        028  5 B   Set shift to 11
        029  8     DELTAP
        030  6 1   Set to y-axis
        031  1 2   Set auto-increment for point index
        032  4 F   Increment point by 16
        033  4 8   Increment point by 9
        034  2 0   Set repeat to 1
        035  8     DELTAP
        036  8     DELTAP
        037  F     End of hints
        Total bytes = 34
        
        ### d = obj.statistics_fused()
        ### for key in sorted(d, key=str):
        ...     print((key, d[key]))
        8 8
        10 1
        13 2
        14 1
        15 1
        (0, 2) 2
        (1, 2) 2
        (1, 7) 1
        (2, 0) 2
        (2, 1) 1
        (2, 5) 1
        (2, 9) 1
        (4, 0) 1
        (4, 1) 1
        (4, 6) 2
        (4, 8) 1
        (4, 15) 1
        (5, 9) 2
        (5, 10) 2
        (5, 11) 1
        (6, 0) 1
        (6, 1) 2
        (6, 10) 1
        """
        
        d = kwArgs.get('d', None)
        
        if d is None:
            d = collections.defaultdict(int)
        
        ny = self.nybbles
        
        if ny:
            i = (7 if ny[2] == 15 else 5)
        
            while i < len(ny):
                op = ny[i]
            
                if op < 7:
                    d[(op, ny[i + 1])] += 1
                    i += 1
                
                else:
                    d[op] += 1
                
                i += 1
        
        return d

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import pprint
    from fontio3.SparkHints import hints

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

