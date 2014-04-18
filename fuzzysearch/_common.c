#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif


static PyObject *
count_differences_with_maximum_byteslike(PyObject *self, PyObject *args)
{
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
