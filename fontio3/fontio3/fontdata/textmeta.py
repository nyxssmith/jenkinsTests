#
# textmeta.py -- Support for blocks of text
#
# Copyright © 2011-2017 Monotype Imaging Inc. All Rights Reserved.
#

r"""
Metaclass for objects resembling blocks of text (for instance, TSI records
associated with single glyphs). Clients wishing to add fontdata capabilities to
their str-derived classes should specify FontDataMetaclass as the metaclass.

The following class attributes are used to control the various behaviors of
instances of the class:

``attrSpec``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``attrSorted``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``textSpec``
    A dict of specification information for the text, where the keys and their
    associated values are defined in the following list. The listed defaults
    apply if the specified key is not present in the ``textSpec``:
    
    ``text_encoding``
        The encoding for the text when represented as binary data. Note that
        the text in the living object is always simply Unicode.
        
        Default is 'ascii'.
    
    ``text_findcvtsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length) pairs, representing locations within the text block of
        substrings containing CVT indices. The ``cvtsRenumbered()`` method will
        convert these substrings into ints, do the renumbering (using the
        keyword arguments given to ``cvtsRenumbered()``), convert the result
        back to Unicode, and replace the contents within the string.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findfdefsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length) pairs, representing locations within the text block of
        substrings containing FDEF indices. The ``fdefsRenumbered()`` method
        will convert these substrings into ints, do the renumbering (using the
        keyword arguments given to ``fdefsRenumbered()``), convert the result
        back to Unicode, and replace the contents within the string.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findglyphsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length) pairs representing locations within the text block of
        substrings containing glyph indices. The ``glyphsRenumbered()`` method
        will convert these substrings into ints, do the renumbering, convert
        back to Unicode and replace the contents within the string.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findinputglyphsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length) pairs representing locations within the text block of
        substrings containing input glyph indices (note these will, in general,
        be a subset of the glyphs in the generator returned by the
        ``text_findglyphsfunc``). The ``gatheredInputGlyphs()`` method will
        convert these substrings into ints in order to add them to the set it
        returns.
        
        Default is ``None``.
    
    ``text_findnamesfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length) pairs representing locations within the text block of
        substrings containing 'name' table indices. The ``namesRenumbered()``
        method will convert these substrings into ints, do the renumbering,
        convert back to Unicode and replace the contents within the string.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findoutputglyphsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length) pairs representing locations within the text block of
        substrings containing output glyph indices (note these will, in
        general, be a subset of the glyphs in the generator returned by the
        ``text_findglyphsfunc``). The ``gatheredOutputGlyphs()`` method will
        convert these substrings into ints in order to add them to the set it
        returns.
        
        Default is ``None``.
    
    ``text_findpcsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length, infoString) triples representing locations within the text
        block of substrings containing PC values (for instance, jump offsets).
        The ``pcsRenumbered()`` method will take the info returned by calls to
        the generator and use it to do the actual PC renumbering in the text.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findpointsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length, glyphIndex) triples representing locations within the text
        block of substrings containing point indices. The
        ``pointsRenumbered()`` method will convert these substrings into ints,
        do the renumbering, convert back to Unicode and replace the contents
        within the string.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findscalablesfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length, *xynone*, round) tuples (*xynone* is one of the strings ``'x'``
        or ``'y'``, or the value ``None``). These tuples represent locations
        within the text block of substrings containing numeric and scalable
        values. The ``scaled()`` method will convert these substrings into
        floats, do the scaling (if indicated by the ``scaleOnlyInX`` or
        ``scaleOnlyInY`` flags), round the values (if indicated, and in
        accordance with the ``text_python3rounding`` flag), convert back to
        Unicode and replace the contents within the string.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findstoragefunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over (offset,
        length) pairs, representing locations within the text block of
        substrings containing storage indices. The ``storageRenumbered()``
        method will convert these substrings into ints, do the renumbering
        (using the keyword arguments given to ``storageRenumbered()``), convert
        the result back to Unicode, and replace the contents within the string.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_findtransformpairsfunc``
        If specified, should be a function taking the string and arbitrary
        keyword arguments. The function should return a generator over
        (xOffset, xLength, yOffset, yLength, round) tuples. These tuples
        represent locations within the text block of substrings containing
        numeric values for transformation. The ``transformed()`` method will
        convert these substrings into floats, transform them, round the results
        (if indicated, and in accordance with the ``text_python3rounding``
        flag), convert back to Unicode, and replace the contents within the
        string.

        If the offset is ``None`` the corresponding length is interpreted as a
        constant value for the purposes of constructing the (x, y) point for
        transformation. In this case, no string part is changed for that
        offset.

        One keyword argument is automatically passed along to this func:
        ``origObj``, which is a reference to ``self``. The string passed in is
        a simple Unicode string, so this ``origObj`` argument may be used to
        access other data from the original object.
        
        Default is ``None``.
    
    ``text_lineending``
        The line ending to be used at ``buildBinary()`` time. Note that at
        ``fromwalker()`` time any line ending is accepted and converted to the
        Python-native '\n' in the living data.
        
        Note this is a Unicode, not a bytes object.
        
        Default is '\n'.
    
    ``text_mergeappend``
        If True then the strings for the two objects will simply be
        concatentated to create the string for the merged object. This flag
        does not affect attribute merging.
        
        Default is False.
    
    ``text_mergefunc``
        If specified, should be a function taking two objects (not just
        strings), and variable keyword arguments. The function will return a
        string (not an object), which will be used along with the merged
        attributes (handled directly in ``merged()``) to create the output
        object.

        If not specified, only attribute merging will be done, unless
        ``text_mergeappend`` is specified.
        
        Default is ``None``.
    
    ``text_nobinarystake``
        If True, the ``buildBinary()`` call will not start with a staking;
        otherwise, by default it will.
        
        Default is False.
    
    ``text_prevalidatedglyphset``
        A set or frozenset containing glyph indices which are to be considered
        valid, even though they exceed the font's glyph count. This is useful
        for passing ``0xFFFF`` values through validation for state tables,
        where that glyph code is used to indicate the deleted glyph.
        
        There is no default.
    
    ``text_python3rounding``
        If True, the Python 3 round function will be used. If False (the
        default), old-style Python 2 rounding will be done. This affects both
        scaling and transforming if one of the rounding options is used.
        
        Default is False.
    
    ``text_recalculatefunc``
        If provided, a function taking the string and arbitrary keyword
        arguments. It should returns a pair, the first value of which is True
        or False, depending on whether the value changed as a result of
        recalculation. The second value is the new string (not object; that
        will be constructed by the ``recalculated()`` method, which also takes
        the attributes into account).
        
        Default is ``None``.
    
    ``text_roundfunc``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result, or ``None`` to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``text_validatecode_namenotintable``
        The code to be used for logging when a name index is not actually
        present in the ``'name'`` table.
        
        Default is ``'G0042'``.
    
    ``text_validatecode_toolargecvt``
        The code to be used for logging when a CVT index is used that is
        greater than or equal to the number of CVTs in the font.
        
        Default is ``'G0029'``.
    
    ``text_validatecode_toolargeglyph``
        The code to be used for logging when a glyph index is used that is
        greater than or equal to the number of glyphs in the font.
        
        Default is ``'G0005'``.
    
    ``text_validatefunc``
        A function taking one positional argument, the value, and an arbitrary
        number of keyword arguments. The function returns True if the object is
        valid (that is, if no errors are present).
        
        There is no default.
    
    ``text_validatefunc_partial``
        A function taking one positional argument, the value, and an arbitrary
        number of keyword arguments. The function returns True if the object is
        valid (that is, if no errors are present). This function does not need
        to check for predetermined things (like glyph index out of bounds.
        
        There is no default.
    
    ``text_wisdom``
        A string encompassing a sensible description of the object as a whole,
        including how it is used.
        
        There is, alas, no default for wisdom.
"""

# System imports
import logging
import math
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, invariants
from fontio3.utilities import pp, span

# -----------------------------------------------------------------------------

#
# Constants
#

validTextSpecKeys = frozenset([
    'text_encoding',
    'text_findcvtsfunc',
    'text_findfdefsfunc',
    'text_findglyphsfunc',
    'text_findinputglyphsfunc',
    'text_findnamesfunc',
    'text_findoutputglyphsfunc',
    'text_findpcsfunc',
    'text_findpointsfunc',
    'text_findscalablesfunc',
    'text_findstoragefunc',
    'text_findtransformpairsfunc',
    'text_lineending',
    'text_mergeappend',
    'text_mergefunc',
    'text_prevalidatedglyphset',
    'text_python3rounding',
    'text_recalculatefunc',
    'text_roundfunc',
    'text_validatecode_namenotintable',
    'text_validatecode_toolargecvt',
    'text_validatecode_toolargeglyph',
    'text_validatefunc',
    'text_validatefunc_partial',
    'text_wisdom'])

# -----------------------------------------------------------------------------

#
# Methods
#

def CM_fromwalker(cls, w, **kwArgs):
    r"""
    Creates a new instance of the class from the specified walker.

    :param w: A walker for the binary data to be consumed in making the new
        instance
    :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
        or equivalent
    :param kwArgs: Optional keyword arguments
    :return: The new instance
    :rtype: *cls*

    .. note::
    
        This is a class method!
    
    All the remaining contents of ``w`` will be used, so if the client wishes
    to limit it then a ``subWalker`` with the appropriate limit should be
    passed to thie method.

    A word about line endings: if what comes from ``w`` contains no newlines of
    any flavor then the returned object won't contain them either. If newlines
    of any flavor are present, however, they will be converted to the common
    Python newline '\\n', and the last line will have a newline, even if it
    didn't in the source text.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> Test1.frombytes(b'abcdefg')
    Test1('abcdefg')
    >>> Test1.frombytes(utilities.fromhex("41 0D 42 0A 43 0D 0A"))
    Test1('A\nB\nC\n')
    """
    
    s = str(w.rest(), cls._TEXTSPEC.get('text_encoding', 'ascii'))
    v = s.splitlines()
    
    if len(v) > 1:
        v.append('')
        s = '\n'.join(v)
    
    return cls(s, **utilities.filterKWArgs(cls, kwArgs))

def M_asImmutable(self, **kwArgs):
    """
    Returns a simple tuple with the object's contents, suitable for use as
    a dict key or in a set.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: The immutable version (or self, if it's already immutable).
    
    The following ``kwArgs`` are supported:
    
    ``memo``
        A dict mapping object IDs to the immutable value for the object. This
        only applies to deep objects. Note that it's safe to use ``id(...)`` in
        this case, since the ``asImmutable()`` call does not do any object
        mutation in situ (it creates lots of new objects, but no reuse of an
        existing ID will ever happen while the call is going on).
        
        This is optional; if one is not provided, a temporary one will be used.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> Test1("This is some text").asImmutable()
    ('Test1', 'This is some text')
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    ...     attrSpec = {'a': {'attr_asimmutablefunc': tuple}}
    >>> Test2("Some more text", a=[1, 2, 3]).asImmutable()
    ('Test2', 'Some more text', ('a', (1, 2, 3)))
    """
    
    AS = self._ATTRSPEC
    s = super(self.__class__, self).__str__()
    
    if not AS:
        return (type(self).__name__, s)
    
    return (
      (type(self).__name__, s) +
      attrhelper.M_asImmutable(AS, self._ATTRSORT, self.__dict__, **kwArgs))

def M_buildBinary(self, w, **kwArgs):
    r"""
    Adds the binary content for the object to the specified writer.

    :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
    :param kwArgs: Optional keyword arguments
    :return: None
    
    The lines will be joined by ``text_lineending``, and ``text_encoding`` will
    be used as the binary encoding (remember that the living object is always
    kept in Unicode).
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_lineending': '\r'}
    
    >>> obj = Test1.frombytes(b"Line 1\nLine 2\r\nLine 3\rLine 4\n\n\nLine 5")
    >>> print(repr(obj))
    Test1('Line 1\nLine 2\nLine 3\nLine 4\n\n\nLine 5\n')
    
    >>> bs = obj.binaryString()
    >>> print(repr(bs))
    b'Line 1\rLine 2\rLine 3\rLine 4\r\r\rLine 5'
    
    >>> utilities.hexdump(bs)
           0 | 4C69 6E65 2031 0D4C  696E 6520 320D 4C69 |Line 1.Line 2.Li|
          10 | 6E65 2033 0D4C 696E  6520 340D 0D0D 4C69 |ne 3.Line 4...Li|
          20 | 6E65 2035                                |ne 5            |
    """
    
    TS = self._TEXTSPEC
    
    if not TS.get('text_nobinarystake', False):
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
    
    s = TS.get('text_lineending', '\n').join(self.splitlines())
    b = s.encode(TS.get('text_encoding', 'ascii'))
    w.addString(b)

def M_checkInput(self, valueToCheck, **kwArgs):
    """
    Check appropriateness of a value for ``self``.
 
    :param valueToCheck: The value to be checked
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if appropriate, False otherwise
    :rtype: bool
    
    This method is used to check the appropriateness of a value for the given
    kind of object. So for example, if an ``'OS/2'`` weight-class value is
    supposed to be a number from 1 to 1000, this method's implementation for
    that object will check that specifically.
    
    The following ``kwArgs`` are supported:
    
    ``attrName``
         An optional string, identifying an attribute of the object. If
         specified, this attribute's own ``checkInput()`` method will be called
         with the ``valueToCheck`` value. Otherwise, this object's checking
         function will be used.
    
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...   attrSpec = dict(
    ...     a = dict(
    ...       attr_inputcheckfunc = (lambda x, **k: 0 <= x < 50)))
    >>> t = Test1("This is some text", a=29)
    >>> t.checkInput(11, attrName='a')
    True
    >>> t.checkInput(111, attrName='a')
    False
    """
    
    if kwArgs.get('attrName', ''):
        return attrhelper.M_checkInput(
          self._ATTRSPEC,
          self.__dict__,
          valueToCheck,
          **kwArgs)
    
    return True

def M_coalesced(self, **kwArgs):
    """
    Return new object representing ``self`` with duplicates coerced to the
    same object.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with duplicates coalesced
    :rtype: Same as ``self``

    Font data often comprises multiple parts that happen to be the same. One
    example here is the platform 0 (Unicode) and platform 3 (Microsoft)
    ``'cmap'`` subtables, which often have exactly the same data. The binary
    format for the ``'cmap'`` table permits sharing here (each table is
    actually an offset, so the two offsets here can refer to the same data).
    This method is used to force this sharing to occur, if possible.

    It's important to remember that fontio3 deals with high-level, more
    abstract representations of font data. In order to allow for both the
    sharing and non-sharing cases, this method uses the object ID (that is, the
    results of calling the built-in ``id()`` function) as a clue. If two
    objects contained in some container object share the same ID, then they'll
    be shared in the binary representation.

    Knowing this, it's now easy to see what this method does. It compares any
    protocol objects it contains, and if it finds some that compare equal but
    have different IDs, it "coalesces" them to refer to the same ID. This will
    then ensure shared references to the same data in the binary data, once
    it is written.
    
    In the returned result, if two objects are equal then they will be the same
    object (i.e. an ``is`` test will return True).

    The following ``kwArgs`` are supported:

    ``pool``
        A dict mapping immutable representations of objects to the objects
        themselves. This is optional; a new, empty dict will be used if one is
        not specified.
    
        This is useful if you want to coalesce objects across many higher-level
        objects.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {'attr_asimmutablefunc': tuple},
    ...       'b': {'attr_asimmutablefunc': tuple}}
    >>> t = Test1("This is some text", a=[1, 2, 3], b = [1] + [2, 3])
    >>> t.a is t.b
    False
    >>> tCoal = t.coalesced()
    >>> tCoal == t
    True
    >>> tCoal.a is tCoal.b
    True
    """
    
    pool = kwArgs.pop('pool', {})  # allows for sharing across objects
    
    dNew = attrhelper.M_coalesced(
      self._ATTRSPEC,
      self.__dict__,
      pool,
      **kwArgs)
    
    return type(self)(super(self.__class__, self).__str__(), **dNew)

def M_compacted(self, **kwArgs):
    """
    Returns a new object which has been compacted.
    
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A new compacted object
    :rtype: Same as ``self``
    
    This method really only affects attributes.
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_compactremovesfalses': True}
    >>> class Top(str, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_followsprotocol': True}}
    >>> t = Top("Some text", a=Bottom([2, False, 0, None, [], 3]))
    >>> print(t)
    Some text, a = (2, False, 0, None, [], 3)
    >>> print(t.compacted())
    Some text, a = (2, 3)
    """
    
    dNew = attrhelper.M_compacted(self._ATTRSPEC, self.__dict__, **kwArgs)
    return type(self)(super(self.__class__, self).__str__(), **dNew)

def M_cvtsRenumbered(self, **kwArgs):
    """
    Return new object with CVT index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with CVT indices renumbered
    :rtype: Same as ``self``

    CVT indices are used in TrueType hinting, and can appear in several
    different tables. If you are merging fonts together, you might want to
    renumber the CVTs in the various input fonts so they don't collide. This
    method helps you do that.

    The following ``kwArgs`` are supported:

    ``cvtDelta``
        An optional integer value (possibly negative) that will be added to the
        old CVT index to obtain the new one.

    ``cvtMappingFunc``
        This is optional. If specified, it should be a function taking one
        positional argument (the CVT index), and should allow for arbitrary
        keyword arguments. It returns the new CVT index.

    ``keepMissing``
        If True (the default) then any values not explicitly included in the
        ``oldToNew`` dict will be left unchanged. If False, those values will
        be replaced with ``None``.

    ``oldToNew``
        A dict mapping old CVT indices to new ones. Note that it's OK for this
        dict to not map every single old CVT index; what happens if this occurs
        is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``cvtDelta``, ``cvtMappingFunc``, or
      ``oldToNew``.
    
    One special case for classes derived from this metaclass: if the caller
    sets ``keepMissing`` to False, and any CVT indices cannot be renumbered,
    they will be replaced with the string ">>>CANNOT RENUMBER<<<".
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findcvtsfunc': func}
    
    >>> obj = Test1("Talking about CVTs 13, 14, and 29")
    >>> print(obj)
    Talking about CVTs 13, 14, and 29
    >>> print(obj.cvtsRenumbered(cvtDelta=80))
    Talking about CVTs 93, 94, and 109
    >>> d = {13: 300, 14: 350}
    >>> print(obj.cvtsRenumbered(oldToNew=d))
    Talking about CVTs 300, 350, and 29
    >>> print(obj.cvtsRenumbered(oldToNew=d, keepMissing=False))
    Talking about CVTs 300, 350, and >>>CANNOT RENUMBER<<<
    >>> f = (lambda n,**k: (n + 50 if n % 2 else n + 400))
    >>> print(obj.cvtsRenumbered(cvtMappingFunc=f))
    Talking about CVTs 63, 414, and 79
    """
    
    g = self._TEXTSPEC.get('text_findcvtsfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._cvtsRenumbered_helper,
          **kwArgs)
    
    # Now do attributes
    dNew = attrhelper.M_cvtsRenumbered(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_fdefsRenumbered(self, **kwArgs):
    """
    Return new object with FDEF index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with FDEF indices renumbered
    :rtype: Same as ``self``

    FDEF (Function DEFinition) indices are used in TrueType hinting, and can
    appear in several different tables. If you are merging fonts together, you
    might want to renumber the FDEFs in the various input fonts so they don't
    collide. This method helps you do that.

    The following ``kwArgs`` are supported:

    ``fdefMappingFunc``
        This is optional. If specified, it should be a function taking one
        positional argument (the FDEF index), and should allow for arbitrary
        keyword arguments. It returns the new FDEF index.

    ``keepMissing``
        If True (the default) then any values not explicitly included in the
        ``oldToNew`` dict will be left unchanged. If False, those values will
        be replaced with ``None``.

    ``oldToNew``
        A dict mapping old FDEF indices to new ones. Note that it's OK for this
        dict to not map every single old FDEF index; what happens if this
        occurs is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``fdefMappingFunc`` or ``oldToNew``.
    
    One special case for classes derived from this metaclass: if the caller
    sets ``keepMissing`` to False, and any FDEF indices cannot be renumbered,
    they will be replaced with the string ">>>CANNOT RENUMBER<<<".
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findfdefsfunc': func}
    
    >>> obj = Test1("Talking about FDEFs 13, 14, and 29")
    >>> print(obj)
    Talking about FDEFs 13, 14, and 29
    >>> d = {13: 300, 14: 350}
    >>> print(obj.fdefsRenumbered(oldToNew=d))
    Talking about FDEFs 300, 350, and 29
    >>> print(obj.fdefsRenumbered(oldToNew=d, keepMissing=False))
    Talking about FDEFs 300, 350, and >>>CANNOT RENUMBER<<<
    >>> f = (lambda n,**k: (n + 50 if n % 2 else n + 400))
    >>> print(obj.fdefsRenumbered(fdefMappingFunc=f))
    Talking about FDEFs 63, 414, and 79
    """
    
    g = self._TEXTSPEC.get('text_findfdefsfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._fdefsRenumbered_helper,
          **kwArgs)
    
    # Now do attributes
    dNew = attrhelper.M_fdefsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_gatheredInputGlyphs(self, **kwArgs):
    """
    Return a set of glyph indices for those glyphs used as inputs to some
    process.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of glyph indices
    :rtype: set

    Any place where glyph indices are the inputs to some rule or process, we
    call those *input glyphs*. Consider the case of *f* and *i* glyphs that are
    present in a ``GSUB`` ligature action to create an *fi* ligature. The *f*
    and *i* glyphs are the input glyphs here; the *fi* ligature glyph is the
    output glyph. Note that this method works for both OpenType and AAT fonts.
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findinputglyphsfunc': func}
    
    >>> s = "It's glyph 19 and also 145, plus 263, cool."
    >>> sorted(Test1(s).gatheredInputGlyphs())
    [19, 145, 263]
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findinputglyphsfunc': func}
    ...     attrSpec = dict(
    ...         a = {'attr_renumberdirect': True},
    ...         b = {'attr_renumberdirect': True, 'attr_isoutputglyph': True})
    
    >>> obj = Test2("It's glyphs 141, 142, and 192", a=200, b=201)
    >>> sorted(obj.gatheredInputGlyphs())
    [141, 142, 192, 200]
    """
    
    f = self._TEXTSPEC.get('text_findinputglyphsfunc', None)
    r = set()
    
    if f is not None:
        for start, count in f(super(self.__class__, self).__str__(), **kwArgs):
            r.add(int(self[start:start+count]))
    
    rAttr = attrhelper.M_gatheredInputGlyphs(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    return r | rAttr

def M_gatheredLivingDeltas(self, **kwArgs):
    """
    Return a set of :py:class:`~fontio3.opentype.living_variations.LivingDeltas`
    objects contained in ``self``; this really only applies to the attributes,
    since the text string cannot contain these objects.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of ``LivingDeltas`` objects.
    :rtype: set

    This method is used to gather all deltas used in variable fonts so they may
    be converted into an :title-reference:`OpenType 1.8` ``ItemVariationStore``.

    You will rarely need to call this method.
    
    A note about the following doctests: for simplicity, I'm using simple
    integers in lieu of actual LivingDeltas objects. Since those objects are
    immutable, the effect is the same. Clients of this method in real code
    should, of course, only use actual LivingDeltas objects!
    
    >>> class Test(str, metaclass=FontDataMetaclass):
    ...   attrSpec = dict(
    ...     a = dict(attr_islivingdeltas = True),
    ...     b = dict())
    >>> obj = Test("hi there", a=4, b=76)
    >>> sorted(obj.gatheredLivingDeltas())
    [4]
    """
    
    return attrhelper.M_gatheredLivingDeltas(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)

def M_gatheredMaxContext(self, **kwArgs):
    """
    Return an integer representing the ``'OS/2'`` maximum context value.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The maximum context
    :rtype: int

    This method is used to recursively walk OpenType or AAT tables to obtain
    the largest matching context used anywhere.

    You will rarely need to call this method.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_maxcontextfunc = (lambda obj: obj[0])))
    >>> Test1("Fred", x = [8, 1, 4]).gatheredMaxContext()
    8
    """
    
    return attrhelper.M_gatheredMaxContext(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)

def M_gatheredOutputGlyphs(self, **kwArgs):
    """
    Return a set of glyph indices for those glyphs generated as outputs from
    some process.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of glyph indices
    :rtype: set

    Any place where glyph indices are the outputs from some rule or process, we
    call those *output glyphs*. Consider the case of *f* and *i* glyphs that
    are present in a ``GSUB`` ligature action to create an *fi* ligature. The
    *f* and *i* glyphs are the input glyphs here; the *fi* ligature glyph is
    the output glyph. Note that this method works for both OpenType and AAT
    fonts.
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findoutputglyphsfunc': func}
    
    >>> sorted(Test1("Oh 12 and 90 and 4312 are good.").gatheredOutputGlyphs())
    [12, 90, 4312]
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findoutputglyphsfunc': func}
    ...     attrSpec = dict(
    ...         a = {'attr_renumberdirect': True},
    ...         b = {'attr_renumberdirect': True, 'attr_isoutputglyph': True})
    
    >>> obj = Test2("It's glyphs 141, 142, and 192", a=200, b=201)
    >>> sorted(obj.gatheredOutputGlyphs())
    [141, 142, 192, 201]
    """
    
    f = self._TEXTSPEC.get('text_findoutputglyphsfunc', None)
    r = set()
    
    if f is not None:
        for start, count in f(super(self.__class__, self).__str__(), **kwArgs):
            r.add(int(self[start:start+count]))
    
    rAttr = attrhelper.M_gatheredOutputGlyphs(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    return r | rAttr

def M_gatheredRefs(self, **kwArgs):
    """
    Return a dict with ``Lookup`` objects contained within ``self``.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A dict mapping ``id(lookupObj)`` to the ``lookupObj``
    :rtype: dict

    When constructing a
    :py:class:`~fontio3.opentype.lookuplist.LookupList` you will
    need to gather all the
    :py:class:`~fontio3.opentype.lookup.Lookup` objects that are
    present in self. Often these will be duplicated: the same effect might be
    present in many different chaining contextual substitution rules, for
    example. By mapping the ``id()`` of the ``Lookup`` as the key in the
    returned dict, this duplication can be eliminated, just yielding the actual
    set of unique ``Lookup`` objects being used.

    You will rarely need to call this method.
    
    >>> class Test(str, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_islookup = True))
    >>> look1 = object()
    >>> look2 = object()
    >>> t = Test("hi there", a=Test(-0.75, a=None, b=look1), b=look2)
    >>> d = t.gatheredRefs()
    >>> len(d)
    2
    >>> id(look1) in d, id(look2) in d
    (True, True)
    """
    
    return attrhelper.M_gatheredRefs(self._ATTRSPEC, self.__dict__, **kwArgs)

def M_glyphsRenumbered(self, oldToNew, **kwArgs):
    """
    Returns a new object with glyphs renumbered.
    
    :param oldToNew: Map from old to new glyph index
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with glyphs renumbered.
    :rtype: Same as ``self``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        None.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.

    One special case for classes derived from this metaclass: if the caller
    sets ``keepMissing`` to False, and any glyphs are not in ``oldToNew``,
    their strings will be replaced with the string ">>>CANNOT RENUMBER<<<".
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findglyphsfunc': func}
    
    >>> oldToNew = {13: 300, 14: 350}
    >>> obj = Test1("Talking about glyphs 13, 14, and 29")
    >>> print(obj)
    Talking about glyphs 13, 14, and 29
    >>> print(obj.glyphsRenumbered(oldToNew))
    Talking about glyphs 300, 350, and 29
    >>> print(obj.glyphsRenumbered(oldToNew, keepMissing=False))
    Talking about glyphs 300, 350, and >>>CANNOT RENUMBER<<<
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findglyphsfunc': func}
    ...     attrSpec = {'a': {'attr_renumberdirect': True}}
    >>> obj = Test2("It's glyph 13! Yay!", a=14)
    >>> print(obj)
    It's glyph 13! Yay!, a = 14
    >>> print(obj.glyphsRenumbered(oldToNew))
    It's glyph 300! Yay!, a = 350
    """
    
    g = self._TEXTSPEC.get('text_findglyphsfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._glyphsRenumbered_helper,
          oldToNew = oldToNew,
          keepMissing = kwArgs.get('keepMissing', True),
          trackDeltas = kwArgs.get('trackDeltas', {}))
    
    # Now do attributes
    dNew = attrhelper.M_glyphsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_hasCycles(self, **kwArgs):
    """
    Determines if self is self-referential.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if self-referential cycles are present; False otherwise
    :rtype: bool
    
    The following ``kwArgs`` are supported:
    
    ``activeCycleCheck``
        A set of ``id()`` values of deep objects. This is used to track deep
        usage; if at any level an object is encountered whose ``id()`` value is
        already present in this set, the function returns True. Note that it's
        safe to use object ID values, since this call does not mutate any data.
    
    ``memo``
        An optional set. This is used to store the ID values of objects that
        have already been found to have no cycles. It speeds up the process.
    """
    
    dACC = kwArgs.pop('activeCycleCheck', set())
    
    return attrhelper.M_hasCycles(
      self._ATTRSPEC,
      self.__dict__,
      activeCycleCheck = (dACC | {id(self)}),
      **kwArgs)

def M_isValid(self, **kwArgs):
    """
    Determine object validity.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if valid, False otherwise
    :rtype: bool
    
    The ``isValid()`` method represents the second half of the validation
    process. It checks the living object for internal consistency. The first
    half of the process is done while the object is being constructed, via one
    of the ``fromvalidated...()`` methods.
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        An :py:class:`~fontio3.fontedit.Editor`-class object. This is required.

    ``fontGlyphCount``
        The number of glyphs in the font. Will be used to check any glyph
        indices for validity. If not specified, the value will be read from the
        editor's ``'maxp'`` table, if present; otherwise, a default value of
        ``0x10000`` is used.
    
    ``logger``
        A logger to which errors will be posted. You should use a logger of the
        sort returned by :py:func:`~fontio3.utilities.makeDoctestLogger`.
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findglyphsfunc': func}
    
    >>> logger = utilities.makeDoctestLogger("Test1")
    >>> e = utilities.fakeEditor(0x10000)
    >>> obj = Test1("I refer to glyphs 200, 400, and 450.")
    >>> obj.isValid(logger=logger, fontGlyphCount=1000, editor=e)
    True
    >>> obj.isValid(logger=logger, fontGlyphCount=350, editor=e)
    Test1 - ERROR - Glyph index 400 is too large.
    Test1 - ERROR - Glyph index 450 is too large.
    False
    
    >>> def valFunc(s, **kwArgs):
    ...     if "gurkle" not in s:
    ...         logger = kwArgs['logger']
    ...         logger.error(('Vx', (), "Objects must have a gurkle in them."))
    ...         return False
    ...     return True
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_validatefunc': valFunc}
    
    >>> logger = utilities.makeDoctestLogger("Test2")
    >>> Test2("The gurkle is a happy beast.").isValid(logger=logger, editor=e)
    True
    >>> Test2("The hurkle is a happy beast.").isValid(logger=logger, editor=e)
    Test2 - ERROR - Objects must have a gurkle in them.
    False
    """
    
    TS = self._TEXTSPEC
    r = True
    s = super(self.__class__, self).__str__()
    fontGlyphCount = kwArgs.get('fontGlyphCount')
    
    if 'editor' in kwArgs:
        editor = kwArgs['editor']
        hasMaxp = (editor is not None) and editor.reallyHas(b'maxp')
        
        if hasMaxp:
            if fontGlyphCount is None:
                fontGlyphCount = editor.maxp.numGlyphs
            
            if hasattr(editor.maxp, 'maxStorage'):
                maxStorage = editor.maxp.maxStorage
            else:
                maxStorage = 0x10000
            
        else:
            if fontGlyphCount is None:
                fontGlyphCount = 0x10000
            
            maxStorage = 0x10000
        
        if (editor is not None) and editor.reallyHas(b'name'):
            namesInTable = {x[-1] for x in editor.name}
        else:
            namesInTable = set()
    
    else:
        editor = None
        maxStorage = 0x10000
        namesInTable = set()
        
        if fontGlyphCount is None:
            fontGlyphCount = 0x10000
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        useName = __name__[__name__.rfind('.')+1:]
        logger = logging.getLogger().getChild(useName)
    
    f = TS.get('text_validatefunc', None)
    
    if f is not None:
        r = f(s, logger=logger, **kwArgs)
    
    else:
        fp = TS.get('text_validatefunc_partial', None)
        
        if fp is not None:
            r = fp(s, logger=logger, **kwArgs)
        
        f = TS.get('text_findglyphsfunc', None)
        
        if f is not None:
            pvs = TS.get('text_prevalidatedglyphset', set())
            
            for start, count in f(s, **kwArgs):
                n = int(s[start:start+count])
                
                if (n not in pvs) and (n >= fontGlyphCount):
                    logger.error((
                      TS.get('text_validatecode_toolargeglyph', 'G0005'),
                      (n,),
                      "Glyph index %d is too large."))
                    
                    r = False
        
        f = TS.get('text_findnamesfunc', None)
        
        if f is not None:
            for start, count in f(s, **kwArgs):
                n = int(s[start:start+count])
                
                if n not in namesInTable:
                    logger.error((
                      TS.get('text_validatecode_namenotintable', 'G0042'),
                      (n,),
                      "Name table index %d not present in 'name' table."))
                    
                    r = False
        
        f = TS.get('text_findcvtsfunc', None)
        
        if (
          (f is not None) and
          (editor is not None) and
          (editor.reallyHas(b'cvt '))):
            
            for start, count in f(s, **kwArgs):
                n = int(s[start:start+count])
                
                if n >= len(editor[b'cvt ']):
                    logger.error((
                      TS.get('text_validatecode_toolargecvt', 'G0029'),
                      (n,),
                      "CVT index %d is not in the CVT table."))
                    
                    r = False
        
        f = TS.get('text_findstoragefunc', None)
        
        if f is not None:
            for start, count in f(s, **kwArgs):
                n = int(s[start:start+count])
                
                if n > maxStorage:
                    logger.error((
                      'E6047',
                      (n, maxStorage),
                      "The storage index %d is greater than the font's "
                      "defined maximum of %d."))
                    
                    r = False
    
    rAttr = attrhelper.M_isValid(
      self._ATTRSPEC,
      self.__dict__,
      logger = logger,
      **kwArgs)
    
    return r and rAttr

def M_merged(self, other, **kwArgs):
    """
    Returns a new object representing the merger of ``other`` into ``self``.
    
    :param other: The object to be merged into ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object representing the merger
    
    The following ``kwArgs`` are supported:
    
    ``replaceWhole``
        An optional Boolean, default False. If True, then in contexts where
        it's appropriate no merge will be attempted; the data in ``other`` will
        simply replace that of ``self`` in the merged object.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    
    >>> print(Test1("abc").merged(Test1("abc")))
    abc
    >>> print(Test1("abc").merged(Test1("def")))
    abc
    >>> print(Test1("abc").merged(Test1("def"), replaceWhole=True))
    def
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_mergeappend': True}
    
    >>> print(Test2("abc").merged(Test2("abc")))
    abcabc
    >>> print(Test2("abc").merged(Test2("def")))
    abcdef
    
    >>> def func(obj1, obj2, **kwArgs):
    ...     s1 = super(obj1.__class__, obj1).__str__()
    ...     s2 = super(obj2.__class__, obj2).__str__()
    ...     return ''.join([s1[:5], '(', s2, ')', s1[5:]])
    
    >>> class Test3(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_mergefunc': func}
    
    >>> print(Test3("abcdefghijkl").merged(Test3("12345")))
    abcde(12345)fghijkl
    """
    
    TS = self._TEXTSPEC
    s = super(self.__class__, self).__str__()
    f = TS.get('text_mergefunc', None)
    
    if f is not None:
        s = f(self, other, **kwArgs)
    elif TS.get('text_mergeappend', False):
        s += super(other.__class__, other).__str__()
    elif (self != other) and kwArgs.get('replaceWhole', False):
        s = super(other.__class__, other).__str__()
    
    # Now do attributes
    dNew = attrhelper.M_merged(
      self._ATTRSPEC,
      self.__dict__,
      other.__dict__,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_namesRenumbered(self, oldToNew, **kwArgs):
    """
    Return a new object with ``'name'`` table references renumbered.
    
    :param oldToNew: A dict mapping old to new indices
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with names renumbered
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        ``None``.
    
    One special case for classes derived from this metaclass: if the caller
    sets ``keepMissing`` to False, and any glyphs are not in ``oldToNew``,
    their strings will be replaced with the string ">>>CANNOT RENUMBER<<<".
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findnamesfunc': func}
    
    >>> oldToNew = {13: 300, 14: 350}
    >>> obj = Test1("Talking about 'name' indices 13, 14, and 29")
    >>> print(obj)
    Talking about 'name' indices 13, 14, and 29
    >>> print(obj.namesRenumbered(oldToNew))
    Talking about 'name' indices 300, 350, and 29
    >>> print(obj.namesRenumbered(oldToNew, keepMissing=False))
    Talking about 'name' indices 300, 350, and >>>CANNOT RENUMBER<<<
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findnamesfunc': func}
    ...     attrSpec = {'a': {'attr_renumbernamesdirect': True}}
    >>> obj = Test2("It's name 13! Yay!", a=14)
    >>> print(obj)
    It's name 13! Yay!, a = 14
    >>> print(obj.namesRenumbered(oldToNew))
    It's name 300! Yay!, a = 350
    """
    
    g = self._TEXTSPEC.get('text_findnamesfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._namesRenumbered_helper,
          oldToNew = oldToNew,
          keepMissing = kwArgs.get('keepMissing', True),
          trackDeltas = kwArgs.get('trackDeltas', {}))
    
    # Now do attributes
    dNew = attrhelper.M_namesRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start, "testInfoString")
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findpcsfunc': func}
    
    >>> mapData = {"testInfoString": ((12, 2), (40, 3), (67, 6))}
    >>> obj = Test1("The PCs are 5, 12, 50, and also 100.")
    >>> print(obj)
    The PCs are 5, 12, 50, and also 100.
    
    >>> print(obj.pcsRenumbered(mapData))
    The PCs are 5, 14, 53, and also 106.
    """
    
    g = self._TEXTSPEC.get('text_findpcsfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._pcsRenumbered_helper,
          mapData = mapData,
          trackDeltas = kwArgs.get('trackDeltas', {}))
    
    # Now do attributes
    dNew = attrhelper.M_pcsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_pointsRenumbered(self, mapData, **kwArgs):
    """
    Returns a new object with point indices renumbered.
    
    :param mapData: Dict mapping glyph index to an ``oldToNew`` dict
    :type mapData: dict(int, dict(int, int))
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with points renumbered
    
    The following ``kwArgs`` are supported:
    
    ``glyphIndex``
        This is required. It is a glyph index, used to select which oldToNew
        dict is to be used for the mapping.
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start, 444)  # glyph 444
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findpointsfunc': func}
    
    >>> mapData = {440: {10: 12, 12: 15, 15: 10}, 444: {10: 25, 25: 10}}
    >>> obj = Test1("The points are 10, 19, and also 25.")
    >>> print(obj)
    The points are 10, 19, and also 25.
    
    >>> print(obj.pointsRenumbered(mapData))
    The points are 25, 19, and also 10.
    """
    
    g = self._TEXTSPEC.get('text_findpointsfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._pointsRenumbered_helper,
          mapData = mapData,
          trackDeltas = kwArgs.get('trackDeltas', {}))
    
    # Now do attributes
    dNew = attrhelper.M_pointsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_pprint(self, **kwArgs):
    """
    Pretty-print the object and its attributes.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    
    The following ``kwArgs`` are supported:
    
    ``indent``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``indentDelta``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``label``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``maxWidth``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``namer``
        An optional :py:class:`~fontio3.utilities.namer.Namer` object that will
        be used wherever glyph index values are shown.
    
    ``noDataString``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``p``
        An optional :py:class:`~fontio3.utilities.pp.PP` object to which output
        will be sent. If one is not provided, a new ``PP`` object will be
        created, potentially using ``kwArgs`` values of its own.
    
    ``stream``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> sv = [
    ...   "This is the first line",
    ...   "This is the second",
    ...   "And this is a third line that is quite a bit longer."]
    >>> obj = Test1(chr(10).join(sv))
    >>> obj.pprint()
    This is the first line
    This is the second
    And this is a third line that is quite a bit longer.
    
    >>> obj.pprint(indent=2)
      This is the first line
      This is the second
      And this is a third line that is quite a bit longer.
    
    >>> obj.pprint(maxWidth=25)
    This is the first line
    This is the second
    And this is a third line
    that is quite a bit
    longer.
    
    >>> obj.pprint(indent=2, maxWidth=25)
      This is the first line
      This is the second
      And this is a third
      line that is quite a
      bit longer.
    """
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    nm = kwArgs.pop('namer', self.getNamer())
    s = super(self.__class__, self).__str__()
    
    # The following is to ensure that the pprint() output of the main text does
    # not have the attributes, since they're printed separately later in this
    # same method.
    
    p(str(self.encode('utf-8'), 'utf-8'))
    
    # Now do attributes
    attrhelper.M_pprint(self, p, (lambda: nm), **kwArgs)

def M_pprintChanges(self, prior, **kwArgs):
    """
    Displays the changes from ``prior`` to ``self``.
    
    :param prior: The previous object, to be compared to ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    
    The following ``kwArgs`` are supported:
    
    ``indent``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``indentDelta``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``keys``
        An optional tuple of attribute names. Normally, all the attributes
        listed in the ``attrSorted`` tuple are included in the
        ``pprint_changes()`` output. You can override this by providing your
        own tuple of attribute names in this keyword.
    
    ``label``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``maxWidth``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``namer``
        An optional :py:class:`~fontio3.utilities.namer.Namer` object that will
        be used for any glyph index displays.
        
        .. warning::
            
            It is a flaw in the current design of ``pprint_changes()`` that
            this ``Namer`` is used for both ``self`` and ``prior``, even though
            ``prior`` may not have the same glyph repertoire that ``self``
            does. This can result in misleading names being shown. It's safe to
            use as long as you know the glyph repertoires are the same for both
            objects.
    
    ``noDataString``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``p``
        An optional :py:class:`~fontio3.utilities.pp.PP` object to which output
        will be sent. If one is not provided, a new ``PP`` object will be
        created, potentially using ``kwArgs`` values of its own.
    
    ``stream``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> Test1("abcde").pprint_changes(Test1("abc"))
    Appended at end:
      de
    >>> Test1("abc").pprint_changes(Test1("abcde"))
    Deleted from the end:
      de
    >>> Test1("abcxyze").pprint_changes(Test1("abcde"))
    This sequence at new index 3:
      xyz
    replaced this sequence at old index 3:
      d
    """
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    nm = kwArgs.pop('namer', self.getNamer())
    
    if self != prior:
        sSelf = super(self.__class__, self).__str__()
        sPrior = super(prior.__class__, prior).__str__()
        kwArgs.pop('combiner', None)
        p.diff_sequence(sSelf, sPrior, combiner='', **kwArgs)
    
    attrhelper.M_pprintChanges(self, prior.__dict__, p, nm, **kwArgs)

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        This is required, and should be an
        :py:class:`~fontio3.fontedit.Editor`-class object.
    
    >>> def func(s, **kwArgs):
    ...     sNew = s[::-1]
    ...     return s != sNew, sNew
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_recalculatefunc': func}
    
    >>> print(Test1("fred").recalculated())
    derf
    >>> print(Test1("aba").recalculated())
    aba
    """
    
    func = self._TEXTSPEC.get('text_recalculatefunc', None)
    s = super(self.__class__, self).__str__()
    
    if func is not None:
        changed, s = func(s, **kwArgs)
    
    # Now do attributes
    dNew = attrhelper.M_recalculated(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_scaled(self, scaleFactor, **kwArgs):
    """
    Returns a object with FUnit distances scaled.
    
    :param float scaleFactor: The scale factor to use
    :param kwArgs: Optional keyword arguments (see below)
    :return: The scaled object
    
    The following ``kwArgs`` are supported:
    
    ``scaleOnlyInX``
        An optional flag. If True, scaling will only happen in X. If False, it
        will happen in both X and Y.
    
    ``scaleOnlyInY``
        An optional flag. If True, scaling will only happen in Y. If False, it
        will happen in both X and Y.
    
    .. note::
        
        It's generally better if you use the ``transformed()`` method in lieu
        of this method, as this method is limited to simple scaling, whereas
        the ``transformed()`` method can also handle skew and rotation.
    
    >>> def func(s, **k):
    ...     pat = re.compile("(-?[0-9]+\.?[0-9]*|-?\.[0-9]+)")
    ...     x = pat.search(s)
    ...     xyn, i, rd, j = (('x', 'y', None), 0, (False, True), 0)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start, xyn[i], rd[j])
    ...         i = (i + 1) % 3
    ...         j = (j + 1) % 2
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findscalablesfunc': func}
    
    >>> obj = Test1("Values 0, 1, 2, 3, 4, -1, -2, -3, and -4")
    >>> print(obj.scaled(0.5))
    Values 0.0, 1, 1.0, 2, 2.0, -1, -1.0, -2, and -2.0
    >>> print(obj.scaled(0.5, scaleOnlyInX=True))
    Values 0.0, 1, 1.0, 2, 4, -1, -1.0, -3, and -2.0
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {
    ...       'text_findscalablesfunc': func,
    ...       'text_python3rounding': True}
    
    >>> obj = Test2("Values 0, 1, 2, 3, 4, -1, -2, -3, and -4")
    >>> print(obj.scaled(0.5))
    Values 0.0, 0, 1.0, 2, 2.0, 0, -1.0, -2, and -2.0
    """
    
    if scaleFactor == 1.0:
        return self.__deepcopy__()
    
    TS = self._TEXTSPEC
    g = TS.get('text_findscalablesfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        scaleOnlyInX = kwArgs.get('scaleOnlyInX', False)
        scaleOnlyInY = kwArgs.get('scaleOnlyInY', False)
        
        if scaleOnlyInX and scaleOnlyInY:
            scaleOnlyInX = scaleOnlyInY = False
        
        if 'text_roundfunc' in TS:
            f = TS['text_roundfunc']
        elif TS.get('text_python3rounding', False):
            f = utilities.newRound
        else:
            f = utilities.oldRound
        
        state = (scaleFactor, f, scaleOnlyInX, scaleOnlyInY)
        
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._scaled_helper,
          state=state,
          trackDeltas = kwArgs.get('trackDeltas', {}))
    
    # Now do attributes
    dNew = attrhelper.M_scaled(
      self._ATTRSPEC,
      self.__dict__,
      scaleFactor,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_storageRenumbered(self, **kwArgs):
    """
    Return new object with storage index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with storage indices renumbered
    :rtype: Same as self

    Storage indices are used in TrueType hinting, and can appear in several
    different tables. If you are merging fonts together, you might want to
    renumber the storage indices in the various input fonts so they don't
    collide. This method helps you do that.

    The following ``kwArgs`` are supported:

    ``keepMissing``
        If True (the default) then any values not explicitly included in the
        ``oldToNew`` dict will be left unchanged. If False, those values will
        be replaced with None.

    ``oldToNew``
        A dict mapping old storage indices to new ones. Note that it's OK for
        this dict to not map every single old storage index; what happens if
        this occurs is specified by the ``keepMissing`` flag.

    ``storageDelta``
        An optional integer value (possibly negative) that will be added to the
        old storage index to obtain the new one.

    ``storageMappingFunc``
        This is optional. If specified, it should be a function taking one
        positional argument (the storage index), and should allow for arbitrary
        keyword arguments. It returns the new storage index.

    .. note::
  
      You should choose exactly *one* of ``storageDelta``,
      ``storageMappingFunc``, or ``oldToNew``.
    
    One special case for classes derived from this metaclass: if the caller
    sets ``keepMissing`` to False, and any storage indices cannot be
    renumbered, they will be replaced with the string ">>>CANNOT RENUMBER<<<".
    
    >>> def func(s, **k):
    ...     pat = re.compile("([0-9]+)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start, end = x.span()
    ...         yield (start, end - start)
    ...         x = pat.search(s, end)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findstoragefunc': func}
    
    >>> obj = Test1("Talking about storage indices 13, 14, and 29")
    >>> print(obj)
    Talking about storage indices 13, 14, and 29
    >>> print(obj.storageRenumbered(storageDelta=80))
    Talking about storage indices 93, 94, and 109
    >>> d = {13: 300, 14: 350}
    >>> print(obj.storageRenumbered(oldToNew=d))
    Talking about storage indices 300, 350, and 29
    >>> print(obj.storageRenumbered(oldToNew=d, keepMissing=False))
    Talking about storage indices 300, 350, and >>>CANNOT RENUMBER<<<
    >>> f = (lambda n,**k: (n + 50 if n % 2 else n + 400))
    >>> print(obj.storageRenumbered(storageMappingFunc=f))
    Talking about storage indices 63, 414, and 79
    """
    
    g = self._TEXTSPEC.get('text_findstoragefunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        s = self._processText(
          g(s, origObj=self, **kwArgs),
          self._storageRenumbered_helper,
          **kwArgs)
    
    # Now do attributes
    dNew = attrhelper.M_storageRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def M_transformed(self, matrixObj, **kwArgs):
    """
    Returns a object with FUnit distances transformed.
    
    :param matrixObj: The :py:class:`~fontio3.fontmath.matrix.Matrix` to use
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The transformed object
    
    This method is preferred to the older ``scaled()`` method, because it
    allows for skews and rotations, in addition to scales and shifts.
    
    >>> def func(s, **k):
    ...     pat = re.compile(
    ...       "\\((-?[0-9]+\.?[0-9]*|-?\.[0-9]+), "
    ...       "*(-?[0-9]+\.?[0-9]*|-?\.[0-9]+)\\)")
    ...     x = pat.search(s)
    ...     while x is not None:
    ...         start1, end1 = x.span(1)
    ...         start2, end2 = x.span(2)
    ...         yield (
    ...           start1,
    ...           end1 - start1,
    ...           start2,
    ...           end2 - start2,
    ...           k.get('round', False))
    ...         x = pat.search(s, end2)
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {'text_findtransformpairsfunc': func}
    
    >>> obj = Test1(
    ...   "The point (1, -3) and the point (-12.25, 5.25) are interesting")
    >>> mShift = matrix.Matrix.forShift(1, 2)
    >>> mScale = matrix.Matrix.forScale(-3, 2)
    >>> m = mShift.multiply(mScale)
    >>> print(obj)
    The point (1, -3) and the point (-12.25, 5.25) are interesting
    >>> print(obj.transformed(m))
    The point (-6.0, -2.0) and the point (33.75, 14.5) are interesting
    >>> print(obj.transformed(m, round=True))
    The point (-6, -2) and the point (34.0, 15.0) are interesting
    """
    
    TS = self._TEXTSPEC
    g = TS.get('text_findtransformpairsfunc', None)
    s = super(self.__class__, self).__str__()
    
    if 'origObj' in kwArgs:
        del kwArgs['origObj']
    
    if g is not None:
        if 'text_roundfunc' in TS:
            f = TS['text_roundfunc']
        elif TS.get('text_python3rounding', False):
            f = utilities.newRound
        else:
            f = utilities.oldRound
        
        state = (matrixObj, f)
        
        s = self._processText2(
          g(s, origObj=self, **kwArgs),
          self._transformed_helper,
          state = state)
    
    # Now do attributes
    dNew = attrhelper.M_transformed(
      self._ATTRSPEC,
      self.__dict__,
      matrixObj,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(s, **dNew)

def PM_processText(self, toProcess, processFunc, **kwArgs):
    """
    Returns a new string whose contents are the current string, where each
    chunk identified in toProcess by a ``(start, length, *extras)`` tuple is
    passed to the ``processFunc`` (with the ``extras`` and ``kwArgs``) for an
    alternative representation.

    The ``toProcess`` iterable itself can be derived, for instance, via the
    ``text_findglyphsfunc``, or by some other means.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> s = Test1("From glyph 12 to glyph 97")
    >>> toProcess = [(11, 2), (23, 2)]  # normally made via some function call
    >>> nm = namer.testingNamer().bestNameForGlyphIndex
    >>> pf = (lambda s,**k: nm(int(s)))
    >>> print(s)
    From glyph 12 to glyph 97
    >>> print(s._processText(toProcess, pf))
    From glyph xyz13 to glyph afii60002
    
    A caller may pass in a keyword argument 'trackDeltas' which will be filled
    with (oldFirst, oldLast): lengthDeltaOldToNew information. This is useful,
    for example, for TSILowLevel.Hints objects which need to alter their
    locInfo data depending on the changes made here.
    
    >>> td = {}
    >>> sNew = s._processText(toProcess, pf, trackDeltas=td)
    >>> for k in sorted(td):
    ...   print(k, td[k])
    (11, 12) 3
    (23, 24) 7
    
    This tells us that the substring at (11, 12) grew by 3 characters, while
    the one at (23, 24) grew by 7.
    """
    
    toProcess = [
      (first, first + count - 1, extras)
      for first, count, *extras in toProcess]
    
    if not toProcess:
        return super(self.__class__, self).__str__()
    
    toProcessTrue = [
      (first, last, True, extras)
      for first, last, extras in toProcess]
    
    s = span.BoundSpan(0, len(self) - 1)
    s.addRanges(t[0:2] for t in toProcess)
    s.invert()
    toNotProcess = [(first, last, False, []) for first, last in s]
    masterList = sorted(toProcessTrue + toNotProcess)
    v = [None] * len(masterList)
    trackDeltas = kwArgs.get('trackDeltas', {})
    
    for i, (first, last, doIt, extras) in enumerate(masterList):
        s = self[first:last+1]
        v[i] = (processFunc(s, *extras, **kwArgs) if doIt else s)
        
        if len(s) != len(v[i]):
            trackDeltas[(first, last)] = len(v[i]) - len(s)
    
    return ''.join(v)

def PM_processText2(self, toProcess, processFunc, **kwArgs):
    """
    Returns a new string whose contents are the current string, where each
    chunk identified in ``toProcess`` by a ``(offset1, length1, offset2,
    length2, *extras)`` pair is passed to the ``processFunc`` (with the
    ``extras`` and ``kwArgs``) for alternative representation(s). If an offset
    is ``None``, the corresponding length is passed to the ``processFunc`` as a
    constant.

    The ``toProcess`` iterable itself can be derived, for instance, via the
    ``text_findtransformpairsfunc``, or by some other means.
    """
    
    dChanges = {}
    
    for offset1, length1, offset2, length2, *extras in toProcess:
        if offset1 is None:
            s1 = str(length1)
        else:
            s1 = self[offset1:offset1+length1]
        
        if offset2 is None:
            s2 = str(length2)
        else:
            s2 = self[offset2:offset2+length2]
        
        s1, s2 = processFunc(s1, s2, *extras, **kwArgs)
        
        if offset1 is not None:
            dChanges[(offset1, length1)] = s1
        
        if offset2 is not None:
            dChanges[(offset2, length2)] = s2
    
    sv = list(super(self.__class__, self).__str__())
    
    for key in sorted(dChanges, reverse=True):
        oldOffset, oldLength = key
        s = dChanges[key]
        sv[oldOffset:oldOffset+oldLength] = list(s)
    
    return ''.join(sv)

def SM_bool(self):
    """
    Determines the Boolean truth or falsehood of ``self``.
    
    :return: True if the string is non-empty, or if it is empty but has one or
        more attributes whose ``bool()`` results are True. This method is only
        included in the class if there are attributes, and at least one
        attribute is not set to be ignored.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> bool(Test1('abc'))
    True
    >>> bool(Test1(''))
    False
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    ...     attrSpec = {'a': {}, 'b': {'attr_ignoreforbool': True}}
    >>> bool(Test2('abc', a=0, b=0))
    True
    >>> bool(Test2('', a=0, b=0))
    False
    >>> bool(Test2('', a=1, b=0))
    True
    >>> bool(Test2('', a=0, b=1))
    False
    """
    
    if len(self):
        return True
    
    return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(str, metaclass=FontDataMetaclass): pass
    >>> b = Bottom("The string is here")
    >>> bCopy = b.__copy__()
    >>> b == bCopy, b is bCopy
    (True, False)
    
    >>> class Top(str, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {}}
    >>> t = Top("This is another string", a=[1, 2, 3])
    >>> tCopy = t.__copy__()
    >>> t == tCopy, t is tCopy
    (True, False)
    >>> t.a is tCopy.a
    True
    """
    
    s = super(self.__class__, self).__str__()
    
    if self._ATTRSPEC:
        return type(self)(s, **self.__dict__)
    else:
        return type(self)(s)

def SM_deepcopy(self, memo=None):
    """
    Make a deep copy.
    
    :return: A deep copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(str, metaclass=FontDataMetaclass): pass
    >>> b = Bottom("String for bottom")
    >>> bCopy = b.__deepcopy__()
    >>> b == bCopy, b is bCopy
    (True, False)
    
    >>> class Top(str, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_deepcopyfunc': (lambda x,m: list(x))}}
    >>> t = Top("String for top", a=[1, 2, 3])
    >>> tCopy = t.__deepcopy__()
    >>> t == tCopy, t is tCopy
    (True, False)
    >>> t.a is tCopy.a
    False
    
    >>> class Topper(str, metaclass=FontDataMetaclass):
    ...     attrSpec = {'b': {'attr_followsprotocol': True}}
    >>> p = Topper("String for topper", b=t)
    >>> pCopy = p.__deepcopy__()
    >>> p == pCopy, p is pCopy
    (True, False)
    >>> p.b is pCopy.b, p.b.a is pCopy.b.a
    (False, False)
    """
    
    s = super(self.__class__, self).__str__()
    
    if memo is None:
        memo = {}
    
    dNew = attrhelper.SM_deepcopy(self._ATTRSPEC, self.__dict__, memo)
    return type(self)(s, **dNew)

def SM_eq(self, other):
    """
    Determines whether ``self`` and ``other`` are equal.
    
    :return: True if the ``__str__()`` of ``self`` is equal to the
        ``__str__()`` of ``other``, and if non-ignored attributes are equal;
        False otherwise.
    
    This method is only included in
    the class if there are attributes, and at least one attribute is not set to
    be ignored.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> Test1('abc') == Test1('abc')
    True
    >>> Test1('abc') == Test1('abc ')
    False
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    ...     attrSpec = {'a': {}, 'b': {'attr_ignoreforcomparisons': True}}
    >>> Test2('abc', a=0, b=0) == Test2('abc', a=0, b=0)
    True
    >>> Test2('abc', a=0, b=0) == Test2('abc ', a=0, b=0)
    False
    >>> Test2('abc', a=1, b=0) == Test2('abc', a=0, b=0)
    False
    >>> Test2('abc', a=0, b=0) == Test2('abc', a=0, b=1)
    True
    """
    
    if self is other:
        return True
    
    if (
      super(self.__class__, self).__str__() !=
      super(other.__class__, other).__str__()):
        
        return False
    
    return attrhelper.SM_eq(
      self._ATTRSPEC,
      getattr(other, '_ATTRSPEC', {}),
      self.__dict__,
      getattr(other, '__dict__', {}))

def SM_hash(self):
    """
    Determine ``self``’s hash value.
    
    :return: A hash value for the object and relevant attributes
    :rtype: int
    
    This method is only included by the metaclass initialization logic if
    there is at least one attribute that has ``attr_ignoreforcomparisons``
    set to False.
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    >>> hash(Test1('abc')) == hash('abc')
    True
    
    >>> class Test2(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    ...     attrSpec = {'a': {}, 'b': {'attr_ignoreforcomparisons': True}}
    >>> hash(Test2('abc', a=0, b=0)) == hash(Test2('abc', a=0, b=0))
    True
    >>> hash(Test2('abc', a=0, b=0)) == hash(Test2('abc ', a=0, b=0))
    False
    >>> hash(Test2('abc', a=0, b=0)) == hash(Test2('abc', a=1, b=0))
    False
    >>> hash(Test2('abc', a=0, b=0)) == hash(Test2('abc', a=0, b=1))
    True
    """
    
    AS = self._ATTRSPEC
    d = self.__dict__
    v = []
    
    for k in sorted(AS):  # not sortedKeys, as this needs to be exhaustive
        ks = AS[k]
        f = ks.get('attr_asimmutablefunc', None)
        obj = d[k]
        
        if not ks.get('attr_ignoreforcomparisons', False):
            if ks.get(
              'attr_asimmutabledeep',
              ks.get('attr_followsprotocol', False)):
                
                v.append(obj.asImmutable())
            
            elif f is not None:
                v.append(f(obj))
            
            else:
                v.append(obj)
    
    return hash((super(self.__class__, self).__str__(), tuple(v)))

def SM_init(self, value, *args, **kwArgs):
    """
    Initialize the attributes from kwArgs if they're present, or the attribute
    initialization function otherwise. This method is only included in the
    class if there are attributes.
    """
    
    AS = self._ATTRSORT
    d = self.__dict__
    f = operator.itemgetter('attr_initfunc')
    
    if args:
        if len(args) > len(AS):
            raise ValueError("Too many positional arguments!")
        
        for i, n in enumerate(args):
            d[AS[i]] = n
    
    AS = self._ATTRSPEC
    changedFuncIDsAlreadyDone = set()
    deferredKeySet = set()
    
    for k, ks in AS.items():
        if k not in d:  # might have been initialized from positional args
            if k in kwArgs:
                d[k] = kwArgs[k]
            
            elif 'attr_initfuncchangesself' in ks:
                # We defer doing these special initializations until all the
                # other positional and keyword arguments are done.
                deferredKeySet.add(k)
            
            else:
                v = ([self] if 'attr_initfuncneedsself' in ks else [])
                # it's now OK to do this, because we've already guaranteed all
                # attrdict specs have an attr_initfunc.
                d[k] = f(ks)(*v)
    
    for k in deferredKeySet:
        ks = AS[k]
        initFunc = f(ks)
        
        if id(initFunc) not in changedFuncIDsAlreadyDone:
            changedFuncIDsAlreadyDone.add(id(initFunc))
            initFunc(self)  # the function changes self's attributes directly
    
    # Only after everything is set up do we do a final attr_ensuretype check.
    
    for k, ks in AS.items():
        et = ks.get('attr_ensuretype', None)
        
        if (et is not None) and (not isinstance(d[k], et)):
            d[k] = et(d[k])

def SM_new(cls, s, *args, **kwArgs):
    """
    Create and return a new instance, but defer attribute initialization to
    ``__init__()``. This method is only included in the class if attributes are
    present.
    
    The specified string will be taken as-is, with no newline conversion being
    done. If newline conversion is needed, use the ``frombytes()`` method
    instead.
    """
    
    return str.__new__(cls, s)

def SM_repr(self):
    """
    Return a string representation of ``self``.
    
    :return: The string representation
    :rtype: str
    
    The returned string can be passed to ``eval()`` in order to get back an
    object equal to the original ``self``.
    
    >>> class Test1(str, metaclass=FontDataMetaclass): pass
    >>> obj1 = Test1("This is some text")
    >>> print(repr(obj1))
    Test1('This is some text')
    >>> obj1 == eval(repr(obj1))
    True
    """
    
    AS = self._ATTRSPEC
    s = super(self.__class__, self).__str__()
    
    if not AS:
        return "%s(%r)" % (self.__class__.__name__, s)
    
    d = self.__dict__
    t = tuple(x for k in AS for x in (k, d[k]))
    sv = [
        self.__class__.__name__,
        '(',
        repr(s),
        ', ',
        (', '.join(["%s=%r"] * len(AS))) % t,
        ')']
    
    return ''.join(sv)

def SM_str(self):
    """
    Return a nicely readable string representation of the object.
    
    :return: A string representation of ``self``
    :rtype: str
    
    >>> class Test1(str, metaclass=FontDataMetaclass):
    ...     textSpec = {}
    ...     attrSpec = {'a': {}}
    >>> print(Test1("This is some text", a=15))
    This is some text, a = 15
    """
    
    selfNamer = getattr(self, '_namer', None)
    
    sv = (
      [super(self.__class__, self).__str__()] +
      attrhelper.SM_str(self, selfNamer))
    
    return ', '.join(sv)

def STM_cvtsRenumbered_helper(s, **kwArgs):
    cvtMappingFunc = kwArgs.get('cvtMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    cvtDelta = kwArgs.get('cvtDelta', None)
    
    if cvtMappingFunc is not None:
        f = lambda x,**k: str(cvtMappingFunc(x, **k))
    
    elif oldToNew is not None:
        f = (
          lambda x, **k:
          str(
            oldToNew.get(
              x,
              (x if keepMissing else ">>>CANNOT RENUMBER<<<"))))
    
    elif cvtDelta is not None:
        f = lambda x,**k: str(x + cvtDelta)
    
    else:
        f = lambda x,**k: str(x)
    
    return f(int(s))

def STM_fdefsRenumbered_helper(s, **kwArgs):
    fdefMappingFunc = kwArgs.get('fdefMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    
    if fdefMappingFunc is not None:
        f = lambda x,**k: str(fdefMappingFunc(x, **k))
    
    elif oldToNew is not None:
        f = (
          lambda x, **k:
          str(
            oldToNew.get(
              x,
              (x if keepMissing else ">>>CANNOT RENUMBER<<<"))))
    
    else:
        f = lambda x,**k: str(x)
    
    return f(int(s))

def STM_glyphsRenumbered_helper(s, **kwArgs):
    old = int(s)
    oldToNew = kwArgs.get('oldToNew', {})
    km = kwArgs.get('keepMissing', True)
    
    if old not in oldToNew:
        return (s if km else ">>>CANNOT RENUMBER<<<")
    else:
        return str(oldToNew[old])

def STM_namesRenumbered_helper(s, **kwArgs):
    old = int(s)
    oldToNew = kwArgs.get('oldToNew', {})
    km = kwArgs.get('keepMissing', True)
    
    if old not in oldToNew:
        return (s if km else ">>>CANNOT RENUMBER<<<")
    else:
        return str(oldToNew[old])

def STM_pcsRenumbered_helper(s, *extras, **kwArgs):
    infoString = extras[0]
    old = int(s)
    mapData = kwArgs.get('mapData', {})
    delta = 0
    
    for threshold, newDelta in mapData.get(infoString, []):
        if old < threshold:
            break
        
        delta = newDelta
    
    old += delta
    return str(old)

def STM_pointsRenumbered_helper(s, *extras, **kwArgs):
    glyphIndex = extras[0]
    old = int(s)
    mapData = kwArgs.get('mapData', {})
    dGlyph = mapData.get(glyphIndex, {})
    old = dGlyph.get(old, old)
    return str(old)

def STM_scaled_helper(s, *extras, **kwArgs):
    xyNone, doRound = extras[0:2]
    old = float(s)
    castType = (int if old == math.trunc(old) else float)
    scaleFactor, roundFunc, scaleOnlyInX, scaleOnlyInY = kwArgs['state']
    
    if (xyNone == 'x') and scaleOnlyInY:
        return s
    
    if (xyNone == 'y') and scaleOnlyInX:
        return s
    
    if doRound:
        old = roundFunc(scaleFactor * old, castType = castType)
    else:
        old = scaleFactor * old
    
    return str(old)

def STM_storageRenumbered_helper(s, **kwArgs):
    storageMappingFunc = kwArgs.get('storageMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    storageDelta = kwArgs.get('storageDelta', None)
    
    if storageMappingFunc is not None:
        f = lambda x,**k: str(storageMappingFunc(x, **k))
    
    elif oldToNew is not None:
        f = (
          lambda x, **k:
          str(
            oldToNew.get(
              x,
              (x if keepMissing else ">>>CANNOT RENUMBER<<<"))))
    
    elif storageDelta is not None:
        f = lambda x,**k: str(x + storageDelta)
    
    else:
        f = lambda x,**k: str(x)
    
    return f(int(s))

def STM_transformed_helper(s1, s2, *extras, **kwArgs):
    doRound = extras[0]
    old1 = float(s1)
    castType1 = (int if old1 == math.trunc(old1) else float)
    old2 = float(s2)
    castType2 = (int if old2 == math.trunc(old2) else float)
    matrixObj, roundFunc = kwArgs['state']
    
    if doRound:
        p = matrixObj.mapPoint((old1, old2))
        old1 = roundFunc(p[0], castType=castType1)
        old2 = roundFunc(p[1], castType=castType2)
    
    else:
        old1, old2 = matrixObj.mapPoint((old1, old2))
    
    return str(old1), str(old2)

# -----------------------------------------------------------------------------

#
# Private functions (metaclass-only; not included in the final class)
#

if 0:
    def __________________(): pass

_methodDict = {
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
    '__repr__': SM_repr,
    '_cvtsRenumbered_helper': staticmethod(STM_cvtsRenumbered_helper),
    '_fdefsRenumbered_helper': staticmethod(STM_fdefsRenumbered_helper),
    '_glyphsRenumbered_helper': staticmethod(STM_glyphsRenumbered_helper),
    '_namesRenumbered_helper': staticmethod(STM_namesRenumbered_helper),
    '_pcsRenumbered_helper': staticmethod(STM_pcsRenumbered_helper),
    '_pointsRenumbered_helper': staticmethod(STM_pointsRenumbered_helper),
    '_processText': PM_processText,
    '_processText2': PM_processText2,
    '_scaled_helper': staticmethod(STM_scaled_helper),
    '_storageRenumbered_helper': staticmethod(STM_storageRenumbered_helper),
    '_transformed_helper': staticmethod(STM_transformed_helper),
    'asImmutable': M_asImmutable,
    'buildBinary': M_buildBinary,
    'checkInput': M_checkInput,
    'coalesced': M_coalesced,
    'compacted': M_compacted,
    'cvtsRenumbered': M_cvtsRenumbered,
    'fdefsRenumbered': M_fdefsRenumbered,
    'fromwalker': classmethod(CM_fromwalker),
    'gatheredInputGlyphs': M_gatheredInputGlyphs,
    'gatheredLivingDeltas': M_gatheredLivingDeltas,
    'gatheredMaxContext': M_gatheredMaxContext,
    'gatheredOutputGlyphs': M_gatheredOutputGlyphs,
    'gatheredRefs': M_gatheredRefs,
    'glyphsRenumbered': M_glyphsRenumbered,
    'hasCycles': M_hasCycles,
    'isValid': M_isValid,
    'merged': M_merged,
    'namesRenumbered': M_namesRenumbered,
    'pcsRenumbered': M_pcsRenumbered,
    'pointsRenumbered': M_pointsRenumbered,
    'pprint': M_pprint,
    'pprint_changes': M_pprintChanges,
    'recalculated': M_recalculated,
    'scaled': M_scaled,
    'storageRenumbered': M_storageRenumbered,
    'transformed': M_transformed
    }

_methodDictAttr = {
    '__init__': SM_init,
    '__new__': SM_new,
    '__str__': SM_str
    }

def _addMethods(cd, bases):
    AS = cd['_ATTRSPEC']
    needEqNe, needBool = attrhelper.determineNeedForEqBool(AS)
    stdClasses = (str, bytes)
    
    for mKey, m in _methodDict.items():
        if mKey in cd:
            continue
        
        for c in reversed(bases):  # do nearest ancestor first
            if hasattr(c, mKey):
                cand = getattr(c, mKey)
                
                if any(getattr(d, mKey, None) is cand for d in stdClasses):
                    continue
                
                cd[mKey] = cand
                break
    
        else:
            cd[mKey] = m
    
    # Only include __eq__ and __hash__ methods if needed
    if needEqNe:
        if '__eq__' not in cd:
            cd['__eq__'] = SM_eq
        
        if '__hash__' not in cd:
            cd['__hash__'] = SM_hash
    
    # Only include __bool__ method if needed
    if needBool:
        if '__bool__' not in cd:
            cd['__bool__'] = SM_bool
    
    if AS:
        for mKey, m in _methodDictAttr.items():
            if mKey in cd:
                continue
            
            for c in reversed(bases):  # do nearest ancestor first
                if hasattr(c, mKey):
                    cand = getattr(c, mKey)
                    
                    if any(getattr(d, mKey, None) is cand for d in stdClasses):
                        continue
                    
                    cd[mKey] = cand
                    break
            
            else:
                cd[mKey] = m

def _validateTextSpec(d):
    """
    """
    
    unknownKeys = set(d) - validTextSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown textSpec keys: %s" % (sorted(unknownKeys),))

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for string-like classes. If this metaclass is applied to a class
    whose base class (or one of whose base classes) is already one of the
    Protocol classes, the ``textSpec`` and ``attrSpec`` will define additions
    to the original. In this case, if an ``attrSorted`` is provided, it will be
    used for the combined attributes (original and newly-added); otherwise the
    new attributes will be added to the end of the ``attrSorted`` list.

    The rules for combining ``attrSpecs`` are a little trickier: note that
    these are dicts of dicts, and so a simple ``update()`` call will
    potentially remove important content. For this reason, the new ``attrSpec``
    for a subclass is walked and the sub-dicts merged separately.
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_TEXTSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            TS = c._TEXTSPEC.copy()
            TS.update(classdict.pop('textSpec', {}))
            classdict['_TEXTSPEC'] = classdict['_MAIN_SPEC'] = TS
            _validateTextSpec(TS)
            AS = {k: v.copy() for k, v in c._ATTRSPEC.items()}
            extraAttrs = classdict.pop('attrSpec', {})
            
            for attrName, attrDict in extraAttrs.items():
                if attrName in AS:
                    AS[attrName].update(attrDict)
                else:
                    AS[attrName] = attrDict
            
            classdict['_ATTRSPEC'] = classdict['_EXTRA_SPEC'] = AS
            attrhelper.validateAttrSpec(AS)
            
            if 'attrSorted' in classdict:
                AT = classdict.pop('attrSorted')
            
            else:
                s = frozenset(c._ATTRSORT)
                v = [x for x in sorted(extraAttrs) if x not in s]
                AT = c._ATTRSORT + tuple(v)
            
            classdict['_ATTRSORT'] = AT
        
        else:
            d = classdict['_TEXTSPEC'] = classdict.pop('textSpec', {})
            classdict['_MAIN_SPEC'] = d
            _validateTextSpec(d)
            d = classdict['_ATTRSPEC'] = classdict.pop('attrSpec', {})
            classdict['_EXTRA_SPEC'] = d
            
            classdict['_ATTRSORT'] = classdict.pop(
              'attrSorted',
              tuple(sorted(d)))
            
            attrhelper.validateAttrSpec(d)
        
        _addMethods(classdict, bases)
        invariants.addInvariantMethods(classdict)
        
        return super(FontDataMetaclass, mcl).__new__(
          mcl,
          classname,
          bases,
          classdict)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import re
    from fontio3.fontdata import seqmeta
    from fontio3.fontmath import matrix
    from fontio3.utilities import namer

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
