/*
 * fastmath.c -- Implementation of fast mathematical utilities.
 *
 * Copyright (c) 2016 Monotype Imaging Inc. All Rights Reserved.
 *
 */

#include <Python.h>
#include <math.h>
#include "AssertMacros.h"

/* ------------------------------------------------------------------------ */

/*** MACROS ***/

/* AE is "almost equal" */
#define AE(v1,v2) (fabs(v2-v1) < 1.0e-5)

/* ------------------------------------------------------------------------ */

/*** TYPES ***/

struct FMSegment
    {
    double  isSpline;
    double  on1X;
    double  on1Y;
    double  offX;
    double  offY;
    double  on2X;
    double  on2Y;
    double  yMin;
    double  yMax;
    };

#ifndef __cplusplus
typedef struct FMSegment FMSegment;
#endif

/* ------------------------------------------------------------------------ */

/*** PROTOTYPES ***/

static int FindSect(double y, FMSegment *walk, Py_ssize_t segCount, double *x1, double *x2);
static void FindYExtrema(FMSegment *walk, Py_ssize_t segCount, double *yMax, double *yMin);
static FMSegment *MakeCSegments(PyObject *segments, Py_ssize_t segCount);

static PyObject *fm_FindLRExtrema(PyObject *self, PyObject *args);

/* ------------------------------------------------------------------------ */

/*** STATIC GLOBALS ***/

static PyMethodDef UtilitiesMethods[] = {
    {"fmFindLRExtrema", fm_FindLRExtrema, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

/* ------------------------------------------------------------------------ */

/*** PRIVATE PROCEDURES ***/

static int FindSect(double y, FMSegment *walk, Py_ssize_t segCount, double *x1, double *x2)
    {
    double  xMin = 100000.0;
    double  xMax = -100000.0;
    int     found = 0;
    
    while (segCount--)
        {
        if (y <= walk->yMax && y >= walk->yMin)
            {
            if (walk->isSpline)
                {
                double  a = walk->on1Y + walk->on2Y - 2.0 * walk->offY;
                double  b = 2.0 * (walk->offY - walk->on1Y);
                double  c = walk->on1Y - y;
                
                if (a)
                    {  /* full quadratic equation */
                    double  det = b * b - 4.0 * a * c;
                    
                    if (AE(det, 0.0))
                        det = 0.0;
                    
                    if (det >= 0.0)
                        {
                        float   t1, t2;
                        
                        det = sqrt(det);
                        t1 = (-b + det) / (2.0 * a);
                        t2 = (-b - det) / (2.0 * a);
                        
                        if (AE(t1, 0.0))
                            t1 = 0.0;
                        else if (AE(t1, 1.0))
                            t1 = 1.0;
                        
                        if (AE(t2, 0.0))
                            t2 = 0.0;
                        else if (AE(t2, 1.0))
                            t2 = 1.0;
                        
                        if (t1 >= 0.0 && t1 <= 1.0)
                            {
                            double  x = (1.0 - t1) * walk->on1X + t1 * walk->on2X;
                            
                            xMin = fmin(x, xMin);
                            xMax = fmax(x, xMax);
                            found = 1;
                            }
                        
                        if (t2 >= 0.0 && t2 <= 1.0)
                            {
                            double  x = (1.0 - t2) * walk->on1X + t2 * walk->on2X;
                            
                            xMin = fmin(x, xMin);
                            xMax = fmax(x, xMax);
                            found = 1;
                            }
                        }
                    }
                
                else
                    {  /* bt + c = 0 */
                    if (b)
                        {
                        double  t = -c / b;
                        double  x = (1.0 - t) * walk->on1X + t * walk->on2X;
                        
                        xMin = fmin(x, xMin);
                        xMax = fmax(x, xMax);
                        found = 1;
                        }
                    
                    else if (AE(y, 0.0))
                        {  /* lines coincide */
                        xMin = fmin(xMin, fmin(walk->on1X, walk->on2X));
                        xMax = fmax(xMax, fmax(walk->on1X, walk->on2X));
                        found = 1;
                        }
                    }
                }
        
            else
                {
                found = 1;
                
                if (AE(walk->yMax, walk->yMin))
                    {  /* horizontal line at y */
                    xMin = fmin(xMin, fmin(walk->on1X, walk->on2X));
                    xMax = fmax(xMax, fmax(walk->on1X, walk->on2X));
                    }
                
                else if (AE(walk->on1X, walk->on2X))
                    {  /* vertical line */
                    xMin = fmin(xMin, walk->on1X);
                    xMax = fmax(xMax, walk->on1X);
                    }
                
                else
                    {  /* non-horizontal line intersecting y */
                    double  t = (y - walk->on1Y) / (walk->on2Y - walk->on1Y);
                    double  x = (1.0 - t) * walk->on1X + t * walk->on2X;
                    
                    xMin = fmin(x, xMin);
                    xMax = fmax(x, xMax);
                    }
                }
            }
        
        walk += 1;
        }
    
    *x1 = xMin;
    *x2 = xMax;
    return found;
    }  /* FindSect */

static void FindYExtrema(FMSegment *walk, Py_ssize_t segCount, double *yMax, double *yMin)
    {
    double  lo = 100000.0;
    double  hi = -100000.0;
    
    while (segCount--)
        {
        if (walk->yMax > hi)
            hi = walk->yMax;
        if (walk->yMin < lo)
            lo = walk->yMin;
        
        walk += 1;
        }
    
    *yMax = hi;
    *yMin = lo;
    }  /* FindYExtrema */

static FMSegment *MakeCSegments(PyObject *segments, Py_ssize_t segCount)
    {
    FMSegment   *retVal, *walk;
    Py_ssize_t  i;
    PyObject    *n, *seg;
    
    retVal = walk = PyMem_Calloc(segCount, sizeof(FMSegment));
    require_action(retVal != NULL, Err_BadReturn, PyErr_NoMemory(););
    
    for (i = 0; i < segCount; i += 1)
        {
        double  d;
        int     isSpline;
        
        seg = PySequence_GetItem(segments, i);
        require(seg != NULL, Err_FreeRetval);
        
        n = PySequence_GetItem(seg, 0);
        require(n != NULL, Err_FreeSeg);
        d = PyFloat_AsDouble(n);
        require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
        isSpline = d;
        Py_DECREF(n);
        
        if (isSpline)
            {
            walk->isSpline = 1.0;
            
            n = PySequence_GetItem(seg, 1);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on1X = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 2);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on1Y = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 3);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->offX = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 4);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->offY = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 5);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on2X = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 6);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on2Y = d;
            Py_DECREF(n);
            
            walk->yMin = fmin(walk->on1Y, fmin(walk->offY, walk->on2Y));
            walk->yMax = fmax(walk->on1Y, fmax(walk->offY, walk->on2Y));
            }
        
        else
            {
            walk->isSpline = 0.0;
            
            n = PySequence_GetItem(seg, 1);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on1X = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 2);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on1Y = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 3);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on2X = d;
            Py_DECREF(n);
            
            n = PySequence_GetItem(seg, 4);
            require(n != NULL, Err_FreeSeg);
            d = PyFloat_AsDouble(n);
            require(d != -1.0 || PyErr_Occurred() == NULL, Err_FreeN);
            walk->on2Y = d;
            Py_DECREF(n);
            
            walk->yMin = fmin(walk->on1Y, walk->on2Y);
            walk->yMax = fmax(walk->on1Y, walk->on2Y);
            }
        
        Py_DECREF(seg);
        walk += 1;
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeN:          Py_DECREF(n);
    Err_FreeSeg:        Py_DECREF(seg);
    Err_FreeRetval:     PyMem_Free(retVal);
    Err_BadReturn:      return NULL;
    }  /* MakeCSegments */

/* ------------------------------------------------------------------------ */

/*** INTERFACE PROCEDURES ***/

static PyObject *fm_FindLRExtrema(PyObject *self, PyObject *args)
    {
    double      y, yMax, yMin;
    FMSegment   *cSegments;
    Py_ssize_t  segCount;
    PyObject    *key, *ptX1, *ptX2, *retVal, *segments, *value;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &segments),
      Err_BadReturn);
    
    Py_INCREF(segments);  /* turn borrowed ref into regular one */
    segCount = PySequence_Length(segments);
    require(segCount != -1, Err_FreeInputs);
    cSegments = MakeCSegments(segments, segCount);
    require(cSegments != NULL, Err_FreeInputs);
    FindYExtrema(cSegments, segCount, &yMax, &yMin);
    retVal = PyDict_New();
    require(retVal != NULL, Err_FreeSegs);
    
    for (y = yMin; y <= yMax; y += 1.0)
        {
        double  x1, x2;
        int     found;
        
        found = FindSect(y, cSegments, segCount, &x1, &x2);
        
        if (found)
            {  /* add entry to dict */
            key = PyLong_FromSsize_t((Py_ssize_t) y);
            require(key, Err_FreeRetVal);
            ptX1 = PyFloat_FromDouble(x1);
            require(ptX1, Err_FreeKey);
            ptX2 = PyFloat_FromDouble(x2);
            require(ptX2, Err_FreeX1);
            value = Py_BuildValue("(OO)", ptX1, ptX2);
            require(value, Err_FreeX2);
            require_noerr(PyDict_SetItem(retVal, key, value), Err_FreeValue);
            Py_DECREF(value);
            Py_DECREF(ptX2);
            Py_DECREF(ptX1);
            Py_DECREF(key);
            }
        }
    
    PyMem_Free(cSegments);
    Py_DECREF(segments);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeValue:      Py_DECREF(value);
    Err_FreeX2:         Py_DECREF(ptX2);
    Err_FreeX1:         Py_DECREF(ptX1);
    Err_FreeKey:        Py_DECREF(key);
    Err_FreeRetVal:     Py_DECREF(retVal);
    Err_FreeSegs:       PyMem_Free(cSegments);
    Err_FreeInputs:     Py_DECREF(segments);
    Err_BadReturn:      return NULL;
    }   /* fm_FindLRExtrema */

/* ------------------------------------------------------------------------ */

/*** MODULE CREATION ***/

static struct PyModuleDef fastmathmodule =
    {
    PyModuleDef_HEAD_INIT,
    "fastmathbackend",
    NULL,   /* module doc string */
    -1,
    UtilitiesMethods
    };

PyMODINIT_FUNC PyInit_fastmathbackend(void)
    {
    return PyModule_Create(&fastmathmodule);
    }  /* PyInit_fastmathbackend */
