#
# cffglyph.py
#
# Copyright © 2013-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF Glyphs.
"""

# System imports
import logging

# Other imports
from fontio3.CFF import cffbounds, cffcompositeglyph, cffcontours
from fontio3.CFF.cffutils import stdStrings
from fontio3.CFF.cffutils import pack_t2_number
from fontio3.CFF.encodings_predefined import adobeStandardEncoding
from fontio3.fontdata import simplemeta
from fontio3.fontmath import pointwithonoff, contour_cubic
from fontio3.utilities import walker

# -----------------------------------------------------------------------------

#
# Constants
#

type2OperatorMap = {
    21: ('rmoveto', 'path'),
    22: ('hmoveto', 'path'),
    4: ('vmoveto', 'path'),
    5: ('rlineto', 'path'),
    6: ('hlineto', 'path'),
    7: ('vlineto', 'path'),
    8: ('rrcurveto', 'path'),
    27: ('hhcurveto', 'path'),
    31: ('hvcurveto', 'path'),
    24: ('rcurveline', 'path'),
    25: ('rlinecurve', 'path'),
    30: ('vhcurveto', 'path'),
    26: ('vvcurveto', 'path'),
    (12, 35): ('flex', 'path'),
    (12, 34): ('hflex', 'path'),
    (12, 36): ('hflex1', 'path'),
    (12, 37): ('flex1', 'path'),
    14: ('endchar', 'path'),

    1: ('hstem', 'hint'),
    3: ('vstem', 'hint'),
    18: ('hstemhm', 'hint'),
    23: ('vstemhm', 'hint'),
    19: ('hintmask', 'hint'),
    20: ('cntrmask', 'hint'),

    (12, 9): ('abs', 'arithmetic'),
    (12, 10): ('add', 'arithmetic'),
    (12, 11): ('sub', 'arithmetic'),
    (12, 12): ('div', 'arithmetic'),
    (12, 14): ('neg', 'arithmetic'),
    (12, 23): ('random', 'arithmetic'),
    (12, 24): ('mul', 'arithmetic'),
    (12, 26): ('sqrt', 'arithmetic'),
    (12, 18): ('drop', 'arithmetic'),
    (12, 28): ('exch', 'arithmetic'),
    (12, 29): ('index', 'arithmetic'),
    (12, 30): ('roll', 'arithmetic'),
    (12, 27): ('dup', 'arithmetic'),

    (12, 20): ('put', 'storage'),
    (12, 21): ('get', 'storage'),

    (12, 3): ('and', 'conditional'),
    (12, 4): ('or', 'conditional'),
    (12, 5): ('not', 'conditional'),
    (12, 15): ('eq', 'conditional'),
    (12, 22): ('ifelse', 'conditional'),

    10: ('callsubr', 'subroutine'),
    29: ('callgsubr', 'subroutine'),
    11: ('return', 'subroutine'),
    }

# -----------------------------------------------------------------------------

#
# Private functions
#


def _actualSubrIndex(i, subrlist):
    """
    Operands 10 (callsubr) and 29 (callgsubr) store *biased* values to refer to
    subroutine indexes. The bias value is based on the number of subroutines.
    This function un-biases the stored value to an actual index.
    """

    count = len(subrlist)

    if count < 1240:
        return i + 107

    if count < 33900:
        return i + 1131

    return i + 32768


def _appendPoint(obj, x, y, onCurve):
    """
    Appends a point at (x,y) to the current contour of 'obj' with onCurve.
    Sets obj's 'curX' and 'curY' to the coordinates of the appended point.
    """

    if obj.get('contours') is None:
        obj['contours'] = cffcontours.CFFContours()
        obj['contours'].append(contour_cubic.Contour_cubic())
        obj['curctr'] += 1

    obj['contours'][obj['curctr']].append(
      pointwithonoff.PointWithOnOff((x, y), onCurve=onCurve))

    obj['curX'] = x
    obj['curY'] = y

def _buildGlyph(obj, w, globalsubrs, private, reversecharsetmap, **kwArgs):
    """
    Appends obj with parsed Type2 CharString data from StringWalker w +
    globalsubrs and private (which should include localsubrs).

    It is set up this way to allow recursive calling/subroutines.
    """

    doValidation = kwArgs.get('doValidation', False)

    if doValidation:
        logger = kwArgs.get('logger')

    while w.stillGoing():
        operands = obj.pop('stack', [])
        mask = None

        while w.stillGoing():
            b0 = w.unpack("B")
#             if kwArgs.get('debug', False):
#                 if b0 in type2OperatorMap:
#                     print("operator: %d, operands: %s" % (b0,operands))
#                     print("stemcount: %d" % (obj.get('stemcount', 0),))

            remLen = w.remainingLength()

            # Hint operators --------------------------------------------------

            if b0 in {1, 3, 18, 23}:

                # htsem, vstem, htstemhm, vstemhm with possible width arg
                # hstem |- y dy {dya dyb}* hstem (1) |-
                # vstem |- x dx {dxa dxb}* vstem (3) |-
                # hstemhm |- y dy {dya dyb}* hstemhm (18) |-
                # vstemhm |- x dx {dxa dxb}* vstemhm (23) |-

                opName = type2OperatorMap[b0][0]

                if doValidation:
                    logger.debug((
                      'V0943',
                      (opName, b0, operands),
                      "%s (%d): %s"))

                    if len(operands) < 2:
                        logger.error((
                          'V0986',
                          (opName),
                          "Insufficient operands for %s"))

                        obj['contours'] = None
                        return

                if len(operands) % 2 and obj['advance'] is None:
                    obj['advance'] = (
                      operands.pop(0) + private.get('nominalWidthX', 0))

                obj['hints'].append((operands, opName))
                obj['stemcount'] += len(operands) // 2
                obj['lastOp'] = opName

                break

            elif b0 in [19, 20]:

                # hintmask, cntrmask with possible width arg AND
                # possible implied vstem args.
                # Mask *follows* operator; length of mask depends on # of stems
                # hintmask |- hintmask (19 + mask) |-
                # cntrmask |- cntrmask (20 + mask) |-

                opName = type2OperatorMap[b0][0]

                if len(operands) % 2 and obj['advance'] is None:
                    # width arg
                    nw = private.get('nominalWidthX', 0)
                    obj['advance'] = operands.pop(0) + nw

                if len(operands):
                    # vstem args
                    obj['hints'].append( (operands, 'vstem') )
                    obj['stemcount'] += len(operands) // 2
                    if doValidation:
                        logger.debug((
                          'V0943',
                          (operands, obj['stemcount']),
                          "vstem/hintmask: %s (stemcount: %d)"))

                    obj['lastOp'] = 'vstem'

                masksize = (obj['stemcount'] + 7)//8 # in bytes
                maskraw = w.chunk(masksize)
                mask = _stob(maskraw)

                # mask key is current {X,Y} coordinate
                obj['masks'][(obj['curX'], obj['curY'])] = (mask, opName)

                if doValidation:
                    logger.debug((
                      'V0943',
                      (opName, b0, operands, mask),
                      "%s (%d): %s mask=%s"))

                obj['lastOp'] = opName

                break

            # Path operators --------------------------------------------------

            elif b0 == 21:

                # rmoveto with possible width arg
                # rmoveto |- dx1 dy1 rmoveto (21) |-

                if doValidation:
                    logger.debug(('V0943', (operands,), "rmoveto (21): %s"))

                    if not 2 <= len(operands) <= 3:
                        logger.error((
                          'V0986',
                          (),
                          "Incorrect number of operands for rmoveto"))

                        obj['contours'] = None
                        return

                # append possible previous single-point contour
                if obj['contours'] and len(obj['contours'][obj['curctr']]) == 1:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                if len(operands) > 2:
                    obj['advance'] = (
                      operands.pop(0) + private.get('nominalWidthX', 0))

                if obj['contours'] is None:
                    obj['contours'] = cffcontours.CFFContours()

                obj['contours'].append(contour_cubic.Contour_cubic())
                obj['curctr'] += 1
                obj['curX'] += operands.pop(0)
                obj['curY'] += operands.pop(0)

                if len(obj['contours'][obj['curctr']]) == 0:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                break

            elif b0 == 22:

                # hmoveto with possible width arg (if # args != 1)
                # hmoveto |- dx1 hmoveto (22) |-

                if doValidation:
                    logger.debug(('V0943', (operands,), "hmoveto (22): %s"))

                    if not 1 <= len(operands) <= 2:
                        logger.error((
                          'V0986',
                          (),
                          "Incorrect number of operands for hmoveto"))

                        obj['contours'] = None
                        return

                # append possible previous single-point contour
                if obj['contours'] and len(obj['contours'][obj['curctr']]) == 1:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                if len(operands) > 1:
                    obj['advance'] = (
                      operands.pop(0) + private.get('nominalWidthX', 0))

                if obj['contours'] is None:
                    obj['contours'] = cffcontours.CFFContours()

                obj['contours'].append(contour_cubic.Contour_cubic())
                obj['curctr'] += 1
                obj['curX'] += operands.pop(0)

                if len(obj['contours'][obj['curctr']]) == 0:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                break

            elif b0 == 4:

                # vmoveto with possible width arg.
                # vmoveto |- dy1 vmoveto (4) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "vmoveto (%d): %s"))

                    if not 1 <= len(operands) <= 2:
                        logger.error((
                          'V0986',
                          (),
                          "Incorrect number of operands for vmoveto"))

                        obj['contours'] = None
                        return

                # append possible previous single-point contour
                if obj['contours'] and len(obj['contours'][obj['curctr']]) == 1:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                if len(operands) > 1:
                    obj['advance'] = (
                      operands.pop(0) + private.get('nominalWidthX', 0))

                if obj['contours'] is None:
                    obj['contours'] = cffcontours.CFFContours()

                obj['contours'].append(contour_cubic.Contour_cubic())
                obj['curctr'] += 1
                obj['curY'] += operands.pop(0)

                if len(obj['contours'][obj['curctr']]) == 0:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                break

            elif b0 == 5:

                # rlineto
                # rlineto |- {dxa dya}+ rlineto (5) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "rlineto (%d): %s"))

                    if len(operands) < 2 or len(operands) % 2:
                        logger.error((
                          'V0986',
                          (),
                          "Unexpected number of operands for rlineto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                for i in range(0, len(operands), 2):
                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i],
                      obj['curY'] + operands[i+1],
                      True)

                break

            elif b0 == 6:

                # hlineto
                # hlineto |- dx1 {dya dxb}* hlineto (6) |-
                # hlineto |- {dxa dyb}+ hlineto (6) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "hlineto (%d): %s"))

                    if len(operands) < 1:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for hlineto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                if len(operands) % 2:

                    # odd number of arguments means to append horizontal line
                    # with length = first arg
                    # subsequent *pairs* are alternating v, h

                    dx1 = operands.pop(0)
                    _appendPoint(obj, obj['curX'] + dx1, obj['curY'], True)

                    for i in range(len(operands)):
                        if i % 2:
                            _appendPoint(
                              obj,
                              obj['curX'] + operands[i],
                              obj['curY'],
                              True)

                        else:
                            _appendPoint(
                              obj,
                              obj['curX'],
                              obj['curY'] + operands[i],
                              True)

                else:

                    # even number of arguments: alternate h, v (h first)

                    for i in range(len(operands)):
                        if i % 2:
                            _appendPoint(
                              obj,
                              obj['curX'],
                              obj['curY'] + operands[i],
                              True)

                        else:
                            _appendPoint(
                              obj,
                              obj['curX'] + operands[i],
                              obj['curY'],
                              True)

                break

            elif b0 == 7:

                # vlineto
                # vlineto |- dy1 {dxa dyb}* vlineto (7) |-
                # vlineto |- {dya dxb}+ vlineto (7) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "vlineto (%d): %s"))
                    if len(operands) < 1:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for vlineto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                if len(operands) % 2:

                    # odd number of arguments means to append vertical line
                    # with length = first arg
                    # subsequent *pairs* are alternating h, v

                    dy1 = operands.pop(0)
                    _appendPoint(obj, obj['curX'], obj['curY'] + dy1, True)

                    for i in range(len(operands)):
                        if i % 2:
                            _appendPoint(
                              obj,
                              obj['curX'],
                              obj['curY'] + operands[i],
                              True)

                        else:
                            _appendPoint(
                              obj,
                              obj['curX'] + operands[i],
                              obj['curY'],
                              True)

                else:

                    # even number of arguments means alternate v, h (v first)

                    for i in range(len(operands)):
                        if i % 2:
                            _appendPoint(
                              obj,
                              obj['curX'] + operands[i],
                              obj['curY'],
                              True)

                        else:
                            _appendPoint(
                              obj,
                              obj['curX'],
                              obj['curY'] + operands[i],
                              True)
                break

            elif b0 == 8:

                # rrcurveto
                # rrcurveto - {dxa dya dxb dyb dxc dyc}+ rrcurveto (8) |-

                if doValidation:
                    logger.debug((
                      'V0943',
                      (b0, operands),
                      "rrcurveto (%d): %s"))

                    if len(operands) < 6:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for rrcurveto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                for i in range(0, len(operands), 6):
                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i],
                      obj['curY'] + operands[i+1],
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i+2],
                      obj['curY'] + operands[i+3],
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i+4],
                      obj['curY'] + operands[i+5],
                      True)

                break

            elif b0 == 27:

                # hhcurveto
                # hhcurveto |- dy1? {dxa dxb dyb dxc}+ hhcurveto (27) |-

                if doValidation:
                    logger.debug((
                      'V0943',
                      (b0, operands),
                      "hhcurveto (%d): %s"))

                    if len(operands) < 4:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for hhcurveto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                dy1 = (operands.pop(0) if len(operands) % 4 else 0)

                for i in range(0, len(operands), 4):
                    dyInitial = dy1 if i == 0 else 0

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i],
                      obj['curY'] + dyInitial,
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i+1],
                      obj['curY'] + operands[i+2],
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i+3],
                      obj['curY'],
                      True)

                break

            elif b0 == 31:

                # hvcurveto
                # hvcurveto |- dx1 dx2 dy2 dy3 {dya dxb dyb dxc dxd dxe dye dyf}* dxf?
                # hvcurveto |- {dxa dxb dyb dyc dyd dxe dye dxf}+ dyf? hvcurveto (31) |-

                if doValidation:
                    logger.debug((
                      'V0943',
                      (b0, operands),
                      "hvcurveto (%d): %s"))

                    if len(operands) < 4:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for hvcurveto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                h = True
                df = operands.pop() if len(operands) % 4 else 0

                for i in range(0, len(operands), 4):
                    dFinal = (df if i + 4 == len(operands) else 0)

                    if h:
                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i],
                          obj['curY'],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i+1],
                          obj['curY'] + operands[i+2],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + dFinal,
                          obj['curY'] + operands[i+3],
                          True)

                    else:
                        _appendPoint(
                          obj,
                          obj['curX'],
                          obj['curY'] + operands[i],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i+1],
                          obj['curY'] + operands[i+2],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i+3],
                          obj['curY'] + dFinal,
                          True)

                    h = not h # alternate each time through

                break

            elif b0 == 24:

                # rcurveline
                # rcurveline |- {dxa dya dxb dyb dxc dyc}+ dxd dyd rcurveline (24) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "rcurveline (%d): %s"))

                    if len(operands) < 8:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for rcurveline"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                dyd = operands.pop()
                dxd = operands.pop()

                for i in range(0, len(operands), 6):
                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i],
                      obj['curY'] + operands[i+1],
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i+2],
                      obj['curY'] + operands[i+3],
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i+4],
                      obj['curY'] + operands[i+5],
                      True)

                _appendPoint(obj, obj['curX'] + dxd, obj['curY'] + dyd, True)
                break

            elif b0 == 25:

                # rlinecurve
                # rlinecurve |- {dxa dya}+ dxb dyb dxc dyc dxd dyd rlinecurve (25) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "rlinecurve (%d): %s"))

                    if len(operands) < 8:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for rlinecurve"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                dyd, dxd, dyc, dxc, dyb, dxb = [
                  operands.pop() for i in range(6)]

                for i in range(0, len(operands), 2):
                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i],
                      obj['curY'] + operands[i+1],
                      True)

                _appendPoint(obj, obj['curX'] + dxb, obj['curY'] + dyb, False)
                _appendPoint(obj, obj['curX'] + dxc, obj['curY'] + dyc, False)
                _appendPoint(obj, obj['curX'] + dxd, obj['curY'] + dyd, True)
                break

            elif b0 == 30:

                # vhcurveto
                # vhcurveto |- dy1 dx2 dy2 dx3 {dxa dxb dyb dyc dyd dxe dye dxf}* dyf?
                # |- {dya dxb dyb dxc dxd dxe dye dyf}+ dxf? vhcurveto (30) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "vhcurveto (%d): %s"))

                    if len(operands) < 4:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for vhcurveto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                v = True
                df = (operands.pop() if len(operands) % 4 else 0)

                for i in range(0, len(operands), 4):
                    dFinal = df if i + 4 == len(operands) else 0

                    if v:
                        _appendPoint(
                          obj,
                          obj['curX'],
                          obj['curY'] + operands[i],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i+1],
                          obj['curY'] + operands[i+2],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i+3],
                          obj['curY'] + dFinal,
                          True)

                    else:
                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i],
                          obj['curY'],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + operands[i+1],
                          obj['curY'] + operands[i+2],
                          False)

                        _appendPoint(
                          obj,
                          obj['curX'] + dFinal,
                          obj['curY'] + operands[i+3],
                          True)

                    v = not v # alternate each time through

                break

            elif b0 == 26:

                # vvcurveto
                # vvcurveto |- dx1? {dya dxb dyb dyc}+ vvcurveto (26) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "vvcurveto (%d): %s"))

                    if len(operands) < 4:
                        logger.error((
                          'V0986',
                          (),
                          "Insufficient operands for vvcurveto"))

                        obj['contours'] = None
                        return

                if obj is None or obj.get('contours') is None:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                dx1 = operands.pop(0) if len(operands) % 4 else 0

                for i in range(0, len(operands), 4):
                    dxInitial = (dx1 if i == 0 else 0)

                    _appendPoint(
                      obj,
                      obj['curX'] + dxInitial,
                      obj['curY'] + operands[i],
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[i+1],
                      obj['curY'] + operands[i+2],
                      False)

                    _appendPoint(
                      obj,
                      obj['curX'],
                      obj['curY'] + operands[i+3],
                      True)

                break

            elif b0 == 14:

                # endchar with possible width arg OR possible seac args
                # endchar - endchar (14) |-

                if doValidation:
                    logger.debug(('V0943', (b0, operands), "endchar (%d): %s"))

                    if len(operands) not in (0, 1, 4, 5):
                        logger.error((
                          'V0986',
                          (),
                          "Incorrect number of operands for endchar"))

                        obj['contours'] = None
                        return

                if len(operands) % 2:
                    # odd # means there is a width
                    obj['advance'] = operands.pop(0) + private.get('nominalWidthX', 0)

                if len(operands) == 4:

                    # 4 remaining operands are from seac:
                    #    'adx', 'ady', 'bchar', 'achar'.
                    # 'bchar' and 'achar' must:
                    #  1) be Standard Encoding codes and
                    #  2) be present in this font
                    #
                    # Translate to SID then look up that SID in the _CFF
                    # reverse charset mapping.

                    if doValidation:
                        logger.error((
                          "V0921",
                          (),
                          "Glyph uses deprecated 'seac' operator"))

                    components = []

                    for o in operands[2:]:
                        sid = adobeStandardEncoding.get(o, None)

                        if sid:
                            sstr = stdStrings[sid]

                            if sstr:
                                gid = reversecharsetmap.get(sstr)
                                components.append(gid)

                    obj['contours'] = None
                    obj['components'] = components
                    obj['accentoffset'] = operands[:2]

                # check for un-added single-point contour.
                if obj['contours'] and len(obj['contours'][obj['curctr']]) == 1:
                    _appendPoint(obj, obj['curX'], obj['curY'], True)

                break

            # Subroutine operators --------------------------------------------

            elif b0 == 10:

                # callsubr
                # callsubr subr# callsubr (10) -

                if doValidation:
                    if len(operands) < 1:
                        logger.error((
                            'V0986',
                            (),
                            "Insufficient operands for callsubr"))

                        obj['contours'] = None
                        return

                    if not hasattr(private, 'localsubrs'):
                        logger.error((
                          'V0993',
                          (),
                          "callsubr in glyph data but no Subrs in Private DICT"))
                        return
                    
                subridx = _actualSubrIndex(operands.pop(), private.localsubrs)

                if doValidation:
                    # show the actual subrIdx, not the operand value
                    logger.debug((
                      'V0943',
                      (b0, subridx, operands),
                      "callsubr (%d): %d %s"))

                obj['stack'] = operands
#                 if kwArgs.get('debug', False):
#                     print("callsubr %d:" % (subridx,))
#                     print(utilities.hexdumpString(private.localsubrs[subridx]), end='')
#                     print("")

                if 0 <= subridx < len(private.localsubrs):
                    subrStr = private.localsubrs[subridx]
                    lensubr = len(subrStr)
                    if doValidation:
                        logger.debug((
                          'Vxxxx',
                          (lensubr,),
                          "callsubr length of subroutine is %d bytes"))

                    if lensubr:
                        wSub = walker.StringWalker(subrStr)
                        _buildGlyph(obj,
                                    wSub,
                                    globalsubrs,
                                    private,
                                    reversecharsetmap,
                                    **kwArgs)

                    else:
                        if doValidation:
                            logger.error((
                              'Vxxxx',
                              (),
                              "callsubr with empty local subroutine!"))
                              
                else:
                    if doValidation:
                        logger.error((
                          'Vxxxx',
                          (subridx,),
                          "Subroutine index %d not found in localsubrs"))

                break

            elif b0 == 29:

                # callgsubr
                # callgsubr globalsubr# callgsubr (29) -

                if doValidation:
                    if len(operands) < 1:
                        logger.error((
                            'V0986',
                            (),
                            "Insufficient operands for callgsubr"))

                        obj['contours'] = None
                        return

                subridx = _actualSubrIndex(operands.pop(), globalsubrs)

                if doValidation:
                    # show the actual subrIdx, not the operand value
                    logger.debug((
                      'V0943',
                      (b0, subridx, operands),
                      "callgsubr (%d): %d %s"))

                obj['stack'] = operands
#                 if kwArgs.get('debug', False):
#                     print("callgsubr %d:" % (subridx,))
#                     print(utilities.hexdumpString(globalsubrs[subridx]), end='')
#                     print("")
                wSub = walker.StringWalker(globalsubrs[subridx])
                _buildGlyph(obj, wSub, globalsubrs, private, reversecharsetmap, **kwArgs)
                break

            elif b0 == 11:

                # subroutine return

                if doValidation:
                    logger.debug((
                      'V0943',
                      (b0, operands),
                      "return (%d): %s"))

                obj['stack'] = operands
                break

            # Operands --------------------------------------------------------

            elif b0 == 28:
                if remLen < 2:
                    if doValidation:
                        logger.error((
                          'V0004',
                          (),
                          "Insufficient bytes for 3-byte operand"))

                        obj['contours'] = None
                        return

                operands.append(w.unpack("h")) # 2-byte signed integer operand

            elif 32 <= b0 <= 246:
                operands.append(b0 - 139) # 1-byte operand

            elif 247 <= b0 <= 254: # two-byte number operand
                if remLen < 1:
                    if doValidation:
                        logger.error((
                          'V0004',
                          (),
                          "Insufficient bytes for 2-byte operand"))

                        obj['contours'] = None
                        return

                b1 = w.unpack("B")

                if b0 < 251:
                    operands.append((b0 - 247) * 256 + b1 + 108)
                else:
                    operands.append((251 - b0) * 256 - b1 - 108)

            elif b0 == 255: # 16.16
                if remLen < 4:
                    if doValidation:
                        logger.error((
                          'V0004',
                          (),
                          "Insufficient bytes for 16.16 operand"))

                    obj['contours'] = None
                    return

                operands.append(w.unpack("l")/65536.0)

            elif b0 == 12: # extension operator
                b1 = w.unpack("B")

                if b1 == 34:

                    # hflex
                    # hflex |- dx1 dx2 dy2 dx3 dx4 dx5 dx6 hflex (12 34) |-

                    if doValidation:
                        logger.debug(('V0943', (b1, operands), "hflex (12,%d): %s"))

                        if len(operands) != 7:
                            logger.error((
                              'V0986',
                              (),
                              "Incorrect number of operands for hflex"))

                            obj['contours'] = None
                            return

                    yStart = obj['curY']

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[0],
                      yStart,
                      False) # dx1

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[1],
                      obj['curY'] + operands[2],
                      False) # dx2, dy2

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[3],
                      obj['curY'],
                      True) # dx3

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[4],
                      obj['curY'],
                      False) # dx4

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[5],
                      yStart,
                      False) # dx5

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[6],
                      yStart,
                      True) # dx6

                    break

                elif b1 == 35:

                    # flex
                    # flex |- dx1 dy1 dx2 dy2 dx3 dy3 dx4 dy4 dx5 dy5 dx6 dy6 fd

                    if doValidation:
                        logger.debug(('V0943', (b1, operands), "flex (12,%d): %s"))

                        if len(operands) != 13:
                            logger.error((
                              'V0986',
                              (),
                              "Incorrect number of operands for flex"))

                            obj['contours'] = None
                            return

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[0],
                      obj['curY'] + operands[1],
                      False) # dx1, dy1

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[2],
                      obj['curY'] + operands[3],
                      False) # dx2, dy2

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[4],
                      obj['curY'] + operands[5],
                      True)  # dx3, dy3

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[6],
                      obj['curY'] + operands[7],
                      False) # dx4, dy4

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[8],
                      obj['curY'] + operands[9],
                      False) # dx5, dy5

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[10],
                      obj['curY'] + operands[11],
                      True)  # dx6, dy6

                    break

                elif b1 == 36:

                    # hflex1
                    # hflex1 |- dx1 dy1 dx2 dy2 dx3 dx4 dx5 dy5 dx6 hflex1 (12 36) |-

                    if doValidation:
                        logger.debug(('V0943', (b1, operands), "hflex1 (12,%d): %s"))

                        if len(operands) != 9:
                            logger.error((
                              'V0986',
                              (),
                              "Incorrect number of operands for hflex1"))

                            obj['contours'] = None
                            return

                    yStart = obj['curY']

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[0],
                      obj['curY'] + operands[1],
                      False) # dx1, dy1

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[2],
                      obj['curY'] + operands[3],
                      False) # dx2, dy2

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[4],
                      obj['curY'],
                      True)  # dx3

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[5],
                      obj['curY'],
                      False) # dx4

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[6],
                      obj['curY'] + operands[7],
                      False) # dx5, dy5

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[8],
                      yStart,
                      True)  # dx6

                    break

                elif b1 == 37:

                    # flex1
                    # flex1 |- dx1 dy1 dx2 dy2 dx3 dy3 dx4 dy4 dx5 dy5 d6 flex1 |-

                    if doValidation:
                        logger.debug(('V0943', (b1, operands), "flex1 (12,%d): %s"))

                        if len(operands) != 11:
                            logger.error((
                              'V0986',
                              (),
                              "Incorrect number of operands for flex1"))

                            obj['contours'] = None
                            return

                    dx = dy = 0
                    xStart = obj['curX']
                    yStart = obj['curY']

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[0],
                      obj['curY'] + operands[1],
                      False) # dx1, dy1

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[2],
                      obj['curY'] + operands[3],
                      False) # dx2, dy2

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[4],
                      obj['curY'] + operands[5],
                      True)  # dx3, dy3

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[6],
                      obj['curY'] + operands[7],
                      False) # dx4, dy4

                    _appendPoint(
                      obj,
                      obj['curX'] + operands[8],
                      obj['curY'] + operands[9],
                      False) # dx5, dy5

                    # meaning of d6 is dependent on orientation of curve, determined
                    # by summing prior x and y operands (every other one).
                    dx = sum(operands[0:-2:2])
                    dy = sum(operands[1:-1:2])

                    # strong X; d6 is delta to x; y=yStart
                    if abs(dx) > abs(dy):
                        _appendPoint(
                          obj,
                          obj['curX'] + operands[10],
                          yStart,
                          True) # dx6

                    # strong Y; d6 is delta to y; x=xStart
                    else:
                        _appendPoint(
                          obj,
                          xStart,
                          obj['curY'] + operands[10],
                          True) # dy6

                    break

                else:
                    extop = type2OperatorMap.get(
                      (12, b1), ('unknownExtensionOperator','unknown'))

                    s = "Unknown extension operator (12,%d) with operands %s" % (
                      b1, operands)

                    if doValidation:
                        logger.error((
                          'V0867',
                          (s),
                          "%s"))

                        obj['contours'] = None
                        return

                    else:
                        raise ValueError(s)

            else:
                s = "Unknown operator %d with operands %s" % (b0, operands)

                if doValidation:
                    logger.error((
                      'V0867',
                      (s),
                      "%s"))

                    obj['contours'] = None
                    return

                else:
                    raise ValueError(s)


def _recalc(obj, **kwArgs):
    """
    Recalculate the object, returning a boolean indicating whether the
    recalculated object is equal to the old object + the new object.
    """
    newObj = obj.__copy__()
    newObj.bounds = cffbounds.CFFBounds.fromcontours(obj.contours)
    return newObj != obj, newObj


def _stob(s):
    """
    Express variable-length bytestring 's' as 1s and 0s, used for masks.
    >>> _stob(b'\x01')
    '00000001'
    >>> _stob(b'abc')
    '011000010110001001100011'
    """
    return "".join(['{0:08b}'.format(c) for c in s])


def _validate(obj, **kwArgs):
    """Perform 'isValid' validation on the object."""
    logger = kwArgs['logger']

    if obj.contours:
        for i, ctr in enumerate(obj.contours):
            if len(ctr) == 1:
                logger.warning((
                  'W1113',
                  (i,),
                  "Contour %d is degenerate (only a single (x, y) location)."))
                  
            if len(ctr) == 2:
                logger.error((
                  'V1013',
                  (i,),
                  "Contour %d is degenerate (only two (x, y) locations)."))

    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CFFGlyph(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire CFF glyphs, constructed from the combination of
    glyph CharStrings, Global (CFF table-wide) subroutines, and Local
    (font-specific) subroutines.
    """

    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)

    attrSpec = dict(
        bounds = dict(
            attr_followsprotocol = True,
            attr_label = "Bounds",
            attr_strneedsparens = True,
            attr_initfunc = (lambda: None)),

        contours = dict(
            attr_followsprotocol = True,
            attr_label = "Contours"),

        cffAdvance = dict(
            attr_label = "CFF Advance",
            attr_initfunc = lambda: 0),
        )

    isComposite = False

    #
    # Class methods
    #



    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary charstring data for the CFFGlyph object to the
        specified LinkedWriter.
        >>> myglyph = _testingValues[0]
        >>> h = utilities.hexdumpString
        >>> print(h(myglyph.binaryString()), end='')
               0 |F75C EFEF 15EF 06EF  0727 060E           |.\.......'..    |

        """
        privatedict=kwArgs.get('private', dict())

        nominalWidthX = privatedict.get('nominalWidthX', 0)
        defaultWidthX = privatedict.get('defaultWidthX', 0)	

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        if defaultWidthX != self.cffAdvance:
            pack_t2_number(self.cffAdvance-nominalWidthX, w) # glyph width

        if self.contours is not None:
            n_total = 0
            ptPrev = pointwithonoff.PointWithOnOff(0,0)
            for ci, cntr in enumerate(self.contours):
                n = 0

                if len(cntr) == 1:
                    # special case single-point contours
                    ptCurr = cntr[0]
                    if ptCurr.x == ptPrev.x:
                        pack_t2_number(ptCurr.y - ptPrev.y, w)
                        w.add("B", 4) # vmoveto
                    elif ptCurr.y == ptPrev.y:
                        pack_t2_number(ptCurr.x - ptPrev.x, w)
                        w.add("B", 22) # hmoveto
                    else:
                        pack_t2_number(ptCurr.x - ptPrev.x, w)
                        pack_t2_number(ptCurr.y - ptPrev.y, w)
                        w.add("B", 21) # rmoveto
                    ptPrev = ptCurr
                    continue

                while n < len(cntr) - 1:
                    ptCurr = cntr[n]
                    if not ptCurr.onCurve:
                        raise ValueError("Unexpected off-curve at pt %d." % (n_total,))

                    if n == 0:
                        # contour start
                        if ptCurr.x == ptPrev.x:
                            pack_t2_number(ptCurr.y - ptPrev.y, w)
                            w.add("B", 4) # vmoveto
                        elif ptCurr.y == ptPrev.y:
                            pack_t2_number(ptCurr.x - ptPrev.x, w)
                            w.add("B", 22) # hmoveto
                        else:
                            pack_t2_number(ptCurr.x - ptPrev.x, w)
                            pack_t2_number(ptCurr.y - ptPrev.y, w)
                            w.add("B", 21) # rmoveto

                    if n + 1 >= len(cntr):
                        ptNext = cntr[0]
                    else:
                        ptNext = cntr[n + 1]

                    if ptNext.onCurve:
                        # state: on, on -> do lineto
                        if ptNext.y == ptCurr.y:
                            pack_t2_number((ptNext.x - ptCurr.x), w)
                            w.add("B", 6) # hlineto
                        elif ptNext.x == ptCurr.x:
                            pack_t2_number((ptNext.y - ptCurr.y), w)
                            w.add("B", 7) # vlineto
                        else:
                            pack_t2_number((ptNext.x - ptCurr.x), w)
                            pack_t2_number((ptNext.y - ptCurr.y), w)
                            w.add("B", 5) # rlineto

                        n += 1
                        n_total += 1
                        ptPrev = ptNext

                    else:
                        # state: on, off; expect off, on to follow.
                        ptC0 = ptNext # n + 1
                        ptC1 = cntr[n + 2]

                        if n + 3 >= len(cntr):
                            ptEnd = cntr[0]
                        else:
                            ptEnd = cntr[n + 3]

                        if (ptCurr.onCurve and
                          not(ptC0.onCurve) and
                          not(ptC1.onCurve) and ptEnd.onCurve):
                            pack_t2_number((ptC0.x - ptCurr.x), w)
                            pack_t2_number((ptC0.y - ptCurr.y), w)
                            pack_t2_number((ptC1.x - ptC0.x), w)
                            pack_t2_number((ptC1.y - ptC0.y), w)
                            pack_t2_number((ptEnd.x - ptC1.x), w)
                            pack_t2_number((ptEnd.y - ptC1.y), w)
                            w.add("B", 8) # rrcurveto
                        else:
                            raise ValueError("Unexpected %s-%s-%s-%s sequence "
                              "at pt %d of contour %d" % (
                                "on" if ptCurr.onCurve else "off",
                                "on" if ptC0.onCurve else "off",
                                "on" if ptC1.onCurve else "off",
                                "on" if ptEnd.onCurve else "off",
                                n_total,
                                ci))

                        n += 3
                        n_total += 3
                        ptPrev = ptEnd

        w.add("B", 14) # endchar

    @classmethod
    def fromcffdata(
      cls, charstring, privatedict, globalsubrs, reversecharsetmap, **kwArgs):


        """
        Constructs and returns a CFFGlyph by parsing and interpreting the
        specified charstring, privatedict (containing localsubrs), and
        globalsubrs, *ALL* of which are required in order to fully parse a
        glyph into a usable form.

        >>> cs = utilities.fromhex(
        ...   "8C 8B BD F7 ED 77 F7 A7 BD 01 8B BD F8 24 BD 03 "
        ...   "8B 04 F8 88 F9 50 FC 88 06 F7 8E FB C5 15 FB 3E "
        ...   "F7 93 05 F7 E8 06 FB 20 FB C0 15 F7 3E F7 93 05 "
        ...   "FC 92 07 FC 06 5E 15 F7 3E F7 93 F7 3E FB 93 05 "
        ...   "FC 06 F8 BF 15 F7 3E FB 93 FB 3E FB 93 05 0E")
        >>> pd = {'nominalWidthX': 499}
        >>> CFFGlyph.fromcffdata(cs, pd, [], {}).pprint()
        Bounds:
          Minimum X: 0
          Minimum Y: 0
          Maximum X: 500
          Maximum Y: 700
        CFF Advance: 500
        Contours:
          Contour 0:
            Point 0: (0, 0), on-curve
            Point 1: (500, 0), on-curve
            Point 2: (500, 700), on-curve
            Point 3: (0, 700), on-curve
          Contour 1:
            Point 0: (250, 395), on-curve
            Point 1: (80, 650), on-curve
            Point 2: (420, 650), on-curve
          Contour 2:
            Point 0: (280, 350), on-curve
            Point 1: (450, 605), on-curve
            Point 2: (450, 95), on-curve
          Contour 3:
            Point 0: (80, 50), on-curve
            Point 1: (250, 305), on-curve
            Point 2: (420, 50), on-curve
          Contour 4:
            Point 0: (50, 605), on-curve
            Point 1: (220, 350), on-curve
            Point 2: (50, 95), on-curve
        """

        glyphobj = dict(
          hints = [],
          masks = {},
          contours = None,
          curX = 0,
          curY = 0,
          curctr = -1,
          advance = None,
          stemcount = 0,
          stack = [],
          lastOp = 0,
          components = [],
          accentoffset = [])

        w = walker.StringWalker(charstring)

        _buildGlyph(
          glyphobj, w, globalsubrs, privatedict, reversecharsetmap, **kwArgs)

        if glyphobj.get('contours', None) is not None:
            for cntr in glyphobj['contours']:
                if cntr[0] == cntr[-1]: del(cntr[-1]) # duplicated start/end

        if glyphobj['advance'] is None:
            glyphobj['advance'] = privatedict.get('defaultWidthX', 0)

        if glyphobj['components']:
            return cffcompositeglyph.CFFCompositeGlyph.fromcffdata(
              glyphobj['components'],
              glyphobj['accentoffset'],
              glyphobj['advance'],
              _origcharstring=charstring,
              )

        elif glyphobj['contours']:
            contours = glyphobj['contours']
            bounds = cffbounds.CFFBounds.fromcontours(contours or [])
            return cls(
              contours=contours,
              bounds=bounds,
              cffAdvance=glyphobj['advance'],
              _origcharstring=charstring,
              )

        else:
            # empty glyph
            return cls(
              bounds=cffbounds.CFFBounds(),
              cffAdvance=glyphobj['advance'],
              _origcharstring="",
              )


    @classmethod
    def fromvalidatedcffdata(
      cls, charstring, privatedict, globalsubrs, reversecharsetmap, **kwArgs):

        """
        Like fromcffdata(), this method constructs and returns a CFFGlyph by
        parsing and interpreting the specified charstring, privatedict
        (containing localsubrs), and globalsubrs, *ALL* of which are required
        in order to fully parse a glyph into a usable form. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger('charstring')
        else:
            logger = logger.getChild('charstring')

        glyphobj = dict(
          hints = [],
          masks = {},
          contours = None,
          curX = 0,
          curY = 0,
          curctr = -1,
          advance = None,
          stemcount = 0,
          stack = [],
          lastOp = 0,
          components = [],
          accentoffset = [])

        w = walker.StringWalker(charstring)

        _buildGlyph(
          glyphobj,
          w,
          globalsubrs,
          privatedict,
          reversecharsetmap,
          doValidation = True,
          logger = logger,
          **kwArgs)

        if glyphobj.get('contours', None) is not None:
            for cntr in glyphobj['contours']:
                if cntr[0] == cntr[-1]: del(cntr[-1]) # duplicated start/end

        if glyphobj['advance'] is None:
            glyphobj['advance'] = privatedict.get('defaultWidthX', 0)

        if glyphobj['components']:
            return cffcompositeglyph.CFFCompositeGlyph.fromvalidatedcffdata(
              glyphobj['components'],
              glyphobj['accentoffset'],
              glyphobj['advance'],
              _origcharstring=charstring,
              )

        elif glyphobj['contours']:
            contours = glyphobj['contours']
            bounds = cffbounds.CFFBounds.fromcontours(contours or [])
            return cls(
              contours=contours,
              bounds=bounds,
              cffAdvance=glyphobj['advance'],
              _origcharstring=charstring,
              )

        else:
            # empty glyph
            return cls(
              bounds=cffbounds.CFFBounds(),
              cffAdvance=glyphobj['advance'],
              _origcharstring="",
              )


    def pointCount(self, **kwArgs):
        """
        Returns the number of points in the (unnormalized) glyph. The following
        keyword arguments are supported but ignored (they are used in the
        pointCount() method for composite glyphs):
        
            editor      This is ignored here.
        """
        
        return sum(len(c) for c in self.contours)


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

    _testingValues = [
        CFFGlyph(
            cffAdvance = 200,
            contours = cffcontours.CFFContours(
                [contour_cubic.Contour_cubic([
                    pointwithonoff.PointWithOnOff((100,100),onCurve=True ),
                    pointwithonoff.PointWithOnOff((200,100),onCurve=True ),
                    pointwithonoff.PointWithOnOff((200,200),onCurve=True ),
                    pointwithonoff.PointWithOnOff((100,200),onCurve=True )
                ])]),
            bounds = cffbounds.CFFBounds(
                xMin=100,
                xMax=200,
                yMin=100,
                yMax=200))]

def _test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    if __debug__:
        _test()

