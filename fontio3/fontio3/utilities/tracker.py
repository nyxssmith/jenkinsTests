#
# tracker.py
#
# Copyright © 2004-2009, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for progress-tracking objects. These don't (yet) support actual locks;
they're just used to update stream trackers.
"""

#
# Classes
#

class ProgressTracker_List:
    """
    ProgressTracker_List objects are used in multi-threaded tools where
    progress lists are the items to be updated. Note there are no graphic-
    related calls in this class; the objects here just manipulate lists of
    numbers.

    A client obtains a cookie (a number) from a ProgressTracker_List object via
    the start or startUnbounded methods. This cookie is passed in to all other
    method calls. It represents a single tracker within the
    ProgressTracker_List object.

    Each single tracker keeps track of three things: current value, maximum
    value, and a label. If the maximum is -1 the tracker is unbounded.
    Unbounded trackers should have labels which are strings with exactly one
    Python "%d" format somewhere, since they may be displayed via Python string
    formatting calls.
    
    Trackers may have associated streams (usually sys.stdout), in which case
    comments and bumps will be displayed on the stream.
    """
    
    #
    # Methods
    #
    
    def __init__(self, lock=None, **kwArgs):
        """
        Initializes the ProgressTracker_List object. The specified lock object
        is used to serialize access to the data in the lists; it should be
        allocated by the caller via the thread.allocate_lock factory function.
        """
        
        self.dLists = {}  # cookie is key, value is list [curr, max, label]
        self.stream = kwArgs.get('stream')  # None is the default
        self.extraCommentIndent = 0
        self.granularity = kwArgs.get('granularity', 1)  # used with streams
    
    def _updateStream(self, cookie):
        """
        Displays the current value of the specified cookie to the output
        stream.
        """
        
        v = self.dLists[cookie]
        
        if callable(v[2]):
            print(v[2](v[0], v[1]), file=self.stream)
        
        elif v[1] == -1:  # unbounded
            print("%s: %d" % (v[2], v[0]), file=self.stream)
        
        else:
            print("%s: %d of %d" % (v[2], v[0], v[1]), file=self.stream)
    
    def bump(self, cookie):
        """
        Increments the progress indicator by one.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(100, "Label 1")
        >>> p.getCurrent(cookie)
        0
        >>> p.bump(cookie)
        >>> p.getCurrent(cookie)
        1
        >>> p.done(cookie)
        
        >>> f = utilities.debugStream()
        >>> p = ProgressTracker_List(stream=f)
        >>> cookie = p.start(3, label=(lambda i,j: ['X', 'Y', 'Z'][i-1]))
        >>> p.bump(cookie)
        >>> print(f.getvalue(), end='')
        X
        >>> p.bump(cookie)
        >>> print(f.getvalue(), end='')
        X
        Y
        >>> p.done(cookie)
        >>> f.close()
        """
        
        self.bumpBy(cookie, 1)
    
    def bumpBy(self, cookie, amount):
        """
        Increments the specified tracker by the specified amount.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(100)
        >>> p.getCurrent(cookie)
        0
        >>> p.bumpBy(cookie, 20)
        >>> p.getCurrent(cookie)
        20
        >>> p.bumpBy(cookie, 20)
        >>> p.getCurrent(cookie)
        40
        >>> p.done(cookie)
        
        >>> p2 = ProgressTracker_List(stream=sys.stdout, granularity=3)
        >>> cookie = p2.start(5, label="count")
        >>> p2.bump(cookie)
        >>> p2.bump(cookie)
        >>> p2.bump(cookie)
        count: 3 of 5
        >>> p2.bump(cookie)
        
        The last one is always displayed, even against granularity:
        
        >>> p2.bump(cookie)
        count: 5 of 5
        
        >>> f = utilities.debugStream()
        >>> p = ProgressTracker_List(stream=f)
        >>> cookie = p.start(3, label=(lambda i,j: ['X', 'Y', 'Z'][i-1]))
        >>> p.bumpBy(cookie, 1)
        >>> print(f.getvalue(), end='')
        X
        >>> p.bumpBy(cookie, 2)
        >>> print(f.getvalue(), end='')
        X
        Z
        >>> p.done(cookie)
        >>> f.close()
        """
        
        v = self.dLists[cookie]
        priorValue = v[0]
        
        if v[1] == -1:  # unbounded
            v[0] += amount
        else:
            v[0] = min(v[1], v[0] + amount)  # pin to count
        
        if (
          self.stream and
          (priorValue != v[0]) and
          ((v[0] == v[1]) or (v[0] % self.granularity == 0))):
            
            self._updateStream(cookie)
    
    def commentEnd(self):
        self.extraCommentIndent -= 1
    
    def commentStart(self, label):
        """
        Adds a comment to the current tracker, without creating a new cookie.
        Note that this method is only useful when the stream is not None, in
        which case the tracker is being used by itself and is not mirroring any
        other GUI tracker.
        
        The label will be indented as appropriate for the current level.
        """
        
        if self.stream:
            n = len(self.dLists)
            
            print(
              "%s%s" % (" " * 2 * (n + self.extraCommentIndent), label),
              file = self.stream)
            
            self.extraCommentIndent += 1
    
    def cookieIterator(self):
        """
        Returns an iterator (actually a generator) for all current cookies, in
        no particular order.
        
        >>> p = ProgressTracker_List()
        >>> cookie1 = p.start(100)
        >>> cookie2 = p.start(50)
        >>> for i, c in enumerate(p.cookieIterator()): p.bumpBy(c, 10 * i + 1)
        ... 
        >>> p.getCurrent(cookie1), p.getCurrent(cookie2)
        (1, 11)
        >>> p.done(cookie1)
        >>> p.done(cookie2)
        """
        
        for cookie in self.dLists:
            yield cookie
    
    def done(self, cookie):
        """
        Frees up this tracker.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(100, "A Label")
        >>> p.getValues(cookie)
        [0, 100, 'A Label']
        >>> p.done(cookie)
        >>> p.getValues(cookie)
        Traceback (most recent call last):
          ...
        KeyError: 0
        """
        
        del self.dLists[cookie]
    
    def getCurrent(self, cookie):
        return self.getValues(cookie)[0]
    
    def getLabel(self, cookie):
        return self.getValues(cookie)[2]
    
    def getMaximum(self, cookie):
        return self.getValues(cookie)[1]
    
    def getValues(self, cookie):
        """
        Returns a (current, maximum, label) triple.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(100, "A Label")
        >>> p.getValues(cookie)
        [0, 100, 'A Label']
        >>> p.bumpBy(cookie, 15)
        >>> p.getValues(cookie)
        [15, 100, 'A Label']
        >>> p.done(cookie)
        """
        
        return self.dLists[cookie]
    
    def reset(self, cookie):
        """
        Reset the current progress to zero.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(100, "Label 1")
        >>> p.getCurrent(cookie)
        0
        >>> p.bump(cookie)
        >>> p.getCurrent(cookie)
        1
        >>> p.reset(cookie)
        >>> p.getCurrent(cookie)
        0
        >>> p.done(cookie)
        """
        
        v = self.dLists[cookie]
        priorValue = v[0]
        v[0] = 0
        
        if self.stream and priorValue:
            self._updateStream(cookie)
    
    def setGranularity(self, newGranularity):
        """
        Sets the granularity for stream-based trackers.
        """
        
        self.granularity = newGranularity
    
    def setPercent(self, cookie, percent):
        """
        Sets the current progress to the specified percentage of the maximum.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(40)
        >>> p.getCurrent(cookie)
        0
        >>> p.setPercent(cookie, 50)
        >>> p.getCurrent(cookie)
        20
        >>> p.done(cookie)
        """
        
        v = self.dLists[cookie]
        priorValue = v[0]
        v[0] = int(round((percent / 100.0) * v[1]))
        
        if self.stream and (priorValue != v[0]):
            self._updateStream(cookie)
    
    def setProgressAndMaximum(self, cookie, progress, maximum):
        """
        Sets the values for the specified tracker.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(100, "A Label")
        >>> p.getValues(cookie)
        [0, 100, 'A Label']
        >>> p.setProgressAndMaximum(cookie, 20, 40)
        >>> p.getValues(cookie)
        [20, 40, 'A Label']
        >>> p.done(cookie)
        """
        
        v = self.dLists[cookie]
        priors = v[:2]
        v[:2] = [progress, maximum]
        
        if self.stream and (priors != v[:2]):
            self._updateStream(cookie)
    
    def setValues(self, cookie, v):
        """
        Sets the three values [current, maximum, label] to the contents of the
        specified list.
        
        >>> p = ProgressTracker_List()
        >>> cookie = p.start(100, "A Label")
        >>> p.getValues(cookie)
        [0, 100, 'A Label']
        >>> p.setValues(cookie, [20, 40, "Another label"])
        >>> p.getValues(cookie)
        [20, 40, 'Another label']
        >>> p.done(cookie)
        """
        
        assert len(v) == 3, "List must have exactly 3 elements!"
        self.dLists[cookie][:] = v
        
        if self.stream:
            self._updateStream(cookie)
    
    def start(self, count, label=None):
        """
        Creates and returns a cookie for a new progress tracker, with count as
        the maximum.
        
        The label may be a string (with an embedded %d in order to support a
        nicely formatted output), or a function taking two arguments (the
        current count and the total) and returning a string.
        
        >>> p = ProgressTracker_List()
        >>> cookie1 = p.start(100)
        >>> cookie2 = p.start(50, "Another tracker")
        >>> p.done(cookie1)
        >>> p.done(cookie2)
        """
        
        cookie = (1 + max(self.dLists)) if self.dLists else 0
        
        if self.stream:
            n = len(self.dLists)
            
            if label is None:
                label = "Progress tracker #%d" % (n + 1,)
            
            elif not callable(label):
                t = (" " * 2 * (n + self.extraCommentIndent), label)
                label = "%s%s" % t
        
        self.dLists[cookie] = [0, count, label]
        return cookie
    
    def startUnbounded(self, label=None):
        """
        Creates and returns a cookie for a new unbounded progress tracker.
        
        The label may be a string (with an embedded %d in order to support a
        nicely formatted output), or a function taking two arguments (the
        current count and the total) and returning a string.
        
        >>> p = ProgressTracker_List()
        >>> cookie1 = p.startUnbounded()
        >>> p.getValues(cookie1)
        [0, -1, None]
        >>> cookie2 = p.startUnbounded("Processing number %d")
        >>> p.getValues(cookie2)
        [0, -1, 'Processing number %d']
        >>> p.done(cookie1)
        >>> p.done(cookie2)
        """
        
        cookie = (1 + max(self.dLists)) if self.dLists else 0
        
        if self.stream:
            count = len(self.dLists)
            
            if label is None:
                label = "Progress tracker #%d" % (count + 1,)
            
            elif not callable(label):
                t = (" " * 2 * (count + self.extraCommentIndent), label)
                label = "%s%s" % t
        
        self.dLists[cookie] = [0, -1, label]
        return cookie
    
    def syncTracker(self, other):
        """
        Makes this tracker reflect the state of the other tracker, using the
        label as the synchronization token.
        
        >>> p1 = ProgressTracker_List()
        >>> c1_1 = p1.start(100, "Fred")
        >>> for c in p1.cookieIterator(): print(p1.getValues(c))
        ... 
        [0, 100, 'Fred']
        >>> p2 = ProgressTracker_List()
        >>> c2_1 = p2.start(50, "Charlie")
        >>> c2_2 = p2.start(40, "Fred")
        >>> c2_3 = p2.startUnbounded("Number %d")
        >>> for c in p2.cookieIterator(): print(p2.getValues(c))
        ... 
        [0, 50, 'Charlie']
        [0, 40, 'Fred']
        [0, -1, 'Number %d']
        >>> p2.bumpBy(c2_2, 15)
        >>> for c in p2.cookieIterator(): print(p2.getValues(c))
        ... 
        [0, 50, 'Charlie']
        [15, 40, 'Fred']
        [0, -1, 'Number %d']
        >>> p1.syncTracker(p2)
        >>> for c in p1.cookieIterator(): print(p1.getValues(c))
        ... 
        [15, 40, 'Fred']
        [0, 50, 'Charlie']
        [0, -1, 'Number %d']
        """
        
        selfLabelToCookie = {}
        touched = set()
        dLists = self.dLists
        
        for selfCookie, selfList in dLists.items():
            selfLabelToCookie[selfList[2]] = selfCookie
         
        for otherCookie, otherList in other.dLists.items():
            if otherList[2] in selfLabelToCookie:
                selfCookie = selfLabelToCookie[otherList[2]]
                dLists[selfCookie][:] = otherList
                touched.add(selfCookie)
            
            else:
                newSelfCookie = ((1 + max(dLists)) if dLists else 0)
                dLists[newSelfCookie] = list(otherList)
                touched.add(newSelfCookie)
        
        for untouched in set(dLists) - touched:
            del dLists[untouched]

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import sys
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
