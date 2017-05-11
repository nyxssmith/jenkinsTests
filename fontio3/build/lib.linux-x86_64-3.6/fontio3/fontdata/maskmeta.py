#
# maskmeta.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for values that are actually collections of bits or bitfields.
Clients wishing to define a class with these behaviors should use object as
the base class, and include the following class variables:

``maskByteLength``
    The byte-length of the binary representation of the mask. Note this may be
    larger than might be otherwise deduced from looking at the bitfield
    definitions in the ``maskSpec``.

``maskControls``
    An optional dict mapping control names to control values. These controls
    are used to deal with the masklike object as a whole:
    
    ``combinedstringfunc``
        A function taking one argument, a sequence of mask labels. The returned
        value should be a string, which will be used to represent the entire
        mask.

        Normally, clients would use this option to combine a potentially
        multiline representation into something a little more compact. For an
        example, see :py:mod:`fontio3.head.macstyle`.
        
        There is no default.
    
    ``fillmissingwithone``
        Normally, gaps in the binary representation are filled with zeroes.
        However, some tables (like ``'PCLT'``) need to be filled with ones
        instead. If that is the case, set this flag True.
        
        Default is False.
    
    ``inputconvolutionfunc``
        A function taking a number representing the whole mask and returning
        another number with bits moved into canonical ordering. For instance,
        if your 16-bit number chooses to identify bit numbers using the
        MSB-as-zero convention, you could specify an ``inputconvolutionfunc``
        like::
        
            lambda n: int('0b' + bin(n+0x10000)[3:][::-1], 2)
        
        to reverse the bits. This function is used in the ``fromnumber`` and
        ``fromvalidatednumber`` methods to process the input before any other
        processing is done.

        The reverse of this function should also be specified using the
        ``outputconvolutionfunc`` keyword. For an example of code that defines
        and uses these two functions, see
        :py:class:`fontio3.OS_2.unicoderanges_v4.UnicodeRanges`.
        
        There is no default.
    
    ``loggername``
        A string used in ``fromvalidatednumber()`` to give a name to the child
        logger.
        
        Default is ``'genericmask'``.
    
    ``outputconvolutionfunc``
        A function taking a number representing the whole mask and returning
        another number with bits moved into canonical ordering. For instance,
        if your 16-bit number chooses to identify bit numbers using the
        MSB-as-zero convention, you could specify an ``outputconvolutionfunc``
        like::
        
            lambda n: int('0b' + bin(n+0x10000)[3:][::-1], 2)
        
        to reverse the bits. This function is used in the ``buildBinary()``
        method to process the output after all other processing is done.

        The reverse of this function should also be specified using the
        ``inputconvolutionfunc`` keyword. For an example of code that uses
        these two functions, see
        :py:class:`fontio3.OS_2.unicoderanges_v4.UnicodeRanges`.
        
        There is no default.
    
    ``recalculatefunc_partial``
        A function taking one positional argument, the whole mask object, and
        optional additional keyword arguments. The function should return a
        pair: the first value is True or False, depending on whether the
        recalculated sequence's value actually changed. The second value is the
        new recalculated mask object to be used (if the first value was True).

        After the ``recalculatefunc_partial`` is done, individual
        ``mask_recalculatefunc`` calls will be made. This allows you to "divide
        the labor" in useful ways.
        
        There is no default.
    
    ``validate_notsettoone_iserror``
        If True, validation will log undefined mask bits not set to one as an
        error (otherwise, warning).
        
        Default is False.
    
    ``validate_notsettozero_iserror``
        If True, validation will log undefined mask bits not set to zero as an
        error (otherwise, warning).
        
        Default is False.
    
    ``validatecode_notsettoone``
        The code to be used for logging when undefined mask bits are not all
        set to one (and ``fillmissingwithone`` is True).
        
        Default is ``'G0015'``.
    
    ``validatecode_notsettozero``
        The code to be used for logging when undefined mask bits are not all
        set to zero (and ``fillmissingwithone`` is False).
        
        Default is ``'G0014'``.
    
    ``validatefunc_partial``
        A function taking one position argument (the whole object), and
        arbitary keyword arguments (e.g. a ``logger`` and an ``editor``). It
        returns True or False depending on whether the object is valid; any
        further tests in ``mask_validatefunc`` or ``mask_validatefunc_partial``
        controls will be run after this function is done.
        
        There is no default.
    
    ``wisdom``
        A string encompassing a sensible description of the mask object as a
        whole, including how it is used.
        
        There is, alas, no default for wisdom.
    
``maskSorted``
    An optional sequence of attribute names which controls the order in which
    these appear in ``__str__()`` or ``pprint()`` output. If not specified, the
    bit positioning of the attribute fields will be used instead, with the most
    significant field first.

``maskSpec``
    A dict mapping attribute names (the keys) to information sub-dicts. These
    sub-dicts map special keys, defined below, to values (or defaults if the
    keys are not present).
    
    ``mask_bitcount``
        The number of contiguous bits making up the value.
        
        There is no default; this is required unless either ``mask_isbool`` or
        ``mask_isantibool`` is True, in which case it is assumed to be 1.
    
    ``mask_boolstrings``
        If ``mask_isbool`` or ``mask_isantibool`` is set, and this key is
        provided, it should be a sequence of two values. These will be used to
        display the state of the Boolean, instead of the usual ``"label: xxx"``
        format. The [0] element is used for False and the [1] element is used
        for True.

        For example, a ``'kerx'`` :py:class:`~fontio3.kerx.coverage.Coverage`
        uses one of these to make a False value display as ``"With-stream"``
        instead of the less-clear ``"Cross-stream: False"``.
        
        Default is ``None``.
    
    ``mask_constantvalue``
        If specified, this value is enforced for the field.
        
        There is no default.
    
    ``mask_enumstrings``
        If ``mask_isenum`` is True, either this or ``mask_enumstringsdict``
        must be specified. If this key is chosen, its value must be a sequence
        with up to ``2**mask_bitcount`` strings. The numeric value is used to
        index into this sequence to determine the attribute's value.
        
        Default is ``None``.
    
    ``mask_enumstringsdict``
        If ``mask_isenum`` is True, either this or ``mask_enumstrings`` must be
        specified. If this key is chosen, its value must be a
        ``collections.defaultdict`` mapping numeric values to their
        corresponding strings. This key should be chosen if the enumerated
        values are sparse, or would require a sequence that is too long. Key 0
        will be used as the default initializer if none is provided. The client
        may set up the ``defaultdict`` so unspecified enumerated values return
        a sensible default string.
        
        Default is ``None``.
    
    ``mask_fixedcharacteristic``
        The number of significant bits before the binary point for a fixed
        value. This includes the sign bit if ``mask_issigned`` is True.
        
        Default is 16 (but only if ``mask_isfixed`` is True).
    
    ``mask_ignoreforcomparisons``
        If True, this value will not be used in comparisons for equality or
        inequality (including ``__eq__()``, ``__ne__()``, and ``__bool__()``).
        
        Default is False.
    
    ``mask_initfunc``
        If specified, it should be a function taking no values, and returning a
        reasonable default value.
        
        Default is a function setting the value to 0/False for everything but
        enums. There is no default for enums; a ``mask_initfunc`` must be
        provided for them.
    
    ``mask_inputcheckfunc``
        If specified, a function taking one positional argument and arbitrary
        keyword arguments, one of which must be ``fieldName`` with the name of
        the field being checked. Returns True if the positional argument is
        acceptable for that field.
        
        There is no default.
    
    ``mask_isantibool``
        If True, the value is a single bit which is interpreted as a True/False
        value. Also, if True the ``mask_bitcount`` is automatically set to 1,
        and need not be specified.

        The difference between a regular bool and an antibool is in the
        antibool, 0 is True and 1 is False. This is useful in cases like the
        fontio3.kern.format1's two coverage flavors in format 1 ``'kern'``
        tables, one of which is 1=horizontal while the other is 0=horizontal.
        
        Default is False.
    
    ``mask_isbool``
        If True, the value is a single bit which is interpreted as a True/False
        value. Also, if True the ``mask_bitcount`` is automatically set to 1,
        and need not be specified.
        
        Default is False.
    
    ``mask_iscvtindex``
        If True, the value is a CVT index, and is subject to being renumbered
        if ``cvtsRenumbered()`` is called.
        
        Default is False.
    
    ``mask_isenum``
        If True, the value is a (zero-based, unsigned) index into the tuple of
        strings defined in ``mask_enumstrings``, or key into the dict of
        strings defined in ``mask_enumstringsdict``.
        
        Default is False.
    
    ``mask_isfdefindex``
        If True, the value is an FDEF index, and is subject to being renumbered
        if ``fdefsRenumbered()`` is called.
        
        Default is False.
    
    ``mask_isfixed``
        If True, the value is a Fixed number. The number of bits before the
        binary point will be defined in ``mask_fixedcharacteristic``.
        
        Default is False.
    
    ``mask_isglyphindex``
        If True, the value is to be treated as a glyph index, which means it
        participates in ``glyphsRenumbered()`` calls. If a
        :py:class:`~fontio3.utilities.namer.Namer` is present and
        ``mask_usenamerforstr`` is set, then this flag triggers the use of a
        glyph name instead of an index in various output methods.
        
        Default is False.
    
    ``mask_isnameindex``
        If True, the value is to be treated as a ``'name'`` table index, which
        means it participates in ``namesRenumbered()`` calls.
        
        Default is False.
    
    ``mask_isoutputglyph``
        If True, then the value is treated as an output glyph. This means it
        will not be added to the accumulating set by a
        ``gatheredInputGlyphs()`` call, and it will be added by a
        ``gatheredOutputGlyphs()`` call (in both cases, of course, assuming
        ``mask_isglyphindex`` is set; if that is not the case, the value will
        not be added, even if this flag is True).
        
        Default is False.
    
    ``mask_ispc``
        If True, the value is to be treated as a Program Counter, which means
        it participates in ``pcsRenumbered()`` calls.
        
        Default is False.
    
    ``mask_ispointindex``
        If True, the value is to be treated as the index of a point in a glyph
        definition, which means the value participates in ``renumberPoints()``
        calls.
        
        Default is False.
    
    ``mask_issigned``
        If True, the value is interpreted as a signed (twos- complement)
        number. This is even true if the ``mask_bitcount`` is 1; in this case,
        the values are 0 for a zero bit, and -1 for a 1 bit.
        
        Default is False.
    
    ``mask_isstorageindex``
        If True, the value is a storage index, and is subject to being
        renumbered if ``storageRenumbered()`` is called.
        
        Default is False.
    
    ``mask_label``
        An optional and more readable label for the key. Note that if
        ``mask_constantvalue`` is specified, this ``mask_label`` will
        constitute the entirety of what gets shown. See
        :py:class:`~fontio3.OS_2.panose_fam1.Panose_fam1` for an example of
        this.
        
        Default is the key name.
    
    ``mask_mergecheckequality``
        If True, and a ``merge()`` is attempted that would change the value,
        then a ``ValueError`` is raised.
        
        Default is False.
    
    ``mask_prevalidatedglyphset``
        A set or frozenset containing glyph indices which are to be considered
        valid, even though they exceed the font's glyph count. This is useful
        for passing ``0xFFFF`` values through validation for state tables,
        where that glyph code is used to indicate the deleted glyph.
        
        There is no default.
    
    ``mask_python3rounding``
        If True, the Python 3 round function will be used. If False (the
        default), old-style Python 2 rounding will be done. This affects both
        scaling and transforming if one of the rounding options is used.
        
        Default is False.
    
    ``mask_recalculatefunc``
        If specified, this should be a function taking at least one argument,
        the value. Additional keyword arguments (for example, ``editor``)
        conforming to the ``recalculate()`` protocol may be specified.

        The function must return a pair. The first value in this returned pair
        is True or False, depending on whether the recalculated object's value
        actually changed. The second value is the new recalculated value to be
        used.
        
        There is no default.
    
    ``mask_representsx``
        If True then this value is interpreted as an x-coordinate. This
        knowledge is used by the ``transformed()`` method to transform a point;
        note in this case there will usually be an associated y-coordinate
        value linked to this one (see the ``mask_transformcounterpart`` control
        for more details).
        
        Default is False.
    
    ``mask_representsy``
        If True then this value is interpreted as a y-coordinate. This
        knowledge is used by the ``transformed()`` method to transform a point;
        note in this case there will usually be an associated x-coordinate
        value linked to this one (see the ``mask_transformcounterpart`` control
        for more details).
        
        Default is False.
    
    ``mask_rightmostbitindex``
        Identifies the least significant bit of the value. Note that bit 0 is
        the least significant bit in the whole value.
        
        There is no default; this is required in all cases.
    
    ``mask_roundfunc``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result, or ``None`` to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``mask_scales``
        If True then this value will be scaled by the ``scaled()`` method, with
        the results rounded to the nearest integral value (with .5 cases
        controlled by ``mask_python3rounding``); if this is not desired, the
        client should instead specify the ``mask_scalesnoround`` flag.
        
        Default is False.
    
    ``mask_scalesnoround``
        If True, this value responds to a ``scaled()`` call. The result will
        not be rounded, so this usually only makes sense for fixed fields,
        since they can accommodate the fractional portion that may result from
        a scaling. If rounding is desired, the ``mask_scales`` flag should be
        used.
        
        Default is False.
    
    ``mask_showonlyiffuncobj``
        If provided, it should be a function taking a single positional
        argument and returning True or False. The positional argument will be
        the entire masklike object, and not just the value for this particular
        portion. See
        :py:mod:`fontio3.kern.header` for an example of where this comes in
        handy.

        Note this is slightly different from the similar
        ``attr_showonlyiffunc`` control for simple objects and attributes, in
        that this takes the whole object, while those take the single attribute
        value. That's why this one has a slightly different name (with the
        "obj" at the end), as a mnemonic reminder.
        
        There is no default.
    
    ``mask_showonlyiftrue``
        If True, the value will not be included in string representations
        (either from ``str()`` or ``pprint()``) if the ``bool()`` of its value
        is False.
        
        Default is False.
    
    ``mask_strusesrepr``
        If True, the string representation of the value of this attribute will
        be created via ``repr()``, not ``str()``. This affects the
        ``__str__()`` and ``pprint()`` methods.
        
        Default is False.
    
    ``mask_transformcounterpart``
        If the value represents one of the two coordinates of a two-dimensional
        point, this control names the other part. (Knowledge of which is X and
        which is Y is derived from the ``mask_representsx`` and
        ``mask_representsy`` controls). This is used to construct a virtual
        point for the purposes of the ``transformed()`` call.

        Note that whether the transformed value is rounded to an integer is
        controlled by ``mask_transformnoround`` (q.v.)

        Also note that this is what controls whether a field is "transformable"
        -- if this key is not present then the value will be unchanged by a
        ``transformed()`` call.
        
        There is no default.
    
    ``mask_transformnoround``
        If True, values after a ``transformed()`` call will not be rounded to
        integers. Note that if this flag is specified, the values will always
        be left as type ``float``, irrespective of the original type. This
        differs from the default case, where rounding will be used but the
        rounded result will be the same type as the original value.

        Note the absence of an "``mask_transforms``" flag. Calls to the
        ``transformed()`` method will only affect non-``None`` values if one or
        more of the ``mask_representsx``, ``mask_representsy``, or
        ``mask_transformcounterpart`` flags are set.
        
        Default is False.
    
    ``mask_usenamerforstr``
        If True, and ``mask_isglyphindex`` is True, and a
        :py:class:`~fontio3.utilities.namer.Namer` has been specified via the
        ``setNamer()`` call, then that ``Namer`` will be used for generating
        the strings produced via the ``__str__()`` special method.

        If a ``Namer`` has been set then it will be used in ``pprint()`` and
        ``pprint_changes()``, unless one is explicitly provided, in which case
        that one will be used instead.
        
        Default is False.
    
    ``mask_validatecode_badenumvalue``
        The code to be used for logging when an unrecognized enum value is used.
        
        Default is ``'G0001'``.
    
    ``mask_validatecode_namenotintable``
        The code to be used for logging when a name table index is being used
        but that index is not actually present in the ``'name'`` table.
        
        Default is ``'G0042'``.
    
    ``mask_validatecode_negativecvt``
        The code to be used for logging when a negative value is used for a CVT
        index.
        
        Default is ``'G0028'``.
    
    ``mask_validatecode_negativeglyph``
        The code to be used for logging when a negative value is used for a
        glyph index.
        
        Default is ``'G0004'``.
    
    ``mask_validatecode_negativeinteger``
        The code to be used for logging when a negative value is used for a
        non-negative item (like a PC or a point index).
        
        Default is ``'G0008'``.
    
    ``mask_validatecode_nocvt``
        The code to be used for logging when a CVT index is used but the font
        has no ``'cvt '`` table.
        
        Default is ``'G0030'``.
    
    ``mask_validatecode_nonintegercvt``
        The code to be used for logging when a non-integer value is used for a
        CVT index.
        
        Default is ``'G0027'``.
    
    ``mask_validatecode_nonintegerglyph``
        The code to be used for logging when a non-integer value is used for a
        glyph index.
        
        Default is ``'G0003'``.
    
    ``mask_validatecode_nonintegralinteger``
        The code to be used for logging when a non-integer value is used for an
        integer item (like a PC or a point index).
        
        Default is ``'G0007'``.
    
    ``mask_validatecode_nonnumericcvt``
        The code to be used for logging when a non-numeric value is used for a
        CVT index.
        
        Default is ``'G0026'``.
    
    ``mask_validatecode_nonnumericglyph``
        The code to be used for logging when a non-numeric value is used for a
        glyph index.
        
        Default is ``'G0002'``.
    
    ``mask_validatecode_nonnumericinteger``
        The code to be used for logging when a non-numeric value is used for an
        integer item (like a PC or a point index).
        
        Default is ``'G0006'``.
    
    ``mask_validatecode_nonnumericnumber``
        The code to be used for logging when a non-numeric value is used.
        
        Default is ``'G0009'``.
    
    ``mask_validatecode_signedvaluetoolarge``
        The code to be used for logging when a signed value does not fit in its
        field.
        
        Default is ``'G0010'``.
    
    ``mask_validatecode_toolargecvt``
        The code to be used for logging when a CVT index is used that is
        greater than or equal to the number of CVTs in the font.
        
        Default is ``'G0029'``.
    
    ``mask_validatecode_toolargeglyph``
        The code to be used for logging when a glyph index is used that is
        greater than or equal to the number of glyphs in the font.
        
        Default is ``'G0005'``.
    
    ``mask_validatecode_unsignedvaluetoolarge``
        The code to be used for logging when an unsigned value does not fit in
        its field.
        
        Default is ``'G0011'``.
    
    ``mask_validatefunc``
        A function taking one positional argument, the value, and an arbitrary
        number of keyword arguments. The function returns True if the object is
        valid (that is, if no errors are present).

        This function must do all item checking. If you want the default
        checking (glyph indices, scalable values, etc.) then use
        ``mask_validatefunc_partial`` instead.
        
        There is no default.
    
    ``mask_validatefunc_partial``
        A function taking one positional argument, a sequence value, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` **will** be passed into this function, unlike most other
        actions.

        This function does not need to do checking on standard things like
        glyph indices or scalable values. If you prefer to do all checking in
        your function, use a ``mask_validatefunc`` instead.
        
        There is no default.
    
    ``mask_wisdom``
        A string encompassing a sensible description of the value, including
        how it is used.
        
        There is, alas, no default for wisdom.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import invariants
from fontio3.utilities import pp, span2, valassist, walkerbit, writer

# -----------------------------------------------------------------------------

#
# Constants
#

validMaskControlsKeys = frozenset([
  'combinedstringfunc',
  'fillmissingwithone',
  'inputconvolutionfunc',
  'loggername',
  'outputconvolutionfunc',
  'recalculatefunc_partial',
  'validate_notsettoone_iserror',
  'validate_notsettozero_iserror',
  'validatecode_notsettoone',
  'validatecode_notsettozero',
  'validatefunc_partial',
  'wisdom'])

validMaskSpecKeys = frozenset([
  'mask_bitcount',
  'mask_boolstrings',
  'mask_constantvalue',
  'mask_enumstrings',
  'mask_enumstringsdict',
  'mask_fixedcharacteristic',
  'mask_ignoreforcomparisons',
  'mask_initfunc',
  'mask_inputcheckfunc',
  'mask_isantibool',
  'mask_isbool',
  'mask_iscvtindex',
  'mask_isenum',
  'mask_isfdefindex',
  'mask_isfixed',
  'mask_isglyphindex',
  'mask_isnameindex',
  'mask_isoutputglyph',
  'mask_ispc',
  'mask_ispointindex',
  'mask_issigned',
  'mask_isstorageindex',
  'mask_label',
  'mask_mergecheckequality',
  'mask_prevalidatedglyphset',
  'mask_python3rounding',
  'mask_recalculatefunc',
  'mask_representsx',
  'mask_representsy',
  'mask_rightmostbitindex',
  'mask_roundfunc',
  'mask_scales',
  'mask_scalesnoround',
  'mask_showonlyiffuncobj',
  'mask_showonlyiftrue',
  'mask_strusesrepr',
  'mask_transformcounterpart',
  'mask_transformnoround',
  'mask_usenamerforstr',
  'mask_validatecode_badenumvalue',
  'mask_validatecode_namenotintable',
  'mask_validatecode_negativecvt',
  'mask_validatecode_negativeglyph',
  'mask_validatecode_negativeinteger',
  'mask_validatecode_nocvt',
  'mask_validatecode_nonintegercvt',
  'mask_validatecode_nonintegerglyph',
  'mask_validatecode_nonintegralinteger',
  'mask_validatecode_nonnumericcvt',
  'mask_validatecode_nonnumericglyph',
  'mask_validatecode_nonnumericinteger',
  'mask_validatecode_nonnumericnumber',
  'mask_validatecode_signedvaluetoolarge',
  'mask_validatecode_toolargecvt',
  'mask_validatecode_toolargeglyph',
  'mask_validatecode_unsignedvaluetoolarge',
  'mask_validatefunc',
  'mask_validatefunc_partial',
  'mask_wisdom'])

# note that 'T' is natively supported for walkers    
_wFormats = {1: 'B', 2: 'H', 3: 'T', 4: 'L', 8: 'Q'}

# -----------------------------------------------------------------------------

#
# Methods
#

def CM_fromnumber(cls, n, **kwArgs):
    """
    Creates and returns a new object via unpacking the specified numeric value.
    
    :param n: The numeric value containing the whole object
    :type n: int
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object
    :rtype: *cls*
    
    .. note::
    
        This is a class method!
    
    The following ``kwArgs`` are supported:
    
    ``logger``
        A logger to which errors, warnings, and general information will be
        posted. This can be an object obtained from the utility function
        :py:func:`~fontio3.utilities.makeDoctestLogger`, for example.
    
    The integer (which in Python 3, recall, is not limited to any given number
    of bytes) contains the data for the object, with bit fields defined as in
    the maskSpec.
    
    >>> print(TestClass2.fromnumber(0x00014000).x)
    1.25
    
    >>> TestClass8.fromnumber(0).pprint()
    Normal enabled: False
    Antibool enabled: True
    
    >>> TestClass8.fromnumber(1).pprint()
    Normal enabled: True
    Antibool enabled: True
    
    >>> TestClass8.fromnumber(2).pprint()
    Normal enabled: False
    Antibool enabled: False
    
    >>> TestClass8.fromnumber(3).pprint()
    Normal enabled: True
    Antibool enabled: False
    
    In this test, note that the maskSpec identifies the "lastBit" as being
    bit 0, which we interpret here as the LSB. The custom inputconvolutionfunc
    reverses the bits in the number, allowing the instantiation to work:
    
    >>> TestClass13.fromnumber(0x8000).pprint()
    lastBit: True
    
    Here we see how a message is logged if a constant field gets an unexpected
    value:
    
    >>> TestClass15.fromnumber(0x0902).pprint()
    Symbol group: 9
    nonconst: 2
    
    >>> logger=utilities.makeDoctestLogger("maskmeta")
    >>> TestClass15.fromnumber(0x0204, logger=logger).pprint()
    maskmeta - WARNING - Bad value of '2' for field 'const9'; '9' used instead.
    Symbol group: 9
    nonconst: 4
   
    >>> TestClass.fromnumber(0xFFFF).getRawMask()
    65535
    """
    
    nCopy = n
    
    if 'inputconvolutionfunc' in cls._MASKCTRL:
        n = cls._MASKCTRL['inputconvolutionfunc'](n)
    
    logger = kwArgs.get('logger')
    
    d = {}
    
    for key, md in sorted(cls._MASKSPEC.items(), key=operator.itemgetter(0)):
        if md.get('mask_isbool', False):
            d[key] = bool(n & (1 << md['mask_rightmostbitindex']))
        
        elif md.get('mask_isantibool', False):
            d[key] = not bool(n & (1 << md['mask_rightmostbitindex']))
        
        else:
            startBit = md['mask_rightmostbitindex']
            count = md['mask_bitcount']
            subMask = (2 ** count - 1) << startBit
            x = (n & subMask) >> startBit
            
            if md.get('mask_isenum', False):
                if 'mask_enumstrings' in md:
                    if x >= len(md['mask_enumstrings']):
                        if logger is not None:
                            logger.warning((
                              'Vxxxx',
                              (key,),
                              "Bad enum value for '%s'; 0 used instead."))
                        x = 0
                    
                    d[key] = md['mask_enumstrings'][x]
                
                else:
                    esd = md['mask_enumstringsdict']
                    
                    if x not in esd:
                        nonNoneKeys = set(esd) - {None}
                        x = (min(nonNoneKeys) if nonNoneKeys else None)
                        if logger is not None:
                            logger.warning((
                              'Vxxxx',
                              (key, x),
                              "Bad enum key for '%s'; %d used instead"))
                    
                    d[key] = md['mask_enumstringsdict'][x]
            
            else:
                if md.get('mask_issigned', False) and (x >> (count - 1)):
                    x -= (2 ** count)
                
                if md.get('mask_isfixed', False):
                    fc = md.get('mask_fixedcharacteristic', 16)
                    x /= (2 ** (count - fc))
                
                d[key] = x
        
        if 'mask_constantvalue' in md:
            if d[key] != md['mask_constantvalue']:
                if logger is not None:
                    logger.warning((
                      'Vxxxx',
                      (d[key], key, md['mask_constantvalue']),
                      "Bad value of '%s' for field '%s'; '%s' used instead."))

                d[key] = md['mask_constantvalue']
                    
    r = cls(**d)
    r.__dict__['_rawNumber'] = nCopy

    return r

def CM_fromvalidatednumber(cls, n, **kwArgs):
    """
    Creates and returns a new object via unpacking the specified numeric value,
    performing validation on the correctness of the binary data.
    
    :param n: The numeric value containing the whole object
    :type n: int
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object
    :rtype: *cls*
    
    .. note::
    
        This is a class method!
    
    The following ``kwArgs`` are supported:
    
    ``annotateBits``
        A boolean flag (default False) which, if True, causes more detail on
        which bits are causing problems to be included in the logger messages.
    
    ``logger``
        A logger to which errors, warnings, and general information will be
        posted. This can be an object obtained from the utility function
        :py:func:`~fontio3.utilities.makeDoctestLogger`, for example.
    
    The integer (which in Python 3, recall, is not limited to any given number
    of bytes) contains the data for the object, with bit fields defined as in
    the maskSpec.
    
    >>> logger = utilities.makeDoctestLogger("fvn")
    >>> obj = TestClass6.fromvalidatednumber(0x8001, logger=logger)
    fvn.genericmask - WARNING - All reserved bits should be set to 0, but some are 1.
    
    >>> fvn = TestClass6.fromvalidatednumber
    >>> obj = fvn(0xC000, logger=logger, annotateBits=True)
    fvn.genericmask - WARNING - Reserved bits [14, 15] set to 1 (expected 0).
    
    >>> fvn = TestClass12.fromvalidatednumber
    >>> obj = fvn(0xFFFC, logger=logger, annotateBits=True)
    fvn.genericmask - WARNING - Reserved bits [1] set to 0 (expected 1).
    
    >>> obj = TestClass15.fromvalidatednumber(0x0204, logger=logger)
    fvn.genericmask.const9 - ERROR - Field 'const9' should have a constant value of 9, but instead has a value of 2

    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     maskByteLength = 2
    ...     maskSpec  = dict(
    ...         a = dict(
    ...             mask_bitcount = 3,
    ...             mask_enumstrings = ['Z', 'R', 'K', 'E', 'A'],
    ...             mask_isenum = True,
    ...             mask_rightmostbitindex = 0),
    ...         b = dict(
    ...             mask_bitcount = 3,
    ...             mask_enumstringsdict = collections.defaultdict(
    ...               (lambda: "Bad"),
    ...               {0: 'z', 4: 'r', 6: 'a'}),
    ...             mask_isenum = True,
    ...             mask_rightmostbitindex = 3))
    >>> Test.fromvalidatednumber(0, logger=logger) == Test(a='Z', b='z')
    True
    
    >>> f = io.StringIO()
    >>> logger = utilities.makeDoctestLogger("fvn-sort", stream=f)
    >>> obj = Test.fromvalidatednumber(0x003E, logger=logger)
    >>> for s in sorted(f.getvalue().splitlines()): print(s)
    fvn-sort.genericmask.a - ERROR - Value 6 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    fvn-sort.genericmask.b - ERROR - Value 7 is not a valid enum value. 0 will be used instead, but the font should be fixed.
    >>> f.close()
    """
    
    logger = kwArgs.get('logger', None)
    labelbits = kwArgs.get('annotateBits', False)
    childName = cls._MASKCTRL.get('loggername', 'genericmask')
    
    if logger is None:
        logger = logging.getLogger().getChild(childName)
    else:
        logger = logger.getChild(childName)
    
    nCopy = n
    
    if 'inputconvolutionfunc' in cls._MASKCTRL:
        n = cls._MASKCTRL['inputconvolutionfunc'](n)
    
    # Check unassigned bits
    fillWithOnes = cls._MASKCTRL.get('fillmissingwithone', False)
    badbits = []
    
    for leftmostBit, bitCount, name in cls._FIELDMAP[False]:
        if name is None:
            startBit = leftmostBit - bitCount + 1
            subMask = (2 ** bitCount - 1) << startBit
            x = (n & subMask) >> startBit
            
            if fillWithOnes:
                if x != (2 ** bitCount - 1):
                    badbits += [
                      b
                      for b in range(startBit, leftmostBit + 1)
                      if (2**b) & n != (2**b)]
            
            else:
                if x:
                    badbits += [
                      b
                      for b in range(startBit, leftmostBit + 1)
                      if (2**b) & n == (2**b)]
                    
    isError = (
      cls._MASKCTRL.get('validate_notsettoone_iserror', False) or
      cls._MASKCTRL.get('validate_notsettozero_iserror', False))
    
    loggerfn = (logger.error if isError else logger.warning)
                    
    if len(badbits) > 0:
        if labelbits:
            if fillWithOnes:
                loggerfn((
                  cls._MASKCTRL.get('validatecode_notsettoone', 'G0015'),
                  (repr(sorted(badbits)),),
                  "Reserved bits %s set to 0 (expected 1)."))
            
            else:
                loggerfn((
                  cls._MASKCTRL.get('validatecode_notsettozero', 'G0014'),
                  (repr(sorted(badbits)),),
                  "Reserved bits %s set to 1 (expected 0)."))

        else:
            if fillWithOnes:
                loggerfn((
                  cls._MASKCTRL.get('validatecode_notsettoone', 'G0015'),
                  (),
                  "All reserved bits should be set to 1, but some are 0."))
            
            else:
                loggerfn((
                  cls._MASKCTRL.get('validatecode_notsettozero', 'G0014'),
                  (),
                  "All reserved bits should be set to 0, but some are 1."))
    
    # Now fill in fields (note that value validation does not happen here; it
    # happens in isValid() instead).
    
    d = {}
    okToReturn = True
    
    for key, md in sorted(cls._MASKSPEC.items(), key=operator.itemgetter(0)):
        if md.get('mask_isbool', False):
            d[key] = bool(n & (1 << md['mask_rightmostbitindex']))
        
        elif md.get('mask_isantibool', False):
            d[key] = not bool(n & (1 << md['mask_rightmostbitindex']))
        
        else:
            startBit = md['mask_rightmostbitindex']
            count = md['mask_bitcount']
            subMask = (2 ** count - 1) << startBit
            x = (n & subMask) >> startBit
            
            if md.get('mask_isenum', False):
                if 'mask_enumstrings' in md:
                    if x >= len(md['mask_enumstrings']):
                        logger.getChild(key).error((
                          md.get('mask_validatecode_badenumvalue', 'G0001'),
                          (x,),
                          "Value %d is not a valid enum value. 0 "
                          "will be used instead, but the font should "
                          "be fixed."))
                        
                        x = 0
                    
                    d[key] = md['mask_enumstrings'][x]
                
                else:
                    esd = md['mask_enumstringsdict']
                    
                    if x not in esd:
                        nonNoneKeys = set(esd) - {None}
                        xNew = (min(nonNoneKeys) if nonNoneKeys else None)
                        
                        logger.getChild(key).error((
                          md.get('mask_validatecode_badenumvalue', 'G0001'),
                          (x, xNew),
                          "Value %d is not a valid enum value. %r will "
                          "be used instead, but the font should be fixed."))
                        
                        x = xNew
                    
                    d[key] = md['mask_enumstringsdict'][x]
            
            else:
                if md.get('mask_issigned', False) and (x >> (count - 1)):
                    x -= (2 ** count)
                
                if md.get('mask_isfixed', False):
                    fc = md.get('mask_fixedcharacteristic', 16)
                    x /= (2 ** (count - fc))
                
                d[key] = x
        
        if 'mask_constantvalue' in md:
            if d[key] != md['mask_constantvalue']:
                logger.getChild(key).error((
                  'V0910',
                  (key, md['mask_constantvalue'], d[key]),
                  "Field '%s' should have a constant value of %s, "
                  "but instead has a value of %s"))
                
                okToReturn = False
    
    if okToReturn:
        r = cls(**d)
        r.__dict__['_rawNumber'] = nCopy
        return r
    
    return None

def CM_fromvalidatedwalker(cls, w, **kwArgs):
    """
    Creates and returns a new object via unpacking bytes from the specified
    walker, performing validation on the correctness of the binary data.
    
    :param w: A walker for the binary data to be consumed in making the new
        instance
    :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
        or equivalent
    :param kwArgs: Optional keyword arguments (see ``fromvalidatednumber``)
    :return: The new instance
    :rtype: *cls*

    .. note::
    
        This is a class method!
    
    The class attribute ``maskByteLength`` controls how many bytes will be
    used. This method is really just a shallow wrapper around a call to
    ``fromvalidatednumber()``.
    
    Unlike pretty much every other Protocol metaclass, this
    ``fromvalidatedwalker()`` method is actually provided here, and thus does
    not need to be added by the inheriting class.
    
    >>> s = utilities.fromhex("ED 2F")
    >>> sorted(
    ...   TestClass.frombytes(s).__dict__.items(),
    ...   key = operator.itemgetter(0))
    [('_rawNumber', 60719), ('a', -0.75), ('b', True), ('c', 'Third'), ('d', -1), ('u', 15)]
    """
    
    mbl = cls._MASKCTRL['maskByteLength']
    
    try:
        n = w.unpack(_wFormats[mbl])
    except KeyError:
        v = w.group("B", mbl)
        n = functools.reduce((lambda x,y: 256 * x + y), v)
    
    return cls.fromvalidatednumber(n, **kwArgs)

def CM_fromwalker(cls, w, **kwArgs):
    """
    Creates and returns a new object via unpacking bytes from the specified
    walker.
    
    :param w: A walker for the binary data to be consumed in making the new
        instance
    :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
        or equivalent
    :param kwArgs: Optional keyword arguments (see ``fromnumber``)
    :return: The new instance
    :rtype: *cls*

    .. note::
    
        This is a class method!
    
    The class attribute ``maskByteLength`` controls how many bytes will be
    used. This method is really just a shallow wrapper around a call to
    ``fromnumber()``.
    
    Unlike pretty much every other Protocol metaclass, this ``fromwalker()``
    method is actually provided here, and thus does not need to be added by the
    inheriting class.
    
    >>> s = utilities.fromhex("ED 2F")
    >>> sorted(
    ...   TestClass.frombytes(s).__dict__.items(),
    ...   key = operator.itemgetter(0))
    [('_rawNumber', 60719), ('a', -0.75), ('b', True), ('c', 'Third'), ('d', -1), ('u', 15)]
    """
    
    mbl = cls._MASKCTRL['maskByteLength']
    
    try:
        n = w.unpack(_wFormats[mbl])
    except KeyError:
        v = w.group("B", mbl)
        n = functools.reduce((lambda x,y: 256 * x + y), v)
    
    return cls.fromnumber(n, **kwArgs)

def M_asImmutable(self, **kwArgs):
    """
    Returns a simple tuple with the object's contents, suitable for use as
    a dict key or in a set.
    
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The immutable version
    :rtype: tuple
    
    The returned object is a tuple with two elements: the name string of the
    type object, and a tuple of (key, value) pairs, sorted by key (for
    reproducibility).
    """
    
    return (
      type(self).__name__,
      tuple((k, self.__dict__[k]) for k in sorted(self.__dict__)))

def M_buildBinary(self, w, **kwArgs):
    """
    Adds the binary content for the object to the specified writer.
    
    :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    :raises ValueError: if ``doValidation`` is True and validation fails
    
    Note that unlike every other Protocol metaclass, this ``buildBinary()``
    method is already provided and thus does not need to be added by the
    inheriting class.
    
    The following ``kwArgs`` are supported:
    
    ``doValidation``
        If True then the object will have ``isValid()`` called on it before its
        contents get added to the writer. If validation fails, a ``ValueError``
        will be raised.

    >>> utilities.hexdump(TestClass.fromnumber(0xED2F).binaryString())
           0 | ED2F                                     |./              |
    
    >>> utilities.hexdump(TestClass12(first=True, last=True).binaryString())
           0 | 7FFE                                     |..              |
    
    >>> utilities.hexdump(TestClass13.fromnumber(0x8000).binaryString())
           0 | 8000                                     |..              |
    """
    
    if kwArgs.get('doValidation', False) and (not self.isValid(**kwArgs)):
        raise ValueError("Object failed validation!")
    
    wSave = w
    w = writer.LinkedWriter()
    cd = self.__class__.__dict__
    MS = cd['_MASKSPEC']
    fillWith1s = cd['_MASKCTRL'].get('fillmissingwithone', False)
    
    for start, count, key in cd['_FIELDMAP'][False]:
        if key is None:
            w.addBitsFromNumber(((2 ** count) - 1 if fillWith1s else 0), count)
        
        else:
            d = MS[key]
            
            # We do the constant value check here, in case validation was
            # skipped.
            
            if 'mask_constantvalue' in d:
                value = d['mask_constantvalue']
            else:
                value = self.__dict__[key]
            
            if d.get('mask_isbool', False):
                w.addBits(('\x80' if value else '\x00'), 1)
            
            elif d.get('mask_isantibool', False):
                w.addBits(('\x00' if value else '\x80'), 1)
            
            elif d.get('mask_isenum', False):
                value = cd['_MASKINV'][key][value]
                w.addBitsFromNumber(value, count)
            
            else:
                if d.get('mask_isfixed', False):
                    shift = count - d.get('mask_fixedcharacteristic', 16)
                    value = int(round(value * (2.0 ** shift)))
                
                w.addBitsFromNumber(value, count)
    
    if 'outputconvolutionfunc' in cd['_MASKCTRL']:
        s = w.binaryString()
        t = walkerbit.StringWalker(s).unpackRest("B")
        n = functools.reduce((lambda x,y: 256 * x + y), t)
        n = cd['_MASKCTRL']['outputconvolutionfunc'](n)
        w = writer.LinkedWriter()
        mBits = cd['_MASKCTRL']['maskByteLength'] * 8
        w.addBitsFromNumber(n, mBits)
    
    wSave.addString(w.binaryString())

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
    
    ``fieldName``
         A required string, identifying a field of the object. The
         ``mask_inputcheckfunc`` will be applied to this field.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...   maskByteLength = 4
    ...   maskSpec  = dict(
    ...     a = dict(
    ...       mask_bitcount = 16,
    ...       mask_inputcheckfunc = (lambda x, **k: 0 <= x < 5),
    ...       mask_issigned = False,
    ...       mask_rightmostbitindex = 16),
    ...     b = dict(
    ...       mask_bitcount = 16,
    ...       mask_inputcheckfunc = (lambda x, **k: 100 <= x < 200),
    ...       mask_issigned = False,
    ...       mask_rightmostbitindex = 0))
    >>> m = Test(a=1, b=120)
    >>> m.checkInput(4, fieldName='a')
    True
    >>> m.checkInput(6, fieldName='a')
    False
    >>> m.checkInput(145, fieldName='b')
    True
    >>> m.checkInput(2, fieldName='b')
    False
    """
    
    fieldName = kwArgs['fieldName']  # must be present
    md = self.__class__._MASKSPEC[fieldName]
    f = md.get('mask_inputcheckfunc', None)
    
    if f is None:
        return True
    
    return f(valueToCheck, **kwArgs)

def M_coalesced(self, **kwArgs):
    """
    Returns a copy of the object, since coalescing does nothing meaningful for
    masklike objects.
    
    :return: Shallow copy of ``self``
    :rtype: Same as ``self``
    """
    
    return type(self)(**self.__dict__)

def M_compacted(self, **kwArgs):
    """
    Returns a copy of the object, since compacting does nothing meaningful for
    masklike objects.
    
    :return: Shallow copy of ``self``
    :rtype: Same as ``self``
    """
    
    return type(self)(**self.__dict__)

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
        This must be True for masklike classes, since you cannot leave a hole
        in mask data.

    ``oldToNew``
        A dict mapping old CVT indices to new ones. Note that it's OK for this
        dict to not map every single old CVT index; what happens if this occurs
        is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``cvtDelta``, ``cvtMappingFunc``, or
      ``oldToNew``.
    
    >>> k1 = TestClass9(cvt=20)
    
    >>> print(k1.cvtsRenumbered(cvtDelta=50))
    cvt = 70
    
    >>> print(k1.cvtsRenumbered(oldToNew={20: 400}))
    cvt = 400
    >>> print(k1.cvtsRenumbered(oldToNew={}))
    cvt = 20
    
    >>> def f(n, **k):
    ...     return n + (150 if n % 10 else 88)
    >>> print(k1.cvtsRenumbered(cvtMappingFunc=f))
    cvt = 108
    """
    
    d = self.__dict__.copy()
    cvtMappingFunc = kwArgs.get('cvtMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    cvtDelta = kwArgs.get('cvtDelta', None)
    
    if cvtMappingFunc is not None:
        pass
    
    elif oldToNew is not None:
        cvtMappingFunc = (
          lambda x, **k:
          oldToNew.get(x, (x if keepMissing else None)))
    
    elif cvtDelta is not None:
        cvtMappingFunc = (lambda x, **k: x + cvtDelta)
    
    else:
        cvtMappingFunc = (lambda x, **k: x)
    
    for k, md in self.__class__._MASKSPEC.items():
        if not md.get('mask_iscvtindex', False):
            continue
        
        assert keepMissing  # cannot have keepMissing False for masks
        d[k] = cvtMappingFunc(d[k], **kwArgs)
    
    return type(self)(**d)

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
        This must be True for masklike classes, since you cannot leave a hole
        in mask data.

    ``oldToNew``
        A dict mapping old FDEF indices to new ones. Note that it's OK for this
        dict to not map every single old FDEF index; what happens if this
        occurs is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``fdefMappingFunc`` or ``oldToNew``.
    
    >>> k1 = TestClass10(fdef=20)
    
    >>> print(k1.fdefsRenumbered(oldToNew={20: 400}))
    fdef = 400
    >>> print(k1.fdefsRenumbered(oldToNew={}))
    fdef = 20
    
    >>> def f(n, **k):
    ...     return n + (150 if n % 10 else 88)
    >>> print(k1.fdefsRenumbered(fdefMappingFunc=f))
    fdef = 108
    """
    
    d = self.__dict__.copy()
    fdefMappingFunc = kwArgs.get('fdefMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    
    if fdefMappingFunc is not None:
        pass
    
    elif oldToNew is not None:
        fdefMappingFunc = (
          lambda x, **k:
          oldToNew.get(x, (x if keepMissing else None)))
    
    else:
        fdefMappingFunc = lambda x,**k: x
    
    for k, md in self.__class__._MASKSPEC.items():
        if not md.get('mask_isfdefindex', False):
            continue
        
        assert keepMissing  # cannot have keepMissing False for masks
        d[k] = fdefMappingFunc(d[k], **kwArgs)
    
    return type(self)(**d)

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
    
    >>> obj = TestClass3(isSpecial=True, gIn=400, gOut=555)
    >>> list(obj.gatheredInputGlyphs())
    [400]
    """
    
    d = self.__dict__
    MS = self.__class__._MASKSPEC
    ig = set()
    
    for k, md in MS.items():
        if (
          md.get('mask_isglyphindex', False) and
          (not md.get('mask_isoutputglyph', False))):
            
            ig.add(d[k])
    
    return ig

def M_gatheredLivingDeltas(self, **kwArgs):
    """
    Returns an empty set, since masklike objects cannot contain LivingDeltas.
    
    :return: An empty set
    :rtype: set
    """
    
    return set()

def M_gatheredMaxContext(self, **kwArgs):
    """
    Return an integer representing the ``'OS/2'`` maximum context value.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The maximum context
    :rtype: int

    This method is used to recursively walk OpenType or AAT tables to obtain
    the largest matching context used anywhere.

    You will rarely need to call this method.
    """
    
    MS = self.__class__._MASKSPEC
    
    return (
      1 if any(d.get('mask_isglyphindex', False) for d in MS.values())
      else 0)

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
    
    >>> obj = TestClass3(isSpecial=True, gIn=400, gOut=555)
    >>> list(obj.gatheredOutputGlyphs())
    [555]
    """
    
    d = self.__dict__
    MS = self.__class__._MASKSPEC
    og = set()
    
    for k, md in MS.items():
        if (
          md.get('mask_isglyphindex', False) and
          md.get('mask_isoutputglyph', False)):
            
            og.add(d[k])
    
    return og

def M_gatheredRefs(self, **kwArgs):
    """
    Returns an empty dict, since masklike objects cannot contain Lookups.
    
    :return: An empty dict
    :rtype: dict
    """
    
    return {}

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
        This must be True for masklike classes, since you cannot leave a hole
        in mask data.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.
    
    >>> obj = TestClass3(gIn=30, gOut=40)
    >>> obj2 = obj.glyphsRenumbered({30: 200})
    >>> obj2.gIn, obj2.gOut
    (200, 40)
    """
    
    d = self.__dict__.copy()
    
    for k, md in self.__class__._MASKSPEC.items():
        if not md.get('mask_isglyphindex', False):
            continue
        
        assert kwArgs.get('keepMissing', True)  # masks require keepMissing set
        d[k] = oldToNew.get(d[k], d[k])
    
    return type(self)(**d)

def M_hasCycles(self, **kwArgs):
    """
    Returns False (no instance of a maskmeta-derived classes can have cycles,
    by its very nature).
    
    :return: False
    """
    
    return False

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
    
    >>> logger = utilities.makeDoctestLogger("Test")
    >>> e = utilities.fakeEditor(0x10000)
    >>> obj = TestClass15(nonconst=5)
    >>> obj.const9 == 9
    True
    >>> obj.const9 = 14
    >>> obj.isValid(logger=logger, editor=e)
    Test.const9 - ERROR - Field 'const9' should have a constant value of 9, but instead has a value of 14
    False
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     maskSpec = {
    ...       'a': {
    ...         'mask_isbool': True,
    ...         'mask_rightmostbitindex': 0},
    ...       'b': {
    ...         'mask_isglyphindex': True,
    ...         'mask_bitcount': 7,
    ...         'mask_rightmostbitindex': 1},
    ...       'c': {
    ...         'mask_issigned': True,
    ...         'mask_bitcount': 3,
    ...         'mask_rightmostbitindex': 8},
    ...       'd': {
    ...         'mask_isfixed': True,
    ...         'mask_bitcount': 32,
    ...         'mask_rightmostbitindex': 11},
    ...       'e': {
    ...         'mask_isenum': True,
    ...         'mask_enumstrings': ['Z', 'Y', 'X', 'W'],
    ...         'mask_bitcount': 2,
    ...         'mask_rightmostbitindex': 43},
    ...       'f': {
    ...         'mask_isfixed': True,
    ...         'mask_issigned': True,
    ...         'mask_bitcount': 16,
    ...         'mask_fixedcharacteristic': 2,
    ...         'mask_rightmostbitindex': 45}}
    ...     maskByteLength = 8
    
    >>> t1 = Test(a=True, b=50, c=-3, d=10.5, e='Y', f=0.75)
    >>> t1.isValid(logger=logger, editor=e)
    True
    
    >>> t2 = Test(b=150, c=-5, d="Fred", f=2.75)
    >>> t2.e = 'A'
    >>> t2.isValid(logger=logger, fontGlyphCount=120, editor=e)
    Test.b - ERROR - The glyph index 150 does not fit in 7 bits.
    Test.c - ERROR - The signed value -5 does not fit in 3 bits.
    Test.d - ERROR - The value 'Fred' is not a real number.
    Test.e - ERROR - Value 'A' is not a valid enum value.
    Test.f - ERROR - The value 2.75 cannot be represented in signed (2.14) format.
    False
    """
    
    cd = self.__class__.__dict__
    MS = cd['_MASKSPEC']
    d = self.__dict__
    r = True
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
    wholeFuncPartial = cd['_MASKCTRL'].get('validatefunc_partial', None)
    
    if logger is None:
        s = __name__[__name__.rfind('.')+1:]
        logger = logging.getLogger().getChild(s)
    
    if wholeFuncPartial is not None:
        r = wholeFuncPartial(self, logger=logger, **kwArgs) and r
    
    for k, md in sorted(MS.items(), key=operator.itemgetter(0)):
        obj = d[k]
        attrLogger = logger.getChild(k)
        
        if 'mask_constantvalue' in md and obj != md['mask_constantvalue']:
            attrLogger.error((
              'V0910',
              (k, md['mask_constantvalue'], obj),
              "Field '%s' should have a constant value of %s, "
              "but instead has a value of %s"))
            
            r = False
        
        f = md.get('mask_validatefunc', None)
        pvs = md.get('mask_prevalidatedglyphset', set())
        numBits = md.get('mask_bitcount', 1)
        signed = md.get('mask_issigned', False)
        
        if f is not None:
            r = f(obj, logger=attrLogger, **kwArgs) and r
        
        else:
            fp = md.get('mask_validatefunc_partial', None)
            
            if fp is not None:
                r = fp(obj, logger=attrLogger, **kwArgs) and r
            
            if md.get('mask_isenum', False):
                try:
                    cd['_MASKINV'][k][obj]
                
                except KeyError:
                    attrLogger.error((
                      md.get('mask_validatecode_badenumvalue', 'G0001'),
                      (obj,),
                      "Value %r is not a valid enum value."))
                    
                    r = False
            
            elif (
              md.get('mask_isglyphindex', False) or
              md.get('mask_isoutputglyph', False)):
                
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  numBits = numBits,
                  label = "glyph index",
                  logger = attrLogger):
                  
                    r = False
                
                elif (obj not in pvs) and (obj >= fontGlyphCount):
                    attrLogger.error((
                      md.get('mask_validatecode_toolargeglyph', 'G0005'),
                      (obj,),
                      "Glyph index %d is too large."))
                    
                    r = False
            
            elif md.get('mask_isnameindex', False):
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  numBits = numBits,
                  label = "name table index",
                  logger = attrLogger):
                  
                    r = False
                
                elif obj not in namesInTable:
                    attrLogger.error((
                      md.get('mask_validatecode_namenotintable', 'G0042'),
                      (obj,),
                      "Name table index %d not present in 'name' table."))
                    
                    r = False
            
            elif md.get('mask_iscvtindex', False):
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  numBits = numBits,
                  label = "CVT index",
                  logger = attrLogger):
                  
                    r = False
                
                elif editor is not None:
                    if b'cvt ' not in editor:
                        attrLogger.error((
                          md.get('item_validatecode_nocvt', 'G0030'),
                          (obj,),
                          "CVT Index %d is being used, but the font "
                          "has no Control Value Table."))
                        
                        r = False
                    
                    elif obj >= len(editor[b'cvt ']):
                        attrLogger.error((
                          md.get(
                            'item_validatecode_toolargecvt',
                            'G0029'),
                          (obj,),
                          "CVT index %d is not defined."))
                        
                        r = False
            
            elif md.get('mask_ispc', False):
                
                # We want to allow for signed jump distances being treated as
                # program counter values, so we do an explicit sign check
                
                if signed:
                    f = valassist.isNumber_integer_signed
                    doc = "jump distance"
                else:
                    f = valassist.isNumber_integer_unsigned
                    doc = "program counter"
                
                if not f(obj, numBits=numBits, label=doc, logger=attrLogger):
                    r = False
            
            elif md.get('mask_ispointindex', False):
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  numBits = numBits,
                  label = "point index",
                  logger = attrLogger):
                  
                    r = False
            
            elif md.get('mask_isstorageindex', False):
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  numBits = numBits,
                  label = "storage index",
                  logger = attrLogger):
                  
                    r = False
                
                elif obj > maxStorage:
                    attrLogger.error((
                      'E6047',
                      (obj, maxStorage),
                      "The storage index %d is greater than the "
                      "font's defined maximum of %d."))
                    
                    r = False
            
            elif md.get('mask_isfixed', False):
                if not valassist.isNumber_fixed(
                  obj,
                  numBits = numBits,
                  signed = signed,
                  characteristic = md.get('mask_fixedcharacteristic', 16),
                  logger = attrLogger):
                  
                    r = False
            
            elif signed:
                if not valassist.isNumber_integer_signed(
                  obj,
                  numBits = numBits,
                  logger = attrLogger):
                  
                    r = False
            
            else:
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  numBits = numBits,
                  logger = attrLogger):
                  
                    r = False
    
    return r

def M_merged(self, other, **kwArgs):
    r"""
    Returns a new object representing the merger of ``other`` into ``self``.
    
    :param other: The object to be merged into ``self``
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A new object representing the merger
    
    There are no keyword arguments supported here; specifically,
    ``conflictPreferOther`` and ``replaceWhole`` are *not* supported. The
    action is always for ``other``\’s values to replace ``self``\’s, except
    where ``mask_mergecheckequality`` is explicitly set for a particular value.
    
    >>> obj1 = TestClass.fromnumber(0xED2F)
    >>> obj2 = obj1.__copy__()
    >>> obj1.a, obj2.a
    (-0.75, -0.75)
    >>> obj2.a = 0.125
    >>> obj3 = obj1.merged(obj2)
    >>> obj3.a, obj3.a
    (0.125, 0.125)
    >>> obj2.c = "Last"
    >>> obj4 = obj1.merged(obj2)
    Traceback (most recent call last):
      ...
    ValueError: Attempt to merge unequal values!
    """
    
    d = self.__dict__.copy()
    dOther = other.__dict__
    
    for k, md in self.__class__._MASKSPEC.items():
        objSelf = d[k]
        objOther = dOther[k]
        
        if objSelf != objOther:
            if md.get('mask_mergecheckequality', False):
                raise ValueError("Attempt to merge unequal values!")
            
            d[k] = objOther
    
    return type(self)(**d)

def M_namesRenumbered(self, oldToNew, **kwArgs):
    """
    Return a new object with ``'name'`` table references renumbered.
    
    :param oldToNew: A dict mapping old to new indices
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with names renumbered
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        This must be True for masklike classes, since you cannot leave a hole
        in mask data.
    
    >>> e = _fakeEditor()
    >>> obj = TestClass14(nameIndex=303)
    >>> obj.pprint(editor=e)
    nameIndex: 303 ('Required Ligatures On')
    
    >>> obj.namesRenumbered({303: 306}).pprint(editor=e)
    nameIndex: 306 ('Regular')
    """
    
    d = self.__dict__.copy()
    
    for k, md in self.__class__._MASKSPEC.items():
        if not md.get('mask_isnameindex', False):
            continue
        
        assert kwArgs.get('keepMissing', True)  # masks require keepMissing set
        d[k] = oldToNew.get(d[k], d[k])
    
    return type(self)(**d)
    
def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> obj = TestClass7(pc=50)
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> obj.pcsRenumbered(mapData, infoString="testcode").pc
    53
    """
    
    d = self.__dict__.copy()
    
    for k, md in self.__class__._MASKSPEC.items():
        if md.get('mask_ispc', False):
            oldValue = d[k]
            delta = 0
            it = mapData.get(kwArgs.get('infoString', None), [])
            
            for threshold, newDelta in it:
                if oldValue < threshold:
                    break
                
                delta = newDelta
            
            d[k] = oldValue + delta
    
    return type(self)(**d)

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
        This must be True for masklike classes, since you cannot leave a hole
        in mask data.
    
    >>> obj = TestClass4(point=4)
    >>> obj2 = obj.pointsRenumbered({25: {4: 3, 3: 4}}, glyphIndex=25)
    >>> obj2.point
    3
    """
    
    d = self.__dict__.copy()
    glyphIndex = kwArgs.get('glyphIndex')
    
    if (glyphIndex is not None) and (glyphIndex in mapData):
        thisMap = mapData[glyphIndex]
        
        for k, md in self.__class__._MASKSPEC.items():
            if not md.get('mask_ispointindex', False):
                continue
            
            assert kwArgs.get('keepMissing', True)
            oldPoint = d[k]
            newPoint = thisMap.get(oldPoint, oldPoint)
            
            if newPoint != oldPoint:
                d[k] = newPoint
    
    return type(self)(**d)

def M_pprint(self, **kwArgs):
    """
    Pretty-print the object and its attributes.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    
    The following ``kwArgs`` are supported:
    
    ``annotateBits``
        If True, each item's label will also include which bits the item
        occupies.
    
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
    
    >>> TestClass.fromnumber(0xED2F).pprint()
    enum: Third
    signed: -1
    fixed: -0.75
    unsigned: 15
    bool: True
    >>> TestClass.fromnumber(0xED2F).pprint(annotateBits=True)
    enum (bits 8-7): Third
    signed (bit 5): -1
    fixed (bits 15-11): -0.75
    unsigned (bits 3-0): 15
    bool (bit 10): True
    
    >>> obj = TestClass3(isSpecial=True, gIn=52, gOut=98)
    >>> obj.pprint()
    Input glyph: 52
    Output glyph: 98
    Glyph is special: True
    >>> obj.pprint(namer=namer.testingNamer())
    Input glyph: xyz53
    Output glyph: afii60003
    Glyph is special: True
    
    >>> TestClass6.fromnumber(0x03).pprint(label="Mac Style")
    Mac Style: Bold Italic
    >>> TestClass6.fromnumber(0).pprint()
    Plain
    
    >>> e = _fakeEditor()
    >>> TestClass14(nameIndex=303).pprint()
    nameIndex: 303
    >>> TestClass14(nameIndex=303).pprint(editor=e)
    nameIndex: 303 ('Required Ligatures On')
    """
    
    d = self.__dict__
    cd = self.__class__.__dict__
    MS = cd['_MASKSPEC']
    CS = cd['_MASKCTRL']
    
    if 'combinedstringfunc' in CS:
        saveLabel = kwArgs.pop('label', None)
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        sv = []
        
        for t in cd['_FIELDMAP'][True]:
            k = t[2]
            
            if d[k]:
                sv.append(MS[k].get('mask_label', k))
        
        p.simple(CS['combinedstringfunc'](sv), label=saveLabel)
        return
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    doAnnotation = kwArgs.get('annotateBits', False)
    nm = kwArgs.get('namer', self.getNamer())
    
    for t in cd['_FIELDMAP'][True]:
        firstBit, bitCount, k = t
        value = d[k]
        md = MS[k]
        boolStrings = md.get('mask_boolstrings', None)
        
        if boolStrings is not None:
            if doAnnotation:
                p("%s (bit %d)" % (boolStrings[value], firstBit))
            else:
                p(boolStrings[value])
            
            continue
        
        soitCase = False
        
        if md.get('mask_showonlyiftrue', False):
            if value:
                if (
                  md.get('mask_isbool', False) or
                  md.get('mask_isantibool', False)):
                    
                    soitCase = True
            
            else:
                continue
        
        if 'mask_constantvalue' in md:
            soitCase = True
        
        f = md.get('mask_showonlyiffuncobj')
        
        if (f is not None) and (not f(self)):
            continue
        
        s = md.get('mask_label', k)
        
        if doAnnotation:
            if bitCount == 1:
                label = "%s (bit %d)" % (s, firstBit)
            
            else:
                label = (
                  "%s (bits %d-%d)" %
                  (s, firstBit, firstBit - bitCount + 1))
        
        else:
            label = s
        
        if (
          md.get('mask_isglyphindex', False) and
          md.get('mask_usenamerforstr', False) and
          nm):
            
            value = nm.bestNameForGlyphIndex(value)
        
        elif md.get('mask_isnameindex', False):
            value = utilities.nameFromKwArgs(value, **kwArgs)
        
        if soitCase:
            p(label)
        else:
            p.simple(value, label=label)

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
    
    >>> oldObj = TestClass.fromnumber(0xED2F)
    >>> newObj = oldObj.__copy__()
    >>> newObj.a = 0.5
    >>> newObj.c = 'Second'
    >>> newObj.pprint_changes(oldObj)
    enum changed from Third to Second
    fixed changed from -0.75 to 0.5
    
    >>> oldObj = TestClass3(gIn=20, gOut=40)
    >>> newObj = TestClass3(gIn=44, gOut=98)
    >>> newObj.pprint_changes(oldObj)
    Input glyph changed from 20 to 44
    Output glyph changed from 40 to 98
    >>> newObj.pprint_changes(oldObj, namer=namer.testingNamer())
    Input glyph changed from xyz21 to xyz45
    Output glyph changed from xyz41 to afii60003
    """
    
    if self != prior:
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        kwArgs.pop('label', None)
        MS = self.__class__._MASKSPEC
        dSelf = self.__dict__
        dPrior = prior.__dict__
        nm = kwArgs.get('namer', self.getNamer())
        
        for t in self.__class__._FIELDMAP[True]:
            k = t[2]
            oldValue = dPrior[k]
            newValue = dSelf[k]
            
            if oldValue == newValue:
                continue
            
            md = MS[k]
            label = md.get('mask_label', k)
            
            if (
              md.get('mask_isglyphindex', False) and
              md.get('mask_usenamerforstr', False) and
              nm):
                
                f = nm.bestNameForGlyphIndex
                oldValue = f(oldValue)
                newValue = f(newValue)
            
            p("%s changed from %s to %s" % (label, oldValue, newValue))

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        This is required, and should be an
        :py:class:`~fontio3.fontedit.Editor`-class object.
    
    >>> obj = TestClass.fromnumber(0xED2F)
    >>> obj.a
    -0.75
    >>> obj2 = obj.recalculated(adjust_a = 1.25)
    >>> obj2.a
    0.5
    """
    
    fWholePartial = self._MASKCTRL.get('recalculatefunc_partial', None)
    
    if fWholePartial is not None:
        d = fWholePartial(self, **kwArgs)[1].__dict__
    else:
        d = self.__dict__.copy()
    
    for k, md in self.__class__._MASKSPEC.items():
        f = md.get('mask_recalculatefunc', None)
        
        if f is not None:
            changed, newValue = f(d[k], **kwArgs)
            
            if changed:
                d[k] = newValue
    
    return type(self)(**d)

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
    
    >>> obj = TestClass2(x=1.5)
    >>> obj.scaled(3.0).x
    4.5
    >>> obj.scaled(3.0, scaleOnlyInY=True).x
    1.5
    """
    
    d = self.__dict__.copy()
    scaleOnlyInX = kwArgs.get('scaleOnlyInX', False)
    scaleOnlyInY = kwArgs.get('scaleOnlyInY', False)
    
    if scaleOnlyInX and scaleOnlyInY:
        scaleOnlyInX = scaleOnlyInY = False
    
    if scaleFactor != 1.0:
        for k, md in self.__class__._MASKSPEC.items():
            if md.get('mask_representsx', False) and scaleOnlyInY:
                continue
            
            if md.get('mask_representsy', False) and scaleOnlyInX:
                continue
            
            if md.get('mask_scalesnoround', False):
                d[k] *= scaleFactor
            
            elif md.get('mask_scales', False):
                roundFunc = md.get('mask_roundfunc', None)
                
                if roundFunc is None:
                    if md.get('mask_python3rounding', False):
                        roundFunc = utilities.newRound
                    else:
                        roundFunc = utilities.oldRound
                
                d[k] = roundFunc(scaleFactor * d[k], castType=type(d[k]))
    
    return type(self)(**d)

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
        This must be True for masklike classes, since you cannot leave a hole
        in mask data.

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
    
    >>> k1 = TestClass11(storage=20)
    
    >>> print(k1.storageRenumbered(storageDelta=50))
    storage = 70
    
    >>> print(k1.storageRenumbered(oldToNew={20: 400}))
    storage = 400
    >>> print(k1.storageRenumbered(oldToNew={}))
    storage = 20
    
    >>> def f(n, **k):
    ...     return n + (150 if n % 10 else 88)
    >>> print(k1.storageRenumbered(storageMappingFunc=f))
    storage = 108
    """
    
    d = self.__dict__.copy()
    storageMappingFunc = kwArgs.get('storageMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    storageDelta = kwArgs.get('storageDelta', None)
    
    if storageMappingFunc is not None:
        pass
    
    elif oldToNew is not None:
        storageMappingFunc = (
          lambda x, **k:
          oldToNew.get(x, (x if keepMissing else None)))
    
    elif storageDelta is not None:
        storageMappingFunc = lambda x,**k: x + storageDelta
    
    else:
        storageMappingFunc = lambda x,**k: x
    
    for k, md in self.__class__._MASKSPEC.items():
        if not md.get('mask_isstorageindex', False):
            continue
        
        assert keepMissing  # cannot have keepMissing False for masks
        d[k] = storageMappingFunc(d[k], **kwArgs)
    
    return type(self)(**d)

def M_transformed(self, matrixObj, **kwArgs):
    """
    Returns a object with FUnit distances transformed.
    
    :param matrixObj: The :py:class:`~fontio3.fontmath.matrix.Matrix` to use
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The transformed object
    
    This method is preferred to the older ``scaled()`` method, because it
    allows for skews and rotations, in addition to scales and shifts.
    
    >>> mShift = matrix.Matrix.forShift(1, 2)
    >>> mScale = matrix.Matrix.forScale(-3, 2)
    >>> m = mShift.multiply(mScale)
    
    >>> obj = TestClass2(x=1.5)
    >>> obj.transformed(m).x
    -7.5
    """
    
    d = self.__dict__.copy()
    mp = matrixObj.mapPoint
    
    for k, md in self.__class__._MASKSPEC.items():
        cpt = md.get('mask_transformcounterpart', None)
        
        if cpt is not None:
            try:
                otherValue = d[cpt]
            except KeyError:
                otherValue = cpt
            
            if md.get('mask_transformnoround', False):
                roundFunc = (lambda x,**k: x)  # ignores the castType
            elif 'mask_roundFunc' in md:
                roundFunc = md['mask_roundfunc']
            elif SS.get('mask_python3rounding', False):
                roundFunc = utilities.newRound
            else:
                roundFunc = utilities.oldRound
            
            if md.get('mask_representsx', False):
                d[k] = roundFunc(
                  mp((d[k], otherValue))[0],
                  castType=type(d[k]))
            
            else:
                assert md.get('mask_representsy', False)
                d[k] = roundFunc(
                  mp((otherValue, d[k]))[1],
                  castType=type(d[k]))
    
    return type(self)(**d)

def SM_bool(self):
    """
    Returns True if at least one of the values is nonzero. Values with
    ``mask_ignoreforcomparisons`` set True are always treated as False for this
    method.
    
    >>> bool(TestClass.fromnumber(0xED2F))
    True
    
    Classes with enums will never be nonzero (unless a label is empty):
    
    >>> bool(TestClass.fromnumber(0))
    True
    >>> bool(TestClass2.fromnumber(0))
    False
    """
    
    d = self.__dict__
    MS = self.__class__._MASKSPEC
    v = [d[k] for k in MS if not MS[k].get('mask_ignoreforcomparisons', False)]
    
    if not v:
        return False
    
    return any(v)

def SM_copy(self):
    """
    Returns a shallow copy (which is the same as a deep copy for masklike
    objects).
    
    >>> obj1 = TestClass.fromnumber(0xED2F)
    >>> obj2 = obj1.__copy__()
    >>> obj1 == obj2, obj1 is obj2
    (True, False)
    """
    
    return type(self)(**self.__dict__)

def SM_deepcopy(self, memo=None):
    """
    Returns a deep copy (which, for masklike objects, is always the same as a
    shallow copy).
    
    >>> obj1 = TestClass.fromnumber(0xED2F)
    >>> obj2 = obj1.__deepcopy__()
    >>> obj1 == obj2, obj1 is obj2
    (True, False)
    """
    
    return type(self)(**self.__dict__)

def SM_eq(self, other):
    """
    Returns True if ``self`` and ``other`` have equal values in all positions.
    
    >>> TestClass.fromnumber(0xED2F) == TestClass.fromnumber(0xED2F)
    True
    
    >>> TestClass.fromnumber(0xED2F) == TestClass.fromnumber(0xED2E)
    False
    
    Field 'd' is ignored for comparisons in TestClass objects:
    >>> TestClass.fromnumber(0xED2F) == TestClass.fromnumber(0xED0F)
    True
    
    Note filler fields are implicitly ignored:
    >>> TestClass.fromnumber(0xED2F) == TestClass.fromnumber(0xEF2F)
    True
    """
    
    if self is other:
        return True
    
    if other is None:
        return False
    
    dSelf = self.__dict__
    dOther = other.__dict__
    
    for k, md in self.__class__._MASKSPEC.items():
        if md.get('mask_ignoreforcomparisons', False):
            continue
        
        if dSelf[k] != dOther[k]:
            return False
    
    return True

def SM_init(self, **kwArgs):
    """
    Initializes the object via the specified keyword arguments. Arguments which
    are omitted will use their ``mask_initfuncs`` to set the initial values.
    
    >>> obj = TestClass(a=-0.75, c='Third', b=True, u=15, d=-1)
    >>> print(obj.c)
    Third
    >>> print(TestClass().c)
    Second
    
    >>> print(TestClass5(x='b'))
    x = b
    >>> print(TestClass5(x='c'))
    Traceback (most recent call last):
      ...
    ValueError: Unknown enumerated value: c
    
    >>> TestClass15().pprint()
    Symbol group: 9
    nonconst: 0
    """
    
    cd = self.__class__.__dict__
    d = self.__dict__
    d.update(kwArgs)
    
    for k, md in cd['_MASKSPEC'].items():
        if k not in d:
            f = md.get('mask_initfunc')
            
            if 'mask_constantvalue' in md:
                d[k] = md['mask_constantvalue']
            
            elif f is not None:
                d[k] = f()
            
            elif (
              md.get('mask_isbool', False) or
              md.get('mask_isantibool', False)):
                
                d[k] = False
            
            elif md.get('mask_isenum', False):
                if 'mask_enumstringsdict' in md:
                    d[k] = md['mask_enumstringsdict'][0]
                else:
                    d[k] = md['mask_enumstrings'][0]
            
            else:
                d[k] = 0
        
        if md.get('mask_isenum', False):
            # any explicitly provided enum strings need to be checked
            toCheck = cd['_MASKINV'][k]
            
            if d[k] not in toCheck:
                raise ValueError("Unknown enumerated value: %s" % (d[k],))

def SM_repr(self):
    """
    Return a string representation of ``self``.
    
    :return: The string representation
    :rtype: str
    
    The returned string can be passed to ``eval()`` in order to get back an
    object equal to the original ``self``.
    
    >>> obj = TestClass.fromnumber(0xED2F)
    >>> obj == eval(repr(obj))
    True
    """
    
    MS = self.__class__._MASKSPEC
    d = self.__dict__
    fmt = "%s(%s)" % (self.__class__.__name__, ', '.join(["%s=%r"] * len(MS)))
    t = tuple(x for k in MS for x in (k, d[k]))
    return fmt % t
    
def SM_str(self):
    """
    Returns a nice string representation of the object. The ordering for the
    values will respect ``maskSorted`` if specified; otherwise, it will be the
    order (high to low) within the binary representation.
    
    >>> print(TestClass.fromnumber(0xED2F))
    enum = Third, signed = -1, fixed = -0.75, unsigned = 15, bool = True
    
    >>> print(TestClass6.fromnumber(0x03))
    Bold Italic
    >>> print(TestClass6())
    Plain
    
    >>> e = _fakeEditor()
    >>> obj = TestClass14(nameIndex=303)
    >>> print(obj)
    nameIndex = 303
    
    >>> obj.__dict__['kwArgs'] = {'editor': e}
    >>> print(obj)
    nameIndex = 303 ('Required Ligatures On')
    """
    
    cd = self.__class__.__dict__
    sv = []
    d = self.__dict__
    MS = cd['_MASKSPEC']
    CS = cd['_MASKCTRL']
    
    if 'combinedstringfunc' in CS:
        for t in cd['_FIELDMAP'][True]:
            k = t[2]
            
            if d[k]:
                sv.append(MS[k].get('mask_label', k))
        
        return CS['combinedstringfunc'](sv)
    
    selfNamer = getattr(self, '_namer', None)
    
    for t in cd['_FIELDMAP'][True]:
        k = t[2]
        obj = d[k]
        ks = MS[k]
        bs = ks.get('mask_boolstrings', None)
        
        if bs is not None:
            sv.append(bs[obj])
            continue
        
        if ks.get('mask_showonlyiftrue', False) and (not bool(obj)):
            continue
        
        f = ks.get('mask_showonlyiffuncobj')
        
        if (f is not None) and (not f(self)):
            continue
        
        if (
          ks.get('mask_isglyphindex', False) and
          ks.get('mask_usenamerforstr', False) and
          selfNamer):
            
            f = selfNamer.bestNameForGlyphIndex
        
        elif ks.get('mask_isnameindex', False):
            kwa = d.get('kwArgs', {})
            f = functools.partial(utilities.nameFromKwArgs, **kwa)
        
        elif ks.get('mask_strusesrepr', False):
            f = repr
        
        else:
            f = str
        
        label = ks.get('mask_label', k)
        sv.append("%s = %s" % (label, f(obj)))
    
    return ', '.join(sv)

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

_methodDict = {
  '__bool__': SM_bool,
  '__copy__': SM_copy,
  '__deepcopy__': SM_deepcopy,
  '__eq__': SM_eq,
  '__init__': SM_init,
  '__repr__': SM_repr,
  '__str__': SM_str,
  'asImmutable': M_asImmutable,
  'buildBinary': M_buildBinary,
  'checkInput': M_checkInput,
  'coalesced': M_coalesced,
  'compacted': M_compacted,
  'cvtsRenumbered': M_cvtsRenumbered,
  'fdefsRenumbered': M_fdefsRenumbered,
  'fromnumber': classmethod(CM_fromnumber),
  'fromvalidatednumber': classmethod(CM_fromvalidatednumber),
  'fromvalidatedwalker': classmethod(CM_fromvalidatedwalker),
  'fromwalker': classmethod(CM_fromwalker),
  'gatheredInputGlyphs': M_gatheredInputGlyphs,
  'gatheredLivingDeltas': M_gatheredLivingDeltas,
  'gatheredMaxContext': M_gatheredMaxContext,
  'gatheredOutputGlyphs': M_gatheredOutputGlyphs,
  'gatheredRefs': M_gatheredRefs,
  'getEnumInverseMaps': classmethod(lambda x: x._MASKINV),
  'getRawMask': lambda x: x.__dict__.get('_rawNumber', None),
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
  'transformed': M_transformed}

def _addMethods(cd):
    cd['__hash__'] = None  # a Python 3 thing
    
    for mKey, m in _methodDict.items():
        if mKey not in cd:
            cd[mKey] = m

def _makeFieldMap(dMS, dAll, tSort):
    """
    Creates the field map, both sorted and unsorted. Since we're now using a
    metaclass, this can be done at class creation time, removing the burden
    from instances. Yay metaclasses!
    
    >>> tUnsorted, tSorted = TestClass._FIELDMAP
    >>> for t in tUnsorted: print(t)
    (15, 5, 'a')
    (10, 1, 'b')
    (9, 1, None)
    (8, 2, 'c')
    (6, 1, None)
    (5, 1, 'd')
    (4, 1, None)
    (3, 4, 'u')
    
    >>> for t in tSorted: print(t)
    (8, 2, 'c')
    (5, 1, 'd')
    (15, 5, 'a')
    (3, 4, 'u')
    (10, 1, 'b')
    """
    
    v = []
    s = span2.Span()
    
    for k, d in dMS.items():
        if d.get('mask_isbool', False) or d.get('mask_isantibool', False):
            size = 1
        else:
            size = d['mask_bitcount']
        
        rb = d['mask_rightmostbitindex']
        v.append((rb + size - 1, size, k))
        s.update(range(rb, rb + size))
    
    d = dict((t[2], t) for t in v)
    v2 = [d[k] for k in tSort]
    s = s.inverted(0, 8 * dAll['maskByteLength'] - 1)
    
    for first, last in s.ranges():
        v.append((last, last - first + 1, None))
    
    v.sort(reverse=True)
    return (v, v2)

def _preprocessEnums(d):
    """
    Add inverted dicts for any keys including a mask_enumstringsdict.
    
    >>> sorted(TestClass._MASKINV['c'].items())
    [('First', 0), ('Last', 3), ('Second', 1), ('Third', 2)]
    """
    
    dOut = {}
    
    for k, md in d.items():
        if md.get('mask_isenum', False):
            sTuple = md.get('mask_enumstrings', None)
            sDict = md.get('mask_enumstringsdict', None)
            
            if sTuple is not None:
                dOut[k] = {s: i for i, s in enumerate(sTuple)}
            
            elif sDict is not None:
                sDict[None]  # force at least one instance of the
                             # default string before inversion
                
                dOut[k] = dict(zip(sDict.values(), sDict.keys()))
            
            else:
                raise ValueError(
                  "All enums must have strings or stringsdicts!")
    
    return dOut

def _validateMaskControls(d):
    """
    """
    
    unknownKeys = set(d) - validMaskControlsKeys
    
    if unknownKeys:
        raise ValueError(
          "Unknown maskControls keys: %s" %
          (sorted(unknownKeys),))

def _validateMaskSpec(d):
    """
    Make sure only known keys are included in the maskSpec. (Checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing)
    
    >>> _validateMaskSpec({
    ...   'a': {'mask_bitcount': 16, 'mask_rightmostbitindex': 0}})
    
    >>> _validateMaskSpec({'a': {'mask_bitcount': 16}})
    Traceback (most recent call last):
      ...
    ValueError: Error in maskSpec member 'a': missing required maskSpec keys ['mask_rightmostbitindex']
    """
    
    for fieldName, dSub in d.items():
        s = set(dSub)
        prefix = "Error in maskSpec member %r: " % (fieldName,)
        requiredKeys = set(['mask_bitcount', 'mask_rightmostbitindex'])
        missingRequiredKeys = requiredKeys - s
        
        if 'mask_isbool' in s or 'mask_isantibool' in s:
            missingRequiredKeys.discard('mask_bitcount')
        
        if missingRequiredKeys:
            fmt = "%smissing required maskSpec keys %s"
            raise ValueError(fmt % (prefix, sorted(missingRequiredKeys)))
        
        unknownKeys = s - validMaskSpecKeys
        
        if unknownKeys:
            fmt = "%sunknown maskSpec keys %s"
            raise ValueError(fmt % (prefix, sorted(unknownKeys)))
        
        if 'mask_representsx' in s and 'mask_representsy' in s:
            fmt = "%scannot represent both x and y!"
            raise ValueError(fmt % (prefix,))
        
        if 'mask_isbool' in s and 'mask_isantibool' in s:
            fmt = "%scannot be bool and antibool!"
            raise ValueError(fmt % (prefix,))
        
        if 'mask_prevalidatedglyphset' in s:
            if not dSub.get('mask_isglyph', False):
                raise ValueError(
                  "Prevalidated glyph set provided, but values "
                  "are not glyph indices!")

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for simple mask-like classes.
    
    .. note::
        
        Unlike most other metaclasses, maskmeta does not permit inheriting an
        existing base class and augmenting it. This doesn't work because of the
        likelihood of explicit bit-location conflicts.
    """
    
    def __new__(mcl, classname, bases, classdict):
        dPer = classdict['_MASKSPEC'] = classdict.pop('maskSpec', {})
        classdict['_EXTRA_SPEC'] = dPer
        _validateMaskSpec(dPer)
        
        dAll = classdict['_MASKCTRL'] = classdict.pop('maskControls', {})
        classdict['_MAIN_SPEC'] = dAll
        _validateMaskControls(dAll)
        
        tSort = classdict['_MASKSORT'] = classdict.pop(
          'maskSorted',
          tuple(sorted(dPer)))
        
        dAll['maskByteLength'] = classdict.pop('maskByteLength')
        
        classdict['_FIELDMAP'] = _makeFieldMap(dPer, dAll, tSort)  # (unsorted,
                                                                   # sorted)
        classdict['_MASKINV'] = _preprocessEnums(dPer)
        
        _addMethods(classdict)
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
    import collections
    import io
    from fontio3.fontmath import matrix
    from fontio3.utilities import namer
    
    def _fakeEditor():
        from fontio3.name.name import Name
        
        _fakeNameTable = {
            (1, 0, 0, 303): "Required Ligatures On",
            (1, 0, 0, 304): "Common Ligatures On",
            (1, 0, 0, 306): "Regular",
            (1, 0, 0, 307): "Small Caps"}
        
        e = utilities.fakeEditor(0x1000)
        e.name = Name(_fakeNameTable)
        return e
    
    def _recalc_a(oldValue, **kwArgs):
        newValue = oldValue + kwArgs['adjust_a']
        return (newValue != oldValue), newValue
    
    class TestClass(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            a = dict(
                mask_bitcount = 5,
                mask_fixedcharacteristic = 3,
                mask_isfixed = True,
                mask_issigned = True,
                mask_label = "fixed",
                mask_recalculatefunc = _recalc_a,
                mask_rightmostbitindex = 11),
            
            b = dict(
                mask_isbool = True,
                mask_label = "bool",
                mask_rightmostbitindex = 10),
            
            c = dict(
                mask_bitcount = 2,
                mask_enumstrings = ("First", "Second", "Third", "Last"),
                mask_initfunc = (lambda: "Second"),
                mask_isenum = True,
                mask_label = "enum",
                mask_mergecheckequality = True,
                mask_rightmostbitindex = 7),
            
            d = dict(
                mask_bitcount = 1,
                mask_ignoreforcomparisons = True,
                mask_issigned = True,
                mask_label = "signed",
                mask_rightmostbitindex = 5),
            
            u = dict(
                mask_bitcount = 4,
                mask_issigned = False,
                mask_label = "unsigned",
                mask_rightmostbitindex = 0))
        
        maskByteLength = 2
        maskSorted = ('c', 'd', 'a', 'u', 'b')
    
    class TestClass2(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            x = dict(
                mask_bitcount = 32,
                mask_isfixed = True,
                mask_issigned = True,
                mask_label = "A 16.16 Fixed value",
                mask_representsx = True,
                mask_rightmostbitindex = 0,
                mask_scalesnoround = True,
                mask_transformcounterpart = 0,
                mask_transformnoround = True))
        
        maskByteLength = 4
    
    class TestClass3(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            isSpecial = dict(
                mask_isbool = True,
                mask_label = "Glyph is special",
                mask_rightmostbitindex = 31),
            
            gIn = dict(
                mask_bitcount = 15,
                mask_isglyphindex = True,
                mask_label = "Input glyph",
                mask_rightmostbitindex = 16,
                mask_usenamerforstr = True),
            
            gOut = dict(
                mask_bitcount = 16,
                mask_isglyphindex = True,
                mask_isoutputglyph = True,
                mask_label = "Output glyph",
                mask_rightmostbitindex = 0,
                mask_usenamerforstr = True))
        
        maskByteLength = 4
    
    class TestClass4(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            point = dict(
                mask_bitcount = 8,
                mask_ispointindex = True,
                mask_label = "Point index",
                mask_rightmostbitindex = 0))
        
        maskByteLength = 1
    
    class TestClass5(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            x = dict(
                mask_bitcount = 8,
                mask_enumstringsdict = collections.defaultdict(
                  lambda: "No value", {0: 'a', 193: 'b'}),
                mask_isenum = True,
                mask_rightmostbitindex = 0))
        
        maskByteLength = 1

    class TestClass6(object, metaclass=FontDataMetaclass):
        maskByteLength = 2
        
        maskControls = dict(
            combinedstringfunc = (
              lambda sv: (' '.join(sv) if sv else "Plain")))
        
        maskSorted = (
          'bold', 'italic', 'underline', 'outline', 'shadow', 'condensed',
          'extended')
        
        maskSpec = dict(
            bold = dict(
                mask_isbool = True,
                mask_label = "Bold",
                mask_rightmostbitindex = 0),
            
            italic = dict(
                mask_isbool = True,
                mask_label = "Italic",
                mask_rightmostbitindex = 1),
            
            underline = dict(
                mask_isbool = True,
                mask_label = "Underline",
                mask_rightmostbitindex = 2),
            
            outline = dict(
                mask_isbool = True,
                mask_label = "Outline",
                mask_rightmostbitindex = 3),
            
            shadow = dict(
                mask_isbool = True,
                mask_label = "Shadow",
                mask_rightmostbitindex = 4),
            
            condensed = dict(
                mask_isbool = True,
                mask_label = "Condensed",
                mask_rightmostbitindex = 5),
            
            extended = dict(
                mask_isbool = True,
                mask_label = "Extended",
                mask_rightmostbitindex = 6))
    
    class TestClass7(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            pc = dict(
                mask_bitcount = 8,
                mask_ispc = True,
                mask_label = "PC",
                mask_rightmostbitindex = 0))
        
        maskByteLength = 1
    
    class TestClass8(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            normalBool = dict(
                mask_isbool = True,
                mask_label = "Normal enabled",
                mask_rightmostbitindex = 0),
            
            antiBool = dict(
                mask_isantibool = True,
                mask_label = "Antibool enabled",
                mask_rightmostbitindex = 1))
        
        maskSorted = ('normalBool', 'antiBool')
        maskByteLength = 1
    
    class TestClass9(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            cvt = dict(
                mask_bitcount = 16,
                mask_iscvtindex = True,
                mask_rightmostbitindex = 0))
        
        maskByteLength = 2
    
    class TestClass10(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            fdef = dict(
                mask_bitcount = 16,
                mask_isfdefindex = True,
                mask_rightmostbitindex = 0))
        
        maskByteLength = 2
    
    class TestClass11(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            storage = dict(
                mask_bitcount = 16,
                mask_isstorageindex = True,
                mask_rightmostbitindex = 0))
        
        maskByteLength = 2
    
    class TestClass12(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            first = dict(
                mask_isantibool = True,
                mask_rightmostbitindex = 15),
            last = dict(
                mask_isantibool = True,
                mask_rightmostbitindex = 0))
        
        maskControls = dict(
            fillmissingwithone = True)
        
        maskByteLength = 2
    
    class TestClass13(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            lastBit = dict(
                mask_isbool = True,
                mask_rightmostbitindex = 0))
        
        maskControls = dict(
            inputconvolutionfunc = (
              lambda n: int('0b' + bin(n+0x10000)[3:][::-1], 2)),
            outputconvolutionfunc = (
              lambda n: int('0b' + bin(n+0x10000)[3:][::-1], 2)))
        
        maskByteLength = 2
    
    class TestClass14(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            nameIndex = dict(
                mask_bitcount = 16,
                mask_isnameindex = True,
                mask_rightmostbitindex = 0))
        
        maskByteLength = 2
    
    class TestClass15(object, metaclass=FontDataMetaclass):
        maskSpec = dict(
            const9 = dict(
                mask_bitcount = 8,
                mask_constantvalue = 9,
                mask_label = "Symbol group: 9",
                mask_rightmostbitindex = 8),
            nonconst = dict(
                mask_bitcount = 8,
                mask_rightmostbitindex = 0))
        
        maskByteLength = 2

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
