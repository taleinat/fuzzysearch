#include <string.h>
#include "fuzzysearch/memmem.h"

int calc_sum(const void *sequence, size_t sequence_len) {
    int seq_sum = 0;
    const void *seq_end = sequence + sequence_len;
    while (sequence != seq_end) {
        seq_sum += *((const unsigned char *)sequence++);
    }
    return seq_sum;
}

void *simple_memmem(const void *haystack, size_t haystacklen,
                    const void *needle, size_t needlelen)
{
    const void* needle_ptr;
    const void* haystack_ptr;
    int sums_diff;

    switch (needlelen) {
        case (0):
            /* empty needle */
            return (void *) haystack;
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
        return (void *) haystack;
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
            return (void *) haystack;
        }
    }

    return NULL;
}

void *simple_memmem_with_needle_sum(const void *haystack, size_t haystacklen,
                                    const void *needle, size_t needlelen,
                                    int needle_sum)
{
    const void* needle_ptr;
    const void* haystack_ptr;
    int sums_diff;

    switch (needlelen) {
        case (0):
            /* empty needle */
            return (void *) haystack;
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
        return (void *) haystack;
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
            return (void *) haystack;
        }
    }

    return NULL;
}


#define LONGLEN sizeof(long)

void *wordlen_memmem(const void *haystack, size_t haystacklen,
                     const void *needle, size_t needlelen)
{
    const void* needle_ptr;
    const void* haystack_ptr;
    int sums_diff;
    int compare_len;
    unsigned long last_needle_chars = 0;
    unsigned long last_haystack_chars = 0;

    switch (needlelen) {
        case (0):
            /* empty needle */
            return (void *) haystack;
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


    if (needlelen > LONGLEN + 1)
    {
        needle_ptr = needle;
        needle += needlelen - LONGLEN;
        sums_diff = 0;
        while (needle_ptr != needle) {
            sums_diff -= *((unsigned char *) needle_ptr++);
            sums_diff += *((unsigned char *) haystack_ptr++);
        }

        needle += LONGLEN;
        while (needle_ptr != needle) {
            last_needle_chars <<= LONGLEN;
            last_needle_chars ^= *(unsigned char *)needle_ptr;
            last_haystack_chars <<= LONGLEN;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr;
            sums_diff -= *((unsigned char *) needle_ptr++);
            sums_diff += *((unsigned char *) haystack_ptr++);
        }
        needle -= needlelen;

        /* we will call memcmp() only once we know that the sums are equal and
           that LONGLEN last chars are equal, so it will be enough to compare
           all but the last LONGLEN + 1 characters */
        compare_len = needlelen - (LONGLEN + 1);

        /* At this point:
           * needle is at least two characters long
           * haystack is at least needlelen characters long (also at least two)
           * the first characters of needle and haystack are identical
        */
        if (   sums_diff == 0
            && last_haystack_chars == last_needle_chars
            && memcmp(haystack, needle, compare_len) == 0)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the sums' difference
           and checking for identity whenever the difference is zero */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            last_haystack_chars <<= LONGLEN;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr;
            sums_diff -= *((unsigned char *) haystack++);
            sums_diff += *((unsigned char *) haystack_ptr++);

            /* if sums_diff == 0, we know that the sums are equal, so it is enough
               to compare all but the last characters */
            if (   sums_diff == 0
                && last_haystack_chars == last_needle_chars
                && memcmp(haystack, needle, compare_len) == 0)
            {
                return (void *) haystack;
            }
        }
    }
    else if (needlelen < LONGLEN)
    {
        needle_ptr = needle;
        needle += needlelen;
        sums_diff = 0;
        while (needle_ptr != needle) {
            sums_diff -= *((unsigned char *) needle_ptr++);
            sums_diff += *((unsigned char *) haystack_ptr++);
        }
        needle -= needlelen;

        /* we will call memcmp() only once we know that the sums are equal, so
           it will be enough to compare all but the last characters */
        compare_len = needlelen - 1;

        /* At this point:
           * needle is at least two characters long
           * haystack is at least needlelen characters long (also at least two)
           * the first characters of needle and haystack are identical
        */
        if (   sums_diff == 0
            && memcmp(haystack, needle, compare_len) == 0)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the sums' difference
           and checking for identity whenever the difference is zero */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            sums_diff -= *((unsigned char *) haystack++);
            sums_diff += *((unsigned char *) haystack_ptr++);

            /* if sums_diff == 0, we know that the sums are equal, so it is enough
               to compare all but the last characters */
            if (   sums_diff == 0
                && memcmp(haystack, needle, compare_len) == 0)
            {
                return (void *) haystack;
            }
        }
    }
    else if (needlelen == LONGLEN)
    {
        needle_ptr = needle;
        needle += needlelen;
        while (needle_ptr != needle) {
            last_needle_chars <<= LONGLEN;
            last_needle_chars ^= *(unsigned char *)needle_ptr++;
            last_haystack_chars <<= LONGLEN;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;
        }
        needle -= needlelen;

        if (last_haystack_chars == last_needle_chars)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the last char
           data and checking for equality */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            last_haystack_chars <<= LONGLEN;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;

            if (last_haystack_chars == last_needle_chars)
            {
                return (void *) (haystack_ptr - needlelen);
            }
        }
    }
    else /* needlelen == LONGLEN + 1 */
    {
        needle_ptr = needle;
        needle += needlelen;
        ++needle_ptr;
        ++haystack_ptr;
        while (needle_ptr != needle) {
            last_needle_chars <<= LONGLEN;
            last_needle_chars ^= *(unsigned char *)needle_ptr++;
            last_haystack_chars <<= LONGLEN;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;
        }
        needle -= needlelen;

        if (   last_haystack_chars == last_needle_chars
            && *(unsigned char *)haystack == *(unsigned char *)needle)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the last char
           data and checking for equality */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            last_haystack_chars <<= LONGLEN;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;

            ++haystack;
            if (   last_haystack_chars == last_needle_chars
                && *(unsigned char *)haystack == *(unsigned char *)needle)
            {
                return (void *) haystack;
            }
        }
    }

    return NULL;
}
