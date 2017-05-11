#
# _generateUnicodeRanges_v1.py
#
# Copyright © 2010, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Code that recalculates fontio3.OS_2.unicoderanges._rangeData from the current
Unicode database in the Python unicodedata module. These data are for Version
1 OS/2 tables.

Just run this file and the new _rangeData will be output to stdout.
"""

import unicodedata

from fontio3.utilities import span

rawData = (
    (0, ((0x0000, 0x007F),)),
    (1, ((0x0080, 0x00FF),)),
    (2, ((0x0100, 0x017F),)),
    (3, ((0x0180, 0x024F),)),
    (4, ((0x0250, 0x02AF),)),
    (5, ((0x02B0, 0x02FF),)),
    (6, ((0x0300, 0x036F),)),
    (7, ((0x0370, 0x03D7),)),
    (8, ((0x03DA, 0x03FF),)),  # Greek symbols and Coptic-specific letters; changes to Coptic in V4
    (9, ((0x0400, 0x04FF),)),
   (10, ((0x0530, 0x058F),)),
   # 11 and 12 represent two parts of Hebrew; in later versions, 11 alone is Hebrew,
   # and 12 eventually becomes Vai. The documentation is not clear on what exactly
   # constitutes "extended" Hebrew, so I've (perhaps arbitrarily) decided it comprises
   # cantillation marks, the Yiddish digraphs, and the extra punctuation.
   (11, ((0x05B0, 0x05EF),)),  # basic Hebrew, just letters and points
   (12, ((0x0590, 0x05AF), (0x05F0, 0x05FF))),  # "extended" Hebrew (see note above)
   (13, ((0x0600, 0x0670),)),  # Arabic basic
   (14, ((0x0671, 0x06FF),)),  # Arabic extended; becomes NKo in V4
   (15, ((0x0900, 0x097F),)),
   (16, ((0x0980, 0x09FF),)),
   (17, ((0x0A00, 0x0A7F),)),
   (18, ((0x0A80, 0x0AFF),)),
   (19, ((0x0B00, 0x0B7F),)),
   (20, ((0x0B80, 0x0BFF),)),
   (21, ((0x0C00, 0x0C7F),)),
   (22, ((0x0C80, 0x0CFF),)),
   (23, ((0x0D00, 0x0D7F),)),
   (24, ((0x0E00, 0x0E7F),)),
   (25, ((0x0E80, 0x0EFF),)),
   (26, ((0x10D0, 0x10F0), (0x10FB, 0x10FB))),  # Georgian basic
   (27, ((0x10A0, 0x01CF), (0x10F1, 0x10F6))),  # Georgian "extended" (Khutsuri); changes to Balinese in V4
   (28, ((0x1100, 0x11FF),)),
   (29, ((0x1E00, 0x1EFF),)),
   (30, ((0x1F00, 0x1FFF),)),
   (31, ((0x2000, 0x206F),)),
   (32, ((0x2070, 0x209F),)),
   (33, ((0x20A0, 0x20CF),)),
   (34, ((0x20D0, 0x20FF),)),
   (35, ((0x2100, 0x214F),)),
   (36, ((0x2150, 0x218F),)),
   (37, ((0x2190, 0x21FF),)),
   (38, ((0x2200, 0x22FF),)),
   (39, ((0x2300, 0x23FF),)),
   (40, ((0x2400, 0x243F),)),
   (41, ((0x2440, 0x245F),)),
   (42, ((0x2460, 0x24FF),)),
   (43, ((0x2500, 0x257F),)),
   (44, ((0x2580, 0x259F),)),
   (45, ((0x25A0, 0x25FF),)),
   (46, ((0x2600, 0x26FF),)),
   (47, ((0x2700, 0x27BF),)),
   (48, ((0x3000, 0x303F),)),
   (49, ((0x3040, 0x309F),)),
   (50, ((0x30A0, 0x30FF),)),
   (51, ((0x3100, 0x312F),)),
   (52, ((0x3130, 0x318F),)),
   (53, ((0x3190, 0x319F),)),  # Kanbun here; note in later versions this becomes Phags-Pa
   (54, ((0x3200, 0x32FF),)),
   (55, ((0x3300, 0x33FF),)),
   (56, ((0xAC00, 0xD7AF),)),
   (59, ((0x4E00, 0x9FFF),)),
   (60, ((0xE000, 0xF8FF),)),
   (61, ((0xF900, 0xFAFF),)),
   (62, ((0xFB00, 0xFB4F),)),
   (63, ((0xFB50, 0xFDFF),)),
   (64, ((0xFE20, 0xFE2F),)),
   (65, ((0xFE30, 0xFE4F),)),
   (66, ((0xFE50, 0xFE6F),)),
   (67, ((0xFE70, 0xFEFF),)),
   (68, ((0xFF00, 0xFFEF),)),
   (69, ((0xFFF0, 0xFFFF),)))

def f(n):
    if n <= 0xFFFF:
        return "0x%04X" % (n,)
    else:
        return "0x%06X" % (n,)

class UInfo(object):
    def __init__(self):
        n = unicodedata.name
        s = set()
        
        for i in range(0x110000):
            try:
                if n(chr(i)) is not None:
                    s.add(i)
            
            except ValueError:
                pass
        
        self.allSpans = span.Span(s)
    
    def oSpan(self, key, thisSpan):
        thisSpan.intersectSpan(self.allSpans)
        v = list(thisSpan)
        
        if len(v) == 1:
            print("% 5s: frozenset(range(%s, %s))," % (str(key), f(v[0][0]), f(1 + v[0][1])))
        
        else:
            v.sort()
            s = ', '.join("range(%s, %s)" % (f(t[0]), f(1 + t[1])) for t in v)
            print("% 5s: frozenset(itertools.chain(%s))," % (str(key), s))
    
    def oSpanAsSpan(self, key, thisSpan):
        if key not in frozenset([60, 90]):
            thisSpan.intersectSpan(self.allSpans)
        
        thisSpan.stringOutputInHex = True
        print("% 5s: (None, f('%s'))," % (str(key), str(thisSpan)))
    
    def report(self):
        for key, pairs in rawData:
            thisSpan = span.SpanFromPairs(pairs)
            self.oSpan(key, thisSpan)
    
    def reportAsSpan(self):
        for key, pairs in rawData:
            thisSpan = span.SpanFromPairs(pairs)
            self.oSpanAsSpan(key, thisSpan)

if __name__ == "__main__":
    infoObj = UInfo()
    infoObj.reportAsSpan()
