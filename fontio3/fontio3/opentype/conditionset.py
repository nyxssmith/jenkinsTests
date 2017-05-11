#
# conditionset.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ConditionSet Tables as found in GSUB v1.1 (OpenType 1.8) or later.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import setmeta
from fontio3.opentype import condition
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ConditionSet(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing ConditionSet Tables. These are [frozen]sets of Conditions
    intended to be matched (boolean AND) as part of a FeatureVariationsRecord.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True)
    
    attrSpec = dict(
        sequence = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Sequence order (lower evaluated first)",
            attr_validatefunc_partial = valassist.isNumber))
    
    format = 1

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureVariations Table object to the
        specified LinkedWriter.
        
        >>> b = _testingValues[0].binaryString(axisOrder=('wght',))
        >>> utilities.hexdump(b)
               0 | 0000                                     |..              |

        >>> b = _testingValues[1].binaryString(axisOrder=('wdth', 'wght',))
        >>> utilities.hexdump(b)
               0 | 0001 0000 0006 0001  0001 0666 4000      |...........f@.  |

        >>> b = _testingValues[2].binaryString(axisOrder=('wdth', 'wght',))
        >>> utilities.hexdump(b)
               0 | 0002 0000 000A 0000  0012 0001 0000 C000 |................|
              10 | 4000 0001 0001 0010  4000                |@.......@.      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))

        stakesDict = dict()
        for i in range(len(self)):
            stakesDict[i] = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, stakesDict[i])

        for i, cond in enumerate(sorted(self)):
            cond.buildBinary(w, stakeValue=stakesDict[i], **kwArgs)


    def match(self, coords, **kwArgs):
        """
        Determine whether the supplied coords satisfy all Conditions of the
        ConditionSet.
        
        The following keyword arguments are used:
        
            axisOrder   A sequence of axis tags, i.e. fvar.axisOrder. The
                        supplied coords must match this ordering.

        >>> ao = ('wght', 'wdth')
        >>> testCoords = (0.5, 0.5)
        >>> _testingValues[2].match(testCoords, axisOrder=ao)
        True
        
        >>> testCoords = (-1, -1)
        >>> _testingValues[2].match(testCoords, axisOrder=ao)
        False

        Invalid axis index (tag); should be ignored
        >>> testCoords = (0.1111,)
        >>> _testingValues[1].match(testCoords, axisOrder=('wdth',)) 
        True
        """
        
        ao = kwArgs['axisOrder']
        
        for cond in self:
            if cond.axisTag in ao:
                ai = ao.index(cond.axisTag)
                if not cond.filterMin <= coords[ai] <= cond.filterMax:
                    return False

        return True


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ConditionSet object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = ("0001 00000006 0001 0000 0123 5678")
        >>> b = utilities.fromhex(s)
        >>> fvb = ConditionSet.fromvalidatedbytes
        >>> obj = fvb(b, sequence=0, logger=logger, axisOrder=('wght',))
        test.conditionset - DEBUG - Walker has 14 remaining bytes.
        test.conditionset - INFO - ConditionCount is 1
        test.condition - DEBUG - Walker has 8 remaining bytes.
        test.condition - INFO - AxisTag 'wght'
        test.condition - INFO - Min: 0.017761, Max: 1.351074
        
        >>> s = ("0002 0000000A 00000012"
        ...      "0001 0001 0010 4000"
        ...      "0001 0000 C000 4000")
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, sequence=0, logger=logger, axisOrder=('wght', 'wdth'))
        test.conditionset - DEBUG - Walker has 26 remaining bytes.
        test.conditionset - INFO - ConditionCount is 2
        test.condition - DEBUG - Walker has 16 remaining bytes.
        test.condition - INFO - AxisTag 'wdth'
        test.condition - INFO - Min: 0.000977, Max: 1.000000
        test.condition - DEBUG - Walker has 8 remaining bytes.
        test.condition - INFO - AxisTag 'wght'
        test.condition - INFO - Min: -1.000000, Max: 1.000000
        
        >>> obj = fvb(b[0:1], sequence=0, logger=logger, axisOrder=('wght',))
        test.conditionset - DEBUG - Walker has 1 remaining bytes.
        test.conditionset - ERROR - Insufficient bytes.
        """

        logger = kwArgs.get('logger', None)
        sequence = kwArgs.pop('sequence')

        if logger is None:
            logger = logging.getLogger()

        logger = logger.getChild("conditionset")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        
        logger.info((
          'Vxxxx',
          (count,),
          "ConditionCount is %d"))
        
        condOffsets = w.group("L", count)
        fvw = condition.Condition.fromvalidatedwalker
        v = list()

        for o in condOffsets:
            wSub = w.subWalker(o)
            v.append(fvw(wSub, **kwArgs))

        return cls(v, sequence=sequence)

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureVariations object from the specified
        walker.

        >>> s = ("0001 00000006 0001 0000 0123 5678")
        >>> b = utilities.fromhex(s)
        >>> fb = ConditionSet.frombytes
        >>> obj = fb(b, sequence=0, axisOrder=('wght',))
        >>> sorted(obj)[0].axisTag
        'wght'
        """

        sequence = kwArgs.pop('sequence')

        count = w.unpack("H")
        condOffsets = w.group("L", count)
        fw = condition.Condition.fromwalker
        v = list()

        for o in condOffsets:
            wSub = w.subWalker(o)
            v.append(fw(wSub, **kwArgs))
            
        return cls(v, sequence=sequence)


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import living_variations
    
    ctv = condition._testingValues
    
    _testingValues = (
        ConditionSet(),
        ConditionSet([condition.Condition(axisTag='wght', filterMin=0.1, filterMax=1.0)]),
        ConditionSet([ctv[1], ctv[2]]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
