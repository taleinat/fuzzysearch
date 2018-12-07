#include <Python.h>
#include "src/fuzzysearch/memmem.h"

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif

#ifdef __GNUC__
  /* Test for GCC > 2.95 */
  #if __GNUC__ > 2 || (__GNUC__ == 2 && (__GNUC_MINOR__ > 95))
    #define likely(x)   __builtin_expect(!!(x), 1)
    #define unlikely(x) __builtin_expect(!!(x), 0)
  #else /* __GNUC__ > 2 ... */
    #define likely(x)   (x)
    #define unlikely(x) (x)
  #endif /* __GNUC__ > 2 ... */
#else /* __GNUC__ */
  #define likely(x)   (x)
  #define unlikely(x) (x)
#endif /* __GNUC__ */


#ifdef IS_PY3K
    #define ARG_TYPES_DEF "y#y#|ll:search_exact_byteslike"
#else
    #if PY_HEX_VERSION >= 0x02070000
        #define ARG_TYPES_DEF "t#t#|ll:search_exact_byteslike"
    #else
        #define ARG_TYPES_DEF "s#s#|ll:search_exact_byteslike"
    #endif
#endif

static PyObject *
search_exact_byteslike(PyObject *self, PyObject *args, PyObject *kwdict) {
    /* input params */
    const char *subseq, *seq;
    int subseq_len, seq_len;
    long int start_index=0, end_index=-1;

    static char *kwlist[] = {"subsequence", "sequence", "start_index", "end_index", NULL};

    PyObject *results;
    PyObject *next_result;
    size_t next_match_index;
    int subseq_sum;
    char *next_match_ptr;

    if (unlikely(!PyArg_ParseTupleAndKeywords(
        args, kwdict, ARG_TYPES_DEF, kwlist,
        &subseq, &subseq_len,
        &seq, &seq_len,
        &start_index,
        &end_index
    ))) {
        return NULL;
    }

    /* this is required because simple_memmem_with_needle_sum() returns the
       haystack if the needle is empty */
    if (unlikely(subseq_len == 0)) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        return NULL;
    }

    if (unlikely(start_index < 0)) {
        PyErr_SetString(PyExc_ValueError, "start_index must be non-negative");
        return NULL;
    }

    if (end_index == -1) end_index = seq_len;
    if (unlikely(end_index < 0)) {
        PyErr_SetString(PyExc_ValueError, "end_index must be non-negative");
        return NULL;
    }

    results = PyList_New(0);
    if (unlikely(!results)) {
        return NULL;
    }

    seq_len = (end_index < seq_len ? end_index : seq_len);
    seq += (start_index < seq_len ? start_index : seq_len);
    seq_len -= (start_index <= seq_len ? start_index : seq_len);

    if (unlikely(seq_len < subseq_len)) {
        return results;
    }

    subseq_sum = calc_sum(subseq, subseq_len);
    next_match_ptr = simple_memmem_with_needle_sum(seq, seq_len,
                                                   subseq, subseq_len,
                                                   subseq_sum);
    while (next_match_ptr != NULL) {
        next_match_index = (const char *)next_match_ptr - seq;
#ifdef IS_PY3K
        next_result = PyLong_FromLong(next_match_index + start_index);
#else
        next_result = PyInt_FromLong(next_match_index + start_index);
#endif
        if (unlikely(next_result == NULL)) {
            goto error;
        }
        if (unlikely(PyList_Append(results, next_result) == -1)) {
            Py_DECREF(next_result);
            goto error;
        }
        Py_DECREF(next_result);

        next_match_ptr = simple_memmem_with_needle_sum(
            next_match_ptr + 1, seq_len - next_match_index - 1,
            subseq, subseq_len,
            subseq_sum);
    }

    return results;

error:
    Py_DECREF(results);
    return NULL;
}


static PyObject *
count_differences_with_maximum_byteslike(PyObject *self, PyObject *args)
{
    /* input params */
    const char *seq1, *seq2;
    int seq1_len, seq2_len, max_differences;

    int i, n_differences;

    if (!PyArg_ParseTuple(
        args,
#ifdef IS_PY3K
        "y#y#i",
#else
    #if PY_HEX_VERSION >= 0x02070000
        "t#t#i",
    #else
        "s#s#i",
    #endif
#endif
        &seq1, &seq1_len,
        &seq2, &seq2_len,
        &max_differences
    )) {
        return NULL;
    }

    if (seq1_len != seq2_len) {
        PyErr_SetString(PyExc_ValueError,
                        "The lengths of the given sequences must be equal.");
        return NULL;
    }

    n_differences = max_differences;
    for (i=seq1_len; i && n_differences; --i) {
        if ((*seq1) != (*seq2)) --n_differences;
        ++seq1;
        ++seq2;
    }

    return PyLong_FromLong((long) (max_differences - n_differences));
}

static PyMethodDef _common_methods[] = {
    {"count_differences_with_maximum_byteslike",
     (PyCFunction)count_differences_with_maximum_byteslike,
     METH_VARARGS, "DOCSTRING."},
    {"search_exact_byteslike",
     (PyCFunction)search_exact_byteslike,
     METH_VARARGS | METH_KEYWORDS, "DOCSTRING"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


#ifdef IS_PY3K

static struct PyModuleDef _common_module = {
   PyModuleDef_HEAD_INIT,
   "_common",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   _common_methods
};

PyMODINIT_FUNC
PyInit__common(void)
{
    return PyModule_Create(&_common_module);
}

#else

PyMODINIT_FUNC
init_common(void)
{
    (void) Py_InitModule("_common", _common_methods);
}

#endif
