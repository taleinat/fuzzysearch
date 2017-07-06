#include <string.h>
#include "src/fuzzysearch/memmem.h"


int calc_sum(const char *sequence, size_t sequence_len) {
    int seq_sum = 0;
    const char *seq_end = sequence + sequence_len;
    while (sequence != seq_end) {
        seq_sum += *((const unsigned char *)sequence++);
    }
    return seq_sum;
}

char *simple_memmem(const char *haystack, size_t haystacklen,
                    const char *needle, size_t needlelen)
{
    const char* needle_ptr;
    const char* haystack_ptr;
    int sums_diff;

    switch (needlelen) {
        case (0):
            /* empty needle */
            return (char *) haystack;
            break;
        case (1):
            /* special case for single-character needles */
            return memchr(haystack, *((unsigned char*) needle), haystacklen);
            break;
    }

    /* start searching through haystack only from the first occurence of the
       first character of needle */
    haystack_ptr = memchr(haystack, *((unsigned char*) needle), haystacklen);
    if (!haystack_ptr) {
        /* the first character of needle isn't in haystack */
        return NULL;
    }
    haystacklen -= (haystack_ptr - haystack);
    if (haystacklen < needlelen) {
        /* the remaining haystack is smaller than needle */
        return NULL;
    }
    haystack = haystack_ptr;

    /* At this point:
       * needle is at least two characters long
       * haystack is at least needlelen characters long (so also at least two)
       * the first characters of needle and haystack are identical
    */

    /* calculate the sum of the first needlelen characters of haystack,
       minus the first needlelen characters of needle */

    sums_diff = 0;
    needle_ptr = needle + 1;
    haystack_ptr++;

    needle += needlelen; /* temporarily set needle to its own end */
    while (needle_ptr != needle) {
        sums_diff += *((unsigned char *) haystack_ptr++);
        sums_diff -= *((unsigned char *) needle_ptr++);
    }
    needle -= needlelen; /* set needle back to its original value */

    /* at this point, haystack_ptr == haystack + needlelen */

    /* note that here we know that the first characters are identical and that
       the sums are equal, so it is enough to compare all but the first and
       last characters */
    if (sums_diff == 0 && memcmp(haystack+1, needle+1, needlelen-2) == 0) {
        return (char *) haystack;
    }

    /* iterate through the remainder of haystack, updating the sums' difference
       and checking for identity whenever the difference is zero */
    needle_ptr = haystack + haystacklen;
    while (haystack_ptr != needle_ptr) {
        sums_diff -= *((unsigned char *) haystack++);
        sums_diff += *((unsigned char *) haystack_ptr++);

        /* if sums_diff == 0, we know that the sums are equal, so it is enough
           to compare all but the last characters */
        if (sums_diff == 0 && memcmp(haystack, needle, needlelen-1) == 0) {
            return (char *) haystack;
        }
    }

    return NULL;
}

char *simple_memmem_with_needle_sum(const char *haystack, size_t haystacklen,
                                    const char *needle, size_t needlelen,
                                    int needle_sum)
{
    const char* needle_ptr;
    const char* haystack_ptr;
    int sums_diff;

    switch (needlelen) {
        case (0):
            /* empty needle */
            return (char *) haystack;
            break;
        case (1):
            /* special case for single-character needles */
            return memchr(haystack, *((unsigned char*) needle), haystacklen);
            break;
    }

    /* start searching through haystack only from the first occurence of the
       first character of needle */
    haystack_ptr = memchr(haystack, *((unsigned char*) needle), haystacklen);
    if (!haystack_ptr) {
        /* the first character of needle isn't in haystack */
        return NULL;
    }
    haystacklen -= (haystack_ptr - haystack);
    if (haystacklen < needlelen) {
        /* the remaining haystack is smaller than needle */
        return NULL;
    }
    haystack = haystack_ptr;

    /* At this point:
       * needle is at least two characters long
       * haystack is at least needlelen characters long (so also at least two)
       * the first characters of needle and haystack are identical
    */

    /* calculate the sum of the first needlelen characters of haystack,
       minus the furst needlelen characters of needle */

    sums_diff = calc_sum(haystack, needlelen) - needle_sum;

    /* note that here we know that the first characters are identical and that
       the sums are equal, so it is enough to compare all but the first and
       last characters */
    if (sums_diff == 0 && memcmp(haystack+1, needle+1, needlelen-2) == 0) {
        return (char *) haystack;
    }


    /* iterate through the remainder of haystack, updating the sums' difference
       and checking for identity whenever the difference is zero */
    haystack_ptr = haystack + needlelen;
    needle_ptr = haystack + haystacklen;
    while (haystack_ptr != needle_ptr) {
        sums_diff -= *((unsigned char *) haystack++);
        sums_diff += *((unsigned char *) haystack_ptr++);

        /* if sums_diff == 0, we know that the sums are equal, so it is enough
           to compare all but the last characters */
        if (sums_diff == 0 && memcmp(haystack, needle, needlelen-1) == 0) {
            return (char *) haystack;
        }
    }

    return NULL;
}
