#include <Python.h>
#include "src/fuzzysearch/memmem.h"
#include "src/fuzzysearch/wordlen_memmem.h"


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
py_simple_memmem(PyObject *self, PyObject *args) {
    /* input params */
    const char *haystack, *needle;
    int haystack_len, needle_len;

    const char *result;
    PyObject *py_result;

    if (unlikely(!PyArg_ParseTuple(
        args,
        "y#y#",
        &needle, &needle_len,
        &haystack, &haystack_len
    ))) {
        return NULL;
    }

    result = simple_memmem(haystack, haystack_len,
                           needle, needle_len);
    if (result == NULL) {
        Py_RETURN_NONE;
    }
    else {
        py_result = PyLong_FromLong(result - haystack);
        if (unlikely(py_result == NULL)) {
            return NULL;
        }
        return py_result;
    }
}

static PyObject *
py_wordlen_memmem(PyObject *self, PyObject *args) {
    /* input params */
    const char *haystack, *needle;
    int haystack_len, needle_len;

    const char *result;
    PyObject *py_result;

    if (unlikely(!PyArg_ParseTuple(
        args,
        "y#y#",
        &needle, &needle_len,
        &haystack, &haystack_len
    ))) {
        return NULL;
    }

    result = wordlen_memmem(haystack, haystack_len,
                            needle, needle_len);
    if (result == NULL) {
        Py_RETURN_NONE;
    }
    else {
        py_result = PyLong_FromLong(result - haystack);
        if (unlikely(py_result == NULL)) {
            return NULL;
        }
        return py_result;
    }
}


static PyMethodDef _pymemmem_methods[] = {
    {"simple_memmem",
     py_simple_memmem,
     METH_VARARGS, "DOCSTRING."},
    {"wordlen_memmem",
     py_wordlen_memmem,
     METH_VARARGS, "DOCSTRING."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


static struct PyModuleDef _pymemmem_module = {
   PyModuleDef_HEAD_INIT,
   "_pymemmem",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   _pymemmem_methods
};

PyMODINIT_FUNC
PyInit__pymemmem(void)
{
    return PyModule_Create(&_pymemmem_module);
}
