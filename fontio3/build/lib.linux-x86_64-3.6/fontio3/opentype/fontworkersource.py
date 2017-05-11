#
# fontworkersource.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for the FontWorkerSource iterator.
"""

# Future imports


# System imports
import re

# -----------------------------------------------------------------------------

#
# Functions
#

def fwsint(s):
    """
    Returns the integer value of 's', or None if it could not be made into an
    int. Used in numerous places in FontWorker source for evaluation of class
    numbers, etc.,"
    
    >>> fwsint('123')
    123
    >>> fwsint('hello, world!')
    >>> fwsint('18 is a number')
    >>> fwsint('      21  ')
    21
    """
    
    try:
        r = int(s)
    except ValueError:
        r = None

    return r

# -----------------------------------------------------------------------------

#
# Classes
#

class FontWorkerSource(object):
    """
    This is an iterator for FontWorker GSUB, GPOS, or GDEF source code.
    It reads in a stream, strips off comments and extraneous whitespace, and
    stores the lines for later use.  In addition to the usual iterator next()
    method, it provides some extra methods like prev(), goto(), push(), and
    pop().
    
    >>> fws = FontWorkerSource(_test_FW_s)
    >>> line = next(fws)
    >>> print(fws.lineNumber, line)
    1 abc
    >>> line = next(fws)
    >>> print(fws.lineNumber, line)
    2 def
    >>> line = next(fws)
    >>> print(fws.lineNumber, line)
    3 ghi
    >>> fws.prev()
    >>> line = next(fws)
    >>> print(fws.lineNumber, line)
    3 ghi
    >>> fws.push()
    >>> fws.goto(1)
    >>> line = next(fws)
    >>> print(fws.lineNumber, line)
    1 abc
    >>> fws.pop()
    >>> line = next(fws)
    >>> print(fws.lineNumber, line)
    4 jkl
    >>> fws.goto(6)
    >>> print(next(fws))
    subtable end
    """
    def __init__(self, s):
        """
        read in lines from a stream, strip off comments and extraneous
        whitespace, and store them for later use
        """
        rawLines = s.readlines()
        lines = [''] # add a dummy line so real line numbers start from one
        for rawLine in rawLines:
            line = re.sub(r'^\s*\%\s*sub-?table\s*$', "subtable end", rawLine)
            line = re.match('^[^%^*]*', line).group()  # strip off comments
            line = line.strip()  # strip off leading/trailing whitespace
            lines.append(line)

        self.lines = lines
        self.lineNumber = 0
        self.stack = []

    def __iter__(self):
        return self

    def __next__(self):
        """
        return the next line
        """
        if self.lineNumber + 1 >= len(self.lines):
            raise StopIteration
        else:
            self.lineNumber += 1
            return self.lines[self.lineNumber]

    def prev(self):
        """
        back up one line
        """
        self.lineNumber -= 1

    def goto(self, lineNumber):
        """
        go to a specific line number
        """
        self.lineNumber = lineNumber - 1 # so next() will be on lineNumber

    def push(self):
        """
        push the current line number on the stack
        """
        self.stack.append(self.lineNumber)

    def pop(self):
        """
        pop a line number off the stack and go to that line number
        """
        self.lineNumber = self.stack.pop()

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from io import StringIO
    
    _test_FW_s = StringIO(
        """abc
        def % some comment
        ghi % another comment
        jkl *** yet more comments ***
        mno
        % subtable
        pqr
        """)

def _test():
    """
    doctest
    """
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

