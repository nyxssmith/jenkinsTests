#
# gposconverter_nonmark.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for non-mark conversion from effects() output to 'kerx' subtables.
"""

# System imports
import collections

# Other imports
from fontio3.kerx import (
  classtable,
  entry,
  valuetuple)

# -----------------------------------------------------------------------------

#
# Classes
#

class Converter:
    """
    """
    
    #
    # Methods
    #
    
    def __init__(self, gVec, xVec, yVec, **kwArgs):
        """
        Initializes the Converter object with the specified vectors of glyphs,
        x-deltas, and y-deltas. Note that because of the way the various
        effects() methods work, the gVec's length might not match the lengths
        of xVec and yVec (although these two latter will always be the same
        length).
        
        Keyword arguments include:
        
            horizontal      Default True; indicates whether the line being
                            laid out is fundamentally horizontal. This affects
                            how "cross-stream" is interpreted.
            
            namer           A Namer object for glyphs in gVec. If none is
                            provided, str() will be used on the glyph indices.
        """
        
        self.gVec = tuple(tuple(abs(g) for g in t) for t in gVec)
        self.xVec = tuple(xVec)
        self.yVec = tuple(yVec)
        self.horizontal = kwArgs.get('horizontal', True)
        namer = kwArgs.get('namer', None)
        self.nmbf = (str if namer is None else namer.bestNameForGlyphIndex)
    
    @staticmethod
    def _actionCellGenerator(d):
        """
        """
        
        for stateName, row in d.items():
            for className, cell in row.items():
                if cell.values is not None:
                    yield (stateName, className)
    
    @staticmethod
    def _makeStateToClasses(d):
        """
        """
        
        r = {}
        
        for stateName, row in d.items():
            if stateName == 'Start of text':
                r[stateName] = ()
            else:
                r[stateName] = tuple(stateName[4:].split('_'))
        
        return r
    
    def _stateNameFromGlyphs(self, gv):
        """
        Given a sequence of glyphs, returns a state name.
        
        >>> obj = Converter((), (), ())
        >>> print(obj._stateNameFromGlyphs(()))
        Start of text
        >>> print(obj._stateNameFromGlyphs((24,)))
        Saw 24
        >>> print(obj._stateNameFromGlyphs((3, 9, 15)))
        Saw 3_9_15
        
        >>> obj.nmbf = (lambda n: hex(n)[2:])
        >>> print(obj._stateNameFromGlyphs(()))
        Start of text
        >>> print(obj._stateNameFromGlyphs((24,)))
        Saw 18
        >>> print(obj._stateNameFromGlyphs((3, 9, 15)))
        Saw 3_9_f
        """
        
        if len(gv) > 1:
            return 'Saw ' + '_'.join(self.nmbf(g) for g in gv)
        elif gv:
            return 'Saw %s' % (self.nmbf(gv[0]),)
        
        return 'Start of text'
    
    def combine(self, d, ct):
        """
        """
        
        stateToClasses = self._makeStateToClasses(d)
        classesToState = {v: k for k, v in stateToClasses.items()}
        pool = collections.defaultdict(set)
        
        for stateName, className in self._actionCellGenerator(d):
            cell = d[stateName][className]
            immut = cell.asImmutable()
            pool[immut].add((stateName, className))
        
        for shareSet in pool.values():
            if len(shareSet) < 2:
                continue
            
            keys = []
            
            for stateName, className in shareSet:
                if stateName == 'Start of text':
                    keys.append([className])
                    continue
                
                keys.append(stateToClasses[stateName] + (className,))
         
            # We can only consolidate glyphs into the same classes if several
            # conditions are met:
            #
            # 1. All combinations are present. Consider a case where we have 4
            #    keys referring to the same Entry: (9, 31, 16), (9, 38, 16),
            #    (9, 31, 20), and (15, 38, 20). At first blush you might think
            #    some sharing was possible here, but consider (15, 38, 16) --
            #    if you consolidated 16 and 20, this key would get unwanted
            #    kerning.
            #
            # 2. No glyphs other than the final glyph can shift.
            #
            # 3. There are no conflicts between sets of potentially shared
            #    glyphs and other, unrelated entries in d.
            #
            # Assuming these conditions all hold, then shared classes are
            # allowed.
            
            allLens = {len(v) for v in keys}
            
            if len(allLens) > 1:
                continue  # don't try to optimize variable-length key sets
            
            allLen = allLens.pop()
            keySets = [{v[i] for v in keys} for i in range(allLen)]
            
            for t in itertools.product(*keySets):
                sn = 'Saw %s' % ('_'.join(t[:-1]),)
                
                if (sn not in d) or (t[-1] not in d[sn]):
                    missing = True
                    break
            
            else:
                missing = False
            
            if missing:
                continue
    
    def convert(self):
        """
        This is the top-level method clients should call. It converts the
        shifts to a list of 'kerx' subtable objects, which is returned from
        this method.
        """
        
        rv = []
        gVec_x, nVec_x, gVec_y, nVec_y = [], [], [], []
        
        for gv, xv, yv in zip(self.gVec, self.xVec, self.yVec):
            if any(xv):
                gVec_x.append(gv)
                nVec_x.append(xv)
            
            if any(yv):
                gVec_y.append(gv)
                nVec_y.append(yv)
        
        if gVec_x:
            rv.extend(
              self.singlePolarization(gVec_x, nVec_x, (not self.horizontal)))
        
        if gVec_y:
            rv.extend(
              self.singlePolarization(gVec_y, nVec_y, self.horizontal))
        
        return rv or None
    
    def initState(self, gVec, nVec, deferreds):
        """
        Create the initial state array precursor dict and the initial class table.
    
        >>> gVec = ((25, 60, 4), (25, 75, 4))
        >>> nVec = ((0, 0, 130), (0, 0, 130))
        >>> obj = Converter((), (), ())  # the arguments are ignored
        >>> defds = []
        >>> d, ct = obj.initState(gVec, nVec, defds)
        >>> ct.pprint()
        4: 4
        25: 25
        60: 60
        75: 75
        >>> for stateName in sorted(d):
        ...     row = d[stateName]
        ...     for className in sorted(row):
        ...         print((stateName, className), row[className])
        ('Saw 25', '60') Name of next state = 'Saw 25_60', Values = None
        ('Saw 25', '75') Name of next state = 'Saw 25_75', Values = None
        ('Saw 25_60', '4') Name of next state = 'Start of text', Push this glyph = True, Values = (130,)
        ('Saw 25_75', '4') Name of next state = 'Start of text', Push this glyph = True, Values = (130,)
        ('Start of text', '25') Name of next state = 'Saw 25', Values = None
        >>> print(defds)
        []
        """
    
        E = entry.Entry
        VT = valuetuple.ValueTuple
        ct = self.makeInitialClassTable(gVec)
        d = {}
        
        for gv, nv in zip(gVec, nVec):
            currState = 'Start of text'
            
            for i, (g, n) in enumerate(zip(gv, nv)):
                gs = self.nmbf(g)
                thisRow = d.setdefault(currState, {})
                noAdv = False
                piece = (() if i == (len(gv) - 1) else gv[:i+1])
                nextState = self._stateNameFromGlyphs(piece)
                
                if n:
                    push = True
                    vt = VT([n])
                
                else:
                    push = False
                    vt = None
                
                e = E(
                  newState = nextState,
                  noAdvance = noAdv,
                  push = push,
                  values = vt)
                
                if gs not in thisRow:
                    thisRow[gs] = e
                
                elif thisRow[gs] != e:
                    deferreds.append((gv, nv))
                    break
                
                currState = nextState
        
        return d, ct
    
    def makeInitialClassTable(self, gVec):
        """
        Creates and returns a ClassTable from the specified vector of tuples.
        """
        
        ct = classtable.ClassTable()
        
        for t in gVec:
            for g in t:
                if g is not None and g not in ct:
                    ct[g] = self.nmbf(g)
        
        return ct
    
    def singlePolarization(self, gVec, nVec, crossStream):
        """
        Returns a list of converted 'kerx' subtables for the specified
        cross-stream state.
        """
        
        rv = []
        deferreds = []
        
        while True:
            d, ct = self.initState(gVec, nVec, deferreds)
            self.combine(d, ct)
            
            if deferreds:
                gVec = tuple(t[0] for t in deferreds)
                nVec = tuple(t[1] for t in deferreds)
                deferreds = []
            
            else:
                break
        
        return rv

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
    if __debug__:
        _test()
