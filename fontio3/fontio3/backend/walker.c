/*
 * walkermodule.c -- Implementation of superfast StringWalkers.
 *
 * Copyright (c) 2009-2012 Monotype Imaging Inc. All Rights Reserved.
 *
 */

#include <Python.h>
#include "AssertMacros.h"

/* --------------------------------------------------------------------------------------------- */

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

/* --------------------------------------------------------------------------------------------- */

/*** TYPES ***/

struct WK_Context
    {
    Py_buffer       liveBuffer;
    PyObject        *originalObject;
    unsigned long   origStart;
    unsigned long   currOffset;
    unsigned long   limit;
    char            isBigEndian;
    char            phase;  /* always 0 through 7 */
    };

#ifndef __cplusplus
typedef struct WK_Context WK_Context;
#endif

/* --------------------------------------------------------------------------------------------- */

/*** PROTOTYPES ***/

static int BytesFromBits(WK_Context *context, unsigned long bitCount, void *buffer);
static void CapsuleDestructor(PyObject *capsule);
static unsigned long FormatByteSize(
    const char *format, unsigned long formatLength, unsigned long *itemCount);
static int FormatProcess(
    PyObject *t, const unsigned char *b, const char *format, unsigned long formatLength,
    Py_ssize_t startIndex, int startIsBigEndian);
static void FreeContext(WK_Context *context);

static PyObject *wk_AbsRest(PyObject *self, PyObject *args);
static PyObject *wk_Align(PyObject *self, PyObject *args);
static PyObject *wk_AsStringAndOffset(PyObject *self, PyObject *args);
static PyObject *wk_AtEnd(PyObject *self, PyObject *args);
static PyObject *wk_BitLength(PyObject *self, PyObject *args);
static PyObject *wk_CalcSize(PyObject *self, PyObject *args);
static PyObject *wk_GetOffset(PyObject *self, PyObject *args);
static PyObject *wk_GetPhase(PyObject *self, PyObject *args);
static PyObject *wk_Group(PyObject *self, PyObject *args);
static PyObject *wk_Length(PyObject *self, PyObject *args);
static PyObject *wk_NewContext(PyObject *self, PyObject *args);
static PyObject *wk_PascalString(PyObject *self, PyObject *args);
static PyObject *wk_Piece(PyObject *self, PyObject *args);
static PyObject *wk_Reset(PyObject *self, PyObject *args);
static PyObject *wk_Rest(PyObject *self, PyObject *args);
static PyObject *wk_SetOffset(PyObject *self, PyObject *args);
static PyObject *wk_Skip(PyObject *self, PyObject *args);
static PyObject *wk_SkipBits(PyObject *self, PyObject *args);
static PyObject *wk_SubWalkerSetup(PyObject *self, PyObject *args);
static PyObject *wk_Unpack(PyObject *self, PyObject *args);
static PyObject *wk_UnpackBCD(PyObject *self, PyObject *args);
static PyObject *wk_UnpackBits(PyObject *self, PyObject *args);
static PyObject *wk_UnpackRest(PyObject *self, PyObject *args);

/* --------------------------------------------------------------------------------------------- */

/*** STATIC GLOBALS ***/

static PyMethodDef WalkerMethods[] = {
    {"wkAbsRest", wk_AbsRest, METH_VARARGS, NULL},
    {"wkAlign", wk_Align, METH_VARARGS, NULL},
    {"wkAsStringAndOffset", wk_AsStringAndOffset, METH_VARARGS, NULL},
    {"wkAtEnd", wk_AtEnd, METH_VARARGS, NULL},
    {"wkBitLength", wk_BitLength, METH_VARARGS, NULL},
    {"wkCalcSize", wk_CalcSize, METH_VARARGS, NULL},
    {"wkGetOffset", wk_GetOffset, METH_VARARGS, NULL},
    {"wkGetPhase", wk_GetPhase, METH_VARARGS, NULL},
    {"wkGroup", wk_Group, METH_VARARGS, NULL},
    {"wkLength", wk_Length, METH_VARARGS, NULL},
    {"wkNewContext", wk_NewContext, METH_VARARGS, NULL},
    {"wkPascalString", wk_PascalString, METH_VARARGS, NULL},
    {"wkPiece", wk_Piece, METH_VARARGS, NULL},
    {"wkReset", wk_Reset, METH_VARARGS, NULL},
    {"wkRest", wk_Rest, METH_VARARGS, NULL},
    {"wkSetOffset", wk_SetOffset, METH_VARARGS, NULL},
    {"wkSkip", wk_Skip, METH_VARARGS, NULL},
    {"wkSkipBits", wk_SkipBits, METH_VARARGS, NULL},
    {"wkSubWalkerSetup", wk_SubWalkerSetup, METH_VARARGS, NULL},
    {"wkUnpack", wk_Unpack, METH_VARARGS, NULL},
    {"wkUnpackBCD", wk_UnpackBCD, METH_VARARGS, NULL},
    {"wkUnpackBits", wk_UnpackBits, METH_VARARGS, NULL},
    {"wkUnpackRest", wk_UnpackRest, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

/* --------------------------------------------------------------------------------------------- */

/*** INTERNAL PROCEDURES ***/

static int BytesFromBits(WK_Context *context, unsigned long bitCount, void *buffer)
    {
    int             phase;
    unsigned char   *from, *to;
    unsigned long   availableBits = 0, byteCount, savedByteCount;
    
    phase = context->phase;
    from = (unsigned char *) context->liveBuffer.buf + context->currOffset;
    to = (unsigned char *) buffer;
    byteCount = savedByteCount = bitCount >> 3UL;
    
    if (context->currOffset < context->limit)
        availableBits = 8 * (context->limit - context->currOffset) - phase;
    
    require(bitCount <= availableBits, BadReturn);
    bitCount &= 7;
    
    if (phase)
        {
        int             counterPhase = 8 - phase;
        unsigned char   thisByte, thisByte2;
        
        while (byteCount--)
            {
            thisByte = (*from++ << phase);
            *to++ = thisByte | (*from >> counterPhase);
            }
        
        if (bitCount)
            {
            if (bitCount + phase <= 8)
                {
                thisByte = (*from << phase);
                *to++ = thisByte & highMasks[8 - bitCount];
                phase += bitCount;
                
                if (phase == 8)
                    {
                    phase = 0;
                    savedByteCount += 1;
                    }
                }
            
            else
                {
                thisByte = (*from++ << phase);
                thisByte2 = (*from & highMasks[16 - (bitCount + phase)]) >> counterPhase;
                *to++ = thisByte | thisByte2;
                savedByteCount += 1;
                phase = (bitCount + phase) - 8;
                }
            }
        
        context->phase = phase;
        }
    
    else
        {
        while (byteCount--)
            *to++ = *from++;
        
        if (bitCount)
            {
            *to = *from & highMasks[8 - bitCount];
            context->phase = (char) bitCount;
            }
        }
    
    context->currOffset += savedByteCount;
    return 0;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  PyErr_SetString(PyExc_IndexError, "Attempt to unpack past the end of the string!");
                return 1;
    }  /* BytesFromBits */

static void CapsuleDestructor(PyObject *capsule)
    {
    WK_Context  *context = PyCapsule_GetPointer(capsule, "walker_capsule");
    
    if (context)
        FreeContext(context);
    }   /* CapsuleDestructor */

static unsigned long FormatByteSize(const char *format, unsigned long formatLength, unsigned long *itemCount)
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

static int FormatProcess(PyObject *t, const unsigned char *b, const char *format, unsigned long formatLength, Py_ssize_t startIndex, int startIsBigEndian)
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

static void FreeContext(WK_Context *context)
    {
    PyBuffer_Release(&context->liveBuffer);
    Py_CLEAR(context->originalObject);
    
    PyMem_Free(context);
    }  /* FreeContext */

/* --------------------------------------------------------------------------------------------- */

/*** INTERFACE PROCEDURES ***/

static PyObject *wk_AbsRest(PyObject *self, PyObject *args)
    {
    int             err;
    PyObject        *co, *retVal;
    Py_ssize_t      origSize;
    unsigned long   offset;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Ok", &co, &offset);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    origSize = context->liveBuffer.len;
    offset += context->origStart;
    
    require(!context->phase, ValueErr);
    
    retVal = PyBytes_FromStringAndSize((const char *) context->liveBuffer.buf + offset, origSize - offset);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    ValueErr:   PyErr_SetString(PyExc_ValueError, "Cannot call absRest when phase is nonzero!");
    BadReturn:  return NULL;
    }  /* wk_AbsRest */

static PyObject *wk_Align(PyObject *self, PyObject *args)
    {
    int             err;
    PyObject        *co;
    unsigned long   bytePhase, multiple;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Ok", &co, &multiple);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    if (context->phase)
        {
        context->phase = 0;
        context->currOffset += 1;
        }
    
    bytePhase = context->currOffset % multiple;
    
    if (bytePhase)
        context->currOffset += multiple - bytePhase;
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_Align */

static PyObject *wk_AsStringAndOffset(PyObject *self, PyObject *args)
    {
    int             err;
    PyObject        *co, *retVal;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    retVal = Py_BuildValue("Ok", context->originalObject, context->currOffset);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_AsStringAndOffset */

static PyObject *wk_AtEnd(PyObject *self, PyObject *args)
    {
    int             err;
    PyObject        *co, *retVal;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    retVal = PyBool_FromLong(context->currOffset == context->limit);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_AtEnd */

static PyObject *wk_BitLength(PyObject *self, PyObject *args)
    {
    int             err;
    PyObject        *co, *retVal;
    unsigned long   n;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    n = 8UL * (context->limit - context->currOffset) - (unsigned char) context->phase;
    
    if (n < 0x80000000UL)
        retVal = PyLong_FromLong((long) n);
    else
        retVal = PyLong_FromUnsignedLong(n);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_BitLength */

static PyObject *wk_CalcSize(PyObject *self, PyObject *args)
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
    }  /* wk_CalcSize */

static PyObject *wk_GetOffset(PyObject *self, PyObject *args)
    {
    char            relative;
    int             err;
    PyObject        *co, *retVal;
    unsigned long   offset;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Ob", &co, &relative);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    offset = context->currOffset;
    
    if (relative)
        offset -= context->origStart;
    
    if (offset > 0x7FFFFFFFUL)
        retVal = PyLong_FromUnsignedLong(offset);
    else
        retVal = PyLong_FromLong(offset);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_GetOffset */

static PyObject *wk_GetPhase(PyObject *self, PyObject *args)
    {
    int             err;
    PyObject        *co, *retVal;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    retVal = PyLong_FromLong(context->phase);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_GetPhase */

static PyObject *wk_Group(PyObject *self, PyObject *args)
    {
    char            finalCoerce;
    const char      *format;
    int             err, formatLength;
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    unsigned char   *b;
    unsigned long   formatByteSize, groupCount, itemCount;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Os#kb", &co, &format, &formatLength, &groupCount, &finalCoerce);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    if (finalCoerce && (groupCount > 1))
        finalCoerce = 0;
    
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    
    b = (unsigned char *) PyMem_Malloc(formatByteSize);
    require(b, BadReturn);
    
    retVal = PyTuple_New(groupCount);
    require(retVal, FreeBuffer);
    
    if (itemCount == 1)
        {
        while (groupCount--)
            {
            err = BytesFromBits(context, 8UL * formatByteSize, b);
            require_noerr(err, FreeRetVal);
            
            err = FormatProcess(retVal, b, format, (unsigned long) formatLength, walkIndex++, context->isBigEndian);
            require_noerr(err, FreeRetVal);
            }
        }
    
    else
        {
        while (groupCount--)
            {
            t = PyTuple_New(itemCount);
            require(t, FreeRetVal);
            
            err = BytesFromBits(context, 8UL * formatByteSize, b);
            require_noerr(err, FreeT);
            
            err = FormatProcess(t, b, format, (unsigned long) formatLength, 0, context->isBigEndian);
            require_noerr(err, FreeT);
            
            /* The following steals a ref to t, so assuming no error happens, we don't need to explicitly free t */
            err = PyTuple_SetItem(retVal, walkIndex++, t);
            require_noerr(err, FreeT);
            }
        }
    
    if (finalCoerce)
        {
        co = PySequence_GetItem(retVal, 0);
        require(co, FreeRetVal);
        
        Py_DECREF(retVal);
        retVal = co;
        }
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeT:      Py_DECREF(t);
    FreeRetVal: Py_DECREF(retVal);
    FreeBuffer: PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* wk_Group */

static PyObject *wk_Length(PyObject *self, PyObject *args)
    {
    char            fromStart;
    int             err;
    PyObject        *co, *retVal;
    unsigned long   n;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Ob", &co, &fromStart);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    /* For compatibility with older versions of StringWalker, this function ignores phase */
    n = context->limit - (fromStart ? context->origStart : context->currOffset);
    
    if (n < 0x80000000UL)
        retVal = PyLong_FromLong((long) n);
    else
        retVal = PyLong_FromUnsignedLong(n);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_Length */

static PyObject *wk_NewContext(PyObject *self, PyObject *args)
    {
    char            isBigEndian;
    int             err;
    PyObject        *obj, *retVal;
    unsigned long   limit, start;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Okkb", &obj, &start, &limit, &isBigEndian);
    require_noerr(err, EH_BadReturn);
    
    context = PyMem_Malloc(sizeof(WK_Context));
    require(context, EH_BadReturn);
    
    Py_INCREF(obj);
    context->originalObject = obj;
    
    err = PyObject_GetBuffer(obj, &context->liveBuffer, PyBUF_SIMPLE);
    require_noerr(err, EH_FreeContext);
    
    context->origStart = start;
    context->currOffset = start;
    context->limit = limit;
    context->isBigEndian = isBigEndian;
    context->phase = 0;
    
    retVal = PyCapsule_New(context, "walker_capsule", CapsuleDestructor);
    require(retVal, EH_ReleaseBuffer);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    EH_ReleaseBuffer:   PyBuffer_Release(&context->liveBuffer);
    EH_FreeContext:     Py_DECREF(obj);
                        PyMem_Free(context);
    EH_BadReturn:       return NULL;
    }  /* wk_NewContext */

static PyObject *wk_PascalString(PyObject *self, PyObject *args)
    {
    char            *b;
    int             err;
    PyObject        *co, *retVal;
    unsigned char   lengthByte;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    err = BytesFromBits(context, 8UL, &lengthByte);
    require_noerr(err, BadReturn);
    
    b = PyMem_Malloc(lengthByte);
    require(b, BadReturn);
    
    err = BytesFromBits(context, 8UL * lengthByte, b);
    require_noerr(err, FreeBuffer);
    
    retVal = PyBytes_FromStringAndSize(b, lengthByte);
    require(retVal, FreeBuffer);
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* wk_PascalString */

static PyObject *wk_Piece(PyObject *self, PyObject *args)
    {
    char            *b, relative, savedPhase;
    int             err;
    PyObject        *co, *retVal;
    unsigned long   length, offset, savedOffset;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Okkb", &co, &length, &offset, &relative);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    savedOffset = context->currOffset;
    savedPhase = context->phase;
    context->phase = 0;
    
    if (relative)
        context->currOffset += offset;
    else
        context->currOffset = offset + context->origStart;
    
    if (context->currOffset + length > context->limit)
        length = context->limit - context->currOffset;
    
    b = PyMem_Malloc(length);
    require(b, BadReturn);
    
    err = BytesFromBits(context, 8UL * length, b);
    require_noerr(err, FreeBuffer);
    
    retVal = PyBytes_FromStringAndSize(b, length);
    require(retVal, FreeBuffer);
    
    PyMem_Free(b);
    context->currOffset = savedOffset;
    context->phase = savedPhase;
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* wk_Piece */

static PyObject *wk_Reset(PyObject *self, PyObject *args)
    {
    int             err;
    PyObject        *co;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    context->currOffset = context->origStart;
    context->phase = 0;
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_Reset */

static PyObject *wk_Rest(PyObject *self, PyObject *args)
    {
    char            *b;
    int             err;
    PyObject        *co, *retVal;
    Py_ssize_t      byteCount;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    byteCount = context->limit - context->currOffset;
    
    b = PyMem_Malloc(byteCount);
    require(b, BadReturn);
    
    err = BytesFromBits(context, 8UL * byteCount - context->phase, b);
    require_noerr(err, FreeBuffer);
    
    retVal = PyBytes_FromStringAndSize(b, byteCount);
    require(retVal, FreeBuffer);
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* wk_Rest */

static PyObject *wk_SetOffset(PyObject *self, PyObject *args)
    {
    char            okToExceed, relative;
    int             err;
    long            offset;
    PyObject        *co;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Olbb", &co, &offset, &relative, &okToExceed);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    context->phase = 0;
    offset += (relative ? context->currOffset : context->origStart);
    require(okToExceed || ((unsigned long) offset < context->limit && offset >= 0), IndexErr);
    context->currOffset = (unsigned long) offset;
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    IndexErr:   PyErr_SetString(PyExc_IndexError, "attempt to set offset past the limit");
    BadReturn:  return NULL;
    }  /* wk_SetOffset */

static PyObject *wk_Skip(PyObject *self, PyObject *args)
    {
    char            resetPhase;
    int             err;
    PyObject        *co;
    unsigned long   byteCount;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Okb", &co, &byteCount, &resetPhase);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    context->currOffset += byteCount;
    
    if (resetPhase)
        context->phase = 0;
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_Skip */

static PyObject *wk_SkipBits(PyObject *self, PyObject *args)
    {
    char            bitRemainder;
    int             err;
    PyObject        *co;
    unsigned long   bitCount, byteCount;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Ok", &co, &bitCount);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    byteCount = bitCount >> 3;
    bitRemainder = (char) (bitCount % 8);
    context->currOffset += byteCount;
    context->phase += bitRemainder;
    
    if (context->phase > 7)
        {
        context->currOffset += 1;
        context->phase -= 8;
        }
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_SkipBits */

static PyObject *wk_SubWalkerSetup(PyObject *self, PyObject *args)
    {
    char            absoluteAnchor, endianChar, relative;
    int             err;
    long            offset;
    PyObject        *co, *newLimit, *retVal;
    unsigned long   newLimitInt;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "OlbbO", &co, &offset, &relative, &absoluteAnchor, &newLimit);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    if (!absoluteAnchor)
        offset += (relative ? context->currOffset : context->origStart);
    
    if (newLimit == Py_None)
        newLimitInt = context->limit;
    
    else
        {
        newLimitInt = (unsigned long) PyLong_AsLong(newLimit);
        require_noerr((newLimitInt == 0xFFFFFFFF) && PyErr_Occurred(), BadReturn);
        
        if (relative)
            newLimitInt += offset;
        
        if (newLimitInt > context->limit)
            newLimitInt = context->limit;
        }
    
    if ((unsigned long) offset > newLimitInt)
        offset = (long) newLimitInt;
    
    endianChar = (context->isBigEndian ? '>' : '<');
    retVal = Py_BuildValue("OlkC", context->originalObject, offset, newLimitInt, endianChar);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* wk_SubWalkerSetup */

static PyObject *wk_Unpack(PyObject *self, PyObject *args)
    {
    char            advance, coerce;
    const char      *format;
    int             err, formatLength;
    PyObject        *co, *retVal;
    unsigned char   *b;
    unsigned long   formatByteSize, itemCount, startingOffset;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Os#bb", &co, &format, &formatLength, &coerce, &advance);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    startingOffset = context->currOffset;  /* in case we need to restore for advance=False */
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    
    retVal = PyTuple_New(itemCount);
    require(retVal, BadReturn);
    
    b = (unsigned char *) PyMem_Malloc(formatByteSize);
    require(b, FreeTuple);
    
    err = BytesFromBits(context, 8UL * formatByteSize, b);
    require_noerr(err, FreeBuffer);
    
    err = FormatProcess(retVal, b, format, (unsigned long) formatLength, 0, context->isBigEndian);
    require_noerr(err, FreeBuffer);
    
    if (coerce && (itemCount == 1))
        {
        co = PySequence_GetItem(retVal, 0);
        require(co, FreeBuffer);
        
        Py_DECREF(retVal);
        retVal = co;
        }
    
    if (!advance)
        context->currOffset = startingOffset;
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(b);
    FreeTuple:  Py_DECREF(retVal);
    BadReturn:  return NULL;
    }  /* wk_Unpack */

static PyObject *wk_UnpackBCD(PyObject *self, PyObject *args)
    {
    char            coerce, walkPhase;
    int             err;
    PyObject        *co, *obj, *retVal;
    unsigned char   *b, *walk;
    unsigned long   bitCount, byteLength, count, i;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Okkb", &co, &count, &byteLength, &coerce);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    bitCount = 4UL * byteLength * count;
    b = PyMem_Malloc((bitCount + 7UL) >> 3);
    require(b, BadReturn);
    
    err = BytesFromBits(context, bitCount, b);
    require_noerr(err, FreeBuffer);
    
    retVal = PyTuple_New(count);
    require(retVal, FreeBuffer);
    walk = b;
    walkPhase = 0;
    
    for (i = 0; i < count; i += 1)
        {
        unsigned long   nybbleCount = byteLength, n = 0;
        
        while (nybbleCount--)
            {
            if (walkPhase)
                {
                n = (n * 10) + (*walk++ & 15);
                walkPhase = 0;
                }
            
            else
                {
                n = (n * 10) + (*walk >> 4);
                walkPhase = 1;
                }
            }
        
        obj = PyLong_FromLong(n);
        require(obj, FreeRetVal);
        
        err = PyTuple_SetItem(retVal, i, obj);  /* steals a ref */
        require_noerr(err, FreeObj);
        }
    
    if (coerce && (count == 1))
        {
        co = PySequence_GetItem(retVal, 0);
        require(co, FreeRetVal);
        
        Py_DECREF(retVal);
        retVal = co;
        }
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeObj:    Py_DECREF(obj);
    FreeRetVal: Py_DECREF(retVal);
    FreeBuffer: PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* wk_UnpackBCD */

static PyObject *wk_UnpackBits(PyObject *self, PyObject *args)
    {
    char            *b, localBuffer[32];
    int             err;
    PyObject        *co, *retVal;
    unsigned long   bitCount, byteCount;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Ok", &co, &bitCount);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    if (bitCount)
        {
        /*
        I'd like to figure out how to only allocate memory once here. As it
        stands now, I have to allocate a buffer to receive the results from
        BytesFromBits, and then pass that in to create the Python string
        object. It would be nice if there were a way to allocate the string
        object and gain access to its internal buffer. When I tried that with
        PyObject_AsWriteBuffer, I got a "TypeError: Cannot use string as
        modifiable buffer" exception.
        */
        
        byteCount = (bitCount + 7UL) >> 3UL;
        
        if (byteCount <= 32)
            b = &localBuffer[0];
        else
            {
            b = PyMem_Malloc(byteCount);
            require(b, BadReturn);
            }
        
        err = BytesFromBits(context, bitCount, b);
        require_noerr(err, FreeBuffer);
        
        retVal = PyBytes_FromStringAndSize(b, byteCount);
        require(retVal, FreeBuffer);
        
        if (byteCount > 32)
            PyMem_Free(b);
        }
    
    else
        {
        retVal = PyBytes_FromStringAndSize(&localBuffer[0], 0);
        require(retVal, BadReturn);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: if (byteCount > 32) PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* wk_UnpackBits */

static PyObject *wk_UnpackRest(PyObject *self, PyObject *args)
    {
    char            coerce;
    const char      *format;
    int             err, formatLength;
    long            groupCount;
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    unsigned char   *b;
    unsigned long   formatByteSize, itemCount;
    WK_Context      *context;
    
    err = !PyArg_ParseTuple(args, "Os#b", &co, &format, &formatLength, &coerce);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "walker_capsule");
    require(context, BadReturn);
    
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    groupCount = (8 * (context->limit - context->currOffset) - context->phase) / (8 * formatByteSize);
    
    if (groupCount > 0)
        {
        b = (unsigned char *) PyMem_Malloc(formatByteSize);
        require(b, BadReturn);
        
        retVal = PyTuple_New(groupCount);
        require(retVal, FreeBuffer);
        
        if (coerce && (itemCount == 1))
            {
            while (groupCount--)
                {
                err = BytesFromBits(context, 8UL * formatByteSize, b);
                require_noerr(err, FreeRetVal);
                
                err = FormatProcess(retVal, b, format, (unsigned long) formatLength, walkIndex++, context->isBigEndian);
                require_noerr(err, FreeRetVal);
                }
            }
        
        else
            {
            while (groupCount--)
                {
                t = PyTuple_New(itemCount);
                require(t, FreeRetVal);
                
                err = BytesFromBits(context, 8UL * formatByteSize, b);
                require_noerr(err, FreeT);
                
                err = FormatProcess(t, b, format, (unsigned long) formatLength, 0, context->isBigEndian);
                require_noerr(err, FreeT);
                
                /* The following steals a ref to t, so assuming no error happens, we don't need to explicitly free t */
                err = PyTuple_SetItem(retVal, walkIndex++, t);
                require_noerr(err, FreeT);
                }
            }
        
        PyMem_Free(b);
        }
    
    else
        {
        retVal = PyTuple_New(0);
        require(retVal, BadReturn);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeT:      Py_DECREF(t);
    FreeRetVal: Py_DECREF(retVal);
    FreeBuffer: PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* wk_UnpackRest */

/* --------------------------------------------------------------------------------------------- */

/*** MODULE CREATION ***/

static struct PyModuleDef walkermodule =
    {
    PyModuleDef_HEAD_INIT,
    "walkerbackend",
    NULL,   /* module doc string */
    -1,
    WalkerMethods
    };

PyMODINIT_FUNC PyInit_walkerbackend(void)
    {
    return PyModule_Create(&walkermodule);
    }  /* PyInit_walkerbackend */
