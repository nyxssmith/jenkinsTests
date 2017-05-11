theModule = """

# The following are feature effects; as features are selected (and remember
# that order is important!) these are integrated into the current effectsList.
# However, any names starting with an underscore are not top-level features,
# but rather are used to build those features.

#
# Swash example
#

_swashInputs = tuple(range(glyphA, glyphZ + 1))
_swashOutputs = tuple(range(glyphASwash, glyphZSwash + 1))

swashCaps = Effect({
    _swashInputs: [('currentToIndexedGlyph', _swashOutputs)]}

#
# Simple (non-brittle) Latin ligs example
#

_latinLigs3 = Effect({
    glyph_l: [
        ('changeMarked', 'latinBasicLigatures_f', glyph_ffl),
        ('currentToGlyph', None),
        ('removeThisEffect',)],
    
    glyph_i: [
        ('changeMarked', 'latinBasicLigatures_f', glyph_ffi),
        ('currentToGlyph', None),
        ('removeThisEffect',)]})

_latinLigs2 = Effect({
    glyph_i: [
        ('changeMarked', 'latinBasicLigatures_f', glyph_fi),
        ('currentToGlyph', None),
        ('removeThisEffect',)],
    
    glyph_l: [
        ('changeMarked', 'latinBasicLigatures_f', glyph_fl),
        ('currentToGlyph', None),
        ('removeThisEffect',)],
    
    glyph_f: [
        ('changeMarked', 'latinBasicLigatures_f', glyph_ff),
        ('currentToGlyph', None),
        ('addEffect', _latinLigs3),
        ('removeThisEffect',)]})

latinBasicLigatures = Effect({
    glyph_f: [
        ('markCurrent', 'latinBasicLigatures_f'),
        ('addEffect', _latinLigs2)]})

#
# Fancy (brittle) Latin lig example
#

_latinFancyLigs7 = Effect({
    glyph_o: [
        ('changeMarked', 'latinFancyLigatures_Zapfino_1', glyph_Zapfino),
        ('changeMarked', 'latinFancyLigatures_Zapfino_2', None),
        ('changeMarked', 'latinFancyLigatures_Zapfino_3', None),
        ('changeMarked', 'latinFancyLigatures_Zapfino_4', None),
        ('changeMarked', 'latinFancyLigatures_Zapfino_5', None),
        ('changeMarked', 'latinFancyLigatures_Zapfino_6', None),
        ('currentToGlyph', None),
        ('removeThisEffect',)]})

_latinFancyLigs6 = Effect({
    glyph_n: [
        ('markCurrent', 'latinFancyLigatures_Zapfino_6'),
        ('addEffect', _latinFancyLigs7),
        ('removeThisEffect',)]})

_latinFancyLigs5 = Effect({
    glyph_i: [
        ('markCurrent', 'latinFancyLigatures_Zapfino_5'),
        ('addEffect', _latinFancyLigs6),
        ('removeThisEffect',)]})

_latinFancyLigs4 = Effect({  # note this is integrated so 'fi' still forms...
    glyph_f: [
        ('markCurrent', 'latinFancyLigatures_Zapfino_4'),
        ('addEffect', _latinFancyLigs5),
        ('removeThisEffect',)]})

_latinFancyLigs3 = Effect({
    glyph_p: [
        ('markCurrent', 'latinFancyLigatures_Zapfino_3'),
        ('addEffect', _latinFancyLigs4),
        ('removeThisEffect',)]})

_latinFancyLigs2 = Effect({
    glyph_a: [
        ('markCurrent', 'latinFancyLigatures_Zapfino_2'),
        ('addEffect', _latinFancyLigs3),
        ('removeThisEffect',)]})

latinFancyLigatures = Effect({
    glyph_Z: [
        ('markCurrent', 'latinFancyLigatures_Zapfino_1'),
        ('addEffect', _latinFancyLigs2)]})
"""
