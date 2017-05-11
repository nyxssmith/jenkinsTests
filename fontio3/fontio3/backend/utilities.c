/*
 * utilities.c -- Implementation of fast utilities.
 *
 * Copyright (c) 2009-2010, 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
 *
 */

#include <Python.h>
#include "AssertMacros.h"

/* --------------------------------------------------------------------------------------------- */

/*** PROTOTYPES ***/

static unsigned long CalcSizeFromFormat(const char *format, unsigned long *itemCount);
static unsigned long GetNextRepeat(char **format);

static PyObject *ut_Checksum(PyObject *self, PyObject *args);
static PyObject *ut_Explode(PyObject *self, PyObject *args);
static PyObject *ut_Implode(PyObject *self, PyObject *args);
static PyObject *ut_Pack(PyObject *self, PyObject *args);

/* --------------------------------------------------------------------------------------------- */

/*** STATIC GLOBALS ***/

static PyMethodDef UtilitiesMethods[] = {
    {"utChecksum", ut_Checksum, METH_VARARGS, NULL},
    {"utExplode", ut_Explode, METH_VARARGS, NULL},
    {"utImplode", ut_Implode, METH_VARARGS, NULL},
    {"utPack", ut_Pack, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

/* --------------------------------------------------------------------------------------------- */

/*** PRIVATE PROCEDURES ***/

static unsigned long CalcSizeFromFormat(const char *format, unsigned long *itemCount)
    {
    char            c = *format++;
    unsigned long   repeat = 0;
    unsigned long   size = 0;
    
    *itemCount = 0;
    
    while (c)
        {
        if (c >= '0' && c <= '9')
            repeat = (10 * repeat) + (c - '0');
        
        else
            {
            switch (c)
                {
                case 'B':
                case 'b':
                case 'c':
                case 'p':
                case 's':
                case 'x':
                    if (!repeat)
                        repeat = 1;
                    
                    if (c == 'p' || c == 's')
                        *itemCount += 1;
                    else if (c != 'x')
                        *itemCount += repeat;
                    
                    size += repeat;
                    repeat = 0;
                    break;
                
                case 'H':
                case 'h':
                    if (!repeat)
                        repeat = 1;
                    
                    *itemCount += repeat;
                    size += repeat * 2;
                    repeat = 0;
                    break;
                
                case 'T':
                case 't':
                    if (!repeat)
                        repeat = 1;
                    
                    *itemCount += repeat;
                    size += repeat * 3;
                    repeat = 0;
                    break;
                
                case 'f':
                case 'I':
                case 'i':
                case 'L':
                case 'l':
                    if (!repeat)
                        repeat = 1;
                    
                    *itemCount += repeat;
                    size += repeat * 4;
                    repeat = 0;
                    break;
                
                case 'd':
                case 'Q':
                case 'q':
                    if (!repeat)
                        repeat = 1;
                    
                    *itemCount += repeat;
                    size += repeat * 8;
                    repeat = 0;
                    break;
                
                default:
                    break;
                }
            }
        
        c = *format++;
        }
    
    return size;
    }  /* CalcSizeFromFormat */

/* --------------------------------------------------------------------------------------------- */

static unsigned long GetNextRepeat(char **format)
    {
    int             done = 0;
    unsigned long   repeat = 0;
    
    while (!done)
        {
        if (**format >= '0' && **format <= '9')
            done = 1;
        
        else
            {
            switch (**format)
                {
                case 'B':
                case 'b':
                case 'c':
                case 'd':
                case 'f':
                case 'H':
                case 'h':
                case 'I':
                case 'i':
                case 'L':
                case 'l':
                case 'p':
                case 'Q':
                case 'q':
                case 's':
                case 'T':
                case 't':
                case 'x':
                    done = 1;
                    break;
                
                default:
                    (*format) += 1;
                    break;
                }
            }
        }
    
    while (**format >= '0' && **format <= '9')
        repeat = (10 * repeat) + (*(*format)++ - '0');
    
    if (!repeat)
        repeat = 1;
    
    done = 0;
    
    while (!done)
        {
        switch (**format)
            {
            case 'B':
            case 'b':
            case 'c':
            case 'd':
            case 'f':
            case 'H':
            case 'h':
            case 'I':
            case 'i':
            case 'L':
            case 'l':
            case 'p':
            case 'Q':
            case 'q':
            case 's':
            case 'T':
            case 't':
            case 'x':
                done = 1;
                break;
            
            default:
                (*format) += 1;
                break;
            }
        }
    
    return repeat;
    }  /* GetNextRepeat */

/* --------------------------------------------------------------------------------------------- */

/*** INTERFACE PROCEDURES ***/

static PyObject *ut_Checksum(PyObject *self, PyObject *args)
    {
    int                 err;
    Py_buffer           buffer;
    Py_ssize_t          len;
    PyObject            *obj, *retVal;
    const unsigned char *walk;
    unsigned char       d[4], *p;
    unsigned long       checksum = 0;
    
    err = !PyArg_ParseTuple(args, "O", &obj);
    require_noerr(err, BadReturn);
    
    require_action(
      PyObject_CheckBuffer(obj),
      BadReturn,
      PyErr_SetString(
        PyExc_ValueError,
        "Checksum requires a bytes or bytearray object!"););
    
    err = PyObject_GetBuffer(obj, &buffer, PyBUF_SIMPLE);
    require_noerr(err, BadReturn);
    
    len = buffer.len;
    walk = (const unsigned char *) buffer.buf;
    
    while (len >= 4)
        {
        /* The following code works regardless of endianness. */
        d[0] = *walk++;
        d[1] = *walk++;
        d[2] = *walk++;
        d[3] = *walk++;
        checksum += ((d[0] << 24UL) + (d[1] << 16UL) + (d[2] << 8UL) + d[3]);
        len -= 4;
        }
    
    if (len)
        {
        d[1] = d[2] = d[3] = 0;  /* d[0] will be used if len > 0 */
        p = d;
        
        while (len--)
            *p++ = *walk++;
        
        checksum += ((d[0] << 24UL) + (d[1] << 16UL) + (d[2] << 8UL) + d[3]);
        }
    
    PyBuffer_Release(&buffer);
    retVal = Py_BuildValue("k", checksum & 0xFFFFFFFFUL);
    require(retVal, BadReturn);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    BadReturn:  return NULL;
    }  /* ut_Checksum */

/* --------------------------------------------------------------------------------------------- */

static PyObject *ut_Explode(PyObject *self, PyObject *args)
    {
    const unsigned char *s, *walk;
    int                 err, len;
    PyObject            *one, *retVal, *zero;
    Py_ssize_t          index;
    
    err = !PyArg_ParseTuple(args, "s#", (const char **) &s, &len);
    require_noerr(err, BadReturn);
    
    zero = PyLong_FromLong(0);
    require(zero, BadReturn);
    
    one = PyLong_FromLong(1);
    require(one, FreeZero);
    
    retVal = PyList_New(8 * len);
    require(retVal, FreeOne);
    
    walk = s;
    index = 0;
    
    while (len--)
        {
        unsigned char   c = *walk++;
        int             count = 8;
        
        while (count--)
            {
            if (c & 0x80U)
                {
                Py_INCREF(one);  /* because PyList_SET_ITEM steals a ref */
                PyList_SET_ITEM(retVal, index++, one);
                }
            else
                {
                Py_INCREF(zero);  /* because PyList_SET_ITEM steals a ref */
                PyList_SET_ITEM(retVal, index++, zero);
                }
            
            c = (unsigned char) ((c & 0x7F) << 1);
            }
        }
    
    Py_DECREF(one);
    Py_DECREF(zero);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeOne:        Py_DECREF(one);
    FreeZero:       Py_DECREF(zero);
    BadReturn:      return NULL;
    }  /* ut_Explode */

/* --------------------------------------------------------------------------------------------- */

static PyObject *ut_Implode(PyObject *self, PyObject *args)
    {
    unsigned char   *buf, c = 0, *walk;
    int             err;
    PyObject        *fastObj, *listObj, **members, *retVal;
    Py_ssize_t      bitCount = 0, len, retLen;
    
    err = !PyArg_ParseTuple(args, "O", &listObj);  /* a borrowed reference */
    require_noerr(err, BadReturn);
    Py_INCREF(listObj);  /* since we allocate mem, claim a reference */
    
    fastObj = PySequence_Fast(listObj, "Must pass a sequence to utImplode!\n");
    require(fastObj, FreeList);
    
    len = PySequence_Fast_GET_SIZE(fastObj);
    retLen = (len + 7) / 8;
    
    if (len)
        {
        members = PySequence_Fast_ITEMS(fastObj);
        require(members, FreeFast);
        
        walk = buf = (unsigned char *) PyMem_Malloc(retLen);
        require(buf, FreeFast);
        
        while (len--)
            {
            c <<= 1;
            
            if (PyObject_IsTrue(*members++))
                c |= 1;
            
            if (++bitCount == 8)
                {
                *walk++ = c;
                c = 0;
                bitCount = 0;
                }
            }
        
        if (bitCount)  /* we have a partial byte at the end */
            *walk = c << (8 - bitCount);
        
        retVal = PyBytes_FromStringAndSize((const char *) buf, retLen);
        require(retVal, FreeBuf);
        
        PyMem_Free(buf);
        }
    
    else
        {
        retVal = PyBytes_FromStringAndSize((const char *) &c, 0);
        require(retVal, FreeFast);
        }
    
    Py_DECREF(fastObj);
    Py_DECREF(listObj);
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeBuf:        PyMem_Free(buf);
    FreeFast:       Py_DECREF(fastObj);
    FreeList:       Py_DECREF(listObj);
    BadReturn:      return NULL;
    }  /* ut_Implode */

/* --------------------------------------------------------------------------------------------- */

static PyObject *ut_Pack(PyObject *self, PyObject *args)
    {
    char            *format, *formatWalk;
    int             err;
    Py_buffer       buffer;
    PyObject        *arg, *formatObj, *retVal;
    unsigned char   *buf, *walk;
    unsigned long   byteSize, itemCount;
    unsigned long   i = 1;
    
    formatObj = PySequence_GetItem(args, 0);
    require(formatObj, BadReturn);
    
    if (!PyObject_CheckBuffer(formatObj))
        /* If a regular string was passed in, we need to convert it to a bytes object first. */
        {
        PyObject    *asciiObj = PyUnicode_AsASCIIString(formatObj);
        
        require(asciiObj, FreeFormatObj);
        Py_CLEAR(formatObj);
        formatObj = asciiObj;
        }
    
    err = PyObject_GetBuffer(formatObj, &buffer, PyBUF_SIMPLE);
    require_noerr(err, FreeFormatObj);
    
    format = (char *) PyMem_Malloc(buffer.len + 1);
    require(format, FreeBufferObj);
    
    (void) memcpy(format, buffer.buf, buffer.len);
    format[buffer.len] = 0;
    
    byteSize = CalcSizeFromFormat(format, &itemCount);
    
    require_action(
        itemCount == PySequence_Length(args) - 1,
        FreeFormat,
        PyErr_SetString(
            PyExc_ValueError,
            "Number of arguments does not match format!"););
    
    formatWalk = format;
    walk = buf = (unsigned char *) PyMem_Malloc(byteSize);
    require(buf, FreeFormat);
    
    while (*formatWalk)
        {
        unsigned long   count, repeat;
        
        count = repeat = GetNextRepeat(&formatWalk);
        
        /* GetNextRepeat always leaves format pointing to a valid char */
        switch (*formatWalk++)
            {
            case 'B':
                while (count--)
                    {
                    long        n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLong(arg);
                    require_noerr(n == -1 && PyErr_Occurred(), FreeArg);
                    
                    require_action(
                        n >= 0 && n < 256,
                        FreeArg,
                        PyErr_SetString(
                            PyExc_ValueError,
                            "Format 'B' requires 0 <= n < 256!"););
                    
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'b':
                while (count--)
                    {
                    long        n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLong(arg);
                    require_noerr(n == -1 && PyErr_Occurred(), FreeArg);
                    
                    require_action(
                        n >= -128 && n < 128,
                        FreeArg,
                        PyErr_SetString(
                            PyExc_ValueError,
                            "Format 'b' requires -128 <= n < 128!"););
                    
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'c':
                while (count--)
                    {
                    char        *cString;
                    Py_ssize_t  cStringLen;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    require_action(
                      PyObject_CheckBuffer(arg),
                      FreeArg,
                      PyErr_SetString(
                        PyExc_ValueError,
                        "Format 'c' requires a bytes or bytearray object!"););
                    
                    /* If the object (which we now know supports the buffer
                       protocol) is not a bytes object, we now make it one. */
                    if (!PyBytes_Check(arg))
                        {
                        PyObject    *bytesObj = PyBytes_FromObject(arg);
                        
                        require(bytesObj, FreeArg);
                        Py_DECREF(arg);
                        arg = bytesObj;
                        }
                    
                    cString = PyBytes_AsString(arg);
                    require(cString, FreeArg);
                    cStringLen = strlen(cString);
                    
                    require_action(
                        cStringLen == 1,
                        FreeArg,
                        PyErr_SetString(
                            PyExc_ValueError,
                            "Format 'c' requires a string of length one!"););
                    
                    *walk++ = *cString;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'H':
                while (count--)
                    {
                    long        n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLong(arg);
                    require_noerr(n == -1 && PyErr_Occurred(), FreeArg);
                    
                    require_action(
                        n >= 0 && n < 65536,
                        FreeArg,
                        PyErr_SetString(
                            PyExc_ValueError,
                            "Format 'H' requires 0 <= n < 65536!"););
                    
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'h':
                while (count--)
                    {
                    long        n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLong(arg);
                    require_noerr(n == -1 && PyErr_Occurred(), FreeArg);
                    
                    require_action(
                        n >= -32768 && n < 32768,
                        FreeArg,
                        PyErr_SetString(
                            PyExc_ValueError,
                            "Format 'h' requires -32768 <= n < 32768!"););
                    
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'I':
            case 'L':
                while (count--)
                    {
                    unsigned long   n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsUnsignedLong(arg);
                    require_noerr(PyErr_Occurred(), FreeArg);
                    
                    *walk++ = (char) (n >> 24);
                    *walk++ = (char) (n >> 16);
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'i':
            case 'l':
                while (count--)
                    {
                    long    n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLong(arg);
                    require_noerr(PyErr_Occurred(), FreeArg);
                    
                    *walk++ = (char) (n >> 24);
                    *walk++ = (char) (n >> 16);
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'p':
                {
                char        *cString;
                Py_ssize_t  cStringLen, leftOvers;
                
                arg = PySequence_GetItem(args, i++);
                require(arg, FreeBuffer);
                
                require_action(
                  PyObject_CheckBuffer(arg),
                  FreeArg,
                  PyErr_SetString(
                    PyExc_ValueError,
                    "Format 'p' requires a bytes or bytearray object!"););
                
                /* If the object (which we now know supports the buffer
                   protocol) is not a bytes object, we now make it one. */
                if (!PyBytes_Check(arg))
                    {
                    PyObject    *bytesObj = PyBytes_FromObject(arg);
                    
                    require(bytesObj, FreeArg);
                    Py_DECREF(arg);
                    arg = bytesObj;
                    }
                
                cString = PyBytes_AsString(arg);
                require(cString, FreeArg);
                cStringLen = strlen(cString);
                
                if (cStringLen >= repeat)
                    cStringLen = repeat - 1;
                
                leftOvers = repeat - 1 - cStringLen;
                *walk++ = (char) (cStringLen > 255 ? 255 : cStringLen);
                
                while (cStringLen--)
                    *walk++ = *cString++;
                
                while (leftOvers--)
                    *walk++ = 0;
                
                Py_DECREF(arg);
                repeat = 1;
                }
                
                break;
            
            case 'Q':
                while (count--)
                    {
                    unsigned PY_LONG_LONG   n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsUnsignedLongLong(arg);
                    require_noerr(PyErr_Occurred(), FreeArg);
                    
                    *walk++ = (char) (n >> 56);
                    *walk++ = (char) (n >> 48);
                    *walk++ = (char) (n >> 40);
                    *walk++ = (char) (n >> 32);
                    *walk++ = (char) (n >> 24);
                    *walk++ = (char) (n >> 16);
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'q':
                while (count--)
                    {
                    PY_LONG_LONG    n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLongLong(arg);
                    require_noerr(PyErr_Occurred(), FreeArg);
                    
                    *walk++ = (char) (n >> 56);
                    *walk++ = (char) (n >> 48);
                    *walk++ = (char) (n >> 40);
                    *walk++ = (char) (n >> 32);
                    *walk++ = (char) (n >> 24);
                    *walk++ = (char) (n >> 16);
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 's':
                {
                char        *cString;
                Py_ssize_t  cStringLen, leftOvers = 0;
                
                arg = PySequence_GetItem(args, i++);
                require(arg, FreeBuffer);
                
                require_action(
                  PyObject_CheckBuffer(arg),
                  FreeArg,
                  PyErr_SetString(
                    PyExc_ValueError,
                    "Format 's' requires a bytes or bytearray object!"););
                
                /* If the object (which we now know supports the buffer
                   protocol) is not a bytes object, we now make it one. */
                if (!PyBytes_Check(arg))
                    {
                    PyObject    *bytesObj = PyBytes_FromObject(arg);
                    
                    require(bytesObj, FreeArg);
                    Py_DECREF(arg);
                    arg = bytesObj;
                    }
                
                cString = PyBytes_AsString(arg);
                require(cString, FreeArg);
                cStringLen = strlen(cString);
                
                if (cStringLen > repeat)
                    cStringLen = repeat;
                else if (cStringLen < repeat)
                    leftOvers = repeat - cStringLen;
                
                while (cStringLen--)
                    *walk++ = *cString++;
                
                while (leftOvers--)
                    *walk++ = 0;
                
                Py_DECREF(arg);
                repeat = 1;
                }
                
                break;
            
            case 'T':
                while (count--)
                    {
                    long        n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLong(arg);
                    require_noerr(n == -1 && PyErr_Occurred(), FreeArg);
                    
                    require_action(
                        n >= 0 && n < 16777216,
                        FreeArg,
                        PyErr_SetString(
                            PyExc_ValueError,
                            "Format 'T' requires 0 <= n < 16777216!"););
                    
                    *walk++ = (char) (n >> 16);
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 't':
                while (count--)
                    {
                    long        n;
                    
                    arg = PySequence_GetItem(args, i++);
                    require(arg, FreeBuffer);
                    
                    n = PyLong_AsLong(arg);
                    require_noerr(n == -1 && PyErr_Occurred(), FreeArg);
                    
                    require_action(
                        n >= -8388608 && n < 8388608,
                        FreeArg,
                        PyErr_SetString(
                            PyExc_ValueError,
                            "Format 't' requires -8388608 <= n < 8388608!"););
                    
                    *walk++ = (char) (n >> 16);
                    *walk++ = (char) (n >> 8);
                    *walk++ = (char) n;
                    Py_DECREF(arg);
                    }
                
                break;
            
            case 'x':
                while (count--)
                    *walk++ = 0;
                
                repeat = 0;
                break;
            
            default:
                require_action(
                    0,
                    FreeBuffer,
                    PyErr_SetString(
                        PyExc_ValueError,
                        "Unsupported format specification!"););
                
                break;  /* error check here? */
            }
        
        itemCount -= repeat;
        }
    
    retVal = PyBytes_FromStringAndSize((const char *) buf, byteSize);
    require(retVal, FreeBuffer);
    
    PyMem_Free(buf);
    PyMem_Free(format);
    PyBuffer_Release(&buffer);
    Py_DECREF(formatObj);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    FreeArg:        Py_DECREF(arg);
    FreeBuffer:     PyMem_Free(buf);
    FreeFormat:     PyMem_Free(format);
    FreeBufferObj:  PyBuffer_Release(&buffer);
    FreeFormatObj:  Py_DECREF(formatObj);
    BadReturn:      return NULL;
    }  /* ut_Pack */

/* --------------------------------------------------------------------------------------------- */

/*** MODULE CREATION ***/

static struct PyModuleDef utilitiesmodule =
    {
    PyModuleDef_HEAD_INIT,
    "utilitiesbackend",
    NULL,   /* module doc string */
    -1,
    UtilitiesMethods
    };

PyMODINIT_FUNC PyInit_utilitiesbackend(void)
    {
    return PyModule_Create(&utilitiesmodule);
    }  /* PyInit_utilitiesbackend */

/* --------------------------------------------------------------------------------------------- */

/*** TEST CODE ***/

// int main(int argc, char *argv[])
//     {
//     PyObject    *args, *ret, *self;
//     
//     Py_Initialize();
//     self = Py_BuildValue("");
//     args = Py_BuildValue("sf", "f", 3.5);
//     ret = ut_Pack(self, args);
//     Py_DECREF(ret);
//     Py_DECREF(args);
//     Py_DECREF(self);
//     Py_Finalize();
//     return 0;
//     }
