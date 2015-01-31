#include <Python.h>
#include "fuzzysearch/memmem.h"

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


static PyObject *
search_exact_byteslike(PyObject *self, PyObject *args) {
    /* input params */
    const char *subseq, *seq;
    int subseq_len, seq_len;

    PyObject *results;
    PyObject *next_result;
    size_t next_match_index;
    int subseq_sum;
    void *next_match_ptr;

    if (unlikely(!PyArg_ParseTuple(
        args, "s#s#",
        &subseq, &subseq_len,
        &seq, &seq_len
    ))) {
        return NULL;
    }

    /* this is required because simple_memmem_with_needle_sum() returns the
       haystack if the needle is empty */
    if (unlikely(subseq_len == 0)) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        return NULL;
    }

    results = PyList_New(0);
    if (unlikely(!results)) {
        return NULL;
    }

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
        next_result = PyLong_FromLong(next_match_index);
#else
        next_result = PyInt_FromLong(next_match_index);
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
        args, "s#s#i",
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
        n_differences -= (*seq1) != (*seq2);
        ++seq1;
        ++seq2;
    }

    return PyLong_FromLong((long) (max_differences - n_differences));
}

static PyMethodDef _common_methods[] = {
    {"count_differences_with_maximum_byteslike",
     count_differences_with_maximum_byteslike,
     METH_VARARGS, "DOCSTRING."},
    {"search_exact_byteslike", search_exact_byteslike,
     METH_VARARGS, "DOCSTRING"},
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
