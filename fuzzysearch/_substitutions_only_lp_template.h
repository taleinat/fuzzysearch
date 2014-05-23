#define DO_FREES free(sub_counts)

static PyObject *
FUNCTION_NAME(PyObject *self, PyObject *args)
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

    PREPARE;

    if (seq_len < subseq_len) {
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
