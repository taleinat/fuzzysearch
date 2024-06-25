#include "src/fuzzysearch/_c_ext_base.h"


#define DECLARE_VARS int found = 0
#define PREPARE
#define OUTPUT_VALUE(x) found = 1; break
#define RETURN_AT_END if (found) { Py_RETURN_TRUE; } else { Py_RETURN_FALSE; }
#define FUNCTION_NAME substitutions_only_has_near_matches_lp_byteslike
#include "src/fuzzysearch/_substitutions_only_lp_template.h"
#undef FUNCTION_NAME
#define FUNCTION_NAME substitutions_only_has_near_matches_ngrams_byteslike
#include "src/fuzzysearch/_substitutions_only_ngrams_template.h"
#undef FUNCTION_NAME
#undef RETURN_AT_END
#undef OUTPUT_VALUE
#undef PREPARE
#undef DECLARE_VARS


#define DECLARE_VARS       \
    PyObject *results;     \
    PyObject *next_result
#define PREPARE              \
    results = PyList_New(0); \
    if (unlikely(!results))  \
        goto error;
#define OUTPUT_VALUE(x) do {                                           \
    next_result = PyLong_FromSsize_t((x));                             \
    if (unlikely(next_result == NULL)) {                               \
        Py_DECREF(results);                                            \
        goto error;                                                    \
    }                                                                  \
    if (unlikely(PyList_Append(results, next_result) == -1)) {         \
        Py_DECREF(next_result);                                        \
        Py_DECREF(results);                                            \
        goto error;                                                    \
    }                                                                  \
    Py_DECREF(next_result);                                            \
} while(0)
#define RETURN_AT_END return results
#define FUNCTION_NAME substitutions_only_find_near_matches_lp_byteslike
#include "src/fuzzysearch/_substitutions_only_lp_template.h"
#undef FUNCTION_NAME
#define FUNCTION_NAME substitutions_only_find_near_matches_ngrams_byteslike
#include "src/fuzzysearch/_substitutions_only_ngrams_template.h"
#undef FUNCTION_NAME
#undef RETURN_AT_END
#undef OUTPUT_VALUE
#undef PREPARE
#undef DECLARE_VARS


static PyMethodDef substitutions_only_methods[] = {
    {"substitutions_only_find_near_matches_lp_byteslike",
     substitutions_only_find_near_matches_lp_byteslike,
     METH_VARARGS,
     "DOCSTRING."},
    {"substitutions_only_find_near_matches_ngrams_byteslike",
     substitutions_only_find_near_matches_ngrams_byteslike,
     METH_VARARGS,
     "DOCSTRING."},
    {"substitutions_only_has_near_matches_lp_byteslike",
     substitutions_only_has_near_matches_lp_byteslike,
     METH_VARARGS,
     "DOCSTRING."},
    {"substitutions_only_has_near_matches_ngrams_byteslike",
     substitutions_only_has_near_matches_ngrams_byteslike,
     METH_VARARGS,
     "DOCSTRING."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


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
