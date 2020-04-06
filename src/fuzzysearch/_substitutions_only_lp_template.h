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


#define DO_FREES free(sub_counts)

static PyObject *
FUNCTION_NAME(PyObject *self, PyObject *args)
{
    /* input params */
    const char *subsequence;
    const char *sequence;
    Py_ssize_t subseq_len, seq_len;
    int max_substitutions_input;
    unsigned int max_substitutions;

    unsigned int *sub_counts;
    Py_ssize_t seq_idx, subseq_idx, count_idx;

    DECLARE_VARS;

#ifdef IS_PY3K
    #define ARGSPEC "y#y#i"
#else
    #if PY_HEX_VERSION >= 0x02070000
        #define ARGSPEC "t#t#i"
    #else
        #define ARGSPEC "s#s#i"
    #endif
#endif

    if (unlikely(!PyArg_ParseTuple(
        args,
        ARGSPEC,
        &subsequence, &subseq_len,
        &sequence, &seq_len,
        &max_substitutions_input
    ))) {
        return NULL;
    }

    if (unlikely(max_substitutions_input < 0)) {
        PyErr_SetString(PyExc_ValueError, "max_l_dist must be non-negative");
        return NULL;
    }
    max_substitutions = (unsigned int) max_substitutions_input;

    if (unlikely(subseq_len < 0 || seq_len < 0)) {
        PyErr_SetString(PyExc_Exception, "an unknown error occurred");
        return NULL;
    }

    if (unlikely(subseq_len == 0)) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        return NULL;
    }

    PREPARE;

    if (unlikely(seq_len < subseq_len)) {
        RETURN_AT_END;
    }

    sub_counts = (unsigned int *) malloc (sizeof(unsigned int) * subseq_len);
    if (sub_counts == NULL) {
        return PyErr_NoMemory();
    }

    if (unlikely(max_substitutions >= subseq_len)) {
        for (seq_idx = 0; seq_idx <= seq_len - subseq_len; ++seq_idx) {
            OUTPUT_VALUE(seq_idx);
        }
        RETURN_AT_END;
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
            OUTPUT_VALUE(seq_idx - subseq_len);
        }
        sub_counts[count_idx] = 0;
    }

    DO_FREES;
    RETURN_AT_END;
}

#undef DO_FREES
