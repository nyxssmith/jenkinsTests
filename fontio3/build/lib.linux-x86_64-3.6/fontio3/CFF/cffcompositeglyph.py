#
# cffcompositeglyph.py
#
# Copyright © 2013-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF Composite Glyphs.
"""

# System imports
import functools
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import seqmeta, simplemeta
from fontio3.fontmath import matrix, rectangle
from fontio3.CFF.cffutils import pack_t2_number

# -----------------------------------------------------------------------------

#
# Private functions
#

def _recalc(obj, **kwArgs):
    editor = kwArgs.get('editor')
    cfftbl = editor[b'CFF ']
    accentglyph = cfftbl[obj.accentGlyph]
    baseglyph = cfftbl[obj.baseGlyph]
    newglyph= baseglyph.__deepcopy__()
    mark = accentglyph.__deepcopy__().transformed(obj.accentOffset) # X/Y offset
    
    if mark.contours is not None:  # yes, it can happen...
        newglyph.contours += mark.contours
    
    newglyph = newglyph.recalculated()
    r = obj.__deepcopy__()
    r.bounds = newglyph.bounds
    return r != obj, r

def _validate(obj, **kwArgs):
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class BadEditorOrCFF(ValueError): pass

class CFFCompositeGlyph(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire CFF "Composite" glyphs (as indicated by 'seac'
    operator).
    """

    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)

    attrSpec = dict(
        bounds = dict(
            attr_followsprotocol = True,
            attr_label = "Bounds",
            attr_strneedsparens = True),

        baseGlyph = dict(
            attr_label = "Base",
            attr_renumberdirect = True,
            attr_usenamerforstr = True),

        accentGlyph = dict(
            attr_label = "Accent",
            attr_renumberdirect = True,
            attr_usenamerforstr = True),

        accentOffset = dict(
            attr_label = "Accent Offset"),

        cffAdvance = dict(
            attr_label = "CFF Advance",
            attr_initfunc=lambda:0),
        )

    isComposite = True

    #
    # Class methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary charstring data for the CFFCompositeGlyph object to the
        specified LinkedWriter.
        #>>> myglyph = _testingValues[0]
        #>>> h = utilities.hexdumpString
        #>>> print(h(myglyph.binaryString()), end='')
        """

        if 'stakeValue' in kwArgs:

            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)

        else:
            stakeValue = w.stakeCurrent()

        privatedict=kwArgs.get('private', dict())

        nominalWidthX = privatedict.get('nominalWidthX', 0)
        defaultWidthX = privatedict.get('defaultWidthX', 0)

        # the following decomposes the composite
        accentglyph = kwArgs.get('accent',dict())
        baseglyph = kwArgs.get('base',dict())
        newglyph= baseglyph.__deepcopy__()
        mark = accentglyph.__deepcopy__().transformed(self.accentOffset) # X/Y offset
        newglyph.contours += mark.contours
        newglyph.bounds = newglyph.bounds.recalculated()

        if(defaultWidthX != newglyph.cffAdvance):
            pack_t2_number(newglyph.cffAdvance-nominalWidthX, w) # glyph width


        if(newglyph.contours!=None):
            curX = 0
            curY = 0
            # self.contours is just a sequence of contours; we can iterate directly
            # over each item rather than indexing.
            for cntr in self.contours:
                # start of each contour (point index 0) is established by rmoveto
                if cntr[0].onCurve:
                    pack_t2_number(cntr[0].x - curX, w) # dx for rmoveto
                    pack_t2_number(cntr[0].y - curY, w) # dy for rmoveto
                    w.add("B", 21) # rmoveto
                else:
                    # raising an error is a better way of conveying problems
                    raise ValueError("First point of contour cannot be off-curve.")

                n = 1
                while n < len(cntr):
                    ptPrev = cntr[n-1]
                    ptCurr = cntr[n]
                    if ptCurr.onCurve:
                        if ptPrev.onCurve:
                            if(ptCurr.y == ptPrev.y):
                                pack_t2_number((ptCurr.x - ptPrev.x), w)
                                w.add("B", 6) #hlineto
                            elif(ptCurr.x == ptPrev.x):
                                pack_t2_number((ptCurr.y - ptPrev.y), w)
                                w.add("B", 7) #vlineto
                            else:
                                pack_t2_number((ptCurr.x - ptPrev.x), w)
                                pack_t2_number((ptCurr.y - ptPrev.y), w)
                                w.add("B", 5) #rlineto
                        else:
                            raise ValueError("Unexpected off-curve point #%d." % (n-1,))

                        n +=1
                        curX = ptCurr.x
                        curY = ptCurr.y

                    else:
                        if n < len(cntr) - 2:
                            ptNext = cntr[n+1]
                            ptNextNext = cntr[n+2]
                        elif n == len(cntr) - 2:
                            ptNext = cntr[n+1]
                            ptNextNext = cntr[0]
                        elif n == len(cntr) - 1:
                            ptNext = cntr[0]
                            ptNextNext = cntr[1]
                            #print("Error: Should not happen")
                            raise ValueError("Unexpected condition point #%d." % (n,))

                        if(ptPrev.onCurve and ~ptNext.onCurve and ptNextNext.onCurve):
                            pack_t2_number((ptCurr.x - ptPrev.x), w)
                            pack_t2_number((ptCurr.y - ptPrev.y), w)
                            pack_t2_number((ptNext.x - ptCurr.x), w)
                            pack_t2_number((ptNext.y - ptCurr.y), w)
                            pack_t2_number((ptNextNext.x - ptNext.x), w)
                            pack_t2_number((ptNextNext.y - ptNext.y), w)
                            w.add("B", 8) #rrcurveto
                        else:
                            #print("Error: Should not happen")
                            raise ValueError("Unexpected condition point #%d." % (n,))

                        n += 3
                        curX = ptNextNext.x
                        curY = ptNextNext.y

            w.add("B", 14) # endchar


    @classmethod
    def fromcffdata(cls, components, offset, advance, **kwArgs):
        """
        Constructs and returns a CFFCompositeGlyph from the specified component
        list and offset pair.

        >>> c = CFFCompositeGlyph.fromcffdata( [5,10], [100,100], 500 )

        NOTE: In the following, the bounds are incomplete; see the note in the
        source code.

        >>> c.pprint(namer = namer.testingNamer())
        Accent: xyz11
        Accent Offset: Shift X by 100.0 and Y by 100.0
        Base: xyz6
        Bounds:
          Minimum X: 0
          Minimum Y: 0
          Maximum X: 0
          Maximum Y: 0
        CFF Advance: 500
        """

        b = components[0]
        a = components[1]
        aOff = matrix.Matrix( ([1,0,0], [0,1,0], [offset[0], offset[1], 1]) )

        # *** NOTE *** This needs to be updated to calculate or otherwise
        # obtain a correct bounding box for the resulting composite glyph.
        # Unlike TrueType, CFF does not store a BBX for composites; it must be
        # calculated from the components.
        #
        # With the current setup, we don't have access to the component glyph
        # data. For now, we just create an empty rectangle.

        glyphbounds = rectangle.Rectangle()

#        aTrans = a.transformed(aOff)
#        B = rectangle.Rectangle
#         glyphbounds = functools.reduce(
#           B.unioned,
#           (b, aTrans),
#           B())

        return cls(
          baseGlyph=b,
          accentGlyph=a,
          accentOffset=aOff,
          bounds=glyphbounds,
          cffAdvance=advance,
        )


    @classmethod
    def fromvalidatedcffdata(cls, components, offset, advance, **kwArgs):
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
            logger = logging.getLogger().getChild('cffcompositeglyph')
        else:
            logger = logger.getChild('cffcompositeglyph')

        b = components[0]
        a = components[1]
        aOff = matrix.Matrix( ([1,0,0], [0,1,0], [offset[0], offset[1], 1]) )

        # *** NOTE *** This needs to be updated to calculate or otherwise
        # obtain a correct bounding box for the resulting composite glyph.
        # Unlike TrueType, CFF does not store a BBX for composites; it must be
        # calculated from the components.
        #
        # With the current setup, we don't have access to the component glyph
        # data. For now, we just create an empty rectangle.

        glyphbounds = rectangle.Rectangle()

        return cls(
          baseGlyph=b,
          accentGlyph=a,
          accentOffset=aOff,
          bounds=glyphbounds,
          cffAdvance=advance,
        )


    def pointCount(self, **kwArgs):
        """
        Returns the number of points in the (unnormalized) glyph. The following
        keyword arguments are supported:
        
            editor      An Editor-class object which is used to get the glyphs
                        representing the components. This is required.
            
        This call may raise one of these exceptions:
        
            BadEditorOrCFF
        """
        
        editor = kwArgs.get('editor')
        if editor is None:
            raise BadEditorOrCFF("No Editor")
        if editor.reallyHas(b'CFF '):
            glyfTable = editor['CFF ']
        else:
            raise BadEditorOrCFF("Missing or damaged CFF table")

        sum = self.baseGlyph.pointCount() + self.accentGlyph.pointCount()
        
        return sum

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    from fontio3.CFF import cffbounds

    _testingValues = [
        CFFCompositeGlyph(
            cffAdvance=667,
            accentOffset=matrix.Matrix(([1, 0, 0], [0, 1, 0], [177, 170, 1])),
            bounds=cffbounds.CFFBounds(xMin=0, yMin=0, yMax=0, xMax=0),
            baseGlyph=38,
            accentGlyph=124)]

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

