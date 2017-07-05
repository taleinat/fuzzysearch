#ifndef MEMMEM_H
#define MEMMEM_H

#include <stddef.h>

int calc_sum(const char *sequence, size_t sequence_len);

char *simple_memmem(const char *haystack, size_t haystacklen,
                    const char *needle, size_t needlelen);

char *simple_memmem_with_needle_sum(const char *haystack, size_t haystacklen,
                                    const char *needle, size_t needlelen,
                                    int needle_sum);

#endif /* MEMMEM_H */
