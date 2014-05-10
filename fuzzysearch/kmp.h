struct KMPstate {
    const char *sequence_ptr;
    const char *sequence_end;
    const char *subsequence;
    int *kmpNext;
    int subseq_index;
    int subseq_len;
};

void preKMP(const char *subsequence, int subsequence_len, int *kmpNext);

struct KMPstate KMP_init(const char *subseq, int subseq_len,
                         const char *seq, int seq_len,
                         int *kmpNext);

const char* KMP_find_next(struct KMPstate *kmp_state);
