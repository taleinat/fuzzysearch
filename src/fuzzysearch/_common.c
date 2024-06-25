#include "src/fuzzysearch/_c_ext_base.h"
#include "src/fuzzysearch/memmem.h"


static PyObject *
search_exact_byteslike(PyObject *self, PyObject *args, PyObject *kwdict) {
    /* input params */
    Py_buffer subseq_pybuf, seq_pybuf;
    Py_ssize_t start_index=0, end_index=-1;

    static char *kwlist[] = {"subsequence", "sequence", "start_index", "end_index", NULL};

    const char *subseq, *seq;
    Py_ssize_t subseq_len, seq_len;
    PyObject *results;
    PyObject *next_result;
    size_t next_match_index;
    int subseq_sum;
    char *next_match_ptr;

    const char* argspec = "y*y*|nn:search_exact_byteslike";

    if (unlikely(!PyArg_ParseTupleAndKeywords(
        args, kwdict,
        argspec,
        kwlist,
        &subseq_pybuf,
        &seq_pybuf,
        &start_index,
        &end_index
    ))) {
        return NULL;
    }

    if (unlikely(!(
        is_simple_buffer(subseq_pybuf) &&
        is_simple_buffer(seq_pybuf)
    ))) {
        PyErr_SetString(PyExc_TypeError, "only contiguous sequences of single-byte values are supported");
        goto error;
    }

    subseq = (const char*)(subseq_pybuf.buf);
    seq = (const char*)(seq_pybuf.buf);
    subseq_len = subseq_pybuf.len;
    seq_len = seq_pybuf.len;

    /* this is required because simple_memmem_with_needle_sum() returns the
       haystack if the needle is empty */
    if (unlikely(subseq_len == 0)) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        goto error;
    }

    if (unlikely(start_index < 0)) {
        PyErr_SetString(PyExc_ValueError, "start_index must be non-negative");
        goto error;
    }

    if (end_index == -1) end_index = seq_len;
    if (unlikely(end_index < 0)) {
        PyErr_SetString(PyExc_ValueError, "end_index must be non-negative");
        goto error;
    }

    results = PyList_New(0);
    if (unlikely(!results)) {
        goto error;
    }

    seq_len = (end_index < seq_len ? end_index : seq_len);
    seq += (start_index < seq_len ? start_index : seq_len);
    seq_len -= (start_index <= seq_len ? start_index : seq_len);

    if (unlikely(seq_len < subseq_len)) {
        next_match_ptr = NULL;
    } else {
        subseq_sum = calc_sum(subseq, subseq_len);
        next_match_ptr = simple_memmem_with_needle_sum(seq, seq_len,
                                                       subseq, subseq_len,
                                                       subseq_sum);
    }

    while (next_match_ptr != NULL) {
        next_match_index = (const char *)next_match_ptr - seq;
        next_result = PyLong_FromLong(next_match_index + start_index);
        if (unlikely(next_result == NULL)) {
            Py_DECREF(results);
            goto error;
        }
        if (unlikely(PyList_Append(results, next_result) == -1)) {
            Py_DECREF(next_result);
            Py_DECREF(results);
            goto error;
        }
        Py_DECREF(next_result);

        next_match_ptr = simple_memmem_with_needle_sum(
            next_match_ptr + 1, seq_len - next_match_index - 1,
            subseq, subseq_len,
            subseq_sum);
    }

    PyBuffer_Release(&subseq_pybuf);
    PyBuffer_Release(&seq_pybuf);
    return results;

error:
    PyBuffer_Release(&subseq_pybuf);
    PyBuffer_Release(&seq_pybuf);
    return NULL;
}


static PyObject *
count_differences_with_maximum_byteslike(PyObject *self, PyObject *args)
{
    /* input params */
    Py_buffer seq1_pybuf, seq2_pybuf;
    int max_differences;

    const char *seq1, *seq2;
    Py_ssize_t seq1_len, seq2_len;
    Py_ssize_t i;
    int n_differences;

    const char* argspec = "y*y*i";

    if (!PyArg_ParseTuple(
        args,
        argspec,
        &seq1_pybuf,
        &seq2_pybuf,
        &max_differences
    )) {
        return NULL;
    }

    if (unlikely(!(
        is_simple_buffer(seq1_pybuf) &&
        is_simple_buffer(seq2_pybuf)
    ))) {
        PyErr_SetString(PyExc_TypeError, "only contiguous sequences of single-byte values are supported");
        goto error;
    }

    seq1 = (const char*)(seq1_pybuf.buf);
    seq2 = (const char*)(seq2_pybuf.buf);
    seq1_len = seq1_pybuf.len;
    seq2_len = seq2_pybuf.len;

    if (seq1_len != seq2_len) {
        PyErr_SetString(PyExc_ValueError,
                        "The lengths of the given sequences must be equal.");
        goto error;
    }

    n_differences = max_differences;
    for (i=seq1_len; i && n_differences; --i) {
        if ((*seq1) != (*seq2)) --n_differences;
        ++seq1;
        ++seq2;
    }

    PyBuffer_Release(&seq1_pybuf);
    PyBuffer_Release(&seq2_pybuf);
    return PyLong_FromLong((long) (max_differences - n_differences));

error:
    PyBuffer_Release(&seq1_pybuf);
    PyBuffer_Release(&seq2_pybuf);
    return NULL;
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
