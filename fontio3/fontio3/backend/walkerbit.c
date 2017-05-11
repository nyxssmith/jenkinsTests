/*
 * walkerbit.c -- Implementation of superfast StringBitWalkers
 *
 * Copyright (c) 2010-2012 Monotype Imaging Inc. All Rights Reserved.
 *
 */

#include <Python.h>
#include "AssertMacros.h"

/* ------------------------------------------------------------------------- */

/*** CONSTANTS ***/

const unsigned char highMasks[8] = {
    0xFF,
    0xFE,
    0xFC,
    0xF8,
    0xF0,
    0xE0,
    0xC0,
    0x80};

/* ------------------------------------------------------------------------- */

/*** TYPES ***/

struct WKB_Context
    {
    Py_buffer       liveBuffer;
    PyObject        *originalObject;
    unsigned long   origBitStart;
    unsigned long   currBitOffset;
    unsigned long   bitLimit;
    char            isBigEndian;
    char            filler[3];
    };

#ifndef __cplusplus
typedef struct WKB_Context WKB_Context;
#endif

/* ------------------------------------------------------------------------- */

/*** PROTOTYPES ***/

static int BytesFromBits(
  WKB_Context   *context,
  unsigned long bitCount,
  unsigned char *buffer);

static void CapsuleDestructor(PyObject *capsule);

static unsigned long FormatByteSize(
  const char    *format,
  unsigned long formatLength,
  unsigned long *itemCount);

static int FormatProcess(
  PyObject              *t,
  const unsigned char   *b,
  const char            *format,
  unsigned long         formatLength,
  Py_ssize_t            startIndex,
  int                   startIsBigEndian);

static void FreeContext(WKB_Context *context);

static int MakeConstants(
  unsigned long bitCountPerItem,
  PyObject **constOne,
  PyObject **constTwo,
  PyObject **constSignedToSubtract);

static PyObject *wkb_AbsRest(PyObject *self, PyObject *args);
static PyObject *wkb_Align(PyObject *self, PyObject *args);
static PyObject *wkb_AsStringAndOffset(PyObject *self, PyObject *args);
static PyObject *wkb_AtEnd(PyObject *self, PyObject *args);
static PyObject *wkb_BitLength(PyObject *self, PyObject *args);
static PyObject *wkb_CalcSize(PyObject *self, PyObject *args);
static PyObject *wkb_GetOffset(PyObject *self, PyObject *args);
static PyObject *wkb_Group(PyObject *self, PyObject *args);
static PyObject *wkb_NewContext(PyObject *self, PyObject *args);
static PyObject *wkb_PascalString(PyObject *self, PyObject *args);
static PyObject *wkb_Piece(PyObject *self, PyObject *args);
static PyObject *wkb_Reset(PyObject *self, PyObject *args);
static PyObject *wkb_SetOffset(PyObject *self, PyObject *args);
static PyObject *wkb_Skip(PyObject *self, PyObject *args);
static PyObject *wkb_SubWalkerSetup(PyObject *self, PyObject *args);
static PyObject *wkb_Unpack(PyObject *self, PyObject *args);
static PyObject *wkb_UnpackBits(PyObject *self, PyObject *args);
static PyObject *wkb_UnpackBitsGroup(PyObject *self, PyObject *args);
static PyObject *wkb_UnpackRest(PyObject *self, PyObject *args);

/* ------------------------------------------------------------------------- */

/*** STATIC GLOBALS ***/

static PyMethodDef WalkerBitMethods[] = {
    {"wkbAbsRest", wkb_AbsRest, METH_VARARGS, NULL},
    {"wkbAlign", wkb_Align, METH_VARARGS, NULL},
    {"wkbAsStringAndOffset", wkb_AsStringAndOffset, METH_VARARGS, NULL},
    {"wkbAtEnd", wkb_AtEnd, METH_VARARGS, NULL},
    {"wkbBitLength", wkb_BitLength, METH_VARARGS, NULL},
    {"wkbCalcSize", wkb_CalcSize, METH_VARARGS, NULL},
    {"wkbGetOffset", wkb_GetOffset, METH_VARARGS, NULL},
    {"wkbGroup", wkb_Group, METH_VARARGS, NULL},
    {"wkbNewContext", wkb_NewContext, METH_VARARGS, NULL},
    {"wkbPascalString", wkb_PascalString, METH_VARARGS, NULL},
    {"wkbPiece", wkb_Piece, METH_VARARGS, NULL},
    {"wkbReset", wkb_Reset, METH_VARARGS, NULL},
    {"wkbSetOffset", wkb_SetOffset, METH_VARARGS, NULL},
    {"wkbSkip", wkb_Skip, METH_VARARGS, NULL},
    {"wkbSubWalkerSetup", wkb_SubWalkerSetup, METH_VARARGS, NULL},
    {"wkbUnpack", wkb_Unpack, METH_VARARGS, NULL},
    {"wkbUnpackBits", wkb_UnpackBits, METH_VARARGS, NULL},
    {"wkbUnpackBitsGroup", wkb_UnpackBitsGroup, METH_VARARGS, NULL},
    {"wkbUnpackRest", wkb_UnpackRest, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

/* ------------------------------------------------------------------------- */

/*** INTERNAL PROCEDURES ***/

static int BytesFromBits(
  WKB_Context *context,
  unsigned long bitCount,
  unsigned char *buffer)
    
    {
    unsigned char   *from;
    unsigned long   currPhase;
    
    require_action(
      (context->currBitOffset + bitCount) <= context->bitLimit,
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "Attempt to unpack past end of string!"););
    
    from = (unsigned char *) context->liveBuffer.buf + (context->currBitOffset >> 3UL);
    currPhase = context->currBitOffset & 7UL;
    context->currBitOffset += bitCount;
    
    if (!currPhase)
        {  /* we're at a byte boundary */
        while (bitCount >= 8UL)
            {
            *buffer++ = *from++;
            bitCount -= 8UL;
            }
        
        if (bitCount)
            {  /* there were 1 to 7 bits remaining to be copied */
            *buffer = *from & highMasks[8UL - bitCount];
            }
        }
    
    else
        {  /* starting phase is nonzero */
        unsigned char   *fromNext = from + 1UL;
        unsigned long   counterPhase = 8UL - currPhase;
        
        while (bitCount >= 8UL)
            {
            *buffer++ = (unsigned char) ((*from++ << currPhase) | (*fromNext++ >> counterPhase));
            bitCount -= 8UL;
            }
        
        if (bitCount)
            {  /* there were 1 to 7 bits remaining to be copied */
            if (bitCount <= counterPhase)
                *buffer++ = (unsigned char) ((*from << currPhase) & highMasks[8UL - bitCount]);
            
            else
                {
                *buffer++ = (unsigned char) (
                  (*from << currPhase) |
                  ((*fromNext & highMasks[8UL - (bitCount - counterPhase)]) >> counterPhase));
                }
            }
        }
    
    return 0;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return -1;
    }  /* BytesFromBits */

static void CapsuleDestructor(PyObject *capsule)
    {
    WKB_Context *context = PyCapsule_GetPointer(capsule, "walkerbit_capsule");
    
    if (context)
        FreeContext(context);
    }   /* CapsuleDestructor */

static unsigned long FormatByteSize(
  const char    *format,
  unsigned long formatLength,
  unsigned long *itemCount)
    
    {
    unsigned long   n, repeat = 0, size = 0;
    
    *itemCount = 0;
    
    while (formatLength--)
        {
        char    c = *format++;
        
        if (c >= '0' && c <= '9')
            repeat = (10UL * repeat) + (unsigned long) (c - '0');
        
        else
            {
            if (!repeat)
                repeat = 1UL;
            
            switch (c)
                {
                case 'B':
                case 'b':
                case 'c':
                case 'p':
                case 's':
                case 'x':
                    size += repeat;
                    
                    if (c == 's' || c == 'p')
                        *itemCount += 1;
                    else if (c != 'x')
                        *itemCount += repeat;
                    
                    break;
                
                case 'H':
                case 'h':
                    n = 2UL * repeat;
                    size += n;
                    *itemCount += repeat;
                    break;
                
                case 'T':
                case 't':
                    n = 3UL * repeat;
                    size += n;
                    *itemCount += repeat;
                    break;
                
                case 'f':
                case 'I':
                case 'i':
                case 'L':
                case 'l':
                    n = 4UL * repeat;
                    size += n;
                    *itemCount += repeat;
                    break;
                
                case 'd':
                case 'Q':
                case 'q':
                    n = 8UL * repeat;
                    size += n;
                    *itemCount += repeat;
                    break;
                
                case 'P':
                    n = sizeof(Py_ssize_t) * repeat;
                    size += n;
                    *itemCount += repeat;
                    break;
                
                default:
                    break;
                }
            
            repeat = 0;
            }
        }
    
    return size;
    }  /* FormatByteSize */

static int FormatProcess(
  PyObject              *t,
  const unsigned char   *b,
  const char            *format,
  unsigned long         formatLength,
  Py_ssize_t            startIndex,
  int                   startIsBigEndian)
    
    {
    int             isBigEndian = startIsBigEndian, robeTest = 1, runningOnBigEndian;
    PyObject        *obj, *obj2, *obj3, *obj4, *obj5, *obj6, *obj7, *obj8, *obj9;
    Py_ssize_t      index = startIndex;
    unsigned long   actualLength, repeat = 0;
    
    runningOnBigEndian = (*(char *) &robeTest) == 0;
    
    while (formatLength--)
        {
        char    c = *format++;
        
        if (c >= '0' && c <= '9')
            repeat = (10UL * repeat) + (unsigned long) (c - '0');
        
        else
            {
            if (!repeat)
                repeat = 1UL;
            
            switch (c)
                {
                case '<':
                    isBigEndian = 0;
                    break;
                
                case '@':
                case '=':
                    {
                    isBigEndian = runningOnBigEndian;
                    break;
                    }
                
                case '!':
                case '>':
                    isBigEndian = 1;
                    break;
                
                case 'B':
                case 'b':
                    while (repeat--)
                        {
                        if (c == 'B')
                            obj = PyLong_FromLong(*b++);
                        else
                            obj = PyLong_FromLong((char) *b++);
                        
                        require(obj, BadReturn);
                        require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                        }
                    
                    break;
                
                case 'H':
                case 'h':
                    while (repeat--)
                        {
                        unsigned char   *pxc, xc[2];
                        int             count = 2;
                        unsigned short  *x = (unsigned short *) &xc[0];
                        
                        if (runningOnBigEndian == isBigEndian)
                            {
                            pxc = &xc[0];
                            
                            while (count--)
                                *pxc++ = *b++;
                            }
                        
                        else
                            {
                            pxc = &xc[1];
                            
                            while (count--)
                                *pxc-- = *b++;
                            }
                        
                        if (c == 'H')
                            obj = PyLong_FromLong(*x);
                        else
                            obj = PyLong_FromLong((short) *x);
                        
                        require(obj, BadReturn);
                        require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                        }
                    
                    break;
                
                case 'I':
                case 'L':
                case 'f':
                case 'i':
                case 'l':
                    while (repeat--)
                        {
                        unsigned char   *pxc, xc[4];
                        int             count = 4;
                        unsigned int   *x = (unsigned int *) &xc[0];
                        
                        if (runningOnBigEndian == isBigEndian)
                            {
                            pxc = &xc[0];
                            
                            while (count--)
                                *pxc++ = *b++;
                            }
                        
                        else
                            {
                            pxc = &xc[3];
                            
                            while (count--)
                                *pxc-- = *b++;
                            }
                        
                        if (c == 'f')
                            obj = PyFloat_FromDouble((double) (*(float *) x));
                        else if (c == 'I' || c == 'L')
                            obj = PyLong_FromUnsignedLong(*x);
                        else
                            obj = PyLong_FromLong(*(int *) x);
                        
                        require(obj, BadReturn);
                        require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                        }
                    
                    break;
                
                case 'T':
                case 't':
                    while (repeat--)
                        {
                        unsigned char   *pxc, xc[4];
                        int             count = 3;
                        unsigned int   *x = (unsigned int *) &xc[0];
                        
                        if (runningOnBigEndian)
                            {
                            if (isBigEndian)
                                {
                                pxc = &xc[1];
                                
                                while (count--)
                                    *pxc++ = *b++;
                                }
                            
                            else
                                {
                                pxc = &xc[3];
                                
                                while (count--)
                                    *pxc-- = *b++;
                                }
                            
                            xc[0] = (c == 'T' ? 0 : (xc[1] < 0x80 ? 0 : 0xFF));
                            }
                        
                        else
                            {
                            if (isBigEndian)
                                {
                                pxc = &xc[2];
                                
                                while (count--)
                                    *pxc-- = *b++;
                                }
                            
                            else
                                {
                                pxc = &xc[0];
                                
                                while (count--)
                                    *pxc++ = *b++;
                                }
                            
                            xc[3] = (c == 'T' ? 0 : (xc[2] < 0x80 ? 0 : 0xFF));
                            }
                        
                        obj = PyLong_FromLong(*(int *) x);
                        require(obj, BadReturn);
                        require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                        }
                    
                    break;
                
                case 'd':
                    while (repeat--)
                        {
                        unsigned char   xc[8];
                        unsigned char   *pxc;
                        double          *x = (double *) &xc[0];
                        int             i = 8;
                        
                        if (runningOnBigEndian == isBigEndian)
                            {
                            pxc = &xc[0];
                            
                            while (i--)
                                *pxc++ = *b++;
                            }
                        
                        else
                            {
                            pxc = &xc[7];
                            
                            while (i--)
                                *pxc-- = *b++;
                            }
                        
                        obj = PyFloat_FromDouble(*x);
                        require(obj, BadReturn);
                        require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                        }
                    
                    break;
                
                case 'Q':
                case 'q':
                    while (repeat--)
                        {
                        unsigned int   highPart, lowPart;
                        
                        if (isBigEndian)
                            {
                            highPart = *b++ << 24;
                            highPart |= *b++ << 16;
                            highPart |= *b++ << 8;
                            highPart |= *b++;
                            lowPart = *b++ << 24;
                            lowPart |= *b++ << 16;
                            lowPart |= *b++ << 8;
                            lowPart |= *b++;
                            }
                        
                        else
                            {
                            lowPart = *b++;
                            lowPart |= *b++ << 8;
                            lowPart |= *b++ << 16;
                            lowPart |= *b++ << 24;
                            highPart = *b++;
                            highPart |= *b++ << 8;
                            highPart |= *b++ << 16;
                            highPart |= *b++ << 24;
                            }
                        
                        obj = PyLong_FromUnsignedLong(highPart);
                        require(obj, BadReturn);
                        obj2 = PyLong_FromLong(32);
                        require(obj2, FreeObj);
                        obj3 = PyNumber_Lshift(obj, obj2);
                        require(obj3, FreeObj2);
                        obj4 = PyLong_FromUnsignedLong(lowPart);
                        require(obj4, FreeObj3);
                        obj5 = PyNumber_Add(obj3, obj4);
                        require(obj5, FreeObj4);
                        
                        if (c == 'q' && highPart > 0x7FFFFFFFUL)
                            {
                            obj6 = PyLong_FromLong(1);
                            require(obj6, FreeObj5);
                            obj7 = PyLong_FromLong(64);
                            require(obj7, FreeObj6);
                            obj8 = PyNumber_Lshift(obj6, obj7);
                            require(obj8, FreeObj7);
                            obj9 = PyNumber_Subtract(obj5, obj8);
                            require(obj9, FreeObj8);
                            require_noerr(PyTuple_SetItem(t, index++, obj9), FreeObj9);
                            /* PyTuple_SetItem steals a ref to obj9, so we don't need to decref it */
                            Py_DECREF(obj8);
                            Py_DECREF(obj7);
                            Py_DECREF(obj6);
                            Py_DECREF(obj5);
                            }
                        
                        else
                            {
                            require_noerr(PyTuple_SetItem(t, index++, obj5), FreeObj5);
                            /* PyTuple_SetItem steals a ref to obj5, so we don't need to decref it */
                            }
                        
                        Py_DECREF(obj4);
                        Py_DECREF(obj3);
                        Py_DECREF(obj2);
                        Py_DECREF(obj);
                        }
                    
                    break;
                
                case 'c':
                    while (repeat--)
                        {
                        obj = PyBytes_FromStringAndSize((const char *) b++, 1);
                        require(obj, BadReturn);
                        require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                        }
                    
                    break;
                
                case 'p':
                    actualLength = *b;
                    obj = PyBytes_FromStringAndSize((const char *) (b + 1), actualLength);
                    require(obj, BadReturn);
                    require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                    b += repeat;
                    break;
                
                case 's':
                    obj = PyBytes_FromStringAndSize((const char *) b, repeat);
                    require(obj, BadReturn);
                    require_noerr(PyTuple_SetItem(t, index++, obj), FreeObj);
                    b += repeat;
                    break;
                
                case 'x':
                    b += repeat;
                    break;
                }
            
            repeat = 0;
            }
        }
    
    return 0;
    
    /*** ERROR HANDLERS ***/
    FreeObj9:   Py_DECREF(obj9);
    FreeObj8:   Py_DECREF(obj8);
    FreeObj7:   Py_DECREF(obj7);
    FreeObj6:   Py_DECREF(obj6);
    FreeObj5:   Py_DECREF(obj5);
    FreeObj4:   Py_DECREF(obj4);
    FreeObj3:   Py_DECREF(obj3);
    FreeObj2:   Py_DECREF(obj2);
    FreeObj:    Py_DECREF(obj);
    BadReturn:  return 1;
    }  /* FormatProcess */

static void FreeContext(WKB_Context *context)
    {
    PyBuffer_Release(&context->liveBuffer);
    Py_CLEAR(context->originalObject);
    
    PyMem_Free(context);
    }  /* FreeContext */

static int MakeConstants(
  unsigned long bitCountPerItem,
  PyObject **constOne,
  PyObject **constTwo,
  PyObject **constSignedToSubtract)
    
    {
    PyObject    *temp;
    
    *constOne = PyLong_FromLong(1L);
    require(*constOne, Err_BadReturn);
    
    *constTwo = PyLong_FromLong(2L);
    require(*constTwo, Err_FreeConstOne);
    
    temp = PyLong_FromLong((long) bitCountPerItem);
    require(temp, Err_FreeConstTwo);
    
    *constSignedToSubtract = PyNumber_Lshift(*constOne, temp);
    require(*constSignedToSubtract, Err_FreeTemp);
    
    Py_DECREF(temp);
    return 0;
    
    /*** ERROR HANDLERS ***/
    Err_FreeTemp:       Py_DECREF(temp);
    Err_FreeConstTwo:   Py_DECREF(*constTwo);
    Err_FreeConstOne:   Py_DECREF(*constOne);
    Err_BadReturn:      return -1;
    }   /* MakeConstants */

/* --------------------------------------------------------------------------------------------- */

static PyObject *wkb_AbsRest(PyObject *self, PyObject *args)
    {
    unsigned char   *buffer;
    unsigned long   bitOffset, byteCount, needBits, origFullBitSize, startBit;
    PyObject        *co, *retVal;
    WKB_Context     *context, tempContext;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ok", &co, &bitOffset),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    origFullBitSize = context->liveBuffer.len << 3UL;
    startBit = context->origBitStart + bitOffset;
    
    require_action(
      startBit < origFullBitSize,
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "AbsRest offset past limit!"););
    
    tempContext.originalObject = context->originalObject;
    tempContext.liveBuffer = context->liveBuffer;
    tempContext.origBitStart = 0;
    tempContext.currBitOffset = startBit;
    tempContext.bitLimit = context->bitLimit;
    tempContext.isBigEndian = context->isBigEndian;
    
    needBits  = origFullBitSize - startBit;
    byteCount = (needBits + 7UL) >> 3UL;
    buffer = PyMem_Malloc(byteCount);
    require(buffer, Err_BadReturn);
    
    require_noerr(
      BytesFromBits(&tempContext, needBits, buffer),
      Err_FreeBuffer);  /* Python exception was already set in BytesFromBits */
    
    retVal = PyBytes_FromStringAndSize((char *) buffer, byteCount);
    require(retVal, Err_FreeBuffer);
    
    PyMem_Free(buffer);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeBuffer: PyMem_Free(buffer);
    Err_BadReturn:  return NULL;
    }  /* wkb_AbsRest */

static PyObject *wkb_Align(PyObject *self, PyObject *args)
    {
    char            absolute;
    unsigned long   adjOff, adjust, bitMultiple;
    PyObject        *co;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Okb", &co, &bitMultiple, &absolute),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    adjust = (absolute ? 0 : context->origBitStart);
    adjOff = context->currBitOffset - adjust;
    context->currBitOffset = (((adjOff) + bitMultiple - 1UL) / bitMultiple) * bitMultiple + adjust;
    
    require_action(
      context->currBitOffset <= context->bitLimit,
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "Align leaves walker past end of data!"););
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_Align */

static PyObject *wkb_AsStringAndOffset(PyObject *self, PyObject *args)
    {
    PyObject    *co, *retVal;
    WKB_Context *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    retVal = Py_BuildValue("Ok", context->originalObject, context->currBitOffset);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_AsStringAndOffset */

static PyObject *wkb_AtEnd(PyObject *self, PyObject *args)
    {
    PyObject        *co, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    retVal = PyBool_FromLong(context->currBitOffset >= context->bitLimit);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_AtEnd */

static PyObject *wkb_BitLength(PyObject *self, PyObject *args)
    {
    PyObject        *co, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    retVal = PyLong_FromUnsignedLong(context->bitLimit - context->currBitOffset);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_BitLength */

static PyObject *wkb_CalcSize(PyObject *self, PyObject *args)
    {
    const char      *format;
    int             formatLength;
    unsigned long   formatByteSize, itemCount;
    PyObject        *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "s#", &format, &formatLength),
      Err_BadReturn);
    
    formatByteSize = FormatByteSize(
      format,
      (unsigned long) formatLength,
      &itemCount);
    
    retVal = PyLong_FromUnsignedLong(formatByteSize);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_CalcSize */

static PyObject *wkb_GetOffset(PyObject *self, PyObject *args)
    {
    char            relative;
    PyObject        *co, *retVal;
    unsigned long   offset;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ob", &co, &relative),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    offset = context->currBitOffset;
    
    if (relative)
        offset -= context->origBitStart;
    
    retVal = Py_BuildValue("k", offset);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_GetOffset */

static PyObject *wkb_Group(PyObject *self, PyObject *args)
    {
    char            finalCoerce;
    const char      *format;
    unsigned char   *b;
    int             formatLength;
    unsigned long   formatByteSize, groupCount, itemCount;
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Os#kb", &co, &format, &formatLength, &groupCount, &finalCoerce),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    if (finalCoerce && (groupCount > 1))
        finalCoerce = 0;
    
    formatByteSize = FormatByteSize(
      format,
      (unsigned long) formatLength,
      &itemCount);
    
    b = (unsigned char *) PyMem_Malloc(formatByteSize);
    require(b, Err_BadReturn);
    
    retVal = PyTuple_New(groupCount);
    require(retVal, Err_FreeBuffer);
    
    if (itemCount == 1)
        {
        while (groupCount--)
            {
            require_noerr(
              BytesFromBits(context, 8UL * formatByteSize, b),
              Err_FreeRetVal);
            
            require_noerr(
              FormatProcess(
                retVal,
                b,
                format,
                (unsigned long) formatLength,
                walkIndex++,
                context->isBigEndian),
              Err_FreeRetVal);
            }
        }
    
    else
        {
        while (groupCount--)
            {
            t = PyTuple_New(itemCount);
            require(t, Err_FreeRetVal);
            
            require_noerr(
              BytesFromBits(context, 8UL * formatByteSize, b),
              Err_FreeT);
            
            require_noerr(
              FormatProcess(
                t,
                b,
                format,
                (unsigned long) formatLength,
                0,
                context->isBigEndian),
              Err_FreeT);
            
            /*
             * The following steals a ref to t, so assuming no error happens,
             * we don't need to explicitly free t. If an error does happen, t
             * will be freed by the error handler.
             */
            
            require_noerr(
              PyTuple_SetItem(retVal, walkIndex++, t),
              Err_FreeT);
            }
        }
    
    if (finalCoerce)
        {
        co = PySequence_GetItem(retVal, 0);
        require(co, Err_FreeRetVal);
        
        Py_DECREF(retVal);
        retVal = co;
        }
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeT:      Py_DECREF(t);
    Err_FreeRetVal: Py_DECREF(retVal);
    Err_FreeBuffer: PyMem_Free(b);
    Err_BadReturn:  return NULL;
    }  /* wkb_Group */

static PyObject *wkb_NewContext(PyObject *self, PyObject *args)
    {
    char            isBigEndian;
    unsigned long   bitLimit, bitStart;
    PyObject        *obj, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Okkb", &obj, &bitStart, &bitLimit, &isBigEndian),
      Err_BadReturn);
    
    context = (WKB_Context *) PyMem_Malloc(sizeof(WKB_Context));
    require(context, Err_BadReturn);
    
    Py_INCREF(obj);
    context->originalObject = obj;
    
    require_noerr(
      PyObject_GetBuffer(obj, &context->liveBuffer, PyBUF_SIMPLE),
      Err_FreeContext);
    
    context->origBitStart = bitStart;
    context->currBitOffset = bitStart;
    context->bitLimit = bitLimit;
    context->isBigEndian = isBigEndian;
    
    retVal = PyCapsule_New(context, "walkerbit_capsule", CapsuleDestructor);
    require(retVal, Err_ReleaseBuffer);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_ReleaseBuffer:  PyBuffer_Release(&context->liveBuffer);
    Err_FreeContext:    Py_DECREF(obj);
                        PyMem_Free(context);
    Err_BadReturn:      return NULL;
    }  /* wkb_NewContext */

static PyObject *wkb_PascalString(PyObject *self, PyObject *args)
    {
    unsigned char   *b, lengthByte;
    PyObject        *co, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    require_noerr(
      BytesFromBits(context, 8UL, &lengthByte),
      Err_BadReturn);
    
    b = PyMem_Malloc(lengthByte);
    require(b, Err_BadReturn);
    
    require_noerr(
      BytesFromBits(context, 8UL * lengthByte, b),
      Err_FreeBuffer);
    
    retVal = PyBytes_FromStringAndSize((char *) b, lengthByte);
    require(retVal, Err_FreeBuffer);
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeBuffer: PyMem_Free(b);
    Err_BadReturn:  return NULL;
    }  /* wkb_PascalString */

static PyObject *wkb_Piece(PyObject *self, PyObject *args)
    {
    char            relative;
    unsigned char   *b;
    unsigned long   bitLength, bitOffset, byteLength, saveOffset;
    PyObject        *co, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Okkb", &co, &bitLength, &bitOffset, &relative),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    bitOffset += (relative ? context->currBitOffset : context->origBitStart);
    
    require_action(
      bitOffset + bitLength <= context->bitLimit,
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "Specified piece larger than available data!"););
    
    byteLength = (bitLength + 7UL) >> 3UL;
    b = PyMem_Malloc(byteLength);
    require(b, Err_BadReturn);
    
    saveOffset = context->currBitOffset;
    context->currBitOffset = bitOffset;
    
    require_noerr(
      BytesFromBits(context, bitLength, b),
      Err_FreeBuffer);
    
    retVal = PyBytes_FromStringAndSize((char *) b, byteLength);
    require(retVal, Err_FreeBuffer);
    
    context->currBitOffset = saveOffset;
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeBuffer:     PyMem_Free(b);
                        context->currBitOffset = saveOffset;
    Err_BadReturn:      return NULL;
    }  /* wkb_Piece */

static PyObject *wkb_Reset(PyObject *self, PyObject *args)
    {
    PyObject    *co;
    WKB_Context *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    context->currBitOffset = context->origBitStart;
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_Reset */

static PyObject *wkb_SetOffset(PyObject *self, PyObject *args)
    {
    char            okToExceed, relative;
    long            signedBitOffset;
    unsigned long   bitOffset;
    PyObject        *co;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Olbb", &co, &signedBitOffset, &relative, &okToExceed),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    signedBitOffset += (long) (relative ? context->currBitOffset : context->origBitStart);
    bitOffset = (unsigned long) signedBitOffset;
    
    require_action(
      okToExceed || (bitOffset < context->bitLimit && signedBitOffset >= 0),
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "Attempt to set offset past the limit"););
    
    context->currBitOffset = bitOffset;
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wk_SetOffset */

static PyObject *wkb_Skip(PyObject *self, PyObject *args)
    {
    long        bitsToSkip;
    PyObject    *co;
    WKB_Context *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ol", &co, &bitsToSkip),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    context->currBitOffset += (unsigned long) bitsToSkip;
    
    if (context->currBitOffset > context->bitLimit)
        {
        if (bitsToSkip < 0)
            context->currBitOffset = 0UL;
        else
            context->currBitOffset = context->bitLimit;
        }
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_Skip */

static PyObject *wkb_SubWalkerSetup(PyObject *self, PyObject *args)
    {
    char            anchor, relative;
    unsigned long   bitOffset, newBitLimit;
    PyObject        *co, *newPyLimit, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "OkbbO", &co, &bitOffset, &relative, &anchor, &newPyLimit),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    if (!anchor)
        bitOffset += (relative ? context->currBitOffset : context->origBitStart);
    
    if (newPyLimit == Py_None)
        newBitLimit = context->bitLimit;
    
    else
        {
        newBitLimit = (unsigned long) PyLong_AsLong(newPyLimit);
        require_noerr((newBitLimit == 0xFFFFFFFFUL) && PyErr_Occurred(), Err_BadReturn);
        
        if (anchor)
            {
            unsigned long   origSize = context->liveBuffer.len << 3UL;
            
            if (newBitLimit == 0)
                newBitLimit = origSize;
            
            if (newBitLimit > origSize)
                newBitLimit = origSize;
            }
        
        else
            {
            if (relative)
                newBitLimit += bitOffset;
            
            if (newBitLimit > context->bitLimit)
                newBitLimit = context->bitLimit;
            }
        }
    
    if (bitOffset > newBitLimit)
        bitOffset = newBitLimit;
    
    retVal = Py_BuildValue(
      "OlkC",
      context->originalObject,
      bitOffset,
      newBitLimit,
      (context->isBigEndian ? '>' : '<'));
    
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* wkb_SubWalkerSetup */

static PyObject *wkb_Unpack(PyObject *self, PyObject *args)
    {
    char            advance, coerce;
    const char      *format;
    unsigned char   *b;
    int             formatLength;
    unsigned long   formatByteSize, itemCount, startingBitOffset;
    PyObject        *co, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Os#bb", &co, &format, &formatLength, &coerce, &advance),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    startingBitOffset = context->currBitOffset;  /* we do this in case we */
                                                 /* need to restore for */
                                                 /* advance=False */
    
    formatByteSize = FormatByteSize(
      format,
      (unsigned long) formatLength,
      &itemCount);
    
    retVal = PyTuple_New(itemCount);
    require(retVal, Err_BadReturn);
    
    b = (unsigned char *) PyMem_Malloc(formatByteSize);
    require(b, Err_FreeTuple);
    
    require_noerr(
      BytesFromBits(context, 8UL * formatByteSize, b),
      Err_FreeBuffer);
    
    require_noerr(
      FormatProcess(
        retVal,
        b,
        format,
        (unsigned long) formatLength,
        0,
        context->isBigEndian),
      Err_FreeBuffer);
    
    if (coerce && (itemCount == 1))
        {
        co = PySequence_GetItem(retVal, 0);
        require(co, Err_FreeBuffer);
        
        Py_DECREF(retVal);
        retVal = co;
        }
    
    if (!advance)
        context->currBitOffset = startingBitOffset;
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeBuffer: PyMem_Free(b);
    Err_FreeTuple:  Py_DECREF(retVal);
    Err_BadReturn:  return NULL;
    }  /* wkb_Unpack */

static PyObject *wkb_UnpackBits(PyObject *self, PyObject *args)
    {
    unsigned char   *b, localBuffer[32];
    unsigned long   bitCount;
    PyObject        *co, *retVal;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ok", &co, &bitCount),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    if (bitCount)
        {
        unsigned long   byteCount = (bitCount + 7UL) >> 3UL;
        
        if (byteCount <= 32UL)
            b = &localBuffer[0];
        
        else
            {
            b = (unsigned char *) PyMem_Malloc(byteCount);
            require(b, Err_BadReturn);
            }
        
        require_noerr(
          BytesFromBits(context, bitCount, b),
          Err_FreeBuffer);
        
        retVal = PyBytes_FromStringAndSize((char *) b, byteCount);
        require(retVal, Err_FreeBuffer);
        
        if (b != localBuffer)
            PyMem_Free(b);
        }
    
    else
        {
        retVal = PyBytes_FromStringAndSize((char *) localBuffer, 0);
        require(retVal, Err_BadReturn);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeBuffer:     if (b != localBuffer) PyMem_Free(b);
    Err_BadReturn:      return NULL;
    }  /* wkb_UnpackBits */

static PyObject *wkb_UnpackBitsGroup(PyObject *self, PyObject *args)
    {
    char            wantSigned;
    
    unsigned char   *b,
                    *bWalk,
                    localBuffer[32],
                    mask = 0x80;
    
    unsigned long   bitCountPerItem,
                    itemCount,
                    totalBitsNeeded,
                    walkIndex = 0;
    
    PyObject        *co,
                    *constOne,
                    *constSignedToSubtract,
                    *constTwo,
                    *retVal,
                    *t,
                    *tNew;
    
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Okkb", &co, &bitCountPerItem, &itemCount, &wantSigned),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    totalBitsNeeded = (unsigned long) (bitCountPerItem * itemCount);
    
    if (totalBitsNeeded)
        {
        unsigned long   byteCount = (totalBitsNeeded + 7UL) >> 3UL;
        
        if (byteCount <= 32UL)
            b = &localBuffer[0];
        
        else
            {
            b = (unsigned char *) PyMem_Malloc(byteCount);
            require(b, Err_BadReturn);
            }
        
        require_noerr(
          BytesFromBits(context, totalBitsNeeded, b),
          Err_FreeBuffer);
        
        retVal = PyTuple_New(itemCount);
        require(retVal, Err_FreeBuffer);
        
        require_noerr(
          MakeConstants(
            bitCountPerItem,
            &constOne,
            &constTwo,
            &constSignedToSubtract),
          Err_FreeRetVal);
        
        bWalk = b;
        
        while (itemCount--)
            {
            char            topBitOn = (char) -1;
            unsigned long   walkCount = bitCountPerItem;
            
            t = PyLong_FromLong(0L);
            require(t, Err_FreeConstants);
            
            while (walkCount--)
                {
                char    on = (*bWalk & mask) != 0;
                
                if (topBitOn == -1)
                    {
                    /* Note we don't need to do the multiplication by 2 for the
                       first bit, since the value is zero. This saves quite a
                       lot of time if bitCountPerItem is one. */
                    topBitOn = on;
                    }
                
                else
                    {
                    tNew = PyNumber_Multiply(t, constTwo);
                    require(tNew, Err_FreeT);
                    
                    Py_DECREF(t);
                    t = tNew;
                    }
                
                if (on)
                    {
                    tNew = PyNumber_Add(t, constOne);
                    require(tNew, Err_FreeT);
                    
                    Py_DECREF(t);
                    t = tNew;
                    }
                
                if (mask == 0x01)
                    {
                    mask = 0x80;
                    bWalk += 1;
                    }
                
                else
                    mask >>= 1;
                }
            
            if (topBitOn && wantSigned)
                {
                tNew = PyNumber_Subtract(t, constSignedToSubtract);
                require(tNew, Err_FreeT);
                
                Py_DECREF(t);
                t = tNew;
                }
            
            /*
             * The following steals a ref to t, so assuming no error happens,
             * we don't need to explicitly free t. If an error does happen, t
             * will be freed by the error handler.
             */
            
            require_noerr(
              PyTuple_SetItem(retVal, walkIndex++, t),
              Err_FreeT);
            }
        
        Py_DECREF(constSignedToSubtract);
        Py_DECREF(constTwo);
        Py_DECREF(constOne);
        
        if (b != localBuffer)
            PyMem_Free(b);
        }
    
    else
        {
        retVal = PyBytes_FromStringAndSize((char *) localBuffer, 0);
        require(retVal, Err_BadReturn);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeT:          Py_DECREF(t);
    Err_FreeConstants:  Py_DECREF(constSignedToSubtract);
                        Py_DECREF(constTwo);
                        Py_DECREF(constOne);
    Err_FreeRetVal:     Py_DECREF(retVal);
    Err_FreeBuffer:     if (b != localBuffer) PyMem_Free(b);
    Err_BadReturn:      return NULL;
    }   /* wkb_UnpackBitsGroup */

static PyObject *wkb_UnpackRest(PyObject *self, PyObject *args)
    {
    char            coerce, strict;
    const char      *format;
    unsigned char   *b;
    int             formatLength;
    
    unsigned long   formatBitSize, formatByteSize, groupCount, itemCount,
                    remainingBits;
    
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    WKB_Context     *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Os#bb", &co, &format, &formatLength, &coerce, &strict),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "walkerbit_capsule");
    require(context, Err_BadReturn);
    
    formatBitSize = FormatByteSize(
      format,
      (unsigned long) formatLength,
      &itemCount) << 3UL;
    
    remainingBits = context->bitLimit - context->currBitOffset;
    
    if (strict)
        {
        require_action(
          remainingBits % formatBitSize == 0,
          Err_BadReturn,
          PyErr_SetString(PyExc_ValueError, "Leftover bits in unpackRest!"););
        }
    
    formatByteSize = (formatBitSize + 7UL) >> 3UL;
    groupCount = remainingBits / formatBitSize;
    
    if (groupCount > 0)
        {
        b = (unsigned char *) PyMem_Malloc(formatByteSize);
        require(b, Err_BadReturn);
        
        retVal = PyTuple_New(groupCount);
        require(retVal, Err_FreeBuffer);
        
        if (coerce && (itemCount == 1))
            {
            while (groupCount--)
                {
                require_noerr(
                  BytesFromBits(context, formatBitSize, b),
                  Err_FreeRetVal);
                
                require_noerr(
                  FormatProcess(
                    retVal,
                    b,
                    format,
                    (unsigned long) formatLength,
                    walkIndex++,
                    context->isBigEndian),
                  Err_FreeRetVal);
                }
            }
        
        else
            {
            while (groupCount--)
                {
                t = PyTuple_New(itemCount);
                require(t, Err_FreeRetVal);
                
                require_noerr(
                  BytesFromBits(context, formatBitSize, b),
                  Err_FreeT);
                
                require_noerr(
                  FormatProcess(
                    t,
                    b,
                    format,
                    (unsigned long) formatLength,
                    0,
                    context->isBigEndian),
                  Err_FreeT);
                
                /*
                 * The following steals a ref to t, so assuming no error
                 * happens, we don't need to explicitly free t.
                 */
                
                require_noerr(
                  PyTuple_SetItem(retVal, walkIndex++, t),
                  Err_FreeT);
                }
            }
        
        PyMem_Free(b);
        }
    
    else
        {
        retVal = PyTuple_New(0);
        require(retVal, Err_BadReturn);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeT:      Py_DECREF(t);
    Err_FreeRetVal: Py_DECREF(retVal);
    Err_FreeBuffer: PyMem_Free(b);
    Err_BadReturn:  return NULL;
    }  /* wkb_UnpackRest */

/* --------------------------------------------------------------------------------------------- */

/*** MODULE CREATION ***/

static struct PyModuleDef walkerbitmodule =
    {
    PyModuleDef_HEAD_INIT,
    "walkerbitbackend",
    NULL,   /* module doc string */
    -1,
    WalkerBitMethods
    };

PyMODINIT_FUNC PyInit_walkerbitbackend(void)
    {
    return PyModule_Create(&walkerbitmodule);
    }  /* PyInit_walkerbitbackend */
