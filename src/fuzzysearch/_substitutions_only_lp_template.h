#define RELEASE_BUFFERS \
    PyBuffer_Release(&subseq_pybuf); \
    PyBuffer_Release(&seq_pybuf)


static PyObject *
FUNCTION_NAME(PyObject *self, PyObject *args)
{
    /* input params */
    Py_buffer subseq_pybuf, seq_pybuf;
    int max_substitutions;

    const char *subsequence;
    const char *sequence;
    Py_ssize_t subseq_len, seq_len;
    int *sub_counts = NULL;
    Py_ssize_t seq_idx, subseq_idx, count_idx;

    DECLARE_VARS;

    const char* argspec = "y*y*i";

    if (unlikely(!PyArg_ParseTuple(
        args,
        argspec,
        &subseq_pybuf,
        &seq_pybuf,
        &max_substitutions
    ))) {
        return NULL;
    }

    if (unlikely(max_substitutions < 0)) {
        PyErr_SetString(PyExc_ValueError, "max_l_dist must be non-negative");
        goto error;
    }

    if (unlikely(!(
        is_simple_buffer(subseq_pybuf) &&
        is_simple_buffer(seq_pybuf)
    ))) {
        PyErr_SetString(PyExc_TypeError, "only contiguous sequences of single-byte values are supported");
        goto error;
    }

    subsequence = (const char*)(subseq_pybuf.buf);
    sequence = (const char*)(seq_pybuf.buf);
    subseq_len = subseq_pybuf.len;
    seq_len = seq_pybuf.len;

    if (unlikely(subseq_len < 0 || seq_len < 0)) {
        PyErr_SetString(PyExc_Exception, "an unknown error occurred");
        goto error;
    }

    if (unlikely(subseq_len == 0)) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        goto error;
    }

    PREPARE;

    if (unlikely(seq_len < subseq_len)) {
        RELEASE_BUFFERS;
        RETURN_AT_END;
    }

    if (unlikely(max_substitutions >= subseq_len)) {
        for (seq_idx = 0; seq_idx <= seq_len - subseq_len; ++seq_idx) {
            OUTPUT_VALUE(seq_idx);
        }
        RELEASE_BUFFERS;
        RETURN_AT_END;
    }

    sub_counts = (int *) malloc (sizeof(int) * subseq_len);
    if (sub_counts == NULL) {
        RELEASE_BUFFERS;
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
            OUTPUT_VALUE(seq_idx - subseq_len);
        }
        sub_counts[count_idx] = 0;
    }

    free(sub_counts);
    RELEASE_BUFFERS;
    RETURN_AT_END;

error:
    RELEASE_BUFFERS;
    return NULL;
}

#undef RELEASE_BUFFERS
