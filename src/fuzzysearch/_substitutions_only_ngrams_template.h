#include "src/fuzzysearch/memmem.h"


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


#define DO_FREES

static PyObject *
FUNCTION_NAME(PyObject *self, PyObject *args)
{
    /* input params */
    const char *subsequence;
    const char *sequence;
    int subseq_len_input, seq_len_input, max_substitutions_input;
    unsigned int subseq_len, seq_len, max_substitutions;

    unsigned int ngram_len, ngram_start, subseq_len_after_ngram;
    const char *match_ptr, *seq_ptr, *subseq_ptr, *subseq_end;
    int subseq_sum;
    unsigned int n_differences;

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
        &subsequence, &subseq_len_input,
        &sequence, &seq_len_input,
        &max_substitutions_input
    ))) {
        return NULL;
    }

    if (unlikely(max_substitutions_input < 0)) {
        PyErr_SetString(PyExc_ValueError, "max_l_dist must be non-negative");
        return NULL;
    }
    max_substitutions = (unsigned int) max_substitutions_input;

    if (unlikely(subseq_len_input < 0 || seq_len_input < 0)) {
        PyErr_SetString(PyExc_Exception, "an unknown error occurred");
        return NULL;
    }
    subseq_len = (unsigned int) subseq_len_input;
    seq_len = (unsigned int) seq_len_input;

    if (unlikely(subseq_len == 0)) {
        PyErr_SetString(PyExc_ValueError, "subsequence must not be empty");
        return NULL;
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
        for (ngram_start = 0; ngram_start <= seq_len - subseq_len; ngram_start++) {
            OUTPUT_VALUE(ngram_start);
        }
        RETURN_AT_END;
    }

    subseq_end = subsequence + subseq_len;

    for (ngram_start = 0; ngram_start <= subseq_len - ngram_len; ngram_start += ngram_len) {
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
}

#undef DO_FREES
