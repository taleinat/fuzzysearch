#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif


static PyObject *
substitutions_only_has_near_matches_byteslike(PyObject *self, PyObject *args)
{
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
//        for(count_idx = 0; count_idx <= seq_idx; ++count_idx) {
//            printf("%d ", sub_counts[count_idx]);
//        }
//        printf("\n");
    }
    sub_counts[seq_idx] = 0;

    for (seq_idx = subseq_len-1; seq_idx < seq_len;) {
        for (subseq_idx = 0; subseq_idx < subseq_len; ++subseq_idx) {
            sub_counts[(seq_idx - subseq_idx) % subseq_len] +=
                subsequence[subseq_idx] != sequence[seq_idx];
        }

//        for(count_idx = 0; count_idx < subseq_len; ++count_idx) {
//            printf("%d ", sub_counts[count_idx]);
//        }
//        printf("\n");

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

static PyMethodDef substitutions_only_methods[] = {
    {"substitutions_only_has_near_matches_byteslike",
     substitutions_only_has_near_matches_byteslike,
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
