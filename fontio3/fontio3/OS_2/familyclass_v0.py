#
# familyclass_v0.py
#
# Copyright © 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
String constants for OS/2 sFamilyClass values.
"""

# System imports
import collections

# -----------------------------------------------------------------------------

#
# Private classes
#

class _DS(collections.defaultdict):
    def __missing__(self, key):
        s = self[key] = "Class %d, Subclass %d" % divmod(key, 256)
        return s

# -----------------------------------------------------------------------------

#
# Constants
#

labels = _DS(lambda: None,
    {
    0x0000: "No Classification",
    
    0x0100: "Oldstyle Serifs",
    0x0101: "Oldstyle Serifs/IBM Rounded Legibility",
    0x0102: "Oldstyle Serifs/Garalde",
    0x0103: "Oldstyle Serifs/Venetian",
    0x0104: "Oldstyle Serifs/Modified Venetian",
    0x0105: "Oldstyle Serifs/Dutch Modern",
    0x0106: "Oldstyle Serifs/Dutch Traditional",
    0x0107: "Oldstyle Serifs/Contemporary",
    0x0108: "Oldstyle Serifs/Calligraphic",
    0x010F: "Oldstyle Serifs/Miscellaneous",
    
    0x0200: "Traditional Serifs",
    0x0201: "Traditional Serifs/Direct Line",
    0x0202: "Traditional Serifs/Script",
    0x020F: "Traditional Serifs/Miscellaneous",
    
    0x0300: "Modern Serifs",
    0x0301: "Modern Serifs/Italian",
    0x0302: "Modern Serifs/Script",
    0x030F: "Modern Serifs/Miscellaneous",
    
    0x0400: "Clarendon Serifs",
    0x0401: "Clarendon Serifs/Clarendon",
    0x0402: "Clarendon Serifs/Modern",
    0x0403: "Clarendon Serifs/Traditional",
    0x0404: "Clarendon Serifs/Newspaper",
    0x0405: "Clarendon Serifs/Stub Serif",
    0x0406: "Clarendon Serifs/Monotone",
    0x0407: "Clarendon Serifs/Typewriter",
    0x040F: "Clarendon Serifs/Miscellaneous",
    
    0x0500: "Slab Serifs",
    0x0501: "Slab Serifs/Monotone",
    0x0502: "Slab Serifs/Humanist",
    0x0503: "Slab Serifs/Geometric",
    0x0504: "Slab Serifs/Swiss",
    0x0505: "Slab Serifs/Typewriter",
    0x050F: "Slab Serifs/Miscellaneous",
    
    0x0700: "Freeform Serifs",
    0x0701: "Freeform Serifs/Modern",
    0x070F: "Freeform Serifs/Miscellaneous",
    
    0x0800: "Sans Serif",
    0x0801: "Sans Serif/IBM Neo-grotesque Gothic",
    0x0802: "Sans Serif/Humanist",
    0x0803: "Sans Serif/Low-x Round Geometric",
    0x0804: "Sans Serif/High-x Round Geometric",
    0x0805: "Sans Serif/Neo-grotesque Gothic",
    0x0806: "Sans Serif/Modified Neo-grotesque Gothic",
    0x0809: "Sans Serif/Typewriter Gothic",
    0x080A: "Sans Serif/Matrix",
    0x080F: "Sans Serif/Miscellaneous",
    
    0x0900: "Ornamentals",
    0x0901: "Ornamentals/Engraver",
    0x0902: "Ornamentals/Black Letter",
    0x0903: "Ornamentals/Decorative",
    0x0904: "Ornamentals/Three-dimensional",
    0x090F: "Ornamentals/Miscellaneous",
    
    0x0A00: "Scripts",
    0x0A01: "Scripts/Uncial",
    0x0A02: "Scripts/Brush Joined",
    0x0A03: "Scripts/Formal Joined",
    0x0A04: "Scripts/Monotone Joined",
    0x0A05: "Scripts/Calligraphic",
    0x0A06: "Scripts/Brush Unjoined",
    0x0A07: "Scripts/Formal Unjoined",
    0x0A08: "Scripts/Monotone Unjoined",
    0x0A0F: "Scripts/Miscellaneous",
    
    0x0C00: "Symbolic",
    0x0C03: "Symbolic/Mixed Serif",
    0x0C06: "Symbolic/Oldstyle Serif",
    0x0C07: "Symbolic/Neo-grotesque Sans Serif",
    0x0C0F: "Symbolic/Miscellaneous"})
