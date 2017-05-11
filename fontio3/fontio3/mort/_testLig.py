#
# _testLig.py
#
# Copyright © 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# from fontio3.mort import (
#   classtable, coverage, entry_ligature, glyphdict, glyphtuple, glyphtupledict,
#   ligature, staterow_ligature)
# 
# GLYPH_c = 70
# GLYPH_e = 72
# GLYPH_f = 73
# GLYPH_i = 76
# GLYPH_l = 79
# GLYPH_o = 82
# GLYPH_fi = 192
# GLYPH_fl = 193
# GLYPH_ff = 330
# GLYPH_ffi = 331
# GLYPH_ffl = 332
# GLYPH_special = 873
# 
# Entry = entry_ligature.Entry
# GTD = glyphtupledict.GlyphTupleDict
# GTI = glyphtuple.GlyphTupleInput
# GTO = glyphtuple.GlyphTupleOutput
# StateRow = staterow_ligature.StateRow
# 
# classTable = classtable.ClassTable({
#     GLYPH_c: "c",
#     GLYPH_e: "e",
#     GLYPH_f: "f",
#     GLYPH_i: "i",
#     GLYPH_l: "l",
#     GLYPH_o: "o"})
# 
# cov = coverage.Coverage(always=True, kind=2)
# 
# entry0 = Entry(
#     newState = "Start of text")
# 
# entry1 = Entry(
#     newState = "Saw f",
#     push = True)
# 
# entry2 = Entry(
#     newState = "Saw o",
#     push = True)
# 
# entry3 = Entry(
#     newState = "Saw ff",
#     push = True,
#     actions = GTD({
#         GTI((GLYPH_f, GLYPH_f)): GTO((GLYPH_ff, None))}))
# 
# entry4 = Entry(
#     newState = "Start of text",
#     push = True,
#     actions = GTD({
#         GTI((GLYPH_f, GLYPH_i)): GTO((GLYPH_fi, None)),
#         GTI((GLYPH_f, GLYPH_l)): GTO((GLYPH_fl, None))}))
# 
# entry5 = Entry(
#     newState = "Start of text",
#     push = True,
#     actions = GTD({
#         GTI((GLYPH_ff, GLYPH_i)): GTO((GLYPH_ffi, None)),
#         GTI((GLYPH_ff, GLYPH_l)): GTO((GLYPH_ffl, None))}))
# 
# entry6 = Entry(
#     newState = "Saw of",
#     push = True)
# 
# entry7 = Entry(
#     newState = "Saw off",
#     push = True,
#     actions = GTD({
#         GTI((GLYPH_f, GLYPH_f)): GTO((GLYPH_ff, None))}))
# 
# entry8 = Entry(
#     newState = "Saw offi",
#     push = True,
#     actions = GTD({
#         GTI((GLYPH_ff, GLYPH_i)): GTO((GLYPH_ffi, None))}))
# 
# entry9 = Entry(
#     newState = "Saw offic",
#     push = True)
# 
# entry10 = Entry(
#     newState = "Start of text",
#     push = True,
#     actions = GTD({
#         GTI((GLYPH_o, GLYPH_ffi, GLYPH_c, GLYPH_e)): GTO((GLYPH_special, None, None, None))}))
# 
# row_SOT = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry0,
#     "f": entry1,
#     "i": entry0,
#     "l": entry0,
#     "o": entry2})
# 
# row_SOL = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry0,
#     "f": entry1,
#     "i": entry0,
#     "l": entry0,
#     "o": entry2})
# 
# row_Sawf = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry0,
#     "f": entry3,
#     "i": entry4,
#     "l": entry4,
#     "o": entry2})
# 
# row_Sawff = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry0,
#     "f": entry1,
#     "i": entry5,
#     "l": entry5,
#     "o": entry2})
# 
# row_Sawo = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry0,
#     "f": entry6,
#     "i": entry0,
#     "l": entry0,
#     "o": entry2})
# 
# row_Sawof = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry0,
#     "f": entry7,
#     "i": entry4,
#     "l": entry4,
#     "o": entry2})
# 
# row_Sawoff = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry0,
#     "f": entry1,
#     "i": entry8,
#     "l": entry5,
#     "o": entry2})
# 
# row_Sawoffi = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry9,
#     "e": entry0,
#     "f": entry1,
#     "i": entry0,
#     "l": entry0,
#     "o": entry2})
# 
# row_Sawoffic = StateRow({
#     "End of text": entry0,
#     "Out of bounds": entry0,
#     "Deleted glyph": entry0,
#     "End of line": entry0,
#     "c": entry0,
#     "e": entry10,
#     "f": entry1,
#     "i": entry0,
#     "l": entry0,
#     "o": entry2})
# 
# ligTable = ligature.Ligature(
#     {
#         "Start of text": row_SOT,
#         "Start of line": row_SOL,
#         "Saw f": row_Sawf,
#         "Saw ff": row_Sawff,
#         "Saw o": row_Sawo,
#         "Saw of": row_Sawof,
#         "Saw off": row_Sawoff,
#         "Saw offi": row_Sawoffi,
#         "Saw offic": row_Sawoffic},
#     coverage = cov,
#     classTable = classTable)
# 
# from fontio3 import fontedit
# e = fontedit.Editor.frompath("/Users/opstadd/Desktop/From other/AC.ttf")
# ligTable.pprint(namer=e.getNamer())
