#
# postheader.py -- standard 32-byte header for a 'post' table
#
# Copyright © 2004-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions for the standard 32-byte header for a 'post' table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_format(obj, **kwArgs):
    if obj not in {1.0, 2.0, 2.5, 3.0, 4.0}:
        kwArgs['logger'].error((
          'V0133',
          (obj,),
          "The format value %s is not valid."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PostHeader(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects containing the header information for any 'post' table.
    
    >>> _testingValues[1].pprint()
    Table format: 2.5
    Italic angle (degrees): 0.0
    Underline position: 40
    Underline thickness: 0
    Font is fixed-pitch: True
    
    >>> logger = utilities.makeDoctestLogger("postheader_val")
    >>> obj = PostHeader(format=9.0, italicAngle=50000, maxMemType42=-1)
    >>> e = utilities.fakeEditor(0x1000)
    >>> obj.isValid(logger=logger, editor=e)
    postheader_val.format - ERROR - The format value 9.0 is not valid.
    postheader_val.italicAngle - ERROR - The value 50000 cannot be represented in signed (16.16) format.
    postheader_val.maxMemType42 - ERROR - The negative value -1 cannot be used in an unsigned field.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        format = dict(
            attr_initfunc = (lambda: 3.0),
            attr_label = "Table format",
            attr_validatefunc = _validate_format,
            attr_wisdom = (
              "Note that format 2.5 is no longer supported; use format 2 "
              "instead.")),
        
        italicAngle = dict(
            attr_initfunc = (lambda: 0.0),
            attr_label = "Italic angle (degrees)",
            attr_validatefunc = valassist.isNumber_fixed),
        
        underlinePosition = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Underline position",
            attr_scaledirect = True,
            attr_representsy = True),
        
        underlineThickness = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Underline thickness",
            attr_scaledirect = True,
            attr_representsy = True),
        
        isFixedPitch = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Font is fixed-pitch"),
        
        minMemType42 = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Minimum memory usage for Type 42",
            attr_showonlyiftrue = True,
            attr_validatefunc = valassist.isFormat_L),
        
        maxMemType42 = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Maximum memory usage for Type 42",
            attr_showonlyiftrue = True,
            attr_validatefunc = valassist.isFormat_L),
        
        minMemType1 = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Minimum memory usage for Type 1",
            attr_showonlyiftrue = True,
            attr_validatefunc = valassist.isFormat_L),
        
        maxMemType1 = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Maximum memory usage for Type 1",
            attr_showonlyiftrue = True,
            attr_validatefunc = valassist.isFormat_L))
    
    attrSorted = (
      'format',
      'italicAngle',
      'underlinePosition',
      'underlineThickness',
      'isFixedPitch',
      'minMemType42',
      'maxMemType42',
      'minMemType1',
      'maxMemType1')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PostHeader object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0003 0000 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 8000 0000 0000  0028 0000 0001 0001 |.........(......|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
        
        %start
        %kind
        protocol method
        %return
        None
        %pos
        w
        A LinkedWriter object to which the binary content for the object will
        be added.
        %note
        This method is how you convert a "living" high-level fontio3 object
        into its equivalent binary data representation.
        %end
        """
        
        # The higher-level Post object will stake its location, so we don't
        w.add("L", int(self.format * 65536))
        w.add("l", int(round(self.italicAngle * 65536)))
        w.add("hh", self.underlinePosition, self.underlineThickness)
        
        # The following weirdness is due to a change in the interpretation of
        # the header from isFixedPitch being a UInt16 followed by 2 zero bytes
        # to a UInt32. To make sure both old and new software catch the value,
        # I replicate the value in both 16-bit parts.
        
        w.add("2H", int(self.isFixedPitch), int(self.isFixedPitch))
        w.add("4L", self.minMemType42, self.maxMemType42, self.minMemType1, self.maxMemType1)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new PostHeader. However, it
        also does validation via the logging module (the client should have
        done a logging.basicConfig call prior to calling this method, unless a
        logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.post')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = PostHeader.fromvalidatedbytes
        >>> obj = fvb(s[0:4], logger=logger)
        test.post.postheader - DEBUG - Walker has 4 remaining bytes.
        test.post.postheader - ERROR - Insufficient bytes.
        
        %start
        %kind
        classmethod
        %return
        A new PostHeader object unpacked from the data in the specified walker.
        %pos
        w
        A walker with the data to unpack.
        %kw
        logger
        An optional logger to which messages will be posted.
        %end
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('postheader')
        else:
            logger = logger.getChild('postheader')
        
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
        
        if w.length() < 32:
            logger.error(('E2311', (), "Insufficient bytes."))
            return None
        
        t = w.unpack("Ll2h5L")
        
        return cls(
          format = t[0] / 65536.0,
          italicAngle = t[1] / 65536.0,
          underlinePosition = t[2],
          underlineThickness = t[3],
          isFixedPitch = bool(t[4]),
          minMemType42 = t[5],
          maxMemType42 = t[6],
          minMemType1 = t[7],
          maxMemType1 = t[8])
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new PostHeader object from the specified walker.
        
        >>> _testingValues[0] == PostHeader.frombytes(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == PostHeader.frombytes(_testingValues[1].binaryString())
        True
        
        %start
        %kind
        classmethod
        %return
        A new PostHeader object unpacked from the data in the specified walker.
        %pos
        w
        A walker with the data to unpack.
        %end
        """
        
        t = w.unpack("Ll2h5L")
        
        return cls(
          format = t[0] / 65536.0,
          italicAngle = t[1] / 65536.0,
          underlinePosition = t[2],
          underlineThickness = t[3],
          isFixedPitch = bool(t[4]),
          minMemType42 = t[5],
          maxMemType42 = t[6],
          minMemType1 = t[7],
          maxMemType1 = t[8])

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        PostHeader(),
        PostHeader(format=2.5, isFixedPitch=True, underlinePosition=40))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
