#
# gasp.py
#
# Copyright © 2009-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the 'gasp' table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.gasp import behavior_v0, behavior_v1

# -----------------------------------------------------------------------------

#
# Classes
#

class GaspIncompatibleMerge(ValueError):
    """
    This exception can be raised when a Gasp object is merged with another, if
    one or more of the Behaviors are not the same.
    """
    
    pass

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class Gasp(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'gasp' tables. These are dicts mapping PPEM
    values (integers) to Behavior objects.
    
    >>> _testingValues[1].pprint()
    Up to 6 PPEM:
      Do gray
    Up to 19 PPEM:
      Grid-fit
    Version: 1
    Default behavior:
      Grid-fit
      Do gray
    
    # JH: disabled this test for now as there seem to be some issues with
    # docstrings, line endings, etc.
    
    # DGO: I'm re-enabling it for fontio3 to see if things are different...
    
    >>> Gasp().wisdom(tighten=True)
    Overall object:
        These tables cover ranges of PPEMs, so interpret the keys as
        stakes in the ground, so to speak. If a Gasp object has, say, keys
        of 6 and 19, then the first covers sizes up to 6 PPEM, and the
        second covers 7-19 PPEM. Sizes not expressly covered are handled
        by the 'default' attribute (q.v.)
    Attribute 'default':
        This is the default Behavior that will be applied at all sizes
        greater than the maximum PPEM present in the keys. It's OK for
        this to be the only Behavior in the Gasp object; that simply means
        it will apply at all PPEMs.
    Attribute 'version': Version 0 is obsolete; version 1 is preferred.
    Interesting methods:
        getEntryForPPEM
            A method returning:
                A Behavior object associated with the specified PPEM value.
            Positional arguments:
                ppem
                    A numeric PPEM value. If this value is greater than the
                    highest key, the default value is returned.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Up to %d PPEM" % (i,)),
        item_pprintlabelpresort = True,
        item_subloggernamefunc = (lambda x: "up to %s ppem" % (x,)),
        map_wisdom = (
          "These tables cover ranges of PPEMs, so interpret the keys as "
          "stakes in the ground, so to speak. If a Gasp object has, say, "
          "keys of 6 and 19, then the first covers sizes up to 6 PPEM, and "
          "the second covers 7-19 PPEM. Sizes not expressly covered are "
          "handled by the 'default' attribute (q.v.)"))
    
    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Version",
            attr_wisdom = "Version 0 is obsolete; version 1 is preferred."),
        
        default = dict(
            attr_followsprotocol = True,
            attr_initfunc = behavior_v1.Behavior,
            attr_label = "Default behavior",
            attr_subloggernamefunc = (lambda x: "up to max ppem"),
            attr_showonlyiftrue = True,
            attr_wisdom = (
              "This is the default Behavior that will be applied at all sizes "
              "greater than the maximum PPEM present in the keys. It's OK "
              "for this to be the only Behavior in the Gasp object; that "
              "simply means it will apply at all PPEMs.")))
    
    attrSorted = ("version", "default")
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0003 0006 0002  0013 0001 FFFF 0003 |................|
        
        %start
        %kind
        protocol method
        %return
        None
        %pos
        w
        A LinkedWriter to which the binary content will be written.
        %kw
        stakeValue
        An optional stake value that will be set at the start of the binary
        data for this object. This can be useful if some higher-level object
        needs to have an offset to this object's data start.
        %note
        This method is how the living object gets converted into binary. Note
        that the binaryString() method is really just a thin wrapper around a
        call to this method.
        %end
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", self.version)  # version
        w.add("H", len(self) + 1)  # count (+1 is for default)
        
        for key in sorted(self):
            w.add("H", key)
            self[key].buildBinary(w, **kwArgs)
        
        w.add("H", 0xFFFF)
        self.default.buildBinary(w, **kwArgs)
    
    def compacted(self, **kwArgs):
        """
        Do custom compacting.
        
        >>> b1 = behavior_v1.Behavior(gridFit=True)
        >>> b2 = behavior_v1.Behavior(symmetricSmoothing=True)
        >>> obj = Gasp({6: b1, 9: b2, 12: b1, 20: b1}, default=b1)
        >>> obj.pprint()
        Up to 6 PPEM:
          Grid-fit
        Up to 9 PPEM:
          Symmetric smoothing
        Up to 12 PPEM:
          Grid-fit
        Up to 20 PPEM:
          Grid-fit
        Version: 1
        Default behavior:
          Grid-fit
        
        >>> obj.compacted().pprint()
        Up to 6 PPEM:
          Grid-fit
        Up to 9 PPEM:
          Symmetric smoothing
        Version: 1
        Default behavior:
          Grid-fit
        
        >>> del obj[9]
        >>> obj.compacted().pprint()
        Version: 1
        Default behavior:
          Grid-fit
        
        %start
        %kind
        protocol method
        %return
        A new Gasp object, compacted.
        %note
        Gasp objects undergo a specialized form of compaction. Adjacent keys
        whose associated Behaviors are equal are redundant, for example, and
        the numerically lower key will be removed.
        
        Also, any numerically highest keys whose associated Behaviors are the
        same as the default are redundant, and are removed.
        %end
        """
        
        r = self.__deepcopy__()
        maxKey = max(r)
        
        while len(r) and (r.default == r[maxKey]):
            del r[maxKey]
            
            if len(r):
                maxKey = max(r)
        
        kSorted = sorted(r)
        
        if len(kSorted) < 2:
            return r
        
        it = list(zip(kSorted, kSorted[1:]))
        
        for thisPPEM, nextPPEM in it:
            if r[thisPPEM] == r[nextPPEM]:
                del r[thisPPEM]
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Gasp. However, it also
        does validation via the logging module (the client should have done a
        logging.basicConfig call prior to calling this method, unless a logger
        is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Gasp.fromvalidatedbytes
        >>> obj = fvb(s[0:2], logger=logger)
        test.gasp - DEBUG - Walker has 2 remaining bytes.
        test.gasp - ERROR - Length 2 is too short (minimum 4)
        
        >>> obj = fvb(b'AA' + s[2:], logger=logger)
        test.gasp - DEBUG - Walker has 16 remaining bytes.
        test.gasp - WARNING - Table version 16705 is not known
        test.gasp - INFO - 3 GASPRANGEs defined.
        
        >>> obj = fvb(
        ...   s[:2] + utilities.fromhex("00 00") + s[4:],
        ...   logger = logger)
        test.gasp - DEBUG - Walker has 16 remaining bytes.
        test.gasp - INFO - Table version is 1
        test.gasp - WARNING - Number of GASPRANGEs is zero
        
        >>> obj = fvb(s[0:8], logger=logger)
        test.gasp - DEBUG - Walker has 8 remaining bytes.
        test.gasp - INFO - Table version is 1
        test.gasp - ERROR - Length 8 is too short for 3 GASPRANGEs (expected 16)
        
        >>> obj = fvb(
        ...   utilities.fromhex("00 00 00 02 00 09 00 01 00 08 cc cc"),
        ...   logger = logger)
        test.gasp - DEBUG - Walker has 12 remaining bytes.
        test.gasp - INFO - Table version is 0
        test.gasp - INFO - 2 GASPRANGEs defined.
        test.gasp - ERROR - The gaspRanges are not sorted.
        
        >>> obj = fvb(
        ...   utilities.fromhex("00 00 00 01 00 88 00 01"),
        ...   logger = logger)
        test.gasp - DEBUG - Walker has 8 remaining bytes.
        test.gasp - INFO - Table version is 0
        test.gasp - INFO - 1 GASPRANGEs defined.
        test.gasp - ERROR - Last gaspRange is not 0xFFFF sentinel.
        
        >>> obj = fvb(
        ...   utilities.fromhex(
        ...     "00 00 00 03 00 08 00 01 00 08 00 02 ff ff 00 02"),
        ...   logger = logger)
        test.gasp - DEBUG - Walker has 16 remaining bytes.
        test.gasp - INFO - Table version is 0
        test.gasp - INFO - 3 GASPRANGEs defined.
        test.gasp - WARNING - Two adjacent ranges have identical ppems
        test.gasp - WARNING - Two adjacent ranges have identical flags
        
        %start
        %kind
        protocol classmethod
        %return
        A new Gasp object from the specified walker.
        %pos
        w
        A walker used to provide the binary data that is converted into the
        living object.
        %kw
        logger
        A logger to which messages will be posted as the binary data are read.
        %end
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('gasp')
        else:
            logger = logger.getChild('gasp')

        tblLen = w.length()
        logger.debug(('V0001', (tblLen,), "Walker has %d remaining bytes."))
        
        if tblLen < 4:
            logger.error((
              'V0004',
              (tblLen,),
              "Length %d is too short (minimum 4)"))
            
            return None
        
        version = w.unpack("H")
        
        if version > 1:
            logger.warning((
              'E1003',
              (version,),
              "Table version %d is not known"))
        
        else:
            logger.info(('V0117', (version,), "Table version is %d"))
        
        count = w.unpack("H")
        r = cls(version=version)
        
        if not count:
            logger.warning(('V0118', (), "Number of GASPRANGEs is zero"))
            return r
        
        else:
            expectedLen = 4 + (count * 4)
            
            if tblLen < expectedLen:
                logger.error((
                  'V0119',
                  (tblLen, count, expectedLen),
                  "Length %d is too short for %d GASPRANGEs (expected %d)"))
                
                return None
            
            else:
                logger.info(('V0120', (count,), "%d GASPRANGEs defined."))
        
        groups = w.group("2H", count)
        keys = [obj[0] for obj in groups]
        
        if keys != sorted(keys):
            logger.error(('E1002', (), "The gaspRanges are not sorted."))
            return None
        
        if keys[-1] != 0xFFFF:
            logger.error((
              'E1001',
              (),
              "Last gaspRange is not 0xFFFF sentinel."))
            
            return None
        
        if version >= 1:
            fvn = behavior_v1.Behavior.fromvalidatednumber
        else:
            fvn = behavior_v0.Behavior.fromvalidatednumber

        for key, n in groups:
            if key == 0xFFFF:
                r.default = fvn(n, logger=logger)
            else:
                r[key] = fvn(n, logger=logger)
        
        # Check for duplicate sizes/behaviors
        
        for index, item in enumerate(groups[:-1]):
            if item[0] == groups[index+1][0]:
                logger.warning((
                  'V0172',
                  (),
                  "Two adjacent ranges have identical ppems"))
            
            if item[1] == groups[index+1][1]:
                logger.warning((
                  'W1004',
                  (),
                  "Two adjacent ranges have identical flags"))

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Gasp from the specified walker.
        
        >>> fb = Gasp.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        >>> _testingValues[1].version
        1
        
        %start
        %kind
        protocol classmethod
        %return
        A new Gasp object from the specified walker.
        %pos
        w
        A walker used to provide the binary data that is converted into the
        living object.
        %end
        """
        
        version = w.unpack("H")
        
        if version > 1:
            raise ValueError("Unknown 'gasp' table version: %d" % (version,))
        
        count = w.unpack("H")
        r = cls(version=version)

        if version >= 1:
            fw = behavior_v1.Behavior.fromwalker
        else:
            fw = behavior_v0.Behavior.fromwalker
        
        while count:
            key = w.unpack("H")
            b = fw(w)
            
            if key == 0xFFFF:
                r.default = b
            else:
                r[key] = b
            
            count -= 1
        
        return r
    
    def getEntryForPPEM(self, ppem):
        """
        Returns the Behavior associated with the specified PPEM value.
        
        >>> obj = _testingValues[1]
        >>> obj.getEntryForPPEM(4).pprint()
        Do gray
        >>> obj.getEntryForPPEM(12).pprint()
        Grid-fit
        >>> obj.getEntryForPPEM(30).pprint()
        Grid-fit
        Do gray
        
        %start
        %kind
        method
        %return
        A Behavior object associated with the specified PPEM value.
        %pos
        ppem
        A numeric PPEM value. If this value is greater than the highest key,
        the default value is returned.
        %end
        """
        
        allSizes = sorted(self)
        
        if not len(self):
            return self.default
        
        for walkPPEM in allSizes:
            if ppem <= walkPPEM:
                return self[walkPPEM]
        
        return self.default
    
    def merged(self, other, **kwArgs):
        """
        Returns a merged Gasp object. If the two are not essentially equal, a
        GaspIncompatibleMerge() exception is raised.
        
        >>> b1 = behavior_v1.Behavior(gridFit=True)
        >>> b2 = behavior_v1.Behavior(symmetricSmoothing=True)
        >>> b3 = behavior_v1.Behavior(doGray=True)
        >>> obj1 = Gasp({6: b1, 9: b2}, default=b3)
        >>> obj2 = Gasp({6: b1, 9: b2, 20: b1}, default=b3)
        >>> obj1.merged(obj1) == obj1
        True
        
        >>> obj1.merged(obj2)
        Traceback (most recent call last):
          ...
        GaspIncompatibleMerge
        
        %start
        %kind
        protocol method
        %return
        A merged Gasp object.
        %pos
        The other Gasp object to be merged with self.
        %exception
        GaspIncompatibleMerge
        This will be raised if self and other are not essentially equal.
        %end
        """
        
        selfComp = self.compacted()
        otherComp = other.compacted()
        
        if selfComp != otherComp:
            raise GaspIncompatibleMerge()
        
        return selfComp

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    b = utilities.fromhex("00 01 00 03 00 06 00 02 00 13 00 01 FF FF 00 03")
    
    _testingValues = (
      Gasp(),
      Gasp.frombytes(b))
    
    del b

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
