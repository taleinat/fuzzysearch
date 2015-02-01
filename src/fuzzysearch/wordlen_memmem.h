#ifndef WORDLEN_MEMMEM_H
#define WORDLEN_MEMMEM_H

#include <stddef.h>

void *wordlen_memmem(const void *haystack, size_t haystacklen,
                     const void *needle, size_t needlelen);

#endif /* WORDLEN_MEMMEM_H */
