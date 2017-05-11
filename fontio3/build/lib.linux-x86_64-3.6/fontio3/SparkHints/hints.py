#
# hints.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Spark-style hints.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

from fontio3.SparkHints import (
  hint_deltag_1,
  hint_deltag_2,
  hint_deltag_3,
  hint_deltak_1,
  hint_deltak_2,
  hint_deltak_3,
  hint_deltal_1,
  hint_deltal_2,
  hint_deltal_3,
  hint_deltap_1,
  hint_deltap_2,
  hint_deltap_3,
  hint_deltas_1,
  hint_deltas_2,
  hint_deltas_3,
  hint_rtgah,
  hint_sdb,
  hint_sds,
  hint_strokedelta_1,
  hint_strokedelta_2,
  hint_strokedelta_3,
  hint_svtca_x,
  hint_svtca_y)

# -----------------------------------------------------------------------------

#
# Constants
#

MAKER_INFO = {
  0x00: hint_svtca_y.Hint_SVTCA_Y.fromwalker,
  0x01: hint_svtca_x.Hint_SVTCA_X.fromwalker,
  0x5D: hint_deltap_1.Hint_DELTAP_1.fromwalker,
  0x5E: hint_sdb.Hint_SDB.fromwalker,
  0x5F: hint_sds.Hint_SDS.fromwalker,
  0x71: hint_deltap_2.Hint_DELTAP_2.fromwalker,
  0x72: hint_deltap_3.Hint_DELTAP_3.fromwalker,
  0x7F: hint_rtgah.Hint_RTGAH.fromwalker,
  0xA1: hint_deltag_1.Hint_DELTAG_1.fromwalker,
  0xA2: hint_strokedelta_1.Hint_STROKEDELTA_1.fromwalker,
  0xA3: hint_strokedelta_2.Hint_STROKEDELTA_2.fromwalker,
  0xA4: hint_strokedelta_3.Hint_STROKEDELTA_3.fromwalker,
  0xA5: hint_deltag_2.Hint_DELTAG_2.fromwalker,
  0xA6: hint_deltag_3.Hint_DELTAG_3.fromwalker,
  0xA7: hint_deltak_1.Hint_DELTAK_1.fromwalker,
  0xA8: hint_deltak_2.Hint_DELTAK_2.fromwalker,
  0xA9: hint_deltak_3.Hint_DELTAK_3.fromwalker,
  0xAA: hint_deltal_1.Hint_DELTAL_1.fromwalker,
  0xAB: hint_deltal_2.Hint_DELTAL_2.fromwalker,
  0xAC: hint_deltal_3.Hint_DELTAL_3.fromwalker,
  0xAD: hint_deltas_1.Hint_DELTAS_1.fromwalker,
  0xAE: hint_deltas_2.Hint_DELTAS_2.fromwalker,
  0xAF: hint_deltas_3.Hint_DELTAS_3.fromwalker}

VALIDATED_MAKER_INFO = {
  0x00: hint_svtca_y.Hint_SVTCA_Y.fromvalidatedwalker,
  0x01: hint_svtca_x.Hint_SVTCA_X.fromvalidatedwalker,
  0x5D: hint_deltap_1.Hint_DELTAP_1.fromvalidatedwalker,
  0x5E: hint_sdb.Hint_SDB.fromvalidatedwalker,
  0x5F: hint_sds.Hint_SDS.fromvalidatedwalker,
  0x71: hint_deltap_2.Hint_DELTAP_2.fromvalidatedwalker,
  0x72: hint_deltap_3.Hint_DELTAP_3.fromvalidatedwalker,
  0x7F: hint_rtgah.Hint_RTGAH.fromvalidatedwalker,
  0xA1: hint_deltag_1.Hint_DELTAG_1.fromvalidatedwalker,
  0xA2: hint_strokedelta_1.Hint_STROKEDELTA_1.fromvalidatedwalker,
  0xA3: hint_strokedelta_2.Hint_STROKEDELTA_2.fromvalidatedwalker,
  0xA4: hint_strokedelta_3.Hint_STROKEDELTA_3.fromvalidatedwalker,
  0xA5: hint_deltag_2.Hint_DELTAG_2.fromvalidatedwalker,
  0xA6: hint_deltag_3.Hint_DELTAG_3.fromvalidatedwalker,
  0xA7: hint_deltak_1.Hint_DELTAK_1.fromvalidatedwalker,
  0xA8: hint_deltak_2.Hint_DELTAK_2.fromvalidatedwalker,
  0xA9: hint_deltak_3.Hint_DELTAK_3.fromvalidatedwalker,
  0xAA: hint_deltal_1.Hint_DELTAL_1.fromvalidatedwalker,
  0xAB: hint_deltal_2.Hint_DELTAL_2.fromvalidatedwalker,
  0xAC: hint_deltal_3.Hint_DELTAL_3.fromvalidatedwalker,
  0xAD: hint_deltas_1.Hint_DELTAS_1.fromvalidatedwalker,
  0xAE: hint_deltas_2.Hint_DELTAS_2.fromvalidatedwalker,
  0xAF: hint_deltas_3.Hint_DELTAS_3.fromvalidatedwalker}

# -----------------------------------------------------------------------------

#
# Functions
#

def _pprint(p, seq, **k):
    for obj in seq:
        p(str(obj))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Hints(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    """
    
    seqSpec = dict(
        item_followsprotocol = True,
        seq_pprintfunc = _pprint)
    
    attrSpec = dict(
        isGray = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: True)),
        
        isOldStyle = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: False)))
    
    #
    # Methods
    #
    
    def analyze(self):
        """
        >>> bs = utilities.fromhex(
        ...   '7F F9 00 41 A2 00 0E 01 '
        ...   '5A 00 A2 00 0E 01 59 7F '
        ...   '0B 01 5D 01 00 07 5B 5D '
        ...   '01 00 20 5A 5D 01 00 21 '
        ...   '5A 00 5D 01 00 20 58 5D '
        ...   '01 00 21 58 01 AA 00 13 '
        ...   '01 59 5D 01 00 08 5A 5D '
        ...   '01 00 0A 5A 5D 01 00 09 '
        ...   '59')
        >>> h = Hints.frombytes(bs)
        >>> h.pprint()
        STROKEDELTA: Point 14 3/8@14
        SVTCA[y]
        STROKEDELTA: Point 14 1/4@14
        RTGAH
        SVTCA[x]
        DELTAP: Point 7 1/2@14
        DELTAP: Point 32 3/8@14
        DELTAP: Point 33 3/8@14
        SVTCA[y]
        DELTAP: Point 32 1/8@14
        DELTAP: Point 33 1/8@14
        SVTCA[x]
        DELTAL: Point 19 1/4@14
        DELTAP: Point 8 3/8@14
        DELTAP: Point 10 3/8@14
        DELTAP: Point 9 1/4@14
        isGray: True
        isOldStyle: True
        
        >>> dPre, dPost = h.analyze()
        
        The following are commented out for now, until I resolve the use of
        pprint.pprint() and varying iteration order in doctest running...
        
        ### pprint.pprint(dPre)
        {False: {14: {0.375: {('STROKEDELTA', 14)}}},
         True: {14: {0.25: {('STROKEDELTA', 14)}}}}
        
        ### pprint.pprint(dPost)
        {False: {14: {0.25: {('DELTAL', 19), ('DELTAP', 9)},
                      0.375: {('DELTAP', 8),
                              ('DELTAP', 10),
                              ('DELTAP', 32),
                              ('DELTAP', 33)},
                      0.5: {('DELTAP', 7)}}},
         True: {14: {0.125: {('DELTAP', 33), ('DELTAP', 32)}}}}
        """
        
        inY = False
        deltaBase = 9
        deltaShift = 3
        dPre = {}  # pre-RTGAH
        dPost = {}  # post-RTGAH
        
        if 'RTGAH' in {obj.kindString for obj in self}:
            d = dPre
        
        else:
            d = dPost
            dPre = None  # allows us to distinguish RTGAH-first streams
        
        for obj in self:
            if obj.kindString == 'SVTCA_Y':
                inY = True
            
            elif obj.kindString == 'SVTCA_X':
                inY = False
            
            elif obj.kindString == 'SDS':
                deltaShift = obj.shift
            
            elif obj.kindString == 'SDB':
                deltaBase = obj.base
            
            elif obj.kindString == 'RTGAH':
                d = dPost
            
            else:
                for single in obj.decompose():
                    part = next(iter(single))
                    d1 = d.setdefault(inY, {})
                    d2 = d1.setdefault(part.ppem, {})
                    s = d2.setdefault(part.shift, set())
                    s.add((single.kindString, part.pointIndex))
        
        return dPre, dPost
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Hints object to the specified
        LinkedWriter.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self.isOldStyle:
            w.add("BB", 0x7F, (249 if self.isGray else 248))
        else:
            w.add("3B", 0xB0, (249 if self.isGray else 248), 0x7F)
        
        stakeFinal = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, stakeFinal)
        d = {'deltaBase': 9, 'deltaShift': 3}
        
        for opObj in self:
            if opObj.kindString == 'SDB':
                d['deltaBase'] = opObj.base
            elif opObj.kindString == 'SDS':
                d['deltaShift'] = opObj.shift
            
            opObj.buildBinary(w, **d)  # don't need to stake each opcode
        
        w.stakeCurrentWithValue(stakeFinal)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        """
        
        logger = kwArgs.pop('logger', None)
        starts = kwArgs.pop('startOffsets', [])
        starts[:] = []
        startLength = int(w.length())
        
        if logger is None:
            logger = logging.getLogger().getChild('SparkHints')
        else:
            logger = logger.getChild('SparkHints')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        op, kind = w.unpack("BB")
        
        if (op == 0xB0) and (kind == 11):
            # special case; RTGAH-only hints
            isGray = False
            isOldStyle = False  # ...in the absence of any other indication
            obj = hint_rtgah.Hint_RTGAH()
            v = [obj]
            starts.append(0)
        
        elif (op not in {0x7F, 0xB0}) or (kind not in {248, 249}):
            logger.error((
              'Vxxxx',
              (),
              "Unknown start for Spark hints"))
            
            return None
        
        else:
            if op == 0xB0:
                if w.length() < 1:
                    logger.error(('V0004', (), "Insufficient bytes"))
                    return None
                
                w.skip(1)  # skip over the actual AA
                isOldStyle = False
            
            else:
                isOldStyle = True
            
            if w.length() < 2:
                logger.error(('V0004', (), "Insufficient bytes"))
                return None
            
            length = w.unpack("H")
            isGray = (kind == 249)
            v = []
            d = {'deltaBase': 9, 'deltaShift': 3, 'logger': logger}
        
            while w.stillGoing():
            
                # Note that we don't actually need a length check on w here, since
                # we just passed the w.stillGoing() test.
            
                peek = w.unpack("B", advance=False)
            
                if peek not in VALIDATED_MAKER_INFO:
                    logger.error((
                      'Vxxxx',
                      (peek,),
                      "Unknown Spark opcode 0x%02X encountered."))
                
                    return None
            
                starts.append(startLength - int(w.length()))
                obj = VALIDATED_MAKER_INFO[peek](w, **d)
            
                if obj is None:
                    return None
            
                v.append(obj)
            
                if peek == 0x5E:  # SDB
                    d['deltaBase'] = obj.base
            
                elif peek == 0x5F:  # SDS
                    d['deltaShift'] = obj.shift
        
        starts.append(startLength - int(w.length()))
        return cls(v, isGray=isGray, isOldStyle=isOldStyle)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        op, kind = w.unpack("BB")
        d = {'deltaBase': 9, 'deltaShift': 3}
        starts = kwArgs.pop('startOffsets', [])
        starts[:] = []
        startLength = int(w.length())
        
        if (op == 0xB0) and (kind == 11):
            # special case; RTGAH-only hints
            isGray = False
            isOldStyle = False  # ...in the absence of any other indication
            obj = hint_rtgah.Hint_RTGAH()
            v = [obj]
            starts.append(0)
        
        else:
            assert (op in {0x7F, 0xB0}) and (kind in {248, 249})
            
            if op == 0xB0:
                w.skip(1)  # skip over the actual AA
                isOldStyle = False
            
            else:
                isOldStyle = True
            
            length = w.unpack("H")
            isGray = (kind == 249)
            v = []
        
            while w.stillGoing():
                peek = w.unpack("B", advance=False)
                assert peek in MAKER_INFO
                starts.append(startLength - int(w.length()))
                obj = MAKER_INFO[peek](w, **d)
                v.append(obj)
            
                if peek == 0x5E:  # SDB
                    d['deltaBase'] = obj.base
            
                elif peek == 0x5F:  # SDS
                    d['deltaShift'] = obj.shift
        
        starts.append(startLength - int(w.length()))
        return cls(v, isGray=isGray, isOldStyle=isOldStyle)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import pprint
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

