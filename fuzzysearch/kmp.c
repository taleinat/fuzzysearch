#include <Python.h>
#include "fuzzysearch/kmp.h"

void preKMP(const char *subseq, int subseq_len, int *kmpNext) {
    int i, j;

    i = 0;
    j = kmpNext[0] = -1;
    while (i != subseq_len) {
        while (j != -1 && subseq[i] != subseq[j])
            j = kmpNext[j];
        i++;
        j++;
        kmpNext[i] = (subseq[i] == subseq[j]) ? kmpNext[j] : j;
    }
}

struct KMPstate KMP_init(const char *subseq, int subseq_len,
                         const char *seq, int seq_len,
                         int *kmpNext) {
    struct KMPstate retval = {
        .sequence_ptr = seq,
        .sequence_end = seq + seq_len,
        .subsequence = subseq,
        .kmpNext = kmpNext,
        .subseq_index = 0,
        .subseq_len = subseq_len,
    };
    return retval;
}

const char* KMP_find_next(struct KMPstate *kmp_state) {
    const char *sequence_ptr = kmp_state->sequence_ptr;
    const char *sequence_end = kmp_state->sequence_end;
    const char *subsequence = kmp_state->subsequence;
    int *kmpNext = kmp_state->kmpNext;
    int subseq_index = kmp_state->subseq_index;
    int subseq_len = kmp_state->subseq_len;

    while (sequence_ptr != sequence_end) {
        while (subseq_index != -1 && subsequence[subseq_index] != (*sequence_ptr))
            subseq_index = kmpNext[subseq_index];
        subseq_index++;
        sequence_ptr++;
        if (subseq_index == subseq_len) {
            kmp_state->subseq_index = kmpNext[subseq_index];
            kmp_state->sequence_ptr = sequence_ptr;
            return sequence_ptr - subseq_len;
        }
    }

    return NULL;
}
