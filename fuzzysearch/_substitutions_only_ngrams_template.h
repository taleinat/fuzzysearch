#include "fuzzysearch/memmem.h"

#if PY_MAJOR_VERSION >= 3
#define IS_PY3K
#endif

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
    int subseq_len, seq_len, max_substitutions;

    int ngram_len, ngram_start, subseq_len_after_ngram;
    const char *match_ptr, *seq_ptr, *subseq_ptr, *subseq_end;
    int subseq_sum;
    int n_differences;

    if (!PyArg_ParseTuple(
        args, "s#s#i",
        &subsequence, &subseq_len,
        &sequence, &seq_len,
        &max_substitutions
    )) {
        return NULL;
    }

    ngram_len = subseq_len / (max_substitutions + 1);
    if (ngram_len == 0) {
        PyErr_SetString(PyExc_ValueError,
            "The subsequence's length must be greater than max_substitutions!"
        );
        return NULL;
    }

    PREPARE;

    if (seq_len < subseq_len) {
        DO_FREES;
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

    DO_FREES;
    RETURN_AT_END;
}

#undef DO_FREES
