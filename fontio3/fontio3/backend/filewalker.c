/*
 * filewalker.c -- Implementation of superfast FileWalkers.
 *
 * Copyright (c) 2010-2012 Monotype Imaging Inc. All Rights Reserved.
 *
 */

#include <Python.h>
#include "AssertMacros.h"
#include <stdio.h>

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

struct FWK_Client
    {
    unsigned long   origStart;
    unsigned long   currOffset;
    unsigned long   limit;
    char            unused;
    char            isBigEndian;
    char            phase;
    unsigned char   byteInProcess;
    };

#ifndef __cplusplus
typedef struct FWK_Client FWK_Client;
#endif

struct FWK_SubContext
    {
    FILE            *f;
    FWK_Client      *lastClientUsed;
    unsigned long   activeClients;
    unsigned long   fileSize;
    };

#ifndef __cplusplus
typedef struct FWK_SubContext FWK_SubContext;
#endif

struct FWK_Context
    {
    FWK_SubContext  *subContext;
    FWK_Client      client;
    };

#ifndef __cplusplus
typedef struct FWK_Context FWK_Context;
#endif

/* --------------------------------------------------------------------------------------------- */

/*** PROTOTYPES ***/

static void BitShiftLeftBuffer(unsigned char *p, unsigned long bitsToShift, unsigned long byteCount);
static void CapsuleDestructor(PyObject *capsule);
static unsigned long FormatByteSize(const char *format, unsigned long formatLength, unsigned long *itemCount);
static int FormatProcess(PyObject *t, const unsigned char *b, const char *format, unsigned long formatLength, Py_ssize_t startIndex, int startIsBigEndian);
static void FreeContext(FWK_Context *context);
static unsigned char *GetFileBitBuffer(FWK_Context *context, unsigned long bitCount);
static int MoveCurrOffset(FWK_Client *client, FWK_SubContext *subContext, long bitCount);

static PyObject *fwk_AbsRest(PyObject *self, PyObject *args);
static PyObject *fwk_Align(PyObject *self, PyObject *args);
static PyObject *fwk_AtEnd(PyObject *self, PyObject *args);
static PyObject *fwk_BitLength(PyObject *self, PyObject *args);
static PyObject *fwk_CalcSize(PyObject *self, PyObject *args);
static PyObject *fwk_DebugPrint(PyObject *self, PyObject *args);
static PyObject *fwk_GetOffset(PyObject *self, PyObject *args);
static PyObject *fwk_GetPhase(PyObject *self, PyObject *args);
static PyObject *fwk_Group(PyObject *self, PyObject *args);
static PyObject *fwk_Length(PyObject *self, PyObject *args);
static PyObject *fwk_NewContext(PyObject *self, PyObject *args);
static PyObject *fwk_PascalString(PyObject *self, PyObject *args);
static PyObject *fwk_Piece(PyObject *self, PyObject *args);
static PyObject *fwk_Reset(PyObject *self, PyObject *args);
static PyObject *fwk_SetOffset(PyObject *self, PyObject *args);
static PyObject *fwk_Skip(PyObject *self, PyObject *args);
static PyObject *fwk_SkipBits(PyObject *self, PyObject *args);
static PyObject *fwk_SubWalkerSetup(PyObject *self, PyObject *args);
static PyObject *fwk_Unpack(PyObject *self, PyObject *args);
static PyObject *fwk_UnpackBCD(PyObject *self, PyObject *args);
static PyObject *fwk_UnpackBits(PyObject *self, PyObject *args);
static PyObject *fwk_UnpackRest(PyObject *self, PyObject *args);

/* --------------------------------------------------------------------------------------------- */

/*** STATIC GLOBALS ***/

static PyMethodDef FileWalkerMethods[] = {
    {"fwkAbsRest", fwk_AbsRest, METH_VARARGS, NULL},
    {"fwkAlign", fwk_Align, METH_VARARGS, NULL},
    {"fwkAtEnd", fwk_AtEnd, METH_VARARGS, NULL},
    {"fwkBitLength", fwk_BitLength, METH_VARARGS, NULL},
    {"fwkCalcSize", fwk_CalcSize, METH_VARARGS, NULL},
    {"fwkDebugPrint", fwk_DebugPrint, METH_VARARGS, NULL},
    {"fwkGetOffset", fwk_GetOffset, METH_VARARGS, NULL},
    {"fwkGetPhase", fwk_GetPhase, METH_VARARGS, NULL},
    {"fwkGroup", fwk_Group, METH_VARARGS, NULL},
    {"fwkLength", fwk_Length, METH_VARARGS, NULL},
    {"fwkNewContext", fwk_NewContext, METH_VARARGS, NULL},
    {"fwkPascalString", fwk_PascalString, METH_VARARGS, NULL},
    {"fwkPiece", fwk_Piece, METH_VARARGS, NULL},
    {"fwkReset", fwk_Reset, METH_VARARGS, NULL},
    {"fwkSetOffset", fwk_SetOffset, METH_VARARGS, NULL},
    {"fwkSkip", fwk_Skip, METH_VARARGS, NULL},
    {"fwkSkipBits", fwk_SkipBits, METH_VARARGS, NULL},
    {"fwkSubWalkerSetup", fwk_SubWalkerSetup, METH_VARARGS, NULL},
    {"fwkUnpack", fwk_Unpack, METH_VARARGS, NULL},
    {"fwkUnpackBCD", fwk_UnpackBCD, METH_VARARGS, NULL},
    {"fwkUnpackBits", fwk_UnpackBits, METH_VARARGS, NULL},
    {"fwkUnpackRest", fwk_UnpackRest, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

/* --------------------------------------------------------------------------------------------- */

/*** INTERNAL PROCEDURES ***/

static void BitShiftLeftBuffer(unsigned char *p, unsigned long bitsToShift, unsigned long byteCount)
    {
    unsigned char   *walkThis = p;
    unsigned char   *walkNext = p + 1;
    unsigned long   rightShift = 8 - bitsToShift;
    
    check(bitsToShift && (bitsToShift < 8));
    
    while (--byteCount)
        {
        *walkThis = (unsigned char) ((*walkThis << bitsToShift) | (*walkNext++ >> rightShift));
        walkThis += 1;
        }
    
    *walkThis = (unsigned char) (*walkThis << bitsToShift);
    }   /* BitShiftLeftBuffer */

static void CapsuleDestructor(PyObject *capsule)
    {
    FWK_Context *context = PyCapsule_GetPointer(capsule, "filewalker_capsule");
    
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

static void FreeContext(FWK_Context *context)
    {
    FWK_SubContext  *subContext = context->subContext;
    FWK_Client      *client = &context->client;
    
    if (subContext->lastClientUsed == client)
        subContext->lastClientUsed = NULL;
    
    subContext->activeClients -= 1;
    
    if (subContext->activeClients == 0)
        {
        fclose(subContext->f);
        PyMem_Free(subContext);
        }
    
    PyMem_Free(context);
    }   /* FreeContext */

static unsigned char *GetFileBitBuffer(FWK_Context *context, unsigned long bitCount)
    {
    FWK_SubContext  *subContext = context->subContext;
    FWK_Client      *client = &context->client;
    unsigned char   *p;
    unsigned long   availableBits = 0, needBytes, readBytes;
    
    if (subContext->lastClientUsed != client)
        {
        fseek(subContext->f, client->currOffset, 0);
        subContext->lastClientUsed = client;
        }
    
    availableBits = (client->limit - client->currOffset) << 3UL;
    
    if (client->phase)
        availableBits += (8UL - client->phase);
    
    require_action(
      bitCount <= availableBits,
      BadReturn,
      PyErr_SetString(PyExc_ValueError, "Not enough bits to satisfy request!"););
    
    if (client->phase == 0)
        {
        if ((bitCount & 7) == 0)  /* integral number of bytes */
            {
            needBytes = bitCount >> 3UL;
            p = (unsigned char *) PyMem_Malloc(needBytes);
            require(p, BadReturn);
            readBytes = fread(p, 1, needBytes, subContext->f);
            
            require_action(
              readBytes == needBytes,
              FreeP,
              PyErr_SetString(PyExc_IOError, "Unable to read file!"););
            }
        
        else  /* non-integral number of bytes */
            {
            needBytes = 1UL + (bitCount >> 3UL);
            p = (unsigned char *) PyMem_Malloc(needBytes);
            require(p, BadReturn);
            readBytes = fread(p, 1, needBytes, subContext->f);
            
            require_action(
              readBytes == needBytes,
              FreeP,
              PyErr_SetString(PyExc_IOError, "Unable to read file!"););
            
            client->byteInProcess = p[needBytes - 1];
            client->phase = bitCount & 7;
            p[needBytes - 1] &= highMasks[8 - client->phase];
            }
        }
    
    else  /* client->phase is nonsero */
        {
        if ((bitCount & 7) == 0)
            {
            needBytes = bitCount >> 3UL;
            p = (unsigned char *) PyMem_Malloc(needBytes + 1);
            require(p, BadReturn);
            p[0] = client->byteInProcess;
            readBytes = fread(p + 1, 1, needBytes, subContext->f);
            
            require_action(
              readBytes == needBytes,
              FreeP,
              PyErr_SetString(PyExc_IOError, "Unable to read file!"););
            
            client->byteInProcess = p[needBytes];
            p[needBytes] &= highMasks[8 - client->phase];
            BitShiftLeftBuffer(p, client->phase, needBytes + 1);
            }
        
        else
            {
            unsigned long   phaseAvailBits = 8 - client->phase;
            
            if (((bitCount - phaseAvailBits) & 7) == 0)
                {
                needBytes = (bitCount - phaseAvailBits) >> 3UL;
                p = (unsigned char *) PyMem_Malloc(needBytes + 1);
                require(p, BadReturn);
                p[0] = client->byteInProcess;
                readBytes = fread(p + 1, 1, needBytes, subContext->f);
                
                require_action(
                  readBytes == needBytes,
                  FreeP,
                  PyErr_SetString(PyExc_IOError, "Unable to read file!"););
                
                BitShiftLeftBuffer(p, client->phase, needBytes + 1);
                client->phase = 0;
                }
            
            else
                {
                needBytes = (bitCount - phaseAvailBits + 7) >> 3UL;
                p = (unsigned char *) PyMem_Malloc(needBytes + 1);
                require(p, BadReturn);
                p[0] = client->byteInProcess;
                readBytes = fread(p + 1, 1, needBytes, subContext->f);
                
                require_action(
                  readBytes == needBytes,
                  FreeP,
                  PyErr_SetString(PyExc_IOError, "Unable to read file!"););
                
                client->byteInProcess = p[needBytes];
                BitShiftLeftBuffer(p, client->phase, needBytes + 1);
                client->phase = (char) ((bitCount - phaseAvailBits) & 7);
                p[needBytes] &= highMasks[8 - client->phase];
                }
            }
        }
    
    client->currOffset += needBytes;
    return p;
    
    /*** ERROR HANDLERS ***/
    FreeP:          PyMem_Free(p);
    BadReturn:      return NULL;
    }   /* GetFileBitBuffer */

static int MoveCurrOffset(FWK_Client *client, FWK_SubContext *subContext, long bitCount)
    {
    long    currBitPosition = ((client->currOffset - (client->phase ? 1 : 0)) << 3UL) + client->phase;
    long    newBitPosition = currBitPosition + bitCount;  /* signed arithmetic, remember */
    long    limitBitPosition = client->limit << 3UL;
    
    if (newBitPosition < 0)
        newBitPosition = 0;
    else if (newBitPosition > limitBitPosition)
        newBitPosition = limitBitPosition;
    
    if (newBitPosition & 7)  /* new position has nonzero phase */
        {
        client->currOffset = (unsigned long) ((newBitPosition + 7) >> 3);
        client->phase = (char) (newBitPosition & 7);
        }
    
    else
        {
        client->currOffset = (unsigned long) (newBitPosition >> 3);
        client->phase = 0;
        }
    
    /* If the new phase is nonzero, we need to read the byteInProcess value */
    if (client->phase)
        {
        fseek(subContext->f, client->currOffset - 1, 0);
        
        require_action(
          fread(&client->byteInProcess, 1, 1, subContext->f) == 1,
          BadReturn,
          PyErr_SetString(PyExc_IOError, "Unable to read file!"););
        }
    
    subContext->lastClientUsed = NULL;  /* force repositioning */
    return 0;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return -1;
    }  /* fwk_SkipBits */

/* --------------------------------------------------------------------------------------------- */

/*** INTERFACE PROCEDURES ***/

static PyObject *fwk_AbsRest(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    unsigned char   *buffer;
    unsigned long   byteCount, bytesRead, offset;
    
    err = !PyArg_ParseTuple(args, "Ok", &co, &offset);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    require_action(
      client->phase == 0,
      BadReturn,
      PyErr_SetString(PyExc_ValueError, "Cannot call absRest when phase is nonzero!"););
    
    subContext->lastClientUsed = client;  /* we are fseeking, so just change it */
    offset += client->origStart;
    byteCount = subContext->fileSize - offset;
    fseek(subContext->f, offset, 0);
    buffer = PyMem_Malloc(byteCount);
    require(buffer, BadReturn);
    
    bytesRead = fread(buffer, 1, byteCount, subContext->f);
    
    require_action(
      bytesRead == byteCount,
      FreeBuffer,
      PyErr_SetString(PyExc_IOError, "Unable to read file!"););
    
    fseek(subContext->f, client->currOffset, 0);  /* clean up file pointer */
    retVal = PyBytes_FromStringAndSize((const char *) buffer, byteCount);
    require(retVal, FreeBuffer);
    
    PyMem_Free(buffer);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(buffer);
    BadReturn:  return NULL;
    }   /* fwk_AbsRest */

static PyObject *fwk_Align(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co;
    unsigned long   bytePhase, multiple;
    
    err = !PyArg_ParseTuple(args, "Ok", &co, &multiple);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    /* Because of read-ahead, we only need to set the phase to 0; the offset is already right. */
    client->phase = 0;
    bytePhase = client->currOffset % multiple;
    
    if (bytePhase)
        client->currOffset += multiple - bytePhase;
    
    subContext->lastClientUsed = client;  /* we are fseeking, so just change it */
    fseek(subContext->f, client->currOffset, 0);
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }   /* fwk_Align */

static PyObject *fwk_AtEnd(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    retVal = PyBool_FromLong((client->currOffset == client->limit) && (client->phase == 0));
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_AtEnd */

static PyObject *fwk_BitLength(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    unsigned long   n;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    n = (client->limit - client->currOffset) << 3UL;
    
    if (client->phase)
        n += (8UL - client->phase);
    
    if (n < 0x80000000UL)
        retVal = PyLong_FromLong((long) n);
    else
        retVal = PyLong_FromUnsignedLong(n);
    
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_BitLength */

static PyObject *fwk_CalcSize(PyObject *self, PyObject *args)
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
    }  /* fwk_CalcSize */

static PyObject *fwk_DebugPrint(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    printf("Context address is 0x%08lX\n", (unsigned long) context);
    printf("Subcontext address is 0x%08lX\n", (unsigned long) subContext);
    printf("Number of active clients: %lu\n", subContext->activeClients);
    printf("Last client used address is 0x%08lX\n", (unsigned long) subContext->lastClientUsed);
    printf("File size: %lu\n", subContext->fileSize);
    printf("Original start: %lu\n", client->origStart);
    printf("Current offset: %lu\n", client->currOffset);
    printf("Limit: %lu\n", client->limit);
    printf("Phase: %d\n", client->phase);
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }   /* fwk_DebugPrint */

static PyObject *fwk_GetOffset(PyObject *self, PyObject *args)
    {
    char            relative;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    unsigned long   offset;
    
    err = !PyArg_ParseTuple(args, "Ob", &co, &relative);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    offset = client->currOffset - (client->phase ? 1 : 0);
    
    if (relative)
        offset -= client->origStart;
    
    if (offset > 0x7FFFFFFFUL)
        retVal = PyLong_FromUnsignedLong(offset);
    else
        retVal = PyLong_FromLong(offset);
    
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_GetOffset */

static PyObject *fwk_GetPhase(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    retVal = PyLong_FromLong((long) client->phase);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }   /* fwk_GetPhase */

static PyObject *fwk_Group(PyObject *self, PyObject *args)
    {
    char            finalCoerce;
    const char      *format;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err, formatLength;
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    unsigned char   *b;
    unsigned long   formatByteSize, groupCount, itemCount;
    
    err = !PyArg_ParseTuple(args, "Os#kb", &co, &format, &formatLength, &groupCount, &finalCoerce);
    require_noerr(err, BadReturn);
    
    if (finalCoerce && (groupCount > 1))
        finalCoerce = 0;
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    retVal = PyTuple_New(groupCount);
    require(retVal, BadReturn);
    
    if (itemCount == 1)
        {
        while (groupCount--)
            {
            b = GetFileBitBuffer(context, formatByteSize << 3UL);
            require(b, FreeRetVal);
            
            err = FormatProcess(retVal, b, format, (unsigned long) formatLength, walkIndex++, client->isBigEndian);
            require_noerr(err, FreeBuffer);
            
            PyMem_Free(b);
            }
        }
    
    else  /* itemCount is more than one */
        {
        while (groupCount--)
            {
            b = GetFileBitBuffer(context, formatByteSize << 3UL);
            require(b, FreeRetVal);
            
            t = PyTuple_New(itemCount);
            require(t, FreeBuffer);
            
            err = FormatProcess(t, b, format, (unsigned long) formatLength, 0, client->isBigEndian);
            require_noerr(err, FreeT);
            
            /* The following steals a reference to t, so we don't need to explicitly free t */
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
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeT:      Py_DECREF(t);
    FreeBuffer: PyMem_Free(b);
    FreeRetVal: Py_DECREF(retVal);
    BadReturn:  return NULL;
    }   /* fwk_Group */

static PyObject *fwk_Length(PyObject *self, PyObject *args)
    {
    char            fromStart;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    unsigned long   n;
    
    err = !PyArg_ParseTuple(args, "Ob", &co, &fromStart);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    /* For compatibility with older versions of StringWalker, this function ignores phase */
    n = client->limit - (fromStart ? client->origStart : client->currOffset);
    
    if (n < 0x80000000UL)
        retVal = PyLong_FromLong((long) n);
    else
        retVal = PyLong_FromUnsignedLong(n);
    
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_Length */

static PyObject *fwk_NewContext(PyObject *self, PyObject *args)
    {
    char            isBigEndian, *path;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *limit, *retVal;
    unsigned long   start;
    
    err = !PyArg_ParseTuple(args, "skOb", &path, &start, &limit, &isBigEndian);
    require_noerr(err, BadReturn);
    
    context = (FWK_Context *) PyMem_Malloc(sizeof(FWK_Context));
    require(context, BadReturn);
    
    client = &context->client;
    subContext = (FWK_SubContext *) PyMem_Malloc(sizeof(FWK_SubContext));
    require(subContext, FW_FreeContext);
    
    context->subContext = subContext;
    subContext->f = fopen(path, "rb");
    
    require_action(
      subContext->f,
      FreeSubContext,
      PyErr_SetString(PyExc_IOError, "Unable to open file!"););
    
    subContext->activeClients = 1;
    subContext->lastClientUsed = client;
    fseek(subContext->f, 0, 2);
    subContext->fileSize = ftell(subContext->f);
    
    if (limit == Py_None)
        client->limit = subContext->fileSize;
    else
        client->limit = (unsigned long) PyLong_AsUnsignedLong(limit);
    
    if (start > client->limit)
        start = client->limit;
    
    fseek(subContext->f, start, 0);
    client->origStart = client->currOffset = start;
    client->isBigEndian = isBigEndian;
    client->phase = 0;
    
    retVal = PyCapsule_New(context, "filewalker_capsule", CapsuleDestructor);
    require(retVal, CloseFile);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    CloseFile:      fclose(subContext->f);
    FreeSubContext: PyMem_Free(subContext);
    FW_FreeContext: PyMem_Free(context);
    BadReturn:      return NULL;
    }   /* fwk_NewContext */

static PyObject *fwk_PascalString(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    unsigned char   *b, *lengthByte;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    lengthByte = GetFileBitBuffer(context, 8UL);
    require(lengthByte, BadReturn);
    
    b = GetFileBitBuffer(context, (*lengthByte) << 3UL);
    require_noerr(err, FreeLength);
    
    retVal = PyBytes_FromStringAndSize((char *) b, *lengthByte);
    require(retVal, FreeBuffer);
    
    PyMem_Free(b);
    PyMem_Free(lengthByte);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(b);
    FreeLength: PyMem_Free(lengthByte);
    BadReturn:  return NULL;
    }  /* fwk_PascalString */

static PyObject *fwk_Piece(PyObject *self, PyObject *args)
    {
    char            relative, savedPhase;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    unsigned char   *b;
    unsigned long   length, offset, savedOffset;
    
    err = !PyArg_ParseTuple(args, "Okkb", &co, &length, &offset, &relative);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    savedOffset = client->currOffset;
    savedPhase = client->phase;
    
    if (client->phase)
        {
        client->phase = 0;
        client->currOffset -= 1;  /* filewalkers do lookahead, unlike walkers */
        }
    
    if (relative)
        client->currOffset += offset;
    else
        client->currOffset = offset + client->origStart;
    
    if (client->currOffset + length > client->limit)
        length = client->limit - client->currOffset;
    
    subContext->lastClientUsed = client;
    fseek(subContext->f, client->currOffset, 0);
    
    b = GetFileBitBuffer(context, length << 3UL);
    require(b, BadReturn);
    
    retVal = PyBytes_FromStringAndSize((char *) b, length);
    require(retVal, FreeBuffer);
    
    PyMem_Free(b);
    client->currOffset = savedOffset;
    client->phase = savedPhase;
    subContext->lastClientUsed = NULL;  /* force repositioning next time */
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(b);
    BadReturn:  return NULL;
    }  /* fwk_Piece */

static PyObject *fwk_Reset(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co;
    
    err = !PyArg_ParseTuple(args, "O", &co);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    client->currOffset = client->origStart;
    client->phase = 0;
    subContext->lastClientUsed = NULL;  /* force repositioning */
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_Reset */

static PyObject *fwk_SetOffset(PyObject *self, PyObject *args)
    {
    char            okToExceed, relative;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    long            offset;
    PyObject        *co;
    
    err = !PyArg_ParseTuple(args, "Olbb", &co, &offset, &relative, &okToExceed);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    if (client->phase)
        {
        client->phase = 0;
        client->currOffset -= 1;  /* filewalkers do lookahead, unlike walkers */
        }
    
    offset += (relative ? client->currOffset : client->origStart);
    
    require_action(
      okToExceed || ((unsigned long) offset < client->limit && offset >= 0),
      BadReturn,
      PyErr_SetString(PyExc_IndexError, "attempt to set offset past the limit"););
    
    client->currOffset = (unsigned long) offset;
    subContext->lastClientUsed = NULL;  /* force repositioning */
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_SetOffset */

static PyObject *fwk_Skip(PyObject *self, PyObject *args)
    {
    char            resetPhase;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co;
    long            byteCount;
    
    err = !PyArg_ParseTuple(args, "Olb", &co, &byteCount, &resetPhase);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    if (resetPhase && client->phase)
        {
        client->phase = 0;
        byteCount -= 1;
        }
    
    err = MoveCurrOffset(client, subContext, byteCount << 3);
    require_noerr(err, BadReturn);
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_Skip */

static PyObject *fwk_SkipBits(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co;
    long            bitCount;
    
    err = !PyArg_ParseTuple(args, "Ol", &co, &bitCount);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    err = MoveCurrOffset(client, subContext, bitCount);
    require_noerr(err, BadReturn);
    
    Py_INCREF(Py_None);
    return Py_None;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* fwk_SkipBits */

static PyObject *fwk_SubWalkerSetup(PyObject *self, PyObject *args)
    {
    char            absoluteAnchor, relative;
    FWK_Client      *newClient, *oldClient;
    FWK_Context     *newContext, *oldContext;
    FWK_SubContext  *subContext;
    int             err;
    long            offset;
    PyObject        *co, *newLimit, *retVal;
    unsigned long   newLimitInt;
    
    err = !PyArg_ParseTuple(args, "OlbbO", &co, &offset, &relative, &absoluteAnchor, &newLimit);
    require_noerr(err, BadReturn);
    
    oldContext = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(oldContext, BadReturn);
    
    subContext = oldContext->subContext;
    oldClient = &oldContext->client;
    
    newContext = (FWK_Context *) PyMem_Malloc(sizeof(FWK_Context));
    require(newContext, BadReturn);
    
    newContext->subContext = subContext;
    newClient = &newContext->client;
    newLimitInt = oldClient->limit;
    
    if (newLimit != Py_None)
        {
        newLimitInt = (unsigned long) PyLong_AsLong(newLimit);
        require_noerr((newLimitInt == 0xFFFFFFFF) && PyErr_Occurred(), FreeNewContext);
        }
    
    if (!absoluteAnchor)
        {
        offset += (relative ? oldClient->currOffset : oldClient->origStart);
        
        if (newLimit != Py_None)
            newLimitInt += (relative ? offset : oldClient->origStart);
        }
    
    if (newLimitInt > oldClient->limit)
        newLimitInt = oldClient->limit;
    
    if ((unsigned long) offset > newLimitInt)
        offset = (long) newLimitInt;
    
    newClient->origStart = newClient->currOffset = offset;
    newClient->limit = newLimitInt;
    newClient->isBigEndian = oldClient->isBigEndian;
    newClient->phase = 0;
    subContext->activeClients += 1;
    subContext->lastClientUsed = newClient;
    fseek(subContext->f, offset, 0);
    
    retVal = PyCapsule_New(newContext, "filewalker_capsule", CapsuleDestructor);
    require(retVal, FreeNewContext);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeNewContext: PyMem_Free(newContext);
    BadReturn:      return NULL;
    }   /* fwk_SubWalkerSetup */

static PyObject *fwk_Unpack(PyObject *self, PyObject *args)
    {
    char            advance, coerce;
    const char      *format;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err, formatLength;
    PyObject        *co, *retVal;
    unsigned char   *b;
    unsigned long   formatByteSize, itemCount, startingOffset;
    
    err = !PyArg_ParseTuple(args, "Os#bb", &co, &format, &formatLength, &coerce, &advance);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    startingOffset = client->currOffset;  /* in case it needs to get reset for no advance case */
    
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    
    retVal = PyTuple_New(itemCount);
    require(retVal, BadReturn);
    
    b = GetFileBitBuffer(context, formatByteSize << 3UL);
    require(b, FreeTuple);
    
    err = FormatProcess(retVal, b, format, (unsigned long) formatLength, 0, client->isBigEndian);
    require_noerr(err, FreeBuffer);
    
    if (coerce && (itemCount == 1))
        {
        co = PySequence_GetItem(retVal, 0);
        require(co, FreeBuffer);
        
        Py_DECREF(retVal);
        retVal = co;
        }
    
    if (!advance)
        {
        fseek(subContext->f, startingOffset, 0);
        client->currOffset = startingOffset;
        }
    
    PyMem_Free(b);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuffer: PyMem_Free(b);
    FreeTuple:  Py_DECREF(retVal);
    BadReturn:  return NULL;
    }  /* fwk_Unpack */

static PyObject *fwk_UnpackBCD(PyObject *self, PyObject *args)
    {
    char            coerce, walkPhase;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *obj, *retVal;
    unsigned char   *b, *walk;
    unsigned long   bitCount, byteLength, count, i;
    
    err = !PyArg_ParseTuple(args, "Okkb", &co, &count, &byteLength, &coerce);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    bitCount = 4UL * byteLength * count;
    
    b = GetFileBitBuffer(context, bitCount);
    require(b, BadReturn);
    
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
    }  /* fwk_UnpackBCD */

static PyObject *fwk_UnpackBits(PyObject *self, PyObject *args)
    {
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err;
    PyObject        *co, *retVal;
    unsigned char   *b;
    unsigned long   bitCount;
    
    err = !PyArg_ParseTuple(args, "Ok", &co, &bitCount);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    if (bitCount)
        {
        b = GetFileBitBuffer(context, bitCount);
        require(b, BadReturn);
        
        retVal = PyBytes_FromStringAndSize((char *) b, (bitCount + 7) >> 3);
        require(retVal, FreeB);
        
        PyMem_Free(b);
        }
    
    else
        {
        retVal = PyBytes_FromStringAndSize("", 0);
        require(retVal, BadReturn);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeB:      PyMem_Free(b);
    BadReturn:  return NULL;
    }   /* fwk_UnpackBits */

static PyObject *fwk_UnpackRest(PyObject *self, PyObject *args)
    {
    char            coerce;
    const char      *format;
    FWK_Client      *client;
    FWK_Context     *context;
    FWK_SubContext  *subContext;
    int             err, formatLength;
    long            groupCount;
    PyObject        *co, *retVal, *t;
    Py_ssize_t      walkIndex = 0;
    unsigned char   *b;
    unsigned long   bitsLeft, formatByteSize, itemCount;
    
    err = !PyArg_ParseTuple(args, "Os#b", &co, &format, &formatLength, &coerce);
    require_noerr(err, BadReturn);
    
    context = PyCapsule_GetPointer(co, "filewalker_capsule");
    require(context, BadReturn);
    
    subContext = context->subContext;
    client = &context->client;
    
    formatByteSize = FormatByteSize(format, (unsigned long) formatLength, &itemCount);
    bitsLeft = (client->limit - client->currOffset) << 3UL;
    
    if (client->phase)
        bitsLeft += (8UL - client->phase);
    
    groupCount = (long) (bitsLeft / (8 * formatByteSize));
    
    if (groupCount > 0)
        {
        retVal = PyTuple_New(groupCount);
        require(retVal, BadReturn);
        
        if (coerce && (itemCount == 1))
            {
            while (groupCount--)
                {
                b = GetFileBitBuffer(context, 8UL * formatByteSize);
                require(b, FreeRetVal);
                
                err = FormatProcess(retVal, b, format, (unsigned long) formatLength, walkIndex++, client->isBigEndian);
                require_noerr(err, FreeBuffer);
                
                PyMem_Free(b);
                }
            }
        
        else
            {
            while (groupCount--)
                {
                b = GetFileBitBuffer(context, 8UL * formatByteSize);
                require(b, FreeRetVal);
                
                t = PyTuple_New(itemCount);
                require(t, FreeBuffer);
                
                err = FormatProcess(t, b, format, (unsigned long) formatLength, 0, client->isBigEndian);
                require_noerr(err, FreeT);
                
                /* The following steals a ref to t, so we don't need to explicitly free t */
                err = PyTuple_SetItem(retVal, walkIndex++, t);
                require_noerr(err, FreeT);
                
                PyMem_Free(b);
                }
            }
        }
    
    else
        {
        retVal = PyTuple_New(0);
        require(retVal, BadReturn);
        }
    
    /* We have not touched client->currOffset throughout this function, by design */
    subContext->lastClientUsed = NULL;  /* force repositioning */
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeT:      Py_DECREF(t);
    FreeBuffer: PyMem_Free(b);
    FreeRetVal: Py_DECREF(retVal);
    BadReturn:  return NULL;
    }  /* fwk_UnpackRest */

/* --------------------------------------------------------------------------------------------- */

/*** MODULE CREATION ***/

static struct PyModuleDef filewalkermodule =
    {
    PyModuleDef_HEAD_INIT,
    "filewalkerbackend",
    NULL,   /* module doc string */
    -1,
    FileWalkerMethods
    };

PyMODINIT_FUNC PyInit_filewalkerbackend(void)
    {
    return PyModule_Create(&filewalkermodule);
    }  /* PyInit_filewalkerbackend */
