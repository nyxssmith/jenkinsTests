#
# ttcontourgroups.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for logically connected groups of TTContour objects, where the
connection represents interior opposite-chirality groups. These objects can be
used to construct hierarchical collections of contours representing high-level
parts of a glyph.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.glyf import ttcontour, ttcontourgroup

# -----------------------------------------------------------------------------

#
# Private functions
#

def _depthMap(possParents, key, currDepth=1):
    r = {}
    
    for childIndex in possParents.get(key, set()):
        if childIndex in possParents:
            r[childIndex] = currDepth
            dSub = _depthMap(possParents, childIndex, currDepth+1)
            
            for i, dep in dSub.items():
                r[i] = max(dep, r.setdefault(i, 0))
        
        else:
            r[childIndex] = max(currDepth, r.setdefault(childIndex, 0))
    
    return r

def _makeRecursively(
  topIndex,
  thisLevel,
  possParents,
  depthMap,
  ttcObj,
  dFilled):
    
    if topIndex in dFilled:
        return
    
    v = []
    
    for childIndex in possParents.get(topIndex, set()):
        if childIndex in possParents:
            _makeRecursively(
              childIndex,
              thisLevel + 1,
              possParents,
              depthMap,
              ttcObj,
              dFilled)
            
            v.append(dFilled[childIndex])
        
        elif depthMap[childIndex] == thisLevel:
            v.append(ttcObj[childIndex])
    
    dFilled[topIndex] = ttcontourgroup.TTContourGroup(
      ttcObj[topIndex],
      children = TTContourGroups(v))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TTContourGroups(list, metaclass=seqmeta.FontDataMetaclass):
    """
    A TTContourGroups object is a list of TTContour and TTContourGroup objects.
    A single glyph can be expressed as one of these objects; note that the
    children of a single TTContourGroup may also be an object of this type!
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True)
    
    #
    # Methods
    #
    
    @classmethod
    def fromttcontours(cls, ttcObj, **kwArgs):
        """
        Given a flat list of TTContour objects (which is, after all, just what
        a TTContours object is), this method returns a TTContourGroups
        object for the top-level contours.
        
        >>> v = TTContourGroups.fromttcontours(_makeTestContours())
        >>> for obj in v: obj.pprint()
        Point 0: (100, 100), on-curve
        Point 1: (100, 1100), on-curve
        Point 2: (1900, 1100), on-curve
        Point 3: (1900, 100), on-curve
        children:
          0:
            Point 0: (200, 200), on-curve
            Point 1: (1400, 200), on-curve
            Point 2: (1400, 1000), on-curve
            Point 3: (200, 1000), on-curve
            children:
              0:
                Point 0: (300, 300), on-curve
                Point 1: (300, 900), on-curve
                Point 2: (1000, 900), on-curve
                Point 3: (1000, 300), on-curve
                children:
                  0:
                    Point 0: (400, 400), on-curve
                    Point 1: (500, 400), on-curve
                    Point 2: (500, 500), on-curve
                    Point 3: (400, 500), on-curve
              1:
                Point 0: (1100, 300), on-curve
                Point 1: (1100, 900), on-curve
                Point 2: (1300, 900), on-curve
                Point 3: (1300, 300), on-curve
          1:
            Point 0: (1500, 200), on-curve
            Point 1: (1800, 200), on-curve
            Point 2: (1800, 1000), on-curve
            Point 3: (1500, 1000), on-curve
            children:
              0:
                Point 0: (1550, 700), on-curve
                Point 1: (1550, 900), on-curve
                Point 2: (1650, 900), on-curve
                Point 3: (1650, 700), on-curve
              1:
                Point 0: (1650, 300), on-curve
                Point 1: (1650, 500), on-curve
                Point 2: (1750, 500), on-curve
                Point 3: (1750, 300), on-curve
        Point 0: (2000, 500), on-curve
        Point 1: (2000, 600), on-curve
        Point 2: (2100, 600), on-curve
        Point 3: (2100, 500), on-curve
        """
        
        possParents = {}  # index of parent -> set of poss. children
        
        for tryParentIndex, tryParent in enumerate(ttcObj):
            s = set()
            
            for tryChildIndex, tryChild in enumerate(ttcObj):
                if tryParentIndex == tryChildIndex:
                    continue
                
                if tryParentIndex in possParents.get(tryChildIndex, set()):
                    continue
                
                if tryParent.containsContour(tryChild):
                    s.add(tryChildIndex)
            
            if s:
                possParents[tryParentIndex] = s
        
        nonTops = {i for s in possParents.values() for i in s}
        tops = set(range(len(ttcObj))) - nonTops
        r = cls()
        
        for topIndex in tops:
            dm = _depthMap(possParents, topIndex)
            d = {}
            
            _makeRecursively(
              topIndex,
              1,
              possParents,
              dm,
              ttcObj,
              d)
            
            r.append(d[topIndex])
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _makeTestContours():
        from fontio3.glyf import ttcontour, ttcontours, ttpoint
        
        P = ttpoint.TTPoint
        C = ttcontour.TTContour
        
        return ttcontours.TTContours([
          C([P(100, 100), P(100, 1100), P(1900, 1100), P(1900, 100)]),      # 0
          C([P(200, 200), P(1400, 200), P(1400, 1000), P(200, 1000)]),      # 1
          C([P(1500, 200), P(1800, 200), P(1800, 1000), P(1500, 1000)]),    # 2
          C([P(300, 300), P(300, 900), P(1000, 900), P(1000, 300)]),        # 3
          C([P(1100, 300), P(1100, 900), P(1300, 900), P(1300, 300)]),      # 4
          C([P(400, 400), P(500, 400), P(500, 500), P(400, 500)]),          # 5
          C([P(1550, 700), P(1550, 900), P(1650, 900), P(1650, 700)]),      # 6
          C([P(1650, 300), P(1650, 500), P(1750, 500), P(1750, 300)]),      # 7
          C([P(2000, 500), P(2000, 600), P(2100, 600), P(2100, 500)])])     # 8

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
