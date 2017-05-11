/*
 * cspan.c -- Implementation of superfast Spans
 *
 * Copyright (c) 2014 Monotype Imaging Inc. All Rights Reserved.
 *
 */

#include <Python.h>
#include "AssertMacros.h"
#include <stdio.h>
#include <stdlib.h>

/* ------------------------------------------------------------------------- */

/*** CONSTANTS ***/

#define SUL sizeof(unsigned long)
#define OPEN_ENDED (1L << (8L * SUL - 1L))
#define DO_INTERNAL_DEBUG 0

/* ------------------------------------------------------------------------- */

/*** TYPES ***/

struct CSpan_Group
    {
    long    first;
    long    last;
    };

#ifndef __cplusplus
typedef struct CSpan_Group CSpan_Group;
#endif

struct CSpan_Context
    {
    unsigned long   numGroups;
    unsigned long   numAlloc;
    CSpan_Group     *groups;
    };

#ifndef __cplusplus
typedef struct CSpan_Context CSpan_Context;
#endif

/* ------------------------------------------------------------------------- */

/*** PROTOTYPES ***/

static CSpan_Context *Canonicalize(PyObject *tuples, int normalize);
static CSpan_Context *Canonicalize_Singles(PyObject *tuples, int normalize);
static void CapsuleDestructor(PyObject *capsule);
static CSpan_Context *CopyContext(CSpan_Context *context);
static int CSGSort(const void *a, const void *b);
static void DebugPrint(CSpan_Context *context);
static PyObject *GroupTuple(CSpan_Group *group);
static int IsFull(CSpan_Context *context);
static CSpan_Context *MakeClosedContext(CSpan_Context *context, unsigned long count);
static CSpan_Context *MakeEmpty(void);
static CSpan_Context *MakeFull(void);
static CSpan_Context *MakeIntersection(CSpan_Context *context1, CSpan_Context *context2);
static CSpan_Context *MakeInverse(CSpan_Context *context);
static CSpan_Context *MakeUnion(CSpan_Context *context1, CSpan_Context *context2);
static int Normalize(CSpan_Context *context);
static int PairIntersect(CSpan_Group *g1, CSpan_Group *g2, CSpan_Group *out);
static int PairToLongs(PyObject *pair, long *thisFirst, long *thisLast);

static PyObject *cspan_AddedFromPairs(PyObject *self, PyObject *args);
static PyObject *cspan_AddedFromSingles(PyObject *self, PyObject *args);
static PyObject *cspan_AsTuple(PyObject *self, PyObject *args);
static PyObject *cspan_Bool(PyObject *self, PyObject *args);
static PyObject *cspan_ContainsValue(PyObject *self, PyObject *args);
static PyObject *cspan_Count(PyObject *self, PyObject *args);
static PyObject *cspan_DebugPrint(PyObject *self, PyObject *args);
static PyObject *cspan_Equal(PyObject *self, PyObject *args);
static PyObject *cspan_Intersected(PyObject *self, PyObject *args);
static PyObject *cspan_Inverted(PyObject *self, PyObject *args);
static PyObject *cspan_IsFull(PyObject *self, PyObject *args);
static PyObject *cspan_NewContext(PyObject *self, PyObject *args);
static PyObject *cspan_Unioned(PyObject *self, PyObject *args);

/* ------------------------------------------------------------------------- */

/*** STATIC GLOBALS ***/

static PyMethodDef CSpanMethods[] = {
    {"cspanAddedFromPairs", cspan_AddedFromPairs, METH_VARARGS, NULL},
    {"cspanAddedFromSingles", cspan_AddedFromSingles, METH_VARARGS, NULL},
    {"cspanAsTuple", cspan_AsTuple, METH_VARARGS, NULL},
    {"cspanBool", cspan_Bool, METH_VARARGS, NULL},
    {"cspanContainsValue", cspan_ContainsValue, METH_VARARGS, NULL},
    {"cspanCount", cspan_Count, METH_VARARGS, NULL},
    {"cspanDebugPrint", cspan_DebugPrint, METH_VARARGS, NULL},
    {"cspanEqual", cspan_Equal, METH_VARARGS, NULL},
    {"cspanIntersected", cspan_Intersected, METH_VARARGS, NULL},
    {"cspanInverted", cspan_Inverted, METH_VARARGS, NULL},
    {"cspanIsFull", cspan_IsFull, METH_VARARGS, NULL},
    {"cspanNewContext", cspan_NewContext, METH_VARARGS, NULL},
    {"cspanUnioned", cspan_Unioned, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

/* ------------------------------------------------------------------------- */

/*** INTERNAL PROCEDURES ***/

#if 0
static void ______________(void){}
#endif

static CSpan_Context *Canonicalize(PyObject *tuples, int normalize)
    {
    CSpan_Context   *retVal;
    Py_ssize_t      i, inputLength;
    PyObject        *fast, *pair;
    
    /*
        The input argument, tuples, is a sequence -- the high-end Python code
        will convert an iterator into a tuple -- of (first, last) pairs. Either
        first, or last, or both of them may be None, in zero or more pairs.
    */
    
    fast = PySequence_Fast(tuples, "Unable to process input sequence!");
    require(fast, Err_BadReturn);
    
    inputLength = PySequence_Fast_GET_SIZE(fast);
    require(inputLength != -1, Err_FreeFast);
    
    if (inputLength)
        {
        retVal = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
        require(retVal, Err_FreeFast);
        
        retVal->groups = (CSpan_Group *) PyMem_Malloc(inputLength * sizeof(CSpan_Group));
        require(retVal->groups, Err_FreeContext);
    
        retVal->numGroups = (unsigned long) inputLength;
        retVal->numAlloc = (unsigned long) inputLength;
        }
    
    else
        {
        retVal = MakeEmpty();
        require(retVal, Err_FreeFast);
        }
    
    for (i = 0; i < inputLength; i += 1)
        {
        CSpan_Group     *g = retVal->groups + i;
        
        pair = PySequence_Fast_GET_ITEM(fast, i);
        require(pair, Err_FreeGroups);
        Py_INCREF(pair);
        require_noerr(PairToLongs(pair, &g->first, &g->last), Err_FreePair);
        Py_DECREF(pair);
        }
    
    if (normalize)
        {
        require_noerr(Normalize(retVal), Err_FreeGroups);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreePair:       Py_DECREF(pair);
    Err_FreeGroups:     PyMem_Free(retVal->groups);
    Err_FreeContext:    PyMem_Free(retVal);
    Err_FreeFast:       Py_DECREF(fast);
    Err_BadReturn:      return NULL;
    }   /* Canonicalize */

static CSpan_Context *Canonicalize_Singles(PyObject *ints, int normalize)
    {
    CSpan_Context   *retVal;
    Py_ssize_t      i, inputLength;
    PyObject        *fast, *intObj;
    
    /*
        The input argument, ints, is a sequence -- the high-end Python code
        will convert an iterator into a tuple -- of integers.
    */
    
    fast = PySequence_Fast(ints, "Unable to process input sequence!");
    require(fast, Err_BadReturn);
    
    inputLength = PySequence_Fast_GET_SIZE(fast);
    require(inputLength != -1, Err_FreeFast);
    
    if (inputLength)
        {
        retVal = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
        require(retVal, Err_FreeFast);
        
        retVal->groups = (CSpan_Group *) PyMem_Malloc(inputLength * sizeof(CSpan_Group));
        require(retVal->groups, Err_FreeContext);
    
        retVal->numGroups = (unsigned long) inputLength;
        retVal->numAlloc = (unsigned long) inputLength;
        }
    
    else
        {
        retVal = MakeEmpty();
        require(retVal, Err_FreeFast);
        }
    
    for (i = 0; i < inputLength; i += 1)
        {
        CSpan_Group     *g = retVal->groups + i;
        long            n;
        
        intObj = PySequence_Fast_GET_ITEM(fast, i);
        require(intObj, Err_FreeGroups);
        Py_INCREF(intObj);
        n = PyLong_AsLong(intObj);
        require_noerr(PyErr_Occurred(), Err_FreeIntObj);
        g->first = g->last = n;
        Py_DECREF(intObj);
        }
    
    if (normalize)
        {
        require_noerr(Normalize(retVal), Err_FreeGroups);
        }
    
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeIntObj:     Py_DECREF(intObj);
    Err_FreeGroups:     PyMem_Free(retVal->groups);
    Err_FreeContext:    PyMem_Free(retVal);
    Err_FreeFast:       Py_DECREF(fast);
    Err_BadReturn:      return NULL;
    }   /* Canonicalize_Singles */

static void CapsuleDestructor(PyObject *capsule)
    {
    CSpan_Context *context = PyCapsule_GetPointer(capsule, "cspan_capsule");
    
    if (context)
        {
        if (context->groups)
            {
            PyMem_Free(context->groups);
            }
        
        PyMem_Free(context);
        }
    }   /* CapsuleDestructor */

static CSpan_Context *CopyContext(CSpan_Context *context)
    {
    CSpan_Context   *r;
    CSpan_Group     *from, *to;
    unsigned long   count;
    
    r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
    require(r, Err_BadReturn);
    count = context->numGroups;
    r->groups = (CSpan_Group *) PyMem_Malloc(count * sizeof(CSpan_Group));
    require(r->groups, Err_FreeR);
    r->numGroups = r->numAlloc = count;
    to = r->groups;
    from = context->groups;
    
    while (count--)
        *to++ = *from++;
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeR:          PyMem_Free(r);
    Err_BadReturn:      return NULL;
    }   /* CopyContext */

static int CSGSort(const void *a, const void *b)
    {
    const CSpan_Group   *x = a, *y = b;
    
    if (x->first < y->first)
        return -1;
    
    if (x->first > y->first)
        return 1;
    
    if (x->last < y->last)
        return -1;
    
    if (x->last > y->last)
        return 1;
    
    return 0;
    }   /* CSGSort */

static void DebugPrint(CSpan_Context *context)
    {
    printf("numAlloc is %lu\n", context->numAlloc);
    printf("numGroups is %lu\n", context->numGroups);
    
    if (context->numGroups)
        {
        CSpan_Group     *walk = context->groups;
        unsigned long   count = context->numGroups;
        
        while (count--)
            {
            if (walk->first == OPEN_ENDED && walk->last == OPEN_ENDED)
                printf("(None, None)\n");
            
            else if (walk->first == OPEN_ENDED)
                printf("(None, %ld)\n", walk->last);
            
            else if (walk->last == OPEN_ENDED)
                printf("(%ld, None)\n", walk->first);
            
            else
                printf("(%ld, %ld)\n", walk->first, walk->last);
            
            walk += 1;
            }
        }
    }   /* DebugPrint */

static PyObject *GroupTuple(CSpan_Group *group)
    {
    PyObject    *r;
    
    if (group->first == OPEN_ENDED && group->last == OPEN_ENDED)
        r = Py_BuildValue("(OO)", Py_None, Py_None);
    
    else if (group->first == OPEN_ENDED)
        r = Py_BuildValue("(Ol)", Py_None, group->last);
    
    else if (group->last == OPEN_ENDED)
        r = Py_BuildValue("(lO)", group->first, Py_None);
    
    else
        r = Py_BuildValue("(ll)", group->first, group->last);
    
    require(r, Err_BadReturn);
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return NULL;
    }   /* GroupTuple */

static int IsFull(CSpan_Context *context)
    {
    CSpan_Group     *base;
    
    if (context->numGroups != 1UL)
        return 0;
    
    base = context->groups;
    return ((base->first == OPEN_ENDED) && (base->last == OPEN_ENDED));
    }   /* IsFull */

static CSpan_Context *MakeClosedContext(CSpan_Context *context, unsigned long count)
    {
    CSpan_Context   *r;
    CSpan_Group     *baseOld, *limitOld, *walkNew, *walkOld;
    
    r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
    require(r, Err_BadReturn);
    r->groups = (CSpan_Group *) PyMem_Malloc(count * sizeof(CSpan_Group));
    require(r->groups, Err_FreeR);
    r->numAlloc = r->numGroups = count;
    
    baseOld = context->groups;
    limitOld = baseOld + context->numGroups;
    walkOld = baseOld - 1;
    walkNew = r->groups;
    
    // Copy the closed pairs to the new context
    
    while (++walkOld != limitOld)
        {
        if (walkOld->first != OPEN_ENDED && walkOld->last != OPEN_ENDED)
            *walkNew++ = *walkOld;
        }
    
    if (count == 1UL)
        return r;
    
    // Sort the new context
    
    qsort(r->groups, (size_t) count, sizeof(CSpan_Group), CSGSort);

    // Combine adjacents
    
        {
        CSpan_Group *from = r->groups;
        CSpan_Group *to = r->groups;
        CSpan_Group *limit = r->groups + r->numGroups;
        CSpan_Group *next;
    
        while (from < limit)
            {
            if (from != to)
                *to = *from;
        
            next = from + 1;
        
            while ((next < limit) && (next->first <= (to->last + 1L)))
                {
                if (next->last > to->last)
                    to->last = next->last;
            
                next += 1;
                }
        
            from = next;
            to += 1;
            }
    
        r->numGroups = to - r->groups;
        }
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeR:          PyMem_Free(r);
    Err_BadReturn:      return NULL;
    }   /* MakeClosedContext */

static CSpan_Context *MakeEmpty(void)
    {
    CSpan_Context   *r;
    
    r = PyMem_Malloc(sizeof(CSpan_Context));
    require(r, Err_BadReturn);
    r->groups = PyMem_Malloc(sizeof(CSpan_Group));
    require(r->groups, Err_FreeR);
    r->numGroups = 0UL;
    r->numAlloc = 1UL;
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeR:          PyMem_Free(r);
    Err_BadReturn:      return NULL;
    }   /* MakeEmpty */

static CSpan_Context *MakeFull(void)
    {
    CSpan_Context   *r;
    
    r = PyMem_Malloc(sizeof(CSpan_Context));
    require(r, Err_BadReturn);
    r->groups = PyMem_Malloc(sizeof(CSpan_Group));
    require(r->groups, Err_FreeR);
    r->numGroups = r->numAlloc = 1UL;
    r->groups->first = r->groups->last = OPEN_ENDED;
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeR:          PyMem_Free(r);
    Err_BadReturn:      return NULL;
    }   /* MakeFull */

static CSpan_Context *MakeIntersection(CSpan_Context *context1, CSpan_Context *context2)
    {
    CSpan_Context   *r;
    CSpan_Group     *out;
    CSpan_Group     *walk1 = context1->groups;
    CSpan_Group     *walk2 = context2->groups;
    unsigned long   count1 = context1->numGroups;
    unsigned long   count2 = context2->numGroups;
    unsigned long   fullCount = count1 * count2;
    
    r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
    require(r, Err_BadReturn);
    r->groups = (CSpan_Group *) PyMem_Malloc(fullCount * sizeof(CSpan_Group));
    require(r->groups, Err_FreeR);
    r->numGroups = 0UL;
    r->numAlloc = fullCount;
    out = r->groups;
    
    while (count1--)
        {
        while (count2--)
            {
            CSpan_Group     sect;
            int             ok = PairIntersect(walk1, walk2++, &sect);
            
            if (ok)
                *out++ = sect;
            }
        
        walk1 += 1;
        count2 = context2->numGroups;
        walk2 = context2->groups;
        }
    
    fullCount = out - r->groups;
    r->numGroups = fullCount;
    r->numAlloc = (fullCount ? fullCount : 1UL);
    out = PyMem_Realloc(r->groups, r->numAlloc * sizeof(CSpan_Group));
    require(out, Err_FreeGroups);
    r->groups = out;
    require_noerr(Normalize(r), Err_FreeGroups);
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeGroups:     PyMem_Free(r->groups);
    Err_FreeR:          PyMem_Free(r);
    Err_BadReturn:      return NULL;
    }   /* MakeIntersection */

static CSpan_Context *MakeInverse(CSpan_Context *context)
    {
    CSpan_Context   *r;
    CSpan_Group     *base, *last, *limit, *walkLeft, *walkRight, *walkOut;
    unsigned long   count;
    
    // we know context is neither full nor empty, and numGroups >= 1
    
    base = context->groups;
    limit = base + context->numGroups;
    last = limit - 1;
    
    if (base->first == OPEN_ENDED && last->last == OPEN_ENDED)
        {
        count = context->numGroups - 1UL;
        r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
        require(r, Err_BadReturn);
        r->groups = (CSpan_Group *) PyMem_Malloc(count * sizeof(CSpan_Group));
        require(r->groups, Err_FreeR);
        r->numGroups = r->numAlloc = count;
        walkLeft = base;
        walkRight = base + 1;
        walkOut = r->groups;
        
        while (count--)
            {
            walkOut->first = (walkLeft++)->last + 1UL;
            (walkOut++)->last = (walkRight++)->first - 1UL;
            }
        }
    
    else if (base->first == OPEN_ENDED)
        {
        count = context->numGroups;
        r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
        require(r, Err_BadReturn);
        r->groups = (CSpan_Group *) PyMem_Malloc(count * sizeof(CSpan_Group));
        require(r->groups, Err_FreeR);
        r->numGroups = r->numAlloc = count;
        walkLeft = base;
        walkRight = base + 1;
        walkOut = r->groups;
        
        while (--count)  // yes, pre-decrement (treats count as count-1)
            {
            walkOut->first = (walkLeft++)->last + 1UL;
            (walkOut++)->last = (walkRight++)->first - 1UL;
            }
        
        walkOut->first = last->last + 1UL;
        walkOut->last = OPEN_ENDED;
        }
    
    else if (last->last == OPEN_ENDED)
        {
        count = context->numGroups;
        r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
        require(r, Err_BadReturn);
        r->groups = (CSpan_Group *) PyMem_Malloc(count * sizeof(CSpan_Group));
        require(r->groups, Err_FreeR);
        r->numGroups = r->numAlloc = count;
        walkOut = r->groups;
        walkOut->first = OPEN_ENDED;
        (walkOut++)->last = base->first - 1UL;
        walkLeft = base;
        walkRight = base + 1;
        
        while (--count)  // yes, pre-decrement (treats count as count-1)
            {
            walkOut->first = (walkLeft++)->last + 1UL;
            (walkOut++)->last = (walkRight++)->first - 1UL;
            }
        }
    
    else
        {
        count = context->numGroups + 1UL;
        r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
        require(r, Err_BadReturn);
        r->groups = (CSpan_Group *) PyMem_Malloc(count * sizeof(CSpan_Group));
        require(r->groups, Err_FreeR);
        r->numGroups = r->numAlloc = count;
        walkOut = r->groups;
        walkOut->first = OPEN_ENDED;
        (walkOut++)->last = base->first - 1UL;
        walkLeft = base;
        walkRight = base + 1;
        count -= 2UL;
        
        while (count--)
            {
            walkOut->first = (walkLeft++)->last + 1UL;
            (walkOut++)->last = (walkRight++)->first - 1UL;
            }
        
        walkOut->first = last->last + 1UL;
        walkOut->last = OPEN_ENDED;
        }
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeR:          PyMem_Free(r);
    Err_BadReturn:      return NULL;
    }   /* MakeInverse */

static CSpan_Context *MakeUnion(CSpan_Context *context1, CSpan_Context *context2)
    {
    CSpan_Context   *r;
    
    if (IsFull(context1) || IsFull(context2))
        {
        r = MakeFull();
        require(r, Err_BadReturn);
        }
    
    else if (!context1->numGroups)
        {
        r = CopyContext(context2);
        require(r, Err_BadReturn);
        }
    
    else if (!context2->numGroups)
        {
        r = CopyContext(context1);
        require(r, Err_BadReturn);
        }
    
    else
        {
        CSpan_Group     *from, *to;
        unsigned long   count, n;
        
        count = context1->numGroups + context2->numGroups;
        r = (CSpan_Context *) PyMem_Malloc(sizeof(CSpan_Context));
        require(r, Err_BadReturn);
        r->groups = (CSpan_Group *) PyMem_Malloc(count * sizeof(CSpan_Group));
        require(r->groups, Err_FreeR);
        r->numGroups = r->numAlloc = count;
        to = r->groups;
        from = context1->groups;
        n = context1->numGroups;
    
        while (n--)
            *to++ = *from++;
    
        from = context2->groups;
        n = context2->numGroups;
    
        while (n--)
            *to++ = *from++;

        require_noerr(Normalize(r), Err_FreeGroups);
        }
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeGroups:     PyMem_Free(r->groups);
    Err_FreeR:          PyMem_Free(r);
    Err_BadReturn:      return NULL;
    }   /* MakeUnion */

static int Normalize(CSpan_Context *context)
    {
    CSpan_Context   *closedContext;
    CSpan_Group     *base, *firstToMove, *last, *lastToMove, *limit, *walk, *walkRet;
    unsigned long   closedCount, leftFence, rightFence;
    
    if (!context->numGroups)
        return 0;
    
    base = context->groups;
    limit = base + context->numGroups;
    last = limit - 1;
    leftFence = rightFence = OPEN_ENDED;  // using it like "None" here...
    closedCount = 0UL;  // number of non-open pairs
    
    // Determine the fences, and the closedCount
    
    for (walk = base; walk != limit; walk += 1)
        {
        if (walk->first == OPEN_ENDED)
            {
            if (walk->last == OPEN_ENDED)
                {
                context->numGroups = 1UL;
                base->first = base->last = OPEN_ENDED;
                return 0;
                }
            
            else if (leftFence == OPEN_ENDED)
                {
                leftFence = walk->last;
                }
            
            else if (walk->last > leftFence)
                {
                leftFence = walk->last;
                }
            }
        
        else if (walk->last == OPEN_ENDED)
            {
            if (rightFence == OPEN_ENDED)
                {
                rightFence = walk->first;
                }
            
            else if (walk->first < rightFence)
                {
                rightFence = walk->first;
                }
            }
        
        else
            {
            closedCount += 1UL;
            }
        }
    
    // If fences overlap, set context as (*, *)
    
    if (leftFence != OPEN_ENDED && rightFence != OPEN_ENDED && leftFence >= (rightFence - 1))
        {
        context->numGroups = 1UL;
        base->first = base->last = OPEN_ENDED;
        return 0;
        }
    
    // Process the closed pairs
    
    firstToMove = NULL;
    lastToMove = NULL;
    
    if (closedCount)
        {
        closedContext = MakeClosedContext(context, closedCount);
        require(closedContext, Err_BadReturn);
        firstToMove = closedContext->groups;
        lastToMove = closedContext->groups + (closedContext->numGroups - 1);
        
        // Stretch the fences, if possible
        
        if (leftFence != OPEN_ENDED)
            {
            walk = closedContext->groups;
            limit = walk + closedContext->numGroups;
            
            while ((walk < limit) && (walk->first <= (leftFence + 1UL)))
                {
                if (walk->last > leftFence)
                    leftFence = walk->last;
                
                walk += 1;
                }
            
            firstToMove = walk;
            }
        
        if (rightFence != OPEN_ENDED)
            {
            walk = closedContext->groups + (closedContext->numGroups - 1);
            limit = closedContext->groups - 1;
            
            while ((walk > limit) && (walk->last >= (rightFence - 1UL)))
                {
                if (walk->first < rightFence)
                    rightFence = walk->first;
                
                walk -= 1;
                }
            
            lastToMove = walk;
            }
        }
    
    // Since fences may have moved, do another overlap check
    
    if (leftFence != OPEN_ENDED && rightFence != OPEN_ENDED && leftFence >= (rightFence - 1))
        {
        context->numGroups = 1UL;
        base->first = base->last = OPEN_ENDED;
        
        if (closedCount)
            {
            PyMem_Free(closedContext->groups);
            PyMem_Free(closedContext);
            }
        
        return 0;
        }
    
    // Put the final data back into context
    
    walkRet = context->groups;
    context->numGroups = 0UL;
    
    if (leftFence != OPEN_ENDED)
        {
        walkRet->first = OPEN_ENDED;
        walkRet->last = leftFence;
        walkRet += 1;
        }
    
    if (firstToMove != NULL && lastToMove != NULL && lastToMove >= firstToMove)
        {
        while (firstToMove <= lastToMove)
            {
            *walkRet++ = *firstToMove++;
            }
        }
    
    if (rightFence != OPEN_ENDED)
        {
        walkRet->first = rightFence;
        walkRet->last = OPEN_ENDED;
        walkRet += 1;
        }
    
    context->numGroups = walkRet - context->groups;
    
    // Now that we're done with it, delete the closedContext and return
    
    if (closedCount)
        {
        PyMem_Free(closedContext->groups);
        PyMem_Free(closedContext);
        }
    
    return 0;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return -1;
    }   /* Normalize */

static int PairIntersect(CSpan_Group *g1, CSpan_Group *g2, CSpan_Group *out)
    {
    int     r = 0;
    long    a = g1->first;
    long    b = g1->last;
    long    c = g2->first;
    long    d = g2->last;
    
    if (a == OPEN_ENDED)
        {
        if (b == OPEN_ENDED)
            {   // (*, *) and anything
            *out = *g2;
            r = 1;
            }
        
        else
            {   // (*, b)
            if (c == OPEN_ENDED)
                {
                if (d == OPEN_ENDED)
                    {   // (*, b) and (*, *)
                    *out = *g1;
                    r = 1;
                    }
                
                else
                    {   // (*, b) and (*, d)
                    out->first = OPEN_ENDED;
                    out->last = (b < d ? b : d);
                    r = 1;
                    }
                }
            
            else if (d == OPEN_ENDED)
                {   // (*, b) and (c, *)
                if (b >= c)
                    {
                    out->first = c;
                    out->last = b;
                    r = 1;
                    }
                }
            
            else
                {   // (*, b) and (c, d)
                if (b >= c)
                    {
                    if (b >= d)
                        {
                        *out = *g2;
                        r = 1;
                        }
                    
                    else
                        {
                        out->first = c;
                        out->last = b;
                        r = 1;
                        }
                    }
                }
            }
        }
    
    else if (b == OPEN_ENDED)
        {   // (a, *)
        if (c == OPEN_ENDED)
            {
            if (d == OPEN_ENDED)
                {   // (a, *) and (*, *)
                *out = *g1;
                r = 1;
                }
            
            else
                {   // (a, *) and (*, d)
                if (d >= a)
                    {
                    out->first = a;
                    out->last = d;
                    r = 1;
                    }
                }
            }
        
        else
            {
            if (d == OPEN_ENDED)
                {   // (a, *) and (c, *)
                out->first = (a > c ? a : c);
                out->last = OPEN_ENDED;
                r = 1;
                }
            
            else
                {   // (a, *) and (c, d)
                if (a <= d)
                    {
                    if (a <= c)
                        {
                        *out = *g2;
                        r = 1;
                        }
                    
                    else
                        {
                        out->first = a;
                        out->last = d;
                        r = 1;
                        }
                    }
                }
            }
        }
    
    else
        {   // (a, b)
        if (c == OPEN_ENDED)
            {
            if (d == OPEN_ENDED)
                {   // (a, b) and (*, *)
                *out = *g1;
                r = 1;
                }
            
            else
                {   // (a, b) and (*, d)
                if (d >= a)
                    {
                    if (d >= b)
                        {
                        *out = *g1;
                        r = 1;
                        }
                    
                    else
                        {
                        out->first = a;
                        out->last = d;
                        r = 1;
                        }
                    }
                }
            }
        
        else
            {
            if (d == OPEN_ENDED)
                {   // (a, b) and (c, *)
                if (c <= b)
                    {
                    if (c <= a)
                        {
                        *out = *g1;
                        r = 1;
                        }
                    
                    else
                        {
                        out->first = c;
                        out->last = b;
                        r = 1;
                        }
                    }
                }
            
            else
                {   // (a, b) and (c, d)
                if (c <= b && d >= a)
                    {
                    out->first = (a > c ? a : c);
                    out->last = (b < d ? b : d);
                    r = 1;
                    }
                }
            }
        }
    
    return r;
    }   /* PairIntersect */

static int PairToLongs(PyObject *pair, long *thisFirst, long *thisLast)
    {
    Py_ssize_t  inputLength;
    PyObject    *fast, *obj;
    
    fast = PySequence_Fast(pair, "Unable to process pair!");
    require(fast, Err_BadReturn);
    
    inputLength = PySequence_Fast_GET_SIZE(fast);
    
    require_action(
      inputLength == 2,
      Err_FreeFast,
      PyErr_SetString(PyExc_ValueError, "Tuple not of length 2!"););
    
    obj = PySequence_Fast_GET_ITEM(fast, 0);  /* borrowed ref. */
    
    if (obj == Py_None)
        {
        *thisFirst = OPEN_ENDED;
        }
    
    else
        {
        *thisFirst = PyLong_AsLong(obj);
        require_noerr(PyErr_Occurred(), Err_FreeFast);
        }
    
    obj = PySequence_Fast_GET_ITEM(fast, 1);  /* borrowed ref. */
    
    if (obj == Py_None)
        {
        *thisLast = OPEN_ENDED;
        }
    
    else
        {
        *thisLast = PyLong_AsLong(obj);
        require_noerr(PyErr_Occurred(), Err_FreeFast);
        }
    
    Py_DECREF(fast);
    return 0;
    
    /*** ERROR HANDLERS ***/
    Err_FreeFast:       Py_DECREF(fast);
    Err_BadReturn:      return -1;
    }   /* PairToLongs */

/* ------------------------------------------------------------------------- */

#if 0
static void ______________(void){}
#endif

static PyObject *cspan_AddedFromPairs(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context, *rContext, *uContext;
    PyObject        *co, *r, *t;
    
    require_noerr(!PyArg_ParseTuple(args, "OO", &co, &t), Err_BadReturn);
    Py_INCREF(t);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_FreeT);
    
    rContext = Canonicalize(t, 0);
    require(rContext, Err_FreeT);
    
    uContext = MakeUnion(context, rContext);
    require(uContext, Err_FreeRContext);
    
    r = PyCapsule_New(uContext, "cspan_capsule", CapsuleDestructor);
    require(r, Err_FreeUContext);
    
    PyMem_Free(rContext->groups);
    PyMem_Free(rContext);
    Py_DECREF(t);
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeUContext:   PyMem_Free(uContext->groups);
                        PyMem_Free(uContext);
    Err_FreeRContext:   PyMem_Free(rContext->groups);
                        PyMem_Free(rContext);
    Err_FreeT:          Py_DECREF(t);
    Err_BadReturn:      return NULL;
    }   /* cspan_AddedFromPairs */

static PyObject *cspan_AddedFromSingles(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context, *rContext, *uContext;
    PyObject        *co, *r, *t;
    
    require_noerr(!PyArg_ParseTuple(args, "OO", &co, &t), Err_BadReturn);
    Py_INCREF(t);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_FreeT);
    
    rContext = Canonicalize_Singles(t, 0);
    require(rContext, Err_FreeT);
    
    uContext = MakeUnion(context, rContext);
    require(uContext, Err_FreeRContext);
    
    r = PyCapsule_New(uContext, "cspan_capsule", CapsuleDestructor);
    require(r, Err_FreeUContext);
    
    PyMem_Free(rContext->groups);
    PyMem_Free(rContext);
    Py_DECREF(t);
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeUContext:   PyMem_Free(uContext->groups);
                        PyMem_Free(uContext);
    Err_FreeRContext:   PyMem_Free(rContext->groups);
                        PyMem_Free(rContext);
    Err_FreeT:          Py_DECREF(t);
    Err_BadReturn:      return NULL;
    }   /* cspan_AddedFromSingles */

static PyObject *cspan_AsTuple(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context;
    PyObject        *co, *r, *t;
    
    require_noerr(!PyArg_ParseTuple(args, "O", &co), Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_BadReturn);
    
    if (!context->numGroups)
        {
        r = Py_BuildValue("()");
        require(r, Err_BadReturn);
        }
    
    else
        {
        CSpan_Group     *walk;
        unsigned long   i;
        
        r = PyTuple_New(context->numGroups);
        require(r, Err_BadReturn);
        
        walk = context->groups;
        
        for (i = 0UL; i < context->numGroups; i += 1UL)
            {
            t = GroupTuple(walk++);
            require(t, Err_FreeR);
            PyTuple_SET_ITEM(r, i, t);
            }
        }
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeR:          Py_DECREF(r);
    Err_BadReturn:      return NULL;
    }   /* cspan_AsTuple */

static PyObject *cspan_Bool(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context;
    PyObject        *co;
    
    require_noerr(!PyArg_ParseTuple(args, "O", &co), Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_BadReturn);
    
    if (context->numGroups)
        Py_RETURN_TRUE;
    
    Py_RETURN_FALSE;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return NULL;
    }   /* cspan_Bool */

static PyObject *cspan_ContainsValue(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context;
    CSpan_Group     *walk;
    long            n;
    PyObject        *co;
    unsigned long   count;
    
    require_noerr(!PyArg_ParseTuple(args, "Ol", &co, &n), Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_BadReturn);
    count = context->numGroups;
    
    if (!count)
        Py_RETURN_FALSE;
    
    /*
        At some point, if performance becomes an issue, we can change this
        logic to use bsearch() if numGroups is over some threshold value. For
        now, we just do a linear search (aborting the search, when indicated,
        given that the groups are sorted).
    */
    
    walk = context->groups;
    
    while (count--)
        {
        if (walk->first == OPEN_ENDED)
            {
            if (walk->last == OPEN_ENDED)
                Py_RETURN_TRUE;
            
            else if (n <= walk->last)
                Py_RETURN_TRUE;
            }
        
        else if (walk->last == OPEN_ENDED)
            {
            if (n >= walk->first)
                Py_RETURN_TRUE;
            }
        
        else if (n < walk->first)
            break;
        
        else if (n <= walk->last)
            Py_RETURN_TRUE;
        
        walk += 1;
        }
    
    Py_RETURN_FALSE;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return NULL;
    }   /* cspan_ContainsValue */

static PyObject *cspan_Count(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context;
    CSpan_Group     *walk;
    PyObject        *co, *r;
    unsigned long   count, cumul = 0;
    
    require_noerr(!PyArg_ParseTuple(args, "O", &co), Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_BadReturn);
    count = context->numGroups;
    
    if (count)
        {
        walk = context->groups;
    
        while (count--)
            {
            if (walk->first == OPEN_ENDED || walk->last == OPEN_ENDED)
                Py_RETURN_NONE;
            
            cumul += ((walk->last - walk->first) + 1UL);
            walk += 1;
            }
        }
    
    r = Py_BuildValue("k", cumul);
    require(r, Err_BadReturn);
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return NULL;
    }   /* cspan_Count */

static PyObject *cspan_DebugPrint(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context;
    PyObject        *co;
    
    require_noerr(!PyArg_ParseTuple(args, "O", &co), Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_BadReturn);
    
    DebugPrint(context);
    Py_RETURN_NONE;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return NULL;
    }   /* cspan_DebugPrint */

static PyObject *cspan_Equal(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context1, *context2;
    CSpan_Group     *g1, *g2;
    PyObject        *co1, *co2;
    unsigned long   count;
    
    require_noerr(!PyArg_ParseTuple(args, "OO", &co1, &co2), Err_BadReturn);
    
    context1 = PyCapsule_GetPointer(co1, "cspan_capsule");
    require(context1, Err_BadReturn);
    
    context2 = PyCapsule_GetPointer(co2, "cspan_capsule");
    require(context2, Err_BadReturn);
    
    if (context1->numGroups != context2->numGroups)
        Py_RETURN_FALSE;
    
    count = context1->numGroups;
    g1 = context1->groups;
    g2 = context2->groups;
    
    while (count--)
        {
        if (g1->first != g2->first)
            Py_RETURN_FALSE;
        
        if ((g1++)->last != (g2++)->last)
            Py_RETURN_FALSE;
        }
    
    Py_RETURN_TRUE;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return NULL;
    }   /* cspan_Equal */

static PyObject *cspan_Intersected(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context1, *context2, *rContext;
    PyObject        *co1, *co2, *r;
    
    require_noerr(!PyArg_ParseTuple(args, "OO", &co1, &co2), Err_BadReturn);
    
    context1 = PyCapsule_GetPointer(co1, "cspan_capsule");
    require(context1, Err_BadReturn);
    
    context2 = PyCapsule_GetPointer(co2, "cspan_capsule");
    require(context2, Err_BadReturn);
    
    if (IsFull(context1))
        {
        rContext = CopyContext(context2);
        require(rContext, Err_BadReturn);
        }
    
    else if (IsFull(context2))
        {
        rContext = CopyContext(context1);
        require(rContext, Err_BadReturn);
        }
    
    else if (!(context1->numGroups && context2->numGroups))
        {
        rContext = MakeEmpty();
        require(rContext, Err_BadReturn);
        }
    
    else
        {
        rContext = MakeIntersection(context1, context2);
        require(rContext, Err_BadReturn);
        }
    
    r = PyCapsule_New(rContext, "cspan_capsule", CapsuleDestructor);
    require(r, Err_FreeRContext);
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeRContext:   PyMem_Free(rContext->groups);
                        PyMem_Free(rContext);
    Err_BadReturn:      return NULL;
    }   /* cspan_Intersected */

static PyObject *cspan_Inverted(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context, *rContext;
    PyObject        *co, *r;
    
    require_noerr(!PyArg_ParseTuple(args, "O", &co), Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_BadReturn);
    
    if (!context->numGroups)
        {
        rContext = MakeFull();
        require(rContext, Err_BadReturn);
        }
    
    else if (
      (context->numGroups == 1) &&
      (context->groups->first == OPEN_ENDED) && 
      (context->groups->last == OPEN_ENDED))
        
        {
        rContext = MakeEmpty();
        require(rContext, Err_BadReturn);
        }
    
    else
        {
        rContext = MakeInverse(context);
        require(rContext, Err_BadReturn);
        }
    
    r = PyCapsule_New(rContext, "cspan_capsule", CapsuleDestructor);
    require(r, Err_FreeRContext);
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeRContext:   PyMem_Free(rContext->groups);
                        PyMem_Free(rContext);
    Err_BadReturn:      return NULL;
    }   /* cspan_Inverted */

static PyObject *cspan_IsFull(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context;
    PyObject        *co;
    
    require_noerr(!PyArg_ParseTuple(args, "O", &co), Err_BadReturn);
    
    context = PyCapsule_GetPointer(co, "cspan_capsule");
    require(context, Err_BadReturn);
    
    if (IsFull(context))
        Py_RETURN_TRUE;
    
    Py_RETURN_FALSE;
    
    /*** ERROR HANDLERS ***/
    Err_BadReturn:      return NULL;
    }   /* cspan_IsFull */

static PyObject *cspan_NewContext(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context;
    PyObject        *initTuple, *retVal;
    
    require_noerr(
      !PyArg_ParseTuple(args, "O", &initTuple),
      Err_BadReturn);
    
    Py_INCREF(initTuple);
    context = Canonicalize(initTuple, 1);
    require(context, Err_FreeIT);
    
    retVal = PyCapsule_New(context, "cspan_capsule", CapsuleDestructor);
    require(retVal, Err_FreeContext);
    
    Py_DECREF(initTuple);
    return retVal;
    
    /*** ERROR HANDLERS ***/
    Err_FreeContext:    PyMem_Free(context->groups);
                        PyMem_Free(context);
    Err_FreeIT:         Py_DECREF(initTuple);
    Err_BadReturn:      return NULL;
    }   /* cspan_NewContext */

static PyObject *cspan_Unioned(PyObject *self, PyObject *args)
    {
    CSpan_Context   *context1, *context2, *rContext;
    PyObject        *co1, *co2, *r;
    
    require_noerr(!PyArg_ParseTuple(args, "OO", &co1, &co2), Err_BadReturn);
    
    context1 = PyCapsule_GetPointer(co1, "cspan_capsule");
    require(context1, Err_BadReturn);
    
    context2 = PyCapsule_GetPointer(co2, "cspan_capsule");
    require(context2, Err_BadReturn);
    
    rContext = MakeUnion(context1, context2);
    require(rContext, Err_BadReturn);
    
    r = PyCapsule_New(rContext, "cspan_capsule", CapsuleDestructor);
    require(r, Err_FreeRContext);
    
    return r;
    
    /*** ERROR HANDLERS ***/
    Err_FreeRContext:   PyMem_Free(rContext->groups);
                        PyMem_Free(rContext);
    Err_BadReturn:      return NULL;
    }   /* cspan_Unioned */

/* ------------------------------------------------------------------------- */

/*** MODULE CREATION ***/

#if 0
static void ______________(void){}
#endif

static struct PyModuleDef cspanmodule =
    {
    PyModuleDef_HEAD_INIT,
    "cspanbackend",
    NULL,   /* module doc string */
    -1,
    CSpanMethods
    };

PyMODINIT_FUNC PyInit_cspanbackend(void)
    {
    return PyModule_Create(&cspanmodule);
    }  /* PyInit_cspanbackend */
