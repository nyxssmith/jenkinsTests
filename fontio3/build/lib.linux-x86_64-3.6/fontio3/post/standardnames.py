#
# standardnames.py
#
# Copyright © 2004-2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Various data accessor assistants for the standard 258 names.
"""

# names is simply a tuple of the 258 standard names
names = (
  ".notdef", ".null", "nonmarkingreturn", "space", "exclam", "quotedbl",
  "numbersign", "dollar", "percent", "ampersand", "quotesingle", "parenleft",
  "parenright", "asterisk", "plus", "comma", "hyphen", "period", "slash",
  "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
  "nine", "colon", "semicolon", "less", "equal", "greater", "question", "at",
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O",
  "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "bracketleft",
  "backslash", "bracketright", "asciicircum", "underscore", "grave", "a", "b",
  "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q",
  "r", "s", "t", "u", "v", "w", "x", "y", "z", "braceleft", "bar",
  "braceright", "asciitilde", "Adieresis", "Aring", "Ccedilla", "Eacute",
  "Ntilde", "Odieresis", "Udieresis", "aacute", "agrave", "acircumflex",
  "adieresis", "atilde", "aring", "ccedilla", "eacute", "egrave",
  "ecircumflex", "edieresis", "iacute", "igrave", "icircumflex", "idieresis",
  "ntilde", "oacute", "ograve", "ocircumflex", "odieresis", "otilde", "uacute",
  "ugrave", "ucircumflex", "udieresis", "dagger", "degree", "cent", "sterling",
  "section", "bullet", "paragraph", "germandbls", "registered", "copyright",
  "trademark", "acute", "dieresis", "notequal", "AE", "Oslash", "infinity",
  "plusminus", "lessequal", "greaterequal", "yen", "mu", "partialdiff",
  "summation", "product", "pi", "integral", "ordfeminine", "ordmasculine",
  "Omega", "ae", "oslash", "questiondown", "exclamdown", "logicalnot",
  "radical", "florin", "approxequal", "Delta", "guillemotleft",
  "guillemotright", "ellipsis", "nonbreakingspace", "Agrave", "Atilde",
  "Otilde", "OE", "oe", "endash", "emdash", "quotedblleft", "quotedblright",
  "quoteleft", "quoteright", "divide", "lozenge", "ydieresis", "Ydieresis",
  "fraction", "currency", "guilsinglleft", "guilsinglright", "fi", "fl",
  "daggerdbl", "periodcentered", "quotesinglbase", "quotedblbase",
  "perthousand", "Acircumflex", "Ecircumflex", "Aacute", "Edieresis", "Egrave",
  "Iacute", "Icircumflex", "Idieresis", "Igrave", "Oacute", "Ocircumflex",
  "apple", "Ograve", "Uacute", "Ucircumflex", "Ugrave", "dotlessi",
  "circumflex", "tilde", "macron", "breve", "dotaccent", "ring", "cedilla",
  "hungarumlaut", "ogonek", "caron", "Lslash", "lslash", "Scaron", "scaron",
  "Zcaron", "zcaron", "brokenbar", "Eth", "eth", "Yacute", "yacute", "Thorn",
  "thorn", "minus", "multiply", "onesuperior", "twosuperior", "threesuperior",
  "onehalf", "onequarter", "threequarters", "franc", "Gbreve", "gbreve",
  "Idotaccent", "Scedilla", "scedilla", "Cacute", "cacute", "Ccaron", "ccaron",
  "dcroat")

# nameSet is a frozen set of the names
nameSet = frozenset(names)

# nameDict is a dict mapping the names to their indices in the standard list
nameDict = {s: i for i, s in enumerate(names)}
# nameDict = dict((s, i) for i, s in enumerate(names))  # maps names to indices

# nameToUnicode maps the names to their unichrs
# unicodeToName maps unichrs to their names
m = ["\uffff", "\u0000", "\u000D"]
m.extend(list(str(bytearray(range(32, 127)), 'mac-roman')))
m.extend(list(str(bytearray(range(128, 240)), 'mac-roman')))
m.append("\uf8ff")
m.extend(list(str(bytearray(range(241, 256)), 'mac-roman')))
m.extend(["\u0141", "\u0142", "\u0160", "\u0161"])
m.extend(["\u017D", "\u017E", "\u00A6", "\u00D0"])
m.extend(["\u00F0", "\u00DD", "\u00FD", "\u00DE"])
m.extend(["\u00FE", "\u2212", "\u00D7", "\u00B9"])
m.extend(["\u00B2", "\u00B3", "\u00BD", "\u00BC"])
m.extend(["\u00BE", "\u20A3", "\u011E", "\u011F"])
m.extend(["\u0130", "\u015E", "\u015F", "\u0106"])
m.extend(["\u0107", "\u010C", "\u010D", "\u0111"])
m.append("\u20AC")
v = list(names) + ["Euro"]

nameToUnicode = dict(zip(v, m))
unicodeToName = dict(zip(m, v))

del m, v
