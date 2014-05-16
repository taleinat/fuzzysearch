#include <stddef.h>

int calc_sum(const void *sequence, size_t sequence_len);

void *simple_memmem(const void *haystack, size_t haystacklen,
                    const void *needle, size_t needlelen);

void *simple_memmem_with_needle_sum(const void *haystack, size_t haystacklen,
                                    const void *needle, size_t needlelen,
                                    int needle_sum);
