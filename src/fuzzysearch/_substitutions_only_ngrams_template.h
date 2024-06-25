#include "src/fuzzysearch/_c_ext_base.h"
#include "src/fuzzysearch/memmem.h"


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
    Py_ssize_t ngram_len, ngram_start, subseq_len_after_ngram;
    const char *match_ptr, *seq_ptr, *subseq_ptr, *subseq_end;
    int subseq_sum;
    int n_differences;

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

    /* this is required because simple_memmem_with_needle_sum() returns the
       haystack if the needle is empty */
    if (unlikely(subseq_len == 0)) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        goto error;
    }

    PREPARE;

    if (unlikely(seq_len < subseq_len)) {
        RETURN_AT_END;
    }

    ngram_len = subseq_len / (max_substitutions + 1);
    if (unlikely(ngram_len <= 0)) {
        /* ngram_len <= 0                                 *
         * IFF                                            *
         * max_substitutions + 1 > subseq_len             *
         * IFF                                            *
         * max_substitutions >= subseq_len                *
         *                                                *
         * So the sub-sequence may be found at any index. */
        for (ngram_start = 0; ngram_start + subseq_len <= seq_len; ngram_start++) {
            OUTPUT_VALUE(ngram_start);
        }
        RETURN_AT_END;
    }

    subseq_end = subsequence + subseq_len;

    for (ngram_start = 0; ngram_start + ngram_len <= subseq_len; ngram_start += ngram_len) {
        subseq_len_after_ngram = subseq_len - (ngram_start + ngram_len);

        subseq_sum = calc_sum(subsequence + ngram_start, ngram_len);

        match_ptr = simple_memmem_with_needle_sum(sequence + ngram_start,
                                  seq_len - ngram_start - subseq_len_after_ngram,
                                  subsequence + ngram_start,
                                  ngram_len,
                                  subseq_sum);

        while (match_ptr != NULL) {
            n_differences = max_substitutions + 1;

            subseq_ptr = subsequence + ngram_start;
            seq_ptr = match_ptr;
            while (subseq_ptr != subsequence && n_differences) {
                n_differences -= *(--subseq_ptr) != *(--seq_ptr);
            }

            if (n_differences) {
                subseq_ptr = subseq_end - subseq_len_after_ngram;
                seq_ptr = match_ptr + ngram_len;
                while (subseq_ptr != subseq_end && n_differences) {
                    n_differences -= (*subseq_ptr++) != (*seq_ptr++);
                }

                if (n_differences) {
                    OUTPUT_VALUE(match_ptr - ngram_start - sequence);
                }
            }

            match_ptr = simple_memmem_with_needle_sum(
                match_ptr + 1,
                seq_len - (match_ptr + 1 - sequence) - subseq_len_after_ngram,
                subsequence + ngram_start,
                ngram_len,
                subseq_sum);
        }
    }

    RETURN_AT_END;

error:
    RELEASE_BUFFERS;
    return NULL;
}

#undef RELEASE_BUFFERS
