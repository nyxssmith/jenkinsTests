/*
 * filewalkerbit.c -- Implementation of superfast FileBitWalkers
 *
 * Copyright (c) 2010-2012 Monotype Imaging Inc. All Rights Reserved.
 *
 */

#include <Python.h>
#include "AssertMacros.h"
#include <stdio.h>

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

struct FWKB_Context
    {
    FILE            *f;
    unsigned long   *refCount;
    unsigned long   fileBitSize;
    unsigned long   origBitStart;
    unsigned long   currBitOffset;
    unsigned long   bitLimit;
    char            isBigEndian;
    char            filler[3];
    };

#ifndef __cplusplus
typedef struct FWKB_Context FWKB_Context;
#endif

/* ------------------------------------------------------------------------- */

/*** PROTOTYPES ***/

static int BytesFromBits(
  FWKB_Context  *context,
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

static void FreeContext(FWKB_Context *context);

static int MakeConstants(
  unsigned long bitCountPerItem,
  PyObject **constOne,
  PyObject **constTwo,
  PyObject **constSignedToSubtract);

static PyObject *fwkb_AbsRest(PyObject *self, PyObject *args);
static PyObject *fwkb_Align(PyObject *self, PyObject *args);
static PyObject *fwkb_AtEnd(PyObject *self, PyObject *args);
static PyObject *fwkb_BitLength(PyObject *self, PyObject *args);
static PyObject *fwkb_CalcSize(PyObject *self, PyObject *args);
static PyObject *fwkb_GetOffset(PyObject *self, PyObject *args);
static PyObject *fwkb_Group(PyObject *self, PyObject *args);
static PyObject *fwkb_NewContext(PyObject *self, PyObject *args);
static PyObject *fwkb_PascalString(PyObject *self, PyObject *args);
static PyObject *fwkb_Piece(PyObject *self, PyObject *args);
static PyObject *fwkb_Reset(PyObject *self, PyObject *args);
static PyObject *fwkb_SetOffset(PyObject *self, PyObject *args);
static PyObject *fwkb_Skip(PyObject *self, PyObject *args);
static PyObject *fwkb_SubWalkerSetup(PyObject *self, PyObject *args);
static PyObject *fwkb_Unpack(PyObject *self, PyObject *args);
static PyObject *fwkb_UnpackBits(PyObject *self, PyObject *args);
static PyObject *fwkb_UnpackBitsGroup(PyObject *self, PyObject *args);
static PyObject *fwkb_UnpackRest(PyObject *self, PyObject *args);

/* ------------------------------------------------------------------------- */

/*** STATIC GLOBALS ***/

static PyMethodDef FileWalkerBitMethods[] = {
    {"fwkbAbsRest", fwkb_AbsRest, METH_VARARGS, NULL},
    {"fwkbAlign", fwkb_Align, METH_VARARGS, NULL},
    {"fwkbAtEnd", fwkb_AtEnd, METH_VARARGS, NULL},
    {"fwkbBitLength", fwkb_BitLength, METH_VARARGS, NULL},
    {"fwkbCalcSize", fwkb_CalcSize, METH_VARARGS, NULL},
    {"fwkbGetOffset", fwkb_GetOffset, METH_VARARGS, NULL},
    {"fwkbGroup", fwkb_Group, METH_VARARGS, NULL},
    {"fwkbNewContext", fwkb_NewContext, METH_VARARGS, NULL},
    {"fwkbPascalString", fwkb_PascalString, METH_VARARGS, NULL},
    {"fwkbPiece", fwkb_Piece, METH_VARARGS, NULL},
    {"fwkbReset", fwkb_Reset, METH_VARARGS, NULL},
    {"fwkbSetOffset", fwkb_SetOffset, METH_VARARGS, NULL},
    {"fwkbSkip", fwkb_Skip, METH_VARARGS, NULL},
    {"fwkbSubWalkerSetup", fwkb_SubWalkerSetup, METH_VARARGS, NULL},
    {"fwkbUnpack", fwkb_Unpack, METH_VARARGS, NULL},
    {"fwkbUnpackBits", fwkb_UnpackBits, METH_VARARGS, NULL},
    {"fwkbUnpackBitsGroup", fwkb_UnpackBitsGroup, METH_VARARGS, NULL},
    {"fwkbUnpackRest", fwkb_UnpackRest, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

/* ------------------------------------------------------------------------- */

/*** INTERNAL PROCEDURES ***/

static int BytesFromBits(FWKB_Context *context, unsigned long bitCount, unsigned char *buffer)
    {
    unsigned long   bytesToRead, bytesWereRead, countPhase, currByteOffset, currPhase;
    
    require_action(
      (context->currBitOffset + bitCount) <= context->bitLimit,
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "Attempt to unpack past the limit!"););
    
    currByteOffset = context->currBitOffset >> 3UL;
    currPhase = context->currBitOffset & 7UL;
    countPhase = bitCount & 7UL;
    context->currBitOffset += bitCount;
    
    /* Seek */
    
    require_noerr_action(
      fseek(context->f, (long) currByteOffset, SEEK_SET),
      Err_BadReturn,
      PyErr_SetString(PyExc_IOError, "Unable to seek in BytesFromBits!"););
    
    /* Read */
    
    bytesToRead = (currPhase + bitCount + 7UL) >> 3UL;
    bytesWereRead = fread(buffer, 1, bytesToRead, context->f);
    
    require_action(
      bytesToRead == bytesWereRead,
      Err_BadReturn,
      PyErr_SetString(PyExc_IOError, "Unable to read file!"););
    
    /* Shift buffer, if needed */
    
    if (currPhase)
        {
        unsigned char   *from = buffer;
        unsigned char   *fromNext = from + 1UL;
        unsigned char   *to = buffer;
        unsigned long   counterPhase = 8UL - currPhase;
        
        while (bitCount >= 8UL)
            {
            *to++ = (unsigned char) ((*from++ << currPhase) | (*fromNext++ >> counterPhase));
            bitCount -= 8UL;
            }
        
        if (bitCount)
            {
            if (bitCount <= counterPhase)
                {
                *to = (unsigned char) ((*from << currPhase) & highMasks[8UL - bitCount]);
                }
            
            else
                {
                unsigned long   maskPhase = 8UL - (bitCount - counterPhase);
                
                *to = (unsigned char) ((*from << currPhase) | ((*fromNext & highMasks[maskPhase]) >> counterPhase));
                }
            }
        }
    
    else if (countPhase)
        {
        buffer[bytesToRead - 1UL] &= highMasks[8UL - countPhase];
        }
    
    return 0;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return -1;
    }  /* BytesFromBits */

static void CapsuleDestructor(PyObject *capsule)
    {
    FWKB_Context    *context = PyCapsule_GetPointer(capsule, "filewalkerbit_capsule");
    
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

/* ------------------------------------------------------------------------- */

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

static void FreeContext(FWKB_Context *context)
    {
    /* This is probably not thread-safe. */
    
    *(context->refCount) -= 1UL;
    
    if (*(context->refCount) == 0)
        {
        fclose(context->f);
        PyMem_Free(context->refCount);
        }
    
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

/* ------------------------------------------------------------------------- */

/*** PROTOCOL PROCEDURES ***/

static PyObject *fwkb_AbsRest(PyObject *self, PyObject *args)
    {
    unsigned char   *buffer;
    FWKB_Context    *context;
    unsigned long   bitOffset, byteCount, needBits, saveOffset, startBit;
    PyObject        *co, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ok", &co, &bitOffset),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    startBit = context->origBitStart + bitOffset;
    
    require_action(
      startBit < context->fileBitSize,
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "AbsRest offset past file end!"););
    
    saveOffset = context->currBitOffset;
    context->currBitOffset = startBit;
    needBits = context->fileBitSize - startBit;
    byteCount = (needBits + 7UL) >> 3UL;
    
    buffer = PyMem_Malloc(byteCount + 1UL);  /* always allocate 1 more byte for BytesFromBits */
    require(buffer, Err_RestoreBitOffset);
    
    require_noerr(
      BytesFromBits(context, needBits, buffer),
      Err_FreeBuffer);  /* Python exception was set in BytesFromBits */
    
    retVal = PyBytes_FromStringAndSize((char *) buffer, byteCount);
    require(retVal, Err_FreeBuffer);
    
    PyMem_Free(buffer);
    context->currBitOffset = saveOffset;
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_RestoreBitOffset:   context->currBitOffset = saveOffset;
    Err_FreeBuffer:         PyMem_Free(buffer);
    Err_BadReturn:          return NULL;
    }  /* fwkb_AbsRest */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_Align(PyObject *self, PyObject *args)
    {
    char            absolute;
    FWKB_Context    *context;
    unsigned long   adjOff, adjust, bitMultiple;
    PyObject        *co;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Okb", &co, &bitMultiple, &absolute),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
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
    }  /* fwkb_Align */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_AtEnd(PyObject *self, PyObject *args)
    {
    FWKB_Context    *context;
    PyObject        *co, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    retVal = PyBool_FromLong(context->currBitOffset >= context->bitLimit);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* fwkb_AtEnd */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_BitLength(PyObject *self, PyObject *args)
    {
    FWKB_Context    *context;
    PyObject        *co, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    retVal = PyLong_FromUnsignedLong(context->bitLimit - context->currBitOffset);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* fwkb_BitLength */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_CalcSize(PyObject *self, PyObject *args)
    {
    const char      *format;
    int             formatLength;
    unsigned long   formatByteSize, itemCount;
    PyObject        *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "s#", &format, &formatLength),
      Err_BadReturn);
    
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    
    retVal = PyLong_FromUnsignedLong(formatByteSize);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* fwkb_CalcSize */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_GetOffset(PyObject *self, PyObject *args)
    {
    char            relative;
    FWKB_Context    *context;
    PyObject        *co, *retVal;
    unsigned long   offset;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ob", &co, &relative),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    offset = context->currBitOffset;
    
    if (relative)
        offset -= context->origBitStart;
    
    retVal = Py_BuildValue("k", offset);
    require(retVal, Err_BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* fwkb_GetOffset */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_Group(PyObject *self, PyObject *args)
    {
    char            finalCoerce;
    const char      *format;
    unsigned char   *b;
    FWKB_Context    *context;
    int             formatLength;
    unsigned long   formatByteSize, groupCount, itemCount;
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Os#kb", &co, &format, &formatLength, &groupCount, &finalCoerce),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    if (finalCoerce && (groupCount > 1))
        finalCoerce = 0;
    
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    
    b = (unsigned char *) PyMem_Malloc(formatByteSize + 1UL);  /* always allocate 1 more byte for BytesFromBits */
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
              FormatProcess(retVal, b, format, (unsigned long) formatLength, walkIndex++, context->isBigEndian),
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
              FormatProcess(t, b, format, (unsigned long) formatLength, 0, context->isBigEndian),
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
    }  /* fwkb_Group */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_NewContext(PyObject *self, PyObject *args)
    {
    char            isBigEndian, *path;
    FWKB_Context    *context;
    unsigned long   bitStart;
    PyObject        *bitLimit, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "skOb", &path, &bitStart, &bitLimit, &isBigEndian),
      Err_BadReturn);
    
    context = (FWKB_Context *) PyMem_Malloc(sizeof(FWKB_Context));
    require(context, Err_BadReturn);
    
    context->refCount = (unsigned long *) PyMem_Malloc(sizeof(unsigned long));
    require(context->refCount, Err_FreeContext);
    
    context->f = fopen(path, "rb");
    
    require_action(
      context->f,
      Err_FreeRefCount,
      PyErr_SetString(PyExc_IOError, "Unable to open file!"););
    
    *(context->refCount) = 1UL;
    
    require_noerr_action(
      fseek(context->f, 0, SEEK_END),
      Err_CloseFile,
      PyErr_SetString(PyExc_IOError, "Unable to seek to end of file!"););
    
    context->fileBitSize = ftell(context->f) << 3UL;
    
    if (bitLimit == Py_None)
        context->bitLimit = context->fileBitSize;
    else
        context->bitLimit = (unsigned long) PyLong_AsUnsignedLong(bitLimit);
    
    if (bitStart > context->bitLimit)
        bitStart = context->bitLimit;
    
    context->origBitStart = context->currBitOffset = bitStart;
    context->isBigEndian = isBigEndian;
    
    retVal = PyCapsule_New(context, "filewalkerbit_capsule", CapsuleDestructor);
    require(retVal, Err_CloseFile);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_CloseFile:      fclose(context->f);
    Err_FreeRefCount:   PyMem_Free(context->refCount);
    Err_FreeContext:    PyMem_Free(context);
    Err_BadReturn:      return NULL;
    }  /* fwkb_NewContext */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_PascalString(PyObject *self, PyObject *args)
    {
    unsigned char   *b, lengthByte[2];  /* always allocate 1 more byte for BytesFromBits */
    FWKB_Context    *context;
    PyObject        *co, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    require_noerr(
      BytesFromBits(context, 8UL, lengthByte),
      Err_BadReturn);
    
    b = PyMem_Malloc(lengthByte[0] + 1UL);  /* always allocate 1 more byte for BytesFromBits */
    require(b, Err_BadReturn);
    
    require_noerr(
      BytesFromBits(context, 8UL * lengthByte[0], b),
      Err_FreeBuffer);
    
    retVal = PyBytes_FromStringAndSize((char *) b, lengthByte[0]);
    require(retVal, Err_FreeBuffer);
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeBuffer: PyMem_Free(b);
    Err_BadReturn:  return NULL;
    }  /* fwkb_PascalString */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_Piece(PyObject *self, PyObject *args)
    {
    char            relative;
    unsigned char   *buffer;
    FWKB_Context    *context;
    unsigned long   bitLength, bitOffset, byteLength, saveOffset;
    PyObject        *co, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Okkb", &co, &bitLength, &bitOffset, &relative),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    bitOffset += (relative ? context->currBitOffset : context->origBitStart);
    
    require_action(
      bitOffset + bitLength <= context->bitLimit,
      Err_BadReturn,
      PyErr_SetString(PyExc_IndexError, "Specified piece larger than available data!"););
    
    byteLength = (bitLength + 7UL) >> 3UL;
    buffer = PyMem_Malloc(byteLength + 1UL);  /* always allocate 1 more byte for BytesFromBits */
    require(buffer, Err_BadReturn);
    
    saveOffset = context->currBitOffset;
    context->currBitOffset = bitOffset;
    
    require_noerr(
      BytesFromBits(context, bitLength, buffer),
      Err_FreeBuffer);
    
    retVal = PyBytes_FromStringAndSize((char *) buffer, byteLength);
    require(retVal, Err_FreeBuffer);
    
    context->currBitOffset = saveOffset;
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeBuffer:     PyMem_Free(buffer);
                        context->currBitOffset = saveOffset;
    Err_BadReturn:      return NULL;
    }  /* fwkb_Piece */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_Reset(PyObject *self, PyObject *args)
    {
    FWKB_Context *context;
    PyObject    *co;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &co),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    context->currBitOffset = context->origBitStart;
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /** ERROR HANDLERS ***/
    Err_BadReturn:  return NULL;
    }  /* fwkb_Reset */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_SetOffset(PyObject *self, PyObject *args)
    {
    char            okToExceed, relative;
    long            signedBitOffset;
    unsigned long   bitOffset;
    FWKB_Context    *context;
    PyObject        *co;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Olbb", &co, &signedBitOffset, &relative, &okToExceed),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
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
    }  /* fwkb_SetOffset */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_Skip(PyObject *self, PyObject *args)
    {
    FWKB_Context *context;
    long        bitsToSkip;
    PyObject    *co;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ol", &co, &bitsToSkip),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
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
    }  /* fwkb_Skip */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_SubWalkerSetup(PyObject *self, PyObject *args)
    {
    char            anchor, relative;
    FWKB_Context    *context, *newContext;
    unsigned long   bitOffset, newBitLimit;
    PyObject        *co, *newPyLimit, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "OkbbO", &co, &bitOffset, &relative, &anchor, &newPyLimit),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
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
            if (newBitLimit == 0)
                newBitLimit = context->fileBitSize;
            
            if (newBitLimit > context->fileBitSize)
                newBitLimit = context->fileBitSize;
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
    
    newContext = (FWKB_Context *) PyMem_Malloc(sizeof(FWKB_Context));
    require(newContext, Err_BadReturn);
    
    newContext->f = context->f;
    newContext->refCount = context->refCount;
    newContext->fileBitSize = context->fileBitSize;
    newContext->origBitStart = newContext->currBitOffset = bitOffset;
    newContext->bitLimit = newBitLimit;
    newContext->isBigEndian = context->isBigEndian;
    *(newContext->refCount) += 1UL;
    
    retVal = PyCapsule_New(newContext, "filewalkerbit_capsule", CapsuleDestructor);
    require(retVal, Err_FreeNewContext);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeNewContext: FreeContext(newContext);
    Err_BadReturn:      return NULL;
    }  /* fwkb_SubWalkerSetup */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_Unpack(PyObject *self, PyObject *args)
    {
    char            advance, coerce;
    const char      *format;
    unsigned char   *b;
    FWKB_Context    *context;
    int             formatLength;
    unsigned long   formatByteSize, itemCount, startingBitOffset;
    PyObject        *co, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Os#bb", &co, &format, &formatLength, &coerce, &advance),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    startingBitOffset = context->currBitOffset;  /* in case we need to restore for advance=False */
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    
    retVal = PyTuple_New(itemCount);
    require(retVal, Err_BadReturn);
    
    b = (unsigned char *) PyMem_Malloc(formatByteSize + 1UL);  /* always allocate 1 more byte for BytesFromBits */
    require(b, Err_FreeTuple);
    
    require_noerr(
      BytesFromBits(context, 8UL * formatByteSize, b),
      Err_FreeBuffer);
    
    require_noerr(
      FormatProcess(retVal, b, format, (unsigned long) formatLength, 0, context->isBigEndian),
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
    }  /* fwkb_Unpack */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_UnpackBits(PyObject *self, PyObject *args)
    {
    unsigned char   *b, localBuffer[33];
    FWKB_Context    *context;
    unsigned long   bitCount;
    PyObject        *co, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Ok", &co, &bitCount),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    if (bitCount)
        {
        unsigned long   byteCount = (bitCount + 7UL) >> 3UL;
        
        if (byteCount <= 32UL)
            b = &localBuffer[0];
        
        else
            {
            b = (unsigned char *) PyMem_Malloc(byteCount + 1UL);  /* always allocate 1 more byte for BytesFromBits */
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
    }  /* fwkb_UnpackBits */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_UnpackBitsGroup(PyObject *self, PyObject *args)
    {
    char            wantSigned;
    
    unsigned char   *b,
                    *bWalk,
                    localBuffer[33],
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
    
    FWKB_Context    *context;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Okkb", &co, &bitCountPerItem, &itemCount, &wantSigned),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    totalBitsNeeded = (unsigned long) (bitCountPerItem * itemCount);
    
    if (totalBitsNeeded)
        {
        unsigned long   byteCount = (totalBitsNeeded + 7UL) >> 3UL;
        
        if (byteCount <= 32UL)
            b = &localBuffer[0];
        
        else
            {
            b = (unsigned char *) PyMem_Malloc(byteCount + 1UL);  /* always allocate 1 more byte for BytesFromBits */
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
    }   /* fwkb_UnpackBitsGroup */

/* ------------------------------------------------------------------------- */

static PyObject *fwkb_UnpackRest(PyObject *self, PyObject *args)
    {
    char            coerce, strict;
    const char      *format;
    unsigned char   *b;
    FWKB_Context    *context;
    int             formatLength;
    unsigned long   formatBitSize, formatByteSize, groupCount, itemCount,
                    remainingBits;
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    
    require_noerr(
      !PyArg_ParseTuple(args, "Os#bb", &co, &format, &formatLength, &coerce, &strict),
      Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalkerbit_capsule");
    require(context, Err_BadReturn);
    
    formatBitSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount) << 3UL;
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
        b = (unsigned char *) PyMem_Malloc(formatByteSize + 1UL);  /* always allocate 1 more byte for BytesFromBits */
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
                  FormatProcess(retVal, b, format, (unsigned long) formatLength, walkIndex++, context->isBigEndian),
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
                  FormatProcess(t, b, format, (unsigned long) formatLength, 0, context->isBigEndian),
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
    }  /* fwkb_UnpackRest */

/* ------------------------------------------------------------------------- */

/*** MODULE CREATION ***/

static struct PyModuleDef filewalkerbitmodule =
    {
    PyModuleDef_HEAD_INIT,
    "filewalkerbitbackend",
    NULL,   /* module doc string */
    -1,
    FileWalkerBitMethods
    };

PyMODINIT_FUNC PyInit_filewalkerbitbackend(void)
    {
    return PyModule_Create(&filewalkerbitmodule);
    }  /* PyInit_filewalkerbitbackend */
