#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif


static PyObject *
substitutions_only_has_near_matches_byteslike(PyObject *self, PyObject *args)
{
    /* input params */
    const char *subsequence;
    const char *sequence;
    int subseq_len, seq_len, max_substitutions;

    unsigned int *sub_counts;
    unsigned int seq_idx, subseq_idx, count_idx;

    if (!PyArg_ParseTuple(
        args, "s#s#i",
        &subsequence, &subseq_len,
        &sequence, &seq_len,
        &max_substitutions
    )) {
        return NULL;
    }

    if (seq_len < subseq_len) {
        Py_RETURN_FALSE;
    }

    /* this is required because simple_memmem_with_needle_sum() returns the
       haystack if the needle is empty */
    if (subseq_len == 0) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        return NULL;
    }

    sub_counts = (unsigned int *) malloc (sizeof(unsigned int) * subseq_len);
    if (sub_counts == NULL) {
        return PyErr_NoMemory();
    }

    for (seq_idx = 0; seq_idx < subseq_len - 1; ++seq_idx) {
        sub_counts[seq_idx] = 0;
        for (subseq_idx = 0; subseq_idx <= seq_idx; ++subseq_idx) {
            sub_counts[seq_idx - subseq_idx] +=
                subsequence[subseq_idx] != sequence[seq_idx];
        }
    }
    sub_counts[seq_idx] = 0;

    for (seq_idx = subseq_len-1; seq_idx < seq_len;) {
        for (subseq_idx = 0; subseq_idx < subseq_len; ++subseq_idx) {
            sub_counts[(seq_idx - subseq_idx) % subseq_len] +=
                subsequence[subseq_idx] != sequence[seq_idx];
        }

        ++seq_idx;
        count_idx = seq_idx % subseq_len;

        if (sub_counts[count_idx] <= max_substitutions) {
            free(sub_counts);
            Py_RETURN_TRUE;
        }
        sub_counts[count_idx] = 0;
    }

    free(sub_counts);
    Py_RETURN_FALSE;
}

#define FUNCTION_NAME substitutions_only_has_near_matches_ngrams_byteslike
#define PREPARE
#define OUTPUT_VALUE(x) Py_RETURN_TRUE
#define RETURN_AT_END Py_RETURN_FALSE
#include "fuzzysearch/_substitutions_only_ngrams_template.h"
#undef RETURN_AT_END
#undef OUTPUT_VALUE
#undef PREPARE
#undef FUNCTION_NAME

#define FUNCTION_NAME substitutions_only_find_near_matches_ngrams_byteslike
#ifdef IS_PY3K
#define PyInt_FromLong(x) PyLong_FromLong(x)
#endif
#define PREPARE              \
    PyObject *results;       \
    PyObject *next_result;   \
    results = PyList_New(0); \
    if (unlikely(!results))  \
        return NULL;
#define OUTPUT_VALUE(x) do {                                           \
    next_result = PyInt_FromLong((x));                                 \
    if (unlikely(next_result == NULL)) {                               \
        Py_DECREF(results);                                            \
        return NULL;                                                   \
    }                                                                  \
    if (unlikely(PyList_Append(results, next_result) == -1)) {         \
        Py_DECREF(next_result);                                        \
        Py_DECREF(results);                                            \
        return NULL;                                                   \
    }                                                                  \
    Py_DECREF(next_result);                                            \
} while(0)
#define RETURN_AT_END return results
#include "fuzzysearch/_substitutions_only_ngrams_template.h"
#undef RETURN_AT_END
#undef OUTPUT_VALUE
#undef PREPARE
#undef FUNCTION_NAME


static PyMethodDef substitutions_only_methods[] = {
    {"substitutions_only_has_near_matches_byteslike",
     substitutions_only_has_near_matches_byteslike,
     METH_VARARGS,
     "DOCSTRING."},
    {"substitutions_only_has_near_matches_ngrams_byteslike",
     substitutions_only_has_near_matches_ngrams_byteslike,
     METH_VARARGS,
     "DOCSTRING."},
    {"substitutions_only_find_near_matches_ngrams_byteslike",
     substitutions_only_find_near_matches_ngrams_byteslike,
     METH_VARARGS,
     "DOCSTRING."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


#ifdef IS_PY3K

static struct PyModuleDef substitutions_only_module = {
   PyModuleDef_HEAD_INIT,
   "_substitutions_only",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   substitutions_only_methods
};

PyMODINIT_FUNC
PyInit__substitutions_only(void)
{
    return PyModule_Create(&substitutions_only_module);
}

#else

PyMODINIT_FUNC
init_substitutions_only(void)
{
    (void) Py_InitModule("_substitutions_only", substitutions_only_methods);
}

#endif
