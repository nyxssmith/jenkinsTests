#
# invert.py
#
# Copyright © 2010-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for raw binary string data with associated creation functions, so a
client may keep large numbers of objects without slowing down performance.
"""

# Other imports
from fontio3 import utilities
from fontio3.utilities import writer

# -----------------------------------------------------------------------------

#
# Classes
#

class Invert(object):
    """
    An Invert object is a string or file walker (backed by a binary string)
    with an associated creation function. The "live" version of the object is
    created on an on-demand basis, so for base types that are very large (for
    instance, fontio3.hints.hints_tt.Hints) there is not much performance
    overhead in creating lots of instances.

    One important restriction: the "live" object must follow the fontdata
    protocol.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, w, createFunc, **kwArgs):
        """
        Initializes the Invert object with the specified walker and creation
        function (which will usually be a fromwalker() method from some
        fontdata-derived class). The walker must have been set with a start and
        limit that exactly encompasses the data needed for the object's
        instantiation.

        The advantage of an Invert object is that the "live" object's creation
        is deferred until it is actually needed. This greatly improves
        performance for complex types. Note also that FileWalkers may be used
        for very large data-driven types (such as 'glyf' tables for CJK fonts).
        
        >>> s = utilities.fromhex("00 03 00 02 00 05 00 06")
        >>> w = walker.StringWalker(s)
        >>> obj = Invert(w, _Helper.fromwalker)
        >>> print(obj)
        [2, 5, 6]
        
        >>> obj = Invert(w, _Helper.fromwalker, n=19)
        >>> print(obj)
        [2, 5, 6], myAttr = 19
        
        >>> w = walker.StringWalker(s, start=2)
        >>> obj = Invert(w, _Helper.fromwalker)
        >>> print(obj)
        [5, 6]
        """
        
        self.w = w  # already has correct start and limit
        self.createFunc = createFunc
        self.savedArgs = kwArgs.copy()
        self.cachedObj = None
    
    #
    # Special methods
    #
    
    def __copy__(self):
        """
        Returns a shallow copy.
        """
        
        r = type(self)(self.w, self.createFunc, **self.savedArgs)
        r.cachedObj = self.cachedObj
        return r
    
    def __deepcopy__(self, memo=None):
        """
        Returns a deep copy. This is essentially the same as a shallow copy,
        but any cached object is recreated.
        """
        
        r = type(self)(self.w, self.createFunc, **self.savedArgs)
        
        if self.cachedObj is not None:
            r._makeContent()
        
        return r
    
    def __eq__(self, other):
        """
        Returns True if self and other are equal. Note that other may be either
        an Invert object, or a "live" object.
        """
        
        self._makeContent()
        
        try:
            other._makeContent()
            oco = other.cachedObj
        
        except AttributeError:
            oco = other
        
        return self.cachedObj == oco
    
    def __ne__(self, other):
        """
        Returns True if self and other are unequal. Note that other may be
        either an Invert object, or a "live" object.
        """
        
        self._makeContent()
        
        try:
            other._makeContent()
            oco = other.cachedObj
        
        except AttributeError:
            oco = other
        
        return self.cachedObj != oco
    
    def __bool__(self):
        """
        Returns True if the "live" object would return True from a bool() call.
        
        >>> w = walker.StringWalker(utilities.fromhex("00 00"))
        >>> obj = Invert(w, _Helper.fromwalker)
        >>> bool(obj)
        False
        """
        
        self._makeContent()
        return bool(self.cachedObj)
    
    def __repr__(self):
        """
        Returns a string that can be eval()'d back to an equal "live" object
        (note that this method does not provide a way of getting a string
        which, when eval()'d, yields an Invert object).
        """
        
        self._makeContent()
        return repr(self.cachedObj)
    
    def __str__(self):
        """
        Returns a nicely readable string representation of the object.
        """
        
        self._makeContent()
        return str(self.cachedObj)
    
    #
    # Private methods
    #
    
    def _makeContent(self):
        """
        """
        
        if self.cachedObj is None:
            self.w.reset()
            self.cachedObj = self.createFunc(self.w, **self.savedArgs)
    
    #
    # Public methods
    #
    
    def asImmutable(self, **kwArgs):
        """
        Returns a version of the object which can be used as a key in a dict.
        This is done recursively with the contents, so all contained
        sub-objects will also be immutable in the returned value. Note that the
        binary string is not used, even though it is immutable; in general, the
        actual asImmutable() results on the "live" object are preferable, as
        they're more readable.
        """
        
        self._makeContent()
        return self.cachedObj.asImmutable(**kwArgs)
    
    def binaryString(self, **kwArgs):
        """
        Returns the binary string for the object. If the "live" object has not
        yet been created, this method simply returns the string directly. If
        the "live" object has been created, its buildBinary() method is called,
        as usual.
        """
        
        if self.cachedObj is None:
            self.w.reset()
            return self.w.rest()
        
        w = writer.LinkedWriter()
        self.buildBinary(w, **kwArgs)
        return w.binaryString()
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Invert object to the specified
        LinkedWriter. Note that if the "live" object has never been asked for
        for this Invert object, the original binary data will be directly
        added, with no further processing needed. However, if the "live" object
        is cached (even if unmodified), its own buildBinary() method will be
        called to accomplish the task.
        """
        
        if self.cachedObj is None:
            self.w.reset()
            w.addString(self.w.rest())
        
        else:
            self.cachedObj.buildBinary(w, **kwArgs)
    
    def clearCachedObject(self):
        """
        Removes the cached object (losing any changes that may have been made
        to it), so the next time live() is called a new "live" object is
        manufactured.
        """
        
        self.cachedObj = None
    
    def coalesced(self, **kwArgs):
        """
        Returns a new "live" object which has been coalesced. See the
        individual metaclasses in the fontdata protocol for the appropriate
        definition of coalescing.
        """
        
        self._makeContent()
        return self.cachedObj.coalesced(**kwArgs)
    
    def compacted(self, **kwArgs):
        """
        Returns a new "live" object which has been compacted. See the
        individual metaclasses in the fontdata protocol for the appropriate
        definition of compacting.
        """
        
        self._makeContent()
        return self.cachedObj.compacted(**kwArgs)
    
    def cvtsRenumbered(self, **kwArgs):
        """
        Returns a new "live" object whose CVT indices have been renumbered.
        """
        
        self._makeContent()
        return self.cachedObj.cvtsRenumbered(**kwArgs)
    
    def fdefsRenumbered(self, **kwArgs):
        """
        Returns a new "live" object whose FDEF indices have been renumbered.
        """
        
        self._makeContent()
        return self.cachedObj.fdefsRenumbered(**kwArgs)
    
    def gatheredInputGlyphs(self, **kwArgs):
        """
        Returns a set of all input glyph indices present in the "live" object.
        """
        
        self._makeContent()
        return self.cachedObj.gatheredInputGlyphs(**kwArgs)
    
    def gatheredLivingDeltas(self, **kwArgs):
        """
        Returns a set of all LivingDeltas objects.
        """
        
        self._makeContent()
        return self.cachedObj.gatheredLivingDeltas(**kwArgs)
    
    def gatheredMaxContext(self, **kwArgs):
        """
        Returns the maximum context for the "live" object (in an OpenType or
        AAT sense).
        """
        
        self._makeContent()
        return self.cachedObj.gatheredMaxContext(**kwArgs)
    
    def gatheredOutputGlyphs(self, **kwArgs):
        """
        Returns a set of all output glyph indices present in the "live" object.
        """
        
        self._makeContent()
        return self.cachedObj.gatheredOutputGlyphs(**kwArgs)
    
    def gatheredRefs(self, **kwArgs):
        """
        Returns a dict mapping the IDs of any OpenType LookupTable objects (in
        the "live" object) to the LookupTable objects themselves.
        """
        
        self._makeContent()
        return self.cachedObj.gatheredRefs(**kwArgs)
    
    def getNamer(self):
        """
        Returns the namer associated with the "live" object, or None.
        """
        
        self._makeContent()
        return self.cachedObj.getNamer()
    
    def glyphsRenumbered(self, oldToNew, **kwArgs):
        """
        Returns a new version of the "live" object with glyphs renumbered in
        accordance with the specified oldToNew map.
        """
        
        self._makeContent()
        return self.cachedObj.glyphsRenumbered(oldToNew, **kwArgs)
    
    def hasCycles(self, **kwArgs):
        """
        Returns True if the "live" object has cycles (i.e. internal circular
        object references for deep objects).
        """
        
        self._makeContent()
        return self.cachedObj.hasCycles(**kwArgs)
    
    def hexdumpString(self, **kwArgs):
        """
        Returns a string with a hex dump of the Invert object. If the "live"
        object has not yet been created, this simply dumps the originally
        specified binary data. Otherwise, it calls the "live" object's
        binaryString() method with the provided kwArgs.
        
        This method will not create the "live" object if it does not already
        exist.
        
        >>> s = utilities.fromhex("00 03 00 02 00 05 00 06")
        >>> obj = Invert(walker.StringWalker(s), _Helper.fromwalker)
        >>> print(obj.hexdumpString(), end='')
               0 |0003 0002 0005 0006                      |........        |
        """
        
        if self.cachedObj is None:
            self.w.reset()
            return utilities.hexdumpString(self.w.rest())
        
        return utilities.hexdumpString(self.cachedObj.binaryString(**kwArgs))
    
    def isValid(self, **kwArgs):
        """
        Returns True if the "live" object is valid, and False otherwise. Uses
        a logger passed as a keyword argument (or the default logger).
        """
        
        self._makeContent()
        return self.cachedObj.isValid(**kwArgs)
    
    def live(self, weak=False):
        """
        Returns the "live" editable object from the binary string and creation
        function originally specified when this Invert object was created. Note
        that if the "live" object has already been created, it is simply
        returned -- specifically, is it NOT re-made.
        
        If the weak argument is True, the "live" object will not be made if it
        doesn't already exist; None is returned in this case.
        """
        
        if not weak:
            self._makeContent()
        
        return self.cachedObj
    
    def merged(self, other, **kwArgs):
        """
        Creates and returns a new object representing the merger of other into
        self. Note that other may be either an Invert object, or a "live"
        object.
        """
        
        self._makeContent()
        
        try:
            other._makeContent()
            oco = other.cachedObj
        
        except AttributeError:
            oco = other
        
        return self.cachedObj.merged(oco, **kwArgs)
    
    def namesRenumbered(self, oldToNew, **kwArgs):
        """
        Returns a new version of the "live" object with 'name' indices
        renumbered in accordance with the specified oldToNew map.
        """
        
        self._makeContent()
        return self.cachedObj.namesRenumbered(oldToNew, **kwArgs)
    
    def pcsRenumbered(self, mapData, **kwArgs):
        """
        Returns a new version of the "live" object with PCs renumbered in
        accordance with the specified mapData.
        """
        
        self._makeContent()
        return self.cachedObj.pcsRenumbered(mapData, **kwArgs)
    
    def pointsRenumbered(self, mapData, **kwArgs):
        """
        Returns a new version of the "live" object with points renumbered in
        accordance with the specified mapData.
        """
        
        self._makeContent()
        return self.cachedObj.pointsRenumbered(mapData, **kwArgs)
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the "live" object.
        """
        
        self._makeContent()
        return self.cachedObj.pprint(**kwArgs)
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Displays changes from prior to self. Note that other may be either an
        Invert object, or a "live" object.
        """
        
        self._makeContent()
        
        try:
            prior._makeContent()
            oco = prior.cachedObj
        
        except AttributeError:
            oco = prior
        
        return self.cachedObj.pprint_changes(oco, **kwArgs)
    
    def recalculated(self, **kwArgs):
        """
        Returns a new version of the "live" object which has been recalculated.
        See the individual metaclasses in the fontdata protocol for a
        description of recalculation.
        """
        
        self._makeContent()
        return self.cachedObj.recalculated(**kwArgs)
    
    def scaled(self, scaleFactor, **kwArgs):
        """
        Returns a new version of the "live" object which has been scaled. See
        the individual metaclasses in the fontdata protocol for a description
        of scaling.
        """
        
        self._makeContent()
        return self.cachedObj.scaled(scaleFactor, **kwArgs)
    
    def setNamer(self, newNamer):
        """
        Sets the specified namer as the active namer for the "live" object.
        """
        
        self._makeContent()
        self.cachedObj.setNamer(newNamer)
    
    def storageRenumbered(self, **kwArgs):
        """
        Returns a new "live" object whose storage indices have been renumbered.
        """
        
        self._makeContent()
        return self.cachedObj.storageRenumbered(**kwArgs)
    
    def transformed(self, matrixObj, **kwArgs):
        """
        Returns a new version of the "live" object which has been transformed.
        See the individual metaclasses in the fontdata protocol for a
        description of transformation.
        """
        
        self._makeContent()
        return self.cachedObj.transformed(matrixObj, **kwArgs)
    
    def walkerIsEmpty(self):
        """
        Returns True if there is no data in the walker (after it is reset).
        """
        
        self.w.reset()
        return self.w.atEnd()

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.fontdata import seqmeta
    from fontio3.utilities import walker
    
    class _Helper(list, metaclass=seqmeta.FontDataMetaclass):
        seqSpec = {'item_renumberdirect': True}
        attrSpec = {'myAttr': {'attr_showonlyiftrue': True}}
        
        @classmethod
        def fromwalker(cls, w, **kwArgs):
            return cls(w.group("H", w.unpack("H")), myAttr=kwArgs.get('n', 0))
        
        def buildBinary(self, w, **kwArgs):
            w.add("H", len(self))
            w.addGroup("H", self)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
