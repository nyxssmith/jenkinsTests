#
# invariants.py
#
# Copyright © 2009-2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
This module controls the Protocol, and provides so-called *invariant* methods.
These are methods whose implementation stays the same in all metaclasses; to
avoid duplication, they are implemented here and then copied into a new class
when that class is created by the metaclass.

No metaclass is actually defined here; it is support code for other
metaclasses.
"""

# System imports
import collections
import textwrap

# Other imports
from fontio3 import utilities
from fontio3.utilities import writer, walkerbit

# -----------------------------------------------------------------------------

#
# Constants
#

_protocolMethods = frozenset([
  'asImmutable',
  'binaryString',
  'buildBinary',
# 'changes',
  'checkInput',
  'coalesced',
  'compacted',
  'converted',
  'cvtsRenumbered',
  'fdefsRenumbered',
  'frombytes',
  'fromvalidatedbytes',
  'fromvalidatedwalker',
  'fromwalker',
  'gatheredInputGlyphs',
  'gatheredLivingDeltas',
  'gatheredMaxContext',
  'gatheredOutputGlyphs',
  'gatheredRefs',
  'getNamer',
  'getSortedAttrNames',
  'glyphsRenumbered',
  'groupfrombytes',
  'groupfromvalidatedwalker',
  'groupfromwalker',
  'hasCycles',
  'isValid',
  'merged',
  'namesRenumbered',
  'nonProtocolMethods',
  'pcsRenumbered',
  'pointsRenumbered',
  'pprint',
  'pprint_changes',
  'recalculated',
  'scaled',
  'setNamer',
  'storageRenumbered',
  'transformed',
  'wisdom'])

wrapper0 = textwrap.TextWrapper()

wrapper4 = textwrap.TextWrapper(
  initial_indent = "    ",
  subsequent_indent = "    ")

wrapper8 = textwrap.TextWrapper(
  initial_indent = "        ",
  subsequent_indent = "        ")

# -----------------------------------------------------------------------------

#
# Private utility functions
#

def _handleExplicitWisdom(obj, **kwArgs):
    od = obj.__class__.__dict__
    mainDict = od['_MAIN_SPEC']
    extraDict = od['_EXTRA_SPEC']  # extra layer of indirection here
    didSomething = False
    tighten = kwArgs.get('tighten', False)
    
    for k, v in mainDict.items():
        if 'wisdom' not in k:
            continue
        
        if k.endswith('_wisdom_key'):
            _showLabeledBlock("Mapping keys", wrapper0, v, wrapper4, **kwArgs)
        
        elif k.endswith('_wisdom_value'):
            _showLabeledBlock(
              "Mapping values",
              wrapper0,
              v,
              wrapper4,
              **kwArgs)
        
        elif k.endswith('_wisdom_index'):
            _showLabeledBlock(
              "Sequence indices",
              wrapper0,
              v,
              wrapper4,
              **kwArgs)
        
        elif k == "item_wisdom":
            if '_SEQSPEC' in od:
                _showLabeledBlock(
                  "Sequence values",
                  wrapper0,
                  v,
                  wrapper4,
                  **kwArgs)
            
            elif '_SETSPEC' in od:
                _showLabeledBlock(
                  "Set values",
                  wrapper0,
                  v,
                  wrapper4,
                  **kwArgs)
            
            else:
                _showLabeledBlock(
                  "Individual values",
                  wrapper0,
                  v,
                  wrapper4,
                  **kwArgs)
        
        else:
            _showLabeledBlock(
              "Overall object",
              wrapper0,
              v,
              wrapper4,
              **kwArgs)
        
        if not tighten:
            print()
        
        didSomething = True
    
    for attrName in sorted(extraDict):
        attrInfo = extraDict[attrName]
        
        for k in sorted(attrInfo):
            v = attrInfo[k]
            
            if 'wisdom' not in k:
                continue
            
            _showLabeledBlock(
              "Attribute '%s'" % (attrName,),
              wrapper0,
              v,
              wrapper4,
              **kwArgs)
            
            if not tighten:
                print()
            
            didSomething = True
    
    return didSomething

def _makeLabeledBlock(lbl, lblWrapper, blk, blkWrapper, **kwArgs):
    r = []
    singleLine = lblWrapper.wrap(lbl + ': ' + blk)
    
    if len(singleLine) == 1:
        r.append(singleLine[0])
    
    else:  # Whole thing didn't fit in one line
        r.append(lblWrapper.wrap(lbl + ':')[0])
        r.extend(blkWrapper.wrap(blk))
    
    if not kwArgs.get('tighten', False):
        r.append('')
    
    return r

def _showLabeledBlock(lbl, lblWrapper, blk, blkWrapper, **kwArgs):
    """
    >>> _showLabeledBlock("abc", wrapper0, "xyz", wrapper4, tighten=True)
    abc: xyz
    
    >>> _showLabeledBlock("abc", wrapper0, "xyz " * 50, wrapper4, tighten=True)
    abc:
        xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz
        xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz
        xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz xyz
        xyz xyz
    """
    
    for line in _makeLabeledBlock(lbl, lblWrapper, blk, blkWrapper, **kwArgs):
        print(line)

def _summary(obj, **kwArgs):
    if not obj.__doc__:
        return ''
    
    sv = obj.__doc__.splitlines()
    sv = [s.strip() for s in sv]
    d = {i: s[0] for i, s in enumerate(sv) if s}
    dRev = utilities.invertDictFull(d, asSets=True)
    
    if '%' in dRev:
        return _summary_annotated(sv, dRev['%'], **kwArgs)
    
    if '>' not in dRev:
        return '\n'.join(sv)
    
    n = min(dRev['>']) - 1
    
    while n > 0:
        if sv[n]:
            break
        
        n -= 1
    
    if not n:
        return ''
    
    return '\n'.join(sv[:n+1])

def _summary_annotated(sv, noteLineSet, **kwArgs):
    tighten = kwArgs.get('tighten', False)
    startIndex = min(noteLineSet)
    endIndex = max(noteLineSet)
    assert sv[startIndex] == '%start'
    assert sv[endIndex] == '%end'
    state = None
    d = {'kind': [], 'return': [], 'pos': [], 'kw': [], 'note': [], 'exc': []}
    
    for s in sv[startIndex+1:endIndex]:
        if state is not None:
            if not s.startswith('%'):
                if state in {'pos', 'kw', 'exc'}:
                    if svName is None:
                        svName = s
                    
                    elif not s:  # paragraph break, handled below
                        d[state].append((svName, ' '.join(svTemp)))
                        svTemp = []
                    
                    else:
                        svTemp.append(s)
                
                elif not s:
                    d[state].append((svName, ' '.join(svTemp)))
                    svTemp = []
                
                else:
                    svTemp.append(s)
                
                continue
            
            else:
                d[state].append((svName, ' '.join(svTemp)))
        
        if s.startswith('%kind'):
            state = 'kind'
        elif s.startswith('%ret'):
            state = 'return'
        elif s.startswith('%pos'):
            state = 'pos'
        elif s.startswith('%kw'):
            state = 'kw'
        elif s.startswith('%exc'):
            state = 'exc'
        elif s.startswith('%note'):
            state = 'note'
        else:
            assert False, "Unknown annotation: %s" % (s,)
        
        svName = None
        svTemp = []
    
    assert svTemp
    d[state].append((svName, ' '.join(svTemp)))
    assert len(d['kind']) == 1
    assert len(d['return']) == 1
    
    rv = _makeLabeledBlock(
      "A %s returning" % (d['kind'][0][1],),
      wrapper0,
      d['return'][0][1],
      wrapper4,
      **kwArgs)
    
    if d['pos']:
        if not tighten:
            rv.append("")
        
        rv.append("Positional arguments:")
        currName = ""
        
        for name, text in d['pos']:
            if not tighten:
                rv.append("")
            
            if name != currName:
                rv.append("    %s" % (name,))
                currName = name
            
            rv.extend(wrapper8.wrap(text))
    
    if d['kw']:
        if not tighten:
            rv.append("")
        
        rv.append("Keyword arguments:")
        currName = ""
        
        for name, text in d['kw']:
            if not tighten:
                rv.append("")
            
            if name != currName:
                rv.append("    %s" % (name,))
                currName = name
            
            rv.extend(wrapper8.wrap(text))
    
    if d['exc']:
        if not tighten:
            rv.append("")
        
        rv.append("Exceptions:")
        currName = ""
        
        for name, text in d['exc']:
            if not tighten:
                rv.append("")
            
            if name != currName:
                rv.append("    %s" % (name,))
                currName = name
            
            rv.extend(wrapper8.wrap(text))
    
    if d['note']:
        if not tighten:
            rv.append("")
        
        rv.append("General notes:")
        
        for ignore, text in d['note']:
            if not tighten:
                rv.append("")
            
            rv.extend(wrapper4.wrap(text))
    
    return '\n'.join(rv)

# -----------------------------------------------------------------------------

#
# Method functions
#

if 0:
    def __________________(): pass

def _binaryString(self, **kwArgs):
    """
    Returns a string with the binary data for the object. This is just a thin
    wrapper around a call to buildBinary(), which is what you should be using,
    if possible.
    
    %start
    %kind
    protocol method
    %return
    A string containing the binary data for the object.
    %note
    This method, while occasionally useful, should generally not be used by
    your code; use buildBinary instead, which aggregates all the binary content
    together, and thus drastically reduces memory use compared to the old
    fontio1-based binaryString() approach.
    %end
    """
    
    try:
        self.buildBinary
    except AttributeError:
        raise NotImplementedError()
    
    w = writer.LinkedWriter()
    self.buildBinary(w, **kwArgs)
    return w.binaryString()

def _converted(self, **kwArgs):
    """
    Default method for 'converted' protocol method. kwArgs:

        returnTokens    returns a sequence of tokens
                        available for various conversions

        filterVersions  specify a filter to use for returned tokens

        useToken        return the converted object using the specified
                        token. Default simply returns 'self'.
    
    %start
    %kind
    protocol method
    %return
    Different values are returned depending on the keyword arguments. Overall,
    this method is intended to return a new object, converted from self, but
    in a different format or with some other key difference. For instance, a
    version 2 'OS/2' table can be converted to a version 5 'OS/2' table.
    %kw
    filterVersions
    This is not currently used in fontio3, but may be defined someday as a way
    to limit the set of tokens returned by this method when returnTokens is
    True.
    %kw
    returnTokens
    Set this to True to get back a sequence (possibly empty) of tokens which
    represent the kinds of conversion this object supports.
    %kw
    useToken
    If a token (a ConverterToken object) is provided here, then the actual
    conversion will be done, and the result returned.
    %note
    Your use of this method will usually come in two parts. First, you'll call
    it with returnTokens set to True. This will return you an iterable of the
    tokens available for this object (this iterable might be empty if no
    conversions are supported).
    
    Second, you'll call it again with a token specified via the useToken
    keyword. This will result in a converted object.
    
    Note that a "token" here is a ConverterToken object as defined in the
    utilities module.
    %end
    """
    
    if kwArgs.get('returnTokens', False):
        return ()
        
    if kwArgs.get('useToken', None):
        return self

def _frombytes(cls, s, **kwArgs):
    """
    Create an instance from the specified binary string, and return it. The
    actual work is done by the fromwalker class method, which this method
    calls.
    
    %start
    %kind
    protocol classmethod
    %return
    A new object, created from the specified binary data.
    %pos
    s
    A string containing the binary data needed to create a living, new object.
    %note
    This is really just a front-end for a call to the class's fromwalker()
    method. A walker is created locally, and is passed along.
    
    Note that any keyword arguments needed by fromwalker should be passed into
    this method, which will pass them along.
    %end
    """
    
    return cls.fromwalker(walkerbit.StringWalkerBit(s), **kwArgs)

def _fromvalidatedbytes(cls, s, **kwArgs):
    """
    Create an instance from the specified binary string, and return it,
    performing validation during the process. The actual work is done by the
    fromvalidatedwalker class method, which this method calls.
    
    %start
    %kind
    protocol classmethod
    %return
    A new object, created from the specified binary data.
    %pos
    s
    A string containing the binary data needed to create a living, new object.
    %kw
    logger
    An optional logger to which messages will be posted. If not provided, the
    system logger will be used, which isn't usually what you want. Get into the
    habit of explicitly providing a logger!
    %note
    This is really just a front-end for a call to the fromvalidatedwalker()
    method of the class. A walker is created locally, and is passed along.
    
    Note that any keyword arguments needed by fromwalker should be passed into
    this method, which will pass them along. This includes the logger.
    %end
    """
    
    return cls.fromvalidatedwalker(walkerbit.StringWalkerBit(s), **kwArgs)

def _getNamer(self):
    """
    Return the current namer, or None.
    
    %start
    %kind
    protocol method
    %return
    The Namer object associated with self, or None if there isn't one.
    %note
    This actually returns the value of a private attribute called '_namer', if
    present.
    
    If there is an attribute called '_editor' associated with self, and there
    is no actual namer assigned yet, one will be made from the _editor object.
    This synthesized namer will not, however, be stored in the '_namer'
    attribute. If you want a name, it's best to create one deliberately.
    %end
    """
    
    nm = self.__dict__.get('_namer', None)
    
    if nm is None and '_editor' in self.__dict__ and self._editor is not None:
        nm = self._editor.getNamer()
    
    return nm

def _groupfrombytes(cls, s, **kwArgs):
    """
    Creates and returns a list of objects by calling the fromwalker method
    until the string is exhausted.
    
    %start
    %kind
    protocol classmethod
    %return
    A list of objects, created until the data source runs out.
    %pos
    s
    A binary string containing the data for one or more objects of class cls.
    A walker will be made from this, and then passed into the groupfromwalker()
    method of cls.
    %note
    See the note for groupfromwalker() for a general caution about using any of
    the groupfrom...() methods.
    %end
    """
    
    return cls.groupfromwalker(walkerbit.StringWalkerBit(s), **kwArgs)

def _groupfromvalidatedwalker(cls, w, **kwArgs):
    """
    Creates and returns a list of objects by calling fromvalidatedwalker()
    until the walker is exhausted. If any item creation fails, None is
    returned.
    
    %start
    %kind
    protocol classmethod
    %return
    A list of objects, created until the data source runs out.
    %pos
    s
    A walker containing the data for one or more objects of class cls. This
    walker provides the bytes for the creation of one or more objects of the
    given class, until the walker runs dry. Validation will be done (that is,
    fromvalidatedwalker() will be called).
    %kw
    logger
    A logger to which errors, warnings, and other diagnostic information will
    be posted.
    %note
    See the note for groupfromwalker() for a general caution about using any of
    the groupfrom...() methods.
    %end
    """
    
    v = []
    logger = kwArgs.pop('logger')
    i = 0
    
    while w.stillGoing():
        itemLogger = logger.getChild("[%d]" % (i,))
        obj = cls.fromvalidatedwalker(w, logger=itemLogger, **kwArgs)
        
        if obj is None:
            return None
        
        v.append(obj)
        i += 1
    
    return v

def _groupfromwalker(cls, w, **kwArgs):
    """
    Creates and returns a list of objects by calling the fromwalker method
    until the walker is exhausted.
    
    %start
    %kind
    protocol classmethod
    %return
    A list of objects, created until the data source runs out.
    %pos
    w
    A walker containing the data for one or more objects of class cls. This
    walker provides the bytes for the creation of one or more objects of the
    given class, until the walker runs dry.
    %note
    In general, when you pass a walker to a method you want the size of the
    walker to be limited in scope. For instance, if you have a walker for the
    binary data for a particular font table, it's not a good idea to pass in a
    walker that goes to the end of the font data; much safer to pass one in
    that has been deliberately limited to just the table in question (using the
    offset and length values in the font's directory)
    
    However, all the groupfrom...() classmethods intentionally violate this.
    While there are rare cases where this is useful (format 4 'kerx' subtables,
    for instance), in general it's safer to just limit your work to single
    objects (and all of their subobject, of course) at a time.
    %end
    """
    
    v = []
    
    while w.stillGoing():
        v.append(cls.fromwalker(w, **kwArgs))
    
    return v

def _nonProtocolMethods(self):
    """
    Returns an iterator over methods exported by self that are not part of the
    standard protocol.
    
    %start
    %kind
    protocol method
    %return
    An iterator over strings representing the methods exported by self that are
    not part of the standard protocol.
    %note
    Method names starting with an underscore will not be included.
    %end
    """
    
    for s in self.__class__.__dict__:
        if s.startswith('_'):
            continue
        
        if s not in _protocolMethods:
            yield s

def _setNamer(self, newNamer):
    """
    Set the specified namer to be used with this object.
    
    %start
    %kind
    protocol method
    %return
    None
    %pos
    newNamer
    The Namer object to be used by self.
    %note
    This method stashes the namer for this object in an attribute named
    '_namer'.
    %end
    """
    
    self.__dict__['_namer'] = newNamer

def _wisdom(self, **kwArgs):
    """
    Returns high-level information about the object.
    
    If the keyword argument "includeProtocol" is True (it's default False) the
    protocol methods will be included as well.
    
    %start
    %kind
    protocol method
    %return
    None
    %kw
    includeProtocol
    Default is False; if True, protocol methods will be included in the method
    list.
    %kw
    tighten
    Default is False; if True, extra blank lines in the output will be
    suppressed.
    %note
    Prints (to stdout) accumulated wisdom about the object, its uses and
    methods.
    %end
    """
    
    tighten = kwArgs.get('tighten', False)
    
    if not _handleExplicitWisdom(self, **kwArgs):
        sm = _summary(self, **kwArgs)
    
        if sm:
            print(sm)
            
            if not tighten:
                print()
    
    if kwArgs.get('includeProtocol', False):
        it = sorted(set(self.nonProtocolMethods()) | _protocolMethods)
        title = "All methods:"
    
    else:
        it = sorted(self.nonProtocolMethods())
        title = "Interesting methods:"
    
    if it:
        print(title)
        
        if not tighten:
            print()
        
        for s in it:
            obj = getattr(self, s)
            
            if isinstance(obj, collections.Callable):
                sm = _summary(getattr(self, s), **kwArgs)
                print("   ", s)
        
                if sm:
                    for ln in sm.splitlines():
                        print("       ", ln)
        
                else:
                    print("        Sorry, no detailed information available.")
                
                if not tighten:
                    print()
            
            else:
                print("   ", s)
                print("        a", type(s))

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def addInvariantMethods(classDict):
    """
    Given a class dict (from a metaclass under construction), add the
    invariant Protocol methods to it.
    
    :param classDict: The class dict under construction
    :type classDict: dict
    :return: None
    """
    
    if 'binaryString' not in classDict:
        classDict['binaryString'] = _binaryString
        
    if 'converted' not in classDict:
        classDict['converted'] = _converted
    
    if 'frombytes' not in classDict:
        classDict['frombytes'] = classmethod(_frombytes)
    
    if 'fromvalidatedbytes' not in classDict:
        classDict['fromvalidatedbytes'] = classmethod(_fromvalidatedbytes)
    
    if 'getNamer' not in classDict:
        classDict['getNamer'] = _getNamer
    
    if 'groupfrombytes' not in classDict:
        classDict['groupfrombytes'] = classmethod(_groupfrombytes)
    
    if 'groupfromvalidatedwalker' not in classDict:
        classDict['groupfromvalidatedwalker'] = classmethod(_groupfromvalidatedwalker)
    
    if 'groupfromwalker' not in classDict:
        classDict['groupfromwalker'] = classmethod(_groupfromwalker)
    
    if 'nonProtocolMethods' not in classDict:
        classDict['nonProtocolMethods'] = _nonProtocolMethods

    if 'setNamer' not in classDict:
        classDict['setNamer'] = _setNamer
    
    if 'wisdom' not in classDict:
        classDict['wisdom'] = _wisdom
    
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
